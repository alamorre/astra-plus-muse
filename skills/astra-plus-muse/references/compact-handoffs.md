# Compact handoffs and staged retrieval

Use this reference whenever a worker finishes, a poll fires, or a planner
claims a gap. Full transcripts, PR bodies, and verbose logs stay in local
files; the coordinator normally sees only the compact handoff below.

## Handoff contract

Default budget: **2000 bytes** for the coordinator-visible handoff. Render
with `scripts/compact_handoff.py`, which validates required fields, bounds
output, and appends a visible truncation marker naming the omitted byte count
and the local continuation path. Required fields: `kind` (one of `initial`,
`unchanged`, `revised`, `stopped-without-pr`), `task_url`, `target`,
`base_sha`, `head_sha`, `state`, `next_action`. Optional: `pr_url`,
`changed_files`, `checks` (each with explicit `name` and `returncode` plus a
log path), `findings`, `continuation`. A missing check renders as `not-run`;
only a `not-run` check may omit its return code. A skipped check keeps its
actual return code — including `rc=0` when the command exited zero while
skipping its tests — plus the word `skipped`. Neither is a pass.

## Staged retrieval

1. **Handoff only.** Start from the compact record; do not preload PR
   bodies, issue histories, transcripts, or full logs.
2. **Changed code, bounded.** Fetch the final diff and only the executable
   context a review question needs, in bounded chunks (one file or hunk
   range at a time). Unfetched remainder is unreviewed, never assumed good.
3. **Failure excerpts on demand.** Read the cited log range for a concrete
   failure or review question, not whole logs to monitor.
4. **History on demand.** Retrieve historical bodies or older revisions only
   to answer a specific review question.

Milestone-driven progress: report state changes (completed, revised,
blocked) with the next action. Where the host permits, skip repetitive
"still waiting" updates; record the next check time in the local ledger
instead. New commits invalidate prior sign-off until the new head is
personally reviewed.

## Planner evidence rule

A claimed gap must cite the exact executable locations inspected (file
paths, symbols, tests) and the existing PR/test evidence checked. A text
search miss is not proof of absence: confirm with the owning module, its
tests, and open/merged PRs before proposing. When the behavior already
exists, return `already implemented` with citations instead of a duplicate
proposal.

Historical example (another repository, already-implemented rejection): a
planner proposed keep-playable timing/restart persistence. Evidence
inspection found `WorkbenchStore.public` and `WorkbenchStore.record_kept_playable`
in `website/backend/workbench.py` with `test_reopen_preserves_sources_selection_candidates_audio_feedback_and_delivery`
and `test_first_kept_playable_requires_both_an_actual_keep_and_successful_delivery`
in `tests/test_workbench.py`, already merged via `alamorre/synth-parrot` PR #154,
which Astra confirmed immediately. The correct planner output was
`already implemented` with those citations, not a new issue. An unsupported
"no existing coverage" assertion without such citations is rejected.

## End-to-end examples

Each example below fits the 2000-byte budget and carries no transcript.

Initial handoff (worker published PR):

```text
kind: initial
task: https://github.com/OWNER/REPO/issues/42
pr: https://github.com/OWNER/REPO/pull/43
target: main
base: <40-hex> head: <40-hex>
state: ready
files: skills/area/SKILL.md, tests/test_area.py
checks:
- unittest: rc=0 @task-runs/42/unittest.log
findings: none
next: astra review head <sha>, verify, then merge if authorized
```

Unchanged poll (nothing new; no PR body re-fetched):

```text
kind: unchanged
task: https://github.com/OWNER/REPO/issues/42
pr: https://github.com/OWNER/REPO/pull/43
target: main
base: <40-hex> head: <same-40-hex-as-before>
state: waiting-ci
files: none new
checks:
- not-run (no checks executed; not a pass)
findings: none
next: recheck at <time>; no action until CI state changes
continued-at: task-runs/42/handoff.json
```

Revised PR (new head after review findings):

```text
kind: revised
task: https://github.com/OWNER/REPO/issues/42
pr: https://github.com/OWNER/REPO/pull/43
target: main
base: <40-hex> head: <new-40-hex>
state: ready-after-fixes
files: src/area.py, tests/test_area.py
checks:
- unittest: rc=0 @task-runs/42/unittest-r2.log
findings: prior findings resolved at new head; see diff
next: astra re-review new head only, verify, then merge if authorized
```

Stopped without PR (partial work preserved locally):

```text
kind: stopped-without-pr
task: https://github.com/OWNER/REPO/issues/42
pr: none
target: main
base: <40-hex> head: <worktree-sha-or-none>
state: stopped-blocked
files: src/area.py (uncommitted)
checks:
- unittest: rc=1 @task-runs/42/unittest.log
findings: <concrete blocker and evidence>
next: <one bounded continuation or escalate to astra>
continued-at: task-runs/42/handoff.json
```

## Rendering command

Render a handoff JSON file from the repository root with its prescribed
interpreter (`<PYTHON>` below); the payload's `continuation` field supplies
the pointer when present:

```sh
<PYTHON> skills/astra-plus-muse/scripts/compact_handoff.py task-runs/issue-1/handoff.json --budget 2000
```

Import recipe for staged tooling (no third-party dependencies):

```python
import sys
sys.path.insert(0, "skills/astra-plus-muse/scripts")
from compact_handoff import render  # or render_text, enforce_budget, measure_bytes
bounded, truncated, omitted = render(payload, budget_bytes=2000)
```

## Reproducible payload measurement

Run from the repository root with its prescribed interpreter:

```sh
<PYTHON> -m unittest discover -s tests -v  # includes compact-handoff fixtures
```

The shaped fixture is built in exactly one place,
`compact_handoff.measurement_fixture()`: the fixed `initial` record versus
the same record plus 400 PR-body lines and 400 transcript lines. It measured
**395 bytes** for the compact handoff, **37195 bytes** for the verbose
variant, and **2000 bytes** for the budgeted truncation with **35373 bytes**
omitted behind a complete marker naming `task-runs/issue-1/handoff.json`.
Re-run the fixture to reproduce these byte counts; they describe this
example only — no tokenizer, dollar, or savings inference is derived from
them. All four handoff kinds (`initial`, `unchanged`, `revised`,
`stopped-without-pr`) render within the default budget untruncated.

Existing guarantees are unchanged: explicit worker model and limits, no
worker merges or self-approval, no bypassed checks, Astra's personal
final-head diff/context review with independent verification, and
head-guarded authorized merge — see SKILL.md and references/handoffs.md.
