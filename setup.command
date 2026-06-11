#!/bin/bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display dialog "Python 3 was not found. Install Python 3.10 or newer from python.org, then run setup.command again." with title "Local Data Masking Tool" buttons {"OK"} default button "OK" with icon stop'
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

osascript -e 'display dialog "Setup complete. Open run.command to launch the app." with title "Local Data Masking Tool" buttons {"OK"} default button "OK"'
