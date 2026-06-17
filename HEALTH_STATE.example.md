# Health State Example

Copy this to `HEALTH_STATE.md` when you do not have Oura/Garmin/Fitbit/Apple Health integrated.
Do **not** commit your personal `HEALTH_STATE.md`.

```yaml
date: 2026-06-11
sleep: normal        # poor | normal | excellent
energy: medium      # low | medium | high
stress: medium      # low | medium | high
readiness_score: 70 # optional 0-100 if a wearable provides it
max_implementation_agents: 1
review_budget_minutes: 45
notes: "Manual fallback. Keep scope boring if sleep is poor."
```

Policy mapping used by `.claude/tools/health_state.py`:

| Condition | Max implementation agents | Night shift | Cross-stack refactors |
|---|---:|---|---|
| sleep poor or energy low | 1 | off | blocked |
| sleep normal and energy medium | 2 | conservative | human approval |
| sleep excellent and energy high | 3 | allowed | still requires spec + critic |
