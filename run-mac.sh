#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -x ".venv/bin/python" ]; then
  ./setup-mac.sh
fi
.venv/bin/python app.py
