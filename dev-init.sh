#!/bin/bash

. ./venv/bin/activate

REQUIREMENTS_FILE='requirements.txt'

if [ -f "$REQUIREMENTS_FILE" ]; then
  pip install -r "$REQUIREMENTS_FILE"
fi

pushd ./src >/dev/null
python main.py
popd >/dev/null
