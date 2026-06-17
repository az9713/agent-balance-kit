# Self-improving harness

The self-improvement layer journals every agent session and mines it weekly for friction, turning repeated pain into new skills — so the harness gets smarter the more you use it.

## Why it exists as its own layer

Every Claude Code session is a record of where the loop was rough: where you had to clarify the same thing twice, where a verification command was missing, where the agent guessed wrong. Most people throw that signal away when the session ends. This layer treats those sessions as gold. A single weekly pass over them can surface the one skill that would have prevented the most rework — and minting that skill compounds, because next week's loop starts tighter.

## How it works: two stages

The design splits cheap-and-constant from expensive-and-occasional:

1. **Journaling** runs on *every* session end. It must be fast and reliable, so it is plain deterministic Python — no model call.
2. **Mining** runs *once a week*, consciously, and is where the intelligence lives — it generates a prompt you hand to Claude.

This separation is deliberate. See [ADR 002](../architecture/adr/002-deterministic-journaling.md).

### Stage 1 — journaling, via the Stop hook

When a session ends, the `Stop` hook pipes Claude Code's hook JSON into `session_journal.py`. The journaler:

- Reads its stdin with `utf-8-sig`, so the UTF-8 BOM that Windows PowerShell prepends when piping into a native process is stripped before parsing. Without this, `json.loads` would fail and every Windows journal entry would silently record an empty `unknown` session — see [common gotchas](#common-gotchas).
- Reads `transcript_path`, the last assistant message (last 2000 chars), `session_id`, and `cwd` from the hook payload.
- Reads the last 200 lines of the transcript.
- Counts **friction signals** — case-insensitive matches for: `error`, `failed`, `failing`, `timeout`, `ambiguous`, `permission`, `blocked`, `retry`, `can't`, `cannot`, `not found`, `hallucinat`, `unclear`.
- Appends a markdown block to `.agent-harness/session-summaries/<YYYY-MM-DD>.md`, including those counts and a set of retrospective questions.

A journal block looks like:

```markdown
## Session 7f3a-...

- time: 2026-06-15T14:02:11
- cwd: `C:\path\to\your-repo`
- transcript: `~/.claude/projects/.../session.jsonl`
- friction_signals: `{"\\berror\\b": 3, "\\bambiguous\\b": 1}`

### Last assistant message tail
...

### Retrospective questions for weekly skill mining
- Where did the agent require repeated clarification?
- Which verification command was missing or unreliable?
- ...
```

The friction counts are a triage signal, not a verdict: a session with many `error` hits is worth a closer look during mining.

### Stage 2 — mining, via `weekly_skill_miner.py`

```powershell
python .claude/tools/weekly_skill_miner.py
```

It reads the **last 14** session-summary files (last 8000 chars of each) and writes a prompt to `.agent-harness/weekly/<ISO-year>-W<ISO-week>-skill-mining-prompt.md`, then prints the path. It does **not** call a model — it assembles the prompt you paste into Claude Code:

```text
Read .agent-harness/weekly/<latest>.md.
Create or update exactly one missing skill under .claude/skills/.
Do not edit production code.
```

The generated prompt asks Claude to rank the top 5 frictions, name the single highest-leverage skill to add, create exactly one `.claude/skills/<name>/SKILL.md`, include a test invocation, and state what *not* to automate yet.

### The `session-retrospective` skill

This skill guides the mining conversation. It classifies friction into a taxonomy — spec ambiguity, verification gap, tool gap, skill gap, subagent gap, safety gap, human overload — and requires the output to be one ranked table plus exactly one concrete patch. Detail: [skills & subagents](../reference/skills-and-subagents.md#session-retrospective).

### Automatic draft-skill generation (v2)

v2 adds a deterministic shortcut between journaling and a finished skill. `generate_skill.py` scans the friction-keyword lines in your session/weekly notes and scaffolds a draft `SKILL.md` — no model call:

```powershell
python .claude/tools/generate_skill.py            # writes a draft under .agent-harness/skill-drafts/
python .claude/tools/generate_skill.py --install  # writes directly into .claude/skills/
```

It is the deterministic counterpart to the model-driven [`auto-skill-generation`](../reference/skills-and-subagents.md#auto-skill-generation) skill: the tool gives you a reviewable starting point; the skill writes a considered one. Both honor the "exactly one" rule below.

> **Review before installing.** `--install` overwrites `.claude/skills/<slug>/SKILL.md` with no existence check and no review. Prefer the default draft location, read it, then promote it by hand.

## The "exactly one" rule

Every cycle mints **one** skill, not five. This is intentional restraint: one well-chosen skill you understand beats a batch you don't, and it keeps the harness's growth reviewable. It mirrors the kit's whole philosophy — don't outrun your ability to review what you're accumulating.

## Interaction with other layers

- **← All layers:** journals capture friction from signal, dispatch, execution, and verification alike.
- **→ Layer 2 (dispatch):** new skills minted here often become dispatch-time skills, tightening how future briefs become contracts.

## Configuration and tuning

- Output directories `.agent-harness/session-summaries/` and `.agent-harness/weekly/` are created on demand. Add `.agent-harness/` to `.gitignore` unless you want the journals versioned.
- Both tools honor `CLAUDE_PROJECT_DIR` for the repo root, falling back to the current directory.
- Run mining on whatever cadence fits — weekly is the default, daily works for high-volume periods.

## Common gotchas

- **Empty journals.** If `session-summaries/` is empty or missing, the Stop hook never ran. Confirm the hook is registered in the *active* settings file (`settings.json` on Windows, the Unix variant on macOS/Linux) and that the session actually stopped (not crashed).
- **Entries that say `## Session unknown` with empty friction.** This was a Windows-only bug: PowerShell prepends a UTF-8 BOM when piping into Python, which broke `json.loads` and degraded every entry. v2 fixes it by decoding stdin with `utf-8-sig`. If you still see `unknown` entries, you're on an unpatched `session_journal.py` — confirm it reads `sys.stdin.buffer.read().decode("utf-8-sig", ...)`.
- **`transcript: not provided`.** The hook payload lacked a transcript path; the journal still records the friction count from the last assistant message. This is expected in some session types.
- **Mining produced no skill.** If there are no summaries yet, the generated prompt says so. Run some gated sessions first.
