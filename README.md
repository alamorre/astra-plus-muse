# Astra plus Muse

A Codex skill for using **Astra as the strategic coordinator and PR reviewer**
while **Muse 1.3 Spark handles small GitHub issues and implementation**.

Muse proposes a batch → Astra resolves design decisions → Muse creates accepted
issues → Muse implements one PR per issue → Astra personally reviews and verifies
the final revision → Astra merges when authorized.

The aim is to spend expensive reasoning on decisions and review while delegating
routine coding. Savings depend on the task, pricing, and rework; no percentage is
promised. Astra sees completed PRs and explicit blockers: worker logs stay on disk,
with completion notifications preferred and status-only checks roughly every ten
minutes when polling is unavoidable. No continuous transcript watching.
This is a community workflow, not an official OpenAI or Meta integration.

## Install

Ask Codex:

```text
Use $skill-installer to install the skill at skills/astra-plus-muse
from https://github.com/alamorre/astra-plus-muse.
```

Or clone into Codex's personal skill directory:

```sh
git clone https://github.com/alamorre/astra-plus-muse.git /path/to/astra-plus-muse
mkdir -p ~/.agents/skills
ln -s /path/to/astra-plus-muse/skills/astra-plus-muse ~/.agents/skills/astra-plus-muse
```

Choose a new clone path and don't overwrite an existing installation. Codex
supports personal skills and symlink discovery; restart if it doesn't appear.
See [OpenAI's skill documentation](https://learn.chatgpt.com/docs/build-skills).

## Use

Select Astra in Codex, open the project, and provide a concrete goal:

```text
Use $astra-plus-muse to implement the CSV export milestone in this repository.
Have Muse propose bite-sized issues and implement them with Muse 1.3 Spark in
YOLO mode. You own design decisions and personally review each final PR revision.
You may create issues, push task branches, open PRs, and merge reviewed PRs into
develop once required checks pass. Keep at most two Muse workers running.
```

For review without merging, say “open and review PRs; leave merging to me.”
The skill retains your existing authorization and project instructions.

Prerequisites: Codex with Astra access; a separately installed and authenticated
Muse CLI with access to `muse-spark-1.3-contributor`; Git; authenticated GitHub CLI
with the permissions your task needs. Python 3.10+ is needed only for the optional
launcher. Muse availability is account-dependent; this repo does not distribute
the CLI or credentials. The invocation was checked against Muse Code 1.0.3.

**YOLO disables Muse's approvals and sandbox and trusts the workspace for the run.**
Workers can use the permissions and credentials available to that process.
Worktrees and “do not merge” prompts are coordination rules, not access controls.
Use a suitably isolated environment or restricted worker credentials if needed.

The [skill](skills/astra-plus-muse/SKILL.md) includes the operating workflow,
[handoff contracts](skills/astra-plus-muse/references/handoffs.md), and a
[launcher reference](skills/astra-plus-muse/references/cli.md). The verified CLI
accepts a role/task prompt file, not a dedicated system-prompt override. No changes
to global Codex or Muse configuration are required.

## Development

```sh
python3 -m venv venv
venv/bin/python -m unittest discover -s tests -v
```

Tests use a fake Muse executable and isolated temporary directories; they do not
spend model credits or create GitHub issues. A real worker's successful exit still
requires inspection of its work and Astra's review.

MIT licensed. Contributions that make delegation more reliable without adding
coordinator overhead are welcome.
