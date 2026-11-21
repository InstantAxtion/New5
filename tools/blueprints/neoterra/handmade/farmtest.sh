#!/bin/bash
# Build the hand-made Farmworks farms into stylepacks/Farmworks and run the in-game farm test on a dedicated server.
#   tools/blueprints/neoterra/handmade/farmtest.sh [name-filter]     e.g. farmtest.sh sugarcane
# One server at a time (a lock serialises concurrent callers). Prints the [farmtest] result lines.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
LOCK=/tmp/neoterra-farmtest.lock
LOG=$(mktemp /tmp/farmtest.XXXXXX.log)
(
  flock 9
  cd "$ROOT"
  python3 "$HERE/handmade.py" stylepacks/Farmworks Farmworks
  cd mod
  timeout 1500 gradle runFarmtest --offline -q -Pfarm="${1:-}" > "$LOG" 2>&1 || true
) 9>"$LOCK"
grep -E "\[farmtest\] (PASS|FAIL)|farms work|FARMTEST|Exception|Caused by" "$LOG" | head -60
echo "full log: $LOG"
