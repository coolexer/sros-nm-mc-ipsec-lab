#!/bin/bash
# usage: sros.sh <node> "cmd1" "cmd2" ...   (or commands on stdin)
# <node> may be a short lab name (seg1) or a full container hostname.
set -euo pipefail
cd "$(dirname "$0")"
topology=${TOPOLOGY:-$(find . -maxdepth 1 -name '*.clab.yml' -print -quit)}
lab_name=${LAB_NAME:-$(awk '/^name:/ {print $2; exit}' "$topology")}
host=$1; shift
[[ $host == clab-* ]] || host="clab-$lab_name-$host"
{
  echo "environment more false"
  if [ $# -gt 0 ]; then printf '%s\n' "$@"; else cat; fi
  echo "logout"
} | timeout 45s sshpass -p 'NokiaSros1!' ssh -tt -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
      -o LogLevel=ERROR -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=3 "admin@$host" 2>&1 | tr -d '\r' \
  | awk 'found {print} /# environment more false/ {found=1} END {if (!found) exit 1}'
