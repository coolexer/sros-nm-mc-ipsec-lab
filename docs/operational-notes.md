# Lab operating conditions and restoration

These notes supplement the [test program](TEST-PROGRAM.md) and
[accepted results](../RESULTS.md). Published measurements use the SR-SIM 26.7.R2 compact profile.

## Resources and time

The measured runtime is WSL2 with 12 logical CPUs, 17.15 GiB RAM and 5 GiB swap, on an
Intel i5-1245U host with 32 GiB RAM. Keep the host awake throughout measurement. Allocate
resources with the host's other workloads in mind; swap does not replace physical memory headroom.

Compact uses one IOM and one MS-ISA2 per SecGW. Each pair has two LACP members on one
network MDA, validating port/link failures. The [reference profile](../profiles/dual-iom.clab.yml)
places member B on IOM 2 for separate IOM/MDA failure domains. The accepted measurements
apply to compact.

All four SR OS nodes select NTP `172.20.30.123` over management. Lab chronyd uses local
stratum 10 and runs with `-x`, providing a common WSL-based time reference without adjusting
the host clock. Production uses an agreed external time source. Verify `show system ntp all`
and the selected Clock Source on each router.

## HA pool preparation before T9

Preparation is separate from the measured fault. Start with OA on seg1 or seg2, an agreed
Current Active and nominal on all participants.

1. Stop both DAs' CPM/IOM components, keeping their netns helpers, the core and eNBs running.
   This is offline maintenance and can interrupt existing traffic.
2. Require at least **10 GiB physical MemAvailable** before HA-table allocation.
3. Disable seg3 ISA, set pool `high-availability tunnel-limit-32k` and save configuration.
4. Cold-start seg3 CPM/IOM. Set the IOM cgroup ceiling to 8 GiB RAM / 9 GiB RAM+swap.
   Wait for CLI, enable ISA, wait for operational state and save the enabled configuration.
5. Observe the operational ISA for 60 s. Start the DAs sequentially, checking each CLI
   and its forwarding routes.
6. Wait for both IKE/CHILD sessions, successful readiness probes, nominal and normal routes
   through seg1. Capture T9's reference SPI pairs only after preparation is complete.

These are this lab's operating conditions, not Nokia hardware capacity specifications.
HA 32k defines the pool limit; the program uses two IPsec tunnels. `prepare_pool()` implements
the procedure; pool-preparation logs in the final evidence group record the actual mode and ISA state.

## Return to normal mode

After T9r, return OA to seg1 and maintain standby seg3: disable ISA, set
`high-availability none`, save configuration, restart the IOM, enable ISA and save its
enabled state. Run readiness probes and verify nominal. This maintenance is outside T9/T9r.

Keep core and eNB containers running during pool maintenance. Distributed SecGW namespace
helpers also remain running, preserving data links while CPM/IOM components restart.

## Forwarding routes and shunting

Before a planned switchover, check BGP routes on the target SecGW to both public eNB networks
and the private MME network. Readiness includes forwarding routes, SAs and actual user traffic.

In T10–T12, core neighbor import policies select the required standby. Replace the policy list
within one MD-CLI candidate transaction: delete the old neighbor import chain, set the required
list and commit. Start measurement after checking the actual selected next-hops. Remove
neighbor overrides after the test so the normal group policy applies.

BGP connect-retry is 5 s; SecGW export-group MRAI is 1 s. Core peerings use BFD except in
the T7-noBFD control. Observe negotiated intervals with `show router bfd session`.
Configured intervals and measured failure-detection time are distinct quantities.

The accepted sequential-failure run records MC-IPsec BFD sessions as `cpm-np`, with
operational transmit/receive intervals of 1000 ms and multiplier 3, although the system
interface requests 100 ms. Core BGP BFD sessions are `iom`, operationally 100 ms × 3.
Nokia's [CPM-NP simulation note](https://documentation.nokia.com/acg/24-7-2/books/mpls-classic/c079-mpls-tp.html)
describes the same 1000-ms negotiation floor on simulated CPM-NP sessions. This is consistent
with this lab's operational output; it is not a production MC-IPsec timer recommendation.
Reducing a requested value that is already 100 ms cannot demonstrate faster MC-IPsec detection
while the operational session remains at 1000 ms. Hardware timer validation is a separate test.

## Sequential DA failure

`T13` (normal pool) and `T14` (HA pool) deliberately keep seg1 off after seg2 takes over.
The second failure waits for two installed tunnels on seg2, all three core routes through
seg2, recovered traffic, bidirectional surviving MCS inSync and a 30-s loss-free observation.
Whole-domain protection is notReady while seg1 is absent. The second injected failure
therefore tests degraded operation; it is not an administrative switchover from nominal.
Each mode records separate first-fault, second-fault and DA-return windows while requiring
the same original IKE pairs across all three. No IKE or MCS reset is inserted between faults.

## Final operational acceptance

The program finishes with:

- OA seg1, agreed Current Active 10.0.0.1 and nominal on every SecGW.
- MCS DB Sync State inSync with both peers on each SecGW.
- Both IKE/CHILD sessions installed; two installed tunnels on the OA.
- Core gateway /32 and both private /32 routes through seg1.
- Forwarding routes on every SecGW to both eNB networks and MME.
- Operational ISAs and two active members per LAG.
- Restored shunting profiles, removed route pins, enabled BFD and revertive false.
- Pool mode none and selected NTP on all four SR OS nodes.
- Saved configuration on every router.

The protocol is published as [operational.log](../results/validated-final-state/operational.log).

## Nokia documentation

- [N:M MC-IPsec, HA pool, election and shunting](https://documentation.nokia.com/sr/26-7/7750-sr/books/ms-isa-esa/ip-tunnels.html).
- [SR-SIM shared host resources](https://documentation.nokia.com/sr/26-7/7x50-shared/srsim-installation-setup/sr-sim-overview.html).
- [SR-SIM host requirements](https://documentation.nokia.com/sr/26-7/7x50-shared/srsim-installation-setup/host-machine-requirements.html).
