import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class CredentialLoaderTests(unittest.TestCase):
    def run_loader(self, fake_sops):
        loader = Path(__file__).resolve().parents[2] / "source_sops_keys.sh"
        with tempfile.TemporaryDirectory() as td:
            sops = Path(td) / "sops"
            sops.write_text("#!/bin/sh\n" + fake_sops + "\n")
            sops.chmod(0o700)
            return subprocess.run(
                ["bash", "-c", 'source "$1" || exit $?; printf "worker:%s" "$TEST_CORPUS_KEY"',
                 "test", str(loader)],
                env={**os.environ, "PATH": td + os.pathsep + os.environ["PATH"]},
                capture_output=True, text=True,
            )

    def test_decryption_failure_does_not_start_worker(self):
        result = self.run_loader("exit 42")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("worker:", result.stdout)

    def test_success_exports_without_printing_secret(self):
        result = self.run_loader("""printf '%s' '{"TEST_CORPUS_KEY":"test-only"}'""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "worker:test-only")
