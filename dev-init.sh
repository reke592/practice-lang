#!/bin/bash

if ! [ -d "venv" ]; then
  python -m venv venv
fi

. ./venv/bin/activate

REQUIREMENTS_FILE='requirements.txt'

if [ -f "$REQUIREMENTS_FILE" ]; then
  pip install -r "$REQUIREMENTS_FILE"
  python -m playwright install chromium
fi
