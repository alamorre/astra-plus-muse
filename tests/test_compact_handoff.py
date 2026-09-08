"""Exercise compact-handoff rendering, budget, measurement, and CLI behavior."""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "skills/astra-plus-muse/scripts"))
import compact_handoff as ch


HELPER = Path(__file__).resolve().parents[1] \
    / "skills/astra-plus-muse/scripts/compact_handoff.py"


def sample(kind="initial"):
    return {
        "kind": kind,
        "task_url": "https://github.com/o/r/issues/1",
        "pr_url": "https://github.com/o/r/pull/2",
        "target": "main",
        "base_sha": "a" * 40,
        "head_sha": "b" * 40,
        "state": "done",
        "changed_files": ["skills/x/SKILL.md", "tests/test_x.py"],
        "checks": [
            {"name": "unittest", "returncode": 0, "log": "runs/t1.log"},
        ],
        "findings": "none",
        "next_action": "astra review head",
    }


def split_marker(bounded):
    """Split bounded output into (head, marker); the marker is complete."""
    index = bounded.rfind("\n[truncated")
    assert index >= 0, "truncation marker missing"
    return bounded[:index], bounded[index:]


def displayed_omitted(marker):
    return int(re.search(r"omitted (\d+) bytes", marker).group(1))


class CompactHandoffTests(unittest.TestCase):
    def test_small_payload_is_unbounded_and_measured(self):
        text = ch.render_text(sample())
        bounded, truncated, omitted = ch.render(sample())
        self.assertFalse(truncated)
        self.assertEqual(omitted, 0)
        self.assertEqual(bounded, text)
        self.assertEqual(ch.measure_bytes(bounded), len(bounded.encode("utf-8")))
        self.assertLessEqual(ch.measure_bytes(bounded), ch.DEFAULT_BUDGET_BYTES)

    def test_large_payload_is_bounded_with_visible_continuation(self):
        payload = sample(kind="revised")
        payload["changed_files"] = [f"src/mod{i:03d}.py" for i in range(300)]
        payload["continuation"] = "task-runs/issue-1/handoff.json"
        bounded, truncated, omitted = ch.render(payload, budget_bytes=2000)
        self.assertTrue(truncated)
        self.assertGreater(omitted, 0)
        self.assertLessEqual(ch.measure_bytes(bounded), 2000)
        self.assertIn("truncated: omitted", bounded)
        self.assertIn("task-runs/issue-1/handoff.json", bounded)
        self.assertIn("not reviewed", bounded)

    def test_missing_required_field_is_rejected(self):
        payload = sample()
        del payload["head_sha"]
        with self.assertRaises(ValueError):
            ch.render_text(payload)

    def test_missing_checks_are_not_a_pass(self):
        payload = sample()
        payload["checks"] = []
        text = ch.render_text(payload)
        self.assertIn("not-run", text)
        self.assertNotIn("rc=0", text)

    def test_skipped_check_keeps_actual_rc_zero(self):
        # A command can exit 0 while skipping its tests; the handoff
        # preserves that evidence and says skipped, never implypass.
        payload = sample()
        payload["checks"] = [{"name": "e2e", "returncode": 0,
                              "status": "skipped", "log": "runs/e2e.log"}]
        text = ch.render_text(payload)
        self.assertIn("- e2e: rc=0 (skipped) @runs/e2e.log", text)
        payload["checks"] = [{"name": "e2e", "returncode": 2, "status": "skipped",
                              "log": "runs/e2e.log"}]
        self.assertIn("skipped", ch.render_text(payload))

    def test_not_run_check_may_omit_returncode(self):
        payload = sample()
        payload["checks"] = [{"name": "ci", "status": "not-run"}]
        text = ch.render_text(payload)
        self.assertIn("(not-run)", text)
        self.assertNotIn("rc=", text)
        self.assertNotIn("pass", text.lower())
        # Any other status still needs its return code.
        payload["checks"] = [{"name": "ci", "status": "passed"}]
        with self.assertRaises(ValueError):
            ch.render_text(payload)

    def test_non_object_inputs_raise_value_error(self):
        for bad in ([], "x", None, 7):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    ch.render(bad)
        payload = sample()
        payload["checks"] = "unittest"
        with self.assertRaises(ValueError):
            ch.render_text(payload)
        payload["checks"] = [{"name": "x", "returncode": 0, "log": 7}]
        with self.assertRaises(ValueError):
            ch.render_text(payload)
        with self.assertRaises(ValueError):
            ch.enforce_budget(b"text", 2000)

    def test_measurement_is_reproducible(self):
        first = ch.measure_bytes(ch.render_text(sample(kind="unchanged")))
        second = ch.measure_bytes(ch.render_text(sample(kind="unchanged")))
        self.assertEqual(first, second)


class BudgetCorrectnessTests(unittest.TestCase):
    def check_case(self, text, budget, continuation):
        bounded, truncated, omitted = ch.enforce_budget(
            text, budget_bytes=budget, continuation=continuation)
        total = len(text.encode("utf-8"))
        self.assertTrue(truncated)
        out_bytes = len(bounded.encode("utf-8"))
        self.assertLessEqual(out_bytes, budget)
        head, marker = split_marker(bounded)
        # Complete marker: full pointer and review status survive.
        self.assertIn(continuation, marker)
        self.assertIn("not reviewed", marker)
        self.assertTrue(marker.endswith("]\n"))
        # Displayed, returned, and actual omitted bytes agree exactly.
        actual = total - len(head.encode("utf-8"))
        self.assertEqual(displayed_omitted(marker), omitted)
        self.assertEqual(omitted, actual)
        self.assertEqual(omitted, total - len(head.encode("utf-8")))
        head.encode("utf-8")  # head is intact text on a boundary
        return bounded, omitted

    def test_ascii_counts_are_exact(self):
        _, omitted = self.check_case("A" * 5000, 2000, "handoff.json")
        self.assertEqual(omitted, 5000 - len(("A" * 5000)[:2000 - 159].encode()))

    def test_exact_boundary_is_not_truncated(self):
        bounded, truncated, omitted = ch.enforce_budget("A" * 2000, 2000)
        self.assertFalse(truncated)
        self.assertEqual(omitted, 0)
        self.assertEqual(bounded, "A" * 2000)

    def test_default_budget_applies(self):
        bounded, truncated, omitted = ch.enforce_budget(
            "A" * 5000, continuation="handoff.json")
        self.assertTrue(truncated)
        self.assertLessEqual(len(bounded.encode("utf-8")),
                             ch.DEFAULT_BUDGET_BYTES)

    def test_multibyte_input_stays_within_byte_budget(self):
        bounded, omitted = self.check_case("資料" * 1000, 2000, "handoff.json")
        # Character slicing would exceed the byte budget; bytes do not.
        self.assertLessEqual(len(bounded.encode("utf-8")), 2000)
        head, _ = split_marker(bounded)
        # Multibyte characters survive intact on the head.
        self.assertIn("資料", head)
        self.assertLess(len(head), len(head.encode("utf-8")))

    def test_multibyte_continuation_pointer_survives_whole(self):
        self.check_case("A" * 5000, 2000, "資料/継続.json")

    def test_small_budget_raises_instead_of_partial_marker(self):
        with self.assertRaises(ValueError):
            ch.enforce_budget("A" * 5000, 100, "handoff.json")
        with self.assertRaises(ValueError):
            ch.enforce_budget("A" * 5000, 0, "handoff.json")

    def test_truncation_without_pointer_fails_loudly(self):
        # No invented placeholder: truncation with no actual pointer
        # raises instead of pointing at nothing.
        with self.assertRaises(ValueError):
            ch.enforce_budget("A" * 5000, 2000)
        with self.assertRaises(ValueError):
            ch.enforce_budget("A" * 5000, 2000, continuation="")
        payload = sample(kind="revised")
        payload["changed_files"] = [f"src/mod{i:03d}.py" for i in range(300)]
        self.assertNotIn("continuation", payload)
        with self.assertRaises(ValueError):
            ch.render(payload, budget_bytes=2000)
        # Short output still needs no pointer at all.
        bounded, truncated, omitted = ch.render(sample())
        self.assertFalse(truncated)
        self.assertEqual(omitted, 0)
        self.assertNotIn("truncated", bounded)

    def test_never_oversized_across_budgets_and_scripts(self):
        texts = ["A" * 5000, "資料" * 1000, "é" * 700 + "A" * 3000,
                 "x" * 1999 + "資料" * 500]
        for text in texts:
            total = len(text.encode("utf-8"))
            for budget in (200, 201, 1000, 1999, 2000, 2001, 10000):
                with self.subTest(total=total, budget=budget):
                    if total <= budget:
                        bounded, truncated, omitted = ch.enforce_budget(
                            text, budget, continuation="handoff.json")
                        self.assertFalse(truncated)
                        self.assertEqual(omitted, 0)
                        continue
                    try:
                        bounded, _, omitted = ch.enforce_budget(
                            text, budget, continuation="handoff.json")
                    except ValueError:
                        continue  # marker cannot fit: honest refusal
                    self.assertLessEqual(len(bounded.encode("utf-8")), budget)
                    head, marker = split_marker(bounded)
                    self.assertEqual(displayed_omitted(marker), omitted)
                    self.assertEqual(omitted, total - len(head.encode()))


class MeasurementFixtureTests(unittest.TestCase):
    def test_shaped_fixture_emits_actual_sizes(self):
        fixture = ch.measurement_fixture()
        print(f"\ncompact={fixture['compact_bytes']} "
              f"verbose={fixture['verbose_bytes']} "
              f"truncated={fixture['bounded_bytes']} "
              f"omitted={fixture['omitted']}")
        self.assertEqual(fixture["compact_bytes"], 395)
        self.assertEqual(fixture["verbose_bytes"], 37195)
        self.assertEqual(fixture["bounded_bytes"], 2000)
        self.assertEqual(fixture["omitted"], 35373)
        self.assertTrue(fixture["truncated"])
        self.assertIn(fixture["continuation"], fixture["bounded_text"])
        head, marker = split_marker(fixture["bounded_text"])
        self.assertEqual(displayed_omitted(marker), fixture["omitted"])
        self.assertEqual(fixture["omitted"],
                         fixture["verbose_bytes"] - len(head.encode("utf-8")))

    def test_all_four_kinds_render_within_default_budget(self):
        for kind in ("initial", "unchanged", "revised", "stopped-without-pr"):
            with self.subTest(kind=kind):
                payload = ch.example_payload(kind)
                bounded, truncated, omitted = ch.render(payload)
                self.assertFalse(truncated, kind)
                self.assertEqual(omitted, 0, kind)
                self.assertLessEqual(ch.measure_bytes(bounded),
                                     ch.DEFAULT_BUDGET_BYTES, kind)


class HelperCliTests(unittest.TestCase):
    def run_cli(self, *argv):
        return subprocess.run(
            [sys.executable, str(HELPER), *argv],
            capture_output=True, text=True, timeout=60)

    def test_cli_renders_handoff_json_within_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.json"
            path.write_text(json.dumps(sample()), encoding="utf-8")
            result = self.run_cli(str(path), "--budget", "2000")
            self.assertEqual(result.returncode, 0, result.stderr)
            expected, _, _ = ch.render(sample(), budget_bytes=2000)
            self.assertEqual(result.stdout, expected)

    def test_cli_uses_payload_continuation_pointer(self):
        payload = sample(kind="revised")
        payload["changed_files"] = [f"src/mod{i:03d}.py" for i in range(300)]
        payload["continuation"] = "task-runs/issue-1/handoff.json"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.run_cli(str(path), "--budget", "2000")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("task-runs/issue-1/handoff.json", result.stdout)
            self.assertLessEqual(len(result.stdout.encode("utf-8")), 2000)

    def test_cli_falls_back_to_absolute_input_path(self):
        # A 3000-char filename forces truncation; with no pointer field
        # and no --continuation flag, the CLI falls back to the absolute
        # input path instead of inventing a placeholder.
        payload = sample()
        payload["changed_files"] = ["x" * 3000 + ".md"]
        self.assertNotIn("continuation", payload)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.run_cli(str(path), "--budget", "2000")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(path.resolve()), result.stdout)
            self.assertIn("truncated: omitted", result.stdout)
            self.assertLessEqual(len(result.stdout.encode("utf-8")), 2000)

    def test_cli_payload_continuation_beats_flag(self):
        payload = sample(kind="revised")
        payload["changed_files"] = [f"src/mod{i:03d}.py" for i in range(300)]
        payload["continuation"] = "task-runs/issue-1/handoff.json"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.run_cli(str(path), "--budget", "2000",
                                  "--continuation", "flag/fallback.json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("task-runs/issue-1/handoff.json", result.stdout)
            self.assertNotIn("flag/fallback.json", result.stdout)

    def test_cli_rejects_missing_and_invalid_input(self):
        result = self.run_cli("/nonexistent/handoff.json")
        self.assertEqual(result.returncode, 2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{not json", encoding="utf-8")
            self.assertEqual(self.run_cli(str(path)).returncode, 2)
            path.write_text(json.dumps({"kind": "initial"}), encoding="utf-8")
            self.assertEqual(self.run_cli(str(path)).returncode, 2)


if __name__ == "__main__":
    unittest.main()
