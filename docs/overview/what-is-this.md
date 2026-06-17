# What is this?

The Agent Balance Kit is a set of files you copy into a repository to turn Claude Code into a self-verifying, self-journaling coding harness.

## The problem it solves

Coding agents now scale faster than the human reviewing them. You can fire up four parallel agents and be exhausted by 11am — not because the agents are slow, but because *your attention* is the constraint, and it degrades under load. The kit's premise: agents loop infinitely if you give them context, verification criteria, and tools; the human still owns judgment, taste, and the merge decision. So the kit automates everything *except* judgment, and it spends deliberate effort protecting the human's attention.

## The mental model

Think of the kit as four layers stacked between a noisy world and a clean merge:

```
   Noisy world (Slack, Linear, GitHub, your own half-formed ideas)
        │
        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Layer 1 — Signal      Turn noise into a low-noise task inbox  │
 │                       (AGENT_TASKS.md)                        │
 ├─────────────────────────────────────────────────────────────┤
 │ Layer 2 — Dispatch    Turn a rough/voice brief into a precise │
 │                       task contract (agent-ready-task skill)  │
 ├─────────────────────────────────────────────────────────────┤
 │ Layer 3 — Execution   Run each task in an isolated git        │
 │                       worktree, steer it from your phone,     │
 │                       gate it with verification + a critic    │
 ├─────────────────────────────────────────────────────────────┤
 │ Layer 4 — Self-improve Journal every session, mine friction   │
 │                       weekly, mint one new skill per cycle    │
 └─────────────────────────────────────────────────────────────┘
        │
        ▼
   A verified diff + an explicit critic report → you decide to merge
```

Each layer is a small, independent mechanism. You can adopt one layer and ignore the rest. The kit is deliberately conservative: it never auto-merges, never auto-pushes, and never runs destructive shell commands.

## How the layers map to files

| Layer | What it does | Concrete files |
|-------|--------------|----------------|
| 1. Signal | A canonical task inbox so you stop opening noisy apps | `AGENT_TASKS.md`, `AGENT_TASKS.example.md` |
| 2. Dispatch | A skill that forces a fuzzy brief into a testable contract | `.claude/skills/agent-ready-task/SKILL.md` |
| 3. Execution | Worktree launcher, remote control, verification gates, subagents | `.claude/tools/agent_ready_loop.py`, `.claude/tools/verify.py`, `.claude/agents/*.md`, `.claude/hooks/*`, `.claude/settings.json` |
| 4. Self-improve | Session journaling and weekly skill mining | `.claude/tools/session_journal.py`, `.claude/tools/weekly_skill_miner.py`, `.claude/skills/session-retrospective/SKILL.md` |

A cross-cutting, optional dimension covers body-state — capping how many implementation agents you run based on how you slept. In v1 this was a manual rule; v2 makes it a tool (`health_state.py`) that emits a policy the night shift and scope-control skill read. See [scope and health](../concepts/scope-and-health.md).

> **On v2.** This page describes the four-layer core, which is unchanged. v2 extends each layer outward — live external signals, browser evidence, an opt-in strict gate, an autonomous night shift, and health-based scope — all additive and mostly opt-in. See [what's new in v2](whats-new-in-v2.md).

## How it all fits together: one end-to-end flow

1. A colleague reports a bug. Instead of opening Slack and getting hijacked by other threads, you add one line to `AGENT_TASKS.md` and mark it `agent-ready`.
2. You dictate a rough brief. The `agent-ready-task` skill converts it into a contract with explicit acceptance criteria and verification commands.
3. You run `agent_ready_loop.py --task TASK-001`. It creates `.worktrees/TASK-001/` — an isolated checkout on its own branch — and drops a prompt file the agent will read.
4. You start Claude Code in that worktree and walk away. From your phone, you steer it ("only satisfy the three acceptance criteria; stop expanding scope").
5. Every edit triggers a fast verification run (a hook). When the agent tries to mark the task complete, a hook blocks completion if verification fails.
6. Before merge, you ask the `critic` subagent for a read-only verdict: PASS, REVISE, or BLOCK.
7. When the session ends, a Stop hook journals it — including a count of friction signals like "error", "ambiguous", "retry".
8. On Friday, the weekly skill miner reads those journals and generates a prompt asking Claude to mint exactly one missing skill. Next week's loop is tighter.

You merged one diff with full evidence, and the harness got slightly smarter — without you having opened a single noisy app or sat at the desk all day.

## What this is NOT

- **Not an autonomous merge bot.** It stops at a verified diff plus a critic report. You merge.
- **Not a bundled Slack/Linear/Oura integration.** The kit ships no credentials. v2 adds *optional* signal sync and health input that you provision yourself (MCP servers or tokens in `.env`); without them, the local Markdown inbox is the default. See [ADR 001](../architecture/adr/001-local-inbox-before-mcp.md) and [ADR 005](../architecture/adr/005-non-mcp-signal-fallback.md).
- **Not an AI-powered journaler.** The Stop hook and weekly miner are plain deterministic Python — no model calls. See [ADR 002](../architecture/adr/002-deterministic-journaling.md).
- **Not a replacement for your project's own tests.** `verify.py` auto-detects common checks; you are expected to customize it per serious repo.

Next: [key concepts](key-concepts.md) defines every term, or jump to the [quickstart](../getting-started/quickstart.md).
