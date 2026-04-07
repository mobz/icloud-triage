#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

if ! python3 -c "import flask" 2>/dev/null; then
  echo "Installing dependencies..."
  pip install -r requirements.txt
fi

echo "Starting iCloud Downloader at http://localhost:5001"
python3 app.py
