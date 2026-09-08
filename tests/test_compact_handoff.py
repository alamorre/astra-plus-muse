"""Exercise compact-handoff rendering, budget, and measurement behavior."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "skills/astra-plus-muse/scripts"))
import compact_handoff as ch


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

    def test_skipped_check_must_not_use_rc_zero(self):
        payload = sample()
        payload["checks"] = [{"name": "e2e", "returncode": 0, "status": "skipped"}]
        with self.assertRaises(ValueError):
            ch.render_text(payload)
        payload["checks"] = [{"name": "e2e", "returncode": 2, "status": "skipped",
                              "log": "runs/e2e.log"}]
        text = ch.render_text(payload)
        self.assertIn("skipped", text)

    def test_measurement_is_reproducible(self):
        first = ch.measure_bytes(ch.render_text(sample(kind="unchanged")))
        second = ch.measure_bytes(ch.render_text(sample(kind="unchanged")))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
