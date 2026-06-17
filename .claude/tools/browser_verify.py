#!/usr/bin/env python3
"""Playwright-based browser smoke verification with evidence artifacts.

Install when needed:
  python -m pip install playwright
  python -m playwright install chromium
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, signal, subprocess, time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()


def start_app(cmd: str | None):
    if not cmd: return None
    if os.name == 'nt':
        return subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    return subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)


def stop_app(proc):
    if not proc: return
    try:
        if os.name == 'nt': proc.terminate()
        else: os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        pass


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--config', default='.agent-harness/browser_targets.json')
    ap.add_argument('--headless', action=argparse.BooleanOptionalAction, default=True)
    args=ap.parse_args()
    cfg_path=Path(args.config)
    if not cfg_path.is_absolute(): cfg_path = ROOT / cfg_path
    if not cfg_path.exists():
        print(f"SKIP: browser config not found: {cfg_path}")
        return 0
    cfg=json.loads(cfg_path.read_text(encoding='utf-8'))
    stamp=dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    outdir=ROOT/'.agent-harness'/'browser-evidence'/stamp
    outdir.mkdir(parents=True, exist_ok=True)
    report=[]
    proc=None
    try:
        proc=start_app(cfg.get('start_command'))
        if proc:
            time.sleep(int(cfg.get('startup_wait_seconds', 5)))
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            report.append(f"# Browser verification\n\nStatus: SKIP\n\nReason: Playwright is not installed: `{e}`\n")
            (outdir/'report.md').write_text('\n'.join(report), encoding='utf-8')
            print(f"SKIP: Playwright not installed. Evidence: {outdir/'report.md'}")
            return 0
        base=cfg.get('base_url','').rstrip('/')
        failures=0
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=args.headless)
            page=browser.new_page()
            console=[]
            page.on('console', lambda msg: console.append(f"{msg.type}: {msg.text}"))
            report.append(f"# Browser verification\n\nRun: {stamp}\nBase URL: `{base}`\n")
            for target in cfg.get('targets',[]):
                name=target.get('name','unnamed')
                url=target.get('url') or (base + '/' + target.get('path','/').lstrip('/'))
                status='PASS'
                err=''
                try:
                    page.goto(url, wait_until='networkidle', timeout=int(target.get('timeout_ms', 30000)))
                    if target.get('fill'):
                        for item in target['fill']:
                            page.fill(item['selector'], item.get('value',''))
                    if target.get('click'):
                        for selector in target['click']:
                            page.click(selector)
                    if target.get('assert_text'):
                        text=target['assert_text']
                        page.get_by_text(text).first.wait_for(timeout=int(target.get('assert_timeout_ms', 10000)))
                    if target.get('assert_url_contains'):
                        if target['assert_url_contains'] not in page.url:
                            raise AssertionError(f"URL did not contain {target['assert_url_contains']}: {page.url}")
                    shot=''
                    if target.get('screenshot', True):
                        shot_path=outdir/f"{name}.png"
                        page.screenshot(path=str(shot_path), full_page=True)
                        shot=str(shot_path)
                except Exception as e:
                    failures+=1; status='FAIL'; err=str(e); shot=''
                    try:
                        shot_path=outdir/f"{name}-failure.png"; page.screenshot(path=str(shot_path), full_page=True); shot=str(shot_path)
                    except Exception: pass
                report.append(f"## {name}\n\n- status: {status}\n- url: `{url}`\n- screenshot: `{shot}`\n- error: `{err}`\n")
            browser.close()
            if console:
                (outdir/'console.log').write_text('\n'.join(console), encoding='utf-8')
                report.append(f"\nConsole log: `{outdir/'console.log'}`\n")
        (outdir/'report.md').write_text('\n'.join(report), encoding='utf-8')
        print(f"Browser evidence: {outdir/'report.md'}")
        return 1 if failures else 0
    finally:
        stop_app(proc)

if __name__=='__main__':
    raise SystemExit(main())
