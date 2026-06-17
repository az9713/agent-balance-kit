# Reference: skills and subagents

The seven skills under `.claude/skills/` and six subagents under `.claude/agents/` that ship with the kit. The weekly retrospective adds more skills over time.

The first three skills and three subagents are the v1 core loop; the rest power the v2 features (external signals, browser evidence, health-based scope, the night shift). See [what's new in v2](../overview/whats-new-in-v2.md).

## Skills

A skill is a `SKILL.md` file with YAML frontmatter (`description`) plus a body Claude reads when the skill is relevant or invoked. Invoke explicitly with `/<skill-name>`.

### agent-ready-task

**Description:** Convert a rough voice brief or ticket into an agent-ready task contract with acceptance criteria, verification, non-goals, risks, and rollback.

**Triggers on:** a rough brief, voice transcript, Slack message, Linear/GitHub ticket, or vague implementation idea.

**Produces** a `# Task Contract` with these sections: Goal (one sentence), Non-goals, Context, Acceptance criteria (checkboxes), Verification (Gate 1/2/3 with commands + expected results), Worktree (branch + path), Risk (highest risk, rollback, files not to touch), Open questions (blocking only).

**Rules:** convert fuzzy language into testable criteria; split if too broad; one worktree per independent task; keep implementation out unless asked.

See [voice-first dispatch](../concepts/voice-first-dispatch.md).

### verify-gates

**Description:** Apply the three verification gates before claiming a coding task is complete.

**Gate 1 (code):** `python .claude/tools/verify.py --fast`, project unit tests, lint/typecheck/build.
**Gate 2 (behavior):** `/run`, `/verify`, Playwright/Chrome browser click-through, or a CLI before/after example. Run `/run-skill-generator` first if the app needs a custom launch recipe.
**Gate 3 (judgment):** a critic subagent reviews against acceptance criteria, security, regression risk, UX/API compatibility, overengineering, missing tests, unclear rollback.

**Requires a final report** mapping files changed → acceptance evidence → verification run → critic review → human decision (merge/revise/abandon).

See [verification gates](../concepts/verification-gates.md).

### session-retrospective

**Description:** Review recent Claude Code session summaries and identify missing skills, hooks, MCP servers, or task templates.

**Use on:** `.agent-harness/session-summaries/` or `.agent-harness/weekly/`.

**Friction taxonomy:** spec ambiguity, verification gap, tool gap, skill gap, subagent gap, safety gap, human overload.

**Output:** a ranked friction table; one recommended improvement; a patch for exactly one skill/hook/agent file; a test prompt proving it triggers; and what remains manual.

See [self-improving harness](../concepts/self-improving-harness.md).

### signal-triage

**Description:** Convert Slack, Linear, GitHub, or Markdown inbound signals into a small set of agent-ready tasks without opening noisy apps manually.

**Reads, in priority order:** MCP tools named `slack`/`linear`/`github`; `.agent-harness/signals/latest.json` (from `sync_external_signals.py`); `.agent-harness/signals/inbox.md` (pasted messages); existing `AGENT_TASKS.md`.

**Produces** append-only task cards in `AGENT_TASKS.md` (id, status, `branch:`, `title:`, source, goal, non_goals, acceptance, verification, risk). Hard rules: deduplicate before appending, never more than 5 new tasks per pass, prefer one boring task, and stop and write the exact missing setup step if a source needs authentication.

> **Divergence:** the skill defines four classes (`ignore`, `needs-human`, `needs-spec`, `agent-ready`); its deterministic counterpart [`signal_triage.py`](tools.md#signal_triagepy) emits only `agent-ready`/`needs-spec`/`signal`. The skill is the richer Claude-driven path. See [signal layer](../concepts/signal-layer.md#external-signal-sync).

### scope-control

**Description:** Adjust agent concurrency and task ambition using `HEALTH_STATE.md`, wearable signals, or the generated health policy file.

**Reads, in order:** `.agent-harness/health_state/latest_policy.json`; `HEALTH_STATE.md`; `.env`/environment policy variables.

**Produces** a decision block: agent load (1–3), night shift (`off`/`queue-only`/`dispatch-allowed`), reason, and blocked work types. It is a workload guardrail, not medical advice. See [scope and health](../concepts/scope-and-health.md).

### auto-skill-generation

**Description:** Convert repeated session friction into exactly one new project skill written under `.claude/skills/`.

**Reads:** `.agent-harness/session-summaries/`, `.agent-harness/weekly/`, `.agent-harness/skill-drafts/`. **Produces** exactly one `.claude/skills/<slug>/SKILL.md`. Hard constraints: one friction pattern only, one skill folder, never edit product code, no broad "be better at coding" skills. The deterministic counterpart is [`generate_skill.py`](tools.md#generate_skillpy). See [self-improving harness](../concepts/self-improving-harness.md).

### browser-verification

**Description:** Run real browser click-through smoke checks and produce evidence before a task is considered complete.

**Use when** a task changes UI, auth, routing, forms, dashboards, browser-visible content, or frontend data flow. It has the agent create `.agent-harness/browser_targets.json` (from the shipped `browser_targets.example.json`) and run `python .claude/tools/browser_verify.py --config .agent-harness/browser_targets.json`, then refuse to claim completion unless `.agent-harness/browser-evidence/<timestamp>/report.md` exists. See [verify in the browser](../guides/verify-in-the-browser.md).

## Subagents

A subagent is a markdown file with YAML frontmatter under `.claude/agents/`. Frontmatter controls tools, model, permission mode, isolation, attached skills, and MCP servers.

### critic

| Field | Value |
|-------|-------|
| `tools` | Read, Grep, Glob, Bash |
| `model` | sonnet |
| `permissionMode` | plan |
| `color` | red |

**Read-only reviewer.** Reviews completed work against acceptance criteria, the diff, tests/verification logs, security and data-loss risk, regression risk, overengineering, missing negative tests, and unclear rollback. **Cannot edit files.** Returns a `# Critic Report` with a verdict of **PASS / REVISE / BLOCK**, acceptance mapping, verification evidence, risks, required fixes, and optional improvements. This is Gate 3.

### browser-tester

| Field | Value |
|-------|-------|
| `tools` | Read, Grep, Glob, Bash |
| `model` | sonnet |
| `permissionMode` | default |
| `color` | blue |
| `mcpServers` | `playwright` (stdio, `npx -y @playwright/mcp@latest`) |

**Behavior tester for UI/web changes.** Finds how to launch the app (README/`package.json`/Makefile), navigates the relevant path, exercises the exact acceptance criteria, and captures failures with URL, steps, and observed result. Does not edit product code unless asked. This is Gate 2. Requires Node/npm for the Playwright MCP server.

### worktree-implementer

| Field | Value |
|-------|-------|
| `tools` | Read, Grep, Glob, Bash, Edit, Write |
| `model` | inherit |
| `permissionMode` | default |
| `isolation` | worktree |
| `skills` | verify-gates |
| `color` | green |

**Implementation agent** for a single task in an isolated worktree. With `isolation: worktree`, Claude Code gives it its own repository copy automatically — an alternative to the [`agent_ready_loop.py`](tools.md#agent_ready_looppy) launcher. Rules: restate the contract before editing, don't expand scope, keep diffs minimal, run verification, ask the critic for review, and produce a final report. It inherits the session model and has the `verify-gates` skill attached.

### signal-agent

| Field | Value |
|-------|-------|
| `model` | sonnet |
| `permissionMode` | default |

**Attention filter, not an executor.** Reads external/project signals (MCP `slack`/`linear`/`github` if available, else `.agent-harness/signals/latest.json`, `inbox.md`, and `AGENT_TASKS.md`) and produces a deduplicated patch to `AGENT_TASKS.md`. It uses the `signal-triage` skill and is explicitly forbidden from launching worktrees, implementing code, or browsing noisy source apps. This is the Layer 1 ingest helper. See [signal layer](../concepts/signal-layer.md#external-signal-sync).

### health-agent

| Field | Value |
|-------|-------|
| `model` | haiku |
| `permissionMode` | default |

**Workload guardrail.** Reads `.agent-harness/health_state/latest_policy.json` (or `HEALTH_STATE.md`) and returns max implementation agents, night-shift state (`off`/`queue-only`/`dispatch-allowed`), blocked work classes, and a one-sentence rationale. It never recommends increasing workload when sleep is poor, energy is low, or stress is high, and gives no medical advice. See [scope and health](../concepts/scope-and-health.md).

### night-shift-supervisor

| Field | Value |
|-------|-------|
| `model` | sonnet |
| `permissionMode` | plan |

**Queue-only supervisor** for low-risk recurring polling. Reads the health policy, `AGENT_TASKS.md`, `.agent-harness/dispatches/`, and `.agent-harness/review-queue.md`; it may triage signals, create worktree prompts, write launch commands, and mark tasks queued. `permissionMode: plan` keeps it from acting. It is blocked from auto-merge, production deploy, DB migration, destructive shell, and broad cross-stack refactors unless you explicitly override — mirroring the [safety constraints](../../CLAUDE.md) and [ADR 003](../architecture/adr/003-no-auto-merge-no-auto-push.md). See [run the night shift](../guides/run-the-night-shift.md).

## How they compose

A typical task uses three subagents and two skills:

1. `agent-ready-task` (skill) → contract.
2. `worktree-implementer` (subagent) → implements in isolation, guided by `verify-gates` (skill).
3. `browser-tester` (subagent) → Gate 2 behavior check.
4. `critic` (subagent) → Gate 3 verdict.

The v2 subagents extend the loop outward: `signal-agent` feeds Layer 1 (signals → tasks), `health-agent` sets the scope budget, and `night-shift-supervisor` runs the queue-only poll while you're away. None of them merge or deploy.
