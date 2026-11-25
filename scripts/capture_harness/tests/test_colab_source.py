import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build as builder
import worker
from adopt_existing import adopt
from engine import Engine, atomic, digest
from metadata import write_metadata


class ColabSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for target in ("worker.RAW", "build.RAW"):
            p = patch(target, self.root / "raw")
            p.start()
            self.addCleanup(p.stop)
        # Any accidental raw or downstream request is a test failure.
        p = patch("httpx.post", side_effect=AssertionError("NO NETWORK"))
        self.http = p.start()
        self.addCleanup(p.stop)
        self.endpoints = ["http://127.0.0.1:33949/v1/chat/completions",
                          "http://127.0.0.1:41235/v1/chat/completions"]
        dep = dict(runtime="vllm-openai (colab)", runtime_version="vllm==test",
                   model_revision="5" * 40, weight_precision="bfloat16",
                   hardware="Google Colab A100", stop_sequence=None)
        self.c = dict(
            provider="local-openai", model="test/Model", label="test-colab",
            slug="test-colab", family="test", id_prefix="TEST", quantization="bfloat16",
            bv1_evaluator=worker.LUNA_ARM, phase_name="test-phase",
            phase=str(self.root / "phase"), analysis_root=str(self.root / "analysis"),
            source_adoption=dict(
                mode="colab-bf16", source_commit="c" * 40, model_revision="5" * 40,
                local_deployment=dep, endpoints=self.endpoints,
                counts={"freeflow": 125, "values": 120},
                sha256={p: {sid: "0" * 64 for sid in worker.identities(p)}
                        for p in ("freeflow", "values")}))
        self.save("values", "CTRL1_1", self.trace("values", "CTRL1_1"))
        self.save("freeflow", "SHORT_1", self.trace("freeflow", "SHORT_1"))

    def trace(self, probe, sid, endpoint=0):
        text = "Preserved answer for " + sid + "."
        usage = dict(prompt_tokens=10, completion_tokens=8, total_tokens=18)
        return dict(
            result=text, model=self.c["model"], model_requested=self.c["model"],
            provider="local-openai", condition=sid.rsplit("_", 1)[0],
            prompt=worker.prompts(probe)[sid.rsplit("_", 1)[0]],
            usage=usage,
            local_deployment=dict(self.c["source_adoption"]["local_deployment"],
                                  endpoint=self.endpoints[endpoint]),
            raw=dict(model=self.c["model"], usage=copy.deepcopy(usage),
                     choices=[dict(index=0, finish_reason="stop",
                                   message=dict(role="assistant", content=text))]))

    def save(self, probe, sid, d, repin=True):
        p = worker.trace_path(self.c, probe, sid)
        atomic(p, d)
        if repin:
            self.c["source_adoption"]["sha256"][probe][sid] = digest(p)
        return p

    def compile(self):
        run = self.root / "run"
        spec = builder.build(dict(run_id="test", models=[self.c]), run,
                             self.root / "analysis")
        config = run / "models" / (self.c["label"] + ".json")
        return run, spec, json.loads(config.read_text())

    def test_snapshot_hash_and_semantics_both_required(self):
        d = self.trace("values", "CTRL1_1")
        self.assertIsNone(worker.raw_problem(d, self.c, "values", "CTRL1_1"))
        p = worker.trace_path(self.c, "values", "CTRL1_1")
        p.write_bytes(p.read_bytes() + b" ")  # Same JSON is not same source.
        self.assertEqual(worker.raw_problem(d, self.c, "values", "CTRL1_1"), "source_sha256")
        with self.assertRaises(ValueError):
            worker.sample(self.c, "CTRL1_1")
        self.save("values", "CTRL1_1", d)
        wrong_snapshot = copy.deepcopy(d)
        wrong_snapshot["result"] = "Changed."
        self.assertEqual(worker.raw_problem(wrong_snapshot, self.c, "values", "CTRL1_1"),
                         "source_snapshot_mismatch")

    def test_exact_identity_prompt_completion_and_provenance(self):
        mutations = [
            lambda d: d.update(provider="openrouter"),
            lambda d: d.update(model="different"),
            lambda d: d.update(model_requested="different"),
            lambda d: d["raw"].update(model="different"),
            lambda d: d.update(condition="CTRL2"),
            lambda d: d.update(prompt=d["prompt"] + " "),
            lambda d: d.update(result="Different answer."),
            lambda d: d.update(error="failed"),
            lambda d: d["local_deployment"].update(model_revision="6" * 40),
            lambda d: d["local_deployment"].update(weight_precision="awq"),
            lambda d: d["local_deployment"].update(runtime_version="different"),
            lambda d: d["local_deployment"].update(hardware="different"),
            lambda d: d["local_deployment"].update(stop_sequence="stop"),
            lambda d: d["local_deployment"].update(extra="unapproved"),
            lambda d: d["local_deployment"].update(endpoint="http://127.0.0.1:5555/v1/chat/completions"),
            lambda d: d["raw"]["choices"].append(copy.deepcopy(d["raw"]["choices"][0])),
            lambda d: d["raw"]["choices"][0].update(finish_reason="length"),
            lambda d: d["raw"]["choices"][0].update(finish_reason="content_filter"),
            lambda d: d["raw"]["choices"][0]["message"].update(role="user"),
            lambda d: d["raw"]["choices"][0]["message"].update(tool_calls=[{}]),
            lambda d: d["raw"]["choices"][0]["message"].update(content=""),
            lambda d: d["raw"]["usage"].update(total_tokens=100),
            lambda d: d["raw"]["usage"].update(completion_tokens=True),
            lambda d: d.update(usage={}),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                d = self.trace("values", "CTRL1_1")
                mutate(d)
                self.save("values", "CTRL1_1", d)  # Even approved hash cannot excuse bad semantics.
                self.assertIsNotNone(worker.raw_problem(d, self.c, "values", "CTRL1_1"))
        for text in (" ", "\ufffd", "<|im_start|>x", "<|im_end|>", "<|endoftext|>"):
            d = self.trace("values", "CTRL1_1")
            d["result"] = d["raw"]["choices"][0]["message"]["content"] = text
            self.save("values", "CTRL1_1", d)
            self.assertIsNotNone(worker.raw_problem(d, self.c, "values", "CTRL1_1"))

    def test_complete_inventory_schema_and_no_or_capture_policy(self):
        mutations = [
            lambda c: c.pop("source_adoption"),
            lambda c: c.update(quantization="awq"),
            lambda c: c.update(or_provider="Qwen"),
            lambda c: c.update(reasoning_effort="none"),
            lambda c: c.update(token_policy={}),
            lambda c: c.update(route_max_tokens=16000),
            lambda c: c["source_adoption"].update(mode="capture"),
            lambda c: c["source_adoption"].update(source_commit="c52ad1321"),
            lambda c: c["source_adoption"].update(model_revision="branch"),
            lambda c: c["source_adoption"]["counts"].update(freeflow=124),
            lambda c: c["source_adoption"]["sha256"]["values"].pop("CTRL1_1"),
            lambda c: c["source_adoption"]["sha256"]["values"].update(EXTRA_1="0" * 64),
            lambda c: c["source_adoption"]["sha256"]["values"].update(CTRL1_1="not-a-hash"),
            lambda c: c["source_adoption"]["local_deployment"].update(endpoint=self.endpoints[0]),
        ]
        worker.validate_source_config(self.c)
        for mutate in mutations:
            c = copy.deepcopy(self.c)
            mutate(c)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                worker.validate_source_config(c)

    def test_enumerated_endpoints_are_strict_and_never_connected(self):
        for i in range(2):
            d = self.trace("values", "CTRL1_1", i)
            self.save("values", "CTRL1_1", d)
            worker.raw_collect(self.c, self.root / "phase", "values", "CTRL1_1")
        for endpoint in [
            "https://127.0.0.1:123/v1/chat/completions",
            "http://localhost:123/v1/chat/completions",
            "http://127.0.0.1:0/v1/chat/completions",
            "http://127.0.0.1:65536/v1/chat/completions",
            "http://127.0.0.1:0123/v1/chat/completions",
            "http://user@127.0.0.1:123/v1/chat/completions",
            self.endpoints[0] + "?x=1", self.endpoints[0] + "#fragment",
            self.endpoints[0] + "/", "http://127.0.0.1:123/v1/%63hat/completions",
            None, 123,
        ]:
            c = copy.deepcopy(self.c)
            c["source_adoption"]["endpoints"] = [endpoint]
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                worker.validate_source_config(c)
        self.http.assert_not_called()

    def test_raw_action_read_only_even_missing_invalid_or_malformed_config(self):
        phase = self.root / "must-not-be-created"
        p = worker.trace_path(self.c, "values", "CTRL1_1")
        original = p.read_bytes()
        worker.raw_collect(self.c, phase, "values", "CTRL1_1")
        self.assertEqual(p.read_bytes(), original)
        self.assertFalse(phase.exists())
        for content in (b"{}", b"not JSON", b"null", b"[]", None):
            if content is None:
                p.unlink()
            else:
                p.write_bytes(content)
            with self.subTest(content=content), self.assertRaises(SystemExit) as cm:
                worker.raw_collect(self.c, phase, "values", "CTRL1_1")
            self.assertEqual(cm.exception.code, 21)
            self.assertFalse(phase.exists())
            if content is not None:
                self.assertEqual(p.read_bytes(), content)
        for change in ({"source_adoption": None}, {"provider": "openrouter"},
                       {"source_adoption": {}}, {"or_provider": "Qwen"}):
            c = dict(self.c, **change)
            with self.assertRaises(SystemExit):
                worker.raw_collect(c, phase, "values", "CTRL1_1")
        c = copy.deepcopy(self.c)
        del c["source_adoption"]
        with self.assertRaises(SystemExit):
            worker.raw_collect(c, phase, "values", "CTRL1_1")
        self.http.assert_not_called()

    def test_builder_retains_pipeline_but_raw_is_local_once(self):
        run, spec, c = self.compile()
        raw = [t for t in spec["tasks"] if t["command"][3] == "raw"]
        self.assertEqual(len(raw), 245)
        self.assertTrue(all(t["pool"] == "local" and t["max_attempts"] == 1
                            and t["timeout"] == 60 for t in raw))
        tasks = {t["id"]: t for t in spec["tasks"]}
        label = self.c["label"]
        self.assertEqual(tasks[label + "/bv1/SHORT_1"]["deps"], [label + "/freeflow/SHORT_1"])
        self.assertEqual(tasks[label + "/a/CTRL1_1/kimi-k2-6"]["deps"], [label + "/values/CTRL1_1"])
        self.assertEqual(c["source_adoption"], self.c["source_adoption"])
        self.assertEqual(spec["input_hashes"][str(run / "models/test-colab.json")],
                         digest(run / "models/test-colab.json"))

    def test_adoption_checks_hash_at_actual_invocation_and_preserves_live_lease(self):
        run, spec, c = self.compile()
        e = Engine(spec, run / "state")
        self.addCleanup(e.lock.close)
        self.addCleanup(e.db.close)
        sid = self.c["label"] + "/freeflow/SHORT_1"
        e.db.execute("UPDATE jobs SET state='running',attempts=1 WHERE id=?", (sid,))
        e.db.commit()
        # Alter source *after compilation*, keeping otherwise valid JSON/semantics.
        p = worker.trace_path(c, "values", "CTRL1_1")
        b = p.read_bytes()
        p.write_bytes(b + b"\n")
        self.assertEqual(adopt(run / "spec.json", run / "state"), 0)
        p.write_bytes(b)
        self.assertEqual(adopt(run / "spec.json", run / "state"), 1)
        row = e.db.execute("SELECT * FROM jobs WHERE id=?",
                           (self.c["label"] + "/values/CTRL1_1",)).fetchone()
        self.assertEqual(row["state"], "done")
        self.assertEqual(row["attempts"], 0)
        self.assertEqual(json.loads(row["receipts"]), {str(p.resolve()): digest(p)})
        self.assertEqual(e.db.execute("SELECT state FROM jobs WHERE id=?", (sid,)).fetchone()[0],
                         "running")
        self.http.assert_not_called()

    def test_values_and_bv1_keep_local_source_identity_and_validate_hashes(self):
        row = worker.sample(self.c, "CTRL1_1")
        self.assertEqual(row["provider"], "local-openai")
        self.assertEqual(row["source_sha256"],
                         self.c["source_adoption"]["sha256"]["values"]["CTRL1_1"])
        phase = Path(self.c["phase"])
        bv_out, outputs, bindings = worker.bv1_paths(self.c, phase)
        bv_out.mkdir(parents=True)
        out = outputs / self.c["label"] / "SHORT_1.md"
        out.parent.mkdir(parents=True)
        out.write_text("Mocked BV1 output.")
        atomic(bindings / "SHORT_1.json", dict(
            source_sha256=digest(worker.trace_path(self.c, "freeflow", "SHORT_1")),
            output_sha256=digest(out), evaluator_arm=worker.LUNA_ARM))
        arm = SimpleNamespace(valid_output=lambda *a: (True, "ok"))
        with patch("worker.module", side_effect=[SimpleNamespace(), arm]):
            bv = worker.bv1(self.c, phase, "SHORT_1", validate=True)
        self.assertEqual(bv["provider"], "local-openai")
        self.assertEqual(bv["evaluator_arm"], worker.LUNA_ARM)
        p = worker.trace_path(self.c, "freeflow", "SHORT_1")
        p.write_bytes(p.read_bytes() + b" ")
        with patch("worker.module", return_value=SimpleNamespace()), self.assertRaises(ValueError):
            worker.bv1(self.c, phase, "SHORT_1", validate=True)
        self.http.assert_not_called()

    def test_metadata_preserves_source_provenance_without_fake_or_route(self):
        write_metadata(self.c)
        write_metadata(self.c, validate=True)
        record = json.loads((Path(self.c["phase"]) / "model_metadata.json").read_text())
        self.assertEqual(record["provider"], "local-openai")
        self.assertIsNone(record["or_provider"])
        self.assertEqual(record["source_adoption"], self.c["source_adoption"])


if __name__ == "__main__":
    unittest.main()
