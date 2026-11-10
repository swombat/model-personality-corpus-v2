"""Offline BV1-Luna v1.2 revalidation lane (analysis issue #1; Mira jRyQzQ):
no calls, reviewed occurrence, own arm, provenance, receipt, idempotent repeat.
Same fixture as test_ineligibility_flow, with X_1 punctuated and blocked after 4
v1 attempts that failed only on quote_sentence_boundary."""
import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ineligibility as INEL
import worker
from apply_luna_v1_1 import tree_fingerprint
from engine import atomic, digest
from test_ineligibility_flow import Flow, LABEL
import apply_bv1_offline as LANE

STUB = """import hashlib, json
from pathlib import Path
ARM = 'bv1-luna-v1.2-offline-20261110'
VALIDATOR = 'bv1-luna-v1.2-validator-20261110'
ORIGINAL_ARM = 'bv1-luna-v1-20260929'
def _sha(b): return hashlib.sha256(b).hexdigest()
def code_sha256(): return _sha(Path(__file__).read_bytes())
def payload(row): return {'req': 'v1', 'condition': row['condition'], 'text': row['text']}
def request_sha256(row): return _sha(json.dumps(payload(row), sort_keys=True).encode())
def transport_valid(status, resp): return status == 200 and resp.get('ok') is True
def attempt_text(rec): return (rec.get('response') or {}).get('text') or ''
def _quote(text):
    for line in text.splitlines():
        if line.startswith('> '): return line[2:]
def closed_quote_starts(source, quote):
    return [] if not quote or quote not in source or quote.startswith('lower') else [source.index(quote)]
def valid_output(text, source=None):
    if not text.startswith('## ok'): return False, 'structure'
    if source is None: return True, ''
    q = _quote(text)
    return (True, '') if q and closed_quote_starts(source, q) else (False, 'quote_sentence_boundary')
def provenance_path(out): return Path(str(out) + '.provenance.json')
def provenance_ok(out, row):
    p = provenance_path(out)
    if not p.exists() or not Path(out).exists(): return False
    d = json.loads(p.read_text()); a = Path(d['attempt_file'])
    return (d['arm'] == ARM and d['validator_code_sha256'] == code_sha256() and a.exists()
            and _sha(a.read_bytes()) == d['attempt_sha256'] and _sha(Path(out).read_bytes()) == d['output_sha256'])
def process(row, outdir):
    out = Path(row['outpath'])
    if out.exists() and provenance_ok(out, row): return
    raise RuntimeError('offline arm never generates')
"""
TASK = f"{LABEL}/bv1/X_1"
AUTH = "mira-test-offline"
GOOD = "## ok evaluation\n## Evidence line\n> It has sentences.\n"


class OfflineLaneTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.flow = None

    def tearDown(self):
        if self.flow:
            self.flow.close()
        self.td.cleanup()

    def make(self, text=GOOD, mutate=None):
        f = self.flow = Flow(self.td.name, unpunctuated_x=False)
        bv = f.root / "analysis/freeflow/personality-eval-bv1"
        (bv / "luna_v1_2.py").write_text(STUB)
        src = f.traces / "freeflow/X_1.json"
        d = INEL.attempt_dir(worker.bv1_paths(f.c, f.phase, worker.LUNA_ARM)[0], f.c, "X_1")
        payload = {"req": "v1", "condition": "X", "text": json.loads(src.read_text())["result"]}
        for i, p in enumerate(sorted(d.glob("*.json"))):
            rec = {"arm": worker.LUNA_ARM, "sample_id": f"{LABEL}/X_1.json", "source_sha256": digest(src),
                   "http_status": "200", "request": payload, "response": {"ok": True, "text": text},
                   "qa_pass": False, "qa_reason": "quote_sentence_boundary"}
            if mutate:
                mutate(i, rec)
            atomic(p, rec)
        return f

    def lane(self, f, **kw):
        kw.setdefault("authorization", AUTH)
        return LANE.apply(f.run / "spec.json", f.run / "state", TASK, **kw)

    def start(self, f):
        return json.loads((f.traces / "freeflow/X_1.json").read_text())["result"].index("It has sentences.")

    def state(self, f, id=TASK):
        return f.engine.db.execute("SELECT state,reason FROM jobs WHERE id=?", (id,)).fetchone()

    def v1(self, f):
        return tree_fingerprint(INEL.attempt_dir(worker.bv1_paths(f.c, f.phase, worker.LUNA_ARM)[0], f.c, "X_1"))

    def test_check_selects_first_attempt_and_writes_nothing(self):
        f = self.make()
        before = self.v1(f)
        sel = self.lane(f, check_only=True)
        self.assertEqual(sel["selected"]["file"].split("/")[-1], "100.json")
        self.assertEqual(sel["selected"]["accepted_starts"], [self.start(f)])
        self.assertIn("It has sentences.", list(sel["selected"]["contexts"].values())[0])
        self.assertEqual((sel["writes"], sel["model_calls"]), (0, 0))
        self.assertFalse(worker.bv1_paths(f.c, f.phase, worker.LUNA_V12_OFFLINE_ARM)[1].exists())
        self.assertEqual(self.state(f)[0], "blocked")
        self.assertEqual(self.v1(f), before)

    def test_apply_needs_authorization_and_a_reviewed_accepted_occurrence(self):
        f = self.make()
        with self.assertRaisesRegex(AssertionError, "authorization"):
            self.lane(f, authorization=None, occurrence=self.start(f))
        with self.assertRaisesRegex(AssertionError, "occurrence"):
            self.lane(f)
        with self.assertRaisesRegex(AssertionError, "occurrence"):
            self.lane(f, occurrence=self.start(f) + 1)
        self.assertEqual(self.state(f)[0], "blocked")

    def test_apply_binds_and_releases_dependency_blocked_descendants(self):
        f = self.make()
        before = self.v1(f)
        sel = self.lane(f, occurrence=self.start(f))
        self.assertTrue(sel["applied"])
        state, reason = self.state(f)
        self.assertEqual(state, "done")
        self.assertEqual(reason, f"evaluated: {worker.LUNA_V12_OFFLINE_ARM} (offline revalidation {AUTH})")
        self.assertEqual(self.state(f, f"{LABEL}/synthesis")[0], "pending")
        self.assertEqual(self.state(f, f"{LABEL}/ready")[0], "pending")  # as the targeted lane: the engine orders deps
        out = Path(sel["output"])
        self.assertEqual(out.read_text(), GOOD)
        self.assertIn("/arms/" + worker.LUNA_V12_OFFLINE_ARM + "/outputs/", str(out))
        self.assertEqual(json.loads(Path(sel["binding"]).read_text())["evaluator_arm"], worker.LUNA_V12_OFFLINE_ARM)
        receipt = json.loads(Path(sel["receipt"]).read_text())
        self.assertEqual(receipt["authorization"], AUTH)
        self.assertEqual(receipt["occurrence"]["quote"], "It has sentences.")
        self.assertEqual(receipt["original_arm"], worker.LUNA_ARM)
        self.assertEqual(self.v1(f), before)
        self.assertEqual(worker.bv1(f.c, f.phase, "X_1", True)["evaluator_arm"], worker.LUNA_V12_OFFLINE_ARM)
        self.assertEqual(worker.bv1_ready_fields(f.c, f.phase)["bv1_variant_arms"], {"X_1": worker.LUNA_V12_OFFLINE_ARM})

    def test_repeat_invocation_is_a_verified_noop(self):
        f = self.make()
        self.lane(f, occurrence=self.start(f))
        r = self.lane(f, occurrence=self.start(f))
        self.assertTrue(r["noop"])

    def test_repeat_after_altered_attempt_or_validator_fails(self):
        f = self.make()
        sel = self.lane(f, occurrence=self.start(f))
        att = Path(json.loads(Path(sel["receipt"]).read_text())["attempt_file"])
        att.write_text(att.read_text().replace("200", "201"))
        with self.assertRaises(AssertionError):
            self.lane(f)
        f2 = self.flow
        stub = f2.root / "analysis/freeflow/personality-eval-bv1/luna_v1_2.py"
        att.write_text(att.read_text().replace("201", "200"))
        stub.write_text(STUB + "\n# changed\n")
        with self.assertRaises(AssertionError):
            self.lane(f)

    def test_altered_source_has_no_eligible_attempt(self):
        f = self.make()
        atomic(f.traces / "freeflow/X_1.json", {"result": "Sample X_1. It has sentences!", "condition": "X"})
        self.assertIsNone(self.lane(f, check_only=True)["selected"])
        with self.assertRaisesRegex(AssertionError, "no eligible"):
            self.lane(f, occurrence=0)

    def test_wrong_sample_non_boundary_failure_and_other_arm_are_ineligible(self):
        def mutate(i, rec):
            if i == 0: rec["sample_id"] = f"{LABEL}/X_2.json"
            if i == 1: rec["qa_reason"] = "invalid_kind"
            if i == 2: rec["arm"] = worker.LUNA_TARGETED_ARM
        f = self.make(mutate=mutate)
        sel = self.lane(f, check_only=True)
        flags = [c["eligible"] for c in sel["candidates"]]
        self.assertEqual(flags, [False, False, False, True])
        self.assertEqual(sel["selected"]["file"].split("/")[-1], "103.json")

    def test_no_transport_or_structure_waiver(self):
        f = self.make(text="## bad\n> It has sentences.\n")
        self.assertIsNone(self.lane(f, check_only=True)["selected"])
        f.close(); self.flow = None; self.td.cleanup(); self.td = tempfile.TemporaryDirectory()
        f = self.make(mutate=lambda i, rec: rec.update(http_status="500"))
        self.assertIsNone(self.lane(f, check_only=True)["selected"])

    def test_dependency_blocked_and_targeted_bound_tasks_refused(self):
        f = self.make()
        with self.assertRaises(Exception):
            LANE.apply(f.run / "spec.json", f.run / "state", f"{LABEL}/synthesis", AUTH, 0)
        atomic(worker.bv1_paths(f.c, f.phase, worker.LUNA_TARGETED_ARM)[2] / "X_1.json", {"x": 1})
        with self.assertRaisesRegex(AssertionError, "targeted binding"):
            self.lane(f, occurrence=self.start(f))

    def test_dag_never_routes_to_the_offline_arm_unbound(self):
        f = self.make()
        with self.assertRaises(Exception):
            worker.bv1(f.c, f.phase, "X_1", True)
        self.assertFalse(worker.bv1_paths(f.c, f.phase, worker.LUNA_V12_OFFLINE_ARM)[1].exists())


if __name__ == "__main__":
    unittest.main()
