# Onboarding

This is the patient version. If you've never used the kit and want to *understand* it — not just run it — read this once. By the end you'll know why each layer exists and how a real day flows through it.

## Start with an analogy

If you've used a CI pipeline, you already know half of this. A CI pipeline takes a commit and runs it through stages — lint, test, build — and won't let it merge until the stages pass. The Agent Balance Kit is that idea pointed at a *coding agent's whole working session* instead of a commit, plus two things CI doesn't have:

1. A **front door** (Layers 1–2) that decides what's even worth working on and turns it into a precise spec.
2. A **memory** (Layer 4) that watches how the work went and makes next week's work smoother.

In the middle (Layer 3) is the CI-like part: isolated execution and verification gates.

## The core idea, stated once

Agents scale; your attention does not. Give an agent context, verification criteria, and tools and it will loop until it satisfies them. What it cannot do is decide whether the result is actually good, actually safe, and actually what the business needed. That judgment is the scarce resource. So the kit's whole shape follows one rule: **automate everything except judgment, and spend real effort protecting the human's attention so there's judgment left to give.**

The failure mode this prevents is *review debt*. The moment you can't review every diff with taste, you're not scaling yourself — you're manufacturing entropy.

## The four abstractions and how they relate

**A task** starts life as noise — a Slack ping, a ticket, a half-formed idea. Layer 1 (the **inbox**) captures it as one line in `AGENT_TASKS.md` and labels it: ignore it, clarify it, or it's ready.

**A task contract** is what a ready task becomes. Layer 2 (the **dispatch skill**) forces your rough or dictated brief into a structure: goal, non-goals, acceptance criteria, verification commands, rollback. This is the step that makes voice safe — talking is fast, but fast vague tasks make agents fail, so the contract is the discipline that catches up to the speed.

**A worktree** is where the contract gets executed. Layer 3 gives each task its own isolated git checkout under `.worktrees/`, so three agents can work at once without trampling each other. While the agent works, **gates** check it — automatically after each edit, and blockingly when it tries to declare done — and a **critic** subagent gives a final read-only verdict.

**A journal** is the trace the work leaves behind. Layer 4's Stop hook writes a summary of every session, counting "friction signals" like *error*, *ambiguous*, *retry*. Once a week, the **skill miner** reads those summaries and asks Claude to mint one new skill that would have prevented the most friction.

The relationship: noise → inbox → contract → worktree (gated + criticized) → merge → journal → next week's skills. It's a loop, and each pass through it tightens the next.

## A realistic day, told as a story

It's Monday. You sit down for a focused 30 minutes — the only deep-desk block you'll need.

You open `AGENT_TASKS.md`, not Slack. Overnight a colleague reported that the blog generator mangles acronyms: "SSO" becomes "Sso" after the sentence-case pass. You add a line, mark it `agent-ready`, and give it acceptance criteria: *SSO stays SSO, API stays API, "HELLO WORLD" becomes "Hello world."* There are two more asks in the inbox you mark `needs-spec` — you don't understand them well enough to write criteria yet, so you don't dispatch them. That restraint is the point.

You dictate the bug into your phone while refilling coffee, then paste the transcript into Claude Code with `/agent-ready-task`. Out comes a clean contract. You run `agent_ready_loop.py --task TASK-001`; it spins up `.worktrees/TASK-001/` on its own branch and writes a prompt file. You start Claude Code there, point it at the prompt, and — this is the part that felt impossible a year ago — you close the laptop and take the dog out.

On the trail, on LTE, you open Claude on your phone. The session is still running on your desk machine, with full filesystem and tool access; remote control just lets you talk to it. You see it's started widening scope toward unrelated typography. You send: *"Stop expanding scope. Only satisfy the three acceptance criteria."* It narrows. You get a flash of insight about the edge case for all-caps single words and fire that back too. You didn't have to remember it for later; it's already applied by the time you're home.

Back at the desk, you don't blindly trust it. You ask the `critic` agent for a verdict. It returns REVISE: the fix works but there's no negative test proving "Sso" can't regress. You ask the agent to add the test. The TaskCompleted hook now passes. You ask the critic again: PASS. You merge by hand and remove the worktree.

When the session ends, the Stop hook quietly journals it. The friction count is low — one REVISE, no repeated clarification. A clean loop.

Friday, you run `weekly_skill_miner.py`. It reads the week's journals and writes a prompt. You paste it into Claude Code. It notices that three times this week you had to remind agents not to expand scope, and proposes a `scope-guard` skill that bakes that reminder into every dispatch. You let it create exactly that one skill. Next week, you won't have to say it.

## Why it works this way — three choices that surprise people

**Why a local Markdown inbox instead of reading Slack directly?** Because the kit refuses to fake credentials, and because the inbox *is* the attention firewall — the act of writing a task down as one line is what stops you from getting hijacked by the next thread. Real Slack/Linear integration is left to MCP servers you configure. See [ADR 001](../architecture/adr/001-local-inbox-before-mcp.md).

**Why is the journaler dumb (no AI)?** The Stop hook runs on every session end; making it call a model would be slow, costly, and could fail silently. Deterministic Python that counts keywords is fast and reliable. The *intelligence* is deferred to the weekly pass, which you run consciously. See [ADR 002](../architecture/adr/002-deterministic-journaling.md).

**Why won't it merge or push for me?** Because the entire value proposition collapses if you stop reviewing. "Speed requires safety": the kit deliberately keeps the merge a human act until your verification gates are *boringly* reliable. See [ADR 003](../architecture/adr/003-no-auto-merge-no-auto-push.md).

## Where to go next

A curated path from here:

1. [Signal layer](../concepts/signal-layer.md) — how the inbox and task states work.
2. [Voice-first dispatch](../concepts/voice-first-dispatch.md) — the task-contract skill in depth.
3. [Worktree execution](../concepts/worktree-execution.md) — worktrees, remote control, and the launcher.
4. [Verification gates](../concepts/verification-gates.md) — the three gates and the subagents that enforce them.
5. [Self-improving harness](../concepts/self-improving-harness.md) — journaling and weekly mining.
6. [Scope and health](../concepts/scope-and-health.md) — the v2 dimension that throttles parallelism.
7. [What's new in v2](../overview/whats-new-in-v2.md) — the additions layered around this core.
8. Then the [guides](../guides/) when you have a real task to run.
