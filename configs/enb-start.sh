#!/bin/sh
# eNB emulator: public address on eth1, inner (S1/X2) address on dummy0, strongSwan IKEv2 initiator.
n=$1
ip addr add 100.64.$n.2/24 dev eth1
ip link set eth1 up
ip route add 198.51.100.0/24 via 100.64.$n.1
ip link add dummy0 type dummy
ip addr add 10.100.$n.1/32 dev dummy0
ip link set dummy0 up
ipsec start >/var/log/ipsec-start.log 2>&1
for _ in $(seq 1 30); do
  [ -S /var/run/charon.vici ] && break
  sleep 1
done
swanctl --load-all >/var/log/swanctl-load.log 2>&1
