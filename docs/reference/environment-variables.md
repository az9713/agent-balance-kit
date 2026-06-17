# Environment variables

The v2 local tools read configuration from environment variables, loaded from a `.env` file at the repo root. Copy `.env.example` to `.env` and fill in the values you need:

```powershell
Copy-Item .env.example .env
```

## How loading works

Each env-aware tool calls a small `load_env_file()` loader before reading any variable. The loader:

- Reads `.env` line by line and sets each `KEY=value` with `os.environ.setdefault`. Because it is `setdefault`, a **real shell environment variable wins** — if `KEY` is already set in your shell, the `.env` value is ignored. This lets you override `.env` per-session without editing the file.
- Strips surrounding quotes and ignores blank lines and `#` comments.
- Reads `.env` from the repo root, resolved under `CLAUDE_PROJECT_DIR` and falling back to the current working directory when that variable is unset. Claude Code sets it for hooks and sessions; for manual runs without it, run from the repo root so the loader finds your `.env`.

`.env` is gitignored (so is `HEALTH_STATE.md`), so your secrets stay out of version control.

## Variables

| Variable | Read by | Default | Purpose |
|----------|---------|---------|---------|
| `SLACK_BOT_TOKEN` | `sync_external_signals.py` (Slack) | — | Required for Slack sync. |
| `SLACK_CHANNEL_IDS` | `sync_external_signals.py` (Slack) | — | Comma/semicolon-separated channel IDs; required for Slack. |
| `SLACK_USER_MENTION` | `sync_external_signals.py` (Slack) | — | Optional substring filter on messages. |
| `LINEAR_API_KEY` | `sync_external_signals.py` (Linear) | — | Required for Linear sync. |
| `LINEAR_TEAM_KEY` | `sync_external_signals.py` (Linear) | — | Optional team filter. |
| `LINEAR_LABEL` | `sync_external_signals.py` (Linear) | `agent-ready` | Issue label to pull. |
| `GITHUB_TOKEN` | `sync_external_signals.py` (GitHub) | — | Optional; unauthenticated calls are limited to ~60/hr. |
| `GITHUB_REPOSITORY` | `sync_external_signals.py` (GitHub) | — | Required, form `owner/repo`. The `.env.example` placeholder `owner/repo` triggers a failing API call if left unedited (gotcha). |
| `GITHUB_LABEL` | `sync_external_signals.py` (GitHub) | `agent-ready` | Issue label to pull. |
| `OURA_ACCESS_TOKEN` | `health_state.py` (`--oura`) | — | Required for the Oura health path. |
| `AGENT_MAX_CONCURRENT` | `poll_agent_ready.py` | `1` | Fallback cap on dispatched tasks when no health policy file exists. |
| `AGENT_REQUIRE_CRITIC` | `require_evidence.py` | off | Set `1`/`true`/`yes`/`on` to require a critic report at completion. |
| `AGENT_REQUIRE_BROWSER` | `require_evidence.py` | off | Set `1`/`true`/`yes`/`on` to require browser evidence at completion. |
| `AGENT_TASK_ID` | `require_evidence.py` | — | Overrides the task id (otherwise derived from the git branch or path). |
| `CLAUDE_PROJECT_DIR` | `verify.py` and the hook wrappers (also `session_journal.py`, `weekly_skill_miner.py`) | current dir | Project root for path resolution; normally set by Claude Code. |

> **`.env.example` also lists the harness vars.** `AGENT_MAX_CONCURRENT`, `AGENT_REQUIRE_CRITIC`, and `AGENT_REQUIRE_BROWSER` appear in `.env.example` so you can set them in one place.

## Gotchas

- **Copying `.env.example` enables the critic gate.** `.env.example` ships `AGENT_REQUIRE_CRITIC=1`. The "off" default in the table above is the code-level behavior when the variable is **unset** — but the documented setup copies `.env.example` to `.env`, and `setdefault` makes that `1` live, so the strict critic check turns on. `AGENT_REQUIRE_BROWSER=0` in the same file is consistent with the off default; only the critic line changes behavior. Clear `AGENT_REQUIRE_CRITIC` in your `.env` if you want the v1 default.
- **Replace the `GITHUB_REPOSITORY` placeholder.** The shipped `owner/repo` is a real (non-empty) value, so the sync tool will call the API for a repository named `owner/repo` and record an error instead of cleanly skipping. Edit or clear it.
- **`.env` is read from the repo root.** Tools resolve it under `CLAUDE_PROJECT_DIR`, falling back to the current working directory when that variable is unset. Claude Code sets it for hooks and sessions; for manual runs without it, run from the repo root. See [common issues](../troubleshooting/common-issues.md).

## Cross-links

- [Set up external signals](../guides/set-up-external-signals.md)
- [Tune scope with health](../guides/tune-scope-with-health.md)
- [Hooks & settings](hooks-and-settings.md)
- [Tools](tools.md)
