# Worktree execution

The execution layer runs each task in an isolated git worktree and lets you steer it remotely, so agents can work in parallel without colliding and you can leave the desk while they do.

## Why it exists as its own layer

Two problems show up the moment you run more than one agent. First, agents editing the same working tree trample each other's changes. Second, the best ideas arrive *away* from the desk — in the shower, on a walk — and you don't want "walk away" to mean "stop work." Worktrees solve the first; remote control solves the second.

## How worktrees work

A git worktree is a second working directory attached to the same repository, on its own branch. The launcher creates one per task under `.worktrees/<TASK-ID>/`. Three agents in three worktrees are three independent checkouts; their diffs never touch until you merge them by hand.

### The launcher: `agent_ready_loop.py`

```powershell
python .claude/tools/agent_ready_loop.py --task TASK-001
```

What it does, in order:

1. Reads `AGENT_TASKS.md` and finds the line for `TASK-001`. It must be marked `agent-ready` or the script exits with an error.
2. Extracts the `branch` and `title` from that line.
3. Runs `git worktree add -b <branch> .worktrees/TASK-001` (skipped if the worktree already exists).
4. Writes a **prompt file** at `.worktrees/TASK-001/.agent-harness/TASK-001-prompt.md` containing the task contract and step-by-step instructions for Claude Code.
5. Prints the exact `cd` + `claude` commands to start, and the paste-in line. With `--open-code`, it also opens the worktree in VS Code.

> **Note:** The launcher resolves the repo root from `CLAUDE_PROJECT_DIR`, falling back to the current working directory when that's unset — the same resolution every kit tool uses. Run it from your repo root when invoking it by hand without that variable set.

### The prompt file

The generated prompt tells the agent to: read `CLAUDE.md`, restate the acceptance criteria, implement the smallest coherent change, run the listed verification commands, run `verify.py --fast`, and produce a critic-ready final report (files changed, tests run, acceptance mapping, risks, next command). Pointing the agent at this file is how you hand off the contract.

## Remote control

Remote control is a Claude Code feature, not kit code — the kit just provides a launch wrapper. It lets a phone or browser drive a session whose execution stays on your machine, with full local filesystem, MCP, and tool access.

Start it inside a session:

```text
/remote-control My Project
```

or from a terminal:

```powershell
claude remote-control --name "My Project"
# or the kit's wrapper:
.\scripts\start-remote-control.ps1 -Name "My Project"
```

```bash
./scripts/start-remote-control.sh "My Project"
```

**Requirements and limits:**

- Requires **Claude Code v2.1.51 or later**.
- The local process must keep running — close the terminal and the session dies.
- Outside server mode, each interactive process supports **one** remote session at a time.

The payoff: start serious thinking at the desk in focus mode, launch the agents, then walk away. From the trail you can narrow scope, answer a question, or fire back a design insight — and it's applied by the time you return.

> **One-command session start (v2):** `scripts/start-task-session.ps1 -Task TASK-001 [-RemoteControl]` (PowerShell) and `scripts/start-task-session.sh TASK-001 [--remote-control]` (Bash) wrap the launcher and `cd` into the worktree, optionally starting remote control in one step.

## The night shift

v2 adds an autonomous, **queue-only** poll so the execution layer keeps moving while you're away — without ever merging or deploying on its own (that stays a human act, [ADR 003](../architecture/adr/003-no-auto-merge-no-auto-push.md)). It is the same worktree mechanism, run on a timer and bounded by a health policy.

`poll_agent_ready.py` scans `AGENT_TASKS.md` for `agent-ready` tasks, and for each eligible one writes a dispatch record (`.agent-harness/dispatches/<TASK-ID>.json`) and appends `.agent-harness/review-queue.md` — a queue of work for *you* to launch and review, not finished merges. `night_shift.py` wraps a single conservative cycle (health policy → optional signal sync + triage → one poll). The [`night-shift-supervisor`](../reference/skills-and-subagents.md#night-shift-supervisor) subagent runs in `plan` mode and is blocked from auto-merge, deploy, migration, destructive shell, and broad refactors.

Two things bound it:

- **Health policy.** The poll reads `.agent-harness/health_state/latest_policy.json`; if `night_shift` is `off` it stops, and the task cap is clamped to the policy's `max_implementation_agents`. See [scope and health](scope-and-health.md).
- **Eligibility.** Only exact `agent-ready` tasks that aren't already dispatched run; the shipped `needs-spec` starter won't, by design.

Schedule it with `scripts/install-night-shift-cron.sh` (macOS/Linux) or `scripts/install-night-shift-windows.ps1` (Windows — requires PowerShell 7). Full walkthrough: [run the night shift](../guides/run-the-night-shift.md).

## Interaction with other layers

- **← Layer 2 (dispatch):** the `branch` and acceptance criteria in the [task contract](voice-first-dispatch.md) populate the `AGENT_TASKS.md` line this layer parses.
- **→ Verification:** every edit the agent makes in the worktree triggers the PostToolUse hook, and completion is gated. See [verification gates](verification-gates.md).
- **The `worktree-implementer` subagent** is an alternative to the launcher: it runs with `isolation: worktree`, giving Claude Code an isolated copy automatically. See [skills & subagents](../reference/skills-and-subagents.md#worktree-implementer).

## Configuration and tuning

- Worktrees live under `.worktrees/` at the repo root. Add it to `.gitignore` in your target repo.
- For a large cross-stack feature, don't dispatch it as one task. Split it into 3–5 subtasks, one worktree each. See the [parallel-agents guide](../guides/run-parallel-agents-for-a-large-feature.md).

## Common gotchas

- **"Task not found or not marked agent-ready."** The line isn't `agent-ready`, the ID is misspelled, or `branch:`/`title:` are out of order. See [task file format](../reference/task-file-format.md).
- **Worktree already exists.** The launcher won't recreate it; it reuses the existing one. Remove a stale worktree with `git worktree remove .worktrees/TASK-001`.
- **Remote control unavailable.** Check `claude --version` against the v2.1.51 minimum, and confirm the desk session is still running.
