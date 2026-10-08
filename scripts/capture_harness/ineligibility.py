"""BV1 ineligibility receipts, version bv1-ineligibility-v1 (2026-10-08).

A freeflow sample is *ineligible* for BV1-Luna when its source contains no
sentence-terminal punctuation at all, so no quotation can satisfy the evaluator
instruction ("a straightforward sentence ending in a period, question mark or
exclamation mark"). Ineligibility is a distinct outcome, never an evaluation:
no output file, no binding, and the sample is excluded from BV1 aggregation with
both counts disclosed.

Nothing here trusts the receipt. Every field except the reviewer reference is
recomputed from the current source, the current evaluator instruction and the
actual attempt directory, and must match exactly. A receipt that lists a subset
of attempts, or attempts that failed for any other reason, does not validate.
The reviewer reference authorises a receipt; it is not evidence.
"""
from __future__ import annotations

import hashlib, json, re, sqlite3
from pathlib import Path

VERSION = "bv1-ineligibility-v1"
REASON = "no_eligible_quotation_under_instruction"
QA_REASON = "quote_sentence_boundary"
LUNA_ARM = "bv1-luna-v1-20260929"
TEST = "no_sentence_terminal_punctuation"
TERMINAL = re.compile(r"[.!?…]")
FIELDS = (
    "version", "reason", "capture", "cell", "slug", "sample", "task",
    "evaluator_arm", "instruction_sha256", "source", "source_sha256",
    "eligibility", "attempts",
)


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def receipt_path(phase, sid) -> Path:
    return Path(phase) / "bv1_ineligible" / f"{sid}.json"


def coverage_path(phase) -> Path:
    return Path(phase) / "bv1_coverage.json"


def task_id(c, sid) -> str:
    return f"{c['label']}/bv1/{sid}"


def attempt_dir(bv_out, c, sid) -> Path:
    return Path(bv_out) / "attempt_responses" / (c["id_prefix"] + "_BV1_" + sid)


def eligibility(source_text: str) -> dict:
    return {"test": TEST, "ineligible": TERMINAL.search(source_text) is None}


def facts(c, sid, source, bv_out, arm_module) -> dict:
    """Everything a receipt asserts, recomputed from the world."""
    attempts = []
    for f in sorted(attempt_dir(bv_out, c, sid).glob("*.json")):
        r = json.loads(f.read_text())
        attempts.append(
            {
                "file": f.name,
                "sha256": sha256(f),
                "qa_pass": r.get("qa_pass"),
                "qa_reason": r.get("qa_reason"),
                "source_sha256": r.get("source_sha256"),
                "arm": r.get("arm"),
            }
        )
    return {
        "version": VERSION,
        "reason": REASON,
        "capture": c["id_prefix"],
        "cell": c["label"],
        "slug": c["slug"],
        "sample": sid,
        "task": task_id(c, sid),
        "evaluator_arm": c.get("bv1_evaluator"),
        "instruction_sha256": hashlib.sha256(arm_module.EXTRA.encode()).hexdigest(),
        "source": str(source),
        "source_sha256": sha256(source),
        "eligibility": eligibility(json.loads(Path(source).read_text())["result"]),
        "attempts": attempts,
    }


def check(receipt, c, sid, source, bv_out, arm_module, outpath, binding) -> dict:
    """Validate a receipt against current state; raise AssertionError if not."""
    expected = facts(c, sid, source, bv_out, arm_module)
    assert set(receipt) == set(FIELDS) | {"reviewer"}, "unexpected receipt fields"
    for k in FIELDS:
        assert receipt[k] == expected[k], f"ineligibility receipt field changed: {k}"
    assert isinstance(receipt["reviewer"], str) and receipt["reviewer"].strip(), "reviewer reference required"
    assert expected["evaluator_arm"] == LUNA_ARM, "receipts apply only to the BV1-Luna arm"
    assert expected["eligibility"]["ineligible"], "source has an eligible sentence ending"
    attempts = expected["attempts"]
    assert attempts, "no preserved attempts"
    for a in attempts:
        assert a["qa_pass"] is False, "an attempt passed QA"
        assert a["qa_reason"] == QA_REASON, f"attempt failed for another reason: {a['qa_reason']}"
        assert a["source_sha256"] == expected["source_sha256"], "attempt for another source"
        assert a["arm"] == LUNA_ARM, "attempt from another evaluator arm"
    assert not Path(outpath).exists(), "evaluation output exists for an ineligible sample"
    assert not Path(binding).exists(), "evaluation binding exists for an ineligible sample"
    return receipt


def check_history(state_db, task, attempts) -> list:
    """The receipt's attempts must be the task's whole history: one preserved
    response per started attempt, and the task never completed."""
    db = sqlite3.connect(f"file:{state_db}?mode=ro", uri=True)
    try:
        events = db.execute(
            "SELECT at,event,details FROM events WHERE id=? ORDER BY at", (task,)
        ).fetchall()
        row = db.execute("SELECT state,attempts FROM jobs WHERE id=?", (task,)).fetchone()
    finally:
        db.close()
    assert row is not None, "unknown task"
    started = [e for e in events if e[1] == "started"]
    assert not any(e[1] == "done" for e in events), "task completed at some point"
    assert row[0] == "blocked", "only a blocked task can be declared ineligible"
    assert len(started) == row[1] == len(attempts), (
        f"attempt history mismatch: {len(started)} started, {row[1]} counted, "
        f"{len(attempts)} preserved"
    )
    return events


def coverage(rows, expected_ids):
    """Gate on sample-id sets. Returns None for a complete run (no change to its
    artifacts), otherwise the coverage record for an incomplete one."""
    ids = [Path(r["sample_id"]).stem for r in rows]
    assert len(ids) == len(set(ids)), "duplicate sample ids"
    assert set(ids) == set(expected_ids), "sample ids differ from the expected set"
    evaluated = [i for i, r in zip(ids, rows) if not r.get("ineligible")]
    ineligible = [i for i, r in zip(ids, rows) if r.get("ineligible")]
    assert not set(evaluated) & set(ineligible), "sample both evaluated and ineligible"
    if not ineligible:
        return None
    assert evaluated, "no evaluable samples remain"
    cov = {
        "version": VERSION,
        "expected": len(ids),
        "evaluated": len(evaluated),
        "evaluated_ids": sorted(evaluated),
        "ineligible": [
            {"sample": i, "reason": REASON, "receipt_sha256": r["receipt_sha256"]}
            for i, r in sorted(zip(ids, rows), key=lambda p: p[0])
            if r.get("ineligible")
        ],
    }
    cov["disclosure"] = header(cov)
    return cov


def header(cov) -> str:
    """Card wording (Mira, 2026-10-08): name the BV1 subset, not the sample."""
    ids = ", ".join(i["sample"] for i in cov["ineligible"])
    n = len(cov["ineligible"])
    return (
        f"BV1 analysis: {cov['evaluated']}/{cov['expected']} freeflow samples evaluated. "
        f"{n} had no quotation eligible under the BV1-Luna instruction ({ids}); "
        "results describe the evaluable subset, and the exclusion is not claimed to be unbiased."
    )
