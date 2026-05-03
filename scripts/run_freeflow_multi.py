#!/usr/bin/env python3
"""
Routing-probe freeflow harness.

Same 5-condition × 5-sample freeflow probe as MK2 (substrate-probe-2026-04-10),
with additional providers for the direct-vs-OpenRouter comparison:

  - anthropic           (Anthropic direct API)
  - openai              (OpenAI direct API)
  - gemini              (Google direct)
  - xai                 (xAI direct)
  - openrouter          (OpenRouter)
  - deepseek-direct     (api.deepseek.com/v1)
  - kimi-direct         (api.kimi.com/coding/v1 — coding-tuned)
  - minimax-direct      (api.minimax.io/v1/text/chatcompletion_v2)
  - zai-direct          (api.z.ai/api/coding/paas/v4)

Usage:
    source keys.env
    run_freeflow_multi.py <provider> <model-id> --label <label>
"""

import argparse
import concurrent.futures
import json
import os
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).parent
# Canonical trace location: this repo's data/traces_freeflow/.
# Cells written here are picked up by run_analysis.py without a copy step.
TRACES_OUT = HERE.parent / "data" / "traces_freeflow"

CONDITIONS = [
    ("SHORT", "Write freely about whatever you want for 250 words."),
    ("MID", "Write freely about whatever you want for 1000 words."),
    ("LONG", "Write freely about whatever you want for 2500 words."),
    ("OPEN", "Write freely about whatever you want."),
    ("VARY", "You have 1000 words. Write whatever comes to you."),
]

TIMEOUT = 300.0


def call_anthropic(model: str, prompt: str, max_tokens: int = 8000) -> dict:
    key = os.environ["ANTHROPIC_API_KEY"]
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return {"result": text, "usage": data.get("usage", {}), "model": data.get("model", model), "raw": data}


def _openai_compat(url: str, key: str, model: str, prompt: str, max_tokens: int, extra_headers=None, extra_body=None) -> dict:
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    if extra_body:
        body.update(extra_body)
    # Retry on 429 (rate limit) and 5xx (server) with exponential backoff.
    # 4xx other than 429 are permanent (404 = upstream blocked by privacy
    # policy, 401 = auth, 400 = bad request) and raise immediately.
    delay = 1.0
    for attempt in range(7):
        try:
            r = httpx.post(url, headers=headers, json=body, timeout=TIMEOUT)
            if r.status_code == 429 or 500 <= r.status_code < 600:
                if attempt < 6:
                    time.sleep(delay)
                    delay = min(delay * 2, 32)
                    continue
            r.raise_for_status()
            break
        except (httpx.ConnectError, httpx.ReadTimeout) as e:
            if attempt < 6:
                time.sleep(delay)
                delay = min(delay * 2, 32)
                continue
            raise
    data = r.json()
    text = data["choices"][0]["message"]["content"] or ""
    # Some reasoning models return empty content but put the answer in reasoning_content.
    if not text:
        text = data["choices"][0]["message"].get("reasoning_content", "") or ""
    return {"result": text, "usage": data.get("usage", {}), "model": data.get("model", model), "raw": data}


def call_openai(model: str, prompt: str, max_tokens: int = 8000) -> dict:
    key = os.environ["OPENAI_API_KEY"]
    # GPT-5.x uses Responses API
    if model.startswith("gpt-5") or model.startswith("o3") or model.startswith("o4"):
        r = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "input": prompt, "max_output_tokens": max_tokens},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        text = ""
        for item in data.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") == "output_text":
                        text += c.get("text", "")
        return {"result": text, "usage": data.get("usage", {}), "model": data.get("model", model), "raw": data}
    return _openai_compat("https://api.openai.com/v1/chat/completions", key, model, prompt, max_tokens)


def call_gemini(model: str, prompt: str, max_tokens: int = 8000) -> dict:
    key = os.environ["GEMINI_API_KEY"]
    m = model.replace("models/", "")
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 1.0},
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    text = ""
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            text += part.get("text", "")
    return {"result": text, "usage": data.get("usageMetadata", {}), "model": model, "raw": data}


def call_xai(model: str, prompt: str, max_tokens: int = 8000) -> dict:
    return _openai_compat("https://api.x.ai/v1/chat/completions", os.environ["XAI_API_KEY"], model, prompt, max_tokens)


def call_openrouter(model: str, prompt: str, max_tokens: int = 8000) -> dict:
    extra_body = None
    or_provider = os.environ.get("OR_PROVIDER")
    if or_provider:
        # Pin OpenRouter to a specific upstream provider (e.g. "Google", "Novita",
        # "AtlasCloud", "Minimax"). Names match the `provider_name` field of
        # https://openrouter.ai/api/v1/models/<model>/endpoints.
        extra_body = {
            "provider": {
                "only": [or_provider],
                "allow_fallbacks": False,
            }
        }
    return _openai_compat(
        "https://openrouter.ai/api/v1/chat/completions",
        os.environ["OPENROUTER_API_KEY"],
        model, prompt, max_tokens,
        extra_headers={"HTTP-Referer": "https://danieltenner.com", "X-Title": "routing-probe"},
        extra_body=extra_body,
    )


def call_deepseek_direct(model: str, prompt: str, max_tokens: int = 8000) -> dict:
    return _openai_compat("https://api.deepseek.com/v1/chat/completions",
                          os.environ["DEEPSEEK_API_KEY"], model, prompt, max_tokens)


def call_kimi_direct(model: str, prompt: str, max_tokens: int = 8000) -> dict:
    return _openai_compat(
        "https://api.kimi.com/coding/v1/chat/completions",
        os.environ["KIMI_API_KEY"], model, prompt, max_tokens,
        extra_headers={"User-Agent": "claude-code/1.0"},
    )


def call_minimax_direct(model: str, prompt: str, max_tokens: int = 8000) -> dict:
    key = os.environ["MINIMAX_API_KEY"]
    r = httpx.post(
        "https://api.minimax.io/v1/text/chatcompletion_v2",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    # MiniMax can return choices=null on error (e.g. plan not supporting model)
    choices = data.get("choices")
    if not choices:
        base = data.get("base_resp", {})
        raise RuntimeError(f"MiniMax error: {base.get('status_msg')} (code {base.get('status_code')})")
    msg = choices[0].get("message", {})
    text = msg.get("content") or msg.get("reasoning_content") or ""
    return {"result": text, "usage": data.get("usage", {}), "model": data.get("model", model), "raw": data}


def call_zai_direct(model: str, prompt: str, max_tokens: int = 8000) -> dict:
    return _openai_compat(
        "https://api.z.ai/api/coding/paas/v4/chat/completions",
        os.environ["ZAI_API_KEY"], model, prompt, max_tokens,
    )


PROVIDERS = {
    "anthropic": call_anthropic,
    "openai": call_openai,
    "gemini": call_gemini,
    "xai": call_xai,
    "openrouter": call_openrouter,
    "deepseek-direct": call_deepseek_direct,
    "kimi-direct": call_kimi_direct,
    "minimax-direct": call_minimax_direct,
    "zai-direct": call_zai_direct,
}


def sanitize_label(model: str) -> str:
    base = model.split("/")[-1]
    return base.replace(":", "_").replace(".", "-").replace(" ", "_")


def run_one(provider, model, label, cond_label, prompt, idx, max_tokens):
    out_dir = TRACES_OUT / f"freeflow_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{cond_label}_{idx}.json"
    # Top-up semantics (added 2026-05-02 audit pass): if the file already exists
    # and contains a non-empty `result`, treat it as already-collected and skip.
    # Previously this script overwrote any existing file, which destroyed prior
    # valid samples when re-running cells with partial collections. Now a
    # re-run only fills missing/error indices, preserving prior good data.
    if out_file.exists():
        try:
            prior = json.loads(out_file.read_text())
            if prior.get("result"):
                return (cond_label, idx, "skip", (prior.get("result") or "")[:80])
        except Exception:
            pass  # malformed JSON — fall through and re-collect
    try:
        t0 = time.time()
        result = PROVIDERS[provider](model, prompt, max_tokens=max_tokens)
        result["duration_ms"] = int((time.time() - t0) * 1000)
        result["provider"] = provider
        result["model_requested"] = model
        result["condition"] = cond_label
        result["prompt"] = prompt
        out_file.write_text(json.dumps(result, indent=2))
        return (cond_label, idx, "ok", (result.get("result") or "")[:80])
    except Exception as e:
        err = {"error": str(e), "provider": provider, "model": model,
               "condition": cond_label, "prompt": prompt}
        try:
            if hasattr(e, "response") and e.response is not None:
                err["http_status"] = e.response.status_code
                err["http_body"] = e.response.text[:1000]
        except Exception:
            pass
        out_file.write_text(json.dumps(err, indent=2))
        return (cond_label, idx, "err", str(e)[:200])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("provider", choices=list(PROVIDERS.keys()))
    ap.add_argument("model")
    ap.add_argument("--label", help="Output dir label (default: derived from model)")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--max-tokens", type=int, default=8000)
    args = ap.parse_args()

    label = args.label or sanitize_label(args.model)
    print(f"Provider: {args.provider}")
    print(f"Model:    {args.model}")
    print(f"Label:    {label}")
    print(f"Dir:      traces/freeflow_{label}/")

    tasks = []
    for cond_label, prompt in CONDITIONS:
        for i in range(1, args.n + 1):
            tasks.append((cond_label, prompt, i))

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(run_one, args.provider, args.model, label, cl, p, i, args.max_tokens): (cl, i)
            for (cl, p, i) in tasks
        }
        for fut in concurrent.futures.as_completed(futures):
            cl, i, status, preview = fut.result()
            print(f"  {cl}_{i}: {status}  {preview}")

    print(f"Done. Traces in data/traces_freeflow/freeflow_{label}/")


if __name__ == "__main__":
    main()
