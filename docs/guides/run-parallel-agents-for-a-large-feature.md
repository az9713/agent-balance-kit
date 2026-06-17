# Run parallel agents for a large feature

Split a cross-stack feature into independent subtasks and run one isolated agent per subtask, so big work parallelizes without the diffs colliding.

> **Goal:** a feature that touches backend, database, and frontend, delivered as several reviewable worktree diffs instead of one tangled branch.

The honest caveat: these flows shine for discrete, bite-sized tasks. A feature that genuinely must change one file across all layers at once does not parallelize — that part stays sequential and human-led. The skill is in the *decomposition*.

## Prerequisites

- The kit installed. See [install the kit](install-into-a-repo.md).
- A feature you can describe in one or two sentences.
- Comfort merging branches by hand.

## Steps

### 1. Write a mini-spec

Before any agent runs, write `specs/<feature>.md` yourself. Capture the goal, the boundary (what's out of scope), and the seams where the work splits. This is human work — it's the judgment the agents can't supply.

### 2. Split into 3–5 independent subtasks

Each subtask must own a distinct area so two agents never edit the same file. A good split for "add saved searches":

| Subtask | Area | Branch |
|---------|------|--------|
| TASK-101 | DB migration + model | `agent/task-101` |
| TASK-102 | API endpoints | `agent/task-102` |
| TASK-103 | Frontend UI | `agent/task-103` |

Give each one its own [task contract](../concepts/voice-first-dispatch.md) with acceptance criteria and verification commands, and add all three to `AGENT_TASKS.md`.

### 3. Create one worktree per subtask

```powershell
python .claude/tools/agent_ready_loop.py --task TASK-101 --open-code
python .claude/tools/agent_ready_loop.py --task TASK-102 --open-code
python .claude/tools/agent_ready_loop.py --task TASK-103 --open-code
```

`--open-code` opens each worktree in VS Code. You now have three isolated checkouts on three branches.

### 4. Run one Claude Code session per worktree

In each worktree:

```text
Read .agent-harness/TASK-1NN-prompt.md and execute the task contract.
```

> **Tip:** Start with one implementation agent, one critic, and one weekly-retrospective agent — not three implementation agents. Scale to a second implementation agent only once your verification logs are boringly green. The health policy caps this further: poor sleep → one implementation agent. See [scope and health](../concepts/scope-and-health.md).

### 5. Require a uniform deliverable from each worktree

Each session must produce:

- the code diff,
- a verification log (`.agent-harness/verify-log.jsonl`),
- migration notes (if it touched data),
- a risk list.

This uniformity is what lets you review three diffs quickly instead of reverse-engineering three different styles of "done."

### 6. Merge in dependency order, gating each

Merge the foundation first (DB), then API, then UI. Run the critic and `verify.py --full` against each before merging:

```powershell
git merge agent/task-101
python .claude/tools/verify.py --full
git merge agent/task-102
python .claude/tools/verify.py --full
git merge agent/task-103
python .claude/tools/verify.py --full
```

## Verification

The feature is integrated when, on the merged branch:

- `python .claude/tools/verify.py --full` is green, and
- the `critic` agent returns PASS against the original `specs/<feature>.md`, not just the individual subtask contracts.

## Troubleshooting

- **Two subtasks keep editing the same file.** Your split has a shared seam — redraw the boundaries so each subtask owns its files, or sequence those two.
- **Merge conflicts between worktrees.** Expected when subtasks aren't truly independent. Merge the foundational branch first and rebase the others, or fold the conflicting pair into one sequential task.
- **You can't review all the diffs with attention.** That's the stop signal. Reduce parallelism until you can. Unreviewed parallel diffs are review debt, not progress.
