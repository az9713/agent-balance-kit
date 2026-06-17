# What's new in v2

v2 implements the previously-missing "Zack-like" layers, and everything is additive and mostly opt-in, so an un-provisioned v2 behaves like v1. See the root [changelog](../../CHANGELOG_v2.md) for the raw list.

## Addition → layer → where to read

| Addition | Layer / dimension | Where to read |
|----------|-------------------|---------------|
| External signal sync (Slack/Linear/GitHub) | Layer 1 — Signal | [signal layer](../concepts/signal-layer.md#external-signal-sync), [guide](../guides/set-up-external-signals.md) |
| Browser verification with evidence | Layer 3 — Execution / Gate 2 | [verification gates](../concepts/verification-gates.md#gate-2-browser-evidence), [guide](../guides/verify-in-the-browser.md) |
| Strict completion-evidence gate (opt-in) | Layer 3 — Execution | [verification gates](../concepts/verification-gates.md#the-strict-evidence-gate-opt-in), [ADR 006](../architecture/adr/006-opt-in-strict-evidence.md) |
| Night shift (autonomous queue-only poller + schedulers) | Layer 3 — Execution | [worktree execution](../concepts/worktree-execution.md#the-night-shift), [guide](../guides/run-the-night-shift.md) |
| Health-based scope control | New cross-cutting dimension | [scope and health](../concepts/scope-and-health.md), [guide](../guides/tune-scope-with-health.md) |
| Automatic draft-skill generation | Layer 4 — Self-improvement | [self-improving harness](../concepts/self-improving-harness.md) |
| New root files (`.env.example`, `HEALTH_STATE.example.md`, `MCP_SETUP.md`, starter `AGENT_TASKS.md`, `.gitignore`) | Setup surface | [environment variables](../reference/environment-variables.md) |

Each addition gates itself off when its inputs are absent: the sync sources self-skip without tokens, the strict gate stays off until you opt in, and the health policy falls back to a built-in default. That is what keeps an un-provisioned v2 equivalent to v1.

## Also fixed

- **Stop-hook journaler BOM.** `session_journal.py` now reads stdin with `utf-8-sig`. On Windows PowerShell, piping a string to a native process prepends a UTF-8 BOM, which made `json.loads()` fail; the hook then recorded an empty `"unknown"` session with no friction signals. Stripping the BOM means journals now capture the real session id and the friction signals (`error`, `failed`, `blocked`, `retry`, and so on) that the weekly skill miner reads.
- **Flattened tree.** The v2 layout no longer nests an inner `agent_balance_kit/` folder; root files (`.env.example`, `CHANGELOG_v2.md`, `AGENT_TASKS.md`) and `.claude/tools/...` sit at the repo root.
- **Consistent repo-root resolution.** Every kit tool now resolves the repo root from `CLAUDE_PROJECT_DIR`, falling back to the current working directory when unset — previously most tools anchored to the working directory only, so running them from a subdirectory wrote to the wrong place. `.env` and config files are resolved the same way.
- **`require-evidence.ps1` fallback.** The PowerShell evidence-gate wrapper now falls back to the current directory when `CLAUDE_PROJECT_DIR` is unset, matching its `.sh` sibling, so running the hook by hand no longer builds a broken path.

## Known gotchas to read before relying on a feature

- **GitHub placeholder repo.** `.env.example` ships `GITHUB_REPOSITORY=owner/repo`; copied verbatim it triggers a failing API call instead of a clean skip.
- **`.env` copy enables the critic gate.** `.env.example` ships `AGENT_REQUIRE_CRITIC=1`, so copying it to `.env` turns the strict critic check on even though the code-level default is off.
- **Browser SKIP satisfies the strict gate.** The strict browser check is an existence check; a `report.md` with a `SKIP` verdict still exits `0` and passes the gate.
- **`pwsh` required for the Windows night shift.** The Windows scheduler path expects PowerShell 7 to run the poller.
- **Night-shift terminology divergence.** The health tool emits `off` / `queue-only` / `dispatch-allowed`; `HEALTH_STATE.example.md` describes them as `off` / `conservative` / `allowed`. The tool's strings are authoritative.

Full detail for each: [common issues](../troubleshooting/common-issues.md).
