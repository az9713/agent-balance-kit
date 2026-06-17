# Reference: tools

The Python tools under `.claude/tools/`. All target Python 3.10+. None call an AI model — every one is deterministic.

> **Working directory.** Every tool resolves the repo root from `CLAUDE_PROJECT_DIR`, falling back to the current working directory when that variable is unset (`Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()`). Claude Code sets `CLAUDE_PROJECT_DIR` for hooks and sessions, so paths resolve correctly there. When you run a tool **by hand** without that variable set, run it from the repo root so the fallback points at the right place. See [common issues](../troubleshooting/common-issues.md#a-tool-wrote-to-the-wrong-place-or-found-no-tasks).

| Tool | Layer | Purpose |
|------|-------|---------|
| `sync_external_signals.py` | 1 Signal | Pull Slack/Linear/GitHub into `signals/latest.json` |
| `signal_triage.py` | 1 Signal | Turn `latest.json` into draft task cards |
| `agent_ready_loop.py` | 3 Execution | Create a worktree + prompt from a task |
| `poll_agent_ready.py` | 3 Execution | Recurring queue-only dispatch poller |
| `night_shift.py` | 3 Execution | One conservative night-shift cycle |
| `verify.py` | 3 Execution | Project-aware verification |
| `browser_verify.py` | 3 Execution | Playwright browser evidence |
| `require_evidence.py` | 3 Execution | Strict completion-evidence gate |
| `session_journal.py` | 4 Self-improvement | Journal a session (Stop hook) |
| `weekly_skill_miner.py` | 4 Self-improvement | Generate the weekly mining prompt |
| `generate_skill.py` | 4 Self-improvement | Scaffold a draft skill from friction |
| `health_state.py` | Scope | Build an agent-load policy from health input |

---

## sync_external_signals.py

Best-effort, credential-optional sync of Slack/Linear/GitHub items into a normalized `.agent-harness/signals/latest.json`. It never dispatches agents or edits code. See [set up external signals](../guides/set-up-external-signals.md).

**Usage:**

```bash
python .claude/tools/sync_external_signals.py --all
python .claude/tools/sync_external_signals.py --github --linear --slack --since-hours 24
```

**Arguments:**

| Flag | Default | Description |
|------|---------|-------------|
| `--github` / `--linear` / `--slack` | — | Sync that source. If none are given, all three run. |
| `--all` | — | Run all three sources. |
| `--since-hours` | `24` | Slack lookback window in hours. |

**Inputs:** loads `.env` from the working directory, then reads per-source env vars — see [environment variables](environment-variables.md). Each source self-skips (records `status: "skipped"`) when its token is absent.

**Output:** writes `.agent-harness/signals/latest.json` shaped `{"synced_at": <UTC ISO8601>, "signals": [...]}`. Prints `Wrote <path> with N items`, then a `Skipped/errors:` list for any source that skipped or failed.

**Exit code:** always `0` — missing credentials and network errors are recorded *inside* `latest.json`, not surfaced as a non-zero exit. A misconfiguration can look like success; read the skipped/errors output. See [ADR 005](../architecture/adr/005-non-mcp-signal-fallback.md).

**Gotcha:** `.env.example` ships `GITHUB_REPOSITORY=owner/repo` — a non-empty placeholder. Copied verbatim, GitHub sync does *not* skip; it makes a real (failing) API call. Replace it with your `owner/repo`.

---

## signal_triage.py

Convert normalized signals into conservative draft task cards appended to `AGENT_TASKS.md`. Defaults to `needs-spec` so nothing is auto-marked ready.

**Usage:**

```bash
python .claude/tools/signal_triage.py            # print cards to stdout
python .claude/tools/signal_triage.py --apply    # append to AGENT_TASKS.md
```

**Arguments:**

| Flag | Default | Description |
|------|---------|-------------|
| `--signals` | `.agent-harness/signals/latest.json` | Input signals file. |
| `--tasks` | `AGENT_TASKS.md` | Tasks file to read/append. |
| `--apply` | off | Append cards. Without it, cards print to stdout only. |
| `--max-new` | `5` | Cap on new cards appended per run. |

**Behavior:** each card gets a content-hashed ID (`TASK-` + 6 hex chars of `SHA1(source:id:title)`). Dedup is a substring check of that ID against the existing tasks file. Cards carry `[fill]` placeholders for `goal`, `acceptance`, and `verification`.

**Exit codes:** `1` if the signals file is missing; `0` otherwise (including "no new cards").

**Divergence to know:** the `signal-triage` skill describes four classes (`ignore`, `needs-human`, `needs-spec`, `agent-ready`); the tool emits `agent-ready`, `needs-spec`, or `signal` — it never emits `ignore`/`needs-human`. The tool is the deterministic subset; the skill is the richer Claude-driven path. See [skills & subagents](skills-and-subagents.md#signal-triage).

---

## agent_ready_loop.py

Create an isolated git worktree and a prompt file from an `agent-ready` task in `AGENT_TASKS.md`.

**Usage:**

```bash
python .claude/tools/agent_ready_loop.py --task TASK-001 [--open-code]
```

**Arguments:**

| Flag | Required | Description |
|------|----------|-------------|
| `--task` | Yes | Task ID to dispatch (e.g. `TASK-001`). Must exist in `AGENT_TASKS.md` and be `agent-ready`. |
| `--open-code` | No | After creating the worktree, open it in VS Code (`code <path>`). |

**Behavior:**

1. Resolves repo root from `CLAUDE_PROJECT_DIR`, else the current directory — run it from your repo root if that variable isn't set.
2. Reads `AGENT_TASKS.md`. Exits with an error if the file is missing or the task isn't found / not `agent-ready`.
3. Creates `.worktrees/<TASK>/` via `git worktree add -b <branch> <path>` (skipped if it already exists).
4. Writes `.worktrees/<TASK>/.agent-harness/<TASK>-prompt.md` with the task contract and instructions.
5. Prints the `cd` + `claude` commands and the paste-in line.

**Exit codes:** `0` on success; raises `SystemExit` with a message if the tasks file or task is missing.

**Parsing:** only the first line of the task is parsed (ID, `agent-ready`, `branch`, `title`). See [task file format](task-file-format.md).

---

## poll_agent_ready.py

Recurring poller that turns `agent-ready` tasks into worktree dispatches and a review-queue entry. The default is safe and **queue-only** — it records work for you to launch, it does not merge or deploy. Drives the [night shift](../guides/run-the-night-shift.md).

**Usage:**

```bash
python .claude/tools/poll_agent_ready.py --once
python .claude/tools/poll_agent_ready.py --loop --every-minutes 15
```

**Arguments:**

| Flag | Default | Description |
|------|---------|-------------|
| `--once` | — | Run a single pass. |
| `--loop` | — | Loop forever, sleeping `--every-minutes` between passes. |
| `--every-minutes` | `15` | Loop interval. |
| `--max-tasks` | none | Cap tasks dispatched this pass (clamped to the health policy — see below). |
| `--execute` | — | Reserved no-op; the poller stays queue-only and prints the manual launch command. |

**Inputs:** `.agent-harness/health_state/latest_policy.json` (if present), `AGENT_TASKS.md`, and the `AGENT_MAX_CONCURRENT` env var (default `1`) as the policy fallback. Checks `.agent-harness/dispatches/<TASK-ID>.json` to avoid re-dispatching.

**Outputs:** writes `.agent-harness/dispatches/<TASK-ID>.json` (task, command, returncode, stdout/stderr) and appends `.agent-harness/review-queue.md`.

**Throttling:** if the policy's `night_shift` is `off`, it prints a notice and stops. `--max-tasks` is clamped to the policy's `max_implementation_agents` — a poor health policy can throttle to zero. See [scope and health](../concepts/scope-and-health.md).

**Eligibility:** a task is dispatched only if its status is exactly `agent-ready`, it matches the strict one-line grammar, and no dispatch record exists. The shipped starter `TASK-001` is `needs-spec`, so nothing dispatches until you promote it.

**Exit code:** always `0`. Per-task failures print stderr but do not change the exit code.

---

## night_shift.py

One conservative night-shift cycle: health policy → optional signal sync + triage → queue-only poll. It does not auto-merge or deploy.

**Usage:**

```bash
python .claude/tools/night_shift.py --sync --max-tasks 1
```

**Arguments:**

| Flag | Description |
|------|-------------|
| `--sync` | Run `sync_external_signals.py --all` then `signal_triage.py --apply` first. |
| `--oura` | Pass `--oura` to `health_state.py`. |
| `--max-tasks N` | Forward a task cap to the poller. |

**Behavior:** always runs `health_state.py`, then (with `--sync`) sync + triage, then `poll_agent_ready.py --once`. It resolves the child tools under `CLAUDE_PROJECT_DIR` (else the current directory) and runs them there, so it works from any directory once that variable is set. Note it does **not** abort if a step fails. Returns the poller's exit code. See [run the night shift](../guides/run-the-night-shift.md).

---

## verify.py

Project-aware verification runner. Auto-detects checks, runs them, logs results as JSONL.

**Usage:**

```bash
python .claude/tools/verify.py --fast      # lightweight checks
python .claude/tools/verify.py --full      # adds build commands
python .claude/tools/verify.py --browser   # also run browser verification
```

**Arguments:**

| Flag | Description |
|------|-------------|
| `--fast` | Lightweight checks. Per-command timeout 180s. |
| `--full` | Adds `npm run build` when present. Per-command timeout 300s. Ignored if `--fast` is also passed (`full = args.full and not args.fast`). |
| `--browser` | Run `browser_verify.py` if `.agent-harness/browser_targets.json` exists. Also runs automatically in full mode. |

**Detected checks:**

| Check | Condition |
|-------|-----------|
| Python compile check | Any `.py` files exist (scans up to 250, skipping `.venv`, `node_modules`, `.git`; reports last 50 errors) |
| `npm run lint` / `typecheck` / `test` | Named script exists in `package.json` |
| `npm run build` | `build` script exists **and** full mode |
| `ruff check .` | `ruff` on PATH, and the repo looks like Python |
| `pytest -q` | `tests/` dir or `test_*.py` files exist |
| Browser verification | `--browser` or full mode, **and** `.agent-harness/browser_targets.json` exists |

> **Note:** On Windows, npm is invoked as `npm.cmd`.

**Output:** appends one JSON record per run to `.agent-harness/verify-log.jsonl` and prints it indented. Record fields: `ts`, `root`, `mode` (`fast`/`full`), `ok`, `results[]` (each `cmd`, `ok`, `returncode`, `seconds`, `stdout_tail`, `stderr_tail`, last 4000 chars each).

**Exit codes:** `0` if `ok`, else `1`. A missing command yields `returncode` 127; a timeout yields `124`.

**No checks detected:** records a single passing result advising you to add tests / `package.json` scripts / `pyproject.toml`. Customize `verify.py` for any serious repo.

**Environment:** repo root from `CLAUDE_PROJECT_DIR`, else `os.getcwd()` — the same resolution every kit tool uses.

---

## browser_verify.py

Playwright browser smoke verification that produces evidence artifacts (screenshots, console log, `report.md`). See [verify in the browser](../guides/verify-in-the-browser.md).

**Usage:**

```bash
python .claude/tools/browser_verify.py --config .agent-harness/browser_targets.json
python .claude/tools/browser_verify.py --no-headless   # watch it run
```

**Arguments:**

| Flag | Default | Description |
|------|---------|-------------|
| `--config` | `.agent-harness/browser_targets.json` | Targets config. |
| `--headless` / `--no-headless` | headless | Run Chromium headless or visible. |

**Config keys:** `start_command`, `startup_wait_seconds` (5), `base_url`, `targets[]` each `name`, `url`|`path`, `timeout_ms` (30000), `fill[]` (`selector`,`value`), `click[]`, `assert_text`, `assert_timeout_ms` (10000), `assert_url_contains`, `screenshot` (true).

**Output:** `.agent-harness/browser-evidence/<YYYYMMDD-HHMMSS>/` with `<name>.png` (or `<name>-failure.png`), `console.log`, and `report.md`.

**Exit codes:** `0` = all targets passed **or** a SKIP (no config file, or Playwright not installed); `1` = one or more target failures.

**Dependency:** Playwright + Chromium (`python -m pip install playwright`, `python -m playwright install chromium`).

**Gotcha:** a SKIP returns `0` and still writes a `report.md`. The strict gate ([require_evidence.py](#require_evidencepy)) only checks that `report.md` *exists*, not that it says PASS — so a SKIP satisfies the gate. Treat SKIP as "not verified."

---

## require_evidence.py

Strict completion gate: blocks task completion (exit `2`) unless required critic and/or browser evidence artifacts exist. **Off by default** — opt-in only. See [ADR 006](../architecture/adr/006-opt-in-strict-evidence.md).

**Usage:** invoked by the `require-evidence` TaskCompleted hook; can be run by hand:

```bash
python .claude/tools/require_evidence.py
```

**Activation (exact):**

- The sentinel file `.agent-harness/STRICT_COMPLETION` enables **both** the critic and browser checks.
- Otherwise, env vars `AGENT_REQUIRE_CRITIC` and `AGENT_REQUIRE_BROWSER` enable each check individually when set to `1`/`true`/`yes`/`on`.
- With none present, the gate is a no-op and exits `0`.

**Checks:**

| Check | Passes when |
|-------|-------------|
| Critic | `.agent-harness/critic-reports/<TID>.md` or `.../latest.md` exists |
| Browser | newest `.agent-harness/browser-evidence/*/report.md` exists (existence only — not PASS) |

The task ID `<TID>` comes from `AGENT_TASK_ID`, else the current git branch, else the path; it is upper-cased (so `TASK-001.md`).

**Exit codes:** `2` = block (missing evidence); `0` = passed or disabled (prints a JSON `systemMessage`).

**Gotchas:** the `STRICT_COMPLETION` sentinel can't select only one check (use the env vars for that); a SKIP browser report satisfies the browser check (existence, not PASS). See [common issues](../troubleshooting/common-issues.md).

---

## session_journal.py

Stop-hook journaler. Reads Claude Code hook JSON from **stdin** and appends a session summary. Deterministic — no model call.

**Usage:** invoked by the `Stop` hook; not run by hand. Equivalent manual call:

```bash
echo '{"session_id":"x","cwd":"."}' | python .claude/tools/session_journal.py
```

**Input (stdin JSON):** reads `transcript_path`, `last_assistant_message`, `session_id`, `cwd`. Stdin is decoded with `utf-8-sig`, so a leading UTF-8 BOM is stripped before parsing — this is what makes the journaler reliable on Windows, where PowerShell prepends a BOM when piping to a native process. Malformed JSON is tolerated (records a `parse_error`).

**Behavior:** reads the last 200 lines of the transcript, counts friction-signal regexes, and appends a block to `.agent-harness/session-summaries/<YYYY-MM-DD>.md`.

**Friction signals counted:** `error`, `failed`, `failing`, `timeout`, `ambiguous`, `permission`, `blocked`, `retry`, `can't`, `cannot`, `not found`, `hallucinat`, `unclear` (all case-insensitive, word-bounded where shown).

**Exit code:** always `0` (a journaler must never block session stop).

**Environment:** repo root from `CLAUDE_PROJECT_DIR`, else `os.getcwd()`.

---

## weekly_skill_miner.py

Generate a weekly prompt that asks Claude to mine session summaries and mint one skill. No model call — it writes a prompt file you paste into Claude Code.

**Usage:**

```bash
python .claude/tools/weekly_skill_miner.py
```

**Behavior:**

1. Reads the **last 14** files in `.agent-harness/session-summaries/` (last 8000 chars of each).
2. Writes `.agent-harness/weekly/<ISO-year>-W<ISO-week>-skill-mining-prompt.md`.
3. Prints the output path.

**Output prompt asks Claude to:** rank the top 5 frictions; name the single highest-leverage skill; create/update exactly one `.claude/skills/<name>/SKILL.md`; not edit production code; include a test invocation; and state what not to automate yet.

**Exit code:** `0`. **Environment:** repo root from `CLAUDE_PROJECT_DIR`, else `os.getcwd()`.

---

## generate_skill.py

Scaffold a draft `SKILL.md` deterministically by scanning friction-keyword lines from session/weekly notes. The deterministic counterpart to the [auto-skill-generation](skills-and-subagents.md#auto-skill-generation) skill.

**Usage:**

```bash
python .claude/tools/generate_skill.py                       # draft only
python .claude/tools/generate_skill.py --name my-skill --install
```

**Arguments:**

| Flag | Default | Description |
|------|---------|-------------|
| `--name` | inferred | Skill name; if omitted, inferred from the friction keywords. |
| `--source` | `session-summaries/` + `weekly/` | Repeatable file or dir to scan (last 50 `.md` per dir). |
| `--install` | off | Write to `.claude/skills/<slug>/SKILL.md` instead of `.agent-harness/skill-drafts/<slug>/`. |

**Behavior:** keeps lines containing friction keywords (capped at 80), then writes a `SKILL.md` with frontmatter, a friction-evidence section, and fixed Trigger/Procedure/Success/Failure sections.

**Exit code:** `0`.

**Gotcha:** `--install` writes directly into `.claude/skills/` with no existence check — it overwrites a same-named skill, and the result is unreviewed. Prefer the default draft location and review before installing.

---

## health_state.py

Build an agent-load policy from a manual `HEALTH_STATE.md` or the Oura API. It gates engineering workload only — **not medical advice**. See [scope and health](../concepts/scope-and-health.md).

**Usage:**

```bash
python .claude/tools/health_state.py --manual HEALTH_STATE.md
python .claude/tools/health_state.py --oura --print
```

**Arguments:**

| Flag | Default | Description |
|------|---------|-------------|
| `--manual` | `HEALTH_STATE.md` | Manual health-state file to parse. |
| `--oura` | off | Try the Oura API first if `OURA_ACCESS_TOKEN` is set. |
| `--print` | off | Print the full policy JSON. |

**Output:** writes `.agent-harness/health_state/latest_policy.json` plus a timestamped `policy-<YYYYMMDD-HHMMSS>.json`. Always exits `0` and always produces a policy (a built-in default when nothing is configured).

**Policy mapping** (authoritative — the tool emits these `night_shift` strings): see the table in [scope and health](../concepts/scope-and-health.md#the-policy). In short: poor → 1 agent / `off`; normal → 2 / `queue-only`; excellent → 3 / `dispatch-allowed`. `max_implementation_agents` in the manual file is a **cap** (it lowers the computed value, never raises it).

See also: [self-improving harness](../concepts/self-improving-harness.md), [verification gates](../concepts/verification-gates.md), [environment variables](environment-variables.md).
