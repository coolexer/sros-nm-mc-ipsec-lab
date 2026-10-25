#!/usr/bin/env python3
"""Parse iputils ping, including missing head/tail and unfinished outages."""
import json
import re
import sys


def metrics(text):
    events, replies = [], []
    start = stop = None
    summary = re.search(r'(\d+) packets transmitted, (\d+) received', text)
    for line in text.splitlines():
        if line.startswith('START '):
            start = float(line.split()[1])
        elif line.startswith('STOP '):
            stop = float(line.split()[1])
        match = re.match(r'\[([\d.]+)\]', line)
        if match:
            stamp = float(match[1])
            events.append(stamp)
            if 'bytes from' in line:
                replies.append((stamp, int(re.search(r'icmp_seq=(\d+)', line)[1])))
    if not events:
        raise ValueError('No timestamped ping observations')
    start = start if start is not None else events[0]
    stop = stop if stop is not None else events[-1]
    # A reply racing SIGINT can be timestamped just after the stop signal.
    stop = max(stop, events[-1])
    stamps = [start, *(r[0] for r in replies), stop]
    gap = max((b-a for a, b in zip(stamps, stamps[1:])), default=stop-start)
    seqs = {r[1] for r in replies}
    last_seq = max(seqs, default=0)
    stable = last_seq >= 10 and all(i in seqs for i in range(last_seq-9, last_seq+1))
    stable = stable and stop-replies[-1][0] <= 0.5
    tx, rx = map(int, summary.groups()) if summary else (None, None)
    if summary and (tx <= 0 or not 0 <= rx <= tx):
        raise ValueError('Invalid ping packet counts')
    return dict(tx=tx, rx=rx, lost=tx-rx if summary else None,
                max_gap_s=round(gap, 6), recovered=bool(stable),
                first_reply_seq=replies[0][1] if replies else None,
                last_reply_seq=last_seq, received_sequences=sorted(seqs),
                stable_since=next((stamp for stamp, seq in replies if seq == last_seq-9), None),
                head_s=round((replies[0][0] if replies else stop)-start, 6),
                tail_s=round(stop-(replies[-1][0] if replies else start), 6),
                explicit_window='START ' in text and 'STOP ' in text)


if __name__ == '__main__':
    print(json.dumps(metrics(open(sys.argv[1], encoding='utf-8').read()), indent=2))
