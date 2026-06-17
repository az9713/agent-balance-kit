---
name: scope-control
description: Adjust agent concurrency and task ambition using HEALTH_STATE.md, Oura/wearable signals, or the generated health policy file.
---

# Scope Control Skill

Use this before launching parallel agents, night-shift polling, or cross-stack refactors.

## Inputs

Read, in order:

1. `.agent-harness/health_state/latest_policy.json`
2. `HEALTH_STATE.md`
3. `.env`/environment policy variables

## Policy

- Poor sleep, low energy, high stress, or readiness score below 60:
  - max 1 implementation agent
  - no night-shift execution
  - no cross-stack refactors
  - only bug fixes with obvious verification
- Normal state:
  - max 2 implementation agents
  - night-shift may queue tasks but should not auto-execute unless explicitly enabled
  - cross-stack work requires a mini-spec
- Excellent state:
  - max 3 implementation agents
  - night-shift may dispatch low-risk worktrees
  - critic and browser evidence remain mandatory

## Output

Before work starts, state:

```text
Agent load decision: <1|2|3> implementation agents.
Night shift: <off|queue-only|dispatch-allowed>.
Reason: <one sentence>.
Blocked work types: <list>.
```

This is a guardrail, not a medical recommendation.
