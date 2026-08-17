#!/bin/bash

pushd "$(dirname $0)"

  mkdir -p venv

  python -m venv venv

  . ./venv/bin/activate

  REQUIREMENTS_FILE='requirements.txt'

  if [ -f "$REQUIREMENTS_FILE" ]; then
    pip install -r "$REQUIREMENTS_FILE"
    pip install --no-cache-dir playwright
    python -m playwright install chromium
  fi

popd