#!/usr/bin/env python3
"""Create agent-load policy from manual HEALTH_STATE.md or Oura API data.

No medical advice. This only gates engineering workload.
"""
from __future__ import annotations

import argparse, datetime as dt, json, os, re, urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
OUTDIR = ROOT / ".agent-harness" / "health_state"


def load_env_file(path: Path | None = None) -> None:
    if path is None:
        path = ROOT / '.env'
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k,v=line.split('=',1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def parse_manual(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    # Accept fenced yaml or plain key:value lines.
    data = {}
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*(?:#.*)?$", line)
        if m:
            key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
            if val.lower() in {"true","false"}:
                val = val.lower()=="true"
            else:
                try:
                    val = int(val)
                except ValueError:
                    pass
            data[key]=val
    return data


def oura_get(endpoint: str, token: str, start_date: str, end_date: str) -> dict:
    url = f"https://api.ouraring.com/v2/usercollection/{endpoint}?start_date={start_date}&end_date={end_date}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_oura() -> dict:
    token = os.environ.get("OURA_ACCESS_TOKEN")
    if not token:
        return {"source":"oura", "available": False, "error":"OURA_ACCESS_TOKEN not set"}
    today = dt.date.today()
    start = (today - dt.timedelta(days=2)).isoformat()
    end = today.isoformat()
    out = {"source":"oura", "available": True, "date": end, "raw": {}}
    for endpoint in ["daily_sleep", "daily_readiness", "daily_activity"]:
        try:
            out["raw"][endpoint] = oura_get(endpoint, token, start, end)
        except Exception as e:
            out["raw"][endpoint] = {"error": str(e)}
    return out


def latest_score(items: list, keys: list[str]) -> int | None:
    if not items:
        return None
    for item in reversed(items):
        for k in keys:
            val = item.get(k)
            if isinstance(val, (int, float)):
                return int(val)
            if isinstance(val, dict):
                # Some APIs put score in nested contributors.
                for sub in ["score", "value"]:
                    if isinstance(val.get(sub), (int,float)):
                        return int(val[sub])
    return None


def normalize_oura(raw: dict) -> dict:
    data = raw.get("raw", {})
    sleep_items = data.get("daily_sleep", {}).get("data", []) if isinstance(data.get("daily_sleep"), dict) else []
    readiness_items = data.get("daily_readiness", {}).get("data", []) if isinstance(data.get("daily_readiness"), dict) else []
    activity_items = data.get("daily_activity", {}).get("data", []) if isinstance(data.get("daily_activity"), dict) else []
    readiness_score = latest_score(readiness_items, ["score", "readiness_score"])
    sleep_score = latest_score(sleep_items, ["score", "sleep_score"])
    activity_score = latest_score(activity_items, ["score", "activity_score"])
    return {
        "source":"oura",
        "date": raw.get("date", dt.date.today().isoformat()),
        "readiness_score": readiness_score,
        "sleep_score": sleep_score,
        "activity_score": activity_score,
        "available": raw.get("available", False),
        "raw_errors": {k:v.get("error") for k,v in data.items() if isinstance(v, dict) and v.get("error")}
    }


def build_policy(data: dict) -> dict:
    sleep = str(data.get("sleep", "")).lower()
    energy = str(data.get("energy", "")).lower()
    stress = str(data.get("stress", "")).lower()
    readiness = data.get("readiness_score")
    sleep_score = data.get("sleep_score")
    explicit_max = data.get("max_implementation_agents")

    poor = sleep == "poor" or energy == "low" or stress == "high"
    if isinstance(readiness, int) and readiness < 60:
        poor = True
    if isinstance(sleep_score, int) and sleep_score < 60:
        poor = True

    excellent = sleep == "excellent" and energy == "high" and stress != "high"
    if isinstance(readiness, int) and readiness >= 80 and isinstance(sleep_score, int) and sleep_score >= 80:
        excellent = True

    if poor:
        max_agents = 1
        night_shift = "off"
        blocked = ["cross-stack refactor", "database migration", "production deploy", "multi-agent implementation"]
        reason = "capacity signal is degraded; preserve review quality."
    elif excellent:
        max_agents = 3
        night_shift = "dispatch-allowed"
        blocked = ["auto-merge", "production deploy without human approval"]
        reason = "capacity signal is strong, but critic and evidence gates still apply."
    else:
        max_agents = 2
        night_shift = "queue-only"
        blocked = ["auto-merge", "production deploy", "broad refactor without mini-spec"]
        reason = "normal capacity; queue or dispatch only low-risk work."

    if isinstance(explicit_max, int) and explicit_max > 0:
        max_agents = min(max_agents, explicit_max)

    return {
        "date": data.get("date", dt.date.today().isoformat()),
        "source": data.get("source", "manual"),
        "max_implementation_agents": max_agents,
        "night_shift": night_shift,
        "blocked_work_types": blocked,
        "reason": reason,
        "inputs": data,
    }


def main() -> int:
    load_env_file()
    ap = argparse.ArgumentParser()
    ap.add_argument("--manual", default="HEALTH_STATE.md", help="Manual HEALTH_STATE.md path")
    ap.add_argument("--oura", action="store_true", help="Try Oura API first if OURA_ACCESS_TOKEN is set")
    ap.add_argument("--print", action="store_true", help="Print policy JSON")
    args = ap.parse_args()

    data = {}
    if args.oura:
        raw = fetch_oura()
        if raw.get("available"):
            data = normalize_oura(raw)
        else:
            data = {"source":"oura", "date":dt.date.today().isoformat(), "error":raw.get("error")}
    if not data or data.get("error"):
        manual = parse_manual(Path(args.manual))
        data = {"source":"manual", "date":dt.date.today().isoformat(), **manual} if manual else {"source":"default", "date":dt.date.today().isoformat(), "sleep":"normal", "energy":"medium", "stress":"medium"}

    policy = build_policy(data)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    (OUTDIR / f"policy-{stamp}.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
    (OUTDIR / "latest_policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
    if args.print:
        print(json.dumps(policy, indent=2))
    else:
        print(f"Wrote {OUTDIR / 'latest_policy.json'}")
        print(f"Agent load: {policy['max_implementation_agents']} | night_shift={policy['night_shift']} | {policy['reason']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
