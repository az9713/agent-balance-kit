# ADR 005: Ship a credential-optional local signal sync as the default, MCP as the upgrade

**Status:** Accepted

## Context

v1 deliberately shipped a local Markdown inbox before any live integration ([ADR 001](001-local-inbox-before-mcp.md)) and holds no credentials. The signal layer's value — an attention firewall — does not depend on live SaaS access; it depends on reducing noise to a ranked task list.

v2 wants external signals (Slack, Linear, GitHub) without breaking that credential-free default. The constraint: a fresh clone with zero configuration must still run the sync tool successfully and produce something the rest of the kit can read. Each sync source therefore self-skips — it emits a `"skipped"` record when its token is absent — so the tool runs with no setup and never raises on missing credentials.

## Decision

Layer 1's external-signal ingestion defaults to deterministic local tools. `sync_external_signals.py` writes a normalized `.agent-harness/signals/latest.json`; `signal_triage.py` turns that file into conservative draft task cards in `AGENT_TASKS.md`. Live MCP servers (slack, linear, github) are an optional richer path, not a requirement.

The file-based `latest.json` is the contract both paths share. Whether signals arrive from the local sync tool or from MCP servers a user wires up themselves, the downstream triage reads the same normalized shape and emits the same task-card output.

## Alternatives considered

### Option A: MCP-only

Pros: matches the inspiring talk's demo; richest data; live dedup.

Cons: every user must stand up MCP servers before anything works; contradicts the credential-free default established in [ADR 001](001-local-inbox-before-mcp.md); nothing in Layer 1 functions until configured.

### Option B: No external signals (v1 status quo)

Pros: zero new surface area; no network calls; no new failure modes.

Cons: leaves Layer 1 fully manual; the "stop opening noisy apps" promise still requires the human to read the noise.

### Option C: Deterministic local fallback that self-skips, MCP as opt-in upgrade (chosen)

Pros: default stays zero-credential and offline-capable; each source self-skips when its token is missing; the `latest.json` contract lets the MCP and non-MCP paths converge on identical task cards.

Cons: the unauthenticated path is thinner than MCP (GitHub without a token is rate-limited; Slack and Linear do nothing without their tokens); a tool that always exits `0` can mask a misconfiguration.

## Rationale

Keeping the default zero-credential and offline-capable preserves the [ADR 001](001-local-inbox-before-mcp.md) posture: the kit installs anywhere and holds no secrets. Because `latest.json` is a stable file contract rather than a live API surface, the triage skill does not care whether the signals came from the bundled sync tool or from MCP servers — both paths land in the same place and produce the same draft cards. MCP becomes an enhancement that enriches the input, not a gate that blocks the loop.

## Trade-offs

The sync tool **always exits `0`**. Missing credentials and network errors are recorded inside `latest.json` as `"skipped"` / `"error"` records rather than failing the process. The benefit is that a no-config run and a scheduled run never crash; the cost is that a misconfiguration can look like success. The console summary prints skipped/error reasons, but an automated caller that only checks the exit code will not notice.

`.env.example` ships a non-empty `GITHUB_REPOSITORY=owner/repo` placeholder. Unlike the empty token fields, a non-empty repository value defeats the self-skip: copied verbatim, it triggers a real API call against a repository named `owner/repo`, which returns an `"error"` record rather than a clean `"skipped"`. Edit or clear it before running. See [common issues](../../troubleshooting/common-issues.md).

Triage stays conservative: it defaults a signal to `needs-spec` unless an `agent-ready` label co-occurs with explicit acceptance/verification markers, caps output at 5 new cards per pass (`--max-new`), and dedupes by a content-hashed `TASK-<sha1[:6]>` id so re-runs do not duplicate cards.

## Consequences

- Layer 1 produces draft task cards with no credentials configured; the cards arrive `needs-spec` and require a human or the dispatch skill to promote them.
- The `latest.json` shape is now a contract that both the sync tool and the [signal-triage skill](../../reference/skills-and-subagents.md) depend on; changing it breaks both paths.
- A scheduled sync that reports "success" may still have synced nothing — read the skipped/error summary, not just the exit code.
- See also: [signal layer](../../concepts/signal-layer.md), [set up external signals](../../guides/set-up-external-signals.md), [environment variables](../../reference/environment-variables.md), and [ADR 001](001-local-inbox-before-mcp.md).
