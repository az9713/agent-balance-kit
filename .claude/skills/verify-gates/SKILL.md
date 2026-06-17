---
description: Apply the three verification gates before claiming a coding task is complete.
---

# Verification gates

Use this skill before finalizing any code change.

## Gate 1 — code-level

Run the fastest reliable commands available:

- `python .claude/tools/verify.py --fast`
- project-specific unit tests
- lint/typecheck/build if present

## Gate 2 — behavior-level

Demonstrate the behavior in the running app or CLI.

Preferred:

- Claude Code `/run`
- Claude Code `/verify`
- browser click-through with Playwright/Chrome MCP
- CLI example with before/after output

If the app needs a custom launch recipe, run `/run-skill-generator` first.

## Gate 3 — judgment-level

Ask a critic subagent to review the diff against:

- acceptance criteria
- security
- regression risk
- UX/API compatibility
- overengineering
- missing tests
- unclear rollback

## Required final report

```markdown
## Final report

### Files changed
-

### Acceptance mapping
- Criterion:
  - evidence:

### Verification run
- command:
- result:

### Critic review
- reviewer:
- findings:
- remaining risks:

### Human decision needed
- merge / revise / abandon
```
