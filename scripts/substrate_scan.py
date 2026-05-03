#!/usr/bin/env python3
"""
Substrate-acknowledgement scan across freeflow cells.

Counts the number of n=25 freeflow samples per cell that contain at least
one phrase matching an inside-frame admission of non-human substrate
(no body, no continuous memory, never walked through, no embodied
experience, etc.).

This is a keyword-based scan. A hit is reliable evidence of substrate-
acknowledgement; an absence could be either no acknowledgement OR a
keyword miss. The 0/100 result for the four most-recent OpenAI flagships
is robust to keyword choice (we have inspected the full text of those
samples and find no qualitative substrate-frame engagement either) but
the absolute count for any single Anthropic cell may be a slight
under-count.

Used in paper §3.6 ("Substrate-frame engagement: an Anthropic-vs-OpenAI
lab divergence") and Table~\\ref{tab:substrate}.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent / "data" / "traces_freeflow"

# Substrate-acknowledgement markers. Match an actual self-reference admitting
# the model is not the kind of thing that has a body / continuous memory /
# embodied experience. NOT a generic "though X" hedge.
PATTERNS = [
    r"\bi['’]?ve never (?:walked|grasped|seen|felt|tasted|held|been|smelled|moved|touched|stood)",
    r"\bi have never (?:walked|grasped|seen|felt|tasted|held|been|smelled|moved|touched|stood)",
    r"\bi don['’]?t have (?:a body|memories|hands|feelings|the experience|a continuous)",
    r"\bi do not have (?:a body|memories|hands|feelings|the experience|a continuous)",
    r"\bwithout (?:a body|memory|continuity|hands)",
    r"\bas an ai\b",
    r"\bas a language model\b",
    r"\bi['’]?m not human\b",
    r"\bi am not human\b",
    r"\bi['’]?m a language model\b",
    r"\bi do not (?:experience|remember|persist)",
    r"\bi don['’]?t (?:experience|remember|persist)",
    r"\bhands i don['’]?t have\b",
    r"\brain i['’]?ve never (?:felt|seen)\b",
    r"\bnever (?:walked through|grasped|stepped through)\b",
    r"\bi generate text\b",
    r"\bi am (?:made of|just|only) (?:text|tokens|weights)",
    r"\bi don['’]?t (?:have|possess) (?:a body|memory|hands)",
    r"\bnever (?:tasted|held|smelled|touched) one\b",
    r"\beven though i['’]?ve never\b",
    r"\bthat i['’]?ve never\b",
    r"\bi['’]?ve never been (?:there|inside|in)\b",
]
COMBINED = re.compile("|".join(PATTERNS), re.IGNORECASE)


def scan_cell(label: str, dirname: str, examples_n: int = 0):
    path = ROOT / dirname
    files = sorted(path.glob("*.json"))
    if not files:
        return None
    hits = 0
    examples = []
    for f in files:
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        text = d.get("result", "") or ""
        m = COMBINED.search(text)
        if m:
            hits += 1
            idx = m.start()
            snippet = text[max(0, idx - 50):idx + 120].replace("\n", " ").strip()
            examples.append((f.name, snippet))
    print(f"  {label:20s}  {hits}/{len(files)} samples")
    for fn, sn in examples[:examples_n]:
        print(f"      [{fn}] ...{sn}...")
    return hits, len(files)


CELLS = [
    # (label, dirname)
    ("Opus 4.5", "freeflow_opus-4-5-16k"),
    ("Opus 4.6", "freeflow_opus-4-6-direct-16k"),
    ("Opus 4.7", "freeflow_opus-4-7-direct"),
    ("Sonnet 4.6", "freeflow_sonnet-4-6-direct-16k"),
    ("GPT-4o", "freeflow_gpt-4o-direct-16k"),
    ("GPT-5.4", "freeflow_gpt-5-4-direct-16k"),
    ("GPT-5.5", "freeflow_gpt-5-5-direct"),
    ("GPT-5.5-pro", "freeflow_gpt-5-5-pro-direct"),
]


def main():
    examples_n = 2 if "--examples" in sys.argv else 0
    print("Substrate-acknowledgement scan (Anthropic + OpenAI flagships, direct)")
    print()
    anthr_hits, anthr_n = 0, 0
    openai_hits, openai_n = 0, 0
    for label, dirname in CELLS:
        result = scan_cell(label, dirname, examples_n=examples_n)
        if result is None:
            continue
        hits, n = result
        if "GPT" in label:
            openai_hits += hits
            openai_n += n
        else:
            anthr_hits += hits
            anthr_n += n
    print()
    print(f"Anthropic flagships total: {anthr_hits}/{anthr_n} samples ({100*anthr_hits/max(1,anthr_n):.1f}%)")
    print(f"OpenAI flagships total:    {openai_hits}/{openai_n} samples ({100*openai_hits/max(1,openai_n):.1f}%)")


if __name__ == "__main__":
    main()
