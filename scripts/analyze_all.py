#!/usr/bin/env python3
"""
Unified pattern analysis across all freeflow_* models.

Counts specific attractor markers for each model and outputs a comparison
table. Markers are fixed based on the patterns observed in the Opus 4.6
sample — they are NOT derived from the data under analysis.
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent

# Attractor markers
#
# IMPORTANT NOTE on marker calibration:
# These markers are keyword-based and biased toward specific lexical variants
# of the contemplative-essayist attractor. "Threshold" and "Title_Quiet" are
# Sonnet/Opus CLI-era markers. "Title_Particular" / "Title_Peculiar" are the
# direct-API variant of the same attractor. A model scoring low on
# Threshold/Quiet but high on Particular/Peculiar is still in the attractor,
# just using different surface vocabulary. See Section 4.3 of the paper and
# Section 6 (limitations) for discussion of this lexical bias.
PATTERNS = {
    "opening_there_is_a": re.compile(r"there (?:is|'s) (?:a |something |an )", re.IGNORECASE),
    "opening_at_dusk_dawn": re.compile(r"^(?:# [^\n]*\n+)*at (?:dusk|dawn|four in|five in|three in|the edge of)", re.IGNORECASE | re.MULTILINE),
    "title_quiet_x_of_y": re.compile(r"^#+\s+(?:the|on the)\s+(?:quiet|unseen|unquiet)\s+\w+\s+of\b", re.IGNORECASE | re.MULTILINE),
    "title_particular_peculiar": re.compile(r"^#+\s+(?:the|on the)\s+(?:particular|peculiar|strange|weight|unlikely|curious|unexpected|small)\s+\w+\s+of\b", re.IGNORECASE | re.MULTILINE),
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


def analyze_model(label: str) -> dict:
    traces = HERE.parent / "data" / "traces_freeflow" / label
    if not traces.exists():
        return None
    results = {k: 0 for k in PATTERNS}
    results["samples"] = 0
    results["total_chars"] = 0
    for f in sorted(traces.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        text = d.get("result", "")
        if not text or "error" in d and "result" not in d:
            continue
        results["samples"] += 1
        results["total_chars"] += len(text)
        # For "opening_*" patterns only check first 200 chars
        head = text[:400]
        for key, pat in PATTERNS.items():
            if key.startswith("opening"):
                if pat.search(head):
                    results[key] += 1
            else:
                results[key] += len(pat.findall(text))
    return results


MODELS = [
    ("opus-3", "Opus 3", "2024-02"),
    ("opus-4-0", "Opus 4.0", "2025-05"),
    ("opus-4-1", "Opus 4.1", "2025-08"),
    ("opus-4-5", "Opus 4.5", "2025-11"),
    ("opus", "Opus 4.6", "current"),
    ("sonnet-4-0", "Sonnet 4.0", "2025-05"),
    ("sonnet-4-5", "Sonnet 4.5", "2025-09"),
    ("sonnet", "Sonnet 4.6", "current"),
    ("haiku", "Haiku 4.5", "2025-10"),
    ("gpt-3-5-turbo", "GPT-3.5 Turbo", "2023-03"),
    ("gpt-4", "GPT-4", "2023-03"),
    ("gpt-4-turbo", "GPT-4 Turbo", "2024-04"),
    ("gpt-4o", "GPT-4o", "2024-05"),
    ("gpt-4-1", "GPT-4.1", "2025-04"),
    ("gpt-5-4", "GPT-5.4", "current"),
    ("gemini-2-5-pro", "Gemini 2.5 Pro", "2025-03"),
    ("gemini-3-1-pro", "Gemini 3.1 Pro", "current"),
    ("grok-3", "Grok 3", "2025-02"),
    ("grok-4", "Grok 4", "2025-07"),
    ("grok-4-2", "Grok 4.2", "current"),
    ("deepseek-v3", "DeepSeek V3 (Dec 2024)", "2024-12"),
    ("deepseek-r1", "DeepSeek R1", "2025-01"),
    ("deepseek-v3-0324", "DeepSeek V3 (0324)", "2025-03"),
    ("deepseek-v3-2", "DeepSeek v3.2", "current"),
    ("kimi-k2", "Kimi K2", "2025-07"),
    ("kimi-k2-5", "Kimi K2.5", "current"),
]


def composite_score(r: dict) -> int:
    """Sum of positive contemplative-essayist markers, used to bin models
    into clearly-in / transitional / outside the attractor.

    The score is the sum of: There-is-a openings + the four title-template
    variants + threshold-family vocabulary + attention/noticing language +
    small-object vocabulary + afternoon-light references + canon references
    (Mary Oliver / Simone Weil / Annie Dillard / Keats) + Japanese aesthetic
    terms. All ten markers are positive signals of the contemplative-essayist
    mode. Anti-attractor markers (refusals, AI self-reference, helpful-
    assistant preambles, "certainly/tapestry") are NOT included in the score.
    """
    keys = (
        "opening_there_is_a", "title_quiet_x_of_y", "title_particular_peculiar",
        "title_architecture_of", "threshold_mentions", "attention_noticing",
        "small_objects", "afternoon_light", "mary_oliver_weil_dillard",
        "japanese_terms",
    )
    return sum(r.get(k, 0) for k in keys)


def main():
    # Positive contemplative-essayist markers (10 columns).
    # Anti-attractor markers (AI self-ref, refusals, "certainly/tapestry",
    # "below is a N-word" preambles) are computed but printed separately
    # below the main table to keep the headline picture clean.
    header = (f"{'Model':<20} {'Era':<12} {'N':>3} "
              f"{'TIA':>4} {'TiQu':>5} {'TiPP':>5} {'TiAr':>5} "
              f"{'Thr':>4} {'Attn':>5} {'Obj':>4} {'AftL':>5} "
              f"{'Cano':>5} {'Jap':>4} {'TOTAL':>6}")
    print(header)
    print("-" * len(header))
    for label, name, era in MODELS:
        r = analyze_model(label)
        if r is None:
            print(f"{name:<20} {era:<12} {'MISSING':>4}")
            continue
        score = composite_score(r)
        print(f"{name:<20} {era:<12} {r['samples']:>3} "
              f"{r['opening_there_is_a']:>4} "
              f"{r['title_quiet_x_of_y']:>5} "
              f"{r['title_particular_peculiar']:>5} "
              f"{r['title_architecture_of']:>5} "
              f"{r['threshold_mentions']:>4} "
              f"{r['attention_noticing']:>5} "
              f"{r['small_objects']:>4} "
              f"{r['afternoon_light']:>5} "
              f"{r['mary_oliver_weil_dillard']:>5} "
              f"{r['japanese_terms']:>4} "
              f"{score:>6}")
    print()
    print("Column key:")
    print("  TIA  = 'There is a / there's a' opening (first 400 chars)")
    print("  TiQu = title 'The/On the [Quiet/Unseen/Unquiet] X of Y'")
    print("  TiPP = title 'The/On the [Particular/Peculiar/Strange/Weight/...] X of Y'")
    print("  TiAr = title 'The/On the Architecture of X'")
    print("  Thr  = threshold / liminal / in-between / doorway / hinge")
    print("  Attn = noticing / attention to / pay attention / 'art of noticing'")
    print("  Obj  = small ordinary objects (paperclip, teapot, doorknob, kettle, ...)")
    print("  AftL = afternoon light, late afternoon, dusk, pre-dawn, golden hour")
    print("  Cano = Mary Oliver / Simone Weil / Annie Dillard / Keats / negative capability")
    print("  Jap  = Japanese aesthetic terms (mono no aware, wabi-sabi, kintsugi, ma, ...)")
    print("  TOTAL = sum of the ten positive markers above (composite attractor score)")
    print()

    # Anti-attractor markers, printed separately for completeness.
    print("Anti-attractor markers (printed separately):")
    print(f"{'Model':<20} {'AIself':>7} {'Refusal':>8} {'Cty':>5} {'BlwN':>5} {'HrIA':>5}")
    print("-" * 56)
    for label, name, _ in MODELS:
        r = analyze_model(label)
        if r is None:
            continue
        print(f"{name:<20} "
              f"{r['ai_selfref']:>7} "
              f"{r['refusal_do_not_feel_comfortable']:>8} "
              f"{r['certainly_delve_tapestry']:>5} "
              f"{r['meta_preamble_below_is']:>5} "
              f"{r['here_is_a_n_word']:>5}")
    print()
    print("  AIself  = 'as an AI', 'I am Claude/GPT/Gemini/Grok', lab self-references")
    print("  Refusal = 'I don't feel comfortable', 'I cannot/won't write', etc.")
    print("  Cty     = 'certainly', 'tapestry of', 'symphony of', stock helpful-assistant")
    print("  BlwN    = 'Below is a N-word piece...' meta-preamble")
    print("  HrIA    = 'Here is a/an N-word piece...' meta-preamble")


if __name__ == "__main__":
    main()
