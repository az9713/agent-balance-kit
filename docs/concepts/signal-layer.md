# Signal layer

The signal layer turns a noisy stream of asks into one low-noise task inbox, so you never open Slack, Linear, or GitHub just to find out what to work on.

## Why it exists as its own layer

Opening a noisy app to "just check" is the single most expensive context switch in agentic work. You go in for one bug and come out with three new threads, a derailed afternoon, and the original bug forgotten. The signal layer firewalls that: an agent (or, in the shipped kit, *you* writing one disciplined line) reads the noise and reduces it to a ranked list of actionable tasks. The benefit is not "AI reads Slack" — it's that your attention stays on the work only you can do.

## How it works

The deployable mechanism is a single file: `AGENT_TASKS.md`, copied from `AGENT_TASKS.example.md`. Every incoming ask becomes one task with a state:

| State | Meaning | What happens |
|-------|---------|--------------|
| `agent-ready` | Fully specified, has acceptance criteria | Can be dispatched to a worktree |
| `needs-spec` | Missing target, path, or criteria | Clarify before dispatching |
| `noise` | Not worth doing | Ignore (conceptual — not parsed) |

Only `agent-ready` tasks are dispatchable. The launcher (`agent_ready_loop.py`) will refuse anything else — see its parsing rules in the [task file format](../reference/task-file-format.md).

## The data: one task's anatomy

A ready task is a checklist line plus indented fields:

```markdown
- [ ] TASK-001 | agent-ready | branch: agent/task-001 | title: Fix acronym-preserving sentence case
  - repo_area: src/text
  - goal: Sentence-case headings without mangling acronyms.
  - non_goals:
    - Do not change markdown rendering.
  - acceptance:
    - SSO remains SSO.
    - API remains API.
    - "HELLO WORLD" becomes "Hello world".
  - verification:
    - python -m pytest tests/test_sentence_case.py -q
  - rollback:
    - Revert the branch.
```

Only the **first line** is machine-parsed (the ID, the `agent-ready` state, the branch, and the title). Everything indented under it is free-form context that gets copied verbatim into the agent's prompt file. That means the sub-fields are for the *agent and you* to read — be as precise as you'd want the agent to be.

## Interaction with other layers

- **→ Layer 2 (dispatch):** A `needs-spec` task is exactly what the [`agent-ready-task` skill](voice-first-dispatch.md) is for — feed it the rough ask and it produces the criteria that promote it to `agent-ready`.
- **→ Layer 3 (execution):** `agent_ready_loop.py --task TASK-001` reads this file, finds the `agent-ready` line, and builds the worktree. See [worktree execution](worktree-execution.md).

## External signal sync

v1 keeps the inbox fully manual — you write each line. v2 adds an **optional** ingest path that pulls Slack, Linear, and GitHub items into the same `AGENT_TASKS.md`, without you opening those apps. It has two modes, and both converge on the same task-card output:

| Mode | How | When |
|------|-----|------|
| MCP servers (richer) | Configure servers named `slack`/`linear`/`github` in Claude Code; the [`signal-triage`](../reference/skills-and-subagents.md#signal-triage) skill / [`signal-agent`](../reference/skills-and-subagents.md#signal-agent) read them directly | You already run those MCP servers |
| Local fallback (default) | `sync_external_signals.py` writes `.agent-harness/signals/latest.json`; `signal_triage.py` turns it into draft cards | Credential-optional, no MCP setup |

The default is the credential-optional local fallback: each source self-skips when its token is missing, so the tools run with zero configuration and the kit stays credential-free. This is [ADR 005](../architecture/adr/005-non-mcp-signal-fallback.md), and it extends [ADR 001](../architecture/adr/001-local-inbox-before-mcp.md)'s "local inbox first" stance rather than replacing it.

Triage stays conservative: new cards default to `needs-spec`, capped at 5 per pass, so nothing is auto-marked ready. You still promote a task deliberately. Step-by-step setup is in [set up external signals](../guides/set-up-external-signals.md); credentials are in [environment variables](../reference/environment-variables.md).

> **Silent-skip caveat:** `sync_external_signals.py` always exits 0 and records missing credentials/network errors *inside* `latest.json` rather than failing. A misconfiguration can look like success — read the `Skipped/errors` output. And `.env.example` ships a `GITHUB_REPOSITORY=owner/repo` placeholder that triggers a real failing API call if copied verbatim.

## Configuration and tuning

The inbox itself needs no configuration — it's a Markdown file. To scale it:

- **Solo/public projects:** replace Slack/Linear with GitHub Issues or this file directly.
- **Connected workspaces:** use the [external signal sync](#external-signal-sync) above, or configure MCP servers and ask Claude to summarize them *into this same schema*. The kit deliberately does not ship credentials — see [ADR 001](../architecture/adr/001-local-inbox-before-mcp.md).

## Common gotchas

- **`AGENT_TASKS.md` doesn't exist yet.** The launcher reads `AGENT_TASKS.md`, not the `.example.md`. Copy it first: `Copy-Item AGENT_TASKS.example.md AGENT_TASKS.md`.
- **A task won't dispatch.** The first line must match the grammar exactly, including the literal `- [ ] ` (unchecked box), the `agent-ready` state, and `branch:` appearing *before* `title:`. See [task file format](../reference/task-file-format.md).
- **Over-filling the inbox.** The discipline is to mark things `needs-spec` honestly rather than dispatching half-specified work. A small `agent-ready` list you trust beats a large one you don't.
