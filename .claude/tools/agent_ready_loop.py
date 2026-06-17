#!/usr/bin/env python3
"""
Create isolated git worktrees from AGENT_TASKS.md.

Task format:
- [ ] TASK-001 | agent-ready | branch: agent/task-001 | title: Fix acronym titlecase
  - acceptance:
    - SSO remains SSO
  - verification:
    - python -m pytest tests/test_titlecase.py -q
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
TASKS = ROOT / "AGENT_TASKS.md"

def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)

def parse_task(task_id: str) -> dict[str, str]:
    if not TASKS.exists():
        raise SystemExit("AGENT_TASKS.md not found. Copy AGENT_TASKS.example.md first.")
    text = TASKS.read_text(encoding="utf-8")
    m = re.search(rf"(?ms)^- \[ \] {re.escape(task_id)} \| agent-ready \| branch:\s*([^|]+)\|\s*title:\s*(.+?)(?=^\- \[ \]|\Z)", text)
    if not m:
        raise SystemExit(f"Task {task_id} not found or not marked agent-ready.")
    return {"branch": m.group(1).strip(), "title": m.group(2).strip(), "body": m.group(0)}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--open-code", action="store_true", help="Open the worktree in VS Code after creation")
    args = ap.parse_args()

    task = parse_task(args.task)
    worktrees = ROOT / ".worktrees"
    worktrees.mkdir(exist_ok=True)
    wt = worktrees / args.task

    if not wt.exists():
        run(["git", "worktree", "add", "-b", task["branch"], str(wt)])
    else:
        print(f"Worktree already exists: {wt}")

    prompt_dir = wt / ".agent-harness"
    prompt_dir.mkdir(exist_ok=True)
    prompt = prompt_dir / f"{args.task}-prompt.md"
    prompt.write_text(f"""# Agent Task {args.task}

## Title

{task['title']}

## Task contract from AGENT_TASKS.md

{task['body']}

## Instructions for Claude Code

1. Read CLAUDE.md if present.
2. Restate acceptance criteria.
3. Implement the smallest coherent change.
4. Run the listed verification commands.
5. Run `python .claude/tools/verify.py --fast` if this scaffold is present.
6. Produce a critic-ready final report:
   - files changed
   - tests run
   - acceptance mapping
   - risks
   - next command
""", encoding="utf-8")

    print(f"\nWorktree ready: {wt}")
    print(f"Prompt ready:   {prompt}")
    print("\nStart Claude Code:")
    print(f"cd {wt}")
    print("claude")
    print(f"Then paste: Read {prompt} and execute the task contract.")

    if args.open_code:
        subprocess.run(["code", str(wt)], check=False)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
