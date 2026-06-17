# Agent Tasks Inbox

Use this file as a low-noise replacement for Slack/Linear/GitHub browsing.

Only tasks marked `agent-ready` should be dispatched.

## Ready tasks

- [ ] TASK-001 | agent-ready | branch: agent/task-001 | title: Fix acronym-preserving sentence case
  - repo_area: src/text
  - goal: Sentence-case headings without mangling acronyms.
  - non_goals:
    - Do not change markdown rendering.
    - Do not change unrelated typography rules.
  - acceptance:
    - SSO remains SSO.
    - API remains API.
    - "HELLO WORLD" becomes "Hello world".
  - verification:
    - python -m pytest tests/test_sentence_case.py -q
  - rollback:
    - Revert the branch.

## Candidate tasks needing clarification

- [ ] TASK-002 | needs-spec | title: Improve onboarding
  - missing:
    - exact screen
    - target user path
    - acceptance criteria
