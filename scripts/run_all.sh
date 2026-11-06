#!/usr/bin/env bash
# Run one booking per account file in parallel, e.g. lmu.env and tum.env.
# Usage:  scripts/run_all.sh                 (all *.env files in the repo root)
#         scripts/run_all.sh lmu.env tum.env
cd "$(dirname "$0")/.."
files=("$@")
[ ${#files[@]} -eq 0 ] && files=(*.env)
for f in "${files[@]}"; do
  [ -f "$f" ] || { echo "skip: $f not found"; continue; }
  name="${f%.env}"
  ENV_FILE="$f" venv/bin/python main.py 2>&1 | sed -u "s/^/[$name] /" &
done
wait
