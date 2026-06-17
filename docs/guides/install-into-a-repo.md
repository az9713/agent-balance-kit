# Install the kit into a repo

Copy the harness into an existing repository and commit it, so the project's agents run with hooks, skills, and subagents active.

> **Goal:** a target repo with a working `.claude/` harness, the correct settings file for your OS, and the scaffold committed.

## Prerequisites

- The kit files (this repo, or its `agent_balance_kit.zip`).
- A target repo that is a git repository (`git status` succeeds).
- Git, Python 3.10+, Claude Code. See [prerequisites](../getting-started/prerequisites.md).

## Steps

### 1. Copy the scaffold

From the kit into your target repo:

```powershell
# Windows PowerShell
$dst = "C:\path\to\your-repo"
Copy-Item -Recurse -Force .\.claude, .\scripts, .\.github, .\.vscode $dst
Copy-Item .\AGENT_TASKS.example.md, .\CLAUDE.md, .\ARCHITECTURE.md $dst
# v2 features (external signals, health-based scope) — copy these too if you'll use them:
Copy-Item .\.env.example, .\HEALTH_STATE.example.md, .\MCP_SETUP.md $dst
```

```bash
# macOS/Linux
dst=/path/to/your-repo
cp -R .claude scripts .github .vscode AGENT_TASKS.example.md CLAUDE.md ARCHITECTURE.md "$dst"
# v2 features — copy these too if you'll use them:
cp .env.example HEALTH_STATE.example.md MCP_SETUP.md "$dst"
```

> The `.claude/` copy already includes the v2 tools, hooks, skills, and subagents. The extra files above are only the v2 *templates* — skip them if you only want the v1 core loop. See [what's new in v2](../overview/whats-new-in-v2.md) for what each enables.

### 2. Make the scripts executable (macOS/Linux only)

```bash
cd /path/to/your-repo
chmod +x .claude/hooks/*.sh scripts/*.sh .claude/tools/*.py
```

### 3. Select the right settings file for your OS

The default `.claude/settings.json` invokes `powershell.exe` — correct on Windows. On macOS/Linux, replace it with the Unix variant, which calls the `.sh` hooks directly:

```bash
cp .claude/settings.unix.json .claude/settings.json
```

See [hooks & settings](../reference/hooks-and-settings.md#choosing-the-right-settings-file) for what differs.

### 4. Ignore the harness's working directories

Add to the target repo's `.gitignore`:

```gitignore
.worktrees/
.agent-harness/
AGENT_TASKS.md
HEALTH_STATE.md
.env
```

`AGENT_TASKS.md` is your personal inbox; keep the committed example, not your live list. Omit it from `.gitignore` if your team wants a shared inbox. `HEALTH_STATE.md` and `.env` hold personal/secret data (v2) — keep them out of git. The kit ships a fuller `.gitignore` you can copy instead, covering the `.agent-harness/` subdirectories individually.

### 5. Commit the scaffold

```powershell
git add .claude scripts .github .vscode AGENT_TASKS.example.md CLAUDE.md ARCHITECTURE.md .gitignore
# add the v2 templates if you copied them:
git add .env.example HEALTH_STATE.example.md MCP_SETUP.md
git commit -m "Add agent balance harness"
```

## Verification

Confirm the tools run and the settings parse:

```powershell
python .claude/tools/verify.py --fast
```

Expected: a JSON record printed to stdout ending with `"ok": true` (or a "No known verification commands detected" result, which also passes). Then start a session and confirm the operating manual loads:

```text
claude
> Read CLAUDE.md and .claude/skills/verify-gates/SKILL.md.
  Summarize the task contract and verification gates before editing.
```

The agent should restate the three gates. If it does, the harness is live.

## Troubleshooting

- **Hooks don't fire on Windows.** PowerShell execution policy may block scripts. The hook commands already pass `-ExecutionPolicy Bypass`; confirm `powershell.exe` is on PATH. Windows PowerShell 5.1 runs the core hooks — only the [night-shift scheduler](run-the-night-shift.md) needs PowerShell 7.
- **Hooks don't fire on macOS/Linux.** You probably skipped step 3 (still using the PowerShell `settings.json`) or step 2 (scripts not executable).
- **`verify.py` errors on import.** You're on Python < 3.10. The tools use 3.10+ type syntax. See [prerequisites](../getting-started/prerequisites.md).

Next: [dispatch your first task](dispatch-your-first-task.md). To turn on v2 features, see [what's new in v2](../overview/whats-new-in-v2.md) and its linked guides (external signals, browser verification, the night shift, health-based scope).
