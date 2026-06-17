# Verify in the browser

Produce real browser click-through evidence — screenshots, a console log, and a `report.md` — before completing any UI, auth, or routing task. The `browser_verify.py` tool drives a headless Chromium session against your running app and writes a timestamped evidence folder.

> **Goal:** a `.agent-harness/browser-evidence/<timestamp>/report.md` that shows each target actually loaded and passed, with screenshots to back it.

## Steps

### 1. Install Playwright

```powershell
python -m pip install playwright
python -m playwright install chromium
```

This pulls the Playwright Python package and downloads the Chromium build it drives. See [prerequisites](../getting-started/prerequisites.md#v2-feature-dependencies).

### 2. Create your browser targets config

```powershell
Copy-Item .agent-harness/browser_targets.example.json .agent-harness/browser_targets.json
```

```bash
cp .agent-harness/browser_targets.example.json .agent-harness/browser_targets.json
```

Then edit `.agent-harness/browser_targets.json` to describe your app and the pages to check.

### 3. Run the verification

```powershell
python .claude/tools/browser_verify.py --config .agent-harness/browser_targets.json
```

Headless is the default. Add `--no-headless` to watch the run in a visible window.

## Config keys

| Key | Default | Meaning |
| --- | --- | --- |
| `start_command` | none | Shell command to launch the app. Omit to test an already-running server. |
| `startup_wait_seconds` | 5 | Seconds to wait after launching `start_command` before navigating. |
| `base_url` | empty | Prefixed to each target's `path`. |
| `targets[]` | — | Array of pages to verify. |
| `targets[].name` | `unnamed` | Used for the screenshot filename and report heading. |
| `targets[].url` or `targets[].path` | — | Absolute URL, or a path joined to `base_url`. |
| `targets[].timeout_ms` | 30000 | Navigation timeout. |
| `targets[].fill[]` | — | `{selector, value}` pairs filled before assertions. |
| `targets[].click[]` | — | Selectors clicked in order. |
| `targets[].assert_text` | — | Text that must appear on the page. |
| `targets[].assert_timeout_ms` | 10000 | Timeout for the `assert_text` wait. |
| `targets[].assert_url_contains` | — | Substring the final URL must contain. |
| `targets[].screenshot` | true | Capture a full-page screenshot. |

## Output

Each run writes `.agent-harness/browser-evidence/<YYYYMMDD-HHMMSS>/` containing:

- `<name>.png` per passing target (or `<name>-failure.png` when a target throws),
- `console.log` (only when the page emitted console messages),
- `report.md` with one section per target listing status, URL, screenshot path, and error.

The tool prints the evidence path. Exit codes:

| Exit | Meaning |
| --- | --- |
| 0 | All targets passed, **or** the run was skipped (no config, or Playwright missing). |
| 1 | One or more targets failed. |

## Integration

`verify.py` runs browser verification when you pass `--browser`, or in full mode (`--full`), and only when `.agent-harness/browser_targets.json` exists. The [`browser-verification` skill](../reference/skills-and-subagents.md) and the `browser-tester` subagent drive the same tool, so the evidence is identical whichever entry point you use.

## Gotchas

- **A SKIP returns exit 0.** A missing config file or a missing Playwright install produces a SKIP `report.md` and exit 0. A caller that treats exit 0 as "verified" gets a false pass. Confirm the report says PASS, not SKIP.
- **The strict evidence gate checks existence, not the verdict.** `require_evidence.py` checks only that a `report.md` *exists*, not that it says PASS — so a SKIP report satisfies the gate. Treat a SKIP as "not verified," never as "passed." See [verification gates](../concepts/verification-gates.md#the-strict-evidence-gate-opt-in).
- **App lifecycle differs by OS.** On Windows the tool launches `start_command` in a new process group and terminates it on exit; on POSIX it starts a session group and sends `SIGTERM`. A `start_command` that detaches its own children may outlive the run on either platform.

## Related

- [verification gates](../concepts/verification-gates.md#gate-2-browser-evidence)
- [tools](../reference/tools.md)
- [skills & subagents](../reference/skills-and-subagents.md)
- [prerequisites](../getting-started/prerequisites.md#v2-feature-dependencies)
