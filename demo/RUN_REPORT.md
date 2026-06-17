# Demo Run Report

A transparent account of a single live run of **Agent Balance Kit v2** — what was executed, what it is meant to demonstrate, and exactly which artifact backs each claim. Written so a reader who was not present can judge the evidence for themselves.

- **Run date:** 2026-06-16
- **Environment:** Windows 11 · Windows PowerShell + Python 3.13.5 · git 2.54
- **Repo state:** local git repo, base commit `157e2cc`, demo commit on top
- **Paths in this report and the evidence files are sanitized:** the real working directory is shown as `<KIT_ROOT>`, and no usernames, emails, machine names, tokens, or home-directory paths appear anywhere in `demo/`.

---

## 1. What this run is

A **functional, end-to-end smoke run of the kit's own tooling**, executed on a real Windows machine and captured verbatim. It is *not* a unit-test suite and *not* a benchmark. It exercises the five user-facing workflows the kit ships, in the order a real operator would hit them, and records the actual stdout and the files each tool produced.

It is also deliberately a **safe** run:

- No real Slack / Linear / GitHub / Oura credentials were supplied — the external calls were allowed to skip.
- No Claude Code session was launched autonomously.
- Nothing was merged, pushed, or deleted.
- The only network behavior was credential-less API calls that the tools themselves declined to make (recorded as `skipped`).

## 2. What it showcases

The kit's thesis (from `README.md` and `CLAUDE.md`): **agents scale, human attention does not — so the harness should remove demands on attention without ever doing autonomous, risky work.**

The run showcases that thesis as five concrete "moments," each removing one attention cost:

| # | Attention cost removed | Workflow exercised |
|---|------------------------|--------------------|
| 1 | Opening noisy apps | external signal sync → local inbox |
| 2 | Sorting actionable from noise | deterministic triage |
| 3 | Over-committing when depleted | health-based concurrency throttle |
| 4 | Supervising agent launches | queue-only worktree staging |
| 5 | Reliving past friction | session journaling + weekly mining |

The narrative walk-through with the captured stdout is in [`DEMO_EVIDENCE.md`](DEMO_EVIDENCE.md). This report is the **evidence index and transparency record** for that walk-through.

## 3. Evidence map — claim → command → artifact

Each row states a claim, the command that produced it, the committed artifact that backs it, and what in that artifact constitutes proof.

| Claim | Command | Evidence file | What proves it |
|-------|---------|---------------|----------------|
| External sources can be polled with **no credentials** and the tool degrades gracefully instead of failing | `sync_external_signals.py --all` | [`evidence/signals-latest.json`](evidence/signals-latest.json) | Three entries with `"status":"skipped"` and a reason per source; the file was still written |
| The triager is **conservative**: only label-bearing, spec-bearing asks become dispatchable | `signal_triage.py --signals demo/sample-signals.json --apply` | [`evidence/signals-latest.json`](evidence/signals-latest.json) (input fixture: [`sample-signals.json`](sample-signals.json)) + the table in `DEMO_EVIDENCE.md` | GitHub issue with `agent-ready` label + acceptance text → `agent-ready`; unlabeled Slack "please fix" → `needs-spec` |
| A degraded capacity signal **lowers** the agent cap and disables the night shift | `health_state.py --manual HEALTH_STATE.md --print` (poor input) | `DEMO_EVIDENCE.md` Moment 3 (captured JSON) | `max_implementation_agents: 1`, `night_shift: "off"`, degraded reason string |
| A strong capacity signal raises the cap but **never** unlocks auto-merge | `health_state.py --manual HEALTH_STATE.md` (excellent input) | [`evidence/policy-excellent.json`](evidence/policy-excellent.json) | `max_implementation_agents: 3`, `night_shift: "dispatch-allowed"`, blocked list still contains production deploy / no auto-merge |
| The poller **obeys** the health policy and refuses work when degraded | `poll_agent_ready.py --once` (under poor policy) | `DEMO_EVIDENCE.md` Moment 4a | stdout: `Night shift is off by health/scope policy.` |
| The poller is **queue-only**: it stages an isolated worktree but does not launch Claude or merge | `poll_agent_ready.py --once` (under excellent policy) | [`evidence/dispatch-TASK-0F2255.json`](evidence/dispatch-TASK-0F2255.json), [`evidence/review-queue.md`](evidence/review-queue.md), [`evidence/worktree-prompt-TASK-0F2255.md`](evidence/worktree-prompt-TASK-0F2255.md) | `returncode: 0`; stdout creates a git worktree and then **prints** the manual `claude` command rather than running it; a review-queue line is appended |
| Session journaling is **deterministic** and survives the Windows PowerShell UTF-8 BOM | piped JSON `\| session_journal.py` | [`evidence/session-summary.md`](evidence/session-summary.md) | `session_id` is `demo-001` (not `unknown`); `friction_signals` correctly counts `failing`, `ambiguous`, `retry` — only possible if the BOM-tolerant decode worked |
| Weekly mining turns journals into a **paste-ready** improvement prompt with no API call | `weekly_skill_miner.py` | [`evidence/weekly-skill-mining-prompt.md`](evidence/weekly-skill-mining-prompt.md) | A complete retrospective prompt embedding the session summary |

## 4. Transparency notes

**Real vs. simulated.** Everything except one input was real execution of the shipped tools:

- **Real:** the signal sync (genuinely skipped for lack of credentials), the triage logic, the health-policy computation, the poller, the git worktree creation, the journaler, and the weekly miner all ran as shipped.
- **Simulated input only:** `demo/sample-signals.json` is a hand-written fixture standing in for the JSON a *credentialed* sync would have produced. It is clearly labeled as such inside the file. It contains no real Slack/GitHub data. The triager that processed it was the real, unmodified tool.
- **Manual input:** the health signals (`poor`, then `excellent`) were typed into `HEALTH_STATE.md` by hand — the documented manual fallback when no wearable is connected. No Oura token was used.

**What was deliberately not exercised (honest gaps):**

- No live Slack / Linear / GitHub / Oura API call succeeded — only the credential-less skip path was tested. The live-credential paths remain unproven by this run.
- No Claude Code agent was actually launched in the worktree; the run stops at the staged hand-off, by design.
- The browser verification gate (`browser_verify.py`) was **not** run here (it needs Playwright + a target app); it is out of scope for this run.
- Single machine, single OS (Windows). The Unix shell mirrors were not exercised.

**Sanitization.** After the run, every absolute path in the committed `demo/` artifacts was replaced: the working directory became `<KIT_ROOT>` and the interpreter path became `python`. The git commits were authored as `demo <demo@local>`. A text search of `demo/` for usernames, home paths, `AppData`, or `Downloads` returns nothing. The kit's own `.gitignore` independently excludes the live `.agent-harness/` outputs, `HEALTH_STATE.md`, `.env`, and `.worktrees/`, so personal runtime state is not committed regardless.

**Reproducibility.** The tools used here are deterministic — no AI model calls, no randomness, no network dependency on the happy path. Re-running the same commands from the kit root on a comparable machine should produce equivalent artifacts (timestamps and the content-hashed task IDs aside). Commands are listed verbatim in `DEMO_EVIDENCE.md`.

**Limits of the evidence.** This run demonstrates that the workflows execute and behave conservatively as designed. It does **not** demonstrate end-to-end value on a real codebase (no real task was implemented), live integrations, or multi-day sustained use. Those are separate claims requiring separate evidence.

## 5. Provenance

- `157e2cc` — base: the kit as audited, including the README install-path fix (Finding #1 from the codebase report).
- demo commit — adds `demo/` (this report, `DEMO_EVIDENCE.md`, the input fixture, and the seven sanitized evidence artifacts) and the `.worktrees/` gitignore guard.

No remote is configured; nothing has been pushed. Pushing is a manual, explicit step left to the operator.
