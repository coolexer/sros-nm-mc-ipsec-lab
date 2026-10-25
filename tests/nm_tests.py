#!/usr/bin/env python3
"""Functional MC-IPsec tests, using stdlib and the existing CLI helper."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from ping_metrics import metrics

ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = ROOT / os.environ.get('TOPOLOGY', next(ROOT.glob('*.clab.yml')).name)
NAME = os.environ.get('LAB_NAME') or re.search(r'^name:\s*(\S+)', TOPOLOGY.read_text(), re.M)[1]
PREFIX = 'clab-' + NAME
SEGS = ('seg1', 'seg2', 'seg3')
DUAL_IOM = 'seg1:2/1/1' in TOPOLOGY.read_text()
MEMBER_B = '2/1/1' if DUAL_IOM else '1/1/2'
RUN = ROOT / 'results' / time.strftime('%Y%m%d-%H%M%S')
LOG = CASE = SPI_BEFORE = None
TRAFFIC = False
AFTER = 0.0
RESULTS = []


class LabError(RuntimeError):
    pass


def log(message):
    line = time.strftime('[%H:%M:%S] ') + str(message)
    print(line, flush=True)
    if LOG:
        with LOG.open('a') as stream:
            stream.write(line + '\n')


def run(args, timeout=50, check=True, input=None):
    result = subprocess.run(args, input=input, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=timeout)
    if check and result.returncode:
        raise LabError(f'Command failed ({result.returncode}): {args}\n{result.stdout}')
    return result.stdout


def docker(node, *args, check=True):
    return run(['docker', 'exec', f'{PREFIX}-{node}', *args], check=check)


def op(node, *commands):
    return run([str(ROOT / 'sros.sh'), node, *commands], timeout=60)


def cfg(node, *commands):
    global AFTER
    output = run([str(ROOT / 'sros.sh'), node], input='\n'.join([
        'edit-config private', *commands, 'exit all', 'commit', 'quit-config', '']))
    if not output.strip() or re.search(r'\b(MINOR|MAJOR|CRITICAL):', output):
        raise LabError(f'Configuration failed on {node}:\n{output}')
    log(f'cfg {node}: {"; ".join(commands)}')
    if TRAFFIC:
        AFTER = time.time()


def action(node, command):
    global AFTER
    output = op(node, command)
    log(output)
    if re.search(r'\b(MINOR|MAJOR|CRITICAL):', output):
        raise LabError(f'Operation failed on {node}')
    if TRAFFIC:
        AFTER = time.time()


def running(node):
    suffix = '-a' if node in SEGS else ''
    return run(['docker', 'inspect', '-f', '{{.State.Running}}',
                f'{PREFIX}-{node}{suffix}'], check=False).strip() == 'true'


def domain(node):
    if not running(node):
        return dict(act='down', prot='unknown', current='unknown', installed=0)
    text = op(node, 'show redundancy multi-chassis ipsec-domain 1')
    result = {}
    for key, label in [('act', 'Activity State'), ('prot', 'Protection Status'), ('current', 'Current Active')]:
        match = re.search(label + r'\s*:\s*(\S+)', text)
        if not match:
            raise LabError(f'Cannot parse {label} on {node}: {text}')
        result[key] = match[1]
    match = re.search(r'^Installed\s+\S+\s+(\d+)', text, re.M)
    result['installed'] = int(match[1]) if match else 0
    return result


def domains():
    return {node: domain(node) for node in SEGS}


def owner(states=None):
    states = states if states is not None else domains()
    candidates = [n for n, s in states.items() if s['act'] in ('active', 'eligible')]
    return candidates[0] if len(candidates) == 1 else 'MULTIPLE:' + ','.join(candidates) if candidates else 'none'


def nominal():
    states = domains()
    active = owner(states)
    return active in SEGS and all(s['prot'] == 'nominal' and
        s['current'] == f'10.0.0.{active[-1]}' for s in states.values())


def paths():
    text = op('ipmpls', 'show router route-table 198.51.100.1/32',
              'show router "100" route-table 10.100.1.1/32', 'show router "100" route-table 10.100.2.1/32')
    result = {}
    for prefix in ('198.51.100.1/32', '10.100.1.1/32', '10.100.2.1/32'):
        match = re.search(r'^' + re.escape(prefix) + r'[^\n]*\n\s*(172\.3[01]\.([123])\.1)\b', text, re.M)
        result[prefix] = 'seg' + match[2] if match else 'missing'
    return result


def routes_to(pub, private):
    table = paths()
    return table['198.51.100.1/32'] == pub and all(table[f'10.100.{n}.1/32'] == private for n in (1, 2))


def forwarding_ready(node):
    prefixes = ('100.64.1.0/24', '100.64.2.0/24', '10.200.0.0/24')
    text = op(node, 'show router route-table ' + prefixes[0],
              'show router route-table ' + prefixes[1],
              'show router "100" route-table ' + prefixes[2])
    return all(re.search(r'^' + re.escape(prefix) + r'\s+Remote\s+BGP\b', text, re.M)
               for prefix in prefixes)


def sas():
    result = []
    for n in (1, 2):
        output = docker(f'enb{n}', 'swanctl', '--list-sas')
        ike = re.search(r'ESTABLISHED,\s*IKEv2,\s*(\S+)\s+(\S+)', output)
        if not ike or 'INSTALLED' not in output:
            return None
        result.append(tuple(ike.groups()))
    return result


def wait(description, predicate, timeout=300):
    log('waiting: ' + description)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            log('ready: ' + description)
            return
        time.sleep(3)
    raise LabError('TIMEOUT: ' + description)


def snapshot(label):
    log(f'{label}: domains={domains()}, paths={paths()}, IKE={sas()}')


def switch_to(target, auto=False):
    wait('nominal before planned switchover', nominal, 360)
    old = owner()
    if old == target:
        return False
    if old not in SEGS:
        raise LabError('No unique OA: ' + old)
    wait(f'forwarding routes on switchover target {target}', lambda: forwarding_ready(target), 180)
    dest = 'auto' if auto else f'to 10.0.0.{target[-1]}'
    action(old, f'tools perform redundancy multi-chassis mc-ipsec force-switchover domain 1 {dest} now')
    wait(f'unique OA {target}', lambda: owner() == target, 90)
    return True


def cli_up(node):
    if not running(node):
        return False
    try:
        return 'System Name' in op(node, 'show system information')
    except (LabError, subprocess.TimeoutExpired):
        return False


def readiness_probes():
    # Idle tunnels can defer the post-switchover CHILD rekey in SR-SIM.
    # Ordinary traffic primes it; never reset IKE or peer domains here.
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        stable = True
        for n in (1, 2):
            before = docker(f'enb{n}', 'swanctl', '--list-sas')
            text = docker(f'enb{n}', 'ping', '-n', '-c', '20', '-i', '0.1', '-W', '1',
                          '-I', f'10.100.{n}.1', '10.200.0.10', check=False)
            after = docker(f'enb{n}', 'swanctl', '--list-sas')
            (RUN / f'readiness-{time.time_ns()}-enb{n}.log').write_text(before + '\n' + text + '\n' + after)
            summary = re.search(r'^(\d+) packets transmitted, (\d+) received[^\n]*', text, re.M)
            log(f'readiness enb{n}: ' + (summary[0] if summary else text))
            stable = stable and bool(summary and summary[1] == summary[2] == '20')
        if stable:
            return
        time.sleep(2)
    raise LabError('Readiness traffic failed to stabilize; no fault was injected')


def baseline(preferred='seg1'):
    for n in (*SEGS, 'ipmpls'):
        wait(n + ' CLI', lambda n=n: cli_up(n), 480)
    for n in SEGS:
        wait(n + ' routes to both eNBs and MME', lambda n=n: forwarding_ready(n), 180)
    wait('both IKE and CHILD SAs', lambda: sas() is not None, 180)
    readiness_probes()
    wait('domain nominal; no automatic sync recovery', nominal, 420)
    if switch_to(preferred):
        readiness_probes()
    wait('2 installed tunnels on OA', lambda: domain(preferred)['installed'] == 2, 180)
    wait('nominal and consistent Current Active', nominal, 360)
    wait(f'all three core routes on {preferred}', lambda: routes_to(preferred, preferred), 150)


def ping_path(n):
    return f'/tmp/nm-validate-{RUN.name}-{CASE}-enb{n}'


def initial_probe_valid(text):
    data = metrics(text)
    received = set(data['received_sequences'])
    return data['last_reply_seq'] >= 10 and not (set(range(1, data['last_reply_seq']+1)) - received)


def start_traffic():
    global TRAFFIC, AFTER
    TRAFFIC = True
    AFTER = 0.0
    for n in (1, 2):
        path = ping_path(n)
        command = (f'echo $$ > {path}.pid; echo START $(python3 -c "import time; print(time.time())") > {path}.ping; '
                   f'exec ping -n -D -O -i 0.1 -W 1 -I 10.100.{n}.1 10.200.0.10 >> {path}.ping 2>&1')
        run(['docker', 'exec', '-d', f'{PREFIX}-enb{n}', 'sh', '-c', command])
    wait('10 consecutive replies on each eNB', traffic_stable, 40)
    for n in (1, 2):
        text = docker(f'enb{n}', 'cat', ping_path(n) + '.ping')
        if not initial_probe_valid(text):
            raise LabError(f'INVALID baseline traffic on enb{n}; failure was not injected')


def traffic_stable():
    for n in (1, 2):
        text = docker(f'enb{n}', 'cat', ping_path(n) + '.ping')
        try:
            data = metrics(text + f'\nSTOP {time.time()}\n')
            if not data['recovered'] or data['stable_since'] < AFTER:
                return False
        except ValueError:
            return False
    return True


def stop_traffic():
    global TRAFFIC
    for n in (1, 2):
        script = (f'import os, signal, time; p="{ping_path(n)}"; '
                  'os.kill(int(open(p+".pid").read()), signal.SIGINT); '
                  'open(p+".stop", "w").write(str(time.time()))')
        docker(f'enb{n}', 'python3', '-c', script)
    time.sleep(0.3)
    result = []
    for n in (1, 2):
        stop = docker(f'enb{n}', 'cat', ping_path(n) + '.stop').strip()
        text = docker(f'enb{n}', 'cat', ping_path(n) + '.ping') + f'\nSTOP {stop}\n'
        (RUN / f'{CASE}-enb{n}.ping').write_text(text)
        item = metrics(text)
        if item['tx'] is None:
            raise LabError('Missing ping summary: measurement is invalid')
        result.append(item)
    TRAFFIC = False
    return result


def begin(name, description, pub='seg1', private='seg1', require_nominal=True):
    global CASE, LOG, SPI_BEFORE
    CASE = name
    LOG = RUN / f'{CASE}.log'
    log(description)
    if require_nominal:
        wait('nominal before test', nominal, 360)
    wait(f'expected routes public={pub}, private={private}', lambda: routes_to(pub, private), 150)
    SPI_BEFORE = sas()
    if SPI_BEFORE is None:
        raise LabError('Missing IKE/CHILD before test')
    snapshot('before')
    start_traffic()
    log('ACTION WINDOW START ' + str(time.time()))


def verdict(expected, loss_class, actual, kept, data):
    if len(data) != 2 or any(d['tx'] is None or d['tx'] <= 0 for d in data):
        return 'INVALID'
    matches = actual in SEGS if expected == 'unique' else expected == actual
    if not matches or not kept:
        return 'FAIL'
    if loss_class == 'blocked':
        return 'PASS' if all(d['lost'] > 0 and not d['recovered'] for d in data) else 'FAIL'
    if not all(d['recovered'] for d in data):
        return 'FAIL'
    if loss_class == 'none' and any(d['lost'] for d in data):
        return 'FAIL'
    return 'PASS'


def finish(expected, loss_class='any', pub=None, private=None):
    data = stop_traffic()
    for item in data:
        item.pop('received_sequences')
    states = domains()
    actual = owner(states)
    table = paths()
    ike = sas()
    kept = SPI_BEFORE is not None and ike == SPI_BEFORE
    pub, private = pub or actual, private or actual
    routes_ok = table['198.51.100.1/32'] == pub and all(table[f'10.100.{n}.1/32'] == private for n in (1, 2))
    installed = states.get(actual, {}).get('installed', 0)
    status = verdict(expected, loss_class, actual, kept, data)
    if status == 'PASS' and (not routes_ok or installed != 2):
        status = 'FAIL'
    row = dict(id=CASE, expected=expected, actual=actual, ike_kept=kept, verdict=status, traffic=data,
               forwarding=dict(public=pub, private=private, paths=table, installed=installed))
    RESULTS.append(row)
    save_results()
    log(json.dumps(row))
    log(f'after: domains={states}, paths={table}, IKE={ike}')
    if status != 'PASS':
        raise LabError('Test failed: ' + CASE)


def save_results():
    (RUN / 'results.json').write_text(json.dumps(RESULTS, indent=2))
    lines = ['| Test | Expected OA | Actual OA | IKE kept | enb1 lost / gap | enb2 lost / gap | Verdict |',
             '|---|---|---|---|---|---|---|']
    for row in RESULTS:
        values = [f"{d['lost']}/{d['max_gap_s']:.3f}s" + ('' if d['recovered'] else ' (not recovered)')
                  for d in row.get('traffic', [])]
        values += ['—'] * (2-len(values))
        lines.append(f"| {row['id']} | {row.get('expected', '—')} | {row.get('actual', '—')} | "
                     f"{row.get('ike_kept', '—')} | {values[0]} | {values[1]} | {row['verdict']} |")
    (RUN / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')


def node_power(nodes, verb):
    global AFTER
    components = ('-1', '-2', '-a') if DUAL_IOM else ('-1', '-a')
    containers = [f'{PREFIX}-{n}{suffix}' for n in nodes for suffix in components]
    run(['docker', verb, *containers])
    log(verb + ' ' + ','.join(nodes))
    if TRAFFIC:
        AFTER = time.time()


def bfd(enabled):
    def setting(path):
        return path + ' true' if enabled else 'delete ' + path
    for n in SEGS:
        cfg(n, setting('/configure router "Base" bgp group "core" bfd-liveness'),
            setting('/configure service vprn "mobile" bgp group "core" bfd-liveness'))
    cfg('ipmpls', setting('/configure router "Base" bgp group "segw" bfd-liveness'),
        setting('/configure service vprn "mobile" bgp group "segw" bfd-liveness'))


def pin_route(side, target):
    context = '/configure router "Base"' if side == 'public' else '/configure service vprn "mobile"'
    prefix = '198.51.100.1/32' if side == 'public' else '10.100.0.0/16'
    kind = 'exact' if side == 'public' else 'longer'
    policy = 'test-pin-' + side
    cfg('ipmpls', f'/configure policy-options prefix-list "{policy}" prefix {prefix} type {kind}',
        f'/configure policy-options policy-statement "{policy}" entry 10 from prefix-list ["{policy}"]',
        f'/configure policy-options policy-statement "{policy}" entry 10 action action-type reject',
        f'/configure policy-options policy-statement "{policy}" default-action action-type accept')
    subnet = '31' if side == 'public' else '30'
    for n in SEGS:
        policy_name = 'accept-all' if n == target else policy
        # MD-CLI merges leaf-lists: remove the old policy chain before replacing it.
        neighbor = f'{context} bgp neighbor "172.{subnet}.{n[-1]}.1"'
        cfg('ipmpls', f'delete {neighbor} import', f'{neighbor} import policy ["{policy_name}"]')


def unpin():
    for subnet, context in [('31', '/configure router "Base"'), ('30', '/configure service vprn "mobile"')]:
        cfg('ipmpls', *(f'delete {context} bgp neighbor "172.{subnet}.{n}.1" import' for n in (1, 2, 3)))


def T0():
    begin('T0', 'Baseline and stateful IKE/CHILD availability')
    time.sleep(10)
    finish('seg1', 'none')


def T1():
    begin('T1', 'Planned auto switchover: DA preferred over DS')
    switch_to('seg2', auto=True)
    wait('traffic recovered', traffic_stable, 90)
    finish('seg2')
    begin('T1b', 'Planned return after nominal', pub='seg2', private='seg2')
    switch_to('seg1')
    wait('traffic recovered', traffic_stable, 90)
    finish('seg1')


def T2():
    begin('T2', 'ISA failure, stateful failover and ISA recovery')
    cfg('seg1', '/configure card 1 mda 2 admin-state disable')
    wait('seg2 OA', lambda: owner() == 'seg2', 90)
    wait('traffic recovered before ISA restoration', traffic_stable, 90)
    finish('seg2')
    begin('T3', 'ISA recovery remains non-revertive', pub='seg2', private='seg2', require_nominal=False)
    cfg('seg1', '/configure card 1 mda 2 admin-state enable')
    wait('all nominal after ISA restoration', nominal, 360)
    time.sleep(10)
    finish('seg2', 'none')


def T4():
    if switch_to('seg2'):
        readiness_probes()
    wait('nominal before revertive setup', nominal, 360)
    cfg('seg1', '/configure card 1 mda 2 admin-state disable',
        '/configure redundancy multi-chassis ipsec-domain 1 revertive true')
    begin('T4', 'Revertive ISA restoration; configuration toggle is outside action window',
          pub='seg2', private='seg2', require_nominal=False)
    cfg('seg1', '/configure card 1 mda 2 admin-state enable')
    wait('seg1 automatically becomes OA', lambda: owner() == 'seg1', 360)
    wait('traffic recovered', traffic_stable, 90)
    finish('seg1')
    switch_to('seg2')
    cfg('seg1', '/configure redundancy multi-chassis ipsec-domain 1 revertive false')


def T5():
    begin('T5', 'One LAG member failure; control and shunt transport survive')
    cfg('seg1', '/configure port 1/1/1 admin-state disable')
    time.sleep(15)
    finish('seg1', 'none')
    cfg('seg1', '/configure port 1/1/1 admin-state enable')


def T6():
    begin('T6', 'Both direct members lost; control connectivity via seg3')
    cfg('seg1', '/configure port 1/1/1 admin-state disable', f'/configure port {MEMBER_B} admin-state disable')
    time.sleep(20)
    if not nominal():
        raise LabError('Alternate underlay path did not preserve nominal')
    finish('seg1', 'none')
    cfg('seg1', '/configure port 1/1/1 admin-state enable', f'/configure port {MEMBER_B} admin-state enable')


def node_failure(no_bfd=False):
    if no_bfd:
        bfd(False)
    begin('T7-noBFD' if no_bfd else 'T7', 'Continuous traffic across OA failure and node return')
    node_power(('seg1',), 'kill')
    wait('seg2 OA', lambda: owner() == 'seg2', 90)
    wait('traffic restored BEFORE restarting failed node', traffic_stable, 180)
    snapshot('failover recovered')
    before = [metrics(docker(f'enb{n}', 'cat', ping_path(n) + '.ping')) for n in (1, 2)]
    log('NODE RETURN WINDOW START ' + str(time.time()))
    node_power(('seg1',), 'start')
    wait('seg1 CLI', lambda: cli_up('seg1'), 480)
    wait('nominal after node return', nominal, 420)
    wait('stable after return', traffic_stable, 90)
    for n in (1, 2):
        after = metrics(docker(f'enb{n}', 'cat', ping_path(n) + '.ping'))
        first = before[n-1]['last_reply_seq']
        missing = set(range(first+1, after['last_reply_seq']+1)) - set(after['received_sequences'])
        if missing:
            raise LabError(f'Node return lost {len(missing)} packets on enb{n}')
    finish('seg2')
    if no_bfd:
        bfd(True)


def prepare_pool(ha, force=False):
    mode = 'tunnel-limit-32k' if ha else 'none'
    text = op('seg3', 'show isa tunnel-member-pool pool1 detail')
    current = re.search(r'High Availability\s*:\s*(.+)', text)
    if not force and current and current[1].strip() == (mode if ha else '(Not Specified)'):
        return
    if owner() not in ('seg1', 'seg2'):
        raise LabError('Pool maintenance requires seg3 to be standby')
    if ha:
        log('OFFLINE HA preparation outside measurement: stop DA components; preserve core, eNBs and netns helpers')
        node_power(('seg1', 'seg2'), 'stop')
    def isa_ready():
        return bool(re.search(r'^\s+2\s+isa2-tunnel\s+up\s+up\b', op('seg3', 'show mda'), re.M))
    try:
        if ha:
            available = int(re.search(r'^MemAvailable:\s+(\d+)', Path('/proc/meminfo').read_text(), re.M)[1]) * 1024
            log(f'Available physical RAM after stopping DAs: {available / 1024**3:.3f} GiB')
            if available < 10 * 1024**3:
                raise LabError('Insufficient RAM for HA preparation (need 10 GiB MemAvailable; swap does not qualify)')
        log('Pool maintenance: disable ISA, change mode, save and cold-restart')
        cfg('seg3', '/configure card 1 mda 2 admin-state disable')
        cfg('seg3', '/configure isa tunnel-member-pool "pool1" high-availability ' + mode)
        action('seg3', '/admin save')
        if ha:
            # Initialize HA using a cold CPM/IOM start.
            node_power(('seg3',), 'stop')
            run(['docker', 'update', '--memory', '8g', '--memory-swap', '9g', f'{PREFIX}-seg3-1'])
            node_power(('seg3',), 'start')
            wait('seg3 cold CPM CLI', lambda: cli_up('seg3'), 300)
        else:
            run(['docker', 'restart', f'{PREFIX}-seg3-1'])
        cfg('seg3', '/configure card 1 mda 2 admin-state enable')
        wait('seg3 ISA equipped and operational', isa_ready, 240)
        action('seg3', '/admin save')
        if ha:
            log('Observe cold HA ISA for 60 seconds before starting DAs')
            for _ in range(12):
                time.sleep(5)
                if not isa_ready():
                    raise LabError('HA ISA lost operational state during preparation')
    finally:
        if ha:
            for node in ('seg1', 'seg2'):
                node_power((node,), 'start')
                wait(node + ' CLI after preparation', lambda node=node: cli_up(node), 300)
                wait(node + ' forwarding routes after preparation', lambda node=node: forwarding_ready(node), 180)
                time.sleep(10)
    readiness_probes()
    wait('nominal after cold pool preparation', nominal, 360)
    text = op('seg3', 'show isa tunnel-member-pool pool1 detail', 'show mda')
    text += '\nHost memory after pool preparation:\n' + Path('/proc/meminfo').read_text()
    (RUN / f'pool-preparation-{time.time_ns()}.log').write_text(text)


def T8(ha=False):
    prepare_pool(ha)
    begin('T9' if ha else 'T8', 'Double failure to DS; HA=' + str(ha))
    log(op('seg3', '/admin show configuration /configure isa'))
    node_power(('seg1', 'seg2'), 'kill')
    wait('seg3 unique OA', lambda: owner() == 'seg3', 120)
    wait('traffic recovered on DS', traffic_stable, 180)
    finish('seg3')
    begin('T9r' if ha else 'T8r', 'Both DAs return: observe election, verify stateful recovery',
          pub='seg3', private='seg3', require_nominal=False)
    node_power(('seg1', 'seg2'), 'start')
    for n in ('seg1', 'seg2'):
        wait(n + ' CLI', lambda n=n: cli_up(n), 480)
    wait('nominal after both DAs return', nominal, 420)
    wait('traffic recovered after both DAs return', traffic_stable, 90)
    # An isolated eligible DS rejoins an election; record its actual outcome.
    # If the OA remains DS, demand no loss; an OA change may have a measured gap.
    finish('unique', 'none' if owner() == 'seg3' else 'any')
    for n in SEGS:
        log(op(n, 'show log log-id 99 application mc_redundancy count 20 descending'))
    if ha:
        baseline()
        prepare_pool(False)


def peer_in_sync(source, target):
    text = op(source, 'show redundancy multi-chassis sync')
    for block in re.split(r'Peer IP Address\s*:\s*', text)[1:]:
        if block.split()[0] == f'10.0.0.{target[-1]}':
            return bool(re.search(r'Sync Oper State\s*:\s*Up\b', block) and
                        re.search(r'DB Sync State\s*:\s*inSync\b', block))
    return False


def observe_stable(seconds=30):
    before = [metrics(docker(f'enb{n}', 'cat', ping_path(n) + '.ping')) for n in (1, 2)]
    log(f'Observe {seconds} seconds of forwarding without additional loss')
    time.sleep(seconds)
    if not traffic_stable():
        raise LabError('Traffic did not remain recovered during the observation')
    for n in (1, 2):
        after = metrics(docker(f'enb{n}', 'cat', ping_path(n) + '.ping'))
        missing = set(range(before[n-1]['last_reply_seq']+1, after['last_reply_seq']+1)) - set(after['received_sequences'])
        if missing:
            raise LabError(f'Observation lost {len(missing)} packets on enb{n}')


def sequential_failure(ha=False):
    prepare_pool(ha)
    number = 'T14' if ha else 'T13'

    def evidence(label, nodes):
        for node in nodes:
            text = op(node, 'show redundancy multi-chassis ipsec-domain 1',
                      'show redundancy multi-chassis sync', 'show isa tunnel-group',
                      'show router bfd session', 'show router "100" bfd session')
            (RUN / f'{CASE}-{label}-{node}.log').write_text(text)
        text = op('ipmpls', 'show router route-table 198.51.100.1/32',
                  'show router "100" route-table 10.100.1.1/32',
                  'show router "100" route-table 10.100.2.1/32',
                  'show router bfd session', 'show router "100" bfd session')
        (RUN / f'{CASE}-{label}-core.log').write_text(text)

    begin(number+'a', 'Sequential failure: seg1 off; verify sustained forwarding through seg2; HA=' + str(ha))
    original_ike = SPI_BEFORE
    evidence('before', SEGS)
    node_power(('seg1',), 'kill')
    wait('seg2 unique OA with two installed tunnels',
         lambda: owner() == 'seg2' and domain('seg2')['installed'] == 2, 120)
    wait('all three core routes through seg2', lambda: routes_to('seg2', 'seg2'), 150)
    wait('traffic restored on seg2 while seg1 stays off', traffic_stable, 180)
    wait('surviving seg2/seg3 MCS inSync in both directions',
         lambda: peer_in_sync('seg2', 'seg3') and peer_in_sync('seg3', 'seg2'), 120)
    observe_stable()
    evidence('recovered', ('seg2', 'seg3'))
    finish('seg2')

    begin(number+'b', 'Second sequential failure: seg2 off while seg1 remains off',
          pub='seg2', private='seg2', require_nominal=False)
    if SPI_BEFORE != original_ike or running('seg1'):
        raise LabError('Sequential boundary requires original IKE and seg1 still off')
    node_power(('seg2',), 'kill')
    wait('seg3 unique OA with two installed tunnels',
         lambda: owner() == 'seg3' and domain('seg3')['installed'] == 2, 120)
    wait('all three core routes through seg3', lambda: routes_to('seg3', 'seg3'), 150)
    wait('traffic restored on seg3 while both DAs stay off', traffic_stable, 180)
    observe_stable()
    evidence('recovered', ('seg3',))
    finish('seg3')

    begin(number+'r', 'Both DAs return after sequential failure; preserve original IKE',
          pub='seg3', private='seg3', require_nominal=False)
    if SPI_BEFORE != original_ike:
        raise LabError('Original IKE changed before DA return')
    node_power(('seg1', 'seg2'), 'start')
    for node in ('seg1', 'seg2'):
        wait(node + ' CLI after sequential failure', lambda node=node: cli_up(node), 480)
    wait('nominal after sequential failure and DA return', nominal, 420)
    wait('traffic recovered after sequential DA return', traffic_stable, 180)
    evidence('returned', SEGS)
    finish('unique', 'none' if owner() == 'seg3' else 'any')
    if ha:
        baseline()
        prepare_pool(False)


def shunting(side):
    number = 'T10' if side == 'public' else 'T11'
    context = '/configure service ies "public" interface "pub"' if side == 'public' else '/configure service vprn "mobile" interface "priv"'
    profile = 'shunt-pub' if side == 'public' else 'shunt-priv'
    for target in ('seg2', 'seg3'):
        pin_route(side, target)
        pub, private = (target, 'seg1') if side == 'public' else ('seg1', target)
        begin(number + '-' + target, f'{side} shunting through {target}', pub, private)
        time.sleep(10)
        finish('seg1', 'none', pub=pub, private=private)
        begin(number + 'b-' + target, f'Negative control: {side} shunting removed on {target}', pub, private)
        cfg(target, f'delete {context} multi-chassis-shunting-profile')
        time.sleep(10)
        finish('seg1', 'blocked', pub=pub, private=private)
        cfg(target, f'{context} multi-chassis-shunting-profile "{profile}"')
        wait('both CHILD SAs after shunt restoration', lambda: sas() is not None, 120)
    unpin()


def T12():
    begin('T12', 'LAG member failure followed by switchover and pinned shunt routes')
    cfg('seg1', '/configure port 1/1/1 admin-state disable')
    switch_to('seg2')
    wait('traffic recovered with member A disabled', traffic_stable, 90)
    pin_route('public', 'seg1')
    pin_route('private', 'seg1')
    wait('routes pinned to former OA', lambda: routes_to('seg1', 'seg1'), 120)
    time.sleep(10)
    wait('shunting through surviving member B', traffic_stable, 30)
    finish('seg2', pub='seg1', private='seg1')
    unpin()
    cfg('seg1', '/configure port 1/1/1 admin-state enable')


def diagnostics():
    for n in SEGS:
        if running(n):
            try:
                text = op(n, 'show redundancy multi-chassis ipsec-domain 1',
                    'show redundancy multi-chassis sync', 'show isa tunnel-group',
                    'show ipsec gateway name "enb-gw" tunnel',
                    'show log log-id 99 count 100 descending', 'show lag')
                (RUN / f'diagnostics-{n}.log').write_text(text)
            except Exception as error:
                log('Diagnostics: ' + str(error))


def cleanup():
    log('restoring lab controls')
    for n in SEGS:
        if not running(n):
            node_power((n,), 'start')
        wait(n + ' CLI for cleanup', lambda n=n: cli_up(n), 480)
    unpin()
    bfd(True)
    for n in SEGS:
        cfg(n, '/configure card 1 mda 2 admin-state enable',
            '/configure port 1/1/1 admin-state enable', f'/configure port {MEMBER_B} admin-state enable',
            '/configure service ies "public" interface "pub" multi-chassis-shunting-profile "shunt-pub"',
            '/configure service vprn "mobile" interface "priv" multi-chassis-shunting-profile "shunt-priv"')
    # The documented revertive admin toggle must occur on a standby.
    if owner() == 'seg1':
        text = op('seg1', '/admin show configuration /configure redundancy multi-chassis ipsec-domain 1')
        if 'revertive true' in text:
            switch_to('seg2')
    cfg('seg1', '/configure redundancy multi-chassis ipsec-domain 1 revertive false')
    # A failed HA preparation can leave the DS ineligible: restore its normal
    # pool before demanding nominal from the whole domain.
    if owner() == 'seg3':
        baseline('seg1')
    prepare_pool(False)
    baseline()
    snapshot('restored baseline')
    for node in (*SEGS, 'ipmpls'):
        action(node, '/admin save')


def main():
    global LOG, CASE
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f'signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    cases = dict(T0=T0, T1=T1, T2=T2, T4=T4, T5=T5, T6=T6,
                 T7=node_failure, **{'T7-noBFD': lambda: node_failure(True)},
                 T8=T8, T9=lambda: T8(True), T10=lambda: shunting('public'),
                 T11=lambda: shunting('private'), T12=T12,
                 T13=sequential_failure, T14=lambda: sequential_failure(True))
    selected = list(cases) if sys.argv[1:] == ['all'] else sys.argv[1:]
    if not selected or any(t not in cases for t in selected):
        raise SystemExit('Usage: tests/nm_tests.sh all | ' + ' '.join(cases))
    lock = ROOT / 'work' / 'nm-tests.lock'
    lock.parent.mkdir(exist_ok=True)
    with lock.open('w') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Another test runner holds the lab lock')
        RUN.mkdir(parents=True)
        LOG = RUN / 'run.log'
        (RUN / 'metadata.json').write_text(json.dumps(dict(topology=str(TOPOLOGY), lab=NAME,
            started=time.time(), tests=selected, runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2))
        (RUN / 'configuration-sha256.json').write_text(json.dumps({
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [TOPOLOGY, *sorted((ROOT / 'configs').rglob('*'))] if path.is_file()
        }, indent=2))
        failed = False
        try:
            for name in selected:
                LOG = RUN / 'run.log'
                CASE = name
                baseline('seg2' if name == 'T4' else 'seg1')
                cases[name]()
        except (Exception, KeyboardInterrupt) as error:
            failed = True
            log('STOP: ' + str(error))
            if TRAFFIC:
                try:
                    data = stop_traffic()
                except Exception as measurement_error:
                    log('Measurement: ' + str(measurement_error))
                    data = []
                if not RESULTS or RESULTS[-1]['id'] != CASE:
                    RESULTS.append(dict(id=CASE or 'preconditions', verdict='INVALID', reason=str(error), traffic=data))
            elif not RESULTS or RESULTS[-1]['verdict'] == 'PASS':
                RESULTS.append(dict(id=(CASE or 'preconditions') + '-readiness', verdict='INVALID', reason=str(error)))
            save_results()
            diagnostics()
        finally:
            LOG = RUN / 'run.log'
            try:
                cleanup()
            except Exception as error:
                failed = True
                log('CLEANUP INCOMPLETE: ' + str(error))
                diagnostics()
        log('Results: ' + str(RUN))
        return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
