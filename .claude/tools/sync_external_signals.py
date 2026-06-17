#!/usr/bin/env python3
"""Best-effort external signal sync for Slack, Linear, and GitHub.

This is intentionally credential-optional and safe. It writes normalized signals to
.agent-harness/signals/latest.json. It does not dispatch agents or edit code.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
OUTDIR = ROOT/'.agent-harness'/'signals'


def load_env_file(path: Path | None = None) -> None:
    if path is None: path = ROOT / '.env'
    if not path.exists(): return
    for line in path.read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def request_json(url: str, headers: dict | None = None, data: bytes | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {}, data=data)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode('utf-8'))


def sync_github() -> list[dict]:
    repo=os.environ.get('GITHUB_REPOSITORY')
    label=os.environ.get('GITHUB_LABEL','agent-ready')
    token=os.environ.get('GITHUB_TOKEN')
    if not repo:
        return [{"source":"github", "status":"skipped", "reason":"GITHUB_REPOSITORY not set"}]
    url=f"https://api.github.com/repos/{repo}/issues?state=open&labels={urllib.parse.quote(label)}&per_page=50"
    headers={"Accept":"application/vnd.github+json", "User-Agent":"agent-balance-kit"}
    if token: headers['Authorization']=f"Bearer {token}"
    try:
        data=request_json(url, headers)
    except Exception as e:
        return [{"source":"github", "status":"error", "reason":str(e)}]
    out=[]
    for issue in data:
        if 'pull_request' in issue: continue
        out.append({
            "source":"github", "kind":"issue", "id":str(issue.get('number')), "title":issue.get('title',''),
            "url":issue.get('html_url',''), "body":issue.get('body') or '', "labels":[lbl.get('name') for lbl in issue.get('labels', [])],
            "status":"raw"
        })
    return out


def sync_linear() -> list[dict]:
    key=os.environ.get('LINEAR_API_KEY')
    label=os.environ.get('LINEAR_LABEL','agent-ready')
    team=os.environ.get('LINEAR_TEAM_KEY')
    if not key:
        return [{"source":"linear", "status":"skipped", "reason":"LINEAR_API_KEY not set"}]
    # Conservative query: pull recent open issues with the label name. Users can narrow by LINEAR_TEAM_KEY.
    team_filter = f', team: {{ key: {{ eq: "{team}" }} }}' if team else ''
    query = f"""
    query AgentReadyIssues {{
      issues(first: 50, filter: {{ labels: {{ name: {{ eq: \"{label}\" }} }}, state: {{ type: {{ neq: \"completed\" }} }}{team_filter} }}) {{
        nodes {{ id identifier title description url priority createdAt updatedAt labels {{ nodes {{ name }} }} }}
      }}
    }}
    """
    try:
        data=request_json('https://api.linear.app/graphql', {"Authorization":key, "Content-Type":"application/json"}, json.dumps({"query":query}).encode())
    except Exception as e:
        return [{"source":"linear", "status":"error", "reason":str(e)}]
    out=[]
    for node in data.get('data',{}).get('issues',{}).get('nodes',[]) or []:
        out.append({
            "source":"linear", "kind":"issue", "id":node.get('identifier') or node.get('id'), "title":node.get('title',''),
            "url":node.get('url',''), "body":node.get('description') or '', "priority":node.get('priority'),
            "labels":[lbl.get('name') for lbl in node.get('labels',{}).get('nodes',[])], "status":"raw"
        })
    return out


def sync_slack(since_hours: int) -> list[dict]:
    token=os.environ.get('SLACK_BOT_TOKEN')
    channels=[c.strip() for c in os.environ.get('SLACK_CHANNEL_IDS','').replace(';',',').split(',') if c.strip()]
    mention=os.environ.get('SLACK_USER_MENTION','')
    if not token or not channels:
        return [{"source":"slack", "status":"skipped", "reason":"SLACK_BOT_TOKEN or SLACK_CHANNEL_IDS not set"}]
    oldest=str(time.time()-since_hours*3600)
    headers={"Authorization":f"Bearer {token}", "Content-Type":"application/x-www-form-urlencoded"}
    out=[]
    for ch in channels:
        params=urllib.parse.urlencode({"channel":ch,"oldest":oldest,"limit":"100"}).encode()
        try:
            data=request_json('https://slack.com/api/conversations.history', headers, params)
        except Exception as e:
            out.append({"source":"slack", "status":"error", "channel":ch, "reason":str(e)}); continue
        if not data.get('ok'):
            out.append({"source":"slack", "status":"error", "channel":ch, "reason":data.get('error')}); continue
        for msg in data.get('messages',[]):
            text=msg.get('text','')
            if mention and mention not in text:
                continue
            out.append({
                "source":"slack", "kind":"message", "id":msg.get('ts'), "title":text[:90].replace('\n',' '),
                "body":text, "channel":ch, "ts":msg.get('ts'), "url":"", "status":"raw"
            })
    return out


def main() -> int:
    load_env_file()
    ap=argparse.ArgumentParser()
    ap.add_argument('--github', action='store_true')
    ap.add_argument('--linear', action='store_true')
    ap.add_argument('--slack', action='store_true')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--since-hours', type=int, default=24)
    args=ap.parse_args()
    use_all=args.all or not (args.github or args.linear or args.slack)
    signals=[]
    if use_all or args.github: signals += sync_github()
    if use_all or args.linear: signals += sync_linear()
    if use_all or args.slack: signals += sync_slack(args.since_hours)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    payload={"synced_at":dt.datetime.now(dt.timezone.utc).isoformat(), "signals":signals}
    (OUTDIR/'latest.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(f"Wrote {OUTDIR/'latest.json'} with {len(signals)} items")
    skipped=[s for s in signals if s.get('status') in {'skipped','error'}]
    if skipped:
        print("Skipped/errors:")
        for s in skipped:
            print(f"- {s.get('source')}: {s.get('reason')}")
    return 0
if __name__=='__main__':
    raise SystemExit(main())
