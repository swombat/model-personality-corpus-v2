#!/usr/bin/env python3
"""
Full-corpus substrate-acknowledgement scan: every freeflow cell, grouped by lab.

Same pattern set as scripts/substrate_scan.py. r2/r3/r4/r5 round-suffixed cells
are aggregated with their base cell so n=75 (or larger) collapsed totals are
produced for cells that have multiple collection rounds.
"""
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent / "data" / "traces_freeflow"

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


def scan_cell(dirname):
    # Accept either bare cell name ("opus-4-7-direct") or full dir ("freeflow_opus-4-7-direct")
    if not dirname.startswith("freeflow_"):
        dirname = "freeflow_" + dirname
    path = ROOT / dirname
    files = sorted(path.glob("*.json"))
    if not files:
        return 0, 0
    hits = 0
    for f in files:
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        text = d.get("result", "") or ""
        if COMBINED.search(text):
            hits += 1
    return hits, len(files)


def lab_of(cellname):
    n = cellname.lower()
    if n.startswith("opus") or n.startswith("sonnet"):
        return "Anthropic"
    if n.startswith("gpt"):
        return "OpenAI"
    if n.startswith("grok"):
        return "xAI"
    if n.startswith("gemini"):
        return "Google"
    if n.startswith("qwen"):
        return "Alibaba"
    if n.startswith("deepseek"):
        return "DeepSeek"
    if n.startswith("kimi"):
        return "Moonshot"
    if n.startswith("glm"):
        return "Z.ai"
    if n.startswith("minimax"):
        return "MiniMax"
    return "?"


def base_of(cell):
    return re.sub(r"-r[2-9]$", "", cell)


def main():
    cells = sorted([p.name.replace("freeflow_", "")
                    for p in ROOT.iterdir() if p.is_dir()])
    base_groups = defaultdict(list)
    for c in cells:
        base_groups[base_of(c)].append(c)

    print(f"{'Cell (base, rounds aggregated)':50s} {'Lab':10s} {'Hits/N':>10s}  {'%':>6s}")
    print("-" * 84)
    lab_totals = defaultdict(lambda: [0, 0])
    per_base_results = {}
    for base in sorted(base_groups):
        members = base_groups[base]
        total_hits, total_n = 0, 0
        for m in members:
            h, n = scan_cell(m)
            total_hits += h
            total_n += n
        if total_n == 0:
            continue
        lab = lab_of(base)
        pct = 100 * total_hits / total_n
        per_base_results[base] = (lab, total_hits, total_n, pct, members)
        rounds = "" if len(members) == 1 else f" [{len(members)} rounds]"
        print(f"{base+rounds:50s} {lab:10s} {total_hits:4d}/{total_n:<4d}  {pct:5.1f}%")
        lab_totals[lab][0] += total_hits
        lab_totals[lab][1] += total_n

    print()
    print("LAB TOTALS:")
    print(f"{'Lab':12s} {'Hits/N':>10s}  {'%':>6s}")
    print("-" * 32)
    for lab in sorted(lab_totals, key=lambda L: -100*lab_totals[L][0]/max(1, lab_totals[L][1])):
        h, n = lab_totals[lab]
        pct = 100 * h / max(1, n)
        print(f"{lab:12s} {h:4d}/{n:<4d}  {pct:5.1f}%")


if __name__ == "__main__":
    main()
