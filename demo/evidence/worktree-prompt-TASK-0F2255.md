# Agent Task TASK-0F2255

## Title

Sentence-case headings without mangling acronyms
  - source: github:42 https://github.com/owner/repo/issues/42
  - goal: [fill] Convert the source ask into one observable outcome.
  - raw_excerpt: Headings get fully lower-cased and SSO becomes Sso. Acceptance: SSO stays SSO, API stays API, 'HELLO WORLD' becomes 'Hello world'. Verify with: python -m pytest tests/test_sentence_case.py -q
  - acceptance:
    - [fill] Add concrete acceptance criteria before dispatch.
  - verification:
    - [fill] Add exact verification command before dispatch.

## Task contract from AGENT_TASKS.md

- [ ] TASK-0F2255 | agent-ready | branch: agent/task-0f2255 | title: Sentence-case headings without mangling acronyms
  - source: github:42 https://github.com/owner/repo/issues/42
  - goal: [fill] Convert the source ask into one observable outcome.
  - raw_excerpt: Headings get fully lower-cased and SSO becomes Sso. Acceptance: SSO stays SSO, API stays API, 'HELLO WORLD' becomes 'Hello world'. Verify with: python -m pytest tests/test_sentence_case.py -q
  - acceptance:
    - [fill] Add concrete acceptance criteria before dispatch.
  - verification:
    - [fill] Add exact verification command before dispatch.



## Instructions for Claude Code

1. Read CLAUDE.md if present.
2. Restate acceptance criteria.
3. Implement the smallest coherent change.
4. Run the listed verification commands.
5. Run `python .claude/tools/verify.py --fast` if this scaffold is present.
6. Produce a critic-ready final report:
   - files changed
   - tests run
   - acceptance mapping
   - risks
   - next command
