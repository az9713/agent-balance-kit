#!/usr/bin/env python3
"""Convert normalized signals into AGENT_TASKS.md draft cards.

This deterministic triager is intentionally conservative. It creates `needs-spec`
unless the signal contains explicit acceptance/verification markers or comes from an
`agent-ready` issue label.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
SIGNALS=ROOT/'.agent-harness'/'signals'/'latest.json'
TASKS=ROOT/'AGENT_TASKS.md'


def slug_id(source: str, external_id: str, title: str) -> str:
    h=hashlib.sha1(f"{source}:{external_id}:{title}".encode()).hexdigest()[:6].upper()
    return f"TASK-{h}"


def existing_text() -> str:
    return TASKS.read_text(encoding='utf-8') if TASKS.exists() else "# Agent Tasks\n\n## Tasks\n\n"


def classify(sig: dict) -> str:
    labels={str(x).lower() for x in sig.get('labels',[]) if x}
    body=(sig.get('body') or '') + '\n' + (sig.get('title') or '')
    if 'agent-ready' in labels and re.search(r'(acceptance|verify|test|done when|definition of done)', body, re.I):
        return 'agent-ready'
    if 'agent-ready' in labels:
        return 'needs-spec'
    if re.search(r'(bug|fix|broken|regression|todo|please|need|should)', body, re.I):
        return 'needs-spec'
    return 'signal'


def card(sig: dict) -> str:
    title=(sig.get('title') or 'Untitled signal').strip().replace('\n',' ')
    tid=slug_id(sig.get('source','unknown'), str(sig.get('id','')), title)
    status=classify(sig)
    branch=f"agent/{tid.lower()}"
    source=f"{sig.get('source','unknown')}:{sig.get('id','')}"
    url=sig.get('url') or ''
    body=(sig.get('body') or '').strip().replace('\r','')
    excerpt=' '.join(body.split())[:350]
    return f"""- [ ] {tid} | {status} | branch: {branch} | title: {title[:100]}
  - source: {source} {url}
  - goal: [fill] Convert the source ask into one observable outcome.
  - raw_excerpt: {excerpt}
  - acceptance:
    - [fill] Add concrete acceptance criteria before dispatch.
  - verification:
    - [fill] Add exact verification command before dispatch.
"""


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--signals', default=str(SIGNALS))
    ap.add_argument('--tasks', default=str(TASKS))
    ap.add_argument('--apply', action='store_true', help='Append to AGENT_TASKS.md')
    ap.add_argument('--max-new', type=int, default=5)
    args=ap.parse_args()
    signals_path=Path(args.signals); tasks_path=Path(args.tasks)
    if not signals_path.exists():
        print(f"No signals file: {signals_path}"); return 1
    payload=json.loads(signals_path.read_text(encoding='utf-8'))
    text=tasks_path.read_text(encoding='utf-8') if tasks_path.exists() else "# Agent Tasks\n\n## Tasks\n\n"
    new=[]
    for sig in payload.get('signals',[]):
        if sig.get('status') in {'skipped','error'}: continue
        c=card(sig)
        tid=re.search(r'- \[ \] (TASK-[A-F0-9]+)', c).group(1)
        if tid in text: continue
        new.append(c)
        if len(new)>=args.max_new: break
    if not new:
        print('No new task cards.'); return 0
    out='\n'.join(new)+'\n'
    if args.apply:
        with tasks_path.open('a', encoding='utf-8') as f:
            f.write('\n'+out)
        print(f"Appended {len(new)} task cards to {tasks_path}")
    else:
        print(out)
    return 0
if __name__=='__main__':
    raise SystemExit(main())
