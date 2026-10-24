# Test program — N:M MC-IPsec switchover

The program checks how a three-node N:M MC-IPsec SecGW behaves in planned switchovers and in failures:
which node becomes operational active (OA), whether the failover is stateful, and how long traffic
stops. The runner is `tests/nm_tests.sh`. Results of one full run are in [RESULTS.md](RESULTS.md).

![redundancy logic](docs/redundancy-logic.svg)

## 1. Test bed

![topology](docs/topology.svg)

### 1.1 Nodes and roles

| Node | `ipsec-domain 1` | Priority | Tunnel group 1 | Notes |
|---|---|---|---|---|
| seg1 | `designated-role active` (DA) | 200 | `multi-active { isa 1/2 }`, `active-isa-number 1` | expected OA |
| seg2 | `designated-role active` (DA) | 100 | same as seg1 | hot standby: synced states are pre-loaded on its ISA |
| seg3 | `designated-role standby` (DS) | 200 | `multi-active { member-pool "pool1" }`, pool = `isa 1/2` | cold standby: synced states kept on the CPM |

`revertive` is `false` on all nodes, which is the default.

### 1.2 Addressing

| Purpose | Addressing |
|---|---|
| System / MIMP / MCS source | 10.0.0.1, .2, .3 (ipmpls 10.0.0.100) |
| SecGW–SecGW link A / B (Base, VLAN 1) | 10.`ab`.1.0/31 and 10.`ab`.2.0/31 for pair a<b (e.g. 10.12.1.0/31) |
| Private shunt (VPRN, VLAN 3, link A only) | 10.1`ab`.1.0/31 |
| SecGW public uplink 1/1/9 (Base) | 172.31.`n`.1/31 ↔ ipmpls 172.31.`n`.0 |
| SecGW private uplink 1/1/10 (VPRN 100) | 172.30.`n`.1/31 ↔ ipmpls 172.30.`n`.0 |
| IPsec gateway (all SecGWs) | `ipsec-gw "enb-gw"` local address 198.51.100.1, public tunnel interface 198.51.100.254/24 |
| eNB public | enb1 100.64.1.2/24, enb2 100.64.2.2/24 (gateway on ipmpls) |
| eNB inner (traffic selector) | enb1 10.100.1.1/32, enb2 10.100.2.1/32 |
| Traffic target | mme 10.200.0.10/24 behind ipmpls VPRN 100 |
| AS numbers | SecGWs 64512, ipmpls 65000 |

### 1.3 Configuration highlights

All of these come from `gen_configs.py` and follow the SR OS 26.7 MS-ISA/ESA guide:

- **N:M domain.** `configure redundancy multi-chassis ipsec-domain 1 { designated-role, priority, tunnel-group 1 }`.
  Each peer has `peer <sys> { sync { ipsec true } mc-ipsec { bfd-liveness true domain 1 } }`, giving
  a full mesh of MIMPv2 and MCS between all three nodes.
- **Inter-chassis links.** There are two per pair. OSPF with BFD at 100 ms × 3 gives ECMP between
  the system addresses. The central MIMP BFD session runs on the system interface.
- **IPsec.**
  - IKEv2 with PSK, IKE AES-128/SHA-256/group 14, ESP AES-128/SHA-256.
  - `ipsec-responder-only true` on the tunnel group.
  - DPD `interval 300 max-retries 3 reply-only`.
  - SecGW lifetimes are about twice those of the eNB: IKE 172800 s vs 86400 s, CHILD 7200 s vs
    3600 s.
  - The tunnel template needs `sp-reverse-route use-security-policy`. Dynamic LAN-to-LAN tunnels on
    an `ipsec-gw` are rejected without it ("lan-to-lan gateway tunnels require a reverse-route
    enabled template").
- **Routing to the OA.** The policy `export-ipsec` matches `protocol ipsec` and sets the MED by
  state: `ipsec-master-with-peer` 100, `ipsec-master-without-peer` 200, `ipsec-non-master` 1000. It
  is exported to ipmpls from the Base router (gateway /32) and from VPRN 100 (reverse routes). The
  core eBGP sessions use `bfd-liveness`.
- **Shunting.**
  - Base: `router ipsec multi-chassis-shunt-interface` / `multi-chassis-shunting-profile "shunt-pub"`,
    applied to IES interface `pub`.
  - VPRN: `shunt-priv`, applied to tunnel interface `priv`.
  - Both use link A to each peer.

## 2. Traffic and measurements

| What | How |
|---|---|
| Traffic | `ping -D -O -i 0.1 -W 1 -I 10.100.n.1 10.200.0.10` from each eNB: 10 pps per eNB, sent through the ESP tunnel |
| Lost packets | from the ping summary (transmitted − received) |
| **Worst gap** | largest interval between two consecutive replies, *including* the tail from the last reply to the end of the test (iputils `-D` timestamps; `-O` prints unanswered sequence numbers) |
| Role / state | `show redundancy multi-chassis ipsec-domain 1` on every SecGW: activity state, protection status, current active, Installed / Standby Dormant tunnel counts |
| Core path | `show router route-table 198.51.100.1/32` (Base) and `show router "100" route-table 10.100.1.1/32` on ipmpls |
| Stateful? | IKE SA SPI on each eNB (`swanctl --list-sas`) before vs after. The same SPI means the IKE SA survived the switchover. |
| Events | last MC_REDUNDANCY events from log 99 of every SecGW |

Each test writes `results/Tn.md` (snapshots, actions, events, verdict) and `results/Tn-enbX.ping` (raw
trace), and appends one line to `results/SUMMARY.md`.

## 3. Preconditions and pass rules

Every test except T3 and T4 starts from the **baseline**:

1. All SR OS nodes answer on the CLI.
2. **Protection status is `nominal` on all SecGWs.** The guide says: "A nominal state must be reached
   on both MC-IPsec chassis before a MC-IPsec switchover is triggered." If the status stays
   `notReady` for 180 s, the runner applies the recovery from the SR OS release notes: disable and
   re-enable `peer <x> mc-ipsec domain 1` on all peers. Every use is logged to
   `results/workarounds.log` and reported in RESULTS.md.
3. seg1 is OA. If not, the runner uses `force-switchover domain 1 to 10.0.0.1 now`.
4. Both eNB IKE SAs are up and seg1 has 2 tunnels `Installed`.
5. The ipmpls best paths for 198.51.100.1/32 and 10.100.1.1/32 point to the current OA, so BGP has
   converged.

**Verdict.**
- PASS when the OA after the test is the expected node and the loss class matches.
- The loss class is one of: `none` (0 packets lost on both eNBs), `any` (loss allowed, measured),
  `some` (loss required; used by the control tests).
- A node in state `eligible` counts as OA. The guide defines it as "unable to reach election
  consensus with its peers, but the node can function locally as OA".
- OBSERVED marks an exploratory test that has no fixed expectation.

## 4. Scenarios

Each scenario lists its action, its expected result, and its loss class.

### T0 — Baseline
- **Action:** traffic only, for 10 s.
- **Expected:** seg1 active/nominal; seg2 standby with 2 tunnels `Installed`; seg3 standby with 2
  tunnels `Standby Dormant`; MED 100 via seg1.
- **Loss:** none.

### T1 / T1b — Planned switchover
- **Action (T1):** on seg1, `tools perform redundancy multi-chassis mc-ipsec force-switchover domain 1 auto now`.
- **Expected (T1):** seg2 becomes OA, because "DA is preferred over DS" (seg3 has the same priority
  as seg1 but is DS). The IKE SA is kept, and the new OA rekeys the CHILD_SA because ESP sequence
  numbers are not synced.
- **Action (T1b):** on seg2, `... force-switchover domain 1 to 10.0.0.1 now`.
- **Expected (T1b):** back to seg1.
- **Loss:** any (measured).

### T2 — ISA failure on the OA
- **Action:** on seg1, `/configure card 1 mda 2 admin-state disable`.
- **Expected:** seg1 goes `notEligible` and seg2 (DA) becomes OA.
- **Loss:** any.

### T3 — ISA recovery, non-revertive (follows T2)
- **Action:** on seg1, `/configure card 1 mda 2 admin-state enable`, then wait for `nominal`.
- **Expected:** seg1 returns as standby and seg2 stays OA.
- **Loss:** none.

### T4 — Revertive (follows T3)
- **Action:** on seg1 (standby), `/configure redundancy multi-chassis ipsec-domain 1 revertive true`.
- **Expected:** a challenger that has been standby and nominal for 60 s, and is DA with the higher
  priority, takes OA back. seg1 becomes OA.
- **Afterwards:** revertive is set back to false.
- **Loss:** any.

### T5 — One of two SecGW links fails
- **Action:** on seg1, `/configure port 1/1/1 admin-state disable` (link A to seg2).
- **Expected:** no switchover. MIMP and MCS stay up over link B (ECMP between the system addresses),
  sync stays `inSync`, protection stays `nominal`.
- **Restore:** the port is re-enabled.
- **Loss:** none.

### T6 — Both direct links seg1–seg2 fail
- **Action:** ports 1/1/1 and 1/1/2 disabled on seg1.
- **Expected:** exploratory. seg3 is still meshed with both, so record adjacencies, OA and loss.
- **Restore:** ports re-enabled.
- **Loss:** any (OBSERVED).

### T7 / T7r / T7b — OA node failure and return
- **Action (T7):** `docker kill` of seg1 (CPM and IOM containers). The veth links stay up on the peer
  side, so detection has to come from BFD, as with a hung or powered-off chassis that has no loss of
  signal on the links.
- **Expected (T7):** seg2 becomes OA. **Loss:** any.
- **Action (T7r):** `docker start` seg1 and wait for `nominal`.
- **Expected (T7r):** non-revertive, so seg2 stays OA. **Loss:** none.
- **Action (T7b):** force-switchover back to seg1. **Loss:** any.
- **Variant:** the same scenario was also run without BFD on the core eBGP sessions (`T7*-noBFD`).

### T8 — Double failure, DS takes over
- **Action:** `docker kill` of seg1 and seg2.
- **Expected:** seg3 (DS) takes the ISA from `pool1`, the CPM downloads the synced states, and seg3
  becomes OA. Without peers it can only reach `eligible`, which is MED 200 in the policy. The impact
  is larger than a DA failover: "the traffic impact during a failover is larger when failing over to
  a DS tunnel group than to a DA tunnel group".
- **Afterwards:** restart seg1 and seg2, wait for `nominal`, record which node is OA.
- **Loss:** any.

### T9 — Double failure with pool high-availability
- **Action:** on seg3, `/configure isa tunnel-member-pool "pool1" high-availability tunnel-limit-32k`,
  wait for `nominal`, then repeat T8.
- **Expected:** "the CPM pre-downloads the synced tunnel states ... to every ISA in the pool". The
  switchover to the DS is faster than in T8, but still slower than to a DA.
- **Afterwards:** HA is set back to `none`.
- **Loss:** any.

### T10 / T10b — Shunting, public side
- **Setup:** on ipmpls, an import policy rejects 198.51.100.1/32 from seg1. The core then sends the
  ESP to a standby (seg2 or seg3, both MED 1000).
- **Expected (T10):** the standby shunts the ESP to the OA over `shunt-pub`. Traffic continues and
  the OA stays seg1. **Loss:** any (0 expected).
- **Action (T10b, control):** delete `multi-chassis-shunting-profile` from IES interface `pub` on
  seg2 and seg3.
- **Expected (T10b):** ESP that arrives at the standby is dropped. **Loss:** some.
- **Restore:** the profiles and the core policy are put back.

### T11 / T11b — Shunting, private side
- **Setup:** on ipmpls VPRN 100, an import policy rejects 10.100.0.0/16 from seg1. Traffic from mme
  to the eNBs then enters a standby.
- **Expected (T11):** the standby shunts it to the OA over `shunt-priv`. **Loss:** any (0 expected).
- **Action (T11b, control):** delete the shunting profile from tunnel interface `priv` on seg2 and seg3.
- **Expected (T11b):** traffic from mme to the eNBs is lost. **Loss:** some.

## 5. Running

```bash
./tests/nm_tests.sh T0 T1 T2 T3 T4      # T3/T4 must follow T2/T3 in the same call
./tests/nm_tests.sh all                 # T0 ... T11
```

- Only one runner can run at a time; a `flock` on `/tmp/nm_tests.lock` enforces this.
- A full run takes about 1.5–2 h on a laptop. Most of the time is spent waiting for SR-SIM node
  restarts and for protection status to return to `nominal`.
- To add a scenario, write a function `Tn() { begin ...; <action>; wait_for ...; finish <expected-OA> <none|any|some>; }`
  and add it to `ALL`.

## 6. Limits of the method

- **SR-SIM is not hardware.** It emulates the control and management plane and limits ports to
  1000 pps. Timings show trends only.
- **No loss of signal on node failure.** `docker kill` leaves the links up. A real power loss usually
  also drops the direct links, which makes detection faster.
- **The 10 pps probe resolves gaps to about 100 ms.**
- **T10b/T11b gaps are the length of the test window**, not a recovery time. They only show that
  traffic stops without shunting.
