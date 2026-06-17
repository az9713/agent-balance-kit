---
name: auto-skill-generation
description: Convert repeated session friction into a new project skill and write it under .claude/skills/.
---

# Auto Skill Generation Skill

Use this after weekly retrospective mining.

## Inputs

Read:

- `.agent-harness/session-summaries/`
- `.agent-harness/weekly/`
- `.agent-harness/skill-drafts/`

## Procedure

1. Identify one repeated friction pattern only.
2. Name the missing reusable procedure.
3. Create exactly one skill folder under `.claude/skills/<slug>/`.
4. Write `SKILL.md` with:
   - frontmatter `name` and `description`
   - triggering conditions
   - input files/tools
   - deterministic checklist
   - success/failure criteria
5. Do not edit product code.
6. Do not create broad skills like "be better at coding".

## Quality bar

A good skill should reduce future prompt ambiguity by at least one full back-and-forth turn.
