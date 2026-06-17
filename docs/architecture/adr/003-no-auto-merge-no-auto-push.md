# ADR 003: Never auto-merge or auto-push

**Status:** Accepted

## Context

The kit can take a task from inbox to a verified, critic-approved diff with very little human keystroke effort. The tempting next step is to close the loop entirely: have the agent merge the branch and push when the gates are green. That would make the system fully autonomous.

The kit's founding premise argues the opposite. Agents scale; human judgment does not. The scarce resource is the human's ability to review with taste. If the system removes the human from the merge, it removes the one checkpoint that judgment flows through.

## Decision

The kit never auto-merges PRs and never pushes to a remote unless explicitly requested. It stops at a verified diff plus an explicit critic report. The human runs `git merge` (and any push) by hand. This is encoded in `CLAUDE.md`'s safety constraints and stated throughout the docs.

## Alternatives considered

### Option A: Auto-merge when all gates pass
Pros: fully closed loop; maximum throughput.
Cons: removes the human review checkpoint precisely when volume is highest; verification gates are detection-based and imperfect, so "all gates pass" is not "correct"; one wrong auto-merge can be expensive to unwind; directly contradicts the kit's thesis.

### Option B: Auto-push to a branch, human merges
Pros: saves a step; PR is ready to review.
Cons: still a network side effect the agent takes on its own; encourages reviewing in the PR UI under time pressure rather than against the contract. Marginal benefit, real loss of control.

### Option C: Stop at a verified local diff; human merges and pushes (chosen)
Pros: keeps judgment in the loop where it's cheapest to apply; no surprising network effects; aligns the tool with its own premise.
Cons: the loop isn't fully autonomous; the human must run the final commands.

## Rationale

"Speed requires safety." The entire value proposition collapses the moment you stop reviewing every diff — at that point you're manufacturing entropy, not scaling yourself. Keeping the merge a deliberate human act is the structural guarantee that review debt can't silently accumulate. The cost (a couple of git commands) is trivial next to the risk it prevents.

## Trade-offs

We gave up full autonomy and the throughput it would unlock. We accepted that the human is the rate limiter on merges — which is exactly the kit's point, not a flaw.

## Consequences

- `verify-before-complete` blocks *completion*, but never merges. The gates inform the human; they don't act for them. See [verification gates](../../concepts/verification-gates.md).
- The kit holds no remote credentials and needs no write access to remotes ([ADR 001](001-local-inbox-before-mcp.md) keeps it credential-free).
- Guidance is to scale parallelism only once verification logs are "boringly reliable" — the autonomy you earn is *more parallel drafts to review*, never *fewer reviews*. See [parallel agents guide](../../guides/run-parallel-agents-for-a-large-feature.md).
