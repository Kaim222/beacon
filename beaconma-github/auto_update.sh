#!/bin/bash
# BEACON Auto-Update Script
# Run via cron: 0 6 * * 1 /path/to/auto_update.sh
# Updates data weekly on Monday mornings

BEACON_DIR="$(dirname "$0")"
cd "$BEACON_DIR"

echo "$(date) — BEACON auto-update starting"

# 1. Pull fresh CTHRU spending data
python3 refresh_data.py 2>&1

# 2. Update the "Last updated" line in the HTML
TODAY=$(date +"%B %Y")
sed -i "s/Last updated: .* ·/Last updated: $TODAY ·/" index.html

echo "$(date) — BEACON auto-update complete"
echo "---"
