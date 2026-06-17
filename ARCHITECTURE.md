# Architecture: Four-Layer Agent Balance Stack

## Layer 1: Signal

Purpose: prevent context-switching into noisy systems.

Inputs:
- Slack mentions/DMs
- Linear/GitHub issues
- email
- calendar
- local Markdown inbox

Output:
- ranked task candidates
- duplicate detection
- agent-ready tasks only

Gap-filled implementation in this kit:
- `AGENT_TASKS.md` is the deployable local inbox.
- Real Slack/Linear integration should be done through your configured MCP servers.

## Layer 2: Voice-first dispatch

Purpose: reduce prompt latency and let you dispatch multiple agents before manual typing would finish.

Input:
- raw dictated brief

Output:
- task contract

Gap-filled implementation:
- `.claude/skills/agent-ready-task/SKILL.md`

## Layer 3: Remote + isolated execution + verification

Purpose: let agents work while you leave the desk, without letting their diffs collide.

Mechanisms:
- Claude Code Remote Control
- git worktrees
- hooks
- Gate 1/2/3 verification
- critic subagent

Gap-filled implementation:
- `.claude/tools/agent_ready_loop.py`
- `.claude/tools/verify.py`
- `.claude/agents/critic.md`
- `.claude/agents/browser-tester.md`
- `.claude/settings.json`

## Layer 4: Self-improving system

Purpose: stop discarding your interaction history. Mine it for repeated friction and convert friction into skills.

Mechanisms:
- Stop hook journals sessions.
- Weekly miner generates a prompt.
- Claude creates exactly one new skill per cycle.

Gap-filled implementation:
- `.claude/tools/session_journal.py`
- `.claude/tools/weekly_skill_miner.py`
- `.claude/skills/session-retrospective/SKILL.md`

## Optional body-state layer

Purpose: prevent burnout-turbo.

Inputs:
- Oura/Apple Health/manual sleep score
- work hours
- review load
- number of active agents

Gap-filled implementation:
- not automated here. Start with a manual rule:
  - poor sleep: max 1 implementation agent
  - normal sleep: max 2 implementation agents
  - high-energy day: max 3 agents, but no auto-merge
