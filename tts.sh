#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -x "$SCRIPT_DIR/.venv/bin/python" ]; then
  "$SCRIPT_DIR/setup.sh"
fi
export PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$SCRIPT_DIR/.venv/bin/python" -m doubao_md_tts "$@"
