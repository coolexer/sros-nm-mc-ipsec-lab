# N:M MC-IPsec functional validation

The [customer test program](docs/TEST-PROGRAM.md) provides detailed actions, packet paths,
acceptance and restoration. The [topology gallery](docs/TOPOLOGY-TESTS.md) shows the full lab,
disabled components and request/reply arrows for each measurement window.

Run `python3 -m unittest discover -s tests -v`, then `./tests/nm_tests.sh all`.
`T2` includes the `T3` ISA recovery measurement. Node failure and return use one continuous
traffic trace rather than separate T7/T7r windows. Individual case names are printed by the runner.

The runner uses the lab name in the topology YAML. Set `TOPOLOGY=filename.clab.yml` if the directory
contains multiple topology files. No operation targets a device outside that lab prefix.

## Configuration

Three SR-7 SecGWs use SR-SIM 26.7.R2. seg1 and seg2 are designated active, with priorities 200/100;
seg3 is designated standby, priority 200, with an ISA member pool. All have one active MS-ISA2.

Each pair has a two-member LACP LAG. The compact profile puts both ports on MDA 1/1;
the reference dual-IOM profile distributes members across IOM 1 and IOM 2. Base VLAN 1 carries OSPF, MIMP/MCS
reachability and public shunting; VPRN VLAN 3 carries private shunting. LAG IDs are 12, 13 and 23.
The redundant members now protect shunting as well as the control transport. The direct pair's
entire LAG is still required for direct shunting between that pair; transit OSPF connectivity
through the third node does not make a failed direct shunt work.

SecGW export policies use MED 100/200/1000 for master-with-peer, master-without-peer and non-master.
Both SecGW BGP core groups use MRAI 1 second. Core BGP uses BFD except during T7-noBFD.
All BGP groups use connect-retry 5 seconds; the SR OS default is 120 seconds.
Use `show router bfd session` to observe negotiated intervals; configured intervals alone are not
the actual detection time. In the current SR-SIM environment some sessions negotiate 1000 ms.

All routers use NTP at 172.20.30.123 over management. The lab chronyd uses the common WSL kernel
clock as a stratum-10 local reference and runs with `-x`: it never adjusts the host clock. This
provides a shared lab reference, not an independent externally disciplined production time source.

IKE/ESP settings retain responder-only, DPD reply-only 300/3, IKE lifetimes 172800/86400 and CHILD
lifetimes 7200/3600. Tests require established IKE and installed CHILD SAs on both eNBs.

Pool-mode preparation requires a unique OA on seg1/seg2 before maintenance.
To enable HA, the runner stops only the DA
CPM/IOM components, disables seg3 ISA, changes and saves the mode, and cold-starts both its CPM
and IOM. The core, eNBs and distributed network namespace helpers remain running. It enables and
saves the ISA, observes it for 60 seconds, starts the DAs sequentially, then checks stable traffic
and nominal. Returning to the normal pool disables its ISA, changes/saves mode, restarts the IOM,
enables/saves the ISA and checks readiness. All maintenance is outside measured failover windows.
This is the SR-SIM lab preparation procedure; hardware maintenance requires the platform procedure.

HA preparation requires at least 10 GiB physical MemAvailable after stopping the DAs; swap does
not qualify. The seg3 IOM has a cgroup ceiling of 8 GiB RAM / 9 GiB RAM+swap.
The default compact profile validates port redundancy with one IOM per SecGW.

## Preconditions and verdicts

Before each independent case: all CLIs respond, exactly one OA exists, all nodes agree on Current
Active, protection is nominal, two tunnels are installed on the OA, both eNBs have IKE/CHILD SAs,
and the public /32 plus both private /32 routes point to the expected OA.
Each SecGW must also have BGP forwarding routes to both public eNB subnets and the private MME
subnet. MIMP/MCS nominal and an installed tunnel alone do not prove those routes have arrived.
Every planned switchover checks the target's forwarding routes before issuing the command.

Each planned switchover separately waits for nominal. Recovery cases deliberately start with a
failed ISA/node and use explicit exceptions to nominal, while checking their expected routes/SAs.
Shunting controls explicitly expect routes on the selected standby.

Baseline setup sends bounded readiness probes outside measurement windows, retrying for at most
90 seconds until both eNBs receive all 20 replies in a batch. Readiness logs retain the SA listing
before and after each probe. Readiness and measured fault windows are separate.

Every traffic window starts with at least ten consecutive successful replies per eNB and no
initial missing replies. Failed preconditions stop the series with INVALID and diagnostics.
There is no automatic peer-domain reset when protection sticks at notReady.

PASS requires the expected unique OA, both original nonempty IKE SPI pairs preserved, installed
CHILD SAs, and recovered traffic on both eNBs. `none` additionally requires zero packet loss.
The negative shunting controls require loss and an unrecovered tail on both eNBs; their lost
traffic is expected and their gap is a test-window bound, not recovery time.

Command/SSH errors and timeouts stop the series and return a nonzero exit code. Cleanup restores
nodes, ISA, member ports, BFD and shunt profiles, removes route pinning, clears revertive on a
standby if necessary, and verifies a nominal seg1 baseline. A cleanup failure is reported explicitly.

## Measurements and records

Ping uses `-D -O -i 0.1 -W 1` from each eNB's inner address. START/STOP timestamps are captured
inside the probe containers. The parser counts transmitted/received packets and includes initial,
interior and trailing intervals without replies. Full loss has a nonzero gap. A stable endpoint
requires ten consecutive sequence numbers and a recent reply. During active tests those ten
replies must be newer than the most recent control action. If stable recovery is not observed,
the gap is reported as not recovered; no finite recovery time is claimed.

Each invocation writes a separate `results/YYYYMMDD-HHMMSS/` with metadata, runner SHA-256,
per-case logs, original ping traces, `results.json` and `SUMMARY.md`. Failures also capture
domain/MCS/ISA/tunnel/event/LAG diagnostics. Previous results are not overwritten.

At 10 pps, resolution is about 100 ms, with additional host scheduling noise. SR-SIM timings do not
establish hardware SLA or scale performance. Two tunnels and a single observation per mode do
not establish a statistically significant HA improvement.

## Scenarios

| Case | Action | Required result |
|---|---|---|
| T0 | Traffic without fault | seg1; no loss |
| T1/T1b | Force auto to seg2, wait nominal, force back | Stateful DA→DA switchovers; recovered traffic |
| T2/T3 | Disable ISA on seg1, then restore | seg2 takes OA; restoring ISA is non-revertive and has no loss |
| T4 | Set revertive while seg1 ISA is disabled and seg2 is OA; enable ISA | seg1 automatically takes OA; config toggle excluded from action window |
| T5 | Disable seg1 member 1/1/1 | seg1 stays OA; no loss |
| T6 | Disable both seg1 members of LAG 12 | MIMP/MCS reroutes via seg3; nominal and no loss |
| T7 | Kill seg1 CPM and its IOM components; wait for traffic recovery; start seg1 | seg2 takes OA; same IKE; no additional missing sequences during node return |
| T7-noBFD | Same with core BFD disabled | Recovery must be observed before restart, even if it needs the BGP hold timeout |
| T8/T8r | Kill both DAs, normal DS pool; measure their return separately | Surviving seg3 forwards with preserved IKE; after DA return require unique OA, nominal and preserved IKE. Record election outcome; no loss if OA stays seg3 |
| T9/T9r | Same with HA pool; save configuration; restore pool mode afterwards | Same checks with HA explicitly configured; do not infer statistical speedup from one run |
| T10 | Pin public route to seg2, then seg3 | Public shunting works through each standby with zero loss |
| T10b | Remove public shunt profile on the selected standby | Both eNBs lose traffic until restoration |
| T11/T11b | Equivalent private-route pinning/profile removal | Private shunting works, and its removal blocks both eNBs |
| T12 | Disable member A, switch OA to seg2, pin both traffic directions to former OA | Shunting over surviving member B restores and sustains both flows |

## Nokia references

- [N:M behavior, shunting and deployment requirements](https://documentation.nokia.com/sr/26-7/7750-sr/books/ms-isa-esa/ip-tunnels.html)
- [Revertive admin-state warning](https://documentation.nokia.com/sr/26-7/7750-sr/books/md-cli-command-reference/redundancy-redundancy_0.html#d43733)
- [LACP configuration](https://documentation.nokia.com/sr/26-7/7750-sr/books/interface-configuration/lag.html)
