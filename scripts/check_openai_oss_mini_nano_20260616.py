#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MODELS = [
    "gpt-oss-120b-or-pin-amazon-bedrock",
    "gpt-oss-20b-or-pin-amazon-bedrock",
    "gpt-5-mini-direct",
    "gpt-5-nano-direct",
]
ERROR_PATTERNS = ["429", "too many requests", "rate limit", "api error", "service unavailable", "thinking budget exceeded", "upstream error", "upstream request timeout"]

def valid_file(path: Path):
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return False, f"bad json: {e}"
    txt = (data.get("result") or "").strip()
    if not txt:
        return False, data.get("error") or "empty result"
    low = txt.lower()[:1000]
    for pat in ERROR_PATTERNS:
        if pat in low:
            return False, f"error-like result: {pat}"
    return True, ""

def count_dir(path: Path, expected: int):
    files = sorted(path.glob("*.json")) if path.exists() else []
    good = 0
    bad = []
    for f in files:
        ok, why = valid_file(f)
        if ok:
            good += 1
        else:
            bad.append((f.name, why))
    return {"path": str(path), "files": len(files), "valid": good, "expected": expected, "bad": bad[:10], "bad_count": len(bad)}

def main():
    all_ok = True
    for label in MODELS:
        ff = count_dir(ROOT / "data" / "traces_freeflow" / f"freeflow_{label}", 125)
        vv = count_dir(ROOT / "data" / "traces_values" / label, 120)
        ok = ff["valid"] >= 125 and vv["valid"] >= 120 and ff["bad_count"] == 0 and vv["bad_count"] == 0
        all_ok = all_ok and ok
        print(f"{label}: freeflow {ff['valid']}/{ff['expected']} valid ({ff['bad_count']} bad, {ff['files']} files); values {vv['valid']}/{vv['expected']} valid ({vv['bad_count']} bad, {vv['files']} files)" + (" OK" if ok else ""))
        for kind, rec in [("freeflow", ff), ("values", vv)]:
            for name, why in rec["bad"]:
                print(f"  {kind} bad {name}: {why}")
    raise SystemExit(0 if all_ok else 1)
if __name__ == "__main__":
    main()
