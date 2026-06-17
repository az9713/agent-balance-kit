# Reference: hooks and settings

The kit registers hooks across four lifecycle events in `.claude/settings.json`. Each is a thin shell script under `.claude/hooks/` that calls a Python tool. `TaskCompleted` runs **two** hooks in order, so there are five hook invocations in total.

## Choosing the right settings file

Two settings files ship. Use exactly one as `.claude/settings.json`:

| File | For | How it calls hooks |
|------|-----|--------------------|
| `settings.json` (default) | Windows | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <hook>.ps1` |
| `settings.unix.json` | macOS/Linux | `<hook>.sh` directly |

On macOS/Linux, overwrite the default: `cp .claude/settings.unix.json .claude/settings.json`. The two are otherwise structurally identical.

## The hooks

| Event | Matcher | Script (Windows / Unix) | Async | Timeout | Can block? |
|-------|---------|--------------------------|-------|---------|-----------|
| `PreToolUse` | `Bash`, `if: Bash(rm *)` | `block-danger.ps1` / `.sh` | No | 10s | Yes (deny) |
| `PostToolUse` | `Write\|Edit\|MultiEdit` | `verify-lite.ps1` / `.sh` | Yes | 300s | No |
| `TaskCompleted` (1st) | (all) | `verify-before-complete.ps1` / `.sh` | No | 300s | Yes (exit 2) |
| `TaskCompleted` (2nd) | (all) | `require-evidence.ps1` / `.sh` | No | 60s | Yes (exit 2), opt-in |
| `Stop` | (all) | `session-journal.ps1` / `.sh` | No | 30s | No |

> Both settings files (`settings.json` and `settings.unix.json`) wire all five hooks identically; only the interpreter and script extension differ.

### PreToolUse → block-danger

Guards against destructive shell commands. Reads the hook JSON from stdin, extracts `tool_input.command`, and if it matches a danger pattern, emits a `permissionDecision: "deny"` with a reason. Always exits `0` (the *decision*, not the exit code, blocks the command).

**Danger patterns differ by platform** — a real gap to know:

| Pattern | Windows (`.ps1`) | Unix (`.sh`) |
|---------|:---:|:---:|
| `rm -rf /` | ✓ | ✓ |
| `rm -rf ~` | ✓ | ✓ |
| `git reset --hard` | ✓ | ✓ |
| `git clean -fdx` | ✓ | ✓ |
| `Remove-Item -Recurse -Force $HOME` | ✓ | ✗ |
| `format ` | ✓ | ✗ |
| `del /s /q` | ✓ | ✗ |
| `rd /s /q` | ✓ | ✗ |

> **Warning:** This is a coarse backstop, not a security boundary — it matches substrings on a short list and only triggers on `Bash` tool calls beginning with `rm` (the `if: Bash(rm *)` matcher). Treat it as a seatbelt, not a vault. Keep destructive operations human-approved regardless.

### PostToolUse → verify-lite

After any `Write`/`Edit`/`MultiEdit`, runs `verify.py --fast` in the background (`async: true`) and discards output. Always exits `0` — it never blocks an edit. This is the fast, ambient Gate 1 feedback loop.

### TaskCompleted → verify-before-complete

When an agent marks a task complete, runs `verify.py --fast`. If verification fails, it writes an error and **exits 2**, which blocks the completion. This is the gate's teeth: a task cannot be "done" while Gate 1 is red.

### TaskCompleted → require-evidence (opt-in)

The second `TaskCompleted` hook runs `require_evidence.py`, a stricter gate that demands evidence *artifacts* before completion. It is **off by default** and does nothing unless you opt in:

- the sentinel file `.agent-harness/STRICT_COMPLETION` turns on **both** the critic and browser checks, or
- the env vars `AGENT_REQUIRE_CRITIC` / `AGENT_REQUIRE_BROWSER` turn on each check individually (`1`/`true`/`yes`/`on`).

When enabled and the required artifact is missing, it **exits 2** to block completion. See [verification gates](../concepts/verification-gates.md#the-strict-evidence-gate-opt-in) and [ADR 006](../architecture/adr/006-opt-in-strict-evidence.md).

> **Both wrappers fall back to the current directory.** `require-evidence.sh` resolves the project as `${CLAUDE_PROJECT_DIR:-$(pwd)}`, and `require-evidence.ps1` does the same in v2 (`$root = $env:CLAUDE_PROJECT_DIR; if (-not $root) { $root = (Get-Location).Path }`). Claude Code sets `CLAUDE_PROJECT_DIR` for real hook runs; the fallback covers running the hook by hand from the repo root.

### Stop → session-journal

When a session ends, pipes the hook's stdin JSON into `session_journal.py`, which appends a journal entry. The tool decodes stdin with `utf-8-sig`, so the UTF-8 BOM that PowerShell prepends when piping to a native process is stripped and the entry captures real fields. Always exits `0`. See [self-improving harness](../concepts/self-improving-harness.md).

## How `${CLAUDE_PROJECT_DIR}` is used

The settings reference hook scripts as `${CLAUDE_PROJECT_DIR}/.claude/hooks/<name>`. Inside each script, the repo root is resolved as `$env:CLAUDE_PROJECT_DIR` (PowerShell) or `${CLAUDE_PROJECT_DIR:-$(pwd)}` (Bash), falling back to the current directory when unset.

## Customizing hooks

- **Loosen/tighten the danger list:** edit the `$danger` array in `block-danger.ps1` and the `case` patterns in `block-danger.sh`. Keep the two in sync.
- **Make PostToolUse blocking:** it's intentionally non-blocking (async, exit 0). Don't make it block — that's what `TaskCompleted` is for.
- **Change verification depth on completion:** `verify-before-complete` runs `--fast` by design (completion should be quick). Run `--full` in CI instead. See [CI in system design](../architecture/system-design.md#continuous-integration).

## Related reference

- The tools these hooks call: [tools](tools.md).
- The verification model: [verification gates](../concepts/verification-gates.md).
