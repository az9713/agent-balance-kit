#!/usr/bin/env python3
"""Strict completion gate for critic/browser evidence.

Enabled when either `.agent-harness/STRICT_COMPLETION` exists or env
AGENT_REQUIRE_CRITIC/AGENT_REQUIRE_BROWSER is set.
"""
from __future__ import annotations
import os, re, subprocess, sys, json
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
HARNESS=ROOT/'.agent-harness'

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

def enabled(name: str) -> bool:
    if (HARNESS/'STRICT_COMPLETION').exists(): return True
    return os.environ.get(name, '').lower() in {'1','true','yes','on'}

def task_id() -> str | None:
    env=os.environ.get('AGENT_TASK_ID')
    if env: return env
    try:
        b=subprocess.check_output(['git','branch','--show-current'], text=True, stderr=subprocess.DEVNULL).strip()
        m=re.search(r'(TASK-[A-Za-z0-9]+|task-[A-Za-z0-9]+)', b)
        if m: return m.group(1).upper()
    except Exception:
        pass
    m=re.search(r'(TASK-[A-Za-z0-9]+|task-[A-Za-z0-9]+)', str(ROOT))
    return m.group(1).upper() if m else None

def latest_file(path: Path, pattern: str) -> Path | None:
    if not path.exists(): return None
    files=list(path.rglob(pattern))
    return max(files, key=lambda p:p.stat().st_mtime) if files else None

def main() -> int:
    load_env_file()
    tid=task_id()
    messages=[]
    if enabled('AGENT_REQUIRE_CRITIC'):
        candidates=[]
        if tid:
            candidates += [HARNESS/'critic-reports'/f'{tid}.md']
        candidates += [HARNESS/'critic-reports'/'latest.md']
        if not any(p.exists() for p in candidates):
            messages.append(f"Missing critic report for {tid or 'current task'} under .agent-harness/critic-reports/.")
    if enabled('AGENT_REQUIRE_BROWSER'):
        rep=latest_file(HARNESS/'browser-evidence','report.md')
        if not rep:
            messages.append("Missing browser evidence under .agent-harness/browser-evidence/*/report.md.")
    if messages:
        sys.stderr.write("\n".join(messages)+"\n")
        return 2
    print(json.dumps({"systemMessage":"Evidence gate passed or not enabled."}))
    return 0
if __name__=='__main__':
    raise SystemExit(main())
