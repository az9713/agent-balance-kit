# Voice-first dispatch

The dispatch layer converts a rough or dictated brief into a precise task contract, so "voice speed" produces specifications an agent can actually satisfy.

## Why it exists as its own layer

Voice is not just faster typing — it changes throughput. At ~184 words per minute of dictation versus ~90 of typing, you can brief three agents before a typist finishes one prompt. But raw speed is dangerous: a fast, vague task makes an agent guess, and a guessing agent produces work you have to redo. The dispatch layer is the counterweight. It forces every brief through a fixed contract, so the speed of voice is spent on volume, not on ambiguity.

## How it works

The mechanism is one skill: `.claude/skills/agent-ready-task/SKILL.md`. A Claude Code skill is a `SKILL.md` file with a YAML `description`; Claude loads it when relevant or when you invoke it directly. This skill triggers on any rough input — a voice transcript, a Slack message, a Linear/GitHub ticket, or a vague idea — and emits a structured task contract.

You invoke it explicitly:

```text
Use /agent-ready-task.

Voice brief:
<paste your raw dictated task here>

Convert this into:
1. exact goal
2. non-goals
3. touched files
4. acceptance criteria
5. verification commands
6. rollback plan
7. open questions only if blocking
```

## The output: a task contract

The skill produces this shape (full template in the [skill reference](../reference/skills-and-subagents.md#agent-ready-task)):

```markdown
# Task Contract

## Goal
One precise sentence.

## Non-goals
- Explicitly list what should not change.

## Context
- Relevant repo areas, files, APIs, tickets, prior decisions.

## Acceptance criteria
- [ ] Observable criterion 1
- [ ] Observable criterion 2

## Verification
- Gate 1:
  - command:
  - expected result:
- Gate 2:
  - command/manual browser path:
  - expected result:
- Gate 3:
  - critic checklist:

## Worktree
- branch:
- suggested worktree path:

## Risk
- highest risk:
- rollback:
- files not to touch:

## Open questions
Only blocking questions. If not blocking, make a reasonable assumption and label it.
```

## The rules the skill enforces

- Convert fuzzy language into **testable** criteria. "Make onboarding better" is not a criterion; "the signup form rejects an empty email with a visible error" is.
- If the brief is too broad, **split it into subtasks** — one worktree per independent task.
- Keep implementation out of this step. The contract describes *what* and *how to verify*, not the code.
- Mark non-blocking unknowns as labeled assumptions rather than stopping to ask.

## Interaction with other layers

- **← Layer 1 (signal):** A `needs-spec` task from the [inbox](signal-layer.md) is the typical input. The contract's acceptance criteria are what let you re-label it `agent-ready`.
- **→ Layer 3 (execution):** The contract's `branch` and acceptance criteria flow into `AGENT_TASKS.md`, which [`agent_ready_loop.py`](worktree-execution.md) then turns into a worktree and a prompt file.

## Tooling for the voice half

The kit does not bundle a speech-to-text tool — any works: OS dictation, ChatGPT Advanced Voice, Whisper Flow, or a local model. The contract step is tool-agnostic on purpose; the discipline lives in the skill, not the microphone.

## Common gotchas

- **Skipping the contract because the brief "seems clear."** Clear-to-you is not testable-by-an-agent. Run it through the skill anyway; the acceptance criteria are cheap insurance against a redo.
- **Asking the skill to implement.** It deliberately stops at the contract. Implementation happens later, in the worktree, against the contract.
- **One contract, many tasks.** If your contract has unrelated acceptance criteria, split it. Parallelism only works when each worktree owns one independent task.
