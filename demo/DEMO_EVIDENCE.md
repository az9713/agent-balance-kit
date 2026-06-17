# Agent Balance Kit v2 — Live Demo Evidence

**Run date:** 2026-06-16 · **Platform:** Windows 11, PowerShell + Python 3.13.5, git 2.54
**Thesis under test:** _agents scale; human attention does not._ Each moment below shows the kit removing a demand on human attention — without ever doing autonomous, risky, or irreversible work.

All outputs in this file are **real captured stdout** from the run. Raw artifacts are archived in [`evidence/`](evidence/) (the live `.agent-harness/` copies are gitignored because they can hold personal data, so they would not survive a push).

> Reproduce: from the kit root, run the commands in each section in order. The demo is git-initialized so the worktree step works; with no credentials the external calls skip cleanly.

---

## Moment 1 — The attention firewall

**Bottleneck:** opening Slack / Linear / GitHub and getting hijacked by threads.
**Relief:** one command turns three noisy systems into one local JSON inbox — and self-skips when you have no credentials, instead of crashing.

```powershell
python .claude/tools/sync_external_signals.py --all
```
```
Wrote ...\.agent-harness\signals\latest.json with 3 items
Skipped/errors:
- github: GITHUB_REPOSITORY not set
- linear: LINEAR_API_KEY not set
- slack: SLACK_BOT_TOKEN or SLACK_CHANNEL_IDS not set
```

No app was opened. Nothing threw. Evidence: [`evidence/signals-latest.json`](evidence/signals-latest.json).

---

## Moment 2 — Noise becomes a small, ranked list

**Bottleneck:** reading every message to decide what's actionable.
**Relief:** a deterministic triager. A signal becomes `agent-ready` **only** if it carries the `agent-ready` label *and* has acceptance/verification markers; everything else is held as `needs-spec`. You glance at a triaged list, not a firehose.

```powershell
python .claude/tools/signal_triage.py --apply                              # real empty feed
python .claude/tools/signal_triage.py --signals demo/sample-signals.json --apply   # credentialed-sync fixture
```
```
No new task cards.
Appended 2 task cards to ...\AGENT_TASKS.md
```

The two cards it wrote (note the different verdicts):

| Card | Source | Labels + body | Verdict |
|------|--------|---------------|---------|
| TASK-0F2255 | github:42 | `agent-ready` label + "Acceptance: … Verify with pytest" | **`agent-ready`** (dispatchable) |
| TASK-DDBEC4 | slack | no label, "please fix when you get a chance" | **`needs-spec`** (held) |

The conservative classifier refused to mark the vague Slack ask ready. Fixture: [`sample-signals.json`](sample-signals.json).

---

## Moment 3 — The capacity throttle

**Bottleneck:** running at full agent throughput on a day you can't review well = manufacturing entropy.
**Relief:** a body-state signal that can only *lower* scope. Tell it you slept badly:

```powershell
# HEALTH_STATE.md: sleep: poor / energy: low / stress: high
python .claude/tools/health_state.py --manual HEALTH_STATE.md --print
```
```json
{
  "max_implementation_agents": 1,
  "night_shift": "off",
  "blocked_work_types": ["cross-stack refactor", "database migration", "production deploy", "multi-agent implementation"],
  "reason": "capacity signal is degraded; preserve review quality."
}
```

Now a recovered day (`sleep: excellent / energy: high / stress: low`):
```
Agent load: 3 | night_shift=dispatch-allowed | capacity signal is strong, but critic and evidence gates still apply.
```

Cap rose to 3 — but **auto-merge stays blocked even on the best day.** The system is allowed to do *less* on its own, never more. Evidence: [`evidence/policy-excellent.json`](evidence/policy-excellent.json).

---

## Moment 4 — Work gets staged without babysitting

**Bottleneck:** sitting at the desk to launch and supervise each agent.
**Relief:** a poller that obeys the health policy and is **queue-only** — it stages isolated worktrees, never launches Claude or merges.

**4a — under the degraded policy, it protects you:**
```powershell
python .claude/tools/poll_agent_ready.py --once
```
```
Night shift is off by health/scope policy.
```

**4b — under recovered capacity, the same command stages the agent-ready task:**
```
+ git worktree add -b agent/task-0f2255 ...\.worktrees\TASK-0F2255
Worktree ready: ...\.worktrees\TASK-0F2255
Prompt ready:   ...\.worktrees\TASK-0F2255\.agent-harness\TASK-0F2255-prompt.md

Start Claude Code:
cd ...\.worktrees\TASK-0F2255
claude
Then paste: Read ...\TASK-0F2255-prompt.md and execute the task contract.
```

It created an isolated git worktree, wrote the agent prompt, logged a review-queue line — then **stopped and handed you the manual command.** `returncode: 0`, no Claude launched, no merge. Evidence: [`evidence/dispatch-TASK-0F2255.json`](evidence/dispatch-TASK-0F2255.json), [`evidence/review-queue.md`](evidence/review-queue.md), [`evidence/worktree-prompt-TASK-0F2255.md`](evidence/worktree-prompt-TASK-0F2255.md).

**This staged gap — work prepared, waiting on one human review — is the attention bottleneck made small and visible.**

---

## Moment 5 — The system mines its own history

**Bottleneck:** reliving the same friction every week.
**Relief:** a Stop hook journals every session deterministically (no AI call), then a weekly miner turns recurring friction into a skill-generation prompt.

```powershell
$j = @{ session_id="demo-001"; cwd="$PWD"; last_assistant_message="hit an ambiguous spec and had to retry the failing test twice before it passed" } | ConvertTo-Json -Compress
$j | python .claude/tools/session_journal.py        # exit 0
python .claude/tools/weekly_skill_miner.py
```

The journal captured the friction automatically:
```
## Session demo-001
- friction_signals: {"\bfailing\b": 1, "\bambiguous\b": 1, "\bretry\b": 1}
```

`session_id` is `demo-001`, **not** `unknown` — confirming the Windows-PowerShell UTF-8 BOM fix holds even though piping a string here injects the BOM. Evidence: [`evidence/session-summary.md`](evidence/session-summary.md), [`evidence/weekly-skill-mining-prompt.md`](evidence/weekly-skill-mining-prompt.md).

---

## What the demo proves about the thesis

| Attention cost removed | Mechanism | Autonomy taken? |
|------------------------|-----------|-----------------|
| Checking 3 noisy apps | one-shot sync → local inbox | none — read-only, self-skips |
| Sorting actionable from noise | deterministic conservative triage | none — only drafts cards |
| Over-committing when degraded | health policy caps concurrency | **negative** — only reduces scope |
| Supervising launches | queue-only worktree staging | none — never runs Claude or merges |
| Repeating past mistakes | deterministic journaling + weekly mining | none — generates a prompt for a human |

Every step **subtracts** a demand on attention. The only thing the system does autonomously is *less* — never anything riskier. That is the kit's answer to the attention bottleneck.
