# Agent Balance Kit

A Windows-first, cross-platform scaffold that drops a four-layer agentic-coding harness into any repo. It exists so you can run coding agents that verify their own work and journal their own friction — keeping *your* attention, not the agent's throughput, as the thing you spend carefully.

---

## Documentation

| Section | What's inside |
|---------|--------------|
| [What is this?](overview/what-is-this.md) | The mental model, the four layers, and how they fit together |
| [What's new in v2](overview/whats-new-in-v2.md) | The v2 additions, each mapped to its layer and doc |
| [Key concepts](overview/key-concepts.md) | Glossary of every term used across these docs |
| [Prerequisites](getting-started/prerequisites.md) | Exact dependencies with verify commands |
| [Quickstart](getting-started/quickstart.md) | Install into a repo and run your first verified task in ~15 minutes |
| [Onboarding](getting-started/onboarding.md) | Zero-to-hero: why the kit is shaped this way, with a full narrative walkthrough |
| [Concepts](concepts/) | Deep dives: [signal](concepts/signal-layer.md), [dispatch](concepts/voice-first-dispatch.md), [execution](concepts/worktree-execution.md), [verification](concepts/verification-gates.md), [self-improvement](concepts/self-improving-harness.md), [scope & health](concepts/scope-and-health.md) |
| [Guides](guides/) | Task-oriented how-tos: [install](guides/install-into-a-repo.md), [dispatch](guides/dispatch-your-first-task.md), [parallel agents](guides/run-parallel-agents-for-a-large-feature.md), [weekly retrospective](guides/run-the-weekly-retrospective.md), [external signals](guides/set-up-external-signals.md), [browser verification](guides/verify-in-the-browser.md), [night shift](guides/run-the-night-shift.md), [scope with health](guides/tune-scope-with-health.md) |
| [Reference](reference/) | Complete reference: [tools](reference/tools.md), [hooks & settings](reference/hooks-and-settings.md), [skills & subagents](reference/skills-and-subagents.md), [task file format](reference/task-file-format.md), [environment variables](reference/environment-variables.md) |
| [Architecture](architecture/system-design.md) | System design and [Architecture Decision Records](architecture/adr/) |
| [Troubleshooting](troubleshooting/common-issues.md) | The failures you will actually hit, and exact fixes |

> **New here?** Start with [What is this?](overview/what-is-this.md), then run the [Quickstart](getting-started/quickstart.md). Coming from v1? Read [What's new in v2](overview/whats-new-in-v2.md).

## Existing root documents

These shipped with the kit and remain authoritative for their narrow purpose. The docs above expand on them:

| File | Purpose |
|------|---------|
| [`../README.md`](../README.md) | Original install-and-use walkthrough |
| [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | Original four-layer summary |
| [`../CLAUDE.md`](../CLAUDE.md) | The operating manual Claude Code reads at session start |
| [`../AGENT_TASKS.example.md`](../AGENT_TASKS.example.md) | A worked example of the task inbox |
| [`../CHANGELOG_v2.md`](../CHANGELOG_v2.md) | The raw list of v2 additions |
| [`../MCP_SETUP.md`](../MCP_SETUP.md) | Configuring Slack/Linear/GitHub/Playwright/Oura MCP servers |
| [`../.env.example`](../.env.example) | Template for the external-signal and health env vars |
| [`../HEALTH_STATE.example.md`](../HEALTH_STATE.example.md) | Template for the manual health-state file |
