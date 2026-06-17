# Quickstart

Install the kit into a repo and run one task end-to-end — from inbox to verified diff with a critic verdict — in about 15 minutes.

This works without reading any other doc. For the *why* behind each step, read [onboarding](onboarding.md) afterward.

> **Prerequisites:** Git, Python 3.10+, Claude Code authenticated. See [prerequisites](prerequisites.md).

## 1. Copy the kit into your target repo

From the root of the kit:

```powershell
# Windows PowerShell, run from a copy of the kit
Copy-Item -Recurse -Force .\.claude, .\scripts, .\.github, .\.vscode C:\path\to\your-repo\
Copy-Item .\AGENT_TASKS.example.md, .\CLAUDE.md C:\path\to\your-repo\
```

```bash
# macOS/Linux
cp -R .claude scripts .github .vscode AGENT_TASKS.example.md CLAUDE.md /path/to/your-repo/
chmod +x /path/to/your-repo/.claude/hooks/*.sh /path/to/your-repo/scripts/*.sh /path/to/your-repo/.claude/tools/*.py
```

> **Note:** On macOS/Linux, also activate the Unix hook config: copy `.claude/settings.unix.json` over `.claude/settings.json`. The default `settings.json` invokes `powershell.exe`. See [hooks & settings](../reference/hooks-and-settings.md#choosing-the-right-settings-file).

## 2. Create your task inbox

```powershell
cd C:\path\to\your-repo
Copy-Item AGENT_TASKS.example.md AGENT_TASKS.md
```

`AGENT_TASKS.md` ships with one worked example, `TASK-001`. Expected: the file exists and contains a line beginning `- [ ] TASK-001 | agent-ready | branch: agent/task-001 | title: ...`.

## 3. Create an isolated worktree for the task

```powershell
python .claude/tools/agent_ready_loop.py --task TASK-001
```

Expected output:

```text
+ git worktree add -b agent/task-001 .worktrees/TASK-001

Worktree ready: C:\path\to\your-repo\.worktrees\TASK-001
Prompt ready:   C:\path\to\your-repo\.worktrees\TASK-001\.agent-harness\TASK-001-prompt.md

Start Claude Code:
cd .worktrees\TASK-001
claude
Then paste: Read <prompt path> and execute the task contract.
```

This created a fresh checkout on branch `agent/task-001` and a prompt file restating the task contract.

## 4. Start Claude Code in the worktree

```powershell
cd .worktrees\TASK-001
claude
```

First prompt:

```text
Read .agent-harness/TASK-001-prompt.md and execute the task contract.
Restate the acceptance criteria before editing.
```

The agent restates the criteria, makes the smallest change, and runs the verification commands listed in the task.

## 5. Watch the verification hooks fire

You don't run these — they run automatically:

- After every `Write`/`Edit`, a **PostToolUse** hook runs `verify.py --fast` in the background.
- When the agent marks the task complete, a **TaskCompleted** hook runs `verify.py --fast` and *blocks completion* (exit code 2) if it fails.

Run a check manually any time:

```powershell
python .claude/tools/verify.py --fast
```

Expected (abridged) output — a JSON record ending in `"ok": true`:

```json
{
  "ts": "2026-06-15T18:03:11Z",
  "mode": "fast",
  "ok": true,
  "results": [ ... ]
}
```

A `"ok": false` means a check failed; read the `stderr_tail` in the failing result.

## 6. Get a critic verdict before merge

In the same session:

```text
Use the critic agent. Review this diff against the task contract and the
verification log at .agent-harness/verify-log.jsonl.
Verdict must be PASS, REVISE, or BLOCK.
```

The `critic` subagent is read-only — it cannot edit your code. It returns a structured report with a verdict and any required fixes.

## 7. Merge — manually

The kit never auto-merges. When the verdict is PASS and you're satisfied:

```powershell
cd C:\path\to\your-repo
git merge agent/task-001
git worktree remove .worktrees/TASK-001
```

## What just happened

You took one task from a low-noise inbox, ran it in isolation, let hooks verify it automatically, got an independent critic verdict, and merged on your own judgment. The agent did the minutiae; you owned the decision. When the session ended, a Stop hook also journaled it to `.agent-harness/session-summaries/` for the [weekly retrospective](../guides/run-the-weekly-retrospective.md).

## Next steps

- [Onboarding](onboarding.md) — why the kit is shaped this way, with a full narrative walkthrough.
- [Dispatch your first real task](../guides/dispatch-your-first-task.md) — using a voice brief and the task-contract skill.
- [Run parallel agents for a large feature](../guides/run-parallel-agents-for-a-large-feature.md).
- [What's new in v2](../overview/whats-new-in-v2.md) — external signals, browser verification, the night shift, and health-based scope.
