#!/bin/bash
# Reset to a clean state as if freshly cloned.
# Removes venv, pycache, and all app data/photos.

set -e
cd "$(dirname "$0")"

echo "This will permanently delete:"
echo "  - .venv/"
echo "  - __pycache__/"
echo "  - ~/Pictures/icloud-triage/  (all photos, thumbnails, app data)"
echo ""
read -p "Are you sure? (yes/N) " confirm
if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

echo "Removing .venv..."
rm -rf .venv

echo "Removing __pycache__..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "Removing ~/Pictures/icloud-triage/..."
rm -rf ~/Pictures/icloud-triage

echo "Done. Run ./start.sh to start fresh."
