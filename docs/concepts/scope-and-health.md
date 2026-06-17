# Scope and health

The kit can gate how many implementation agents run, whether the night shift dispatches, and which work types are allowed, from a single health/energy policy. This is a workload guardrail — it lowers throughput on a degraded day and raises it on a strong one. It is **not medical advice**; it only modulates engineering load.

## Where it sits

Scope-and-health is a cross-cutting dimension, not one of the four layers. It does not produce signals, dispatch tasks, or verify code. It modulates Layer 3 throughput: the policy it produces caps the number of implementation agents and decides whether the [night shift](worktree-execution.md#the-night-shift) is allowed to dispatch.

## Data flow

```text
HEALTH_STATE.md (manual)   ─┐
                            ├─→ health_state.py ─→ .agent-harness/health_state/latest_policy.json
Oura (OURA_ACCESS_TOKEN)   ─┘                              │
                                                           ├─→ poll_agent_ready.py (night shift)
                                                           └─→ scope-control skill / health-agent subagent
```

`health_state.py` reads one of two inputs. With `--oura` and `OURA_ACCESS_TOKEN` set, it pulls daily sleep / readiness / activity from the Oura API. Otherwise (or if Oura is unavailable) it reads the manual `HEALTH_STATE.md`. If neither is present it falls back to a built-in normal default. It always writes `.agent-harness/health_state/latest_policy.json` (plus a timestamped copy) and always exits `0`.

Downstream, `poll_agent_ready.py` reads `latest_policy.json` to decide how many tasks to dispatch and whether to run at all; the scope-control skill and health-agent subagent read the same file to reason about the day's load.

## The policy

`build_policy()` classifies the day as **poor**, **excellent**, or **normal**, in that priority order (poor wins over excellent if both somehow apply), and maps each to a cap and a night-shift mode:

| Class | max_implementation_agents | night_shift | Trigger conditions |
|-------|--------------------------:|-------------|--------------------|
| poor | 1 | `off` | `sleep=poor` **or** `energy=low` **or** `stress=high` **or** `readiness_score < 60` **or** `sleep_score < 60` |
| normal | 2 | `queue-only` | none of the poor or excellent conditions hold |
| excellent | 3 | `dispatch-allowed` | (`sleep=excellent` **and** `energy=high` **and** `stress≠high`) **or** (`readiness_score ≥ 80` **and** `sleep_score ≥ 80`) |

`poll_agent_ready.py` compares the policy's `night_shift` value against the literal string `"off"`: when it is `off`, the poller prints that the night shift is off and dispatches nothing. Any other value lets it proceed (it does not separately distinguish `queue-only` from `dispatch-allowed` — the kit's poller is queue-only by design and does not auto-run Claude).

The policy also lists `blocked_work_types` per class (for example, a poor day blocks cross-stack refactors and production deploys); these are advisory text for the scope-control skill and health-agent to honor, not enforced by the poller.

## Terminology divergence

The tool emits `off` / `queue-only` / `dispatch-allowed`. These strings are **authoritative** — `poll_agent_ready.py` compares against `"off"`. `HEALTH_STATE.example.md`'s table describes the modes as `off` / `conservative` / `allowed`; that wording is **descriptive only** and does not match the emitted strings. When you read code or the policy JSON, trust `off` / `queue-only` / `dispatch-allowed`.

## max_implementation_agents is a cap, not a target

If `HEALTH_STATE.md` sets `max_implementation_agents`, it is applied as `min(class_default, your_value)` — it can only **lower** the class default, never raise it. Setting `max_implementation_agents: 5` on an excellent day still yields 3; setting `1` on an excellent day yields 1. Use it to hold scope down, not to override a poor-day cap upward.

## Cross-links

- [Tune scope with health](../guides/tune-scope-with-health.md)
- [Run the night shift](../guides/run-the-night-shift.md)
- [Worktree execution](worktree-execution.md#the-night-shift)
- [`health_state.py` reference](../reference/tools.md#health_statepy)
- [Skills & subagents — scope control](../reference/skills-and-subagents.md#scope-control)
- [Environment variables](../reference/environment-variables.md)
