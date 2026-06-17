# Architecture Decision Records

The non-obvious choices in the kit, each recorded so a future engineer doesn't reverse it without the original context.

| ADR | Decision | Status |
|-----|----------|--------|
| [001](001-local-inbox-before-mcp.md) | Ship a local Markdown inbox instead of live Slack/Linear integration | Accepted |
| [002](002-deterministic-journaling.md) | Make journaling deterministic; defer intelligence to a weekly pass | Accepted |
| [003](003-no-auto-merge-no-auto-push.md) | Never auto-merge or auto-push | Accepted |
| [004](004-windows-first-dual-shell-hooks.md) | Windows-first, with dual PowerShell and Bash hook implementations | Accepted |
| [005](005-non-mcp-signal-fallback.md) | Ship a credential-optional local signal sync as the default, MCP as the upgrade | Accepted |
| [006](006-opt-in-strict-evidence.md) | Make the strict completion-evidence gate opt-in, off by default | Accepted |

ADRs 001–004 cover the v1 core; 005–006 cover the v2 additions ([what's new in v2](../../overview/whats-new-in-v2.md)).

See [system design](../system-design.md) for how these decisions shape the architecture.
