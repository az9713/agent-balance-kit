---
description: Review recent Claude Code session summaries and identify missing skills, hooks, MCP servers, or task templates.
---

# Session retrospective

Use this skill when reviewing `.agent-harness/session-summaries/` or `.agent-harness/weekly/`.

## Job

Find repeated friction and convert exactly one high-frequency issue into a reusable improvement.

## Friction taxonomy

- **Spec ambiguity**: acceptance criteria missing or non-testable.
- **Verification gap**: agent could not prove the change worked.
- **Tool gap**: missing MCP, script, CLI, browser, fixture, seed data.
- **Skill gap**: repeated prompt/procedure should become `.claude/skills/<name>/SKILL.md`.
- **Subagent gap**: recurring specialist review deserves `.claude/agents/<name>.md`.
- **Safety gap**: dangerous command, secret access, production boundary unclear.
- **Human overload**: too many parallel agents, too many PRs, too much review debt.

## Output

1. Ranked friction table.
2. One recommended improvement.
3. Patch for exactly one skill/hook/agent file.
4. A test prompt proving the improvement triggers.
5. What remains manual.
