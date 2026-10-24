[13:31:17] # T1b — force-switchover to seg1
[13:31:17] Ожидание: back to seg1
[13:31:17] --- state: before
[13:31:17]   seg1: act=standby prot=notReady cur=seg2 inst=2 dorm=0
[13:31:18]   seg2: act=active prot=notReady cur=seg2 inst=2 dorm=0
[13:31:18]   seg3: act=standby prot=notReady cur=seg2 inst=0 dorm=2
[13:31:18]   ipmpls best: 198.51.100.1/32->seg2  10.100.1.1/32->seg2  
[13:31:19]   IKE SPI: enb1=1ffdc8f143b431d6_i* enb2=433cf9af7679ac50_i*

[/]
A:admin@seg2-a# tools perform redundancy multi-chassis mc-ipsec force-switchover domain 1 to 10.0.0.1 now

[/]
A:admin@seg2-a# logout
[13:31:24] ok after 1 s: seg1 becomes OA
[13:31:46]   enb1 traffic: lost/max-gap = 3/440ms  (244 packets transmitted, 241 received, 1.22951% packet loss, time 24518ms)
[13:31:46]   enb2 traffic: lost/max-gap = 3/436ms  (240 packets transmitted, 237 received, 1.25% packet loss, time 24077ms)
[13:31:46] --- state: after
[13:31:46]   seg1: act=active prot=notReady cur=seg1 inst=2 dorm=0
[13:31:47]   seg2: act=standby prot=notReady cur=seg1 inst=2 dorm=0
[13:31:47]   seg3: act=standby prot=notReady cur=seg1 inst=0 dorm=2
[13:31:48]   ipmpls best: 198.51.100.1/32->seg1  10.100.1.1/32->seg1  
[13:31:48]   IKE SPI: enb1=1ffdc8f143b431d6_i* enb2=433cf9af7679ac50_i*
[13:31:48] --- MC_REDUNDANCY events (log 99, newest first)
  seg1 2026/10/24 11:31:23.961 "Multi-chassis ipsec domain 1 local activity state changed from standby to active because the force-switchover tool was used. The active router in the domain is 10.0.0.1."
  seg1 2026/10/24 11:31:04.692 "Multi-chassis ipsec domain 1 local activity state changed from notEligible to standby because the local isa tunnel group became eligible. The active router in the domain is 10.0.0.2."
  seg1 2026/10/24 11:30:49.769 "Multi-chassis ipsec domain 1 local activity state changed from standby to notEligible because the local isa tunnel group became ineligible. The active router in the domain is 10.0.0.2."
  seg1 2026/10/24 11:30:49.740 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg1 2026/10/24 11:30:49.740 "Multi-chassis ipsec domain 1 local activity state changed from active to standby because the force-switchover tool was used. The active router in the domain is 10.0.0.2."
  seg2 2026/10/24 11:31:39.014 "Multi-chassis ipsec domain 1 local activity state changed from notEligible to standby because the local isa tunnel group became eligible. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 11:31:23.989 "Multi-chassis ipsec domain 1 local activity state changed from standby to notEligible because the local isa tunnel group became ineligible. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 11:31:23.961 "Multi-chassis ipsec domain 1 local activity state changed from active to standby because the force-switchover tool was used. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 11:30:49.739 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg2 2026/10/24 11:30:49.739 "Multi-chassis ipsec domain 1 local activity state changed from standby to active because the force-switchover tool was used. The active router in the domain is 10.0.0.2."
  seg3 2026/10/24 11:31:23.961 "Multi-chassis ipsec domain 1 has elected a new active router because the force-switchover tool was used. The local router's activity state is standby. The active router in the domain is 10.0.0.1."
  seg3 2026/10/24 11:30:49.739 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg3 2026/10/24 11:30:49.739 "Multi-chassis ipsec domain 1 has elected a new active router because the force-switchover tool was used. The local router's activity state is standby. The active router in the domain is 10.0.0.2."
  seg3 2026/10/24 11:30:40.646 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg3 2026/10/24 11:30:30.620 "Multi-chassis ipsec domain 1 local activity state changed from notEligible to standby because the local isa tunnel group became eligible. The active router in the domain is 10.0.0.1."
[13:31:51] RESULT: expected OA=seg1 actual OA=seg1, IKE SA kept=yes, verdict=PASS
