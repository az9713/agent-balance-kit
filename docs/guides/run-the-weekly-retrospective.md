# Run the weekly retrospective

Mine a week of session journals for friction and mint one new skill, so recurring pain stops recurring.

> **Goal:** one new or updated `.claude/skills/<name>/SKILL.md` that would have prevented this week's most expensive friction — and nothing else changed.

## Prerequisites

- The kit installed, with the `Stop` hook active. See [install the kit](install-into-a-repo.md).
- At least a few completed sessions, so `.agent-harness/session-summaries/` is non-empty.

## Steps

### 1. Confirm you have journals to mine

```powershell
Get-ChildItem .agent-harness/session-summaries/
```

```bash
ls .agent-harness/session-summaries/
```

Expect one `<YYYY-MM-DD>.md` file per day you worked. Empty? The Stop hook never ran — see [self-improving harness](../concepts/self-improving-harness.md#common-gotchas).

### 2. Generate the weekly prompt

```powershell
python .claude/tools/weekly_skill_miner.py
```

```bash
python3 .claude/tools/weekly_skill_miner.py
```

It reads the last 14 summary files and prints the path it wrote, for example:

```text
C:\path\to\your-repo\.agent-harness\weekly\2026-W24-skill-mining-prompt.md
```

The kit's wrapper does the same and reminds you what to do next:

```powershell
.\scripts\weekly-retrospective.ps1
```

### 3. Hand the prompt to Claude Code

```text
Read .agent-harness/weekly/2026-W24-skill-mining-prompt.md.
Create or update exactly one missing skill under .claude/skills/.
Do not edit production code.
```

The prompt instructs Claude to rank the top 5 frictions, name the single highest-leverage skill, create exactly one `SKILL.md`, include a test invocation, and state what not to automate yet. The [`session-retrospective` skill](../reference/skills-and-subagents.md#session-retrospective) shapes this analysis.

### 4. Review the proposed skill before keeping it

Read the new `SKILL.md`. Ask: would this actually have shortened the loop, or is it ceremony? Keep it only if it earns its place. Then commit it on its own:

```powershell
git add .claude/skills/
git commit -m "Add skill from W24 retrospective"
```

## Verification

A good cycle ends with:

- exactly **one** new or changed file under `.claude/skills/`,
- **zero** production-code changes (`git status` shows only the skill),
- a test invocation in the skill you can actually run.

## Troubleshooting

- **"No summaries found yet."** No journals exist. Confirm the Stop hook is in the active settings file and run some sessions first.
- **Claude wants to create several skills.** Hold it to one. The "exactly one" rule keeps the harness's growth reviewable — see [self-improving harness](../concepts/self-improving-harness.md#the-exactly-one-rule).
- **The mined skill edits product code.** Reject it. The retrospective is allowed to change the harness, never the application.
- **Friction counts look empty despite a rough week.** The journaler only scans the last 200 transcript lines and the last assistant message. Long sessions can bury early friction; mine more often (daily) during heavy periods.
