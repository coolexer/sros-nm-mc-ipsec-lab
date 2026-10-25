#!/bin/sh
# eNB emulator: public address on eth1, inner (S1/X2) address on dummy0, strongSwan IKEv2 initiator.
set -eu
n=$1
ip addr replace "100.64.$n.2/24" dev eth1
ip link set eth1 up
ip route replace 198.51.100.0/24 via "100.64.$n.1"
ip link show dummy0 >/dev/null 2>&1 || ip link add dummy0 type dummy
ip addr replace "10.100.$n.1/32" dev dummy0
ip link set dummy0 up
if ! pgrep -x charon >/dev/null; then
  ipsec start >/var/log/ipsec-start.log 2>&1
fi
for _ in $(seq 1 30); do
  # A stale VICI socket can survive a container restart; test the service.
  if swanctl --stats >/dev/null 2>&1; then
    swanctl --load-all >/var/log/swanctl-load.log 2>&1
    exit 0
  fi
  sleep 1
done
echo 'strongSwan VICI did not become ready within 30 seconds' >&2
exit 1
