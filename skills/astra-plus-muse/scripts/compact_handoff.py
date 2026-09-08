#!/usr/bin/env python3
"""Render and measure compact coordinator handoffs with an explicit byte budget.

Deterministic stdlib-only helper. It bounds visible coordinator output and makes
truncation explicit; full evidence stays in local files for staged retrieval.
It never treats missing or skipped checks as passes.
"""

DEFAULT_BUDGET_BYTES = 2000

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
            if not check.get("name"):
                errors.append("each check needs a name")
            if check.get("returncode") is None:
                errors.append(f"check {check.get('name', '?')!r} needs an explicit returncode")
            # A skip is never a pass: it must say so explicitly.
            status = str(check.get("status", "")).lower()
            if status == "skipped" and str(check.get("returncode")) == "0":
                errors.append(
                    f"check {check.get('name', '?')!r}: skipped must not use returncode 0")
    return errors


def _check_line(check):
    status = check.get("status", "")
    line = f"- {check.get('name')}: rc={check.get('returncode')}"
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


def enforce_budget(text, budget_bytes=DEFAULT_BUDGET_BYTES, continuation="local file"):
    """Bound text to budget_bytes with a visible truncation marker.

    Returns (bounded_text, truncated, omitted_bytes). Untruncated text is
    returned unchanged; truncated text ends with a marker naming the omitted
    byte count and where the full record lives. Never returns oversized text.
    """
    if budget_bytes <= 0:
        raise ValueError("budget_bytes must be positive")
    raw = text.encode("utf-8")
    if len(raw) <= budget_bytes:
        return text, False, 0
    # Reserve room for the omitted-count segment; fit the head exactly.
    omitted = len(raw)  # upper bound; refined below
    marker = f"\n[truncated: omitted {omitted} bytes; see {continuation}]\n"
    budget = budget_bytes
    head = raw[:max(0, budget - len(marker.encode("utf-8")))]
    # Avoid splitting a UTF-8 sequence.
    while head and (budget - len(head) < len(marker.encode("utf-8"))):
        head = head[:-1]
    try:
        head_text = head.decode("utf-8")
    except UnicodeDecodeError:
        head_text = head.decode("utf-8", errors="ignore")
    omitted = len(raw) - len(head)
    marker = (f"\n[truncated: omitted {omitted} bytes; full record at {continuation}; "
              "retrieve staged chunks per references/compact-handoffs.md; "
              "unreviewed remainder is not reviewed]\n")
    marker_bytes = marker.encode("utf-8")
    if len(marker_bytes) >= budget:
        marker = marker[:budget]
        return marker, True, len(raw)
    head = raw[:budget - len(marker_bytes)]
    head_text = head.decode("utf-8", errors="ignore")
    return head_text + marker, True, len(raw) - len(head)


def render(payload, budget_bytes=DEFAULT_BUDGET_BYTES, continuation="local file"):
    """Validate, render, and bound a handoff payload in one step."""
    cont = payload.get("continuation") or continuation
    text = render_text(payload)
    bounded, truncated, omitted = enforce_budget(
        text, budget_bytes=budget_bytes, continuation=cont)
    return bounded, truncated, omitted
