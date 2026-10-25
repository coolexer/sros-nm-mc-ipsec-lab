"""Full compact-topology views, using the scenario generator's existing state data."""
from html import escape
from pathlib import Path

OUT = Path(__file__).with_name('topology-scenarios')
FWD, REV, OFF, OA, CONTROL = '#005aff', '#c46a00', '#c62828', '#008653', '#087f8c'
INK, GRAY = '#122344', '#68788f'
NODES = {'seg1': (700, 270), 'seg2': (700, 650), 'seg3': (1210, 465)}
PUBLIC = {
    'seg1': [(560, 405), (620, 405), (620, 365), (700, 365)],
    'seg2': [(560, 535), (645, 535), (645, 745), (700, 745)],
    'seg3': [(400, 325), (400, 230), (1520, 230), (1520, 560), (1490, 560)],
}
PRIVATE = {
    'seg1': [(560, 445), (645, 445), (645, 400), (700, 400)],
    'seg2': [(560, 575), (620, 575), (620, 780), (700, 780)],
    'seg3': [(360, 325), (360, 210), (1550, 210), (1550, 595), (1490, 595)],
}
PEERS = {
    ('seg1', 'seg2'): [[(820, 430), (820, 650)], [(850, 430), (850, 650)]],
    ('seg1', 'seg3'): [[(980, 340), (1270, 465)], [(980, 360), (1290, 465)]],
    ('seg2', 'seg3'): [[(980, 715), (1270, 625)], [(980, 735), (1290, 625)]],
}
ACTIONS = {
    'T0': ('Baseline forwarding', 'No component is disabled. Both eNBs send traffic through OA seg1.'),
    'T1': ('Planned switchover', 'Run force-switchover auto on seg1: OA seg1 → seg2.'),
    'T1b': ('Planned return', 'Run force-switchover to 10.0.0.1 on seg2: OA seg2 → seg1.'),
    'T2': ('Active ISA failure', 'Disable ISA 1/2 on seg1. Its CPM/IOM and network interfaces remain enabled.'),
    'T3': ('ISA return without reversion', 'Enable ISA 1/2 on seg1. With non-revertive operation, seg2 remains OA.'),
    'T4': ('Automatic revertive return', 'Enable seg1 ISA with revertive true. After eligibility conditions are met, OA seg2 → seg1.'),
    'T5': ('Single LAG member failure', 'Disable seg1 port 1/1/1: LAG 12 member A. Member B, port 1/1/2, remains enabled.'),
    'T6': ('Direct LAG 12 failure', 'Disable seg1 ports 1/1/1 and 1/1/2. MIMP/MCS uses the alternate path through seg3.'),
    'T7': ('OA failure with core BFD', 'Kill seg1 CPM and IOM. Restore seg1 only after traffic has recovered through seg2.'),
    'T7-noBFD': ('OA failure without core BFD', 'Kill seg1 CPM and IOM with core BGP BFD disabled. Main arrows show forwarding after hold expiry.'),
    'T8': ('Both DAs fail: normal pool', 'Kill seg1 and seg2 CPM/IOM components. Traffic must recover on DS seg3 before the DAs restart.'),
    'T8r': ('Both DAs return: normal pool', 'Start seg1 and seg2 CPM/IOM components. In the accepted measurement, seg3 remains OA.'),
    'T9': ('Both DAs fail: HA pool', 'Kill seg1 and seg2 CPM/IOM components. Synchronized states are preloaded on the seg3 HA pool ISA.'),
    'T9r': ('Both DAs return: HA pool', 'Start seg1 and seg2 CPM/IOM components. In the accepted measurement, seg3 remains OA.'),
    'T12': ('Shunting on surviving member B', 'Disable seg1 port 1/1/1, switch OA to seg2 and pin public/private routes through seg1.'),
}
GALLERY = []


def label(x, y, value, size=17, color=INK, anchor='start', weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(value)}</text>'


def rect(x, y, w, h, fill='white', stroke='#ccd5e0', width=1.5, radius=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def line(points, color='#b4bfce', width=2, dashed=False, marker=False):
    attrs = ' stroke-dasharray="8 6"' if dashed else ''
    if marker:
        attrs += f' marker-end="url(#m{color[1:]})"'
    coords = ' '.join(f'{x},{y}' for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{attrs}/>'


def cross(x, y, size=10):
    return (f'<circle cx="{x}" cy="{y}" r="{size+5}" fill="white"/>'
            f'<path d="M{x-size},{y-size} L{x+size},{y+size} M{x-size},{y+size} L{x+size},{y-size}" stroke="{OFF}" stroke-width="4"/>')


def peer_path(source, target, member=None):
    pair = tuple(sorted((source, target)))
    points = PEERS[pair][member] if member is not None else [
        ((a[0]+b[0])/2, (a[1]+b[1])/2) for a, b in zip(*PEERS[pair])]
    return points if pair[0] == source else list(reversed(points))


def draw_topology(test, active, public, private, down, isa, block, ports):
    OUT.mkdir(exist_ok=True)
    assert active not in down and active not in isa
    assert public not in down and private not in down
    target = public if block == 'public' else private
    if test.startswith(('T10', 'T11')):
        side = 'public' if test.startswith('T10') else 'private'
        target = public if side == 'public' else private
        title = f'{side.capitalize()} shunt disabled on {target}' if block else f'{side.capitalize()} shunting through {target}'
        action = (f'Keep routes pinned through {target}; remove only the {side} shunting profile on {target}.' if block else
                  f'Pin {"the gateway /32" if side == "public" else "both inner /32 routes"} on the core through {target}; shunting profiles remain enabled.')
    else:
        title, action = ACTIONS[test]
    phase = ('Recovered path before seg1 restart' if test in ('T7', 'T7-noBFD') else
             'Recovered path before both DAs restart' if test in ('T8', 'T9') else
             'Forwarding after the action')
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1160" viewBox="0 0 1600 1160" font-family="Arial, sans-serif">', '<defs>']
    for color in (FWD, REV, OFF, CONTROL):
        out.append(f'<marker id="m{color[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10z" fill="{color}"/></marker>')
    out += ['</defs>', '<rect width="1600" height="1160" fill="white"/>',
            label(35, 43, test+' · '+title, 29, weight=700),
            label(35, 75, 'N:M MC-IPsec · SR-SIM 26.7.R2 · compact · gateway 198.51.100.1/32 · ipsec-domain / tunnel-group 1', 17, GRAY),
            rect(30, 95, 1540, 95, '#f4f7fc'), label(48, 126, action, 19, weight=600),
            label(48, 157, f'{phase}: OA {active}; public ingress {public}; private ingress {private}.', 17, GRAY),
            rect(650, 200, 920, 685, '#f6f9ff', '#d8e2f2'),
            label(680, 261, 'SecGW full mesh: LAG 12 / 13 / 23', 19, weight=600),
            rect(280, 325, 280, 360, '#f1faf7', '#84bca7'),
            label(420, 360, 'ipmpls · one 7750 SR-1', 18, anchor='middle', weight=600),
            label(420, 381, 'AS 65000', 14, GRAY, 'middle')]

    # Physical paths stay visible even when not selected for user traffic.
    for node in NODES:
        unavailable = node in down
        for points in (PUBLIC[node], PRIVATE[node]):
            out.append(line(points, '#d29898' if unavailable else '#aebccc', 2, unavailable))
    enbs = [[(225, 405), (300, 425)], [(225, 550), (260, 550), (260, 465), (300, 465)]]
    mme = [(420, 650), (420, 760)]
    for points in [*enbs, mme]:
        out.append(line(points))
    for pair, members in PEERS.items():
        for i, points in enumerate(members):
            unavailable = any(n in down for n in pair) or (pair == ('seg1', 'seg2') and ports and ports[i] == 'DOWN')
            out.append(line(points, OFF if unavailable else '#9caabd', 3, unavailable))
            if unavailable and not any(n in down for n in pair):
                out.append(cross((points[0][0]+points[-1][0])/2, (points[0][1]+points[-1][1])/2, 8))

    flows = []
    def flow(points, color, offset=0, dashed=False):
        points = [(x+offset, y+offset) for x, y in points]
        flows.append(line(points, 'white', 8))
        flows.append(line(points, color, 4, dashed, True))

    # Forward request: eNB -> Base -> public ingress -> OA -> VPRN -> MME.
    for points in enbs:
        flow(points, FWD, -4)
    flow(PUBLIC[public], FWD, -4)
    if block != 'public':
        if public != active:
            flow(peer_path(public, active, 1 if ports and ports[0] == 'DOWN' else None), FWD, -4)
        flow(list(reversed(PRIVATE[active])), FWD, -4)
        flow(mme, FWD, -5)
        # Return response: MME -> VPRN -> private ingress -> OA -> Base -> eNB.
        flow(list(reversed(mme)), REV, 5)
        flow(PRIVATE[private], REV, 4)
        if block != 'private':
            if private != active:
                flow(peer_path(private, active, 1 if ports and ports[0] == 'DOWN' else None), REV, 4)
            flow(list(reversed(PUBLIC[active])), REV, 4)
            for points in enbs:
                flow(list(reversed(points)), REV, 4)
    if test == 'T6':
        flow(peer_path('seg1', 'seg3'), CONTROL, 9, True)
        flow(peer_path('seg3', 'seg2'), CONTROL, 9, True)
    if test == 'T7-noBFD':
        flow(PUBLIC['seg1'], OFF, 8, True)
        out.append(cross(665, 373))
        out.append(label(1000, 285, 'Before hold expiry: core → seg1 = blackhole', 16, OFF))

    # Independent physical ports avoid crossing the six external core uplinks.
    # P ports belong to Base; V ports belong to VPRN 100. Internal switching is omitted.
    for y, name, info in [(390, 'Base · public', 'ESP / gateway 198.51.100.1'), (550, 'VPRN 100 · private', 'Inner IP / MME network')]:
        out += [rect(300, y, 210, 100, 'white', '#84bca7'),
                label(405, y+36, name, 20, anchor='middle', weight=600),
                label(405, y+66, info, 14, GRAY, 'middle')]
    for node in NODES:
        for side, routes in [('P', PUBLIC), ('V', PRIVATE)]:
            x, y = routes[node][0]
            out.append(f'<circle cx="{x}" cy="{y}" r="4" fill="white" stroke="{GRAY}"/>')
            out.append(label(x if node == 'seg3' else x-10,
                             y+15 if node == 'seg3' else y+4,
                             node[-1]+side, 11, GRAY,
                             'middle' if node == 'seg3' else 'end'))
    for i, y in enumerate((355, 500), 1):
        out += [rect(50, y, 175, 100), label(67, y+28, f'eNB{i} · strongSwan', 16, weight=600),
                label(67, y+55, f'public 100.64.{i}.2', 14, GRAY), label(67, y+80, f'inner 10.100.{i}.1', 14, GRAY)]
    out += [rect(320, 760, 210, 95), label(425, 795, 'MME', 21, anchor='middle', weight=600),
            label(425, 824, '10.200.0.10', 17, GRAY, 'middle')]
    for node, (x, y) in NODES.items():
        dead, isa_off = node in down, node in isa
        returned = (test in ('T8r', 'T9r') and node in ('seg1', 'seg2')) or (test in ('T3', 'T4') and node == 'seg1')
        color = OFF if dead else OA if node == active else GRAY
        role = 'OA · eligible' if node == active and test in ('T8', 'T9') else 'OA' if node == active else 'OFF' if dead else 'standby'
        designated = 'DA' if node != 'seg3' else 'DS'
        priority = 100 if node == 'seg2' else 200
        out += [rect(x, y, 280, 160, '#fff4f4' if dead else '#effaf4' if node == active else 'white', color, 2.5),
                label(x+15, y+29, f'{node} · {designated} · priority {priority}', 18, color, weight=600),
                label(x+15, y+51, f'10.0.0.{node[-1]}     {role}', 16, color)]
        shunt_off = block and node == target
        out += [rect(x+10, y+62, 120, 87, '#fff2f2' if dead or shunt_off else '#f6f8fb', OFF if dead or shunt_off else '#c5cfdb', radius=6),
                label(x+18, y+82, 'CPM + IOM '+('OFF' if dead else 'UP'), 13, OFF if dead else INK),
                label(x+18, y+103, f'{block} shunt OFF' if shunt_off else 'Network MDA 1/1', 12, OFF if shunt_off else GRAY),
                label(x+18, y+122, 'public 1/1/9', 12, GRAY), label(x+18, y+140, 'private 1/1/10', 12, GRAY)]
        isa_color = OFF if dead or isa_off else OA if node == active or returned else GRAY
        out += [rect(x+140, y+62, 130, 87, '#fff0f0' if dead or isa_off else '#f1faf5', isa_color, 2, 6),
                label(x+205, y+84, 'MS-ISA2 · 1/2', 15, isa_color, 'middle', 600),
                label(x+205, y+111, 'OFF' if dead or isa_off else 'encrypt / decrypt' if node == active else 'UP', 14, isa_color, 'middle'),
                label(x+205, y+135, 'RESTORED' if returned else 'pool HA' if node == 'seg3' and test.startswith('T9') else 'pool' if node == 'seg3' else 'tunnel-group 1', 12, isa_color, 'middle')]
        if dead:
            out.append(cross(x+270, y+12, 8))
        if isa_off:
            out.append(cross(x+260, y+73, 7))

    out.extend(flows)
    out += [label(893, 485, 'LAG 12', 17, weight=600),
            label(893, 510, 'A: 1/1/1', 14, OFF if any(n in down for n in ('seg1','seg2')) or ports and ports[0] == 'DOWN' else GRAY),
            label(893, 533, 'B: 1/1/2', 14, OFF if any(n in down for n in ('seg1','seg2')) or ports and ports[1] == 'DOWN' else OA if ports else GRAY),
            label(1040, 322, 'LAG 13 · 2 members', 16, GRAY),
            label(1040, 775, 'LAG 23 · 2 members', 16, GRAY)]
    if test == 'T6':
        out += [label(1040, 350, 'MIMP/MCS → seg3', 16, CONTROL), label(1040, 800, 'MIMP/MCS → seg2', 16, CONTROL)]
    if test == 'T12':
        out.append(label(893, 563, 'Shunt VLAN 1 + 3: B only', 16, OA))
    if block:
        end = PUBLIC[target][-1] if block == 'public' else PRIVATE[target][-1]
        out.append(cross(end[0]+(18 if target == 'seg3' else -18), end[1]))
    out += [rect(30, 900, 1540, 65, '#f5f3ff', '#d3c9ec'),
            label(48, 928, 'NTP · 172.20.30.123', 18, '#65439b', weight=600),
            label(48, 951, 'chronyd -x · management', 14, '#65439b'),
            label(420, 929, 'Shared time reference → seg1 / seg2 / seg3 / ipmpls', 18, '#65439b'),
            label(420, 952, 'Separate management network; NTP is outside the user-traffic path.', 14, '#65439b')]
    for x, color, caption in [(40, FWD, 'Request eNB → MME'), (355, REV, 'Reply MME → eNB'), (670, CONTROL, 'MIMP/MCS in T6')]:
        out += [line([(x, 995), (x+55, 995)], color, 4, color == CONTROL, True), label(x+70, 1001, caption, 17, color)]
    out += [rect(1030, 984, 22, 22, '#effaf4', OA, radius=4), label(1065, 1001, 'OA', 17, OA), cross(1175, 995, 7), label(1195, 1001, 'Disabled / blocked', 17, OFF)]
    fwd = 'eNB → Base → '+public+(f' → public shunt → {active}' if public != active else '')+' ISA decrypt → VPRN → MME'
    ret = 'MME → VPRN → '+private+(f' → private shunt → {active}' if private != active else '')+' ISA encrypt → Base → eNB'
    if block == 'public':
        fwd, ret = f'eNB → Base → {public}: ESP BLOCKED; the request does not reach MME.', 'No MME reply: the request is blocked on the standby public ingress.'
    elif block == 'private':
        ret = f'MME → VPRN → {private}: reply BLOCKED before the shunt to the {active} ISA.'
    out += [label(40, 1045, 'Request: '+fwd, 18, FWD), label(40, 1080, 'Reply: '+ret, 18, REV),
            label(40, 1125, 'Core ports: 1/2/3 = SecGW; P = Base/public, V = VPRN/private. Thin lines: links. Arrows: traffic. LAG members: MDA 1/1.', 16, GRAY), '</svg>']
    (OUT/(test+'-paths.svg')).write_text('\n'.join(out)+'\n', encoding='utf-8', newline='\n')
    GALLERY.append((test, title, action))


def write_gallery():
    assert len(GALLERY) == 23 and len({case for case, _, _ in GALLERY}) == 23
    lines = ['# Per-test topology and traffic paths', '',
             'Each view shows the complete compact lab, the action and the resulting traffic path. '
             'Blue arrows carry requests to MME; orange arrows carry replies to the eNBs. '
             'Green identifies the OA; red identifies a disabled component or a blocked path. '
             'The dashed teal path in T6 is MIMP/MCS reachability, separate from user traffic.', '',
             'Base and VPRN 100 are routing instances of one core router. '
             'Its external ports are labeled by SecGW number and routing instance: P = Base/public, V = VPRN/private. '
             'Internal core switching is omitted; the request and reply sequences state the processing order. '
             'For T7-noBFD, the red dashed path shows the transient blackhole before hold expiry; '
             'the main arrows show recovered forwarding. '
             'T8r/T9r show the accepted outcome with seg3 remaining OA. '
             'Blocking in T10b/T11b is the expected negative-control result.', '',
             '[Detailed test program](TEST-PROGRAM.md) · [Results](../RESULTS.md)', '',
             '| Test | Action | Processing sequence |', '|---|---|---|']
    for case, title, action in GALLERY:
        lines.append(f'| [{case}](#{case.lower()}) | {action} | [Packet processing](scenarios/{case}.svg) |')
    for case, title, action in GALLERY:
        lines += ['', f'## {case}', '', f'**{title}.** {action}', '', f'![{case}: {title}](topology-scenarios/{case}-paths.svg)']
    (OUT.parent/'TOPOLOGY-TESTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')
