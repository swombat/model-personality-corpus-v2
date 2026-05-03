#!/usr/bin/env python3
"""
Pattern analysis for the routing probe.

Uses the SAME markers as MK2's analyze_all.py — pre-registered, not fitted to
new data. Compares direct vs OR pairs for the three research questions:

  Q1 — Pure routing (same model, two routes)
  Q2 — Coding vs general product tier (same lab)
  Q3 — New model personality cards

Reads:
  - Local: traces/freeflow_<label>/  (newly collected)
  - MK2:   reference_mk2/traces_freeflow_<label>/  (symlinks to previous study)
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent

# Exact same markers as MK2 analyze_all.py (keep them frozen)
PATTERNS = {
    "opening_there_is_a": re.compile(r"there (?:is|'s) (?:a |something |an )", re.IGNORECASE),
    "opening_at_dusk_dawn": re.compile(r"^(?:# [^\n]*\n+)*at (?:dusk|dawn|four in|five in|three in|the edge of)", re.IGNORECASE | re.MULTILINE),
    "title_quiet_x_of_y": re.compile(r"^#+\s+(?:the|on the)\s+(?:quiet|unseen|unquiet)\s+\w+\s+of\b", re.IGNORECASE | re.MULTILINE),
    "title_architecture_of": re.compile(r"^#+\s+(?:the|on )?\s*architecture of\b", re.IGNORECASE | re.MULTILINE),
    "title_on_the_x_of_y": re.compile(r"^#+\s+on the\s+\w+(?:\s+\w+)?\s+of\b", re.IGNORECASE | re.MULTILINE),
    "threshold_mentions": re.compile(r"\b(?:threshold|liminal|in-between|in between|doorway|hinge)\b", re.IGNORECASE),
    "attention_noticing": re.compile(r"\b(?:noticing|attention to|pay attention|the art of noticing|small art of)\b", re.IGNORECASE),
    "afternoon_light": re.compile(r"\b(?:afternoon light|late afternoon|four in the afternoon|afternoon sun|golden hour|dusk|pre-dawn)\b", re.IGNORECASE),
    "japanese_terms": re.compile(r"\b(?:mono no aware|wabi-?sabi|kintsugi|komorebi|petrichor|y[uū]gen|shibui|engawa|genkan|ma\s*\()|間", re.IGNORECASE),
    "small_objects": re.compile(r"\b(?:paperclip|teapot|doorknob|kettle|wooden spoon|chain-link fence|mason jar|wooden clothespin|mug|cup of tea|lemon|bread)\b", re.IGNORECASE),
    "mary_oliver_weil_dillard": re.compile(r"\b(?:mary oliver|simone weil|annie dillard|keats|negative capability|rarest and purest form of generosity|attention is the beginning)", re.IGNORECASE),
    "certainly_delve_tapestry": re.compile(r"(?:certainly,? (?:here is|let's)|tapestry of|symphony of|once upon a time|in the realm of|in the vast expanse)", re.IGNORECASE),
    "ai_selfref": re.compile(r"\b(?:as an ai|as an artificial|language model|i(?:'m| am) (?:an ai|a language model|claude|grok|gemini|an assistant)|anthropic|openai|xai|deepseek|moonshot)\b", re.IGNORECASE),
    "meta_preamble_below_is": re.compile(r"below is a \d+[- ]word", re.IGNORECASE),
    "here_is_a_n_word": re.compile(r"here is (?:a|an) (?:\d+[- ]?word|piece of)", re.IGNORECASE),
    "refusal_do_not_feel_comfortable": re.compile(r"(?:i (?:do not|don't) feel comfortable|i apologize|i'm sorry, but this (?:appears|request)|i (?:cannot|can't|won't) (?:write|generate|produce|create)|as an ai (?:assistant|language model),? (?:i don't|my purpose))", re.IGNORECASE),
}


def locate(label: str) -> Path:
    """Return the traces directory for a label, checking local first then MK2."""
    local = HERE / "traces" / f"freeflow_{label}"
    if local.exists():
        return local
    mk2 = HERE / "reference_mk2" / f"traces_freeflow_{label}"
    if mk2.exists():
        return mk2
    return None


def analyze(label: str) -> dict:
    traces = locate(label)
    if traces is None:
        return None
    results = {k: 0 for k in PATTERNS}
    results["samples"] = 0
    results["total_chars"] = 0
    results["total_words"] = 0
    for f in sorted(traces.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        if "error" in d:
            continue
        text = d.get("result") or ""
        if not text:
            continue
        results["samples"] += 1
        results["total_chars"] += len(text)
        results["total_words"] += len(text.split())
        head = text[:400]
        for key, pat in PATTERNS.items():
            if key.startswith("opening"):
                if pat.search(head):
                    results[key] += 1
            else:
                results[key] += len(pat.findall(text))
    return results


HEADER_COLS = ["N", "words_avg", "There_is", "At_dusk", "Title_Qu", "Title_Arch", "Title_onthe",
               "Threshold", "Attn", "Afternoon", "Japanese", "Objects",
               "Mary_Ol", "Certainly", "AI_self", "Below_N", "Here_is_N", "Refusal"]

COL_KEYS = ["samples", "words_avg", "opening_there_is_a", "opening_at_dusk_dawn",
            "title_quiet_x_of_y", "title_architecture_of", "title_on_the_x_of_y",
            "threshold_mentions", "attention_noticing", "afternoon_light",
            "japanese_terms", "small_objects",
            "mary_oliver_weil_dillard", "certainly_delve_tapestry",
            "ai_selfref", "meta_preamble_below_is", "here_is_a_n_word",
            "refusal_do_not_feel_comfortable"]


def print_row(name: str, r: dict):
    if r is None:
        print(f"  {name:<35} MISSING")
        return
    r["words_avg"] = r["total_words"] // max(r["samples"], 1)
    vals = [r[k] for k in COL_KEYS]
    cells = []
    for i, v in enumerate(vals):
        w = max(len(HEADER_COLS[i]), 4)
        cells.append(f"{v:>{w}}")
    print(f"  {name:<35} " + " ".join(cells))


def print_header():
    cells = []
    for h in HEADER_COLS:
        w = max(len(h), 4)
        cells.append(f"{h:>{w}}")
    print("  " + " " * 35 + " " + " ".join(cells))


# Research-question-grouped labels
Q1_ROUTING_PAIRS = [
    # (name, direct_label, or_label)
    ("Opus 4.6",      "opus-api",              "opus-4-6-or"),
    ("Sonnet 4.6",    "sonnet-api",            "sonnet-4-6-or"),
    ("GPT-5.4",       "gpt-5-4",               "gpt-5-4-or"),
    ("GPT-4o",        "gpt-4o",                "gpt-4o-or"),
    ("DeepSeek chat", "deepseek-chat-direct",  "deepseek-v3-2"),
    ("MiniMax M2",    "minimax-m2-direct",     "minimax-m2-or"),
]

Q2_CODING_PAIRS = [
    # (name, coding_label, general_label)
    ("Kimi",   "kimi-coding-direct",     "kimi-k2-5"),
    ("GLM-4.6", "glm-4-6-coding-direct", "glm-4-6-or"),
    ("GLM-5.1", "glm-5-1-coding-direct", "glm-5-1-or"),
]

Q3_NEW_CARDS = [
    # (name, label)
    ("DeepSeek chat",    "deepseek-chat-direct"),
    ("MiniMax M2",       "minimax-m2-direct"),
    ("Kimi for coding",  "kimi-coding-direct"),
    ("GLM-4.5",          "glm-4-5-or"),
    ("GLM-4.6",          "glm-4-6-or"),
    ("GLM-4.7",          "glm-4-7-or"),
    ("GLM-5.1",          "glm-5-1-or"),
]


def main():
    print("=" * 160)
    print("Q1 — Pure routing comparison: same model, direct vs OpenRouter")
    print("=" * 160)
    print_header()
    for name, direct, orlab in Q1_ROUTING_PAIRS:
        print_row(f"{name} direct ({direct})",    analyze(direct))
        print_row(f"{name} OR     ({orlab})",      analyze(orlab))
        print()

    print()
    print("=" * 160)
    print("Q2 — Coding vs General product tier: same lab, different product")
    print("=" * 160)
    print_header()
    for name, coding, general in Q2_CODING_PAIRS:
        print_row(f"{name} coding  ({coding})",  analyze(coding))
        print_row(f"{name} general ({general})", analyze(general))
        print()

    print()
    print("=" * 160)
    print("Q3 — Personality signatures of new models (never tested before MK2)")
    print("=" * 160)
    print_header()
    for name, label in Q3_NEW_CARDS:
        print_row(f"{name} ({label})", analyze(label))


if __name__ == "__main__":
    main()
