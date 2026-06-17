---
description: Convert a rough voice brief or ticket into an agent-ready task contract with acceptance criteria, verification, non-goals, risks, and rollback.
---

# Agent-ready task contract

Use this skill when the user provides a rough brief, voice transcript, Slack message, Linear/GitHub ticket, or vague implementation idea.

## Output format

Produce:

```markdown
# Task Contract

## Goal
One precise sentence.

## Non-goals
- Explicitly list what should not change.

## Context
- Relevant repo areas, files, APIs, tickets, prior decisions.

## Acceptance criteria
- [ ] Observable criterion 1
- [ ] Observable criterion 2
- [ ] Observable criterion 3

## Verification
- Gate 1:
  - command:
  - expected result:
- Gate 2:
  - command/manual browser path:
  - expected result:
- Gate 3:
  - critic checklist:

## Worktree
- branch:
- suggested worktree path:

## Risk
- highest risk:
- rollback:
- files not to touch:

## Open questions
Only blocking questions. If not blocking, make a reasonable assumption and label it.
```

## Rules

- Convert fuzzy language into testable criteria.
- If the brief is too broad, split into subtasks.
- Prefer one worktree per independent task.
- Keep implementation out of this step unless explicitly asked.
