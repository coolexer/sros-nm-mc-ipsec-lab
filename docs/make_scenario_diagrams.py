"""Generate deterministic SVG traffic-path diagrams using only the standard library."""
from html import escape
from pathlib import Path
import textwrap
from scenario_topology import draw_topology, write_gallery

OUT = Path(__file__).with_name('scenarios')
BLUE, GREEN, RED, GRAY = '#2563eb', '#14804a', '#c42b32', '#64748b'


def text(x, y, value, size=16, color='#17233c', anchor='middle'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(value)}</text>'


def box(x, y, w, h, label, color=BLUE, fill='#f1f5ff'):
    result = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{color}" stroke-width="2"/>']
    lines = label.split('|')
    for i, line in enumerate(lines):
        result.append(text(x+w/2, y+h/2+(i-(len(lines)-1)/2)*21+5, line, 16, color))
    return result


def traffic(y, labels, blocked=None):
    result = []
    width = (1120 - 28*(len(labels)-1))/len(labels)
    for i, label in enumerate(labels):
        x = 40+i*(width+28)
        color = RED if i == blocked else GRAY if blocked is not None and i > blocked else BLUE
        result.extend(box(x, y, width, 70, label, color))
        if i < len(labels)-1:
            inactive = blocked is not None and i >= blocked
            dash = ' stroke-dasharray="4 4"' if inactive else ''
            marker = 'arrow-blocked' if inactive else 'arrow'
            result.append(f'<path d="M {x+width+3} {y+35} h 20" stroke="{RED if inactive else BLUE}" stroke-width="3" fill="none" marker-end="url(#{marker})"{dash}/>')
            if i == blocked:
                result.append(text(x+width+14, y+23, '×', 28, RED))
    return result


def draw(test, title, active='seg1', public=None, private=None, down=(), isa=(),
         block=None, ports=None, note='MIMP/MCS full mesh; all peers reachable'):
    public, private = public or active, private or active
    draw_topology(test, active, public, private, down, isa, block, ports)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720" font-family="Arial, sans-serif">',
           '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8z" fill="#2563eb"/></marker><marker id="arrow-blocked" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8z" fill="#c42b32"/></marker></defs>',
           '<rect width="1200" height="720" fill="white"/>',
           text(40, 38, test + '  ' + title, 23, anchor='start'),
           text(40, 65, 'Logical paths after the action; Base and VPRN 100 are instances of the same ipmpls router', 15, GRAY, 'start')]
    for i, node in enumerate(('seg1', 'seg2', 'seg3')):
        designated = 'DA  priority ' + ('200' if node == 'seg1' else '100') if node != 'seg3' else 'DS  priority 200'
        state = 'NODE OFF' if node in down else 'ISA OFF' if node in isa else 'OA  encrypt / decrypt' if node == active else 'standby'
        color = RED if node in down or node in isa else GREEN if node == active else GRAY
        out.extend(box(40+390*i, 92, 340, 85, node + '  ' + designated + '|' + state, color, '#f4f8f6' if node == active else '#f8fafc'))
    out.append(text(40, 211, 'Forward  eNB to MME', 19, anchor='start'))
    f = ['eNB1 / eNB2|10.100.x.1', 'ipmpls Base|ESP to GW /32']
    f += [public + '|public ingress', active + '|ISA decrypt'] if public != active else [active + '|ISA decrypt']
    f += ['ipmpls VPRN|clear inner IP', 'MME|10.200.0.10']
    out.extend(traffic(232, f, 2 if block == 'public' else None))
    out.append(text(40, 337, 'ESP: eNB → gateway 198.51.100.1; after ISA decryption: inner IP → 10.200.0.10', 15, GRAY, 'start'))
    out.append(text(40, 382, 'Return  MME to eNB', 19, anchor='start'))
    r = ['MME|10.200.0.10', 'ipmpls VPRN|10.100.x.1 /32']
    r += [private + '|private ingress', active + '|ISA encrypt'] if private != active else [active + '|ISA encrypt']
    r += ['ipmpls Base|ESP to eNB', 'eNB1 / eNB2|10.100.x.1']
    out.extend(traffic(403, r, 2 if block == 'private' else None))
    out.append(text(40, 507, 'Inner IP reaches the OA before encryption; the encrypted return packet uses the public Base instance', 15, GRAY, 'start'))
    if public != active:
        label = (f'Public shunt disabled on {public}: ESP cannot reach the OA {active}' if block == 'public' else
                 f'Public shunt: {public} → {active}; dedicated peer next-hop, no decryption on the standby')
        out.append(text(40, 548, label, 16, RED if block == 'public' else BLUE, 'start'))
    if private != active:
        label = (f'Private shunt disabled on {private}: inner IP cannot reach the OA {active} ISA' if block == 'private' else
                 f'Private shunt: {private} → {active}; inner IP is forwarded to the active ISA')
        out.append(text(40, 577, label, 16, RED if block == 'private' else BLUE, 'start'))
    for i, line in enumerate(textwrap.wrap(note, 118)):
        out.append(text(40, 620+23*i, line, 16, GRAY, 'start'))
    if ports:
        out.append(text(40, 681, 'LAG 12 member A: ' + ports[0] + '    member B: ' + ports[1] + '    compact: both on MDA 1/1', 16, RED if ports[1] == 'DOWN' else GREEN, 'start'))
    out.append('</svg>')
    (OUT / (test + '.svg')).write_text('\n'.join(out), encoding='utf-8', newline='\n')


def main():
    OUT.mkdir(exist_ok=True)
    draw('T0', 'Baseline; no fault')
    draw('T1', 'Planned auto switchover to the second DA', active='seg2')
    draw('T1b', 'Planned return after nominal', active='seg1')
    draw('T2', 'Disable ISA 1/2 on seg1', active='seg2', isa=('seg1',))
    draw('T3', 'Restore ISA; non-revertive operation', active='seg2')
    draw('T4', 'Automatic revertive return after eligibility', note='Revertive configured on standby before measurement; seg1 must remain standby and nominal for the eligibility interval')
    draw('T5', 'Disable one direct LAG 12 member', ports=('DOWN', 'UP'))
    draw('T6', 'Disable both direct LAG 12 members', ports=('DOWN', 'DOWN'), note='MIMP/MCS path after LAG 12 loss: seg1 → LAG 13 → seg3 → LAG 23 → seg2; OA stays seg1')
    draw('T7', 'Kill seg1 CPM and IOM; BFD enabled', active='seg2', down=('seg1',), note='MIMP elects seg2; core withdraws failed next-hop using BFD/BGP; traffic must recover BEFORE seg1 is restarted')
    draw('T7-noBFD', 'Same fault without BFD; eventual recovered path', active='seg2', down=('seg1',), note='Before hold expiration: core → dead seg1 = blackhole, even while seg2 is already OA. Only the recovered path is drawn here')
    draw('T8', 'Kill both DAs; normal DS pool', active='seg3', down=('seg1', 'seg2'), note='seg3 is eligible while isolated; pool allocates ISA and CPM downloads states on takeover; both DAs remain off until recovery')
    draw('T8r', 'Start both DAs; observe the election', active='seg3', note='Shown outcome: OA stays seg3. Require unique OA, preserved IKE, nominal on all nodes; zero loss when OA stays seg3')
    draw('T9', 'Kill both DAs; HA pool', active='seg3', down=('seg1', 'seg2'), note='Before fault: high-availability tunnel-limit-32k pre-downloads synced states to seg3 ISA. Preparation and its restart are outside measurement')
    draw('T9r', 'Start both DAs after HA takeover', active='seg3', note='Shown outcome: OA stays seg3. Record actual election; require stateful recovery and nominal; restore normal pool after the case')
    for target in ('seg2', 'seg3'):
        draw('T10-'+target, 'Public route pinned to ' + target, public=target)
        draw('T10b-'+target, 'Remove public shunt profile on ' + target, public=target, block='public', note='Expected negative control: both eNB flows stop; no finite recovery time is claimed before restoring the profile')
        draw('T11-'+target, 'Private routes pinned to ' + target, private=target)
        draw('T11b-'+target, 'Remove private shunt profile on ' + target, private=target, block='private', note='Expected negative control: return traffic stops on the selected standby; restore profile before the next case')
    draw('T12', 'Member A off; OA seg2; both directions pinned to seg1', active='seg2', public='seg1', private='seg1', ports=('DOWN', 'UP'), note='Both public and private shunts cross LAG 12 on surviving member B. Control-plane reachability alone cannot prove this data path')
    write_gallery()


if __name__ == '__main__':
    main()
