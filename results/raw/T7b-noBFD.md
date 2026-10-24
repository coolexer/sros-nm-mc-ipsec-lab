[13:55:09] # T7b — force-switchover to seg1
[13:55:09] Ожидание: back to seg1
[13:55:09] --- state: before
[13:55:09]   seg1: act=standby prot=nominal cur=seg2 inst=2 dorm=0
[13:55:09]   seg2: act=active prot=nominal cur=seg2 inst=2 dorm=0
[13:55:10]   seg3: act=standby prot=nominal cur=seg2 inst=0 dorm=2
[13:55:10]   ipmpls best: 198.51.100.1/32->seg2  10.100.1.1/32->seg2  
[13:55:10]   IKE SPI: enb1=1ffdc8f143b431d6_i* enb2=433cf9af7679ac50_i*
[13:55:16] force-switchover on seg2 -> seg1

[/]
A:admin@seg2-a# tools perform redundancy multi-chassis mc-ipsec force-switchover domain 1 to 10.0.0.1 now

[/]
A:admin@seg2-a# logout
[13:55:17] ok after 1 s: seg1 becomes OA
[13:55:38]   enb1 traffic: lost/max-gap = 3/454ms  (253 packets transmitted, 250 received, 1.18577% packet loss, time 25412ms)
[13:55:39]   enb2 traffic: lost/max-gap = 1/217ms  (252 packets transmitted, 251 received, 0.396825% packet loss, time 25303ms)
[13:55:39] --- state: after
[13:55:40]   seg1: act=active prot=notReady cur=seg1 inst=2 dorm=0
[13:55:40]   seg2: act=standby prot=notReady cur=seg1 inst=2 dorm=0
[13:55:41]   seg3: act=standby prot=notReady cur=seg1 inst=0 dorm=2
[13:55:41]   ipmpls best: 198.51.100.1/32->seg1  10.100.1.1/32->seg1  
[13:55:42]   IKE SPI: enb1=1ffdc8f143b431d6_i* enb2=433cf9af7679ac50_i*
[13:55:42] --- MC_REDUNDANCY events (log 99, newest first)
  seg1 2026/10/24 11:55:16.553 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg1 2026/10/24 11:55:16.553 "Multi-chassis ipsec domain 1 local activity state changed from standby to active because the force-switchover tool was used. The active router in the domain is 10.0.0.1."
  seg1 2026/10/24 11:54:40.881 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg1 2026/10/24 11:53:46.561 "ipsec back in sync with peer 10.0.0.3."
  seg1 2026/10/24 11:53:46.561 "ipsec back in sync with peer 10.0.0.2."
  seg2 2026/10/24 11:55:31.437 "Multi-chassis ipsec domain 1 local activity state changed from notEligible to standby because the local isa tunnel group became eligible. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 11:55:16.570 "Multi-chassis ipsec domain 1 local activity state changed from standby to notEligible because the local isa tunnel group became ineligible. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 11:55:16.553 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg2 2026/10/24 11:55:16.553 "Multi-chassis ipsec domain 1 local activity state changed from active to standby because the force-switchover tool was used. The active router in the domain is 10.0.0.1."
  seg2 2026/10/24 11:54:40.879 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg3 2026/10/24 11:55:16.553 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg3 2026/10/24 11:55:16.553 "Multi-chassis ipsec domain 1 has elected a new active router because the force-switchover tool was used. The local router's activity state is standby. The active router in the domain is 10.0.0.1."
  seg3 2026/10/24 11:54:40.881 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg3 2026/10/24 11:53:10.671 "The Sync status of peer 10.0.0.1 changed to inSync"
  seg3 2026/10/24 11:51:59.859 "Multi-chassis ipsec domain 1 has elected a new active router because an inter-chassis link went down. The local router's activity state is standby. The active router in the domain is 10.0.0.2."
[13:55:44] RESULT: expected OA=seg1 actual OA=seg1, IKE SA kept=yes, verdict=PASS
