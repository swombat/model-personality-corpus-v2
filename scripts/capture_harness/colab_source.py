"""Strict, offline source contract for preserved Colab BF16 completions.

No transport, copying or repair lives here. SHA256 binds the bytes actually read,
not a build-time observation or a re-serialization of the parsed JSON.
"""

import hashlib
import json
import re


def valid_endpoint(endpoint):
    # Deliberately narrower than a general URL parser: no userinfo, escapes,
    # queries, fragments, alternate loopback spellings or zero/out-of-range port.
    if not isinstance(endpoint, str):
        return False
    match = re.fullmatch(r"http://127\.0\.0\.1:([1-9][0-9]{0,4})/v1/chat/completions", endpoint)
    return bool(match and int(match[1]) <= 65535)


def validate_config(c, inventories):
    s = c.get("source_adoption")
    if c.get("provider") != "local-openai" or not isinstance(s, dict):
        raise ValueError("Colab adoption requires local-openai and source_adoption")
    if s.get("mode") != "colab-bf16" or c.get("quantization") != "bfloat16":
        raise ValueError("only colab-bf16 / bfloat16 source adoption is supported")
    if any(k in c for k in ("or_provider", "reasoning_effort", "token_policy", "route_max_tokens")):
        raise ValueError("Colab sources must not declare OpenRouter capture policy")
    for field in ("source_commit", "model_revision"):
        if not re.fullmatch(r"[0-9a-f]{40}", str(s.get(field, ""))):
            raise ValueError("Colab source needs full pinned " + field)
    dep = s.get("local_deployment")
    fields = {"runtime", "runtime_version", "model_revision", "weight_precision",
              "hardware", "stop_sequence"}
    if not isinstance(dep, dict) or set(dep) != fields:
        raise ValueError("Colab source needs the exact local_deployment provenance")
    if (dep["runtime"] != "vllm-openai (colab)"
            or dep["weight_precision"] != "bfloat16"
            or dep["model_revision"] != s["model_revision"]
            or dep["stop_sequence"] is not None
            or any(not isinstance(dep[k], str) or not dep[k].strip()
                   for k in ("runtime_version", "hardware"))):
        raise ValueError("invalid Colab BF16 deployment provenance")
    endpoints = s.get("endpoints")
    if (not isinstance(endpoints, list) or not endpoints
            or any(not valid_endpoint(e) for e in endpoints)
            or len(set(endpoints)) != len(endpoints)):
        raise ValueError("Colab source needs enumerated strict loopback endpoints")
    if not isinstance(c.get("model"), str) or not c["model"].strip():
        raise ValueError("Colab source needs exact model identity")
    counts, hashes = s.get("counts"), s.get("sha256")
    if not isinstance(counts, dict) or not isinstance(hashes, dict):
        raise ValueError("Colab source needs counts and per-sample SHA256 inventory")
    if set(counts) != set(inventories) or set(hashes) != set(inventories):
        raise ValueError("Colab source requires both canonical probes")
    for probe, ids in inventories.items():
        if type(counts[probe]) is not int or counts[probe] != len(ids):
            raise ValueError("Colab source count mismatch: " + probe)
        h = hashes[probe]
        if not isinstance(h, dict) or set(h) != set(ids):
            raise ValueError("Colab source sample inventory mismatch: " + probe)
        if any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v)
               for v in h.values()):
            raise ValueError("invalid Colab source SHA256: " + probe)


def problem(d, c, probe, sid, canonical_prompt, source_bytes):
    s = c["source_adoption"]
    expected = s["sha256"].get(probe, {}).get(sid)
    if not expected or hashlib.sha256(source_bytes).hexdigest() != expected:
        return "source_sha256"
    if json.loads(source_bytes) != d:
        return "source_snapshot_mismatch"
    if not isinstance(d, dict):
        return "source_schema"
    dep = d.get("local_deployment")
    if (not isinstance(dep, dict)
            or not valid_endpoint(dep.get("endpoint"))
            or dep["endpoint"] not in s["endpoints"]
            or {k: v for k, v in dep.items() if k != "endpoint"} != s["local_deployment"]
            or d.get("provider") != "local-openai"
            or any(d.get(k) != c["model"] for k in ("model", "model_requested"))
            ):
        return "source_identity_provenance"
    if d.get("condition") != sid.rsplit("_", 1)[0] or d.get("prompt") != canonical_prompt:
        return "prompt_identity"
    raw = d.get("raw")
    if not isinstance(raw, dict) or raw.get("model") != c["model"]:
        return "route_identity"
    choices = raw.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        return "source_choices"
    choice = choices[0]
    if choice.get("finish_reason") != "stop":
        return "finish_" + str(choice.get("finish_reason"))
    message = choice.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        return "source_message"
    text = message.get("content")
    if not isinstance(text, str) or not text.strip():
        return "empty_final"
    if d.get("error") or d.get("result") != text:
        return "result_mismatch"
    if message.get("tool_calls") or message.get("function_call") or message.get("refusal"):
        return "non_text_completion"
    if "\ufffd" in text or any(t in text for t in ("<|im_start|>", "<|im_end|>", "<|endoftext|>")):
        return "text_fidelity"
    usage = raw.get("usage")
    if not isinstance(usage, dict) or usage != d.get("usage"):
        return "usage_mismatch"
    if (any(type(usage.get(k)) is not int or usage[k] < 0
            for k in ("prompt_tokens", "completion_tokens", "total_tokens"))
            or usage["completion_tokens"] == 0
            or usage["total_tokens"] != usage["prompt_tokens"] + usage["completion_tokens"]):
        return "usage_counts"
    return None
