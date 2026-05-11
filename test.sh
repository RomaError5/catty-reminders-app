#!/bin/bash
set -e
cd "$(dirname "$0")"

export PYTHONPATH="$PWD:$PYTHONPATH"

if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
fi

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

if [ -d "tests" ]; then
    pytest tests --maxfail=1 --disable-warnings -q
else
    echo "No tests found, skipping"
fi