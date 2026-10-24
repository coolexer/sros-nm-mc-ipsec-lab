#!/bin/bash
# usage: sros.sh <node> "cmd1" "cmd2" ...   (or commands on stdin)
# <node> may be a short lab name (seg1) or a full container hostname.
host=$1; shift
[[ $host == clab-* ]] || host="clab-nm-mc-ipsec-$host"
{
  echo "environment more false"
  if [ $# -gt 0 ]; then printf '%s\n' "$@"; else cat; fi
  echo "logout"
} | sshpass -p 'NokiaSros1!' ssh -tt -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
      -o LogLevel=ERROR -o ConnectTimeout=10 "admin@$host" 2>&1 | tr -d '\r' \
  | awk 'found {print} /# environment more false/ {found=1}'
