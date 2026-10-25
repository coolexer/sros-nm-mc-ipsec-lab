#!/bin/bash
# usage: apply_cfg.sh <cfg-file> <node> [node...]   -- merge an MD-CLI snippet in private mode and commit
set -euo pipefail
cd "$(dirname "$0")"
cfg=$1; shift
for node in "$@"; do
  out=$({
    echo "edit-config private"
    cat "$cfg"
    echo "exit all"
    echo "commit"
    echo "quit-config"
  } | ./sros.sh "$node")
  if [ -z "$out" ] || grep -qE '\b(MINOR|MAJOR|CRITICAL):' <<<"$out"; then
    echo "[$node] FAILED"; echo "$out"; exit 1
  fi
  echo "[$node] committed"
done
