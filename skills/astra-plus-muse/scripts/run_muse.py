#!/usr/bin/env python3
"""Run one authorized Muse handoff, retaining output and the real process status."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def parser():
    result = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    result.add_argument("--workspace", type=Path, required=True)
    result.add_argument("--prompt-file", type=Path, required=True)
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--model", default="muse-spark-1.3-contributor",
                        help="explicit Muse model ID; no automatic fallback")
    result.add_argument("--reasoning-effort", default="xhigh",
                        choices=["none", "minimal", "low", "medium", "high",
                                 "xhigh", "max", "ultra"], help="worker reasoning effort")
    result.add_argument("--max-model-steps", type=positive_int, default=40,
                        help="Muse step cap for this invocation")
    result.add_argument("--max-tool-output-bytes", type=positive_int, default=12000,
                        help="Muse tool output cap; full process logs stay on disk")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    workspace = args.workspace.resolve()
    prompt = args.prompt_file.resolve()
    output = args.output_dir.resolve()
    if not workspace.is_dir() or not prompt.is_file() or prompt.stat().st_size == 0:
        raise ValueError("workspace must be a directory and prompt-file a nonempty file")
    if not args.model.strip():
        raise ValueError("model must not be empty")
    if output.exists():
        raise ValueError("output-dir already exists; preserve it and choose a new attempt")
    muse = shutil.which("muse")
    if muse is None:
        raise ValueError("Muse CLI is missing; install and authenticate it before dispatch")
    flags = ["--yolo", "--model", "--reasoning-effort", "--max-model-steps",
             "--max-tool-output-bytes", "--workspace", "--prompt-file", "--json"]
    help_result = subprocess.run([muse, "exec", "--help"], cwd=workspace,
                                 capture_output=True, text=True, timeout=30)
    help_text = help_result.stdout + help_result.stderr
    missing = [flag for flag in flags if flag not in help_text]
    if help_result.returncode or missing:
        raise ValueError(f"Muse exec help failed or required flags are missing: {missing}")
    command = [muse, "exec", "--yolo", "--model", args.model,
               "--reasoning-effort", args.reasoning_effort,
               "--max-model-steps", str(args.max_model_steps),
               "--max-tool-output-bytes", str(args.max_tool_output_bytes),
               "--workspace", str(workspace), "--prompt-file", str(prompt), "--json"]
    output.mkdir(parents=True, mode=0o700)
    (output / "invocation.json").write_text(json.dumps({
        "argv": command, "cwd": str(workspace),
    }, indent=2) + "\n")
    started = time.monotonic()
    # Files avoid unbounded in-memory event logs and preserve the actual exit code.
    with (output / "events.jsonl").open("wb") as stdout, \
            (output / "stderr.log").open("wb") as stderr:
        completed = subprocess.run(command, cwd=workspace, stdout=stdout, stderr=stderr)
    result = {"returncode": completed.returncode,
              "elapsed_seconds": round(time.monotonic() - started, 3)}
    # A sparse status reader must never mistake a partially written marker for completion.
    pending = output / "result.json.tmp"
    pending.write_text(json.dumps(result, indent=2) + "\n")
    pending.replace(output / "result.json")
    print(json.dumps({"output_dir": str(output), **result}))
    # subprocess uses negative signal numbers; shells use 128 + signal number.
    return completed.returncode if completed.returncode >= 0 else 128 - completed.returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"run_muse: {error}", file=sys.stderr)
        sys.exit(2)
