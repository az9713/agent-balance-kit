# System design

The Agent Balance Kit is a file-based harness layered over Claude Code. It has no server, no database, and no daemon — every component is a script, a markdown file, or a config entry that Claude Code or git executes. This is for developers who will *work on* the kit, not just use it.

## High-level architecture

```
                          ┌──────────────────────────────┐
                          │        AGENT_TASKS.md         │  Layer 1: Signal
                          │   (agent-ready | needs-spec)  │
                          └───────────────┬──────────────┘
                                          │
                       /agent-ready-task  │  Layer 2: Dispatch
                       (skill → contract) │
                                          ▼
                       ┌──────────────────────────────────┐
                       │      agent_ready_loop.py          │  Layer 3: Execution
                       │  git worktree add -b <branch>     │
                       │  .worktrees/<TASK>/ + prompt.md   │
                       └───────────────┬──────────────────┘
                                       │
                 ┌─────────────────────┼───────────────────────┐
                 ▼                     ▼                         ▼
        Claude Code session    Hooks (settings.json)     Subagents (.claude/agents)
        in the worktree    ┌───────────────────────┐   ┌────────────────────────┐
        (steer via remote  │ PostToolUse → verify   │   │ worktree-implementer   │
         control)          │ TaskCompleted → gate   │   │ browser-tester (Gate 2)│
                           │ PreToolUse → block      │   │ critic (Gate 3)        │
                           │ Stop → journal          │   └────────────────────────┘
                           └──────────┬─────────────┘
                                      │ verify.py → verify-log.jsonl
                                      │ session_journal.py → session-summaries/
                                      ▼
                       ┌──────────────────────────────────┐
                       │     weekly_skill_miner.py         │  Layer 4: Self-improve
                       │  summaries → weekly prompt → Claude│
                       │  → exactly one new SKILL.md        │
                       └──────────────────────────────────┘
```

> **v2 extends this diagram outward, not inward.** The four-layer spine above is unchanged. v2 adds, around it: external signal sync feeding `AGENT_TASKS.md` (Layer 1), browser evidence and an opt-in strict gate at completion (Layer 3), an autonomous night-shift poller (Layer 3), a draft-skill generator (Layer 4), and a health policy that throttles the whole thing. See [what's new in v2](../overview/whats-new-in-v2.md).

## Component breakdown

The v1 core:

| Component | Type | Role |
|-----------|------|------|
| `AGENT_TASKS.md` | Markdown | The signal inbox; first line is machine-parsed |
| `agent-ready-task` | Skill | Brief → task contract |
| `agent_ready_loop.py` | Python | Task → worktree + prompt file |
| `verify.py` | Python | Project-aware Gate 1 (and Gate 2 browser in v2); logs JSONL |
| `.claude/settings.json` | Config | Registers hooks across four events (five invocations) |
| `.claude/hooks/*` | Shell | Thin wrappers that call the Python tools |
| `critic` / `browser-tester` / `worktree-implementer` | Subagents | Gates 3 and 2, and isolated implementation |
| `session_journal.py` | Python | Stop-hook journaler (deterministic; BOM-safe stdin) |
| `weekly_skill_miner.py` | Python | Weekly mining-prompt generator |
| `.github/workflows/agent-verify.yml` | CI | Runs `verify.py --full` on push/PR |
| `.vscode/tasks.json` | Editor | One-click "Verify Fast" and "Weekly Skill Miner" |

The v2 additions:

| Component | Type | Role |
|-----------|------|------|
| `sync_external_signals.py` / `signal_triage.py` | Python | Pull Slack/Linear/GitHub → `signals/latest.json` → draft task cards |
| `signal-triage` skill / `signal-agent` | Skill / Subagent | Model-driven triage into the inbox |
| `browser_verify.py` | Python | Gate 2 browser evidence (Playwright) |
| `require_evidence.py` + `require-evidence` hook | Python / Hook | Opt-in strict completion gate (exit 2 blocks) |
| `poll_agent_ready.py` / `night_shift.py` | Python | Queue-only autonomous dispatch |
| `night-shift-supervisor` | Subagent | Plan-mode supervisor for the night shift |
| `health_state.py` | Python | Build the scope policy from health input |
| `scope-control` skill / `health-agent` | Skill / Subagent | Apply the policy to concurrency |
| `generate_skill.py` / `auto-skill-generation` | Python / Skill | Scaffold a draft skill from friction |
| `scripts/install-night-shift-*`, `night-shift-once.*`, `start-task-session.*` | Scripts | Schedulers and session launchers |

## Data flows

**Dispatch flow:** `AGENT_TASKS.md` line → `agent_ready_loop.py` parses branch/title → `git worktree add` → writes `.worktrees/<TASK>/.agent-harness/<TASK>-prompt.md` → human points Claude Code at the prompt.

**Verification flow:** agent edits a file → `PostToolUse` hook → `verify.py --fast` → appends to `.agent-harness/verify-log.jsonl`. Agent marks done → `TaskCompleted` hook → `verify.py --fast` → exit 2 blocks completion on failure.

**Journaling flow:** session ends → `Stop` hook pipes hook JSON to `session_journal.py` → appends to `.agent-harness/session-summaries/<date>.md` with friction counts.

**Improvement flow:** weekly → `weekly_skill_miner.py` reads last 14 summaries → writes weekly prompt → human pastes into Claude → one new `.claude/skills/<name>/SKILL.md`.

**External-signal flow (v2):** `sync_external_signals.py` → `.agent-harness/signals/latest.json` → `signal_triage.py --apply` → draft cards appended to `AGENT_TASKS.md`. Each source self-skips without credentials.

**Night-shift flow (v2):** scheduler (cron / Task Scheduler) → `night_shift.py` → `health_state.py` (policy) → optional sync + triage → `poll_agent_ready.py --once` → dispatch records in `.agent-harness/dispatches/` + lines in `.agent-harness/review-queue.md`. Never merges.

**Strict-gate flow (v2):** agent marks done → `TaskCompleted` runs `verify-before-complete` then `require-evidence` → if enabled and the critic/browser artifact is missing, exit 2 blocks completion.

## Key design decisions

Each is captured as an ADR — read these before changing the corresponding behavior:

| Decision | ADR |
|----------|-----|
| Ship a local Markdown inbox, not live Slack/Linear integration | [ADR 001](adr/001-local-inbox-before-mcp.md) |
| Make journaling deterministic (no AI), defer intelligence to a weekly pass | [ADR 002](adr/002-deterministic-journaling.md) |
| Never auto-merge or auto-push | [ADR 003](adr/003-no-auto-merge-no-auto-push.md) |
| Windows-first with dual PowerShell/Bash hooks | [ADR 004](adr/004-windows-first-dual-shell-hooks.md) |
| Credential-optional local signal sync by default, MCP as the upgrade | [ADR 005](adr/005-non-mcp-signal-fallback.md) |
| Strict completion-evidence gate is opt-in, off by default | [ADR 006](adr/006-opt-in-strict-evidence.md) |

## State and storage

All state is files in the target repo:

| Path | Contents | Version-controlled? |
|------|----------|---------------------|
| `AGENT_TASKS.md` | Your live inbox | Usually no (keep the `.example.md`) |
| `.worktrees/<TASK>/` | Isolated checkouts | No — gitignore |
| `.agent-harness/verify-log.jsonl` | Verification history | No — gitignore |
| `.agent-harness/session-summaries/` | Daily journals | No — gitignored in v2 |
| `.agent-harness/weekly/` | Weekly mining prompts | No — gitignored in v2 |
| `.agent-harness/signals/` | Synced external signals (v2) | No — gitignore |
| `.agent-harness/health_state/` | Generated scope policy (v2) | No — gitignore |
| `.agent-harness/dispatches/`, `review-queue.md` | Night-shift records (v2) | No — gitignore |
| `.agent-harness/browser-evidence/` | Gate 2 artifacts (v2) | No — gitignore |
| `.agent-harness/skill-drafts/` | Draft skills (v2) | No — gitignore |
| `HEALTH_STATE.md`, `.env` | Personal health/secrets (v2) | No — gitignored |
| `.claude/skills/`, `.claude/agents/` | The growing harness | Yes — commit |

The v2 `.gitignore` ignores the runtime outputs above (and `HEALTH_STATE.md`, `.env`). Two paths are *not* ignored — `.agent-harness/verify-log.jsonl` and a `STRICT_COMPLETION` sentinel — so they would be tracked if created.

## Continuous integration

`.github/workflows/agent-verify.yml` runs on every push to `main`/`master` and every pull request. It sets up Python 3.11 and Node 22, installs deps when lockfiles/manifests are present (`npm ci`, `pip install -r requirements.txt`, `pip install -e .`), and runs `python .claude/tools/verify.py --full`. CI is where `--full` (including build) belongs; the `TaskCompleted` hook stays on `--fast` so completion is quick.

## Scaling characteristics

- **Parallelism** scales with worktrees — each task is an independent checkout, so N agents need N worktrees. The real ceiling is human review capacity, not machine resources.
- **Verification** is per-repo and detection-based; it scales only as far as you extend `verify.py` and your test suite.
- **Journaling** is O(sessions) and cheap because it never calls a model; the weekly mining is O(one model call you trigger).
- The kit has **no shared mutable state** between agents, so there is nothing to contend on — the design is embarrassingly parallel up to your attention budget.

## Scope and health layer

In v1 this was a manual rule; v2 implements it as `health_state.py`, which turns `HEALTH_STATE.md` or Oura data into a policy the night shift and `scope-control` skill read:

| Rest state | Max agents | Night shift |
|------------|-----------|-------------|
| Poor | 1 | `off` |
| Normal | 2 | `queue-only` |
| Excellent | 3 | `dispatch-allowed` |

The deeper point is human-capacity-aware scheduling: the bottleneck is attention, so the number of agents you run should track how much reviewing attention you actually have. It is a workload guardrail, not medical advice. Full detail: [scope and health](../concepts/scope-and-health.md).

## Dependencies

Git, Python 3.10+, a shell, and Claude Code. On Windows the core hooks run on Windows PowerShell 5.1; PowerShell 7 (`pwsh`) is required only for the night-shift scheduler. Optional, per v2 feature: Node/npm (JS repos and the Playwright MCP), ruff, Playwright + Chromium (browser evidence), `cron` / Windows Task Scheduler (night shift), and API tokens or MCP servers for Slack/Linear/GitHub/Oura. No external services are required by the kit itself. Full matrix: [prerequisites](../getting-started/prerequisites.md).
