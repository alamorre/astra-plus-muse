# Muse execution

Verified against local `muse --help` and `muse exec --help` from Muse Code
1.1.1 (1.1.1-R2514.1), on 2026-09-12. The model ID below was also observed in active
worker invocations. Availability and pricing depend on the user's Muse account;
this package does not install Muse, supply credentials, or assert public access.

The CLI exposes `--prompt-file`, not a dedicated system-prompt flag. The handoff
is a role-and-task prompt. Do not invent `--system-prompt` or assume an unverified
agent-definition overlay changes the root system instructions.

## Launcher

Use Python 3.10+ from the target repository's prescribed environment. Here `<PYTHON>`
means that interpreter and `<SKILL_DIR>` is the installed skill's absolute path.
The launcher has no third-party dependencies.

```sh
<PYTHON> <SKILL_DIR>/scripts/run_muse.py \
  --workspace /absolute/path/to/issue-worktree \
  --prompt-file /absolute/path/to/filled-handoff.md \
  --output-dir /absolute/path/to/private-runs/issue-42-attempt-1
```

The output directory must not exist. Use a new directory for each attempt; keep
logs outside tracked source. The launcher checks CLI support, records the exact
arguments, streams stdout/stderr to disk, and records the process exit code and
elapsed time in `result.json`. Consult `--help` for defaults and overrides. It
does not create a worktree, assemble prompts, publish to GitHub, or merge anything.
Its default invocation uses YOLO as requested by this workflow; invoke it only
after the coordinator has established that authority.

Run the launcher in the host's managed background process facility when available;
retain its process/session ID and prefer completion notifications. If unavailable,
check only process status or `result.json` about every ten minutes; do not load
`events.jsonl` or repeatedly tail `stderr.log` while it works. The coordinator
normally sees the completed PR, not the ongoing transcript. Do not abandon an
active process or assume reaching a model-step limit ends
all shell children. If cancelled, reconcile the branch, PR, and still-running
processes before continuing. Do not start a second writer on the same worktree.

## Direct equivalent

```sh
muse exec --yolo --model muse-spark-1.3-contributor \
  --reasoning-effort xhigh --max-model-steps 40 \
  --max-tool-output-bytes 12000 \
  --workspace /absolute/path/to/issue-worktree \
  --prompt-file /absolute/path/to/filled-handoff.md --json
```

Capture stdout/stderr locally without putting a pipeline in the way of the actual
exit status. Avoid interpolating issue text into shell commands. A nonzero status
requires inspection; a zero status still requires checking the requested artifacts.
Neither model-step limits nor output truncation guarantee a monetary budget.

If the installed CLI lacks a required flag, stop that launch and report the mismatch.
Use its help or vendor documentation to establish a compatible invocation; never
silently drop YOLO/model selection/limits, switch providers, or change credentials.

## Reasoning configuration

Use `xhigh` for planning, implementation, and revisions unless the user/coordinator
explicitly chooses another effort. Extra high is the user-selected default because
max was unavailable on the current Contributor account; this is an explicit choice,
not an automatic fallback. Competency takes priority over token price.
The launcher and direct invocation both pass the effort explicitly; the native
CLI's `high` default is not used. Do not select `ultra` merely because it appears
in CLI help: that does not establish a stronger backend mode.

[Meta's release](https://research.meta.ai/blog/introducing-muse-spark-1-3) makes max
available in Muse Code and Meta Model API, and its
[evaluation methodology](https://research.meta.ai/static/muse-spark-1-3-multimodal-evaluation-methodology)
uses max for Muse Spark 1.3. [CursorBench 4.0](https://cursor.com/cursorbench)
reported 37.5% at extra high, 41.6% at max, and 32.6% at medium when checked on
2026-09-12. Max remains the stronger benchmark configuration; this evidence does
not guarantee a gain in Muse Code or
prove standard/Contributor parity or the meaning of `ultra`.

Before first dispatch with a model/account/effort combination, verify support
using a bounded harmless request in an empty temporary workspace. For example:

```sh
muse exec --model muse-spark-1.3-contributor --reasoning-effort xhigh \
  --max-model-steps 1 --workspace /absolute/path/to/empty-probe-workspace \
  --disable-shell --disable-write --disable-web-tools \
  --no-foreign-personal-context --no-session-log --json \
  'Reply with only OK. Do not use tools.'
```

Retain the command, stdout/stderr, real exit status, and terminal result. Record
requested model/effort separately from effective settings if the backend exposes
them; successful completion alone is only a compatibility check, not proof of
effective reasoning or competency. Do not rerun unchanged rejected configurations.

A local check on 2026-09-12 returned API 400 and exit 1 because max on Contributor
required an active Muse Code subscription for that account. Treat an equivalent
rejection as an access prerequisite, not an implementation defect. Resolve the
entitlement or obtain explicit agreement on a supported model/effort before more
work; do not purchase subscriptions, switch tiers, or downgrade automatically.
The launcher retains failure logs and propagates the failure status without retry.

The user subsequently selected `xhigh`; the same bounded check at extra high
completed with exit 0 and final answer `OK`, without an effort fallback warning.
This establishes compatibility for that account, not a competency benchmark or
independent proof of effective backend effort.
