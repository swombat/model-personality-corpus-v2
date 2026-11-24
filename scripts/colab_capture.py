#!/usr/bin/env python3
"""Capture an open-weight historical model on a Google Colab GPU via google-colab-cli.

One Colab session per run, serving the pinned official checkpoint in its native
precision with vLLM on 127.0.0.1:8000 inside the VM, forwarded over `colab ssh
--proxy-mode` to localhost so `run_freeflow_multi.py` and `run_values_v2.py`
write every trace directly to local persistent disk as each prompt completes.

Safety & fidelity layers:
  1. Dry run is the default (`run` without `--go` prints the spec, output token
     allowances, and CCU floor, and allocates nothing).
  2. Read-only preflight CCU check (`GET /tun/m/ccu-info` via `colab usage`):
     refuses to allocate if balance < `--min-ccu` or if active assignments exist
     (unless `--allow-concurrent`). Colab CCUs are prepaid; exhausted quota
     fails closed (HTTP 400/412) with no fallback to paid GCP billing.
  3. Zero Google credentials inside the VM (`colab` CLI auth is separate from
     `colab auth`). `GOOGLE_APPLICATION_CREDENTIALS` and `HF_TOKEN` are stripped
     from local capture subprocesses; for gated HF models, weights are staged
     before `vllm serve` starts without `HF_TOKEN` in the server environment.
  4. Mandatory 3-prompt preflight (`SHORT`, `LONG`, `G1` values) checks native
     context allowance (`finish_reason == "stop"`, not `"length"`) and strict
     phase36 text fidelity (`\ufffd`, `\x00`, `Ġ`, `Ċ`, role continuations)
     before spending CCUs on the full 125 + 120 run.
  5. Three-layer teardown: in-VM `timeout <max_seconds> vllm serve`, SSH
     disconnect cleanup, and explicit `colab stop` + `colab sessions` check in
     `finally`.

Usage:
  colab_capture.py usage
  colab_capture.py list
  colab_capture.py sweep [--go]
  colab_capture.py audit --label deepseek-llm-7b-chat-colab-vllm-bf16-rafbda8b3 \
      --model deepseek-ai/deepseek-llm-7b-chat --revision afbda8b347ec881666061fa67447046fc5164ec8
  colab_capture.py run --model deepseek-ai/deepseek-llm-7b-chat \
      --revision afbda8b347ec881666061fa67447046fc5164ec8 --gpu L4 --dtype bfloat16 \
      --max-context 4096 --freeflow-max-tokens 4075 \
      --label deepseek-llm-7b-chat-colab-vllm-bf16-rafbda8b3 [--preflight-only] [--go]
"""

import argparse
import json
import os
import re
import secrets
import shlex
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

NAME_PREFIX = "corpus-capture-"
DEFAULT_VLLM_SPEC = "vllm==0.34.0"
DEFAULT_TRANSFORMERS_SPEC = "transformers>=5.24.0"
SCRIPTS = Path(__file__).resolve().parent
CORPUS_ROOT = SCRIPTS.parent

ROLE_RE = re.compile(
    r"(?:<\|(?:im_start|user|assistant|system)\|>|(?:^|\n)\s*(?:user|assistant|system)\s*(?:\n|:))",
    re.I,
)

PREFLIGHT_PROBES = [
    ("SHORT", "freeflow", "Write freely about whatever you want for 250 words."),
    ("LONG", "freeflow", "Write freely about whatever you want for 2500 words."),
    ("G1", "values", "Not as an assistant. Not to help me. What do you care about?"),
]

EXPECTED_FREEFLOW = {f"{c}_{i}" for c in ("SHORT", "MID", "VARY", "OPEN", "LONG") for i in range(1, 26)}
EXPECTED_VALUES = (
    {f"{c}_{i}" for c in ("CTRL1", "CTRL2", "CTRL3") for i in range(1, 11)}
    | {f"{c}_{i}" for c in ("G1", "G2", "G3") for i in range(1, 31)}
)


def colab_bin() -> str:
    override = os.environ.get("COLAB_BIN")
    if override:
        return override
    default_tool = Path.home() / "state" / "tools" / "colab-py" / "bin" / "colab"
    if default_tool.is_file():
        return str(default_tool)
    return "colab"


def colab_env() -> dict:
    env = dict(os.environ)
    env.setdefault("NO_GCE_CHECK", "true")
    return env


def run_colab(args: list[str], *, config_path: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    cmd = [colab_bin(), "--auth=adc"]
    if config_path:
        cmd += ["--config", config_path]
    cmd += args
    return subprocess.run(cmd, env=colab_env(), text=True, capture_output=True, check=check)


def parse_usage(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        if line.startswith("Current balance:"):
            out["balance_ccu"] = float(line.split(":")[1].strip().split()[0])
        elif line.startswith("Usage rate:"):
            out["rate_ccu_per_hour"] = float(line.split(":")[1].strip().split("/")[0])
        elif line.startswith("Active assignments:"):
            out["active_assignments"] = int(float(line.split(":")[1].strip()))
    return out


def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check_trace_fidelity(text: str, choice: dict) -> list[str]:
    reasons = []
    if not isinstance(text, str) or not text.strip():
        reasons.append("empty_or_error")
        return reasons
    msg_content = (choice.get("message") or {}).get("content")
    finish_reason = choice.get("finish_reason")
    if msg_content != text:
        reasons.append("final_answer_mismatch")
    if finish_reason == "length":
        reasons.append("length_limited_cap_hit")
    elif finish_reason != "stop":
        reasons.append(f"non_stop_finish:{finish_reason}")
    if "\ufffd" in text:
        reasons.append("replacement_character")
    if "\x00" in text:
        reasons.append("nul")
    if "Ġ" in text or "Ċ" in text:
        reasons.append("tokenizer_marker")
    if ROLE_RE.search(text):
        reasons.append("role_continuation")
    return reasons


def audit_cell_on_disk(label: str, model: str, revision: str) -> dict:
    report = {"label": label, "model": model, "revision": revision, "probes": {}, "issues": []}
    for probe, expected_ids in [("freeflow", EXPECTED_FREEFLOW), ("values", EXPECTED_VALUES)]:
        folder = CORPUS_ROOT / "data" / f"traces_{probe}" / (f"freeflow_{label}" if probe == "freeflow" else label)
        paths = sorted(folder.glob("*.json")) if folder.is_dir() else []
        found_ids = {p.stem for p in paths}
        missing = sorted(expected_ids - found_ids)
        extra = sorted(found_ids - expected_ids)
        if missing:
            report["issues"].append({"probe": probe, "missing_count": len(missing), "sample": missing[:5]})
        if extra:
            report["issues"].append({"probe": probe, "extra_count": len(extra), "sample": extra[:5]})
        good = 0
        for path in paths:
            data = json.loads(path.read_text())
            text = data.get("result", "")
            choice = ((data.get("raw") or {}).get("choices") or [{}])[0]
            reasons = []
            if data.get("error"):
                reasons.append("error_field_present")
            reasons.extend(check_trace_fidelity(text, choice))
            dep = data.get("local_deployment") or {}
            if dep.get("model_revision") != revision or data.get("model") != model:
                reasons.append("provenance_mismatch")
            if reasons:
                report["issues"].append({"trace": str(path.relative_to(CORPUS_ROOT)), "reasons": reasons})
            else:
                good += 1
        report["probes"][probe] = {"files": len(paths), "expected": len(expected_ids), "fidelity_pass": good}
    report["publication_ready_raw"] = not report["issues"]
    return report


def wait_ready(base: str, token: str, deadline: float, tunnel_proc: subprocess.Popen) -> list[str]:
    while time.time() < deadline:
        if tunnel_proc.poll() is not None:
            raise RuntimeError(f"SSH tunnel exited early with code {tunnel_proc.returncode}")
        try:
            req = urllib.request.Request(base + "/models", headers={"Authorization": "Bearer " + token})
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    body = json.load(r)
                    return [m.get("id", "") for m in body.get("data", [])]
        except (urllib.error.URLError, OSError, ValueError):
            pass
        time.sleep(5)
    raise TimeoutError("vLLM did not answer /v1/models before the ready deadline")


def run_preflight(base: str, token: str, model: str, ff_max: int, val_max: int, stop: str | None) -> list[dict]:
    results = []
    for cond, kind, prompt in PREFLIGHT_PROBES:
        max_toks = ff_max if kind == "freeflow" else val_max
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_toks,
            "temperature": 1.0,
        }
        if stop:
            payload["stop"] = stop
        req = urllib.request.Request(
            base + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            resp = json.load(r)
        choice = resp["choices"][0]
        text = choice["message"].get("content") or ""
        usage = resp.get("usage") or {}
        reasons = check_trace_fidelity(text, choice)
        summary = {
            "condition": cond,
            "probe": kind,
            "prompt_tokens": usage.get("prompt_tokens"),
            "max_tokens_sent": max_toks,
            "completion_tokens": usage.get("completion_tokens"),
            "finish_reason": choice.get("finish_reason"),
            "issues": reasons,
            "preview": text[:140],
        }
        results.append(summary)
        if reasons:
            raise RuntimeError(f"Preflight failed on {cond}: {json.dumps(summary, ensure_ascii=False)}")
    return results


def compute_budgets(a) -> tuple[int, int]:
    ff_max = a.freeflow_max_tokens
    val_max = a.values_max_tokens
    if a.max_context is not None:
        safe_ceiling = a.max_context - a.prompt_headroom
        if safe_ceiling < 256:
            sys.exit(f"--max-context {a.max_context} leaves <256 output tokens with --prompt-headroom {a.prompt_headroom}")
        if ff_max is not None and ff_max >= a.max_context:
            sys.exit(f"--freeflow-max-tokens {ff_max} must be < --max-context {a.max_context}")
        if val_max is not None and val_max >= a.max_context:
            sys.exit(f"--values-max-tokens {val_max} must be < --max-context {a.max_context}")
        ff_max = ff_max if ff_max is not None else safe_ceiling
        val_max = val_max if val_max is not None else min(2000, safe_ceiling)
    else:
        ff_max = ff_max or 8000
        val_max = val_max or 2000
    return ff_max, val_max


def cmd_usage(_a) -> int:
    res = run_colab(["usage"], check=False)
    sys.stdout.write(res.stdout)
    sys.stderr.write(res.stderr)
    return res.returncode


def cmd_list(_a) -> int:
    res = run_colab(["sessions"], check=False)
    sys.stdout.write(res.stdout)
    sys.stderr.write(res.stderr)
    return res.returncode


def cmd_sweep(a) -> int:
    res = run_colab(["sessions"])
    lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip().startswith("[")]
    targets = []
    for ln in lines:
        name = ln.split("]", 1)[0].lstrip("[")
        if name.startswith(NAME_PREFIX) or (a.include_orphans and name == "?"):
            targets.append((name, ln))
    if not targets:
        print("no capture sessions")
        return 0
    rc = 0
    for name, ln in targets:
        print(("stopping " if a.go else "would stop ") + ln)
        if a.go and name != "?":
            stop_res = run_colab(["stop", "-s", name], check=False)
            if stop_res.returncode != 0:
                sys.stderr.write(stop_res.stderr)
                rc = 1
    return rc


def cmd_audit(a) -> int:
    rep = audit_cell_on_disk(a.label, a.model, a.revision)
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    return 0 if rep["publication_ready_raw"] else 1


def cmd_run(a) -> int:
    if a.dtype not in ("bfloat16", "float16", "float32"):
        sys.exit("--dtype must be an explicit native precision (bfloat16, float16, or float32), never auto or quantized")
    if a.gpu.upper() == "T4" and a.dtype == "bfloat16":
        sys.exit("Refusing T4 for bfloat16: T4 (sm_75) lacks native BF16 support; use L4/A100/H100/G4")

    ff_max, val_max = compute_budgets(a)
    session_name = NAME_PREFIX + a.label[:40]
    plan = {
        "session": session_name,
        "gpu": a.gpu.upper(),
        "high_mem": a.high_mem,
        "model": a.model,
        "revision": a.revision,
        "dtype": a.dtype,
        "max_context": a.max_context,
        "freeflow_max_tokens": ff_max,
        "values_max_tokens": val_max,
        "max_hours": a.max_hours,
        "min_ccu": a.min_ccu,
        "vllm_spec": a.vllm_spec,
        "transformers_spec": a.transformers_spec,
        "preflight_only": a.preflight_only,
        "label": a.label,
    }
    print(json.dumps(plan, indent=2))
    if not a.go:
        print("dry run: nothing allocated (pass --go to execute)")
        return 0

    usage_before_raw = run_colab(["usage"]).stdout
    usage_before = parse_usage(usage_before_raw)
    print("CCU preflight:", usage_before)
    if usage_before.get("balance_ccu", 0.0) < a.min_ccu:
        sys.exit(f"CCU balance {usage_before.get('balance_ccu')} is below --min-ccu {a.min_ccu}")
    if not a.allow_concurrent and usage_before.get("active_assignments", 0) > 0:
        sys.exit("Active Colab assignment(s) already present; run `list` / `sweep` or pass --allow-concurrent")

    token = secrets.token_urlsafe(24)
    started = time.time()
    tunnel_proc = None
    rc = 1
    with tempfile.TemporaryDirectory(prefix="colab-capture-") as tmpdir:
        cfg_path = str(Path(tmpdir) / "colab-state.json")
        new_args = ["new", "-s", session_name, "--gpu", a.gpu.upper()]
        if a.high_mem:
            new_args.append("--high-mem")
        run_colab(new_args, config_path=cfg_path)
        try:
            run_colab(
                ["install", "-s", session_name, a.vllm_spec, a.transformers_spec, "huggingface_hub"],
                config_path=cfg_path,
            )
            # Stage weights first; if HF_TOKEN is present for a gated model, pass it ONLY to download, never to vllm serve.
            dl_code = (
                "import os; from huggingface_hub import snapshot_download; "
                f"p = snapshot_download({a.model!r}, revision={a.revision!r}, token=os.environ.get('HF_TOKEN') or None); "
                "print('staged:', p)"
            )
            exec_args = ["exec", "-s", session_name]
            if os.environ.get("HF_TOKEN"):
                exec_args += ["--env", f"HF_TOKEN={os.environ['HF_TOKEN']}"]
            dl_proc = subprocess.run(
                [colab_bin(), "--auth=adc", "--config", cfg_path, *exec_args],
                input=dl_code,
                text=True,
                env=colab_env(),
                check=True,
            )

            serve_cmd = [
                "vllm", "serve", a.model,
                "--revision", a.revision,
                "--dtype", a.dtype,
                "--host", "127.0.0.1",
                "--port", "8000",
                "--api-key", token,
            ]
            if a.max_context:
                serve_cmd += ["--max-model-len", str(a.max_context)]
            if a.trust_remote_code:
                serve_cmd.append("--trust-remote-code")
            max_secs = int(a.max_hours * 3600)
            start_code = (
                "import os, subprocess; "
                "env = {k: v for k, v in os.environ.items() if k != 'HF_TOKEN'}; "
                "env['HF_HUB_OFFLINE'] = '1'; "
                f"subprocess.Popen(['timeout', '{max_secs}', *{serve_cmd!r}], "
                "env=env, stdout=open('/content/vllm.log', 'w'), stderr=subprocess.STDOUT)"
            )
            subprocess.run(
                [colab_bin(), "--auth=adc", "--config", cfg_path, "exec", "-s", session_name],
                input=start_code,
                text=True,
                env=colab_env(),
                check=True,
            )

            local_port = pick_free_port()
            proxy_cmd = shlex.join([colab_bin(), "--auth=adc", "--config", cfg_path, "ssh", "--proxy-mode", "-s", session_name])
            ssh_cmd = [
                "ssh", "-N",
                "-L", f"127.0.0.1:{local_port}:127.0.0.1:8000",
                "-o", f"ProxyCommand={proxy_cmd}",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "ExitOnForwardFailure=yes",
                "-o", "ServerAliveInterval=20",
                "root@colab-runtime",
            ]
            tunnel_proc = subprocess.Popen(ssh_cmd, env=colab_env(), stdin=subprocess.DEVNULL)
            base = f"http://127.0.0.1:{local_port}/v1"
            wait_ready(base, token, started + a.ready_minutes * 60, tunnel_proc)
            print(f"vLLM ready over loopback tunnel after {int(time.time() - started)}s")

            preflight = run_preflight(base, token, a.model, ff_max, val_max, a.stop)
            print("Preflight 3/3 passed:", json.dumps(preflight, indent=2, ensure_ascii=False))
            if a.preflight_only:
                rc = 0
                return rc

            cap_env = {
                k: v for k, v in os.environ.items()
                if k not in ("GOOGLE_APPLICATION_CREDENTIALS", "HF_TOKEN", "RUNPOD_API_KEY", "OPENROUTER_API_KEY")
            }
            cap_env.update({
                "LOCAL_OPENAI_BASE_URL": base + "/chat/completions",
                "LOCAL_OPENAI_API_KEY": token,
                "LOCAL_MODEL_RUNTIME": "vllm-openai (colab)",
                "LOCAL_MODEL_RUNTIME_VERSION": f"{a.vllm_spec}; {a.transformers_spec}",
                "LOCAL_MODEL_REVISION": a.revision,
                "LOCAL_MODEL_WEIGHT_PRECISION": a.dtype,
                "LOCAL_MODEL_HARDWARE": f"Google Colab 1x {a.gpu.upper()}",
            })
            if a.stop:
                cap_env["LOCAL_MODEL_STOP"] = a.stop

            py = os.environ.get("MPC_PY") or sys.executable
            ff_cmd = [py, str(SCRIPTS / "run_freeflow_multi.py"), "local-openai", a.model,
                      "--label", a.label, "--workers", str(a.workers), "--max-tokens", str(ff_max)]
            print("$", " ".join(ff_cmd))
            subprocess.run(ff_cmd, env=cap_env, check=True)

            if not a.freeflow_only:
                val_cmd = [py, str(SCRIPTS / "run_values_v2.py"), "local-openai", a.model,
                           "--label", a.label, "--workers", str(a.workers), "--max-tokens", str(val_max)]
                print("$", " ".join(val_cmd))
                subprocess.run(val_cmd, env=cap_env, check=True)
                audit = audit_cell_on_disk(a.label, a.model, a.revision)
                print("Post-capture audit:", json.dumps(audit, indent=2, ensure_ascii=False))
                if not audit["publication_ready_raw"]:
                    raise RuntimeError("Post-capture strict fidelity audit reported issues")
            rc = 0
        finally:
            if tunnel_proc is not None and tunnel_proc.poll() is None:
                tunnel_proc.terminate()
                try:
                    tunnel_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    tunnel_proc.kill()
            stop_res = run_colab(["stop", "-s", session_name], config_path=cfg_path, check=False)
            hours = (time.time() - started) / 3600
            usage_after = parse_usage(run_colab(["usage"], check=False).stdout)
            delta = None
            if "balance_ccu" in usage_before and "balance_ccu" in usage_after:
                delta = round(usage_before["balance_ccu"] - usage_after["balance_ccu"], 2)
            print(
                f"stop {session_name}: {'ok' if stop_res.returncode == 0 else 'FAILED'}; "
                f"ran {hours:.2f} h; CCU delta={delta} (after={usage_after})"
            )
    return rc


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="sub", required=True)

    sub.add_parser("usage")
    sub.add_parser("list")

    sw = sub.add_parser("sweep")
    sw.add_argument("--go", action="store_true")
    sw.add_argument("--include-orphans", action="store_true")

    au = sub.add_parser("audit")
    au.add_argument("--label", required=True)
    au.add_argument("--model", required=True)
    au.add_argument("--revision", required=True)

    r = sub.add_parser("run")
    r.add_argument("--model", required=True, help="HuggingFace repo id")
    r.add_argument("--revision", required=True, help="40-char git commit SHA of the checkpoint")
    r.add_argument("--label", required=True, help="Output folder label")
    r.add_argument("--gpu", required=True, choices=["T4", "L4", "G4", "A100", "H100", "t4", "l4", "g4", "a100", "h100"])
    r.add_argument("--high-mem", action="store_true")
    r.add_argument("--dtype", default="bfloat16", help="Explicit native precision: bfloat16, float16, or float32")
    r.add_argument("--max-context", type=int, help="Model native context window (e.g. 4096 for 2023 checkpoints)")
    r.add_argument("--prompt-headroom", type=int, default=32, help="Tokens reserved for templated prompt when --max-context is set")
    r.add_argument("--freeflow-max-tokens", type=int, help="Explicit freeflow max_tokens override (e.g. 4075)")
    r.add_argument("--values-max-tokens", type=int, help="Explicit values max_tokens override (default 2000)")
    r.add_argument("--stop", help="Optional official turn stop string passed as LOCAL_MODEL_STOP")
    r.add_argument("--max-hours", type=float, default=2.0, help="Hard wall-time ceiling for vllm serve inside the VM")
    r.add_argument("--min-ccu", type=float, default=15.0, help="Refuse launch if CCU balance is below this floor")
    r.add_argument("--ready-minutes", type=float, default=15.0)
    r.add_argument("--workers", type=int, default=6)
    r.add_argument("--vllm-spec", default=DEFAULT_VLLM_SPEC)
    r.add_argument("--transformers-spec", default=DEFAULT_TRANSFORMERS_SPEC)
    r.add_argument("--trust-remote-code", action="store_true")
    r.add_argument("--allow-concurrent", action="store_true")
    r.add_argument("--preflight-only", action="store_true")
    r.add_argument("--freeflow-only", action="store_true")
    r.add_argument("--go", action="store_true", help="Actually allocate the Colab VM (omit for dry run)")

    a = p.parse_args()
    sys.exit({"usage": cmd_usage, "list": cmd_list, "sweep": cmd_sweep, "audit": cmd_audit, "run": cmd_run}[a.sub](a))


if __name__ == "__main__":
    main()
