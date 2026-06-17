#!/usr/bin/env python3
"""
Project-aware verification runner.

Fast mode:
- runs lightweight checks likely to finish quickly.
Full mode:
- adds build commands when detected.

Outputs JSONL to .agent-harness/verify-log.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
LOG = ROOT / ".agent-harness" / "verify-log.jsonl"

def run(cmd: list[str], timeout: int = 120) -> dict[str, Any]:
    start = time.time()
    try:
        p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        return {
            "cmd": cmd,
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "seconds": round(time.time() - start, 3),
            "stdout_tail": p.stdout[-4000:],
            "stderr_tail": p.stderr[-4000:],
        }
    except FileNotFoundError as e:
        return {"cmd": cmd, "ok": False, "returncode": 127, "seconds": 0, "stderr_tail": str(e)}
    except subprocess.TimeoutExpired:
        return {"cmd": cmd, "ok": False, "returncode": 124, "seconds": timeout, "stderr_tail": f"Timed out after {timeout}s"}

def node_scripts() -> dict[str, str]:
    pkg = ROOT / "package.json"
    if not pkg.exists():
        return {}
    try:
        return json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {})
    except Exception:
        return {}

def python_compile_check() -> dict[str, Any]:
    files = [p for p in ROOT.rglob("*.py") if ".venv" not in p.parts and "node_modules" not in p.parts and ".git" not in p.parts]
    errors = []
    for p in files[:250]:
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as e:
            errors.append(f"{p.relative_to(ROOT)}: {e}")
    return {
        "cmd": ["python", "-m", "py_compile", "<project .py files>"],
        "ok": not errors,
        "returncode": 0 if not errors else 1,
        "seconds": 0,
        "stdout_tail": f"Checked {min(len(files), 250)} Python files.",
        "stderr_tail": "\n".join(errors[-50:]),
    }

def detect_commands(full: bool) -> list[list[str]]:
    cmds: list[list[str]] = []
    scripts = node_scripts()
    npm = "npm.cmd" if os.name == "nt" else "npm"
    if scripts:
        for name in ("lint", "typecheck", "test"):
            if name in scripts:
                cmds.append([npm, "run", name])
        if full and "build" in scripts:
            cmds.append([npm, "run", "build"])

    # Python checks
    if (ROOT / "pyproject.toml").exists() or (ROOT / "requirements.txt").exists() or any(ROOT.rglob("*.py")):
        if shutil.which("ruff"):
            cmds.append(["ruff", "check", "."])
        if (ROOT / "tests").exists() or any(ROOT.rglob("test_*.py")):
            cmds.append([sys.executable, "-m", "pytest", "-q"])

    return cmds

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--browser", action="store_true", help="Run browser verification if .agent-harness/browser_targets.json exists")
    args = parser.parse_args()
    full = args.full and not args.fast

    LOG.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    if any(ROOT.rglob("*.py")):
        results.append(python_compile_check())

    for cmd in detect_commands(full=full):
        results.append(run(cmd, timeout=300 if full else 180))

    browser_cfg = ROOT / ".agent-harness" / "browser_targets.json"
    if (args.browser or full) and browser_cfg.exists():
        results.append(run([sys.executable, ".claude/tools/browser_verify.py", "--config", str(browser_cfg)], timeout=600))

    if not results:
        results.append({
            "cmd": ["verify"],
            "ok": True,
            "returncode": 0,
            "seconds": 0,
            "stdout_tail": "No known verification commands detected. Add package.json scripts, tests/, pyproject.toml, or customize .claude/tools/verify.py.",
            "stderr_tail": ""
        })

    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": str(ROOT),
        "mode": "full" if full else "fast",
        "ok": all(r["ok"] for r in results),
        "results": results,
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0 if record["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
