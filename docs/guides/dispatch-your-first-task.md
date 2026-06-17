# Dispatch your first task

Take a rough, spoken idea all the way to a verified diff: contract it, run it in a worktree, gate it, and get a critic verdict.

> **Goal:** one real change, built by an agent in isolation, with evidence you can review in under a minute.

## Prerequisites

- The kit installed and committed in your repo. See [install the kit](install-into-a-repo.md).
- A speech-to-text tool (optional but recommended). Any works.
- `AGENT_TASKS.md` created: `Copy-Item AGENT_TASKS.example.md AGENT_TASKS.md`.

## Steps

### 1. Capture the brief by voice

Dictate the change as you'd explain it to a colleague. Don't polish it. Example transcript:

```text
The sentence-case pass in the blog generator is breaking acronyms.
SSO turns into Sso, API turns into Api. Fix it so known acronyms stay
uppercase but normal headings still get sentence cased. Don't touch
the markdown renderer.
```

### 2. Force it through the task-contract skill

In Claude Code:

```text
Use /agent-ready-task.

Voice brief:
The sentence-case pass in the blog generator is breaking acronyms. SSO
turns into Sso, API turns into Api. Fix it so known acronyms stay
uppercase but normal headings still get sentence cased. Don't touch the
markdown renderer.

Convert this into a task contract with acceptance criteria and verification commands.
```

You get back a contract with testable criteria — for example: *SSO remains SSO; API remains API; "HELLO WORLD" becomes "Hello world"; markdown rendering unchanged.*

### 3. Add the task to the inbox

Copy the contract's branch, title, acceptance, and verification into one `AGENT_TASKS.md` entry. The first line must match the grammar exactly:

```markdown
- [ ] TASK-001 | agent-ready | branch: agent/task-001 | title: Fix acronym-preserving sentence case
  - acceptance:
    - SSO remains SSO.
    - API remains API.
    - "HELLO WORLD" becomes "Hello world".
  - verification:
    - python -m pytest tests/test_sentence_case.py -q
```

See [task file format](../reference/task-file-format.md) for the exact rules.

### 4. Create the worktree

```powershell
python .claude/tools/agent_ready_loop.py --task TASK-001
```

This makes `.worktrees/TASK-001/` on branch `agent/task-001` and writes the prompt file.

### 5. Run the agent, then walk away

```powershell
cd .worktrees\TASK-001
claude
```

```text
Read .agent-harness/TASK-001-prompt.md and execute the task contract.
Restate the acceptance criteria first.
```

Optionally start [remote control](../concepts/worktree-execution.md#remote-control) and steer from your phone:

```text
/remote-control TASK-001
```

The PostToolUse hook runs `verify.py --fast` after each edit; the TaskCompleted hook blocks "done" if Gate 1 is red.

### 6. Get a critic verdict

```text
Use the critic agent. Review the diff against the task contract and
.agent-harness/verify-log.jsonl. Verdict: PASS, REVISE, or BLOCK.
```

## Verification

You're done when:

- `python .claude/tools/verify.py --fast` prints `"ok": true`.
- The critic returns **PASS** with each acceptance criterion mapped to evidence.

Then merge by hand:

```powershell
cd C:\path\to\your-repo
git merge agent/task-001
git worktree remove .worktrees/TASK-001
```

## Troubleshooting

- **"Task TASK-001 not found or not marked agent-ready."** The first line is malformed. Check for the literal `- [ ] `, the `agent-ready` state, and `branch:` before `title:`. See [task file format](../reference/task-file-format.md).
- **Critic returns REVISE for "no negative test."** Ask the agent to add a test proving the regression can't return (e.g. that "SSO" never becomes "Sso"), then re-run the critic.
- **Hook didn't run verification.** Confirm you're using the OS-correct settings file. See [install the kit](install-into-a-repo.md), step 3.
