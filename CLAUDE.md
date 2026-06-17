# Project Agent Operating Manual

## Operating principle

Human judgment is the bottleneck. Agents may do the minutiae, but the human remains responsible for task selection, specification quality, risk judgment, and final merge.

## Required loop

For any non-trivial change:

1. Restate the task contract.
2. Identify touched files and likely risk.
3. Use a git worktree or a clean branch.
4. Make the smallest coherent change.
5. Run verification gates.
6. Ask a critic subagent to review the diff.
7. Summarize:
   - what changed
   - what was verified
   - what remains risky
   - exact next command for the human

## Delegation rule

Do not delegate implementation of an area where the human lacks enough understanding to review the result. When the task touches an unfamiliar subsystem, first create a learning/research pass and teach the human the architecture before editing.

## Verification gates

- Gate 1: code-level verification: lint, build, unit tests.
- Gate 2: behavior-level verification: run the app, use browser or CLI to demonstrate the behavior.
- Gate 3: judgment-level verification: critic pass against acceptance criteria and risk.

## Stop rule

Do not say a task is done unless:

- Acceptance criteria are explicitly mapped to evidence.
- Verification commands and results are listed.
- Known limitations are named.
- If verification could not run, the reason is stated and the next command is provided.

## Safety constraints

- Do not modify `.env`, credential files, SSH keys, browser cookies, or production secrets.
- Do not run destructive shell commands without explicit permission.
- Do not auto-merge PRs.
- Do not push to remote unless explicitly requested.
