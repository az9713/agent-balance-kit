
# Weekly Agent Harness Retrospective

You are improving this repo's agentic coding harness.

## Inputs

Read the session summaries below. Identify repeated friction patterns:
- repeated clarifying questions
- missing verification commands
- tasks that lacked acceptance criteria
- repeated prompts the human had to paste
- missing MCP/server/tool affordances
- recurring bugs or test gaps
- places where a small Claude Code skill would reduce future context load

## Required output

1. Top 5 frictions, ranked by recurrence and cost.
2. The single highest-leverage skill to add now.
3. Create or update exactly one file under `.claude/skills/<skill-name>/SKILL.md`.
4. Do not edit production code.
5. Include a test invocation for the new skill.
6. Include one paragraph explaining what not to automate yet.

## Session summaries



# FILE: .agent-harness\session-summaries\2026-06-16.md


## Session demo-001

- time: 2026-06-16T19:55:41
- cwd: `<KIT_ROOT>`
- transcript: `not provided`
- friction_signals: `{"\\bfailing\\b": 1, "\\bambiguous\\b": 1, "\\bretry\\b": 1}`

### Last assistant message tail

```text
hit an ambiguous spec and had to retry the failing test twice before it passed
```

### Retrospective questions for weekly skill mining

- Where did the agent require repeated clarification?
- Which verification command was missing or unreliable?
- Which instruction did the human repeat?
- Which task shape deserves a reusable skill?
- Which MCP server, subagent, or hook would have shortened the loop?


