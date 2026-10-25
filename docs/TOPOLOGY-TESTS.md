# Per-test topology and traffic paths

Each view shows the complete compact lab, the action and the resulting traffic path. Blue arrows carry requests to MME; orange arrows carry replies to the eNBs. Green identifies the OA; red identifies a disabled component or a blocked path. The dashed teal path in T6 is MIMP/MCS reachability, separate from user traffic.

Base and VPRN 100 are routing instances of one core router. Its external ports are labeled by SecGW number and routing instance: P = Base/public, V = VPRN/private. Internal core switching is omitted; the request and reply sequences state the processing order. For T7-noBFD, the red dashed path shows the transient blackhole before hold expiry; the main arrows show recovered forwarding. T8r/T9r and T13r/T14r show the accepted outcome with seg3 remaining OA. Blocking in T10b/T11b is the expected negative-control result.

[Detailed test program](TEST-PROGRAM.md) · [Results](../RESULTS.md)

| Test | Action | Processing sequence |
|---|---|---|
| [T0](#t0) | No component is disabled. Both eNBs send traffic through OA seg1. | [Packet processing](scenarios/T0.svg) |
| [T1](#t1) | Run force-switchover auto on seg1: OA seg1 → seg2. | [Packet processing](scenarios/T1.svg) |
| [T1b](#t1b) | Run force-switchover to 10.0.0.1 on seg2: OA seg2 → seg1. | [Packet processing](scenarios/T1b.svg) |
| [T2](#t2) | Disable ISA 1/2 on seg1. Its CPM/IOM and network interfaces remain enabled. | [Packet processing](scenarios/T2.svg) |
| [T3](#t3) | Enable ISA 1/2 on seg1. With non-revertive operation, seg2 remains OA. | [Packet processing](scenarios/T3.svg) |
| [T4](#t4) | Enable seg1 ISA with revertive true. After eligibility conditions are met, OA seg2 → seg1. | [Packet processing](scenarios/T4.svg) |
| [T5](#t5) | Disable seg1 port 1/1/1: LAG 12 member A. Member B, port 1/1/2, remains enabled. | [Packet processing](scenarios/T5.svg) |
| [T6](#t6) | Disable seg1 ports 1/1/1 and 1/1/2. MIMP/MCS uses the alternate path through seg3. | [Packet processing](scenarios/T6.svg) |
| [T7](#t7) | Kill seg1 CPM and IOM. Restore seg1 only after traffic has recovered through seg2. | [Packet processing](scenarios/T7.svg) |
| [T7-noBFD](#t7-nobfd) | Kill seg1 CPM and IOM with core BGP BFD disabled. Main arrows show forwarding after hold expiry. | [Packet processing](scenarios/T7-noBFD.svg) |
| [T8](#t8) | Kill seg1 and seg2 CPM/IOM components. Traffic must recover on DS seg3 before the DAs restart. | [Packet processing](scenarios/T8.svg) |
| [T8r](#t8r) | Start seg1 and seg2 CPM/IOM components. In the accepted measurement, seg3 remains OA. | [Packet processing](scenarios/T8r.svg) |
| [T9](#t9) | Kill seg1 and seg2 CPM/IOM components. Synchronized states are preloaded on the seg3 HA pool ISA. | [Packet processing](scenarios/T9.svg) |
| [T9r](#t9r) | Start seg1 and seg2 CPM/IOM components. In the accepted measurement, seg3 remains OA. | [Packet processing](scenarios/T9r.svg) |
| [T10-seg2](#t10-seg2) | Pin the gateway /32 on the core through seg2; shunting profiles remain enabled. | [Packet processing](scenarios/T10-seg2.svg) |
| [T10b-seg2](#t10b-seg2) | Keep routes pinned through seg2; remove only the public shunting profile on seg2. | [Packet processing](scenarios/T10b-seg2.svg) |
| [T11-seg2](#t11-seg2) | Pin both inner /32 routes on the core through seg2; shunting profiles remain enabled. | [Packet processing](scenarios/T11-seg2.svg) |
| [T11b-seg2](#t11b-seg2) | Keep routes pinned through seg2; remove only the private shunting profile on seg2. | [Packet processing](scenarios/T11b-seg2.svg) |
| [T10-seg3](#t10-seg3) | Pin the gateway /32 on the core through seg3; shunting profiles remain enabled. | [Packet processing](scenarios/T10-seg3.svg) |
| [T10b-seg3](#t10b-seg3) | Keep routes pinned through seg3; remove only the public shunting profile on seg3. | [Packet processing](scenarios/T10b-seg3.svg) |
| [T11-seg3](#t11-seg3) | Pin both inner /32 routes on the core through seg3; shunting profiles remain enabled. | [Packet processing](scenarios/T11-seg3.svg) |
| [T11b-seg3](#t11b-seg3) | Keep routes pinned through seg3; remove only the private shunting profile on seg3. | [Packet processing](scenarios/T11b-seg3.svg) |
| [T12](#t12) | Disable seg1 port 1/1/1, switch OA to seg2 and pin public/private routes through seg1. | [Packet processing](scenarios/T12.svg) |
| [T13a](#t13a) | Kill seg1 CPM/IOM. Keep seg1 off; verify seg2 forwarding and seg2/seg3 MCS inSync, then observe 30 s. | [Packet processing](scenarios/T13a.svg) |
| [T13b](#t13b) | With seg1 still off and seg2 forwarding verified, kill seg2 CPM/IOM. Observe traffic through seg3 for 30 s. | [Packet processing](scenarios/T13b.svg) |
| [T13r](#t13r) | Start both DAs after seg1 → seg2 → seg3 failover. Record the election; require preserved IKE and nominal. | [Packet processing](scenarios/T13r.svg) |
| [T14a](#t14a) | Kill seg1 CPM/IOM with HA pool on seg3. Keep seg1 off; verify seg2 forwarding and MCS inSync, then observe 30 s. | [Packet processing](scenarios/T14a.svg) |
| [T14b](#t14b) | After verified seg2 operation, kill seg2 CPM/IOM while seg1 stays off. Observe HA pool takeover on seg3 for 30 s. | [Packet processing](scenarios/T14b.svg) |
| [T14r](#t14r) | Start both DAs after sequential HA takeover on seg3. Record the election; require preserved IKE and nominal. | [Packet processing](scenarios/T14r.svg) |

## T0

**Baseline forwarding.** No component is disabled. Both eNBs send traffic through OA seg1.

![T0: Baseline forwarding](topology-scenarios/T0-paths.svg)

## T1

**Planned switchover.** Run force-switchover auto on seg1: OA seg1 → seg2.

![T1: Planned switchover](topology-scenarios/T1-paths.svg)

## T1b

**Planned return.** Run force-switchover to 10.0.0.1 on seg2: OA seg2 → seg1.

![T1b: Planned return](topology-scenarios/T1b-paths.svg)

## T2

**Active ISA failure.** Disable ISA 1/2 on seg1. Its CPM/IOM and network interfaces remain enabled.

![T2: Active ISA failure](topology-scenarios/T2-paths.svg)

## T3

**ISA return without reversion.** Enable ISA 1/2 on seg1. With non-revertive operation, seg2 remains OA.

![T3: ISA return without reversion](topology-scenarios/T3-paths.svg)

## T4

**Automatic revertive return.** Enable seg1 ISA with revertive true. After eligibility conditions are met, OA seg2 → seg1.

![T4: Automatic revertive return](topology-scenarios/T4-paths.svg)

## T5

**Single LAG member failure.** Disable seg1 port 1/1/1: LAG 12 member A. Member B, port 1/1/2, remains enabled.

![T5: Single LAG member failure](topology-scenarios/T5-paths.svg)

## T6

**Direct LAG 12 failure.** Disable seg1 ports 1/1/1 and 1/1/2. MIMP/MCS uses the alternate path through seg3.

![T6: Direct LAG 12 failure](topology-scenarios/T6-paths.svg)

## T7

**OA failure with core BFD.** Kill seg1 CPM and IOM. Restore seg1 only after traffic has recovered through seg2.

![T7: OA failure with core BFD](topology-scenarios/T7-paths.svg)

## T7-noBFD

**OA failure without core BFD.** Kill seg1 CPM and IOM with core BGP BFD disabled. Main arrows show forwarding after hold expiry.

![T7-noBFD: OA failure without core BFD](topology-scenarios/T7-noBFD-paths.svg)

## T8

**Both DAs fail: normal pool.** Kill seg1 and seg2 CPM/IOM components. Traffic must recover on DS seg3 before the DAs restart.

![T8: Both DAs fail: normal pool](topology-scenarios/T8-paths.svg)

## T8r

**Both DAs return: normal pool.** Start seg1 and seg2 CPM/IOM components. In the accepted measurement, seg3 remains OA.

![T8r: Both DAs return: normal pool](topology-scenarios/T8r-paths.svg)

## T9

**Both DAs fail: HA pool.** Kill seg1 and seg2 CPM/IOM components. Synchronized states are preloaded on the seg3 HA pool ISA.

![T9: Both DAs fail: HA pool](topology-scenarios/T9-paths.svg)

## T9r

**Both DAs return: HA pool.** Start seg1 and seg2 CPM/IOM components. In the accepted measurement, seg3 remains OA.

![T9r: Both DAs return: HA pool](topology-scenarios/T9r-paths.svg)

## T10-seg2

**Public shunting through seg2.** Pin the gateway /32 on the core through seg2; shunting profiles remain enabled.

![T10-seg2: Public shunting through seg2](topology-scenarios/T10-seg2-paths.svg)

## T10b-seg2

**Public shunt disabled on seg2.** Keep routes pinned through seg2; remove only the public shunting profile on seg2.

![T10b-seg2: Public shunt disabled on seg2](topology-scenarios/T10b-seg2-paths.svg)

## T11-seg2

**Private shunting through seg2.** Pin both inner /32 routes on the core through seg2; shunting profiles remain enabled.

![T11-seg2: Private shunting through seg2](topology-scenarios/T11-seg2-paths.svg)

## T11b-seg2

**Private shunt disabled on seg2.** Keep routes pinned through seg2; remove only the private shunting profile on seg2.

![T11b-seg2: Private shunt disabled on seg2](topology-scenarios/T11b-seg2-paths.svg)

## T10-seg3

**Public shunting through seg3.** Pin the gateway /32 on the core through seg3; shunting profiles remain enabled.

![T10-seg3: Public shunting through seg3](topology-scenarios/T10-seg3-paths.svg)

## T10b-seg3

**Public shunt disabled on seg3.** Keep routes pinned through seg3; remove only the public shunting profile on seg3.

![T10b-seg3: Public shunt disabled on seg3](topology-scenarios/T10b-seg3-paths.svg)

## T11-seg3

**Private shunting through seg3.** Pin both inner /32 routes on the core through seg3; shunting profiles remain enabled.

![T11-seg3: Private shunting through seg3](topology-scenarios/T11-seg3-paths.svg)

## T11b-seg3

**Private shunt disabled on seg3.** Keep routes pinned through seg3; remove only the private shunting profile on seg3.

![T11b-seg3: Private shunt disabled on seg3](topology-scenarios/T11b-seg3-paths.svg)

## T12

**Shunting on surviving member B.** Disable seg1 port 1/1/1, switch OA to seg2 and pin public/private routes through seg1.

![T12: Shunting on surviving member B](topology-scenarios/T12-paths.svg)

## T13a

**Sequential failure: first DA, normal pool.** Kill seg1 CPM/IOM. Keep seg1 off; verify seg2 forwarding and seg2/seg3 MCS inSync, then observe 30 s.

![T13a: Sequential failure: first DA, normal pool](topology-scenarios/T13a-paths.svg)

## T13b

**Sequential failure: second DA, normal pool.** With seg1 still off and seg2 forwarding verified, kill seg2 CPM/IOM. Observe traffic through seg3 for 30 s.

![T13b: Sequential failure: second DA, normal pool](topology-scenarios/T13b-paths.svg)

## T13r

**DA return after sequential failure, normal pool.** Start both DAs after seg1 → seg2 → seg3 failover. Record the election; require preserved IKE and nominal.

![T13r: DA return after sequential failure, normal pool](topology-scenarios/T13r-paths.svg)

## T14a

**Sequential failure: first DA, HA pool.** Kill seg1 CPM/IOM with HA pool on seg3. Keep seg1 off; verify seg2 forwarding and MCS inSync, then observe 30 s.

![T14a: Sequential failure: first DA, HA pool](topology-scenarios/T14a-paths.svg)

## T14b

**Sequential failure: second DA, HA pool.** After verified seg2 operation, kill seg2 CPM/IOM while seg1 stays off. Observe HA pool takeover on seg3 for 30 s.

![T14b: Sequential failure: second DA, HA pool](topology-scenarios/T14b-paths.svg)

## T14r

**DA return after sequential failure, HA pool.** Start both DAs after sequential HA takeover on seg3. Record the election; require preserved IKE and nominal.

![T14r: DA return after sequential failure, HA pool](topology-scenarios/T14r-paths.svg)
