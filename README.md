# Agent Balance Kit v2

A Windows-first, cross-platform scaffold for a Zack Proser-style sustainable agent workflow.

The point is not "more agents." The point is to keep human attention, review quality, and body state from becoming the failure mode.

## What v2 adds

v2 implements the missing external-loop pieces from the first scaffold:

1. **Slack / Linear / GitHub signal agents**
   - MCP-ready `signal-triage` skill and `signal-agent`.
   - Local fallback: `.claude/tools/sync_external_signals.py` pulls Slack/Linear/GitHub using environment variables and writes `.agent-harness/signals/latest.json`.
   - `.claude/tools/signal_triage.py` converts normalized signals into `AGENT_TASKS.md` cards.

2. **Real browser click-through verification**
   - `.claude/tools/browser_verify.py` runs Playwright smoke checks from `.agent-harness/browser_targets.json`.
   - Evidence is written to `.agent-harness/browser-evidence/<timestamp>/report.md` with screenshots.
   - `verify.py --full` automatically runs browser verification when `.agent-harness/browser_targets.json` exists.

3. **Recurring night-shift polling**
   - `.claude/tools/night_shift.py` runs health policy, optional external sync, triage, and conservative queue creation.
   - `.claude/tools/poll_agent_ready.py` polls `AGENT_TASKS.md` for `agent-ready` tasks and creates worktree prompts.
   - Windows Task Scheduler and cron installers are included.

4. **Oura / body-state feedback with fallback**
   - `.claude/tools/health_state.py` creates `.agent-harness/health_state/latest_policy.json`.
   - Supports manual `HEALTH_STATE.md` immediately.
   - Can attempt Oura API reads when `OURA_ACCESS_TOKEN` is present.
   - The policy limits max implementation agents and disables night shift when capacity is degraded.

5. **Automatic skill generation**
   - `.claude/tools/generate_skill.py` mines session summaries / weekly notes and creates a draft `SKILL.md`.
   - `auto-skill-generation` skill tells Claude how to refine and install exactly one reusable skill.

---

## 0. Prerequisites

Required:

- Git
- Python 3.10+
- PowerShell 7+ on Windows, or Bash on macOS/Linux
- Claude Code installed and authenticated

Optional:

- Node/npm for JavaScript projects
- Playwright for browser verification
- Claude mobile app for Remote Control
- Slack / Linear / GitHub / Oura credentials

Check:

```powershell
git --version
python --version
claude --version
```

---

## 1. Install into an existing repo

From the target repo:

```powershell
Expand-Archive .\agent_balance_kit_v2.zip -DestinationPath .\agent_balance_kit_v2
Copy-Item -Recurse -Force .\agent_balance_kit_v2\* .
Copy-Item -Recurse -Force .\agent_balance_kit_v2\.* . -ErrorAction SilentlyContinue
```

On macOS/Linux:

```bash
unzip agent_balance_kit_v2.zip -d agent_balance_kit_v2
cp -R agent_balance_kit_v2/. .
chmod +x .claude/hooks/*.sh scripts/*.sh .claude/tools/*.py
```

Commit the scaffold:

```powershell
git add .claude .agent-harness scripts .github .vscode AGENT_TASKS.md AGENT_TASKS.example.md HEALTH_STATE.example.md MCP_SETUP.md .env.example .gitignore CLAUDE.md README.md ARCHITECTURE.md
git commit -m "Add agent balance harness v2"
```

---

## 2. Minimal safe run

```powershell
python .claude/tools/health_state.py --print
python .claude/tools/verify.py --fast
python .claude/tools/poll_agent_ready.py --once
```

This does not call Slack/Linear/Oura and does not launch autonomous coding. It only verifies the harness and queues worktree prompts if you already have `agent-ready` tasks.

---

## 3. Four-layer loop

### Layer 1 — Signal layer

Configure external credentials in `.env` or use MCP servers as described in `MCP_SETUP.md`.

Local fallback:

```powershell
Copy-Item .env.example .env
# edit .env
python .claude/tools/sync_external_signals.py --github --linear --slack
python .claude/tools/signal_triage.py --apply
```

MCP path inside Claude Code:

```text
Use the signal-triage skill. Read Slack/Linear/GitHub through MCP if available, otherwise read .agent-harness/signals/latest.json. Append only deduplicated task cards to AGENT_TASKS.md.
```

### Layer 2 — Voice-first task contract

Dictate a rough task, then force it through `/agent-ready-task`:

```text
Use /agent-ready-task.

Voice brief:
<raw dictated task>

Convert this into exact goal, non-goals, touched files, acceptance criteria, verification commands, rollback plan, and blocking questions only.
```

### Layer 3 — Worktree execution + verification

Create an isolated task worktree:

```powershell
python .claude/tools/agent_ready_loop.py --task TASK-001
```

Start a task session:

```powershell
.\scripts\start-task-session.ps1 -Task TASK-001
```

Remote Control:

```powershell
.\scripts\start-task-session.ps1 -Task TASK-001 -RemoteControl
```

Verification:

```powershell
python .claude/tools/verify.py --fast
python .claude/tools/verify.py --full
```

Browser verification:

```powershell
Copy-Item .agent-harness/browser_targets.example.json .agent-harness/browser_targets.json
python -m pip install playwright
python -m playwright install chromium
python .claude/tools/browser_verify.py --config .agent-harness/browser_targets.json
```

Strict completion gates are available but opt-in. Enable them with either:

```powershell
New-Item .agent-harness/STRICT_COMPLETION -ItemType File
```

or environment variables:

```powershell
$env:AGENT_REQUIRE_CRITIC="1"
$env:AGENT_REQUIRE_BROWSER="1"
```

When enabled, Claude Code's `TaskCompleted` hook blocks completion unless critic/browser evidence exists.

### Layer 4 — Self-improvement

Weekly prompt generation:

```powershell
python .claude/tools/weekly_skill_miner.py
```

Automatic draft skill generation:

```powershell
python .claude/tools/generate_skill.py
```

Install a generated skill directly:

```powershell
python .claude/tools/generate_skill.py --name spec-clarifier --install
```

Then in Claude Code:

```text
Use the auto-skill-generation skill. Review .agent-harness/skill-drafts/ and install exactly one high-value skill under .claude/skills/.
```

---

## 4. Body-state / Oura layer

Oura is a smart ring / wearable. In this workflow it is just a capacity signal. The agent uses sleep/readiness/activity to reduce workload when the human reviewer is likely degraded.

You do not need Oura. The default substitute is manual:

```powershell
Copy-Item HEALTH_STATE.example.md HEALTH_STATE.md
# edit sleep / energy / stress
python .claude/tools/health_state.py --manual HEALTH_STATE.md --print
```

Oura attempt:

```powershell
$env:OURA_ACCESS_TOKEN="<bearer token>"
python .claude/tools/health_state.py --oura --print
```

Other good substitutes:

- Apple Watch / Apple Health export
- Garmin Body Battery / sleep score
- Fitbit readiness / sleep score
- WHOOP recovery
- manual 30-second self-report

The workflow does not require medical-grade accuracy. It only needs a conservative throttle on agent concurrency.

---

## 5. Night-shift polling

One conservative cycle:

```powershell
python .claude/tools/night_shift.py --sync --max-tasks 1
```

Windows recurring task:

```powershell
.\scripts\install-night-shift-windows.ps1 -IntervalMinutes 15
```

macOS/Linux cron:

```bash
./scripts/install-night-shift-cron.sh
```

Default night shift is **queue-only**. It creates worktree prompts and review queue entries; it does not auto-merge or deploy.

---

## 6. Recommended first deployment pattern

Do not start with four implementation agents.

Start with:

```text
1 signal agent
1 implementation worktree
1 critic pass
1 browser smoke target if UI exists
1 weekly skill miner
```

Only increase concurrency after the review queue becomes boring.
