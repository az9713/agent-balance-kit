#!/usr/bin/env python3
"""One-command conservative night-shift cycle.

Runs health policy, optional external signal sync, triage, and worktree queue creation.
It does not auto-merge or deploy.
"""
from __future__ import annotations
import argparse, os, subprocess, sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
TOOLS = ROOT / ".claude" / "tools"


def run(cmd):
    print('>',' '.join(str(c) for c in cmd))
    return subprocess.run(cmd, cwd=ROOT, text=True).returncode


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--sync', action='store_true', help='Sync external signals first')
    ap.add_argument('--oura', action='store_true', help='Try Oura API for health policy')
    ap.add_argument('--max-tasks', type=int, default=None)
    args=ap.parse_args()
    run([sys.executable, str(TOOLS/'health_state.py')] + (['--oura'] if args.oura else []))
    if args.sync:
        run([sys.executable, str(TOOLS/'sync_external_signals.py'),'--all'])
        run([sys.executable, str(TOOLS/'signal_triage.py'),'--apply'])
    cmd=[sys.executable, str(TOOLS/'poll_agent_ready.py'),'--once']
    if args.max_tasks is not None: cmd += ['--max-tasks', str(args.max_tasks)]
    return run(cmd)
if __name__=='__main__':
    raise SystemExit(main())
