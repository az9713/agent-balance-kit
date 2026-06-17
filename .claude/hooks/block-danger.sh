#!/usr/bin/env bash
set -euo pipefail
INPUT="$(cat || true)"
CMD="$(python3 - <<'PY' "$INPUT"
import json, sys
try:
    data=json.loads(sys.argv[1])
    print(data.get("tool_input",{}).get("command",""))
except Exception:
    print("")
PY
)"
case "$CMD" in
  *"rm -rf /"*|*"rm -rf ~"*|*"git reset --hard"*|*"git clean -fdx"*)
    python3 - <<'PY'
import json
print(json.dumps({
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked by Agent Balance Kit: destructive command. Ask the user explicitly."
  }
}))
PY
    ;;
esac
exit 0
