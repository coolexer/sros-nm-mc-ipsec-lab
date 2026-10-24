[14:40:31] # T7b — force-switchover to seg1
[14:40:31] Ожидание: back to seg1
[14:40:31] --- state: before
[14:40:32]   seg1: act=standby prot=nominal cur=seg2 inst=2 dorm=0
[14:40:32]   seg2: act=active prot=nominal cur=seg2 inst=2 dorm=0
[14:40:33]   seg3: act=standby prot=nominal cur=seg2 inst=0 dorm=2
[14:40:33]   ipmpls best: 198.51.100.1/32->seg2  10.100.1.1/32->seg2  
[14:40:34]   IKE SPI: enb1=123925ae997e133c_i* enb2=3095f5042cafc595_i*
[14:40:40] force-switchover on seg2 -> seg1

[/]
A:admin@seg2-a# tools perform redundancy multi-chassis mc-ipsec force-switchover domain 1 to 10.0.0.1 now

[/]
A:admin@seg2-a# logout
[14:40:41] ok after 1 s: seg1 becomes OA
[14:41:03]   enb1 traffic: lost/max-gap = 3/478ms  (261 packets transmitted, 258 received, 1.14943% packet loss, time 26226ms)
[14:41:03]   enb2 traffic: lost/max-gap = 3/451ms  (259 packets transmitted, 256 received, 1.1583% packet loss, time 26031ms)
[14:41:03] --- state: after
[14:41:04]   seg1: act=active prot=notReady cur=seg1 inst=2 dorm=0
[14:41:04]   seg2: act=standby prot=notReady cur=seg1 inst=2 dorm=0
[14:41:05]   seg3: act=standby prot=notReady cur=seg1 inst=0 dorm=2
[14:41:05]   ipmpls best: 198.51.100.1/32->seg1  10.100.1.1/32->seg2  
[14:41:06]   IKE SPI: enb1=123925ae997e133c_i* enb2=3095f5042cafc595_i*
[14:41:06] --- MC_REDUNDANCY events (log 99, newest first)
  seg1 2026/10/24 12:40:40.529 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg1 2026/10/24 12:40:40.529 "Multi-chassis ipsec domain 1 local activity state changed from standby to active because the force-switchover tool was used. The active router in the domain is 10.0.0.1."
  seg1 2026/10/24 12:40:07.127 "ipsec back in sync with peer 10.0.0.3."
  seg1 2026/10/24 12:40:07.127 "ipsec back in sync with peer 10.0.0.2."
  seg1 2026/10/24 12:40:02.600 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg2 2026/10/24 12:40:55.522 "Multi-chassis ipsec domain 1 local activity state changed from notEligible to standby because the local isa tunnel group became eligible. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 12:40:40.589 "Multi-chassis ipsec domain 1 local activity state changed from standby to notEligible because the local isa tunnel group became ineligible. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 12:40:40.530 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg2 2026/10/24 12:40:40.530 "Multi-chassis ipsec domain 1 local activity state changed from active to standby because the force-switchover tool was used. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 12:40:02.598 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg3 2026/10/24 12:40:40.534 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg3 2026/10/24 12:40:40.534 "Multi-chassis ipsec domain 1 has elected a new active router because the force-switchover tool was used. The local router's activity state is standby. The active router in the domain is 10.0.0.1."
  seg3 2026/10/24 12:40:02.600 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg3 2026/10/24 12:39:30.436 "The Sync status of peer 10.0.0.1 changed to inSync"
  seg3 2026/10/24 12:38:18.864 "The Sync status of peer 10.0.0.1 changed to outOfSync"
[14:41:08] RESULT: expected OA=seg1 actual OA=seg1, IKE SA kept=yes, verdict=PASS
