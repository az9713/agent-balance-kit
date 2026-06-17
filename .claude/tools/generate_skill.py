#!/usr/bin/env python3
"""Generate a draft Claude Code skill from repeated friction notes.

This is deterministic scaffolding, not a replacement for Claude's judgment. It creates
a reviewable SKILL.md draft that Claude/human can refine.
"""
from __future__ import annotations
import argparse, datetime as dt, os, re, textwrap
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()

KEYWORDS=['ambiguity','unclear','failed','failure','retry','back and forth','missing','manual','repeat','friction','struggle','blocked','verify']

def slugify(s: str) -> str:
    s=re.sub(r'[^a-zA-Z0-9]+','-',s.lower()).strip('-')
    return s[:60] or 'generated-skill'

def collect(paths: list[Path]) -> list[str]:
    lines=[]
    for p in paths:
        if p.is_dir():
            files=sorted(p.rglob('*.md'))[-50:]
        else:
            files=[p] if p.exists() else []
        for f in files:
            for line in f.read_text(encoding='utf-8', errors='ignore').splitlines():
                lo=line.lower()
                if any(k in lo for k in KEYWORDS):
                    lines.append(f"{f}: {line.strip()}")
    return lines[:80]

def infer_name(lines: list[str]) -> str:
    text=' '.join(lines).lower()
    if 'browser' in text or 'playwright' in text: return 'browser-evidence-check'
    if 'test' in text or 'verify' in text or 'lint' in text: return 'verification-tightening'
    if 'spec' in text or 'ambigu' in text or 'unclear' in text: return 'spec-clarifier'
    if 'mcp' in text or 'tool' in text: return 'tool-setup-check'
    return 'friction-reducer'

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--name', default=None)
    ap.add_argument('--source', action='append', default=[])
    ap.add_argument('--install', action='store_true', help='Write into .claude/skills/<slug>/SKILL.md instead of skill-drafts')
    args=ap.parse_args()
    sources=[Path(s) for s in args.source] or [ROOT/'.agent-harness'/'session-summaries', ROOT/'.agent-harness'/'weekly']
    lines=collect(sources)
    name=args.name or infer_name(lines)
    slug=slugify(name)
    outdir=(ROOT/'.claude'/'skills'/slug) if args.install else (ROOT/'.agent-harness'/'skill-drafts'/slug)
    outdir.mkdir(parents=True, exist_ok=True)
    evidence='\n'.join(f"- {line}" for line in lines[:20]) or '- No friction lines found; fill manually.'
    body=f"""---
name: {slug}
description: Auto-generated draft skill for reducing repeated workflow friction around {name.replace('-', ' ')}.
---

# {name.replace('-', ' ').title()}

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Trigger when

Use this skill when the task resembles the friction evidence below, or when the user asks for this workflow explicitly.

## Friction evidence

{evidence}

## Required inputs

- Task goal
- Existing files likely affected
- Acceptance criteria
- Verification command or evidence target

## Procedure

1. Restate the goal in one sentence.
2. Identify ambiguity before editing.
3. Convert ambiguity into a checklist.
4. Execute the smallest safe change.
5. Run the relevant verification gate.
6. Write a short evidence note under `.agent-harness/`.

## Success criteria

- One fewer clarification loop next time.
- Verification command is explicit.
- The human can review the result from the evidence artifact without reopening noisy context.

## Failure criteria

- The skill encourages broad refactors.
- The skill lacks an observable verification step.
- The skill cannot be applied in under 10 minutes of agent time.
"""
    (outdir/'SKILL.md').write_text(body, encoding='utf-8')
    print(f"Wrote {outdir/'SKILL.md'}")
    return 0
if __name__=='__main__':
    raise SystemExit(main())
