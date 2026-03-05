#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src"
TASK_ID="smoke-task-$(date +%s)"

python3 -m full_rewrite.cli task add "$TASK_ID" "smoke"
python3 -m full_rewrite.cli task claim smoke-worker
python3 -m full_rewrite.cli task complete "$TASK_ID"
python3 -m full_rewrite.cli context add user "smoke"
python3 -m full_rewrite.cli observe
