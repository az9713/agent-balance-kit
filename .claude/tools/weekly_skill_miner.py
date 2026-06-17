#!/usr/bin/env python3
"""
Generate a weekly prompt for Claude Code to mine session summaries and create missing skills.
No API calls. It writes a Markdown prompt you paste into Claude Code.
"""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
SUM = ROOT / ".agent-harness" / "session-summaries"
OUT = ROOT / ".agent-harness" / "weekly"

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()
    iso_year, iso_week, _ = today.isocalendar()
    out = OUT / f"{iso_year}-W{iso_week:02d}-skill-mining-prompt.md"

    summaries = []
    for p in sorted(SUM.glob("*.md"))[-14:]:
        summaries.append(f"\n\n# FILE: {p.relative_to(ROOT)}\n\n{p.read_text(encoding='utf-8', errors='replace')[-8000:]}")

    body = f"""
# Weekly Agent Harness Retrospective

You are improving this repo's agentic coding harness.

## Inputs

Read the session summaries below. Identify repeated friction patterns:
- repeated clarifying questions
- missing verification commands
- tasks that lacked acceptance criteria
- repeated prompts the human had to paste
- missing MCP/server/tool affordances
- recurring bugs or test gaps
- places where a small Claude Code skill would reduce future context load

## Required output

1. Top 5 frictions, ranked by recurrence and cost.
2. The single highest-leverage skill to add now.
3. Create or update exactly one file under `.claude/skills/<skill-name>/SKILL.md`.
4. Do not edit production code.
5. Include a test invocation for the new skill.
6. Include one paragraph explaining what not to automate yet.

## Session summaries

{''.join(summaries) if summaries else '[No summaries found yet. Run Claude Code with the Stop hook enabled first.]'}
"""
    out.write_text(body, encoding="utf-8")
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
