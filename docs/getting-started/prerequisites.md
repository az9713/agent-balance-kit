# Prerequisites

What you need before installing the kit. Verify each before running the [quickstart](quickstart.md).

The **core loop** (signal → dispatch → worktree execution → verification → journaling) needs only the four required tools below. The v2 features — external signal sync, browser verification, the night shift, and health-based scope — each add their own optional dependency, listed under [v2 feature dependencies](#v2-feature-dependencies). Install those only for the features you turn on.

## Required

### Git

Worktrees are core to Layer 3.

- Verify: `git --version` (any modern version with `git worktree` — 2.5+)
- Install: [git-scm.com/downloads](https://git-scm.com/downloads)

### Python 3.10+

All kit tools are Python and use 3.10+ syntax (`list[str]`, `dict[str, str]`, `X | Y` unions).

- Verify: `python --version` (should print `Python 3.10.x` or higher)
- Install: [python.org/downloads](https://www.python.org/downloads/)

> **Note:** On macOS/Linux the shell hooks call `python3`, not `python`. Make sure `python3` resolves. On Windows the hooks and CI call `python`.

### A shell

- **Windows:** the registered hooks invoke `powershell.exe` — **Windows PowerShell 5.1 is enough for the core loop** (it ships with Windows 10/11). PowerShell 7 (`pwsh`) is *recommended* but only *required* for the night-shift scheduler (see below). Verify: `powershell -version` (5.1+) and, if you plan to use the night shift, `pwsh --version` (7+).
- **macOS/Linux:** Bash. Verify: `bash --version`.

### Claude Code, installed and authenticated

The kit is a harness *for* Claude Code. Hooks, skills, and subagents only do anything inside a Claude Code session.

- Verify: `claude --version`
- For [remote control](../concepts/worktree-execution.md#remote-control), you need **Claude Code v2.1.51 or later**.

## v2 feature dependencies

Each row is needed **only** if you enable that feature. The core loop runs without any of them.

| Feature | Needs | Verify / install |
|---------|-------|------------------|
| [Browser verification](../concepts/verification-gates.md#gate-2-browser-evidence) | Playwright + Chromium | `python -m pip install playwright` then `python -m playwright install chromium` |
| [External signal sync](../concepts/signal-layer.md#external-signal-sync) (live) | MCP servers **or** API tokens | [MCP setup](../guides/set-up-external-signals.md); tokens go in `.env` (see [environment variables](../reference/environment-variables.md)) |
| [Night shift](../concepts/worktree-execution.md#the-night-shift) on **Windows** | **PowerShell 7 (`pwsh`)** + Task Scheduler | `pwsh --version`; install: `winget install Microsoft.PowerShell` |
| [Night shift](../concepts/worktree-execution.md#the-night-shift) on **macOS/Linux** | `cron` | `crontab -l` (cron is preinstalled on most distros/macOS) |
| [Health-based scope](../concepts/scope-and-health.md) (wearable) | Oura access token | put `OURA_ACCESS_TOKEN` in `.env`; the manual `HEALTH_STATE.md` path needs nothing |

> **Why PowerShell 7 for the night shift?** `scripts/install-night-shift-windows.ps1` registers a Scheduled Task whose action runs `pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ...\night-shift-once.ps1`. The task literally invokes `pwsh.exe`, so without PowerShell 7 installed the scheduled run fails even though your interactive hooks work fine on 5.1. The `cron` path on macOS/Linux has no such requirement.

## Optional (quality-of-life)

### Node.js + npm

Needed if your target repo is TypeScript/JavaScript. `verify.py` auto-detects `package.json` scripts (`lint`, `typecheck`, `test`, `build`) and the CI workflow sets up Node 22.

- Verify: `node --version`, `npm --version`
- Install: [nodejs.org/download](https://nodejs.org/download)

### ruff

If installed and on PATH, `verify.py` adds `ruff check .` to Gate 1 for Python repos. If absent, it is silently skipped.

- Verify: `ruff --version`
- Install: `pip install ruff`

### The Claude mobile app

Needed for [remote control](../concepts/worktree-execution.md#remote-control) — steering a desk session from your phone.

### A speech-to-text tool

For [voice-first dispatch](../concepts/voice-first-dispatch.md). Any works: OS dictation, ChatGPT Advanced Voice, Whisper Flow, or a local model. The kit does not bundle one.

## One-shot check

Core loop:

```bash
git --version
python --version
claude --version
```

All three printing versions means you can run the [quickstart](quickstart.md). Add `pwsh --version` (Windows) before setting up the [night shift](../guides/run-the-night-shift.md).
