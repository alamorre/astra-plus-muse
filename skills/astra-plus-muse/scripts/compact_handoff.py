#!/usr/bin/env python3
"""Render and measure compact coordinator handoffs with an explicit byte budget.

Deterministic stdlib-only helper. It bounds visible coordinator output and makes
truncation explicit; full evidence stays in local files for staged retrieval.
It never treats missing or skipped checks as passes.
"""

import argparse
import json
import sys
from pathlib import Path


DEFAULT_BUDGET_BYTES = 2000

MEASUREMENT_PR_BODY_LINES = 400
MEASUREMENT_TRANSCRIPT_LINES = 400
MEASUREMENT_CONTINUATION = "task-runs/issue-1/handoff.json"

REQUIRED_FIELDS = ("kind", "task_url", "target", "base_sha", "head_sha",
                   "state", "next_action")
OPTIONAL_FIELDS = ("pr_url", "changed_files", "checks", "findings",
                   "continuation")
KINDS = ("initial", "unchanged", "revised", "stopped-without-pr")


def measure_bytes(text):
    """Return the UTF-8 byte length of text (reproducible payload size)."""
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    return len(text.encode("utf-8"))


def validate(payload):
    """Return a list of error strings; empty means the payload is well-formed."""
    errors = []
    if not isinstance(payload, dict):
        return ["payload must be an object"]
    for field in REQUIRED_FIELDS:
        value = payload.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"missing required field: {field}")
    if payload.get("kind") not in KINDS:
        errors.append(f"kind must be one of {', '.join(KINDS)}")
    for key in payload:
        if key not in REQUIRED_FIELDS + OPTIONAL_FIELDS:
            errors.append(f"unknown field: {key}")
    checks = payload.get("checks", [])
    if checks is not None and not isinstance(checks, list):
        errors.append("checks must be a list")
    else:
        for check in checks or []:
            if not isinstance(check, dict):
                errors.append("each check must be an object")
                continue
            if not isinstance(check.get("name"), str) or not check["name"].strip():
                errors.append("each check needs a name")
            status = check.get("status", "")
            if status is not None and not isinstance(status, str):
                errors.append(
                    f"check {check.get('name', '?')!r}: status must be a string")
            log = check.get("log")
            if log is not None and not isinstance(log, str):
                errors.append(
                    f"check {check.get('name', '?')!r}: log must be a path string")
            # A skip is never a pass, but the actual return code is
            # preserved: a command can exit 0 while skipping its tests,
            # so rc=0 with an explicit skipped status is rendered as
            # skipped, never rewritten. Only a not-run check may omit
            # its return code, and it never renders as a pass either.
            if check.get("returncode") is None and \
                    str(status or "").lower() != "not-run":
                errors.append(
                    f"check {check.get('name', '?')!r} needs an explicit returncode")
    return errors


def _check_line(check):
    status = check.get("status") or ""
    line = f"- {check.get('name')}"
    if check.get("returncode") is not None:
        line += f": rc={check.get('returncode')}"
    if status:
        line += f" ({status})"
    if check.get("log"):
        line += f" @{check.get('log')}"
    return line


def render_text(payload):
    """Render the payload deterministically (fixed field order, sorted lists)."""
    errors = validate(payload)
    if errors:
        raise ValueError("; ".join(errors))
    lines = [
        f"kind: {payload['kind']}",
        f"task: {payload['task_url']}",
        f"pr: {payload.get('pr_url', 'none')}",
        f"target: {payload['target']}",
        f"base: {payload['base_sha']} head: {payload['head_sha']}",
        f"state: {payload['state']}",
    ]
    files = sorted(payload.get("changed_files") or [])
    lines.append("files: " + (", ".join(files) if files else "none"))
    lines.append("checks:")
    checks = payload.get("checks") or []
    if not checks:
        lines.append("- not-run (no checks executed; not a pass)")
    else:
        for check in sorted(checks, key=lambda c: str(c.get("name"))):
            lines.append(_check_line(check))
    lines.append(f"findings: {payload.get('findings') or 'none'}")
    lines.append(f"next: {payload['next_action']}")
    if payload.get("continuation"):
        lines.append(f"continued-at: {payload['continuation']}")
    return "\n".join(lines) + "\n"


def _truncation_marker(omitted_bytes, continuation):
    """Build the complete truncation marker; it is never sliced."""
    return (f"\n[truncated: omitted {omitted_bytes} bytes; "
            f"full record at {continuation}; "
            "retrieve staged chunks per references/compact-handoffs.md; "
            "unreviewed remainder is not reviewed]\n")


def enforce_budget(text, budget_bytes=DEFAULT_BUDGET_BYTES, continuation="local file"):
    """Bound text to budget_bytes with a visible truncation marker.

    Returns (bounded_text, truncated, omitted_bytes). Untruncated text is
    returned unchanged; truncated text is a UTF-8 character-boundary head
    plus one complete marker naming the omitted byte count and the local
    continuation path. The displayed count, the returned count, and the
    actual lost bytes are all equal: len(text.encode) minus the byte
    length of the decoded head. The marker is never sliced: when even the
    marker plus one head byte cannot fit, this raises ValueError instead
    of emitting a misleading partial marker.
    """
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if not isinstance(budget_bytes, int) or isinstance(budget_bytes, bool) \
            or budget_bytes <= 0:
        raise ValueError("budget_bytes must be a positive integer")
    if not isinstance(continuation, str) or not continuation:
        raise ValueError("continuation must be a nonempty path string")
    raw = text.encode("utf-8")
    total = len(raw)
    if total <= budget_bytes:
        return text, False, 0
    # The marker names the omitted count, so reserve room for the widest
    # possible count: omitted can never exceed total, hence never needs
    # more digits than total. One cut, no iteration, no oscillation.
    digits_total = len(str(total))
    max_marker = len(_truncation_marker(total, continuation).encode("utf-8"))
    if max_marker >= budget_bytes:
        raise ValueError(
            f"budget {budget_bytes} bytes cannot fit the "
            f"{max_marker}-byte truncation marker; "
            "raise the budget or shorten the continuation path")
    allowance = budget_bytes - (max_marker - digits_total) - digits_total
    # raw is valid UTF-8, so a prefix cut can only strand a trailing
    # partial sequence; ignoring it drops exactly those bytes, and the
    # head stays on a character boundary within the byte budget even
    # when the continuation pointer itself is multibyte.
    head_text = raw[:allowance].decode("utf-8", errors="ignore")
    head_bytes = len(head_text.encode("utf-8"))
    omitted = total - head_bytes
    marker = _truncation_marker(omitted, continuation)
    return head_text + marker, True, omitted


def render(payload, budget_bytes=DEFAULT_BUDGET_BYTES, continuation="local file"):
    """Validate, render, and bound a handoff payload in one step."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    cont = payload.get("continuation") or continuation
    text = render_text(payload)
    bounded, truncated, omitted = enforce_budget(
        text, budget_bytes=budget_bytes, continuation=cont)
    return bounded, truncated, omitted


def example_payload(kind="initial"):
    """Return a small fixed handoff payload of the given kind.

    Single construction site for the examples quoted in
    references/compact-handoffs.md and the tests below; every kind
    renders within the default budget without truncation.
    """
    payload = {
        "kind": kind,
        "task_url": "https://github.com/OWNER/REPO/issues/42",
        "target": "main",
        "base_sha": "0" * 40,
        "head_sha": "9" * 40,
        "state": "ready",
        "pr_url": "https://github.com/OWNER/REPO/pull/43",
        "changed_files": ["skills/area/SKILL.md", "tests/test_area.py"],
        "checks": [
            {"name": "unittest", "returncode": 0,
             "log": "task-runs/42/unittest.log"},
        ],
        "findings": "none",
        "next_action": "astra review head, verify, then merge if authorized",
    }
    if kind == "unchanged":
        payload["state"] = "waiting-ci"
        payload["checks"] = []
        payload["next_action"] = "recheck at <time>; no action until CI changes"
        payload["continuation"] = "task-runs/42/handoff.json"
    elif kind == "revised":
        payload["state"] = "ready-after-fixes"
        payload["checks"] = [
            {"name": "unittest", "returncode": 0,
             "log": "task-runs/42/unittest-r2.log"},
        ]
        payload["findings"] = "prior findings resolved at new head; see diff"
        payload["next_action"] = \
            "astra re-review new head only, verify, then merge if authorized"
    elif kind == "stopped-without-pr":
        del payload["pr_url"]
        payload["state"] = "stopped-blocked"
        payload["changed_files"] = ["src/area.py (uncommitted)"]
        payload["checks"] = [
            {"name": "unittest", "returncode": 1,
             "log": "task-runs/42/unittest.log"},
        ]
        payload["findings"] = "<concrete blocker and evidence>"
        payload["next_action"] = "<one bounded continuation or escalate>"
        payload["continuation"] = "task-runs/42/handoff.json"
    return payload


def measurement_fixture():
    """Build the shaped compact-vs-verbose measurement fixture.

    Returns a dict with the compact handoff text, the verbose variant
    (the same record plus MEASUREMENT_PR_BODY_LINES PR-body lines and
    MEASUREMENT_TRANSCRIPT_LINES transcript lines), and the budgeted
    truncation of that verbose text with its byte sizes. This is the
    one authoritative construction site: tests and documentation
    derive their numbers from here instead of hardcoding them.
    """
    compact_text = render_text(example_payload("initial"))
    verbose_text = compact_text + "".join(
        f"pr-body line {i:04d}: <review discussion excerpt>\n"
        for i in range(MEASUREMENT_PR_BODY_LINES))
    verbose_text += "".join(
        f"transcript line {i:04d}: <worker event excerpt>\n"
        for i in range(MEASUREMENT_TRANSCRIPT_LINES))
    bounded_text, truncated, omitted = enforce_budget(
        verbose_text, budget_bytes=DEFAULT_BUDGET_BYTES,
        continuation=MEASUREMENT_CONTINUATION)
    return {
        "compact_text": compact_text,
        "verbose_text": verbose_text,
        "bounded_text": bounded_text,
        "truncated": truncated,
        "omitted": omitted,
        "compact_bytes": measure_bytes(compact_text),
        "verbose_bytes": measure_bytes(verbose_text),
        "bounded_bytes": measure_bytes(bounded_text),
        "continuation": MEASUREMENT_CONTINUATION,
    }


def build_parser():
    """Return the CLI parser for the helper."""
    result = argparse.ArgumentParser(
        description="Validate, render, and byte-bound a compact "
                    "coordinator handoff from a JSON payload file.")
    result.add_argument("handoff", type=Path,
                        help="path to a handoff JSON payload; its "
                             "continuation field supplies the pointer "
                             "when present")
    result.add_argument("--budget", type=int, default=DEFAULT_BUDGET_BYTES,
                        help="coordinator-visible byte budget")
    result.add_argument("--continuation", default="local file",
                        help="fallback continuation pointer when the "
                             "payload has none")
    return result


def main(argv=None):
    """Render the handoff JSON file to stdout within the byte budget."""
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.handoff.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"compact_handoff: cannot read {args.handoff}: {error}",
              file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"compact_handoff: invalid JSON in {args.handoff}: {error}",
              file=sys.stderr)
        return 2
    try:
        bounded, _, _ = render(payload, budget_bytes=args.budget,
                               continuation=args.continuation)
    except ValueError as error:
        print(f"compact_handoff: {error}", file=sys.stderr)
        return 2
    sys.stdout.write(bounded)
    return 0


if __name__ == "__main__":
    sys.exit(main())
