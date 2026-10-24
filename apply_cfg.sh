#!/bin/bash
# usage: apply_cfg.sh <cfg-file> <node> [node...]   -- merge an MD-CLI snippet in private mode and commit
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
  errs=$(grep -E "MINOR|MAJOR|CRITICAL" <<<"$out")
  if [ -n "$errs" ]; then echo "[$node] FAILED"; echo "$errs"; else echo "[$node] committed"; fi
done
