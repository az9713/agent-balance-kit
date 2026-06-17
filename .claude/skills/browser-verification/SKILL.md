---
name: browser-verification
description: Run real browser click-through smoke checks and produce evidence before a task can be considered complete.
---

# Browser Verification Skill

Use this when a task changes UI, auth, routing, forms, dashboards, browser-visible content, or frontend data flow.

## Required artifact

Create or update:

```text
.agent-harness/browser_targets.json
```

Use `.agent-harness/browser_targets.example.json` as the template.

## Run

```bash
python .claude/tools/browser_verify.py --config .agent-harness/browser_targets.json
```

## Evidence standard

The report must include:

- URL visited.
- Assertion performed.
- Screenshot path when screenshots are enabled.
- PASS/FAIL/SKIP status.
- Browser console errors, if available.

## Completion rule

For UI/auth/routing tasks, do not claim completion unless browser evidence exists under:

```text
.agent-harness/browser-evidence/<timestamp>/report.md
```
