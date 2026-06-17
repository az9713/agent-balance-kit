# Tune scope with health

Gate your engineering workload — agent concurrency, the night shift, and which work types are allowed — from a health/energy policy. This is a workload guardrail, **not medical advice**. The tool only decides how much agent work to allow; it makes no health claims and stores no diagnosis.

> **Goal:** a `.agent-harness/health_state/latest_policy.json` that downstream tools read to cap agent load and decide whether the night shift runs.

## Two input paths

### Manual

```powershell
Copy-Item HEALTH_STATE.example.md HEALTH_STATE.md
```

```bash
cp HEALTH_STATE.example.md HEALTH_STATE.md
```

Edit `HEALTH_STATE.md` with today's values. The file is gitignored — keep it private.

### Wearable

Pass `--oura` with `OURA_ACCESS_TOKEN` set in `.env`. When the Oura fetch succeeds, its scores feed the same policy logic; if it fails or the token is missing, the tool falls back to the manual file (and then to a built-in default).

## Run it

```powershell
python .claude/tools/health_state.py [--manual HEALTH_STATE.md] [--oura] [--print]
```

It writes `.agent-harness/health_state/latest_policy.json` plus a timestamped `policy-<YYYYMMDD-HHMMSS>.json`. It always exits 0 and **always** produces a policy — a built-in default (`sleep: normal`, `energy: medium`, `stress: medium`) when nothing is configured. Run it from the repo root so the output lands in the right `.agent-harness/`.

## Manual keys

| Key | Values | Meaning |
| --- | --- | --- |
| `date` | a date | Recorded on the policy. |
| `sleep` | `poor` / `normal` / `excellent` | Sleep quality. |
| `energy` | `low` / `medium` / `high` | Energy level. |
| `stress` | `low` / `medium` / `high` | Stress level. |
| `readiness_score` | 0–100 (optional) | Wearable-style readiness. |
| `sleep_score` | 0–100 (optional) | Consumed by the tool, but absent from the example template — add it yourself if you want it to count. |
| `max_implementation_agents` | integer | A **cap**. It can only lower the computed agent count, never raise it. |
| `review_budget_minutes` | integer | Parsed but unused. |
| `notes` | text | Parsed but unused. |

## Policy thresholds

These are authoritative — read straight from the tool.

| Tier | Result | Triggered by |
| --- | --- | --- |
| poor | max **1** agent, `night_shift: off` | `sleep=poor` **OR** `energy=low` **OR** `stress=high` **OR** `readiness_score<60` **OR** `sleep_score<60` |
| excellent | max **3** agents, `night_shift: dispatch-allowed` | (`sleep=excellent` AND `energy=high` AND `stress≠high`) **OR** (`readiness_score≥80` AND `sleep_score≥80`) |
| normal | max **2** agents, `night_shift: queue-only` | anything else |

After the tier is chosen, `max_implementation_agents` from the manual file is applied as a cap (it can only lower the result).

## Consumers

- The `scope-control` skill.
- The `health-agent` subagent (model `haiku`).
- `poll_agent_ready.py`, which reads `night_shift` and `max_implementation_agents` from `latest_policy.json` to decide whether and how much the night shift dispatches.

## Divergence to know about

The **tool emits** `night_shift` values `off` / `queue-only` / `dispatch-allowed`. The `HEALTH_STATE.example.md` table labels the tiers `off` / `conservative` / `allowed`. The tool's emitted strings are authoritative — `poll_agent_ready.py` compares against the literal `off`, and the other strings flow through unchanged. Treat the example table's `conservative` / `allowed` wording as descriptive only; the real values written to `latest_policy.json` are `queue-only` and `dispatch-allowed`.

## Gotchas

- **The example's `max_implementation_agents: 1` pins you to one agent.** It is a cap, so copying it verbatim holds agent load at 1 regardless of how good your health inputs are. Remove or raise it if you want the computed tier to take effect.
- **The YAML fence is decorative.** The parser regex-scans every `key: value` line in `HEALTH_STATE.md`, fence or no fence. Stray prose shaped like `something: value` can be picked up as a key — keep loose text out of the file.
- **Inline comments are fine.** A `# comment` after a value is stripped correctly, so `energy: high  # slept well` parses as `energy=high`.

## Related

- [scope and health](../concepts/scope-and-health.md)
- [run the night shift](run-the-night-shift.md)
- [tools](../reference/tools.md)
- [skills & subagents](../reference/skills-and-subagents.md)
- [environment variables](../reference/environment-variables.md)
