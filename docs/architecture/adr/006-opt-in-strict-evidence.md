# ADR 006: Make the strict completion-evidence gate opt-in, off by default

**Status:** Accepted

## Context

v1 already blocks completion on Gate 1 through the `verify-before-complete` hook: an agent cannot mark a task done while lint/build/tests are red. That gate checks that code is *correct enough to compile and pass tests*; it does not demand artifacts.

v2 adds a stricter gate that demands evidence — a critic report at `.agent-harness/critic-reports/<TID>.md` (falling back to `latest.md`), and/or browser evidence at `.agent-harness/browser-evidence/*/report.md`. Forcing this on every task would block ordinary non-UI completions (a docs fix has no browser report; a trivial change may not warrant a critic pass) and would contradict the kit's graceful-degradation principle. So the strict gate defaults off, and a team escalates rigor deliberately.

## Decision

The strict evidence gate — `require_evidence.py`, run by the `require-evidence` `TaskCompleted` hook — is **off by default**. It turns on two ways:

- The sentinel file `.agent-harness/STRICT_COMPLETION`. Its presence enables **both** the critic and browser checks.
- The per-gate environment variables `AGENT_REQUIRE_CRITIC` and `AGENT_REQUIRE_BROWSER`, each enabled when set to `1`, `true`, `yes`, or `on`.

When a gate is enabled and its required artifact is missing, the hook writes the reason to stderr and exits `2`, which **blocks** completion.

## Alternatives considered

### Option A: Always-on

Pros: maximum rigor; every completion carries proof.

Cons: blocks legitimate completions that have no artifact to show (docs, config, non-UI changes); too rigid for the core loop; contradicts graceful degradation.

### Option B: Never enforce

Pros: nothing new can block a completion.

Cons: no teeth — the artifacts exist but nothing requires them, so they get skipped under time pressure.

### Option C: Opt-in with two granularities (chosen)

Pros: default behavior stays identical to v1; a team can escalate rigor per-repo (the `STRICT_COMPLETION` sentinel) or per-session (the env vars), and the env vars allow enabling a single gate.

Cons: two mechanisms for one concept (sentinel and env vars) means two places to look when debugging why a completion was blocked.

## Rationale

Keeping the gate off by default means an existing v1 workflow behaves identically after upgrading — nothing new blocks completion until someone opts in. Offering both a per-repo sentinel and per-session env vars lets the escalation match the situation: drop the sentinel into a repo where every task genuinely needs proof, or export an env var for one session working on a UI change that needs a browser report.

## Trade-offs / documented gotchas

These are gotchas to work around, not design wins:

- The `STRICT_COMPLETION` sentinel turns on **both** checks at once, with no way to select only one. To require just the critic or just the browser, use the env vars instead of the sentinel.
- The browser check is an **existence** check, not a PASS check. `require_evidence.py` looks for any `report.md` under `.agent-harness/browser-evidence/*/`; a report whose verdict is `SKIP` still satisfies the gate. The gate proves a report was produced, not that the behavior passed.
- *(Resolved in v2.)* The `require-evidence.ps1` wrapper originally had no working-directory fallback, unlike `require-evidence.sh`. Both now resolve `CLAUDE_PROJECT_DIR` with a current-directory fallback, so running the hook by hand no longer builds a broken path.
- `.env.example` ships `AGENT_REQUIRE_CRITIC=1`. The documented setup flow copies `.env.example` to `.env`, and the loader's `setdefault` makes that value live — so copying the example **enables the critic gate**, even though the code-level default with the variable unset is off. `AGENT_REQUIRE_BROWSER=0` in the same file is consistent with the off default; only the critic line flips behavior. Clear it in your `.env` if you want the v1 default. See [common issues](../../troubleshooting/common-issues.md).

## Consequences

- An un-provisioned v2 (no sentinel, no env vars, unset variables) behaves exactly like v1 on completion.
- A blocked completion can originate from the sentinel **or** an env var; check both when diagnosing.
- A passing browser gate does not mean the browser test passed — read the report's verdict.
- See also: [verification gates](../../concepts/verification-gates.md#the-strict-evidence-gate-opt-in), [hooks & settings](../../reference/hooks-and-settings.md), [ADR 003](003-no-auto-merge-no-auto-push.md), and [common issues](../../troubleshooting/common-issues.md).
