---
name: astra-plus-muse
description: Orchestrate Muse 1.3 Spark through its CLI in YOLO mode for GitHub issue planning and implementation, with Astra owning strategic decisions, escalations, personal PR review, and authorized merges. Use for cost-conscious delegation of a development backlog or feature into small PRs.
---

# Astra plus Muse

Keep Astra's attention on decisions and review. Use Muse for repository inspection,
proposed task batches, bite-sized issues, implementation, tests, and PR revisions.
The user's instructions take precedence over this skill's guidance.

## Establish the working contract

1. Identify the repository, goal, authorized target branch, applicable `AGENTS.md`,
   acceptance criteria, required checks, and existing work. Preserve uncommitted
   work and active agents. Reuse authorization already given; ask only for a
   missing decision that prevents concrete progress.
2. Establish whether GitHub issue/PR creation, branch pushes, and eventual merges
   are authorized by the task. Installation or automatic selection of this skill
   alone grants none of these permissions. Carry the established permissions into
   each handoff. Explicitly requested YOLO delegation does not need reconfirmation.
3. Check `muse --version`, `muse exec --help`, Git, and authenticated GitHub access.
   The worker model is **`muse-spark-1.3-contributor`**, observed with Muse Code
   1.0.3. Keep it explicit; never silently substitute a Codex model or another Muse
   tier. If unavailable, report that specific prerequisite and continue independent
   planning/review that remains possible.
4. Use the Muse CLI from Codex's shell tools. Native Codex subagents are not a
   substitute for Muse: their model list may not include it. Keep the coordinating
   Codex session on Astra; a skill cannot switch the parent model. If it is running
   another model, disclose that and have the user select Astra for the intended
   review role instead of claiming an Astra review occurred.

`--yolo` disables Muse's approval and OS sandbox controls and trusts the workspace
for that run. Use it when authorized and permitted by the host environment; never
route around a host restriction. Worktrees separate Git changes, not credentials
or filesystem access. The no-merge rule below is a worker instruction, not a
technical access boundary. Users needing enforcement must give workers restricted
credentials or separate execution environments.

## Muse proposes; Astra decides

Give a planning Muse run the goal, approved constraints, a bounded relevant source
set, and [the planner contract](references/handoffs.md#planner). Request a small
batch of independently verifiable issues and dependency order. Start with roughly
three to five proposals, adapting to the work. The planner proposes before
publishing, so design assumptions and duplicates can be resolved cheaply.

Astra reviews the proposal for architecture, domain meaning, compatibility,
high-impact risks, and sequencing. Resolve strategic questions before assigning
implementation. A task is ready for Muse when it has one observable outcome,
explicit non-goals, acceptance criteria, concrete verification commands, and no
unresolved design fork. Split cross-cutting changes along a testable seam; a small
line count alone does not make a task simple. A difficult investigation can be a
bounded evidence-gathering issue whose conclusions return to Astra.

After Astra accepts the batch, have Muse create the approved GitHub issues using
[the issue contract](references/handoffs.md#issue). Search open issues/PRs first;
update or reference existing work rather than duplicating it. Explicitly supply
the repository to GitHub commands. Keep parent issues open until their full
acceptance criteria are satisfied.

## Dispatch one issue per worker

Create a dedicated branch and worktree from the agreed target revision for each
ready issue. Record the issue, base branch/SHA, branch, worktree, worker run, and PR
in a small local ledger outside tracked source. Assign one writer to each branch.
Parallelize independent issues only; serialize overlapping changes and tasks with
unmerged dependencies. Start with two workers unless the user's limits or task
shape suggest otherwise. Do not create an unbounded worker tree.

Read [the implementer contract](references/handoffs.md#implementer) and assemble a
fresh prompt containing the accepted issue and relevant decisions. Do not send
the entire coordinator conversation. Put the role contract in the worker's system
instructions when the installed integration supports that; the verified CLI uses
`--prompt-file` and exposes no dedicated system-prompt flag. With that CLI, prepend
the contract to the task prompt and do not claim system-level enforcement.

Use [the CLI reference](references/cli.md) to run the bundled launcher or invoke
Muse directly. Set the model and run limits explicitly. Start with medium reasoning
for routine work; raise it only for a justified bounded attempt. Keep full logs
local and return concise evidence. Model-step limits control a single invocation,
not dollars, wall time, subprocess duration, or a whole multi-run task.

The implementer must finish the issue, run relevant tests and repository-required
pre-push checks, commit only intended files, push its branch, and open/update a PR
against the explicit target when those actions are authorized. Its prompt must
say **do not merge, enable auto-merge, push the target branch, or approve your own
work**. It must report incomplete work and real failures rather than equating a
zero CLI exit code with a finished PR. Preserve useful partial work on interruption.

## Stay out of the worker's context loop

Treat the completed PR as Astra's normal implementation handoff. Let Muse finish
implementation, tests, and publication without progress interviews. Prefer a
background completion notification or a durable completion marker. Never stream
JSONL events, repeatedly tail logs, or load worker transcripts into Astra just to
watch. Do useful independent coordinator work or yield until a completion event.

When completion notifications are unavailable, check only a process status or
small completion marker at a sparse cadence: roughly every ten minutes by default,
longer for known long checks. Record the next check time in the local ledger and
do not busy-poll between checks. These are monitoring intervals, not blocking tool
waits; follow the host's wait limits. Adapt only for an explicit deadline, failure
signal, user request, or resource concern. An active worker alone needs no intervention.

On completion, read the compact handoff and PR diff. Keep coordinator-visible
handoffs within the budget and retrieve the rest in stages per
[compact handoffs](references/compact-handoffs.md); unfetched context is
unreviewed. Ask Muse for one concise blocker report if required, not a
narrated replay. Keep coordinator status updates brief and milestone-driven.
A retry or continuation still needs a bounded task, never a fresh copy of
the full history.

## Handle failures without spending in circles

Read the compact result, changed-file summary, and remaining work before restarting a worker.
For a concrete implementation defect, send one narrowly scoped correction to
Muse. After two unsuccessful implementation attempts on the same blocker, stop
repeating the prompt: Astra diagnoses the cause, resolves a design question,
splits the task, or takes over the hard portion. Auth, unavailable resources, and
host restrictions are prerequisites, not reasons for repeated model retries.

When a run simply reaches its limit, inspect its artifacts and supply a continuation
with the precise remaining work and a new explicit budget. Do not restart completed
research or repeat successful full checks unless changes invalidate them. No
automatic retry loop. Report actual usage when available; do not promise a savings
percentage or invent costs from step counts.

## Astra personally reviews and signs off

For each PR, Astra must read the final diff **and relevant executable context**,
compare behavior with the originating issue and repository standards, and
independently verify the affected behavior. Muse's summary, another reviewer, or
green CI is supporting evidence, not a replacement for Astra's review.

Send blocking findings with file/context, impact, and a concrete expected outcome
to Muse. Add regression coverage where warranted; review the fixes personally.
Record [review evidence](references/handoffs.md#review) on the PR or in the project's
retained review location, naming the reviewed head SHA, target, findings and their
resolution, independent checks, and any skips or unavailable prerequisites. If the
GitHub account also authored the PR, record an explicitly attributed Astra review
comment instead of pretending GitHub permits self-approval. Respect any required
independent human approval.

Before merging, confirm merge authorization, intended target, and unchanged head;
all required checks must pass for that final revision. A skipped/unavailable check
is not a pass. If the base changed, assess and verify integration before merging.
Use the repository's merge strategy and GitHub's head-match guard, for example
`gh pr merge <PR> --repo <OWNER/REPO> --squash --match-head-commit <REVIEWED_SHA>`.
Do not bypass protection with `--admin` or substitute future auto-merge for review.
If a merge queue is required, verify its result before claiming the PR merged.

Only Astra gives the final sign-off and performs the authorized merge. If merges
were not authorized, leave the reviewed PR ready and report its URL. After a
confirmed merge, update the ledger and issue status accurately, then select the
next ready work. Report remaining parent scope without claiming partial work
completes the entire goal.
