"""Exercise launcher behavior with a fake CLI; never invoke a model or GitHub."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNNER = Path(__file__).resolve().parents[1] / "skills/astra-plus-muse/scripts/run_muse.py"
FAKE = '''#!{python}
import json, os, pathlib, sys
if sys.argv[1:] == ["exec", "--help"]:
    print("--yolo --model --reasoning-effort --max-model-steps "
          "--max-tool-output-bytes --workspace --prompt-file --json"
          if not os.environ.get("MISSING_FLAGS") else "--model")
    sys.exit(0)
pathlib.Path(os.environ["CAPTURE"]).write_text(json.dumps(sys.argv[1:]))
print(json.dumps({{"type": "completed", "cwd": os.getcwd()}}))
with pathlib.Path(os.environ["CAPTURE"] + ".calls").open("a") as calls:
    calls.write("called\\n")
print(os.environ.get("WORKER_DIAGNOSTIC", "worker diagnostic"), file=sys.stderr)
sys.exit(int(os.environ.get("WORKER_EXIT", "0")))
'''


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "work tree"
        self.workspace.mkdir()
        self.prompt = self.root / "prompt with spaces.md"
        self.prompt.write_text("Issue text: `literal` $(not-shell-code)\n")
        self.output = self.root / "logs"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        muse = self.bin / "muse"
        muse.write_text(FAKE.format(python=sys.executable))
        muse.chmod(0o755)
        self.capture = self.root / "argv.json"
        self.env = {**os.environ, "PATH": str(self.bin), "CAPTURE": str(self.capture)}

    def run_launcher(self, *extra):
        return subprocess.run(
            [sys.executable, str(RUNNER), "--workspace", str(self.workspace),
             "--prompt-file", str(self.prompt), "--output-dir", str(self.output), *extra],
            env=self.env, capture_output=True, text=True,
        )

    def test_launches_explicit_model_yolo_and_limits_with_literal_paths(self):
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        args = json.loads(self.capture.read_text())
        self.assertEqual(args, [
            "exec", "--yolo", "--model", "muse-spark-1.3-contributor",
            "--reasoning-effort", "xhigh", "--max-model-steps", "40",
            "--max-tool-output-bytes", "12000", "--workspace", str(self.workspace),
            "--prompt-file", str(self.prompt), "--json",
        ])
        self.assertEqual(json.loads((self.output / "events.jsonl").read_text())["cwd"],
                         str(self.workspace))
        self.assertEqual((self.output / "stderr.log").read_text(), "worker diagnostic\n")
        self.assertNotIn("worker diagnostic", result.stdout + result.stderr)
        self.assertNotIn('"type": "completed"', result.stdout)
        self.assertEqual(json.loads((self.output / "result.json").read_text())["returncode"], 0)

    def test_failed_worker_keeps_evidence_and_nonzero_status(self):
        self.env["WORKER_EXIT"] = "7"
        result = self.run_launcher()
        self.assertEqual(result.returncode, 7)
        self.assertEqual(json.loads((self.output / "result.json").read_text())["returncode"], 7)
        self.assertTrue((self.output / "events.jsonl").is_file())

    def test_rejected_max_preserves_failure_without_retry_or_downgrade(self):
        diagnostic = ("API error 400: reasoning_effort max requires an active "
                      "Muse Code subscription for model muse-spark-1.3-contributor")
        self.env.update(WORKER_EXIT="1", WORKER_DIAGNOSTIC=diagnostic)
        result = self.run_launcher("--reasoning-effort", "max")
        self.assertEqual(result.returncode, 1)
        invocation = json.loads((self.output / "invocation.json").read_text())["argv"]
        self.assertEqual(invocation[invocation.index("--reasoning-effort") + 1], "max")
        self.assertEqual(invocation[invocation.index("--model") + 1],
                         "muse-spark-1.3-contributor")
        self.assertEqual(json.loads((self.output / "result.json").read_text())["returncode"], 1)
        self.assertIn(diagnostic, (self.output / "stderr.log").read_text())
        self.assertEqual(Path(str(self.capture) + ".calls").read_text().splitlines(), ["called"])

    def test_existing_attempt_is_not_overwritten_or_relaunched(self):
        self.output.mkdir()
        evidence = self.output / "result.json"
        evidence.write_text("prior evidence")
        result = self.run_launcher()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(evidence.read_text(), "prior evidence")
        self.assertFalse(self.capture.exists())

    def test_incompatible_cli_stops_before_launch(self):
        self.env["MISSING_FLAGS"] = "1"
        result = self.run_launcher()
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.capture.exists())
        self.assertFalse(self.output.exists())

    def test_missing_cli_is_reported_without_fallback(self):
        (self.bin / "muse").unlink()
        result = self.run_launcher()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Muse CLI is missing", result.stderr)

    def test_empty_prompt_stops_before_launch(self):
        self.prompt.write_text("")
        result = self.run_launcher()
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.capture.exists())

    def test_nonpositive_budget_stops_before_launch(self):
        for value in ["0", "-1"]:
            with self.subTest(value=value):
                result = self.run_launcher("--max-model-steps", value)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(self.capture.exists())

    def test_explicit_overrides_are_used(self):
        result = self.run_launcher("--max-model-steps", "12", "--reasoning-effort", "high")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = json.loads(self.capture.read_text())
        self.assertEqual(args[args.index("--max-model-steps") + 1], "12")
        self.assertEqual(args[args.index("--reasoning-effort") + 1], "high")


if __name__ == "__main__":
    unittest.main()
