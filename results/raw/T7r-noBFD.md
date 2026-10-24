[13:52:50] # T7r — Возврат seg1 после отказа
[13:52:50] Ожидание: non-revertive: seg2 stays OA, no loss
[13:52:50] --- state: before
[13:52:51]   seg1: act=discovery prot=notReady cur=0.0.0.0 inst=0 dorm=0
[13:52:51]   seg2: act=active prot=notReady cur=seg2 inst=2 dorm=0
[13:52:51]   seg3: act=standby prot=notReady cur=seg2 inst=0 dorm=2
[13:52:52]   ipmpls best: 198.51.100.1/32->seg1  10.100.1.1/32->seg1  
[13:52:52]   IKE SPI: enb1=1ffdc8f143b431d6_i* enb2=433cf9af7679ac50_i*
[13:54:43] ok after 106 s: all nominal
[13:55:04]   enb1 traffic: lost/max-gap = 62/226ms  (1278 packets transmitted, 1216 received, 4.85133% packet loss, time 129465ms)
[13:55:05]   enb2 traffic: lost/max-gap = 53/303ms  (1270 packets transmitted, 1217 received, 4.17323% packet loss, time 128631ms)
[13:55:05] --- state: after
[13:55:05]   seg1: act=standby prot=nominal cur=seg2 inst=2 dorm=0
[13:55:06]   seg2: act=active prot=nominal cur=seg2 inst=2 dorm=0
[13:55:06]   seg3: act=standby prot=nominal cur=seg2 inst=0 dorm=2
[13:55:06]   ipmpls best: 198.51.100.1/32->seg2  10.100.1.1/32->seg2  
[13:55:07]   IKE SPI: enb1=1ffdc8f143b431d6_i* enb2=433cf9af7679ac50_i*
[13:55:07] --- MC_REDUNDANCY events (log 99, newest first)
  seg1 2026/10/24 11:54:40.881 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg1 2026/10/24 11:53:46.561 "ipsec back in sync with peer 10.0.0.3."
  seg1 2026/10/24 11:53:46.561 "ipsec back in sync with peer 10.0.0.2."
  seg1 2026/10/24 11:53:11.175 "ipsec lost sync with peer 10.0.0.3."
  seg1 2026/10/24 11:53:11.175 "ipsec lost sync with peer 10.0.0.2."
  seg2 2026/10/24 11:54:40.879 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg2 2026/10/24 11:53:10.671 "The Sync status of peer 10.0.0.1 changed to inSync"
  seg2 2026/10/24 11:51:59.857 "Multi-chassis ipsec domain 1 local activity state changed from standby to active because an inter-chassis link went down. The active router in the domain is 10.0.0.2."
  seg2 2026/10/24 11:51:59.838 "The Sync status of peer 10.0.0.1 changed to outOfSync"
  seg2 2026/10/24 11:51:59.789 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg3 2026/10/24 11:54:40.881 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg3 2026/10/24 11:53:10.671 "The Sync status of peer 10.0.0.1 changed to inSync"
  seg3 2026/10/24 11:51:59.859 "Multi-chassis ipsec domain 1 has elected a new active router because an inter-chassis link went down. The local router's activity state is standby. The active router in the domain is 10.0.0.2."
  seg3 2026/10/24 11:51:59.333 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg3 2026/10/24 11:51:59.333 "The Sync status of peer 10.0.0.1 changed to outOfSync"
[13:55:09] RESULT: expected OA=seg2 actual OA=seg2, IKE SA kept=yes, verdict=FAIL
