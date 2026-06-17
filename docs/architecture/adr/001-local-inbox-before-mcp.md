# ADR 001: Ship a local Markdown inbox instead of live Slack/Linear integration

**Status:** Accepted

## Context

The signal layer's job is to stop you from opening noisy apps. The talk that inspired the kit demonstrates Claude Code reading Slack and Linear over MCP, deduplicating asks, and surfacing only what matters. The obvious implementation would bundle those integrations.

But integrations need credentials, per-workspace configuration, and network access. Bundling them would mean either shipping fake/placeholder credentials (useless and misleading) or making the kit unusable until a multi-step OAuth dance is complete. The kit's goal is to be droppable into any repo in minutes.

## Decision

Ship a single local file, `AGENT_TASKS.md`, as the canonical inbox. Real Slack/Linear/GitHub integration is left to MCP servers the user configures in their own Claude Code environment; the user then asks Claude to summarize those sources *into the same `AGENT_TASKS.md` schema*.

## Alternatives considered

### Option A: Bundle Slack + Linear MCP config
Pros: matches the talk's demo exactly; zero manual task entry.
Cons: requires credentials the kit can't ship; breaks the "works in 5 minutes" promise; couples the kit to specific SaaS products; a security liability if credentials are mishandled.

### Option B: Local Markdown inbox (chosen)
Pros: zero external dependencies; works offline and in any repo immediately; the schema is the integration contract, so any source can feed it later.
Cons: manual task entry until you wire up MCP; no automatic dedup.

## Rationale

The *attention firewall* — the actual value — does not require live integration. The discipline of reducing an ask to one line in a file is itself the firewall. A local inbox delivers that on day one, and the schema becomes the stable target that real integrations populate later. Integration is an enhancement, not a prerequisite.

## Trade-offs

We gave up out-of-the-box automatic ingestion. New users type tasks by hand at first. We accepted that in exchange for a kit that installs anywhere instantly and never holds credentials.

## Consequences

- The `AGENT_TASKS.md` [grammar](../../reference/task-file-format.md) is a public contract; integrations must emit it.
- The kit holds no secrets, simplifying [ADR 003](003-no-auto-merge-no-auto-push.md)'s safety posture.
- Documentation must make the "connect MCP later" path explicit so users don't think manual entry is the ceiling. See [signal layer](../../concepts/signal-layer.md#configuration-and-tuning).
