#!/bin/sh

set -e
set -u

WOLBOT_DIR='/opt/wolbot'
WOLBOT_SCRIPT='wolbot.py'
PYTHON_VENV='wolbot_venv'

printf '[LAUNCHER] Changing working directory to "%s".\n' "$WOLBOT_DIR"
cd "$WOLBOT_DIR"

printf '[LAUNCHER] Activating virtual environment "%s".\n' "$PYTHON_VENV"
. "$WOLBOT_DIR/$PYTHON_VENV/bin/activate"

printf '[LAUNCHER] Launching script "%s".\n' "$WOLBOT_SCRIPT"
set +e
python3 "$WOLBOT_DIR/$WOLBOT_SCRIPT"

printf '[LAUNCHER] Script quit with exit code %s.\n' "$?"
