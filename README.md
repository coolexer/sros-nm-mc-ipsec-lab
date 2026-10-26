# SR OS N:M MC-IPsec security gateway lab (containerlab, SR-SIM 26.7)

A containerlab lab that reproduces a three-node **N:M multi-chassis IPsec** security gateway (SecGW) on
Nokia 7750 SR-7 **SR-SIM 26.7.R2**, with real IKEv2/ESP traffic from strongSwan "eNB" emulators. It
includes an automated switchover test runner.

- [Customer test program](TEST-PROGRAM.md) describes every action, both packet directions,
  acceptance and recovery, with a full topology view for each measured window.
- [Per-test topology gallery](TOPOLOGY-TESTS.md) shows disabled components and request/reply
  arrows for all 29 windows. Companion packet-processing diagrams are linked from the gallery.
- [Editable diagram workbook](docs/lab-diagrams.drawio) contains all 61 diagrams as native
  draw.io shapes, text and connectors. See [editing diagrams](#editing-diagrams).
- [RESULTS.md](RESULTS.md) contains the accepted measurements, their source traces and final
  operational state.
- [Operating conditions](OPERATIONAL-NOTES.md) covers resources, pool preparation and restoration.

![topology](docs/topology.svg)

![redundancy logic](docs/redundancy-logic.svg)

## What is modelled

| Node | Role | Hardware (SR-SIM) |
|---|---|---|
| `seg1` | SecGW, **designated active (DA)**, priority 200 | 7750 SR-7, CPM5, one `iom4-e`, network MDA 1/1 and MS-ISA2 1/2 |
| `seg2` | SecGW, **designated active (DA)**, priority 100 | same |
| `seg3` | SecGW, **designated standby (DS)**, priority 200, ISA in a `tunnel-member-pool` | same |
| `ipmpls` | "IP/MPLS" core: Base = public side, VPRN `mobile` = private side | 7750 SR-1 |
| `enb1`, `enb2` | IKEv2 PSK initiators (strongSwan 5.9) with inner addresses 10.100.x.1 | Linux |
| `mme` | traffic target 10.200.0.10 behind the private side | Linux |
| `ntp` | shared time reference, management 172.20.30.123 | Linux, chronyd with host-clock adjustment disabled |

All three SecGWs are in one N:M redundancy domain (`ipsec-domain 1` ↔ `tunnel-group 1`), with one
MS-ISA2 per node (`active-isa-number 1`):

- Every pair uses a **two-member LACP LAG**. Both control traffic and public/private
  shunting survive one member failure. OSPF routes MIMP/MCS between system addresses.
- The gateway address 198.51.100.1 is the same on all nodes. It and the reverse routes are announced
  to the core over eBGP. The MED depends on the MIMP state: `ipsec-master-with-peer` 100,
  `ipsec-master-without-peer` 200, `ipsec-non-master` 1000.
- The core BGP sessions use BFD.
- SecGW export groups use a one-second BGP MRAI. All nodes use a shared lab NTP reference.
- BGP groups retry TCP connections after five seconds to avoid long boot-time reconnect waits.
- The SecGWs are responder-only, use DPD `reply-only`, and have longer IKE/CHILD lifetimes than the
  eNBs. These are the SR OS MC-IPsec deployment requirements.

## Requirements

- Linux or WSL2 with Docker and **containerlab ≥ 0.80**. The `sfm:` key is at node level, which needs
  0.80.
- Image `registry.srlinux.dev/pub/nokia_srsim:26.7.R2`.
- An **SR-SIM license valid for 26.7**, saved as `license.txt` in the repo root. It is not included.
- Python 3 on the host. The runner uses the standard library; `shellcheck` is optional for checking helpers.
- The compact profile uses one IOM per SecGW. HA preparation is an offline maintenance phase:
  it temporarily stops both DA CPM/IOM components, keeps network namespaces, core and eNBs
  running, and requires **10 GiB physical MemAvailable** before allocation (swap does not count).
  The DS IOM is capped at 8 GiB RAM / 9 GiB RAM+swap.
  See [operational conditions and preparation](OPERATIONAL-NOTES.md).
- `sshpass` on the host, used by the CLI helper scripts.
- The VS Code **containerlab** extension is optional. The `*.annotations.json` file gives the
  TopoViewer layout.

## Quick start

```bash
docker build -t enb-strongswan:local images/enb        # strongSwan on top of network-multitool
cp /path/to/your/srsim-26.7-license.txt license.txt
python3 gen_configs.py                                  # (re)generates configs/ ; already committed
sudo containerlab deploy -t nm-mc-ipsec.clab.yml --reconfigure  # fresh generated config; resets saved device config
python3 -m unittest discover -s tests -v
./tests/nm_tests.sh T0                                  # baseline check
./tests/nm_tests.sh all                                 # full 29-window program; includes offline HA preparation
latest=$(find results -mindepth 1 -maxdepth 1 -type d -name '20*' | sort | tail -1)
cat "$latest/SUMMARY.md"
```

The eNBs start IKE automatically and keep retrying until the SecGWs are up. If they gave up, run:
`docker exec clab-nm-mc-ipsec-enb1 swanctl --initiate --child s1u`.

The default compact topology validates port redundancy with both LAG members on one MDA.
It does not model the independent IOM/MDA placement required for hardware deployment.
For that reference layout, generate with `python3 gen_configs.py --dual-iom` and deploy
`profiles/dual-iom.clab.yml`; set `TOPOLOGY=profiles/dual-iom.clab.yml` when running tests.
The two-IOM profile requires a larger resource budget and is provided as a reference layout.
The published measurements use compact. Run `python3 gen_configs.py` again before returning to compact.

## Repository layout

| Path | Content |
|---|---|
| `nm-mc-ipsec.clab.yml` | containerlab topology |
| `nm-mc-ipsec.clab.yml.annotations.json` | TopoViewer layout: groups, role labels, notes |
| `gen_configs.py` | single source of truth for addressing; generates `configs/*.partial.cfg` (MD-CLI) and the strongSwan configs |
| `configs/` | generated SR OS partial startup configs, eNB start script and `swanctl.conf` |
| `images/enb/Dockerfile` | eNB image (strongSwan) |
| `sros.sh` | run MD-CLI commands on a node over SSH (`./sros.sh seg1 'show ...'`) |
| `apply_cfg.sh` | merge and commit an MD-CLI snippet on one or more nodes |
| `TEST-PROGRAM.md` | complete customer test program, actions, traffic paths and acceptance criteria |
| `TOPOLOGY-TESTS.md` | per-test topology gallery and packet-processing diagrams |
| `RESULTS.md` | accepted measurements, source evidence and final operational state |
| `tests/nm_tests.sh` / `nm_tests.py` | test runner, see TEST-PROGRAM.md |
| `tests/ping_metrics.py` / `test_runner.py` | probe parser and regression checks |
| `results/validated-compact-*/` | current run metadata, logs, JSON results and original ping traces; see RESULTS.md for provenance |
| `OPERATIONAL-NOTES.md` | resource conditions, pool preparation and final operational checks |
| `docs/topology-scenarios/`, `docs/scenarios/` | full per-test topologies and companion packet-processing diagrams |
| `docs/make_scenario_diagrams.py` | regenerates both diagram sets and the topology gallery |
| `docs/lab-diagrams.drawio` | editable workbook: three overview pages and topology/processing pages for all 29 windows |
| `docs/make_editable_diagrams.py` | builds the editable workbook from the published SVG elements, using Python's standard library |

## Editing diagrams

Download [lab-diagrams.drawio](docs/lab-diagrams.drawio) using GitHub's **Download raw file**
button. Open it in [diagrams.net](https://app.diagrams.net/) or draw.io Desktop with
**File > Open from > Device**.

The workbook contains 61 pages: **Overview - compact**, **Overview - dual IOM**,
**Redundancy logic**, and a **topology** and **processing** page for each test window.
Nodes, component cards, text and connectors are editable objects. Move a node by dragging
its outer card; double-click a label to edit its text. Connection endpoints are attached
to device/component cards, and intermediate waypoints can be moved independently.
Use **View > Layers** to show or hide **Frames**, **Physical links**, **Devices**,
**Traffic and fault markers**, and **Notes**. **Fit Window** (`Ctrl+Shift+H`) fits the page.

Save your edits as `.drawio`. To update a diagram in the GitHub documents, export the
corresponding page with **File > Export as > SVG** and replace its existing SVG in `docs/`.
If **Include a copy of my diagram** is enabled, select **Current Page** to embed only
that page's editable data in its SVG.
The workbook page names identify the test and view; `T12 - topology`, for example, maps
to `docs/topology-scenarios/T12-paths.svg`, and `T12 - processing` maps to
`docs/scenarios/T12.svg`. The three overview pages map to `docs/topology.svg`,
`docs/topology-dual-iom.svg` and `docs/redundancy-logic.svg` respectively.

`python3 docs/make_editable_diagrams.py` rebuilds the workbook from the lab generators'
SVG elements. This replaces the workbook, so save a separate copy of manual `.drawio`
edits before rebuilding it. The scenario SVG generator similarly replaces its generated
SVGs when run.

## Useful commands

```bash
./sros.sh seg1 'show redundancy multi-chassis ipsec-domain 1'      # role, activity state, protection status
./sros.sh seg1 'show redundancy multi-chassis sync'                # MCS state per peer
./sros.sh seg1 'show ipsec gateway name "enb-gw" tunnel'           # dynamic tunnels
./sros.sh ipmpls 'show router bgp routes 198.51.100.1/32'          # which SecGW the core prefers
docker exec clab-nm-mc-ipsec-enb1 swanctl --list-sas
```

## Disclaimer

This is a lab for functional behaviour. SR-SIM emulates the control and management plane and limits
port throughput to 1000 pps. The absolute switchover times are therefore **not** representative of
hardware. Compare the scenarios with each other instead. This is not an official Nokia deliverable.
