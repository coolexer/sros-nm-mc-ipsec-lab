[14:39:10] # T7r — Возврат seg1 после отказа
[14:39:10] Ожидание: non-revertive: seg2 stays OA, no loss
[14:39:10] --- state: before
[14:39:11]   seg1: act=discovery prot=notReady cur=0.0.0.0 inst=0 dorm=0
[14:39:12]   seg2: act=active prot=notReady cur=seg2 inst=2 dorm=0
[14:39:12]   seg3: act=standby prot=notReady cur=seg2 inst=0 dorm=2
[14:39:12]   ipmpls best: 198.51.100.1/32->seg2  10.100.1.1/32->seg2  
[14:39:13]   IKE SPI: enb1=123925ae997e133c_i* enb2=3095f5042cafc595_i*
[14:40:05] ok after 47 s: all nominal
[14:40:26]   enb1 traffic: lost/max-gap = 0/157ms  (702 packets transmitted, 702 received, 0% packet loss, time 70607ms)
[14:40:27]   enb2 traffic: lost/max-gap = 0/149ms  (698 packets transmitted, 698 received, 0% packet loss, time 70193ms)
[14:40:27] --- state: after
[14:40:27]   seg1: act=standby prot=nominal cur=seg2 inst=2 dorm=0
[14:40:28]   seg2: act=active prot=nominal cur=seg2 inst=2 dorm=0
[14:40:28]   seg3: act=standby prot=nominal cur=seg2 inst=0 dorm=2
[14:40:28]   ipmpls best: 198.51.100.1/32->seg2  10.100.1.1/32->seg2  
[14:40:29]   IKE SPI: enb1=123925ae997e133c_i* enb2=3095f5042cafc595_i*
[14:40:29] --- MC_REDUNDANCY events (log 99, newest first)
  seg1 2026/10/24 12:40:07.127 "ipsec back in sync with peer 10.0.0.3."
  seg1 2026/10/24 12:40:07.127 "ipsec back in sync with peer 10.0.0.2."
  seg1 2026/10/24 12:40:02.600 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg1 2026/10/24 12:39:30.937 "ipsec lost sync with peer 10.0.0.3."
  seg1 2026/10/24 12:39:30.937 "ipsec lost sync with peer 10.0.0.2."
  seg2 2026/10/24 12:40:02.598 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg2 2026/10/24 12:39:30.433 "The Sync status of peer 10.0.0.1 changed to inSync"
  seg2 2026/10/24 12:38:18.867 "The Sync status of peer 10.0.0.1 changed to outOfSync"
  seg2 2026/10/24 12:38:18.739 "Multi-chassis ipsec domain 1 local activity state changed from standby to active because an inter-chassis link went down. The active router in the domain is 10.0.0.2."
  seg2 2026/10/24 12:38:18.735 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
  seg3 2026/10/24 12:40:02.600 "Protection status for the multi-chassis ipsec domain 1 changed to nominal"
  seg3 2026/10/24 12:39:30.436 "The Sync status of peer 10.0.0.1 changed to inSync"
  seg3 2026/10/24 12:38:18.864 "The Sync status of peer 10.0.0.1 changed to outOfSync"
  seg3 2026/10/24 12:38:18.741 "Multi-chassis ipsec domain 1 has elected a new active router because an inter-chassis link went down. The local router's activity state is standby. The active router in the domain is 10.0.0.2."
  seg3 2026/10/24 12:38:18.622 "Protection status for the multi-chassis ipsec domain 1 changed to notReady"
[14:40:31] RESULT: expected OA=seg2 actual OA=seg2, IKE SA kept=yes, verdict=PASS
