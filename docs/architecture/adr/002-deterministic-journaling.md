# ADR 002: Make session journaling deterministic, defer intelligence to a weekly pass

**Status:** Accepted

## Context

Layer 4 mines your session history for friction. The raw material is Claude Code's JSONL transcripts, which are long, noisy, and not meant for direct AI consumption. There are two places intelligence could live: in a per-session step that summarizes each session as it ends, or in a periodic step that analyzes accumulated summaries.

The per-session step runs on the `Stop` hook — once for *every* session, automatically. Anything on that path must be fast, cheap, and impossible to fail in a way that disrupts the session.

## Decision

Split the layer in two:

1. **Journaling** (`session_journal.py`, Stop hook) is plain deterministic Python. It counts keyword "friction signals" and writes a structured Markdown summary. It makes **no model call** and always exits 0.
2. **Mining** (`weekly_skill_miner.py`) is a deterministic *prompt generator*. It assembles recent summaries into a prompt that *you* paste into Claude Code consciously. The model intelligence lives here, triggered on demand.

## Alternatives considered

### Option A: AI summarization on every Stop hook
Pros: richer per-session summaries; less noise to mine later.
Cons: a model call on every session end is slow and costly; a flaky call could hang or disrupt session stop; turns a lifecycle hook into a billable, failable dependency.

### Option B: Point Claude directly at raw JSONL weekly
Pros: no journaling code at all.
Cons: raw JSONL is verbose and full of junk; it blows context budget and buries the friction signal. The talk's Q&A explicitly raises this as a real problem.

### Option C: Deterministic journal + on-demand weekly mining (chosen)
Pros: the hot path (every session) is fast and reliable; intelligence is applied deliberately, once, against pre-cleaned summaries; cost and failure are bounded and visible.
Cons: per-session summaries are coarse (keyword counts, not semantic); the friction taxonomy is a heuristic, not understanding.

## Rationale

The constraint that decides it: the Stop hook runs unconditionally and must never become a liability. Deterministic code satisfies that absolutely. Cleaning the data deterministically first also makes the weekly model pass cheaper and sharper than pointing it at raw transcripts. Intelligence is most valuable when applied consciously, not sprinkled on every session end.

## Trade-offs

We gave up semantic per-session summaries. The journals record *that* friction occurred (keyword counts) and a message tail, not a nuanced narrative. The weekly model pass recovers the nuance when it matters, against curated input.

## Consequences

- The journaler's friction-signal list is a tunable heuristic; adding signals is a code edit. See [tools](../../reference/tools.md#session_journalpy).
- Mining cadence is a human choice (weekly default, daily under load).
- The kit never silently spends model tokens; every model call is one you trigger. See [self-improving harness](../../concepts/self-improving-harness.md).
