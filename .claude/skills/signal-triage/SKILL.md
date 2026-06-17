---
name: signal-triage
description: Convert Slack, Linear, GitHub, or Markdown inbound signals into a small set of agent-ready tasks without opening noisy applications manually.
---

# Signal Triage Skill

Purpose: protect the human's attention. You are not trying to ingest everything. You are trying to surface only asks that deserve action.

## Inputs

Use whichever sources are available:

1. MCP tools named `slack`, `linear`, or `github`.
2. `.agent-harness/signals/latest.json` produced by `sync_external_signals.py`.
3. `.agent-harness/signals/inbox.md` for pasted messages.
4. Existing `AGENT_TASKS.md`.

## Classification

Classify each inbound item as:

- `ignore`: FYI, duplicate, social, non-actionable.
- `needs-human`: requires judgment, politics, commitment, or sensitive context.
- `needs-spec`: likely useful, but missing acceptance criteria or verification.
- `agent-ready`: specific enough to dispatch to an isolated worktree.

## Output contract

Append only concise task cards to `AGENT_TASKS.md`:

```markdown
- [ ] TASK-123 | agent-ready | branch: agent/task-123 | title: Short imperative title
  - source: slack|linear|github|manual:<link-or-id>
  - goal: Observable result.
  - non_goals:
    - Explicitly out of scope.
  - acceptance:
    - User-observable criterion.
  - verification:
    - Exact command.
  - risk:
    - Main failure mode.
```

## Hard rules

- Deduplicate against existing tasks before appending.
- Do not dispatch vague tasks.
- Never create more than 5 new tasks in one triage pass.
- Prefer one boring `agent-ready` task over five ambiguous tasks.
- If Slack/Linear/GitHub tools require authentication, stop and write the exact missing setup step.
