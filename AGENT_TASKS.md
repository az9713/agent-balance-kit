# Agent Tasks

This is the canonical local task inbox. External signal sync and manual triage should write here.

Status vocabulary:
- `signal`: raw ask; not dispatchable.
- `needs-spec`: promising but missing acceptance criteria or verification.
- `agent-ready`: dispatchable to a worktree.
- `in-flight`: dispatched; awaiting diff/evidence.
- `review`: needs human/critic review.
- `done`: merged or intentionally closed.

## Tasks

- [ ] TASK-001 | needs-spec | branch: agent/task-001 | title: Replace this starter task
  - source: manual
  - goal: Replace this task with your first real agent-ready task.
  - acceptance:
    - Add at least one observable acceptance criterion.
  - verification:
    - python .claude/tools/verify.py --fast
