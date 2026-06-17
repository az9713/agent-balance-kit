#!/usr/bin/env python3
"""
Claude Code Stop hook journaler.

Reads hook JSON from stdin, extracts transcript metadata, and appends a lightweight
session summary. This is deterministic and does not call an AI model.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
OUTDIR = ROOT / ".agent-harness" / "session-summaries"

FRICTION_PATTERNS = [
    r"\berror\b", r"\bfailed\b", r"\bfailing\b", r"\btimeout\b", r"\bambiguous\b",
    r"\bpermission\b", r"\bblocked\b", r"\bretry\b", r"\bcan't\b", r"\bcannot\b",
    r"\bnot found\b", r"\bhallucinat", r"\bunclear\b"
]

def read_tail(path: Path, max_lines: int = 200) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-max_lines:]
    except Exception:
        return []

def count_patterns(text: str) -> dict[str, int]:
    return {p: len(re.findall(p, text, flags=re.I)) for p in FRICTION_PATTERNS if re.search(p, text, flags=re.I)}

def main() -> int:
    # Read stdin as bytes and decode with utf-8-sig so a leading BOM is stripped.
    # Windows PowerShell prepends a UTF-8 BOM when piping a string to a native
    # process (the `$inputJson | python ...` line in session-journal.ps1), which
    # otherwise makes json.loads() fail and silently degrades every journal entry.
    raw = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
    try:
        data: dict[str, Any] = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {"parse_error": True, "raw_tail": raw[-1000:]}

    transcript_path = data.get("transcript_path")
    last_msg = str(data.get("last_assistant_message", ""))[-2000:]
    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", str(ROOT))

    transcript_tail = []
    if transcript_path:
        transcript_tail = read_tail(Path(os.path.expanduser(transcript_path)))
    transcript_text = "\n".join(transcript_tail)
    friction = count_patterns(transcript_text + "\n" + last_msg)

    today = dt.datetime.now().strftime("%Y-%m-%d")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / f"{today}.md"

    block = f"""
## Session {session_id}

- time: {dt.datetime.now().isoformat(timespec='seconds')}
- cwd: `{cwd}`
- transcript: `{transcript_path or 'not provided'}`
- friction_signals: `{json.dumps(friction, ensure_ascii=False)}`

### Last assistant message tail

```text
{last_msg if last_msg else '[empty or unavailable]'}
```

### Retrospective questions for weekly skill mining

- Where did the agent require repeated clarification?
- Which verification command was missing or unreliable?
- Which instruction did the human repeat?
- Which task shape deserves a reusable skill?
- Which MCP server, subagent, or hook would have shortened the loop?

"""
    with out.open("a", encoding="utf-8") as f:
        f.write(block)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
