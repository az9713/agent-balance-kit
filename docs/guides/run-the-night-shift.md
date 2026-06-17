# Run the night shift

Run a conservative, queue-only recurring poll that turns `agent-ready` tasks into worktree prompts and a review queue. The night shift never auto-merges and never deploys — it only queues work for you to launch and review. See [ADR 003](../architecture/adr/003-no-auto-merge-no-auto-push.md).

> **Goal:** for each eligible task, a `.agent-harness/dispatches/<TASK-ID>.json` worktree prompt and a `.agent-harness/review-queue.md` entry — created on a schedule, with nothing merged.

## One pass by hand

```powershell
python .claude/tools/night_shift.py [--sync] [--oura] [--max-tasks N]
```

The cycle runs, in order:

1. `health_state.py` (with `--oura` when you pass `--oura`) to refresh the policy.
2. Only with `--sync`: `sync_external_signals.py --all`, then `signal_triage.py --apply`.
3. `poll_agent_ready.py --once` (with `--max-tasks N` when given).

It resolves its child tools under `CLAUDE_PROJECT_DIR` (falling back to the current directory), so it works from anywhere once that variable is set; run it from the repo root if it isn't. It does **not** abort if a step fails; a failed sync or health refresh still lets the poll run.

## The poller

```powershell
python .claude/tools/poll_agent_ready.py [--once|--loop] [--every-minutes 15] [--max-tasks N] [--execute]
```

It reads `.agent-harness/health_state/latest_policy.json` and `AGENT_TASKS.md`. For each eligible task it writes `.agent-harness/dispatches/<TASK-ID>.json` and appends a line to `.agent-harness/review-queue.md`.

| Behavior | Detail |
| --- | --- |
| Night shift off | If the policy's `night_shift` is `off`, it prints a notice and stops. |
| Concurrency cap | `--max-tasks` is clamped to the policy's `max_implementation_agents`, which falls back to the `AGENT_MAX_CONCURRENT` env var (default 1). |
| `--execute` | A reserved no-op. The poller stays queue-only and prints the manual launch command instead of running Claude. |
| Exit code | Always 0. |

## Eligibility

A task is dispatched only if **all** of these hold:

- its status is exactly `agent-ready`,
- it matches the strict one-line task grammar,
- no `.agent-harness/dispatches/<TASK-ID>.json` already exists for it.

The shipped starter `TASK-001` is `needs-spec`, so nothing dispatches until you promote a task to `agent-ready`. See [task file format](../reference/task-file-format.md).

## Schedule it

### macOS / Linux

```bash
bash scripts/install-night-shift-cron.sh
```

This installs a crontab entry:

```text
*/15 * * * * cd '<repo>' && python .claude/tools/night_shift.py --sync --max-tasks 1 >> .agent-harness/night-shift.log 2>&1
```

Output is appended to `.agent-harness/night-shift.log`.

### Windows

```powershell
pwsh scripts/install-night-shift-windows.ps1 [-TaskName AgentBalanceNightShift] [-RepoPath <cwd>] [-IntervalMinutes 15]
```

This registers a Scheduled Task whose action runs `pwsh.exe ... scripts\night-shift-once.ps1` (which runs `night_shift.py --sync --max-tasks 1`). It **requires PowerShell 7 (`pwsh`)** — see [prerequisites](../getting-started/prerequisites.md#v2-feature-dependencies). Unlike cron, the scheduled task does **not** redirect output to a log file.

### A single pass for either OS

`scripts/night-shift-once.ps1` and `scripts/night-shift-once.sh` each run `night_shift.py --sync --max-tasks 1` once. The schedulers above call these.

## The supervisor subagent

The `night-shift-supervisor` subagent (model `sonnet`, `permissionMode: plan`) stays queue-only and is blocked from auto-merge, production deploy, database migration, destructive shell, and broad cross-stack refactors unless you explicitly override. See [skills & subagents](../reference/skills-and-subagents.md#night-shift-supervisor).

## Gotchas

- **`pwsh` is required on Windows.** The installer and the once-script invoke `pwsh.exe`; Windows PowerShell 5.1 will not run them.
- **Run manual invocations from the repo root** (or set `CLAUDE_PROJECT_DIR`). The tools resolve `.agent-harness/` and their children under `CLAUDE_PROJECT_DIR`, falling back to the current directory when it's unset.
- **Logging differs by OS.** cron appends to `.agent-harness/night-shift.log`; the Windows Scheduled Task does not redirect output anywhere.
- **A poor or `off` health policy throttles the shift to zero.** `max_implementation_agents` caps `--max-tasks`, and `night_shift: off` stops the poll entirely. See [scope and health](../concepts/scope-and-health.md).
- **The starter task won't dispatch.** `TASK-001` ships as `needs-spec`. Promote a task to `agent-ready` first.

## Related

- [worktree execution](../concepts/worktree-execution.md#the-night-shift)
- [scope and health](../concepts/scope-and-health.md)
- [tune scope with health](tune-scope-with-health.md)
- [task file format](../reference/task-file-format.md)
- [tools](../reference/tools.md)
