# Verification gates

Verification is what makes "walk away while agents work" safe: a change is not done until it passes three escalating gates, two of which fire automatically.

## Why it exists as its own layer

Speed requires safety. An agent that can loop infinitely will happily declare victory on broken code unless something independent checks it. The gates are that independent check, layered from cheapest to most judgment-heavy so that fast feedback catches most problems and a human-grade review catches the rest.

## The three gates

| Gate | Level | What runs | Automated? |
|------|-------|-----------|------------|
| 1 | Code | lint, build, unit tests, Python compile check (`verify.py`) | Yes — after every edit, and blocking on completion |
| 2 | Behavior | run the app; CLI output or browser click-through | Partly — via the `browser-tester` subagent |
| 3 | Judgment | critic subagent reviews the diff vs. acceptance criteria and risk | On request — the `critic` subagent |

### Gate 1 — code-level, via `verify.py`

`verify.py` is project-aware. It auto-detects what to run:

- A **Python compile check** on up to 250 `.py` files (skipping `.venv`, `node_modules`, `.git`).
- **npm scripts** if `package.json` defines them: `lint`, `typecheck`, `test`, and `build` (build only in `--full`).
- **`ruff check .`** if `ruff` is on PATH.
- **`pytest -q`** if a `tests/` directory or `test_*.py` files exist.

Run it directly:

```powershell
python .claude/tools/verify.py --fast   # lightweight checks, 180s/cmd
python .claude/tools/verify.py --full    # adds build, 300s/cmd
```

Every run appends a JSON record to `.agent-harness/verify-log.jsonl` and exits `0` if all checks passed, `1` otherwise. If it detects no known commands, it records a friendly "nothing to verify — customize me" result and passes. You are expected to extend `verify.py` for any serious repo. Full field reference: [tools](../reference/tools.md#verifypy).

### Gate 2 — behavior-level

Code that compiles can still be wrong. Gate 2 demonstrates the behavior in the running system. Preferred routes, in order:

- Claude Code `/run` and `/verify`.
- The **`browser-tester` subagent**, which launches the app, navigates the relevant path, exercises the exact acceptance criteria via Playwright MCP, and reports failures with URL + steps + observed result.
- A CLI example showing before/after output.

If your app needs a custom launch recipe, generate one first (`/run-skill-generator`) so `/run` and `/verify` know how to start it.

### Gate 2 browser evidence

v2 adds a deterministic Gate 2 path that leaves **artifacts on disk**, so behavior verification is reviewable after the fact rather than living only in a subagent's transcript. `browser_verify.py` (Playwright) drives real targets and writes `.agent-harness/browser-evidence/<timestamp>/` containing a screenshot per target, a `console.log`, and a `report.md`. `verify.py` runs it when you pass `--browser` or in full mode, and the [`browser-verification`](../reference/skills-and-subagents.md#browser-verification) skill makes it a completion requirement for UI/auth/routing work. Setup and config keys: [verify in the browser](../guides/verify-in-the-browser.md).

> **SKIP is not PASS.** `browser_verify.py` exits `0` and still writes a `report.md` when there's no config file or Playwright isn't installed (a SKIP). A SKIP means "not verified," not "passed" — don't treat exit 0 alone as proof. This matters because the strict gate below checks only that `report.md` exists.

### Gate 3 — judgment-level, via the `critic`

The `critic` subagent is **read-only** — it has no Edit or Write tools and runs in plan permission mode. It reviews the completed work against acceptance criteria, the actual diff, verification logs, security and data-loss risk, regression risk, overengineering, missing negative tests, and unclear rollback. It returns a verdict:

```markdown
# Critic Report

## Verdict
PASS / REVISE / BLOCK

## Acceptance criteria mapping
## Verification evidence
## Risks
## Required fixes before merge
## Optional improvements
```

Because it cannot edit, its verdict is advice — you (or the implementing agent) act on it.

## How the gates are wired to hooks

Two gates run without you asking, through hooks registered in `.claude/settings.json`:

| Hook event | Trigger | Action |
|------------|---------|--------|
| `PostToolUse` (Write/Edit/MultiEdit) | After any edit | Run `verify.py --fast` in the background (async), non-blocking |
| `TaskCompleted` (1st) | Agent marks task done | Run `verify.py --fast`; **exit 2 blocks completion** if it fails |
| `TaskCompleted` (2nd) | Agent marks task done | Run `require_evidence.py` (the strict gate below); **exit 2 blocks** when enabled and evidence is missing |

The blocking behavior is the teeth: an agent literally cannot mark a task complete while Gate 1 is red. Full hook reference: [hooks & settings](../reference/hooks-and-settings.md).

## The strict evidence gate (opt-in)

The two automated gates above check that code passes and behavior was demonstrated. v2 adds a third automated check that demands the *artifacts* of judgment-level review exist before completion: `require_evidence.py`, wired as the second `TaskCompleted` hook. It is **off by default at the code level** and blocks (exit 2) only when enabled and the required proof is missing:

| Enabled by | Effect |
|------------|--------|
| `.agent-harness/STRICT_COMPLETION` (sentinel file) | Requires **both** a critic report and browser evidence |
| `AGENT_REQUIRE_CRITIC=1` | Requires a critic report at `.agent-harness/critic-reports/<TID>.md` (or `latest.md`) |
| `AGENT_REQUIRE_BROWSER=1` | Requires browser evidence at `.agent-harness/browser-evidence/*/report.md` |

This is [ADR 006](../architecture/adr/006-opt-in-strict-evidence.md): rigor you escalate deliberately, so ordinary non-UI completions aren't blocked for lacking artifacts.

> **The shipped `.env.example` turns the critic check on.** `.env.example` sets `AGENT_REQUIRE_CRITIC=1` (and `AGENT_REQUIRE_BROWSER=0`). If you copy it to `.env` for the signal/health features, the loader's `setdefault` makes that value live — so completions will **block** until a critic report exists at `.agent-harness/critic-reports/<TID>.md`. The code default with the variable unset is off; the example file is the thing that enables it. Set it to `0` if you don't want the gate. See [common issues](../troubleshooting/common-issues.md#task-completion-is-blocked-by-a-missing-critic-report) and [environment variables](../reference/environment-variables.md).

> **Existence, not PASS.** The browser check is satisfied by any `report.md` — including a SKIP report. Pair it with a real, passing [browser run](../guides/verify-in-the-browser.md), not a SKIP.

## The required final report

The `verify-gates` skill closes every change with a report mapping each acceptance criterion to evidence, listing the verification commands and results, summarizing the critic review, and stating the human decision needed: merge, revise, or abandon. This report is the artifact you actually review — it's how you spend judgment efficiently instead of re-reading the whole diff.

## Interaction with other layers

- **← Execution:** gates run inside the [worktree](worktree-execution.md), against that task's isolated diff.
- **→ Self-improvement:** a failing gate or a missing verification command is exactly the friction the [weekly miner](self-improving-harness.md) looks for.

## Common gotchas

- **`verify.py` reports "No known verification commands detected."** Your repo has no tests, npm scripts, or ruff. That's a *pass*, not a failure — but add real checks or the gate is hollow.
- **Fast and full at once.** `--full` is ignored if `--fast` is also passed (`full = args.full and not args.fast`). Pick one.
- **The critic edited my code.** It can't — by design. If you want edits, ask the implementing agent to apply the critic's required fixes.
- **Playwright not installed.** The `browser-tester` subagent declares an MCP server (`npx @playwright/mcp@latest`); first run will fetch it. Ensure Node/npm are present.
