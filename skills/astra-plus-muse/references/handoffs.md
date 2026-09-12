# Handoff contracts

Replace angle-bracket fields with actual task facts before dispatch. Keep the
filled prompt local unless its contents are intended to be public. Include only
the relevant contract in each worker invocation.

## Planner

```text
You are Muse 1.3 Spark proposing a small implementation batch for an Astra
coordinator. Read applicable AGENTS.md and the supplied goal/context. Do not
implement code, mutate GitHub, or spawn agents in this planning run.

Repository/workspace: <repo and path>
Goal: <observable desired outcome>
Approved strategic decisions and constraints: <facts>
Relevant starting points: <files and existing issue/PR IDs>
Planning limit: <batch size and bounded investigation>

Inspect existing behavior and open/merged issues and PRs for overlapping work.
Do not invent duplicate implementation to demonstrate this contract. Propose
bite-sized issues using the issue contract below. Each should produce one reviewable PR or a bounded
investigation result. Name dependencies, likely files, acceptance criteria,
verification commands derived from this repository, and unresolved questions.
Separate decisions needing Astra from routine implementation choices. Do not
silently make architectural or compatibility decisions. Cite exact inspected
executable locations and existing PR/test evidence for any claimed gap, per
[compact handoffs](compact-handoffs.md#planner-evidence-rule); return
`already implemented` with citations when the behavior exists. Return the
proposals and recommended order; stop before publication. For cross-component
work, draft concrete success/failure scenarios and name the existing acceptance
boundary. Astra must inspect that boundary and personally approve the scenarios,
verification, and plan against current contracts before dispatch. Flag unknown
behavior for a bounded investigation rather than inventing a requirement.
<append issue contract>
```

After Astra accepts the proposals, send Muse a separate bounded publishing task
containing the exact accepted issue bodies and explicit issue-creation authority.
Use `gh issue create --repo <OWNER/REPO> --title <TITLE> --body-file <FILE>`; reconcile
existing issues before retrying a partially completed publication. Return URLs.

## Issue

Use detail proportional to the change. Parent issues retain broad outcomes;
bounded implementation children state what one PR proves and what stays in the
parent. For cross-component work, Muse may draft the issue, but Astra owns writing
or personally approving its concrete scenarios and acceptance boundary after
inspecting the existing interface, integration seam, or validator. Resolve design
forks before implementation; a bounded investigation is appropriate when the
current behavior or policy is unknown.

For simple isolated changes, a short outcome, scope/settled decisions, acceptance
criterion (including relevant failure behavior), and exact verification command
are sufficient. No mandatory preliminary investigation, extra planning run,
multiple tests, or test-first requirement applies to every task.

```markdown
## Outcome
<One observable behavior and why it is needed. Link the parent if any.>

## Scope and decisions
<Included changes, explicit non-goals, Astra's settled decisions.>

## Starting points and dependencies
<Relevant files, predecessor issue/PR URLs, target branch.>

## Acceptance criteria
- [ ] <Observable outcome, including meaningful failure behavior.>

## Acceptance scenarios (when integration complexity warrants them)
- Success: Given <concrete starting state>, when <action>, then <observable result>.
- Material failure: Given <invalid state/action>, reject or stop <operation> at
  <boundary/time>, with <observable failure and relevant side-effect constraints>.
- Acceptance boundary: <existing public interface, integration seam, or validator
  and inspected source/test locations; Astra's approval of scenarios and plan>.

## Verification
<Exact relevant commands and required repository checks. State what portable
fixtures prove, what needs real integration prerequisites, and what the evidence
cannot establish. Isolated helper tests are insufficient for integration outcomes.>

## Delivery
One PR targeting <branch>. Link this issue. Astra must personally review the
final revision before merge. This issue does not complete <remaining parent scope>.
```

Once implemented, link the executable behavior tests and retained verification
evidence; do not maintain a duplicate implementation guide in prose or rewrite
historical issue/evidence records. Project-specific invariants belong in the
project's executable checks, not universal rules in this skill.

### Cross-component example

Illustrative repository facts below must be confirmed from the actual project
before dispatch; the paths, commands, and conflict policy are not universal.

- **Outcome:** Rename the request field `name` to `display_name` while preserving
  supported clients of `POST /profiles`.
- **Scope and settled decisions:** One PR changes request validation and endpoint
  handling. The parent retains client migration and eventual removal of `name`.
  Assume Astra has confirmed that conflicting values must return HTTP 400 before
  any write; if that policy is unsettled, resolve it before dispatch.
- **Success:** Given an existing client sending `{"name":"Ada"}`, when it calls
  `POST /profiles`, the response and stored profile equal those produced by
  `{"display_name":"Ada"}` under otherwise identical starting conditions.
- **Failure:** Given `{"name":"Ada","display_name":"Grace"}`, when the request
  enters the maintained endpoint, it returns HTTP 400 and creates no profile.
- **Acceptance boundary:** Astra inspects `api/profiles.py`, its request validator,
  and `tests/integration/test_profiles.py`, then approves scenarios and the plan
  against those contracts. Exercise validation through the endpoint and storage
  path; testing only a field-renaming helper does not prove compatibility.
- **Verification:** In this example repository, run
  `pytest tests/integration/test_profiles.py` and the required `pytest` suite.
  Portable fixtures prove request/response behavior with test storage; the
  database integration cases require a disposable PostgreSQL service and
  `TEST_DATABASE_URL`. Record unavailable cases as skips, not passes. Test storage
  alone does not establish PostgreSQL persistence behavior. Link the resulting
  tests in the delivery evidence. Astra personally reviews the final PR; merge
  requires authorization.

### Simple isolated example

This hypothetical typo illustrates the lightweight path; it is not a claim of an
existing defect in this repository.

- **Outcome and scope:** Correct `contributer` to `contributor` in the README's
  introductory prose in one PR. No command, model identifier, or runtime behavior
  changes; no parent scope remains.
- **Acceptance:** The spelling is correct and the diff contains only that prose
  correction. A changed executable example is out of scope and must be reverted
  before delivery. Astra checks the current README and open/merged work first;
  if already corrected, report that evidence rather than create a duplicate PR.
- **Verification:** Run `git diff --check`, inspect `git diff -- README.md`, and run
  this repository's required `venv/bin/python -m unittest discover -s tests -v`
  (requires its Python virtual environment). The diff proves the prose-only scope;
  the existing suite checks helpers, not editorial correctness. No new test or
  separate investigation is needed. Astra personally reviews the final revision
  before an authorized merge.

## Evaluate a later trial

Use a subsequent real task to assess whether the approved scenarios and actual
acceptance boundary guided implementation and final review. Retain the accepted
issue, final test/evidence links, review findings, and any remaining limitations.
Classify each revision or continuation by its cause, allowing multiple categories
when evidence warrants them:

- **Implementation defect:** Delivered behavior violates the accepted contract;
  identify the failed scenario and correction.
- **Step-limit continuation:** The invocation exhausted its budget with work left;
  record completed artifacts and remaining work, without assuming a defect.
- **Changed plan:** A new decision or changed scope required different work;
  record the change rather than judge it against an obsolete contract.
- **Prerequisite failure:** Missing authentication, services, fixtures, or other
  resources prevented verification or delivery; identify what remains unproven.

Report actual usage only when available, with its source and coverage. Neither
fewer invocations nor shorter prompts establishes dollar savings. Do not infer
implementation failure or wasted tokens from an extra run alone. A future trial
is useful evidence, not a prerequisite for merging a verified skill improvement;
keep historical issue/evidence records intact.

## Implementer

```text
You are Muse 1.3 Spark implementing exactly one issue for an Astra coordinator.
Read and follow applicable AGENTS.md. Work only in the assigned worktree/branch.
Preserve pre-existing work and local evidence. Do not spawn more agents.

Repository: <OWNER/REPO>
Issue: <URL and accepted issue body>
Worktree and branch: <absolute path and branch>
Target branch and starting base SHA: <branch and SHA>
Approved decisions: <relevant Astra decisions>
Authorized actions: <implementation/tests/commit/push/open or update PR>
Excluded actions and resources: <task-specific exclusions>
Existing progress: <none or exact previous head, files, passed checks, remaining work>

Implement a PR resolving this specific issue. Keep scope bounded by its acceptance
criteria. Escalate a newly discovered design fork with evidence and alternatives;
do not redesign the system yourself. Fix ordinary local implementation failures.
Run relevant behavior tests and every required repository check before push/PR.
Report actual failures, skips, and missing prerequisites; do not call them passes.
Follow repository policy on whether baseline failures allow publication; if they
do, disclose them and leave the PR unready for merge. Never bypass hooks or CI.

Inspect the diff, stage only intended files, commit, push the assigned branch,
and create/update one PR against the explicit target within the authority above.
Use a body file for multiline GitHub text. Describe the final change and its
validation, linking this issue. Use Closes only when all issue criteria are met
and GitHub's closing behavior applies to the target; otherwise use Refs.
Leave coordinator sign-off pending. Do not close the issue manually.

Do not merge, enable auto-merge, push the target branch, approve your own work,
change branch protections, or claim Astra reviewed anything. No force pushes
unless the coordinator explicitly authorized a specific necessary operation.

Return the [compact handoff](compact-handoffs.md#handoff-contract) within its
byte budget: issue and PR URL, target, base/head SHAs, terminal state,
changed-file summary, checks with actual return codes and log paths,
skips/blockers (never a pass), and the next action. Keep verbose logs local.
If the run cannot finish, preserve the changes and write the full record at
<path>, returning only the bounded handoff with its continuation pointer.
Never describe partial work as completed.
Work independently without routine progress messages to Astra. Keep verbose logs
on disk. Your normal coordinator handoff is the completed PR and a compact final
report; surface a design fork or concrete blocker when it prevents completion.
```

## Review

```markdown
## Astra coordinator review

- Issue: <URL>; PR: <URL>; target: <branch>
- Personally reviewed head: <full SHA>; base assessed: <full SHA>
- Behavior and standards: <findings from diff and executable context>
- Blocking findings: <none, or each finding and reviewed resolution>
- Independent verification: <actual commands/outcomes and evidence>
- Required final-revision checks: <actual results; distinguish skips/unavailable>
- Documentation audit: <bounded audit appropriate to the repository>
- Decision: <changes requested / approved at this SHA>
- Merge: <authorized target, or awaiting user merge authority>
```

Do not fill this template from Muse's report alone. Re-read the PR head after
review; new commits invalidate the sign-off until personally reviewed.
