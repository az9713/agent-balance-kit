#!/usr/bin/env bash
set -euo pipefail
NAME="${1:-agent-session}"
claude remote-control --name "$NAME"
