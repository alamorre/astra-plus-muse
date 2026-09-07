# Muse execution

Verified against local `muse --help` and `muse exec --help` from Muse Code
1.0.3 (1.0.3-R2198.1), on 2026-09-07. The model ID below was also observed in active
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
  --reasoning-effort medium --max-model-steps 40 \
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
