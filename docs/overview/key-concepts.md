# Key concepts

Every term used across these docs, defined to stand alone. Grouped by layer, then alphabetical within general terms.

## General

**Agent Balance Kit (the kit)** — The collection of files in this repo (`.claude/`, `scripts/`, CI, VSCode tasks, and the root markdown docs) that scaffold a four-layer agentic workflow. Named after the talk it implements, whose thesis is that agents scale but human attention does not.

**Attention firewall** — The design goal behind Layer 1. Rather than letting noisy apps interrupt you, an agent reads them and surfaces only what's actionable, so your focus stays on work only a human can do.

**Harness** — The kit once installed into a target repo. "Run the harness" means use the installed scripts, hooks, skills, and subagents together.

**Layer** — One of the four independent mechanisms (signal, dispatch, execution, self-improvement). Each works alone; you can adopt one and skip the others.

**Target repo** — The repository you copy the kit into. The kit documents itself but is meant to be deployed elsewhere.

## Layer 1 — Signal

**Task inbox** — The file `AGENT_TASKS.md`, a low-noise replacement for browsing Slack/Linear/GitHub. You copy it from `AGENT_TASKS.example.md` on first use. See the [task file format](../reference/task-file-format.md).

**Task state** — A label a task carries. Only `agent-ready` is dispatchable; the v2 starter documents the full lifecycle: `signal` → `needs-spec` → `agent-ready` → `in-flight` → `review` → `done`. See [task file format](../reference/task-file-format.md#task-states).

**External signal sync (v2)** — An optional Layer 1 ingest that pulls Slack/Linear/GitHub items into `AGENT_TASKS.md`, either via MCP servers or the credential-optional local tools `sync_external_signals.py` (writes `.agent-harness/signals/latest.json`) and `signal_triage.py` (writes draft cards). See [signal layer](../concepts/signal-layer.md#external-signal-sync) and [ADR 005](../architecture/adr/005-non-mcp-signal-fallback.md).

## Layer 2 — Dispatch

**Task contract** — A structured task spec with a goal, non-goals, context, acceptance criteria, verification gates, worktree/branch, risk, and rollback. Produced by the `agent-ready-task` skill from a rough or voice brief. The contract is what makes "voice speed" safe — fast dictation without a contract produces ambiguous tasks that agents fail.

**Voice-first dispatch** — Using speech-to-text to brief agents, then forcing the transcript through the task-contract format. Fast enough to dispatch several agents before a typist finishes one prompt.

## Layer 3 — Execution

**Worktree** — An isolated git checkout created under `.worktrees/<TASK-ID>/` on its own branch, so parallel agents never collide in the same working tree. Created by `agent_ready_loop.py`.

**Prompt file** — The file `.worktrees/<TASK-ID>/.agent-harness/<TASK-ID>-prompt.md` that `agent_ready_loop.py` writes. It restates the task contract and tells Claude Code exactly what to do. You point the agent at it to start work.

**Remote control** — A Claude Code feature (`claude remote-control` or `/remote-control`) that lets you steer a local session from your phone or browser while execution stays on your machine. Requires Claude Code v2.1.51+. Outside server mode, one remote session per interactive process.

**Verification gate** — A checkpoint a change must pass before it counts as done. The kit defines three:
- **Gate 1 (code-level)** — lint, build, unit tests, Python compile check. Run by `verify.py`.
- **Gate 2 (behavior-level)** — run the app and demonstrate the behavior (CLI output or browser click-through).
- **Gate 3 (judgment-level)** — a critic subagent reviews the diff against acceptance criteria and risk.

**Critic** — The read-only `critic` subagent that returns a verdict of PASS, REVISE, or BLOCK. It cannot edit files. It is Gate 3.

**Browser evidence (v2)** — Artifacts (screenshots, console log, `report.md`) written under `.agent-harness/browser-evidence/<timestamp>/` by `browser_verify.py` (Playwright) to prove Gate 2 behavior. See [verification gates](../concepts/verification-gates.md#gate-2-browser-evidence).

**Strict evidence gate (v2)** — An opt-in second `TaskCompleted` hook (`require_evidence.py`) that blocks completion (exit 2) unless a critic report and/or browser evidence exists. Enabled by the `.agent-harness/STRICT_COMPLETION` sentinel or the `AGENT_REQUIRE_CRITIC`/`AGENT_REQUIRE_BROWSER` env vars. See [ADR 006](../architecture/adr/006-opt-in-strict-evidence.md).

**Night shift (v2)** — An autonomous, queue-only poll (`poll_agent_ready.py`, wrapped by `night_shift.py`) that turns `agent-ready` tasks into dispatch records and a review queue while you're away — never merging or deploying. See [worktree execution](../concepts/worktree-execution.md#the-night-shift).

**Subagent** — A specialized agent defined as a markdown file under `.claude/agents/`. The kit ships six: `critic`, `browser-tester`, `worktree-implementer`, plus the v2 `signal-agent`, `health-agent`, and `night-shift-supervisor`. See [skills & subagents](../reference/skills-and-subagents.md).

**Hook** — A command Claude Code runs automatically at a lifecycle point (before a tool, after a tool, on task completion, on stop). The kit registers hooks across four events — `TaskCompleted` runs two, for five invocations in all. See [hooks & settings](../reference/hooks-and-settings.md).

## Layer 4 — Self-improvement

**Session summary (journal)** — A markdown block appended to `.agent-harness/session-summaries/<date>.md` by the Stop hook when a session ends. It records the session id, cwd, transcript path, a tail of the last assistant message, and a count of friction signals. Deterministic — no model call.

**Friction signal** — A word or phrase the journaler counts as evidence the loop was rough: `error`, `failed`, `timeout`, `ambiguous`, `permission`, `blocked`, `retry`, `can't`, `cannot`, `not found`, `hallucinat`, `unclear`. High counts flag sessions worth mining.

**Skill miner** — The script `weekly_skill_miner.py`. It reads recent session summaries and writes a weekly prompt asking Claude to identify the top frictions and mint exactly one new skill. It does not call a model itself.

**Skill** — A reusable procedure for Claude Code, defined as `.claude/skills/<name>/SKILL.md` with a YAML `description`. The kit ships seven: `agent-ready-task`, `verify-gates`, `session-retrospective`, plus the v2 `signal-triage`, `scope-control`, `auto-skill-generation`, and `browser-verification`. The weekly loop adds more over time.

**Draft-skill generator (v2)** — The deterministic `generate_skill.py`, which scaffolds a draft `SKILL.md` from friction-keyword lines in your notes — the tool counterpart to the `auto-skill-generation` skill. See [self-improving harness](../concepts/self-improving-harness.md#automatic-draft-skill-generation-v2).

## Scope and health (cross-cutting)

**Health policy (v2)** — A JSON policy at `.agent-harness/health_state/latest_policy.json`, produced by `health_state.py` from `HEALTH_STATE.md` or Oura, that caps parallelism and gates the night shift: poor → 1 agent / `off`; normal → 2 / `queue-only`; excellent → 3 / `dispatch-allowed`. A workload guardrail, not medical advice. In v1 this was a manual rule; v2 makes it a tool the night shift and `scope-control` skill read. See [scope and health](../concepts/scope-and-health.md).
