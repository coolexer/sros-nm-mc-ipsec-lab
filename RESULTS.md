# N:M MC-IPsec validation results

**Test dates: 24–25 October 2026.** The compact-profile program is complete:
all 29 accepted measurement windows meet their functional criteria. Coverage includes
stateful DA switchover, normal/HA DS takeover, sequential DA failures, node return, public/private shunting and
forwarding over a surviving LAG member.

The [customer test program](TEST-PROGRAM.md) describes each action, both traffic
directions, acceptance and restoration. The [per-test topology gallery](TOPOLOGY-TESTS.md)
shows the complete lab, disabled components and traffic arrows for every window.

![Validated lab topology](docs/topology.svg)

## Validated environment

| Parameter | Value |
|---|---|
| SR OS | SR-SIM 26.7.R2 |
| Orchestrator | containerlab 0.80.0 |
| SecGWs | Three 7750 SR-7s; CPM5, one IOM4-e and one MS-ISA2 per node |
| Roles | seg1 DA priority 200; seg2 DA priority 100; seg3 DS priority 200 |
| Core | One 7750 SR-1: public Base and private VPRN 100 |
| Initiators | Two Linux eNBs; strongSwan 5.9.12; IKEv2/ESP |
| Probe traffic | Configured 10 ICMP echo requests/s per eNB inner address to 10.200.0.10 |
| Inter-node links | LAG 12/13/23, two LACP members each; VLAN 1 public/control, VLAN 3 private |
| Time | Shared NTP 172.20.30.123 over management; chronyd -x, local stratum 10 |
| Runtime | WSL2, 12 logical CPUs, 17.15 GiB RAM, 5 GiB swap |
| Host | Intel i5-1245U, 32 GiB RAM |

The program ran in sequential groups. The table consolidates the final accepted measurements
for each scenario; their source groups are identified under Evidence. This is functional
validation of two tunnels. Numerical gaps apply to this SR-SIM instance; hardware SLA
thresholds and load-test parameters are agreed separately.

## Accepted measurements

Each eNB column gives lost packets and the maximum interval without a reply.
The test identifier links to its measurement log.

| Window | OA after | IKE kept | eNB1: lost / max gap | eNB2: lost / max gap | Verdict |
|---|---|---|---|---|---|
| [T0](results/validated-compact-20261025-072430/T0.log) | seg1 | yes | 0 / 0.103 s | 0 / 0.103 s | PASS |
| [T1](results/validated-compact-20261024-212054/T1.log) | seg2 | yes | 3 / 0.440 s | 3 / 0.440 s | PASS |
| [T1b](results/validated-compact-20261024-212054/T1b.log) | seg1 | yes | 3 / 0.440 s | 3 / 0.443 s | PASS |
| [T2](results/validated-compact-20261024-212948/T2.log) | seg2 | yes | 3 / 0.436 s | 3 / 0.461 s | PASS |
| [T3](results/validated-compact-20261024-212948/T3.log) | seg2 | yes | 0 / 0.161 s | 0 / 0.184 s | PASS |
| [T4](results/validated-compact-20261024-212948/T4.log) | seg1 | yes | 3 / 0.426 s | 3 / 0.431 s | PASS |
| [T5](results/validated-compact-20261024-212948/T5.log) | seg1 | yes | 0 / 0.119 s | 0 / 0.134 s | PASS |
| [T6](results/validated-compact-20261024-212948/T6.log) | seg1 | yes | 0 / 0.107 s | 0 / 0.109 s | PASS |
| [T7](results/validated-compact-20261024-212948/T7.log) | seg2 | yes | 25 / 2.947 s | 25 / 2.953 s | PASS |
| [T7-noBFD](results/validated-compact-20261024-212948/T7-noBFD.log) | seg2 | yes | 744 / 84.238 s | 742 / 84.187 s | PASS |
| [T8](results/validated-compact-20261024-215807/T8.log) | seg3 | yes | 25 / 2.948 s | 26 / 3.033 s | PASS |
| [T8r](results/validated-compact-20261024-215807/T8r.log) | seg3 | yes | 0 / 0.184 s | 0 / 0.154 s | PASS |
| [T9](results/validated-compact-20261025-072430/T9.log) | seg3 | yes | 24 / 2.811 s | 22 / 2.602 s | PASS |
| [T9r](results/validated-compact-20261025-072430/T9r.log) | seg3 | yes | 0 / 0.105 s | 0 / 0.105 s | PASS |
| [T10-seg2](results/validated-compact-20261025-070431/T10-seg2.log) | seg1 | yes | 0 / 0.104 s | 0 / 0.103 s | PASS |
| [T10b-seg2](results/validated-compact-20261025-070431/T10b-seg2.log) | seg1 | yes | 93 / 10.534 s — blocked | 95 / 10.843 s — blocked | PASS |
| [T10-seg3](results/validated-compact-20261025-070431/T10-seg3.log) | seg1 | yes | 0 / 0.104 s | 0 / 0.104 s | PASS |
| [T10b-seg3](results/validated-compact-20261025-070431/T10b-seg3.log) | seg1 | yes | 92 / 10.507 s — blocked | 96 / 10.827 s — blocked | PASS |
| [T11-seg2](results/validated-compact-20261025-070431/T11-seg2.log) | seg1 | yes | 0 / 0.103 s | 0 / 0.104 s | PASS |
| [T11b-seg2](results/validated-compact-20261025-070431/T11b-seg2.log) | seg1 | yes | 93 / 10.582 s — blocked | 95 / 10.800 s — blocked | PASS |
| [T11-seg3](results/validated-compact-20261025-070431/T11-seg3.log) | seg1 | yes | 0 / 0.118 s | 0 / 0.105 s | PASS |
| [T11b-seg3](results/validated-compact-20261025-070431/T11b-seg3.log) | seg1 | yes | 92 / 10.558 s — blocked | 94 / 10.793 s — blocked | PASS |
| [T12](results/validated-compact-20261025-070431/T12.log) | seg2 | yes | 1 / 0.205 s | 2 / 0.314 s | PASS |
| [T13a](results/validated-compact-20261025-091934/T13a.log) | seg2 | yes | 27 / 3.201 s | 27 / 3.180 s | PASS |
| [T13b](results/validated-compact-20261025-091934/T13b.log) | seg3 | yes | 24 / 2.786 s | 23 / 2.693 s | PASS |
| [T13r](results/validated-compact-20261025-091934/T13r.log) | seg3 | yes | 0 / 0.228 s | 0 / 0.213 s | PASS |
| [T14a](results/validated-compact-20261025-091934/T14a.log) | seg2 | yes | 27 / 3.181 s | 27 / 3.144 s | PASS |
| [T14b](results/validated-compact-20261025-091934/T14b.log) | seg3 | yes | 22 / 2.618 s | 22 / 2.640 s | PASS |
| [T14r](results/validated-compact-20261025-091934/T14r.log) | seg3 | yes | 0 / 0.106 s | 0 / 0.105 s | PASS |

Every accepted window preserved both original IKE SAs: both SPI values of each session were
checked before and after the action. CHILD SAs were installed; CHILD rekey on switchover
was allowed. Ownership checks examine the domain, including an isolated DS in eligible state.

The gap includes the window head, inter-reply intervals and the tail after the final reply.
Even a no-loss 10-pps stream has normal intervals near 0.1 s. This is an ICMP observation
including host scheduling, rather than exact hardware forwarding downtime.

In T10b/T11b, blocking after profile removal is the **expected negative-control result**.
The window includes successful baseline replies before the action. After profile removal,
both flows remain blocked through the end of observation. That gap bounds the observed
blockage; it is not recovery time. The profile is restored after the control window ends.

## Verified behavior

### DA switchover and ISA return

T1/T1b demonstrate controlled seg1 → seg2 → seg1 switchover while preserving IKE.
Disabling the active ISA in T2 transfers ownership to seg2. Restoring the ISA in T3 leaves
seg2 as OA under non-revertive operation, without packet loss.

T4 demonstrates automatic return to the preferred DA with revertive enabled. The
[election event log](results/validated-compact-20261024-212948/T4-election-events.log)
records nominal at 19:33:31.290 UTC and takeover at 19:35:32.265 UTC, approximately 121 s
later. Nokia's 60-s standby/nominal condition is a minimum eligibility interval. The role-return
wait and the short user-traffic gap are separate measurements.

### Link resilience

T5 retains OA and traffic when one LAG member fails. T6 disables both direct LAG 12 members:
MIMP/MCS remains reachable through seg3, all participants stay nominal and user traffic
continues without loss. The [control-underlay route](results/validated-compact-20261024-212948/T6-underlay-evidence.log)
is recorded separately.

Both members are on one network MDA in compact. T5/T6/T12 therefore validate port/link
failures. The [dual-IOM reference topology](profiles/dual-iom.clab.yml) places members on
different IOMs for a separate component-redundancy program.

### OA failure and core BFD

In T7, seg1 CPM/IOM components are killed. Traffic recovers through seg2 **before seg1
restarts**. Returning seg1 adds no missing sequence numbers and preserves IKE.

T7-noBFD is a separate control with BFD disabled only on core BGP peerings. The core retains
the failed OA next-hop until BGP hold expiration; the negotiated hold time is 90 s. See the
[route and BGP evidence](results/validated-compact-20261024-212948/T7-noBFD-stale-core-route.log).
Traffic also recovers before seg1 startup in this variant, and node return adds no loss.
The normal lab configuration enables BFD.

#### Traffic restoration versus node reintegration

The accepted [T7 log](results/validated-compact-20261024-212948/T7.log) records two
separate phases. Times below are UTC on 24 October 2026; state observations are runner
polling timestamps, rather than packet-level transition timestamps. The log's local
timestamps (UTC+02:00) are converted to UTC here using its epoch window markers.

| Event | T7 with BFD | T7-noBFD control |
|---|---|---|
| seg1 kill completed | 19:43:08 | 19:47:24 |
| First replies after the main gap, eNB1 / eNB2 (packet timestamps) | 19:43:10.150 / 19:43:10.140 | 19:48:46.961 / 19:48:46.911 |
| seg2 observed as OA | 19:43:14 | 19:47:29 |
| Ten consecutive replies confirmed on both eNBs, while seg1 was off | 19:43:15 | 19:48:49 |
| seg1 start completed | 19:43:19 | 19:48:53 |
| seg1 CLI available | 19:43:40 | 19:49:10 |
| All domains observed nominal after node return | 19:44:55 | 19:50:34 |
| Measured maximum reply gap, eNB1 / eNB2 | **2.947 / 2.953 s** | **84.238 / 84.187 s** |
| Additional packets lost during node return | **0 / 0** | **0 / 0** |

T7 therefore has approximately 3 s of traffic interruption. The approximately 96 s from
seg1 startup to nominal describes simulator boot and return to the protected domain state;
traffic already uses seg2 during this phase. The CLI becomes available before nominal.
The retained snapshots do not isolate individual boot, peering and synchronization times.

In the no-BFD control, OA election and core routing converge at different times. The
[captured core state](results/validated-compact-20261024-212948/T7-noBFD-stale-core-route.log)
shows the old next-hop `172.31.1.1`, BGP still Established, BFD disabled, Active Hold Time
90 s and Active Keep Alive 30 s. This explains the long blackhole toward failed seg1.
Hold time is measured from the last received BGP message, so a roughly 84 s interruption
after the failure is consistent with a 90 s hold timer. IKE identifiers are preserved in
both variants; neither outage requires waiting for seg1 to restart.

The configuration requests BFD at 100 ms with multiplier 3. Operational session output
retained with the sequential tests distinguishes two implementations: core BGP uses
`iom` sessions at 100 ms; MC-IPsec uses `cpm-np` sessions at 1000 ms with multiplier 3.
Nokia documents a [1000-ms negotiation floor for simulated CPM-NP BFD](https://documentation.nokia.com/acg/24-7-2/books/mpls-classic/c079-mpls-tp.html),
consistent with this lab's output. The approximately 3-s MC-IPsec detection timer is
therefore consistent with the observed failover gaps. It is a simulator condition,
not a production timer recommendation.

The retained T7 snapshots do not isolate the exact BFD, OA-election and route/data-plane
convergence contributions. A tenfold reduction of the operational BFD interval would
reduce that detection timer from approximately 3 s to 0.3 s, without guaranteeing a
tenfold reduction of the complete reply gap. Configuring 100 ms alone does not demonstrate
that reduction when the operational session remains at 1000 ms. Hardware restoration
time requires a separate measurement on the target platform.

### DS takeover and pool HA

T8 and T9 recover both flows on seg3 after both DAs are killed, preserving IKE and before
the DAs return. T8 uses a normal pool; T9 uses `high-availability tunnel-limit-32k`.
The user-packet processing path is the same:

![T9: complete topology during HA DS takeover](docs/topology-scenarios/T9-paths.svg)

Normal mode downloads states from CPM to ISA at takeover. HA preloads them on the pool ISA;
takeover still requires activation. The measured gaps also include fault detection and route
convergence. One observation per mode on two tunnels does not establish a statistical HA
performance advantage.

T8r/T9r separately measure both DAs returning. In both accepted measurements, seg3 remains
OA, all participants reach nominal, both IKE pairs survive and neither eNB loses packets.
Each eNB receives all 933 replies in the final T9r window.

HA preparation is completed before the measured fault, as specified in the
[operational conditions](OPERATIONAL-NOTES.md). The group ends with OA seg1 and
normal pool mode none.

### Sequential DA failures: verified seg1 → seg2 → seg3

T13 (normal pool) and T14 (HA pool) validate two successive complete DA failures with
an explicit intermediate forwarding checkpoint. Unlike T8/T9, the second DA is kept
running until the first takeover has been verified.

1. Start nominal on seg1. Record both original IKE pairs and baseline routes/BFD.
2. Kill seg1 CPM/IOM. Require OA seg2, two installed tunnels, all three core /32 routes
   through seg2, recovered replies and surviving seg2/seg3 MCS inSync in both directions.
3. Observe 30 s without additional missing sequence numbers. Keep seg1 off.
4. Start the second measured window through seg2, check the original IKE pairs and
   seg1's off state, then kill seg2 CPM/IOM.
5. Require isolated seg3 to be the unique forwarding owner with two installed tunnels,
   all core /32 routes through seg3 and recovered traffic. Observe another 30 s without
   additional loss, before either DA restarts.
6. Measure both DAs returning. Both original IKE pairs survive the complete chain and
   return. In both accepted runs, seg3 remains OA, return adds zero loss, and all domains
   become nominal. Cleanup restores the normal-pool seg1 baseline.

| Pool mode | First fault: seg1 → seg2 gap, eNB1 / eNB2 | Second fault: seg2 → seg3 gap, eNB1 / eNB2 | DA return: lost, eNB1 / eNB2 |
|---|---|---|---|
| Normal pool | 3.201 s / 3.180 s | 2.786 s / 2.693 s | 0 / 0 |
| HA pool | 3.181 s / 3.144 s | 2.618 s / 2.640 s | 0 / 0 |

![First sequential fault: seg1 off and verified forwarding through seg2](docs/topology-scenarios/T13a-paths.svg)

![Second sequential fault: both DAs off and traffic through the HA pool on seg3](docs/topology-scenarios/T14b-paths.svg)

The first fault leaves whole-domain protection notReady because seg1 is absent. The
surviving seg2/seg3 MCS relationship is still synchronized. The second fault deliberately
tests this degraded state; no planned force-switchover, IKE reset or peer-domain reset
is inserted between failures. Each fault has its own complete ping traces and gap.
The three windows per mode share the same original IKE identity; their boundary checks
prevent a new session from being mistaken for a stateful continuation.

The [sequential measurement group](results/validated-compact-20261025-091934/) contains per-node and core
operational evidence. The [restored baseline BFD details](results/validated-compact-20261025-091934/bfd-baseline-detail.log)
distinguish configured intervals from operational CPM-NP and IOM intervals. HA preparation
is outside measured windows. These single observations do not establish a statistically
significant speed difference between pool modes.

### Shunting through both standbys

For T10/T11, the core selects the relevant routes through seg2 and then seg3. All four
positive windows pass without loss. Removing the corresponding profile in four negative
controls blocks both round-trip flows while preserving OA and IKE.

T12 combines member-A failure, switchover to OA seg2 and both traffic paths pinned through
former OA seg1. Its final stable part demonstrates shunting on surviving member B:

![T12: requests and replies shunt over the surviving LAG member](docs/topology-scenarios/T12-paths.svg)

## Evidence

| Measurement group | Accepted windows |
|---|---|
| [24 October, group 1](results/validated-compact-20261024-212054/) | T1, T1b |
| [24 October, group 2](results/validated-compact-20261024-212948/) | T2, T3, T4, T5, T6, T7, T7-noBFD |
| [24 October, group 3](results/validated-compact-20261024-215807/) | T8, T8r |
| [25 October, shunting](results/validated-compact-20261025-070431/) | Four public, four private windows, and T12 |
| [25 October, HA and baseline](results/validated-compact-20261025-072430/) | T9, T9r, T0 |
| [25 October, sequential failures](results/validated-compact-20261025-091934/) | T13a, T13b, T13r, T14a, T14b, T14r |

Each directory contains the accepted windows listed for that group: original log lines
from window start through the after-action snapshot, complete START/STOP ping traces,
JSON metrics and source-invocation metadata. These results are not presented as one
uninterrupted `all` invocation. All **58 original ping traces** were independently reparsed
and matched to their stored metrics. The sequential chains were also independently checked
for original IKE continuity and both 30-s loss-free checkpoints per mode. T7/T7-noBFD were also checked for additional missing
sequences during node return.

Index: [validated-compact-index.json](results/validated-compact-index.json).
Checksums: [validated-evidence-sha256.json](results/validated-evidence-sha256.json).
Group names use WSL local time; SR OS event timestamps are explicitly marked UTC, and ping
uses Unix timestamps. Retain those time references when correlating evidence.

## Final operational state

Operational acceptance passed: OA seg1, one agreed Current Active, nominal protection on
all SecGWs, MCS inSync, both IKE/CHILD sessions installed and two installed tunnels on OA.
The gateway and private routes use seg1. ISAs and both members of every LAG are operational;
shunting is restored, BFD enabled, revertive false and pool mode none. Shared NTP is selected
on all four routers. Temporary neighbor route pins are removed and configurations saved.

Full protocol: [operational.log](results/validated-final-state/operational.log).
The scenarios and configuration were checked against the
[Nokia SR OS 26.7 IP tunnels guide](https://documentation.nokia.com/sr/26-7/7750-sr/books/ms-isa-esa/ip-tunnels.html)
and the command references listed in the [test program](TEST-PROGRAM.md).

## Repository consistency audit

An offline repository audit on 25 October 2026 checked the source, generated artifacts
and published evidence. The accepted measurement files retain their original bytes and
source-invocation metadata; this audit does not introduce a new live failover measurement.

| Check | Verified result |
|---|---|
| Configuration generation | The compact generator reproduces all six committed configuration files byte for byte. Both topology profiles have 15 links with unique endpoints and matching two-member LAG bindings. |
| Nokia design basis | DA/DS election order, full-mesh peering, direct public/private shunting, normal/HA pool behavior, responder-only operation, DPD, lifetimes and shared NTP agree with the documented functional design. |
| Runner regression | 30 offline regression tests, including replay of all 29 accepted windows through the OA, IKE, installed-tunnel and expected-route checks. |
| Measurement integrity | All 58 original ping traces reproduce the stored metrics; all 142 evidence-file SHA-256 checksums match. |
| Documentation | Five English Markdown documents in the repository root; local links, image references and heading fragments resolve. |
| Diagrams | All 61 SVGs parse and render; marker/filter references resolve. The generators reproduce all 58 scenario SVGs and the topology gallery byte for byte. |
| Windows/WSL checkout | Executable text uses LF; published evidence preserves its exact bytes, including metadata, when Git uses automatic Windows line-ending conversion. |
| Shell helpers | ShellCheck passes; an absent or empty configuration file is rejected before the CLI helper is called. |

The current runner records and validates forwarding explicitly. Replaying the archived
after-action snapshots confirms that the existing accepted windows meet these checks too.
Their original runner checksums describe the measurement-time version and are retained.

Audit scope is the GitHub repository and its published evidence. The compact profile's
shared IOM/MDA, two-tunnel scale and simulated BFD timing remain the stated test conditions.
The dual-IOM profile is a reference layout; hardware failure domains, congestion/QoS behavior
and production numerical SLAs require their own acceptance program.
