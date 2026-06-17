# Set up external signals

Turn Slack, Linear, GitHub, and Markdown inbound into agent-ready task cards in `AGENT_TASKS.md`. There are two paths: MCP servers (richer, live tools) and a local credential-optional fallback that writes a JSON inbox the triager reads.

> **Goal:** new draft task cards appended to `AGENT_TASKS.md`, each traceable back to the source signal that produced it.

## Path A — MCP servers (richer)

Configure servers named `slack`, `linear`, and `github` in Claude Code. Each is added once at user scope:

```powershell
claude mcp add-json slack '<json>' --scope user
claude mcp add-json linear '<json>' --scope user
claude mcp add-json github '<json>' --scope user
```

The exact JSON per server (command, args, env) is in [MCP_SETUP.md](../../MCP_SETUP.md). Once the servers are connected, the `signal-triage` skill and the `signal-agent` subagent read those MCP tools directly — no local sync step is needed. See [skills & subagents](../reference/skills-and-subagents.md).

## Path B — local fallback (no MCP, credential-optional)

This path needs no MCP servers and runs even with zero credentials configured: each source self-skips when its token is missing. The tools resolve paths from `CLAUDE_PROJECT_DIR`, falling back to the current directory — so run these commands from the repo root unless that variable is set.

### 1. Create your `.env`

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

Then fill the tokens you have. Every variable name is listed in [environment variables](../reference/environment-variables.md). The relevant ones:

| Variable | Used by | Notes |
| --- | --- | --- |
| `SLACK_BOT_TOKEN` | Slack | Bot token with channel-history scope for the configured channels. |
| `SLACK_CHANNEL_IDS` | Slack | Comma- or semicolon-separated channel IDs. |
| `SLACK_USER_MENTION` | Slack | Optional substring filter — only messages containing it are kept. |
| `LINEAR_API_KEY` | Linear | API key with read access. |
| `LINEAR_TEAM_KEY` | Linear | Optional team filter. |
| `LINEAR_LABEL` | Linear | Defaults to `agent-ready`. |
| `GITHUB_TOKEN` | GitHub | Optional. Unauthenticated requests are capped at 60/hr. |
| `GITHUB_REPOSITORY` | GitHub | `owner/repo`. |
| `GITHUB_LABEL` | GitHub | Defaults to `agent-ready`. |

Real shell environment variables override `.env`. The loader uses `setdefault`, so anything already exported in your shell wins over the file.

### 2. Sync signals into the local inbox

```powershell
python .claude/tools/sync_external_signals.py --all
```

Use individual flags to limit sources (`--github`, `--linear`, `--slack`), and `--since-hours 24` to set the Slack lookback window (default 24). The tool writes `.agent-harness/signals/latest.json`, shaped:

```json
{ "synced_at": "<UTC ISO8601>", "signals": [ ... ] }
```

It always exits 0. Each source self-skips when its credentials are missing, recording a `status: "skipped"` entry inside the signals array rather than failing. The command prints a `Skipped/errors:` block listing every source that skipped or errored — read it, because a misconfiguration looks like success (see [Gotchas](#gotchas)).

### 3. Triage signals into task cards

```powershell
python .claude/tools/signal_triage.py --apply
```

This reads `latest.json` and appends conservative draft cards to `AGENT_TASKS.md`. Options:

| Flag | Default | Effect |
| --- | --- | --- |
| `--apply` | off | Append cards to the tasks file. Without it, cards print to stdout. |
| `--max-new` | 5 | Maximum number of new cards per run. |
| `--signals PATH` | `.agent-harness/signals/latest.json` | Read signals from a different file. |
| `--tasks PATH` | `AGENT_TASKS.md` | Append to a different tasks file. |

Behavior:

- Exits 1 only if the signals file is missing; otherwise exits 0 (including "No new task cards.").
- Dedups by a content-hashed `TASK-<6 hex>` id, checked as a substring of the tasks file — a card whose id already appears is skipped.
- Cards default to status `needs-spec`, with `[fill]` placeholders for goal, acceptance, and verification that you complete by hand. (The classifier can also emit `agent-ready` when an `agent-ready`-labeled source already carries acceptance/verification markers, or `signal` for low-signal inbound; `needs-spec` is the common case.)

See [task file format](../reference/task-file-format.md) for the card grammar, and promote a card to `agent-ready` only after you fill in its acceptance and verification.

## Gotchas

- **The GitHub placeholder makes a real API call.** `.env.example` ships `GITHUB_REPOSITORY=owner/repo` — a non-empty placeholder. If you copy it verbatim, GitHub sync does **not** skip; it calls `https://api.github.com/repos/owner/repo/issues` and records a 404 `error` (not a `skipped`) entry. Replace it with your real `owner/repo`, or blank it to make the source skip cleanly.
- **Paths follow your working directory.** The tools anchor to the current directory. Run them from the repo root or `latest.json` and the cards land in the wrong place.
- **Shell env overrides `.env`.** The loader uses `setdefault`, so an exported variable always beats the file value. Unset stale exports if the file value is the one you mean.
- **Failures hide inside the JSON, not in the exit code.** Missing credentials and network errors are recorded inside `latest.json` and the sync still exits 0 — a broken setup looks like a successful run. Always read the `Skipped/errors:` output.

## Related

- [signal layer](../concepts/signal-layer.md#external-signal-sync)
- [environment variables](../reference/environment-variables.md)
- [task file format](../reference/task-file-format.md)
- [skills & subagents](../reference/skills-and-subagents.md)
- [tools](../reference/tools.md)
