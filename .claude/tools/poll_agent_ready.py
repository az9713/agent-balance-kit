#!/usr/bin/env python3
"""Recurring poller for agent-ready tasks.

Default behavior is safe queue-only: create worktree prompts and review-queue entries.
Use an external scheduler (cron / Task Scheduler) to run this every 15 minutes.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve(); HARNESS=ROOT/'.agent-harness'

def load_policy() -> dict:
    p=HARNESS/'health_state'/'latest_policy.json'
    if p.exists():
        try: return json.loads(p.read_text(encoding='utf-8'))
        except Exception: pass
    return {"max_implementation_agents": int(os.environ.get('AGENT_MAX_CONCURRENT','1')), "night_shift":"queue-only"}

def parse_tasks() -> list[dict]:
    text=(ROOT/'AGENT_TASKS.md').read_text(encoding='utf-8') if (ROOT/'AGENT_TASKS.md').exists() else ''
    tasks=[]
    for m in re.finditer(r'^- \[ \] (?P<id>TASK-[A-Za-z0-9]+) \| (?P<status>[^|]+) \| branch: (?P<branch>[^|]+) \| title: (?P<title>.+)$', text, re.M):
        block_start=m.start(); next_m=re.search(r'^- \[ \] TASK-', text[m.end():], re.M)
        block=text[block_start:m.end()+next_m.start()] if next_m else text[block_start:]
        tasks.append({**m.groupdict(), 'status':m.group('status').strip(), 'block':block})
    return tasks

def dispatched(task_id: str) -> bool:
    return (HARNESS/'dispatches'/f'{task_id}.json').exists()

def create_worktree(task: dict) -> bool:
    cmd=[sys.executable, '.claude/tools/agent_ready_loop.py', '--task', task['id']]
    res=subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    (HARNESS/'dispatches').mkdir(parents=True, exist_ok=True)
    payload={"task":task, "created_at":dt.datetime.now().isoformat(), "command":cmd, "returncode":res.returncode, "stdout":res.stdout, "stderr":res.stderr}
    (HARNESS/'dispatches'/f"{task['id']}.json").write_text(json.dumps(payload, indent=2), encoding='utf-8')
    with (HARNESS/'review-queue.md').open('a', encoding='utf-8') as f:
        f.write(f"\n- {dt.datetime.now().isoformat(timespec='seconds')} | {task['id']} | {task['title'].strip()} | queued worktree prompt\n")
    if res.returncode != 0:
        print(res.stderr); return False
    print(res.stdout.strip())
    return True

def once(max_tasks: int | None, execute: bool=False) -> int:
    policy=load_policy()
    max_allowed=int(policy.get('max_implementation_agents',1))
    if max_tasks is None: max_tasks=max_allowed
    max_tasks=max(0, min(max_tasks, max_allowed))
    if policy.get('night_shift') == 'off':
        print('Night shift is off by health/scope policy.'); return 0
    tasks=[t for t in parse_tasks() if t['status']=='agent-ready' and not dispatched(t['id'])]
    selected=tasks[:max_tasks]
    if not selected:
        print('No undispatched agent-ready tasks.'); return 0
    for t in selected:
        create_worktree(t)
        if execute:
            print(f"Execution requested, but this kit does not auto-run Claude by default. Start manually in .worktrees/{t['id']} or adapt scripts/start-task-session.ps1.")
    return 0

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--once', action='store_true')
    ap.add_argument('--loop', action='store_true')
    ap.add_argument('--every-minutes', type=int, default=15)
    ap.add_argument('--max-tasks', type=int, default=None)
    ap.add_argument('--execute', action='store_true', help='Reserved opt-in; default is queue-only')
    args=ap.parse_args()
    if args.loop:
        while True:
            once(args.max_tasks, args.execute)
            time.sleep(args.every_minutes*60)
    return once(args.max_tasks, args.execute)
if __name__=='__main__':
    raise SystemExit(main())
