# Reference: task file format

The grammar of `AGENT_TASKS.md`, the Layer 1 inbox. Only the **first line** of each task is machine-parsed; the indented body is free-form context.

## The parsed first line

`agent_ready_loop.py` finds a task with this exact pattern (derived from the parser's regex):

```text
- [ ] <TASK-ID> | agent-ready | branch: <branch> | title: <title>
```

Every element is mandatory and order-sensitive:

| Element | Rule |
|---------|------|
| `- [ ] ` | Literal. A markdown unchecked box with single spaces. A checked box `- [x]` will **not** match. |
| `<TASK-ID>` | Matched exactly and case-sensitively against `--task`. E.g. `TASK-001`. |
| ` \| agent-ready \| ` | Literal ` | agent-ready | `. The state must be exactly `agent-ready`. |
| `branch: <branch>` | The branch comes **before** the title. `<branch>` is everything up to the next `|`, then stripped — so it cannot contain a `|`. |
| `title: <title>` | The title runs to the end of the line. |

Example that parses:

```markdown
- [ ] TASK-001 | agent-ready | branch: agent/task-001 | title: Fix acronym-preserving sentence case
```

## The unparsed body

Anything indented under the first line, up to the next `- [ ]` line or end of file, is captured **verbatim** and copied into the worktree's prompt file. The parser does not read individual sub-fields — they're for you and the agent. Use them to be precise:

```markdown
- [ ] TASK-001 | agent-ready | branch: agent/task-001 | title: Fix acronym-preserving sentence case
  - repo_area: src/text
  - goal: Sentence-case headings without mangling acronyms.
  - non_goals:
    - Do not change markdown rendering.
  - acceptance:
    - SSO remains SSO.
    - API remains API.
    - "HELLO WORLD" becomes "Hello world".
  - verification:
    - python -m pytest tests/test_sentence_case.py -q
  - rollback:
    - Revert the branch.
```

### Recommended body fields

These have no enforced schema, but the [`agent-ready-task` skill](../concepts/voice-first-dispatch.md) and the prompt template expect them:

| Field | Purpose |
|-------|---------|
| `repo_area` | Where the change lives, to scope the agent |
| `goal` | One-sentence intent |
| `non_goals` | What must not change |
| `acceptance` | Observable, testable criteria |
| `verification` | Exact commands that prove success |
| `rollback` | How to undo |

## Task states

The state field is part of the parsed first line, but only one value is dispatchable. The v2 starter `AGENT_TASKS.md` documents the full lifecycle vocabulary:

| State | Dispatchable? | Meaning |
|-------|:---:|---------|
| `signal` | No | Raw inbound, not yet triaged into a task |
| `needs-spec` | No | Missing criteria/target; run the `agent-ready-task` skill to promote it |
| `agent-ready` | **Yes** | Fully specified; the launcher (or night-shift poller) will build a worktree |
| `in-flight` | No | An agent is working it |
| `review` | No | Awaiting human review/merge |
| `done` | No | Merged/closed |

Only `agent-ready` is dispatched; the other states are workflow bookkeeping for you (and the [signal-triage](skills-and-subagents.md#signal-triage) flow, which writes new cards as `needs-spec`). The shipped starter `TASK-001` is `needs-spec`, so nothing dispatches out of the box — promote it to `agent-ready` first.

> **Same grammar drives the night shift.** [`poll_agent_ready.py`](tools.md#poll_agent_readypy) parses this identical first-line pattern and dispatches only `agent-ready` tasks. A task that doesn't match the exact one-line grammar is silently skipped by the poller. See [run the night shift](../guides/run-the-night-shift.md).

A `needs-spec` example, which the launcher will refuse:

```markdown
- [ ] TASK-002 | needs-spec | title: Improve onboarding
  - missing:
    - exact screen
    - target user path
    - acceptance criteria
```

## Common parse failures

| Symptom | Cause |
|---------|-------|
| "Task X not found or not marked agent-ready" | State isn't `agent-ready`, ID is misspelled/mis-cased, or the box is checked |
| Branch comes out wrong | `branch:` and `title:` are swapped — branch must come first |
| Branch truncated | The branch value contained a `|` |
| Nothing matches | Missing the literal `- [ ] ` prefix, or extra spaces inside the box (`- [  ]`) |

See also: [signal layer](../concepts/signal-layer.md), [`agent_ready_loop.py`](tools.md#agent_ready_looppy).
