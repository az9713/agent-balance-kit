# Common issues

The failures you'll actually hit, ordered roughly by how often they bite. Each lists the symptom as you'd describe it, the real cause, and the exact fix.

## Hooks never run (no verification, no journals)

**Cause:** Wrong settings file for your OS. The default `.claude/settings.json` invokes `powershell.exe`; on macOS/Linux that does nothing.

**Fix (macOS/Linux):**

```bash
cp .claude/settings.unix.json .claude/settings.json
chmod +x .claude/hooks/*.sh .claude/tools/*.py
```

**If that doesn't work:** confirm hooks are enabled in your Claude Code version and that the session restarted after the settings change. See [hooks & settings](../reference/hooks-and-settings.md#choosing-the-right-settings-file).

## "Task TASK-001 not found or not marked agent-ready"

**Cause:** The first line of the task doesn't match the parser. Most often the state isn't `agent-ready`, the box is checked, or `branch:`/`title:` are out of order.

**Fix:** Make the first line exactly:

```markdown
- [ ] TASK-001 | agent-ready | branch: agent/task-001 | title: Your title here
```

Check: literal `- [ ] ` (one space in the box), state is `agent-ready`, `branch:` comes before `title:`, the ID's case matches `--task`. Full grammar: [task file format](../reference/task-file-format.md).

## "AGENT_TASKS.md not found. Copy AGENT_TASKS.example.md first."

**Cause:** The launcher reads `AGENT_TASKS.md`, but only the `.example.md` exists.

**Fix:**

```powershell
Copy-Item AGENT_TASKS.example.md AGENT_TASKS.md
```

## `verify.py` reports "No known verification commands detected"

**Cause:** The repo has no tests, no `package.json` scripts, and no `ruff`. This is recorded as a **passing** result — the gate is simply empty.

**Fix:** Add real checks so the gate has teeth: a `tests/` directory with `test_*.py`, `package.json` scripts (`lint`/`test`/`build`), or install `ruff` (`pip install ruff`). Then extend `.claude/tools/verify.py` for anything project-specific. See [verification gates](../concepts/verification-gates.md).

## SyntaxError when running a kit tool

**Cause:** Python older than 3.10. The tools use `list[str]`, `dict[str, str]`, and `X | Y` union syntax.

**Fix:** Install Python 3.10+ and confirm `python --version`. On macOS/Linux, the hooks call `python3` — make sure that resolves to 3.10+. See [prerequisites](../getting-started/prerequisites.md).

## `--full` didn't run the build

**Cause:** You passed both `--fast` and `--full`. The script computes `full = args.full and not args.fast`, so `--fast` wins.

**Fix:** Run `verify.py --full` alone.

## "Worktree already exists"

**Cause:** A worktree for that task is still on disk from a previous run.

**Fix:** Reuse it, or remove and recreate:

```powershell
git worktree remove .worktrees/TASK-001
python .claude/tools/agent_ready_loop.py --task TASK-001
```

## Remote control won't connect

**Cause:** Claude Code older than v2.1.51, or the desk session stopped.

**Fix:** Check `claude --version` against the v2.1.51 minimum. Confirm the local session is still running — remote control steers a live local process; if the terminal closed, the session is gone. Outside server mode, only one remote session per process. See [worktree execution](../concepts/worktree-execution.md#remote-control).

## `browser-tester` can't start a browser

**Cause:** The Playwright MCP server (`npx -y @playwright/mcp@latest`) needs Node/npm, and the first run downloads it.

**Fix:** Install Node 18+ and npm, then retry; allow the first run time to fetch the package. See [skills & subagents](../reference/skills-and-subagents.md#browser-tester).

## Session summaries directory is empty

**Cause:** The `Stop` hook never ran — usually the wrong settings file (see the first issue), or the session crashed instead of stopping cleanly.

**Fix:** Confirm the Stop hook is in the active settings file, then complete a normal session. The journaler always exits 0, so a present-but-empty file means it ran with no friction to record, while a *missing* file means it never ran. See [self-improving harness](../concepts/self-improving-harness.md#common-gotchas).

## Journal entries all say "## Session unknown" with empty friction

**Cause:** A Windows-only bug, **fixed in v2.** PowerShell prepends a UTF-8 BOM when piping a string into a native process, and the old `session_journal.py` called `json.loads` on it without stripping the BOM — so parsing failed and every entry degraded to an empty `unknown` record. It still exited 0, so the failure was silent.

**Fix:** v2 decodes stdin with `utf-8-sig`, which strips the BOM. If you still see `unknown` entries, you're running an unpatched tool — confirm `session_journal.py` reads `sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")`.

## Task completion is blocked by a missing critic report

**Cause:** The opt-in [strict evidence gate](../concepts/verification-gates.md#the-strict-evidence-gate-opt-in) is enabled and the required artifact is missing, so `require_evidence.py` exits 2. The most common trigger is **copying `.env.example` to `.env`** — it ships `AGENT_REQUIRE_CRITIC=1`, which the loader makes live. The sentinel file `.agent-harness/STRICT_COMPLETION` does the same for both checks.

**Fix:** either produce the evidence — a critic report at `.agent-harness/critic-reports/<TASK-ID>.md` (or `latest.md`), and/or browser evidence at `.agent-harness/browser-evidence/*/report.md` — or turn the gate off: set `AGENT_REQUIRE_CRITIC=0` / `AGENT_REQUIRE_BROWSER=0` in `.env` and remove any `STRICT_COMPLETION` file. See [environment variables](../reference/environment-variables.md) and [ADR 006](../architecture/adr/006-opt-in-strict-evidence.md).

## A tool wrote to the wrong place, or found no tasks

**Cause:** Every kit tool resolves the repo root from `CLAUDE_PROJECT_DIR`, falling back to the current working directory when that variable is unset. Claude Code sets it for hooks and sessions, so this is correct there. It only bites when you run a tool **by hand** from a subdirectory *without* `CLAUDE_PROJECT_DIR` set — then the fallback points at the subdirectory and `.agent-harness/` / `AGENT_TASKS.md` are read/written in the wrong place.

**Fix:** run manual invocations from the repo root, or set `CLAUDE_PROJECT_DIR` first (`$env:CLAUDE_PROJECT_DIR = (Get-Location).Path`). See the working-directory note in [tools](../reference/tools.md).

## GitHub signal sync returns an error instead of skipping

**Cause:** `.env.example` ships `GITHUB_REPOSITORY=owner/repo` — a non-empty placeholder. Copied verbatim, the GitHub source does not self-skip; it makes a real API call to `.../repos/owner/repo/issues` and records a 404 error in `latest.json`.

**Fix:** set `GITHUB_REPOSITORY` to your real `owner/repo` in `.env`, or blank it to skip GitHub. See [set up external signals](../guides/set-up-external-signals.md).

## Browser verification "passed" but nothing was checked

**Cause:** `browser_verify.py` returns exit 0 for a **SKIP** — no config file at `.agent-harness/browser_targets.json`, or Playwright not installed. It even writes a `report.md` saying SKIP, which then satisfies the strict gate's existence-only browser check.

**Fix:** install Playwright (`python -m pip install playwright`, `python -m playwright install chromium`) and create `browser_targets.json` from the shipped `browser_targets.example.json`. Treat a SKIP as "not verified." See [verify in the browser](../guides/verify-in-the-browser.md).

## The night shift isn't dispatching anything

**Cause:** Usually one of: the only task is the shipped `needs-spec` starter (nothing is `agent-ready`); the health policy's `night_shift` is `off` or its `max_implementation_agents` is 0; you ran the poller from a subdirectory; or, on Windows, the scheduled task can't find `pwsh.exe`.

**Fix:** promote a task to `agent-ready`; check `.agent-harness/health_state/latest_policy.json` (regenerate with `health_state.py`); run from the repo root; and on Windows install PowerShell 7. See [run the night shift](../guides/run-the-night-shift.md) and [scope and health](../concepts/scope-and-health.md).

## `require-evidence.ps1` builds a bad path when `CLAUDE_PROJECT_DIR` is unset

**Status:** fixed in v2. Both `require-evidence.ps1` and `require-evidence.sh` now fall back to the current directory (`Get-Location` / `$(pwd)`) when `CLAUDE_PROJECT_DIR` is unset, so running the hook by hand from the repo root works. If you see a path like `/.claude/tools/require_evidence.py`, you're on an unpatched `.ps1` — confirm it sets `$root = $env:CLAUDE_PROJECT_DIR; if (-not $root) { $root = (Get-Location).Path }`. See [hooks & settings](../reference/hooks-and-settings.md#taskcompleted--require-evidence-opt-in).

## A dangerous command was allowed on macOS/Linux but blocked on Windows (or vice versa)

**Cause:** The danger-pattern lists in `block-danger.ps1` and `block-danger.sh` have diverged. The PowerShell version blocks several Windows-specific patterns (`format`, `del /s /q`, `rd /s /q`, `Remove-Item -Recurse -Force $HOME`) that the Bash version does not.

**Fix:** Treat `block-danger` as a coarse seatbelt, not a security boundary, and keep destructive operations human-approved. To harden, edit both scripts so their pattern lists match. See [ADR 004](../architecture/adr/004-windows-first-dual-shell-hooks.md) and [hooks & settings](../reference/hooks-and-settings.md#pretooluse--block-danger).

## PowerShell won't run the hook scripts

**Cause:** Execution policy blocking scripts.

**Fix:** The registered hooks already pass `-ExecutionPolicy Bypass`, so this should not occur for hook invocations. If you run a `.ps1` directly and it's blocked, invoke it the same way the hook does:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\.claude\hooks\verify-lite.ps1
```

Windows PowerShell 5.1 runs the core hooks; only the [night-shift scheduler](../guides/run-the-night-shift.md) needs PowerShell 7. See [prerequisites](../getting-started/prerequisites.md#a-shell).

## The weekly miner produced no skill / an empty prompt

**Cause:** No session summaries exist yet, so there's nothing to mine.

**Fix:** Run several gated sessions first (so the Stop hook journals them), then re-run `python .claude/tools/weekly_skill_miner.py`. See [run the weekly retrospective](../guides/run-the-weekly-retrospective.md).
