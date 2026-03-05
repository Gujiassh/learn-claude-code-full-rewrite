#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src"

python3 -m full_rewrite.cli task add smoke-task "smoke"
python3 -m full_rewrite.cli task claim smoke-worker
python3 -m full_rewrite.cli task complete smoke-task
python3 -m full_rewrite.cli context add user "smoke"
python3 -m full_rewrite.cli observe
