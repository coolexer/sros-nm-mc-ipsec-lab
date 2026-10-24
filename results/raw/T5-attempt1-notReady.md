[13:45:48] # T5 — Отказ 1 из 2 линков seg1-seg2
[13:45:48] Ожидание: no switchover, nominal, no loss
[13:45:48] --- state: before
[13:45:48]   seg1: act=active prot=notReady cur=seg1 inst=2 dorm=0
[13:45:49]   seg2: act=standby prot=notReady cur=seg1 inst=2 dorm=0
[13:45:49]   seg3: act=standby prot=notReady cur=seg1 inst=0 dorm=2
[13:45:49]   ipmpls best: 198.51.100.1/32->seg1  10.100.1.1/32->seg1  
[13:45:50]   IKE SPI: enb1=1ffdc8f143b431d6_i* enb2=433cf9af7679ac50_i*
[13:45:55] cfg seg1: /configure port 1/1/1 admin-state disable
[13:46:25]   seg1->seg2 adjacency: Admin State           : Up              Oper State            : Up
[13:46:25]   seg1 sync seg2: DB Sync State           : inSync
[13:46:27]   enb1 traffic: lost/max-gap = 2/106ms  (346 packets transmitted, 344 received, 0.578035% packet loss, time 34756ms)
[13:46:27]   enb2 traffic: lost/max-gap = 2/209ms  (344 packets transmitted, 342 received, 0.581395% packet loss, time 34548ms)
[13:46:27] --- state: after
[13:46:28]   seg1: act=active prot=notReady cur=seg1 inst=2 dorm=0
[13:46:28]   seg2: act=standby prot=notReady cur=seg1 inst=2 dorm=0
[13:46:29]   seg3: act=standby prot=notReady cur=seg1 inst=0 dorm=2
[13:46:29]   ipmpls best: 198.51.100.1/32->seg1  10.100.1.1/32->seg1  
[13:46:29]   IKE SPI: enb1=1ffdc8f143b431d6_i* enb2=433cf9af7679ac50_i*
[13:46:29] --- MC_REDUNDANCY events (log 99, newest first)
  seg1 2026/10/24 11:43:44.146 "Multi-chassis ipsec domain 1 local activity state changed from standby to active because the force-switchover tool was used. The active router in the domain is 10.0.0.1."
  seg1 2026/10/24 11:39:10.253 "ipsec back in sync with peer 10.0.0.3."
  seg1 2026/10/24 11:39:10.253 "ipsec back in sync with peer 10.0.0.2."
  seg1 2026/10/24 11:38:52.604 "Multi-chassis ipsec domain 1 local activity state changed from notEligible to standby because the local isa tunnel group became eligible. The active router in the domain is 10.0.0.2."
  seg1 2026/10/24 11:38:42.251 "Multi-chassis ipsec domain 1 local activity state changed from discovery to notEligible because peer contact was established while the local isa tunnel group is down. The active router in the domain is 10.0.0.2."
  seg2 2026/10/24 11:43:59.229 "Multi-chassis ipsec domain 1 local activity state changed from notEligible to standby because the local isa tunnel group became eligible. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 11:43:44.180 "Multi-chassis ipsec domain 1 local activity state changed from standby to notEligible because the local isa tunnel group became ineligible. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 11:43:44.151 "Multi-chassis ipsec domain 1 local activity state changed from active to standby because the force-switchover tool was used. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 11:38:37.730 "Multi-chassis ipsec domain 1 local activity state changed from standby to active because an inter-chassis link went down. The active router in the domain is 10.0.0.2."
  seg2 2026/10/24 11:38:28.868 "Multi-chassis ipsec domain 1 local activity state changed from notEligible to standby because the local isa tunnel group became eligible. The active router in the domain is 10.0.0.1."
  seg3 2026/10/24 11:43:44.144 "Multi-chassis ipsec domain 1 has elected a new active router because the force-switchover tool was used. The local router's activity state is standby. The active router in the domain is 10.0.0.1."
  seg3 2026/10/24 11:38:37.731 "Multi-chassis ipsec domain 1 has elected a new active router because an inter-chassis link went down. The local router's activity state is standby. The active router in the domain is 10.0.0.2."
  seg3 2026/10/24 11:38:13.874 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg3 2026/10/24 11:38:13.874 "Multi-chassis ipsec domain 1 has elected a new active router because a revertive switchover occurred. The local router's activity state is standby. The active router in the domain is 10.0.0.1."
  seg3 2026/10/24 11:35:03.002 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
[13:46:32] RESULT: expected OA=seg1 actual OA=seg1, IKE SA kept=yes, verdict=FAIL
