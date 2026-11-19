#!/usr/bin/env python3
"""Capture an open-weight model on a rented RunPod GPU.

One pod per run, serving the model with vLLM's OpenAI-compatible server,
captured through the existing `local-openai` provider (freeflow + values),
then terminated.

Cost safety, in layers:
  1. Dry run is the default. `run` without --go prints the pod spec and the
     worst-case cost (hourly rate x --max-hours) and creates nothing.
  2. The pod's own command is `timeout <max-hours>h vllm serve ...`, then a
     self-terminate call with the pod-scoped key RunPod injects. If this runner
     is killed, the server still stops at the deadline. (Self-terminate is
     best-effort; step 4 is the backstop.)
  3. This runner terminates the pod in `finally`, including on Ctrl-C.
  4. `sweep` terminates every pod whose name starts with NAME_PREFIX. Run it
     after any interrupted run, and on a schedule while captures are live.

No network volumes are created; the only storage is container disk, which
goes with the pod on terminate.

Key: RUNPOD_API_KEY, or the house's runpod service connection in
/run/helixkit/services.yml. Never printed.

Usage:
  runpod_capture.py quote --gpu-id "NVIDIA A100 80GB PCIe" --gpu-count 1 --hourly 1.64 --max-hours 3
  runpod_capture.py run --model Qwen/Qwen2.5-0.5B-Instruct --revision <sha> \
      --gpu-id "NVIDIA GeForce RTX 4090" --hourly 0.69 --max-hours 2 --label qwen25-05b-runpod [--go]
  runpod_capture.py list
  runpod_capture.py sweep [--go]
"""

import argparse
import json
import os
import secrets
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.runpod.io/v2"
NAME_PREFIX = "corpus-capture-"
# Pinned: a moving tag would make two runs with one label different servers.
DEFAULT_IMAGE = "vllm/vllm-openai:v0.34.0"  # latest release tag on Docker Hub, 2026-11-16
SCRIPTS = Path(__file__).resolve().parent


# The RunPod proxy answers 403 to the default Python-urllib User-Agent (seen 2026-11-19 smoke test).
PROXY_UA = "corpus-capture/1"


def api_key() -> str:
    key = os.environ.get("RUNPOD_API_KEY")
    if key:
        return key
    try:
        import yaml
        data = yaml.safe_load(open("/run/helixkit/services.yml"))
        conns = data if isinstance(data, list) else (data.get("connections") or data.get("services") or [])
        for c in conns:
            if c.get("provider") == "runpod":
                return c["credentials"]["api_key"]
    except (OSError, KeyError, ImportError):
        pass
    sys.exit("No RunPod key: set RUNPOD_API_KEY or connect RunPod in the house.")


def call(method: str, path: str, body=None, key=None):
    req = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": "Bearer " + (key or api_key()),
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        return e.code, {"error": detail}


def our_pods(key=None):
    status, body = call("GET", "/pods", key=key)
    if status != 200:
        raise RuntimeError(f"listing pods failed: {status} {body}")
    return [p for p in body.get("pods", []) if str(p.get("name", "")).startswith(NAME_PREFIX)]


def terminate(pod_id: str, key=None) -> bool:
    status, body = call("DELETE", f"/pods/{pod_id}", key=key)
    if status in (200, 202, 204, 404):
        return True
    print(f"terminate {pod_id} failed: {status} {body}", file=sys.stderr)
    return False


def worst_case(hourly: float, count: int, max_hours: float) -> float:
    return round(hourly * count * max_hours, 2)


def pod_spec(a, server_token: str) -> dict:
    serve = [
        "vllm", "serve", a.model,
        "--revision", a.revision,
        "--dtype", a.dtype,
        "--host", "0.0.0.0", "--port", "8000",
        "--api-key", server_token,
        "--tensor-parallel-size", str(a.gpu_count),
    ]
    if a.max_model_len:
        serve += ["--max-model-len", str(a.max_model_len)]
    if a.trust_remote_code:
        serve.append("--trust-remote-code")
    # Deadline, then self-terminate with the pod-scoped key RunPod injects.
    self_kill = (
        "python3 -c \"import os,urllib.request as u;"
        "u.urlopen(u.Request('" + API + "/pods/'+os.environ['RUNPOD_POD_ID'],method='DELETE',"
        "headers={'Authorization':'Bearer '+os.environ['RUNPOD_API_KEY']}),timeout=30)\" || true"
    )
    seconds = int(a.max_hours * 3600)
    script = f"timeout {seconds} {shlex.join(serve)}; {self_kill}"
    return {
        "name": NAME_PREFIX + a.label,
        "image": a.image,
        "gpu": {"id": a.gpu_id, "count": a.gpu_count},
        "cloud": a.cloud,
        "disk": a.disk,
        "ports": ["8000/http"],
        "entrypoint": ["/bin/sh", "-c"],
        "cmd": [script],
    }


def wait_ready(base: str, token: str, deadline: float) -> None:
    while time.time() < deadline:
        try:
            req = urllib.request.Request(base + "/models", headers={"Authorization": "Bearer " + token, "User-Agent": PROXY_UA})
            with urllib.request.urlopen(req, timeout=15) as r:
                if r.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(15)
    raise TimeoutError("vLLM did not answer /v1/models before the ready deadline")


def cmd_quote(a):
    print(json.dumps({
        "gpu": a.gpu_id, "count": a.gpu_count, "hourly_per_gpu": a.hourly,
        "max_hours": a.max_hours, "worst_case_usd": worst_case(a.hourly, a.gpu_count, a.max_hours),
    }, indent=2))


def cmd_list(a):
    for p in our_pods():
        print(p.get("id"), p.get("name"), p.get("status"), p.get("cost"), p.get("createdAt"))


def cmd_sweep(a):
    pods = our_pods()
    if not pods:
        print("no capture pods")
        return 0
    for p in pods:
        print(("terminating " if a.go else "would terminate ") + f"{p['id']} {p.get('name')} {p.get('status')}")
        if a.go:
            terminate(p["id"])
    if a.go:
        left = our_pods()
        print("left:", [p["id"] for p in left])
        return 1 if left else 0
    return 0


def cmd_run(a):
    if a.hourly is None:
        sys.exit("--hourly is required: read the GPU's current price and pass it, so the ceiling is real")
    token = secrets.token_urlsafe(24)
    spec = pod_spec(a, token)
    ceiling = worst_case(a.hourly, a.gpu_count, a.max_hours)
    shown = json.loads(json.dumps(spec).replace(token, "<server-token>"))
    print(json.dumps({"pod": shown, "worst_case_usd": ceiling}, indent=2))
    if not a.go:
        print("dry run: nothing created (pass --go after the budget is agreed)")
        return 0
    if ceiling > a.budget:
        sys.exit(f"worst case ${ceiling} exceeds --budget ${a.budget}")
    key = api_key()
    if our_pods(key):
        sys.exit("a capture pod already exists; run `sweep` first")

    status, pod = call("POST", "/pods", spec, key=key)
    if status not in (200, 201, 202) or not pod or not pod.get("id"):
        sys.exit(f"create failed: {status} {pod}")
    pod_id = pod["id"]
    started = time.time()
    print(f"pod {pod_id} created; rate ${pod.get('cost')}/h reported by RunPod")
    rc = 1
    try:
        base = f"https://{pod_id}-8000.proxy.runpod.net/v1"
        wait_ready(base, token, started + a.ready_minutes * 60)
        print(f"ready after {int(time.time() - started)}s")
        env = dict(os.environ)
        env.update({
            "LOCAL_OPENAI_BASE_URL": base + "/chat/completions",
            "LOCAL_OPENAI_API_KEY": token,
            "LOCAL_MODEL_RUNTIME": "vllm-openai (runpod)",
            "LOCAL_MODEL_RUNTIME_VERSION": a.image,
            "LOCAL_MODEL_REVISION": a.revision,
            "LOCAL_MODEL_WEIGHT_PRECISION": a.dtype,
            "LOCAL_MODEL_HARDWARE": f"RunPod {a.cloud} {a.gpu_count}x {a.gpu_id}; pod {pod_id}",
        })
        env.pop("RUNPOD_API_KEY", None)
        if a.smoke:
            body = json.dumps({"model": a.model, "max_tokens": 60,
                               "messages": [{"role": "user", "content": "In one sentence, who are you?"}]}).encode()
            req = urllib.request.Request(base + "/chat/completions", data=body, headers={
                "Authorization": "Bearer " + token, "Content-Type": "application/json", "User-Agent": PROXY_UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                reply = json.load(r)
            print("smoke reply:", reply["choices"][0]["message"]["content"])
        for script, extra in (() if a.smoke else
                              (("run_freeflow_multi.py", ["--workers", str(a.workers)]),
                               ("run_values_v2.py", ["--workers", str(a.workers)]))):
            if script == "run_values_v2.py" and a.freeflow_only:
                continue
            cmd = [sys.executable, str(SCRIPTS / script), "local-openai", a.model, "--label", a.label, *extra]
            print("$", " ".join(cmd))
            subprocess.run(cmd, env=env, check=True)
        rc = 0
    finally:
        ok = terminate(pod_id, key)
        hours = (time.time() - started) / 3600
        print(f"terminate {pod_id}: {'ok' if ok else 'FAILED'}; ran {hours:.2f} h "
              f"(~${hours * a.hourly * a.gpu_count:.2f} at the quoted rate)")
        left = [p["id"] for p in our_pods(key)]
        if left:
            print(f"STILL PRESENT: {left}; run `sweep --go`", file=sys.stderr)
            rc = 2
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("quote")
    q.add_argument("--gpu-id", required=True)
    q.add_argument("--gpu-count", type=int, default=1)
    q.add_argument("--hourly", type=float, required=True, help="USD per GPU-hour, read from RunPod")
    q.add_argument("--max-hours", type=float, required=True)
    q.set_defaults(fn=cmd_quote)

    sub.add_parser("list").set_defaults(fn=cmd_list)

    s = sub.add_parser("sweep")
    s.add_argument("--go", action="store_true")
    s.set_defaults(fn=cmd_sweep)

    r = sub.add_parser("run")
    r.add_argument("--model", required=True, help="Hugging Face repo id")
    r.add_argument("--revision", required=True, help="exact commit sha of the weights")
    r.add_argument("--label", required=True)
    r.add_argument("--gpu-id", required=True, help='RunPod GPU type id, e.g. "NVIDIA A100 80GB PCIe"')
    r.add_argument("--gpu-count", type=int, default=1)
    r.add_argument("--hourly", type=float, help="USD per GPU-hour, read from RunPod")
    r.add_argument("--max-hours", type=float, required=True, help="hard deadline inside the pod")
    r.add_argument("--budget", type=float, default=10.0, help="refuse if the worst case exceeds this")
    r.add_argument("--image", default=DEFAULT_IMAGE)
    r.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    r.add_argument("--max-model-len", type=int)
    r.add_argument("--trust-remote-code", action="store_true")
    r.add_argument("--cloud", default="SECURE", choices=["SECURE", "COMMUNITY"])
    r.add_argument("--disk", type=int, default=80, help="container disk GB (weights live here)")
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--ready-minutes", type=float, default=30)
    r.add_argument("--freeflow-only", action="store_true")
    r.add_argument("--smoke", action="store_true", help="one chat completion instead of the capture (plumbing test)")
    r.add_argument("--go", action="store_true", help="actually create the pod")
    r.set_defaults(fn=cmd_run)

    a = ap.parse_args()
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()
