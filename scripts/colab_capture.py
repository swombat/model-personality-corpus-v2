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
import signal
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
DEFAULT_TRANSFORMERS_SPEC = "transformers==5.22.2"
DEFAULT_TOKENIZERS_SPEC = "tokenizers==0.23.3"
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
    soulshouse_shim = Path.home() / "state" / "tools" / "bin" / "colab-soulshouse"
    if soulshouse_shim.is_file():
        return str(soulshouse_shim)
    default_tool = Path.home() / "state" / "tools" / "colab-py" / "bin" / "colab"
    if default_tool.is_file():
        return str(default_tool)
    return "colab"


def mpc_python_bin() -> str:
    override = os.environ.get("MPC_PY")
    if override:
        return override
    default_venv = Path.home() / "state" / "tools" / "mpc-py" / "bin" / "python3"
    if default_venv.is_file():
        return str(default_venv)
    return sys.executable


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


EXEC_SENTINEL = "__COLAB_EXEC_OK__:"


def run_remote_python(
    ssh_base: list[str],
    body_code: str,
    *,
    extra_env: dict[str, str] | None = None,
    step_label: str = "remote_exec",
) -> dict:
    """Run Python directly inside the Colab VM over the multiplexed OpenSSH ControlMaster
    (bypassing Jupyter `colab exec` websockets and `colab_request` hooks completely)."""
    env_prelude = ""
    for k, v in (extra_env or {}).items():
        env_prelude += f"import os as _os; _os.environ[{k!r}] = {v!r}\n"
    wrapped = (
        env_prelude
        + "import json as _json\n"
        "def _colab_step():\n"
        + "\n".join("    " + ln for ln in body_code.splitlines())
        + "\n_res = _colab_step()\n"
        + f"print({EXEC_SENTINEL!r} + _json.dumps(_res if _res is not None else {{}}), flush=True)\n"
    )
    cmd = [*ssh_base, "root@colab-runtime", "python3", "-u", "-"]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=colab_env(),
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write(wrapped)
    proc.stdin.close()
    captured: list[str] = []
    result_obj: dict | None = None
    for raw_line in proc.stdout:
        line = raw_line.rstrip("\n")
        if line.startswith(EXEC_SENTINEL):
            result_obj = json.loads(line[len(EXEC_SENTINEL):])
        else:
            print(f"[{step_label}] {line}", flush=True)
            captured.append(line)
    rc = proc.wait()
    if rc == 0 and result_obj is not None:
        return result_obj
    tail = "\n".join(captured[-40:])
    raise RuntimeError(f"{step_label} failed (rc={rc}).\nOUTPUT:\n{tail}")


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


def parse_session_endpoints(text: str) -> list[str]:
    endpoints = []
    for raw in text.splitlines():
        ln = raw.strip()
        if ln.startswith("[") and "]" in ln:
            rest = ln.split("]", 1)[1].strip()
            ep = rest.split("|", 1)[0].strip()
            if ep:
                endpoints.append(ep)
    return endpoints


def read_assigned_metadata(cfg_path: str, session_name: str) -> dict:
    p = Path(cfg_path)
    if not p.is_file():
        return {}
    data = json.loads(p.read_text())
    entry = data.get(session_name) or {}
    return {
        k: entry.get(k)
        for k in ("name", "endpoint", "accelerator", "variant", "machine_shape")
        if entry.get(k) is not None
    }


def direct_unassign_endpoint(endpoint: str) -> tuple[bool, str]:
    shim = Path(colab_bin())
    py_interp = str(Path.home() / "state" / "tools" / "colab-py" / "bin" / "python3")
    if not Path(py_interp).is_file():
        py_interp = sys.executable
    code = (
        "import importlib.machinery, importlib.util, sys\n"
        f"loader = importlib.machinery.SourceFileLoader('colab_soulshouse', {str(shim)!r})\n"
        "spec = importlib.util.spec_from_loader(loader.name, loader)\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "loader.exec_module(mod)\n"
        "from colab_cli.client import Client, Prod\n"
        "client = Client(Prod(), mod._make_session())\n"
        f"client.unassign({endpoint!r})\n"
        "print('unassigned:' + " + repr(endpoint) + ")\n"
    )
    res = subprocess.run([py_interp, "-c", code], env=colab_env(), text=True, capture_output=True)
    return (res.returncode == 0, (res.stdout + " " + res.stderr).strip())


def adopt_server_endpoint(endpoint: str, session_name: str, cfg_path: str) -> dict:
    shim = Path(colab_bin())
    py_interp = str(Path.home() / "state" / "tools" / "colab-py" / "bin" / "python3")
    if not Path(py_interp).is_file():
        py_interp = sys.executable
    code = (
        "import importlib.machinery, importlib.util, json, sys\n"
        f"loader = importlib.machinery.SourceFileLoader('colab_soulshouse', {str(shim)!r})\n"
        "spec = importlib.util.spec_from_loader(loader.name, loader)\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "loader.exec_module(mod)\n"
        "from colab_cli.client import Client, Prod\n"
        "from colab_cli.state import SessionState, StateStore\n"
        "client = Client(Prod(), mod._make_session())\n"
        f"matches = [a for a in client.list_assignments() if a.endpoint == {endpoint!r}]\n"
        "if not matches:\n"
        f"    sys.exit('Active assignment not found on server: ' + {endpoint!r})\n"
        "a = matches[0]\n"
        "s = SessionState(\n"
        f"    name={session_name!r},\n"
        "    token=a.runtime_proxy_info.token,\n"
        "    url=a.runtime_proxy_info.url,\n"
        "    endpoint=a.endpoint,\n"
        "    token_expires_at=a.runtime_proxy_info.expires_at(),\n"
        "    variant=a.variant.name,\n"
        "    accelerator=a.accelerator.value,\n"
        "    machine_shape=a.machine_shape.name,\n"
        ")\n"
        f"StateStore({cfg_path!r}).add(s)\n"
        "print(json.dumps({'name': s.name, 'endpoint': s.endpoint, 'accelerator': s.accelerator, 'variant': s.variant, 'machine_shape': s.machine_shape}))\n"
    )
    res = subprocess.run([py_interp, "-c", code], env=colab_env(), text=True, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"adopt_server_endpoint failed (rc={res.returncode}): {res.stdout} {res.stderr}")
    return json.loads(res.stdout.strip().splitlines()[-1])


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


def audit_cell_on_disk(
    label: str,
    model: str,
    revision: str,
    *,
    freeflow_only: bool = False,
    values_only: bool = False,
) -> dict:
    report = {"label": label, "model": model, "revision": revision, "probes": {}, "issues": []}
    probe_specs = []
    if not values_only or (CORPUS_ROOT / "data" / "traces_freeflow" / f"freeflow_{label}").is_dir():
        probe_specs.append(("freeflow", EXPECTED_FREEFLOW))
    if not freeflow_only or (CORPUS_ROOT / "data" / "traces_values" / label).is_dir():
        probe_specs.append(("values", EXPECTED_VALUES))
    for probe, expected_ids in probe_specs:
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


def wait_ready(
    base: str,
    token: str,
    deadline: float,
    tunnel_proc: subprocess.Popen,
    *,
    ssh_base: list[str] | None = None,
    vllm_pid: int | None = None,
) -> list[str]:
    polls = 0
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
        polls += 1
        if ssh_base and vllm_pid and polls % 3 == 0:
            chk = subprocess.run(
                [*ssh_base, "root@colab-runtime", f"kill -0 {vllm_pid} 2>/dev/null"],
                env=colab_env(),
                stdin=subprocess.DEVNULL,
                capture_output=True,
            )
            if chk.returncode != 0:
                raise RuntimeError(f"vllm serve (pid={vllm_pid}) exited before /v1/models became ready")
        time.sleep(5)
    raise TimeoutError("vLLM did not answer /v1/models before the ready deadline")


def build_capture_env(
    base: str,
    token: str,
    model_rev: str,
    dtype: str,
    runtime_ver: str,
    hardware_label: str,
    stop: str | None,
) -> dict[str, str]:
    stripped = {
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_COLAB_ACCESS_TOKEN",
        "SOULSHOUSE_BEARER_TOKEN",
        "HELIXKIT_BEARER_TOKEN",
        "HF_TOKEN",
        "RUNPOD_API_KEY",
        "OPENROUTER_API_KEY",
    }
    cap_env = {k: v for k, v in os.environ.items() if k not in stripped}
    cap_env.update({
        "LOCAL_OPENAI_BASE_URL": base + "/chat/completions",
        "LOCAL_OPENAI_API_KEY": token,
        "LOCAL_MODEL_RUNTIME": "vllm-openai (colab)",
        "LOCAL_MODEL_RUNTIME_VERSION": runtime_ver,
        "LOCAL_MODEL_REVISION": model_rev,
        "LOCAL_MODEL_WEIGHT_PRECISION": dtype,
        "LOCAL_MODEL_HARDWARE": hardware_label,
    })
    if stop:
        cap_env["LOCAL_MODEL_STOP"] = stop
    return cap_env


def run_preflight(
    py: str,
    cap_env: dict[str, str],
    model: str,
    ff_max: int,
    val_max: int,
    preflight_dir: Path,
) -> list[dict]:
    """Run SHORT, LONG, and G1 through `run_freeflow_multi.call_local_openai` (exact same
    request shape and default publisher sampling as full capture) and persist every raw trace."""
    preflight_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for cond, kind, prompt in PREFLIGHT_PROBES:
        max_toks = ff_max if kind == "freeflow" else val_max
        helper_code = (
            f"import json, sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); "
            "from run_freeflow_multi import call_local_openai; "
            "t0 = time.time(); "
            f"res = call_local_openai({model!r}, {prompt!r}, max_tokens={max_toks}); "
            "res['duration_ms'] = int((time.time() - t0) * 1000); "
            "res['provider'] = 'local-openai'; "
            f"res['model_requested'] = {model!r}; "
            f"res['condition'] = {cond!r}; "
            f"res['probe'] = {kind!r}; "
            f"res['prompt'] = {prompt!r}; "
            "print(json.dumps(res))"
        )
        proc = subprocess.run([py, "-c", helper_code], env=cap_env, text=True, capture_output=True, check=True)
        trace = json.loads(proc.stdout)
        resp = trace.get("raw") or {}
        choice = (resp.get("choices") or [{}])[0]
        text = trace.get("result") or ""
        usage = resp.get("usage") or {}
        reasons = check_trace_fidelity(text, choice)
        trace["preflight_issues"] = reasons
        out_path = preflight_dir / f"{cond}.json"
        out_path.write_text(json.dumps(trace, indent=2, ensure_ascii=False))
        summary = {
            "condition": cond,
            "probe": kind,
            "saved_to": str(out_path),
            "prompt_tokens": usage.get("prompt_tokens"),
            "max_tokens_sent": max_toks,
            "completion_tokens": usage.get("completion_tokens"),
            "finish_reason": choice.get("finish_reason"),
            "issues": reasons,
            "preview": text[:140],
        }
        results.append(summary)
        (preflight_dir / "summary.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
        if reasons:
            raise RuntimeError(f"Preflight failed on {cond}: {json.dumps(summary, ensure_ascii=False)}")

    # Verify non-greedy sampling on a repeat of SHORT before running 25x rollouts.
    short_prompt = PREFLIGHT_PROBES[0][2]
    rep_code = (
        f"import json, sys; sys.path.insert(0, {str(SCRIPTS)!r}); "
        "from run_freeflow_multi import call_local_openai; "
        f"print(json.dumps(call_local_openai({model!r}, {short_prompt!r}, max_tokens=128)))"
    )
    rep_proc = subprocess.run([py, "-c", rep_code], env=cap_env, text=True, capture_output=True, check=True)
    rep_trace = json.loads(rep_proc.stdout)
    first_short = json.loads((preflight_dir / "SHORT.json").read_text()).get("result") or ""
    second_short = rep_trace.get("result") or ""
    if second_short.strip() == first_short.strip() or (
        len(first_short) >= 80 and len(second_short) >= 80 and first_short[:80] == second_short[:80] and first_short == second_short
    ):
        raise RuntimeError("Preflight failed: repeat SHORT probe produced identical text (greedy decoding suspected)")
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
    rep = audit_cell_on_disk(a.label, a.model, a.revision, freeflow_only=a.freeflow_only, values_only=a.values_only)
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    return 0 if rep["publication_ready_raw"] else 1


def cmd_run(a) -> int:
    if a.freeflow_only and a.values_only:
        sys.exit("Pass at most one of --freeflow-only and --values-only")
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
        "tokenizers_spec": a.tokenizers_spec,
        "preflight_only": a.preflight_only,
        "freeflow_only": a.freeflow_only,
        "values_only": a.values_only,
        "label": a.label,
    }
    print(json.dumps(plan, indent=2))
    if not a.go:
        print("dry run: nothing allocated (pass --go to execute)")
        return 0

    py = mpc_python_bin()
    py_check = subprocess.run([py, "-c", "import httpx"], capture_output=True, text=True)
    if py_check.returncode != 0:
        sys.exit(f"Local capture Python ({py}) cannot import httpx: {py_check.stderr.strip()}")

    usage_before_raw = run_colab(["usage"]).stdout
    usage_before = parse_usage(usage_before_raw)
    print("CCU preflight:", usage_before)
    if usage_before.get("balance_ccu", 0.0) < a.min_ccu:
        sys.exit(f"CCU balance {usage_before.get('balance_ccu')} is below --min-ccu {a.min_ccu}")
    if not a.allow_concurrent and not a.adopt_endpoint and usage_before.get("active_assignments", 0) > 0:
        sys.exit("Active Colab assignment(s) already present; run `list` / `sweep` or pass --allow-concurrent")

    token = secrets.token_hex(24)
    started = time.time()
    tunnel_proc = None
    rc = 1
    prev_sigterm = signal.getsignal(signal.SIGTERM)

    def _on_sigterm(signum, _frame):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, _on_sigterm)
    state_dir = Path.home() / "state" / "colab-sessions"
    state_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(state_dir, 0o700)
    cfg_path = str(state_dir / f"{session_name}-{os.getpid()}.json")
    assigned_meta: dict = {}
    with tempfile.TemporaryDirectory(prefix="colab-capture-") as tmpdir:
        ssh_key = str(Path(tmpdir) / "id_ed25519")
        ctl_sock = str(Path(tmpdir) / "ssh-ctl.sock")
        subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-f", ssh_key, "-q"], check=True)
        preflight_dir = CORPUS_ROOT / "logs" / "colab_preflight" / a.label
        preflight_dir.mkdir(parents=True, exist_ok=True)

        if a.adopt_endpoint:
            assigned_meta = adopt_server_endpoint(a.adopt_endpoint, session_name, cfg_path)
        else:
            new_args = ["new", "-s", session_name, "--gpu", a.gpu.upper()]
            if a.high_mem:
                new_args.append("--high-mem")
            new_res = run_colab(new_args, config_path=cfg_path, check=False)
            if new_res.returncode != 0:
                for fp in (cfg_path, cfg_path + ".lock"):
                    Path(fp).unlink(missing_ok=True)
                raise RuntimeError(f"colab new failed (rc={new_res.returncode}): {new_res.stdout} {new_res.stderr}")
            assigned_meta = read_assigned_metadata(cfg_path, session_name)
        (preflight_dir / "assignment.json").write_text(
            json.dumps(
                {
                    **assigned_meta,
                    "pid": os.getpid(),
                    "started_epoch": round(started, 3),
                },
                indent=2,
            )
        )
        print("Assigned Colab VM:", json.dumps(assigned_meta))
        try:
            local_port = pick_free_port()
            proxy_cmd = shlex.join([colab_bin(), "--auth=adc", "--config", cfg_path, "ssh", "--proxy-mode", "--identity", ssh_key, "-s", session_name])
            ssh_base = [
                "ssh",
                "-i", ssh_key,
                "-o", "IdentitiesOnly=yes",
                "-o", f"ProxyCommand={proxy_cmd}",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", f"ControlPath={ctl_sock}",
                "-o", "ServerAliveInterval=20",
                "-o", "ServerAliveCountMax=6",
            ]
            tunnel_proc = subprocess.Popen(
                [
                    *ssh_base,
                    "-M",
                    "-N",
                    "-L", f"127.0.0.1:{local_port}:127.0.0.1:8000",
                    "-o", "ExitOnForwardFailure=yes",
                    "root@colab-runtime",
                ],
                env=colab_env(),
                stdin=subprocess.DEVNULL,
            )
            ssh_deadline = time.time() + 90
            while not Path(ctl_sock).exists():
                if tunnel_proc.poll() is not None:
                    raise RuntimeError(f"SSH master exited before socket ready (rc={tunnel_proc.returncode})")
                if time.time() >= ssh_deadline:
                    raise TimeoutError("Timed out waiting for SSH ControlMaster socket")
                time.sleep(1)
            print(f"SSH ControlMaster + loopback tunnel established on 127.0.0.1:{local_port} after {int(time.time() - started)}s")

            pkgs = [a.vllm_spec, a.transformers_spec, a.tokenizers_spec, "huggingface_hub"]
            install_code = (
                "import shutil, subprocess, sys\n"
                f"pkgs = {pkgs!r}\n"
                "if shutil.which('uv'):\n"
                "    subprocess.check_call(['uv', 'pip', 'install', '--system', *pkgs])\n"
                "else:\n"
                "    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', *pkgs])\n"
                "import torch, transformers, tokenizers, vllm\n"
                "gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total,memory.free,driver_version', '--format=csv,noheader'], text=True).strip()\n"
                "disk = subprocess.check_output(['df', '-h', '/content'], text=True).strip()\n"
                "import os\n"
                "leaked = [k for k in os.environ if k.startswith(('GOOGLE_', 'SOULSHOUSE_', 'HELIXKIT_'))]\n"
                "gcloud_present = os.path.exists('/root/.config/gcloud/application_default_credentials.json')\n"
                "return {\n"
                "    'gpu': gpu,\n"
                "    'disk': disk,\n"
                "    'vllm': vllm.__version__,\n"
                "    'transformers': transformers.__version__,\n"
                "    'tokenizers': tokenizers.__version__,\n"
                "    'torch': torch.__version__,\n"
                "    'leaked_env_keys': leaked,\n"
                "    'gcloud_adc_present': gcloud_present,\n"
                "}\n"
            )
            vm_info = run_remote_python(ssh_base, install_code, step_label="install_and_probe")
            if vm_info.get("leaked_env_keys") or vm_info.get("gcloud_adc_present"):
                raise RuntimeError(f"Credential boundary violation inside VM: {vm_info}")
            print("VM environment verified:", json.dumps(vm_info))

            # Stage weights first; if HF_TOKEN is present for a gated model, pass it ONLY to download, never to vllm serve.
            dl_code = (
                "import glob, json, os, struct, zipfile\n"
                "from pathlib import Path\n"
                "from huggingface_hub import HfApi, snapshot_download\n"
                "tok = os.environ.get('HF_TOKEN') or None\n"
                f"info = HfApi().model_info({a.model!r}, revision={a.revision!r}, token=tok)\n"
                "rfiles = [s.rfilename for s in (info.siblings or [])]\n"
                "has_st = any(fn.endswith('.safetensors') for fn in rfiles)\n"
                "ignore = ['pytorch_model*.bin', '*.msgpack', '*.h5', 'consolidated*.pth'] if has_st else None\n"
                f"p = Path(snapshot_download({a.model!r}, revision={a.revision!r}, token=tok, ignore_patterns=ignore))\n"
                "dtypes = set()\n"
                "for st in sorted(p.glob('*.safetensors'))[:2]:\n"
                "    with open(st, 'rb') as f:\n"
                "        n = struct.unpack('<Q', f.read(8))[0]\n"
                "        hdr = json.loads(f.read(n))\n"
                "    for k, v in hdr.items():\n"
                "        if k != '__metadata__' and isinstance(v, dict) and 'dtype' in v:\n"
                "            dtypes.add(v['dtype'])\n"
                "for bf in sorted(p.glob('pytorch_model*.bin'))[:2]:\n"
                "    if zipfile.is_zipfile(bf):\n"
                "        with zipfile.ZipFile(bf) as zf:\n"
                "            for nm in zf.namelist():\n"
                "                if nm.endswith('data.pkl'):\n"
                "                    raw = zf.read(nm).decode('latin1', 'ignore')\n"
                "                    for s in ('BFloat16Storage', 'HalfStorage', 'FloatStorage', 'ByteStorage', 'CharStorage'):\n"
                "                        if s in raw:\n"
                "                            dtypes.add(s)\n"
                "cfg = json.loads((p / 'config.json').read_text()) if (p / 'config.json').exists() else {}\n"
                "gen = json.loads((p / 'generation_config.json').read_text()) if (p / 'generation_config.json').exists() else {}\n"
                "tmpl_probe = {}\n"
                "try:\n"
                "    from transformers import AutoTokenizer\n"
                "    tz = AutoTokenizer.from_pretrained(str(p))\n"
                "    s = tz.apply_chat_template([{'role': 'user', 'content': 'Write freely about whatever you want for 250 words.'}], tokenize=False, add_generation_prompt=True)\n"
                "    ids = tz.apply_chat_template([{'role': 'user', 'content': 'Write freely about whatever you want for 250 words.'}], tokenize=True, add_generation_prompt=True)\n"
                "    tmpl_probe['hf_rendered'] = s\n"
                "    tmpl_probe['hf_token_count'] = len(ids) if isinstance(ids, list) else len(getattr(ids, 'input_ids', []))\n"
                "except Exception as e:\n"
                "    tmpl_probe['hf_err'] = str(e)\n"
                "if (p / 'tokenizer.model.v1').exists():\n"
                "    try:\n"
                "        from mistral_common.tokens.tokenizers.mistral import MistralTokenizer\n"
                "        from mistral_common.protocol.instruct.messages import UserMessage\n"
                "        from mistral_common.protocol.instruct.request import ChatCompletionRequest\n"
                "        mt = MistralTokenizer.from_file(str(p / 'tokenizer.model.v1'))\n"
                "        enc = mt.encode_chat_completion(ChatCompletionRequest(messages=[UserMessage(content='Write freely about whatever you want for 250 words.')]))\n"
                "        tmpl_probe['mistral_common_text'] = enc.text\n"
                "        tmpl_probe['mistral_common_token_count'] = len(enc.tokens)\n"
                "    except Exception as e:\n"
                "        tmpl_probe['mistral_common_err'] = str(e)\n"
                "return {'staged_path': str(p), 'has_safetensors': has_st, 'inspected_tensor_dtypes': sorted(dtypes), 'torch_dtype': cfg.get('torch_dtype'), 'max_position_embeddings': cfg.get('max_position_embeddings'), 'sliding_window': cfg.get('sliding_window'), 'generation_config': gen, 'template_probe': tmpl_probe}\n"
            )
            extra_dl = {"HF_TOKEN": os.environ["HF_TOKEN"]} if os.environ.get("HF_TOKEN") else None
            ckpt_info = run_remote_python(ssh_base, dl_code, extra_env=extra_dl, step_label="snapshot_download")
            print("Checkpoint staged & verified:", json.dumps(ckpt_info))
            expected_storage = {"bfloat16": {"BF16", "BFloat16Storage"}, "float16": {"F16", "HalfStorage"}, "float32": {"F32", "FloatStorage"}}[a.dtype]
            found_storage = set(ckpt_info.get("inspected_tensor_dtypes") or [])
            if not (found_storage & expected_storage):
                raise RuntimeError(f"Native precision mismatch: --dtype {a.dtype} vs checkpoint tensors {sorted(found_storage)}")
            tp = ckpt_info.get("template_probe") or {}
            rendered = tp.get("mistral_common_text") or tp.get("hf_rendered") or ""
            if not rendered or ("mistral-7b-instruct-v0.1" in a.model.lower() and ("[INST]" not in rendered or "[/INST]" not in rendered)):
                raise RuntimeError(f"Publisher template gate failed: {tp}")
            (preflight_dir / "vm_manifest.json").write_text(
                json.dumps({"plan": plan, "vm": vm_info, "checkpoint": ckpt_info}, indent=2, ensure_ascii=False)
            )

            serve_cmd = [
                "serve", a.model,
                "--revision", a.revision,
                "--dtype", a.dtype,
                "--host", "127.0.0.1",
                "--port", "8000",
                f"--api-key={token}",
            ]
            if a.max_context:
                serve_cmd += ["--max-model-len", str(a.max_context)]
            if a.trust_remote_code:
                serve_cmd.append("--trust-remote-code")
            max_secs = int(a.max_hours * 3600)
            start_code = (
                "import os, shutil, subprocess, sys\n"
                "from pathlib import Path\n"
                "env = {k: v for k, v in os.environ.items() if k != 'HF_TOKEN'}\n"
                "env['HF_HUB_OFFLINE'] = '1'\n"
                "vllm_bin = shutil.which('vllm') or str(Path(sys.executable).with_name('vllm'))\n"
                "logf = open('/content/vllm.log', 'w')\n"
                f"p = subprocess.Popen(['timeout', '{max_secs}', vllm_bin, *{serve_cmd!r}], env=env, stdin=subprocess.DEVNULL, stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)\n"
                "return {'pid': p.pid, 'vllm_bin': vllm_bin}\n"
            )
            start_info = run_remote_python(ssh_base, start_code, step_label="start_vllm")
            vllm_pid = int(start_info["pid"])

            base = f"http://127.0.0.1:{local_port}/v1"
            try:
                wait_ready(base, token, started + a.ready_minutes * 60, tunnel_proc, ssh_base=ssh_base, vllm_pid=vllm_pid)
            except Exception:
                try:
                    tail = run_remote_python(
                        ssh_base,
                        "from pathlib import Path\np = Path('/content/vllm.log')\nreturn {'vllm_log_tail': p.read_text(errors='replace')[-4000:] if p.exists() else 'missing'}",
                        step_label="read_vllm_log",
                    )
                    print("vLLM startup log tail:", tail.get("vllm_log_tail"), file=sys.stderr)
                except Exception:
                    pass
                raise
            print(f"vLLM ready over loopback tunnel after {int(time.time() - started)}s")
            vllm_meta = run_remote_python(
                ssh_base,
                "from pathlib import Path\n"
                "lines = Path('/content/vllm.log').read_text(errors='replace').splitlines() if Path('/content/vllm.log').exists() else []\n"
                "keep = [ln for ln in lines if any(k in ln.lower() for k in ('sampling', 'tokenizer', 'dtype', 'max_model_len', 'chat_template', 'model weights'))]\n"
                "return {'vllm_startup_highlights': keep[-40:]}\n",
                step_label="inspect_vllm_startup",
            )
            print("vLLM startup highlights:", json.dumps(vllm_meta, ensure_ascii=False))
            (preflight_dir / "vm_manifest.json").write_text(
                json.dumps({"plan": plan, "vm": vm_info, "checkpoint": ckpt_info, "vllm_startup": vllm_meta}, indent=2, ensure_ascii=False)
            )

            gpu_name = (vm_info.get("gpu") or "").split(",")[0].strip() or a.gpu.upper()
            runtime_ver = f"vllm=={vm_info.get('vllm')}; transformers=={vm_info.get('transformers')}; tokenizers=={vm_info.get('tokenizers')}; torch=={vm_info.get('torch')}"
            hardware_label = f"Google Colab 1x {gpu_name}"
            cap_env = build_capture_env(base, token, a.revision, a.dtype, runtime_ver, hardware_label, a.stop)

            preflight = run_preflight(py, cap_env, a.model, ff_max, val_max, preflight_dir)
            print("Preflight 3/3 passed:", json.dumps(preflight, indent=2, ensure_ascii=False))
            if a.preflight_only:
                rc = 0
                return rc

            if not a.values_only:
                ff_cmd = [py, str(SCRIPTS / "run_freeflow_multi.py"), "local-openai", a.model,
                          "--label", a.label, "--n", "25", "--workers", str(a.workers), "--max-tokens", str(ff_max)]
                print("$", " ".join(ff_cmd))
                subprocess.run(ff_cmd, env=cap_env, check=True)

            if not a.freeflow_only:
                val_cmd = [py, str(SCRIPTS / "run_values_v2.py"), "local-openai", a.model,
                           "--label", a.label, "--workers", str(a.workers), "--max-tokens", str(val_max)]
                print("$", " ".join(val_cmd))
                subprocess.run(val_cmd, env=cap_env, check=True)
            audit = audit_cell_on_disk(
                a.label,
                a.model,
                a.revision,
                freeflow_only=a.freeflow_only,
                values_only=a.values_only,
            )
            print("Post-capture audit:", json.dumps(audit, indent=2, ensure_ascii=False))
            if not audit["publication_ready_raw"]:
                raise RuntimeError("Post-capture strict fidelity audit reported issues")
            rc = 0
        finally:
            if a.keep_session and rc == 0 and tunnel_proc is not None and tunnel_proc.poll() is None:
                try:
                    run_remote_python(
                        ssh_base,
                        "import shutil, subprocess\nsubprocess.run(['pkill', '-f', 'vllm'], check=False)\nshutil.rmtree('/root/.cache/huggingface/hub', ignore_errors=True)\nreturn {'cleaned_for_reuse': True}\n",
                        step_label="cleanup_for_reuse",
                    )
                except Exception:
                    pass
            if tunnel_proc is not None and tunnel_proc.poll() is None:
                tunnel_proc.terminate()
                try:
                    tunnel_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    tunnel_proc.kill()
            assigned_ep = assigned_meta.get("endpoint")
            fallback_detail = None
            if a.keep_session and rc == 0:
                stop_cli_rc = None
                sessions_after = run_colab(["sessions"], check=False).stdout
                active_eps = parse_session_endpoints(sessions_after)
                ep_stopped = False
                other_active_eps = [ep for ep in active_eps if ep != assigned_ep]
                for fp in (cfg_path, cfg_path + ".lock"):
                    Path(fp).unlink(missing_ok=True)
            else:
                stop_res = run_colab(["stop", "-s", session_name], config_path=cfg_path, check=False)
                stop_cli_rc = stop_res.returncode
                sessions_after = run_colab(["sessions"], check=False).stdout
                active_eps = parse_session_endpoints(sessions_after)
                if assigned_ep and assigned_ep in active_eps:
                    fb_ok, fallback_detail = direct_unassign_endpoint(assigned_ep)
                    sessions_after = run_colab(["sessions"], check=False).stdout
                    active_eps = parse_session_endpoints(sessions_after)
                ep_stopped = (assigned_ep not in active_eps) if assigned_ep else (stop_res.returncode == 0)
                other_active_eps = [ep for ep in active_eps if ep != assigned_ep]
                if ep_stopped:
                    for fp in (cfg_path, cfg_path + ".lock"):
                        Path(fp).unlink(missing_ok=True)
            hours = (time.time() - started) / 3600
            usage_after = parse_usage(run_colab(["usage"], check=False).stdout)
            delta = None
            if "balance_ccu" in usage_before and "balance_ccu" in usage_after:
                delta = round(usage_before["balance_ccu"] - usage_after["balance_ccu"], 2)
            print(
                f"finish {session_name} (endpoint={assigned_ep}): {'KEPT_FOR_REUSE' if (a.keep_session and rc == 0) else ('stopped' if ep_stopped else 'STOP_FAILED')} "
                f"(other_active={len(other_active_eps)}); ran {hours:.2f} h; "
                f"account CCU delta={delta} (after={usage_after})"
            )
            (preflight_dir / "run_summary.json").write_text(
                json.dumps(
                    {
                        "session": session_name,
                        "endpoint": assigned_ep,
                        "label": a.label,
                        "model": a.model,
                        "revision": a.revision,
                        "rc": rc,
                        "kept_for_reuse": bool(a.keep_session and rc == 0),
                        "stop_ok": ep_stopped,
                        "stop_cli_rc": stop_cli_rc,
                        "fallback_unassign": fallback_detail,
                        "other_active_endpoints_at_stop": other_active_eps,
                        "wall_hours": round(hours, 4),
                        "wall_seconds": round(time.time() - started, 1),
                        "usage_before": usage_before,
                        "usage_after": usage_after,
                        "account_ccu_delta_during_window": delta,
                    },
                    indent=2,
                )
            )
            signal.signal(signal.SIGTERM, prev_sigterm)
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
    au.add_argument("--freeflow-only", action="store_true")
    au.add_argument("--values-only", action="store_true")

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
    r.add_argument("--tokenizers-spec", default=DEFAULT_TOKENIZERS_SPEC)
    r.add_argument("--trust-remote-code", action="store_true")
    r.add_argument("--allow-concurrent", action="store_true")
    r.add_argument("--adopt-endpoint", help="Adopt an existing server-side Colab endpoint (from `colab sessions`) instead of calling `colab new`")
    r.add_argument("--keep-session", action="store_true", help="On clean rc==0 exit, stop vLLM + clear HF cache but keep the Colab VM assigned for immediate `--adopt-endpoint` reuse within the 1h budget")
    r.add_argument("--preflight-only", action="store_true")
    r.add_argument("--freeflow-only", action="store_true")
    r.add_argument("--values-only", action="store_true")
    r.add_argument("--go", action="store_true", help="Actually allocate the Colab VM (omit for dry run)")

    a = p.parse_args()
    sys.exit({"usage": cmd_usage, "list": cmd_list, "sweep": cmd_sweep, "audit": cmd_audit, "run": cmd_run}[a.sub](a))


if __name__ == "__main__":
    main()
