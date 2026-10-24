[13:51:50] # T7 — Отказ узла OA (docker kill seg1)
[13:51:50] Ожидание: BFD detect -> seg2 OA
[13:51:50] --- state: before
[13:51:50]   seg1: act=active prot=nominal cur=seg1 inst=2 dorm=0
[13:51:51]   seg2: act=standby prot=nominal cur=seg1 inst=2 dorm=0
[13:51:51]   seg3: act=standby prot=nominal cur=seg1 inst=0 dorm=2
[13:51:51]   ipmpls best: 198.51.100.1/32->seg1  10.100.1.1/32->seg1  
[13:51:52]   IKE SPI: enb1=1ffdc8f143b431d6_i* enb2=433cf9af7679ac50_i*
[13:51:58] seg1 killed
[13:52:03] ok after 5 s: seg2 becomes OA
[13:52:25]   enb1 traffic: lost/max-gap = 236/102ms  (274 packets transmitted, 38 received, 86.1314% packet loss, time 30479ms)
[13:52:25]   enb2 traffic: lost/max-gap = 238/102ms  (271 packets transmitted, 33 received, 87.8229% packet loss, time 30208ms)
[13:52:25] --- state: after
[13:52:25]   seg1: DOWN
[13:52:26]   seg2: act=active prot=notReady cur=seg2 inst=2 dorm=0
[13:52:26]   seg3: act=standby prot=notReady cur=seg2 inst=0 dorm=2
[13:52:26]   ipmpls best: 198.51.100.1/32->seg1  10.100.1.1/32->seg1  
[13:52:27]   IKE SPI: enb1=1ffdc8f143b431d6_i* enb2=433cf9af7679ac50_i*
[13:52:27] --- MC_REDUNDANCY events (log 99, newest first)
  seg2 2026/10/24 11:51:59.857 "Multi-chassis ipsec domain 1 local activity state changed from standby to active because an inter-chassis link went down. The active router in the domain is 10.0.0.2."
  seg2 2026/10/24 11:51:59.838 "The Sync status of peer 10.0.0.1 changed to outOfSync"
  seg2 2026/10/24 11:51:59.789 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg2 2026/10/24 11:47:34.968 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg2 2026/10/24 11:43:59.229 "Multi-chassis ipsec domain 1 local activity state changed from notEligible to standby because the local isa tunnel group became eligible. The active router in the domain is 10.0.0.1."
  seg3 2026/10/24 11:51:59.859 "Multi-chassis ipsec domain 1 has elected a new active router because an inter-chassis link went down. The local router's activity state is standby. The active router in the domain is 10.0.0.2."
  seg3 2026/10/24 11:51:59.333 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg3 2026/10/24 11:51:59.333 "The Sync status of peer 10.0.0.1 changed to outOfSync"
  seg3 2026/10/24 11:47:34.968 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg3 2026/10/24 11:43:44.144 "Multi-chassis ipsec domain 1 has elected a new active router because the force-switchover tool was used. The local router's activity state is standby. The active router in the domain is 10.0.0.1."
[13:52:29] RESULT: expected OA=seg2 actual OA=seg2, IKE SA kept=yes, verdict=PASS
