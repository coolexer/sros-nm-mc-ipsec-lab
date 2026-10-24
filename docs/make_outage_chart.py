"""Render docs/outage-chart.svg from the measured worst gap per scenario (max of enb1/enb2)."""
from pathlib import Path

# (label, worst gap in seconds, lost packets enb1/enb2, category)
DATA = [
    ("T1  force-switchover seg1 -> seg2", 0.449, "3/4", "switch"),
    ("T1b force-switchover seg2 -> seg1", 0.440, "3/3", "switch"),
    ("T2  ISA failure on OA", 0.442, "3/3", "switch"),
    ("T3  ISA restored, non-revertive", 0.0, "0/0", "none"),
    ("T4  revertive take-over", 0.438, "3/3", "switch"),
    ("T5  1 of 2 SecGW links down", 0.0, "0/0", "none"),
    ("T6  both seg1-seg2 links down", 0.0, "0/0", "none"),
    ("T7  OA node failure, no BFD to core", 26.98, "236/238", "bad"),
    ("T7  OA node failure, BFD to core", 2.891, "24/25", "node"),
    ("T7r failed node returns", 0.0, "0/0", "none"),
    ("T8  double failure -> DS (pool)", 3.213, "41/35", "node"),
    ("T9  double failure -> DS (pool HA)", 2.760, "23/23", "node"),
    ("T10 public shunting (enb1)", 0.0, "0/-", "none"),
    ("T10b public, shunting removed", 21.40, "185/189", "control"),
    ("T11 private shunting", 0.0, "0/0", "none"),
    ("T11b private, shunting removed", 21.35, "184/188", "control"),
]
COLORS = {"switch": "#2563EB", "node": "#00A36C", "bad": "#DC2626", "control": "#94A3B8", "none": "#22C55E"}

W, LEFT, TOP, ROW, SCALE_MAX, BAR_W = 1100, 330, 90, 30, 28.0, 600


def x(v):
    return LEFT + BAR_W * v / SCALE_MAX


def main():
    h = TOP + ROW * len(DATA) + 90
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" '
           'font-family="Segoe UI, Helvetica, Arial, sans-serif">',
           f'<rect width="{W}" height="{h}" fill="#FFFFFF"/>',
           '<text x="30" y="38" font-size="21" font-weight="700" fill="#001135">'
           'Worst traffic gap per scenario (10 pps per eNB, max of enb1/enb2)</text>',
           '<text x="30" y="62" font-size="12.5" fill="#475569">SR-SIM 26.7.R2 - compare scenarios with each other; '
           'absolute values are not hardware figures</text>']
    for s in range(0, 29, 4):
        out.append(f'<line x1="{x(s):.1f}" y1="{TOP - 8}" x2="{x(s):.1f}" y2="{TOP + ROW * len(DATA)}" '
                   'stroke="#E2E8F0"/>')
        out.append(f'<text x="{x(s):.1f}" y="{TOP + ROW * len(DATA) + 18}" font-size="11" fill="#64748B" '
                   f'text-anchor="middle">{s} s</text>')
    for i, (label, v, lost, cat) in enumerate(DATA):
        y = TOP + i * ROW
        out.append(f'<text x="{LEFT - 12}" y="{y + 19}" font-size="12.5" fill="#1F2937" text-anchor="end">{label}</text>')
        if cat == "none":
            out.append(f'<circle cx="{LEFT + 8}" cy="{y + 14}" r="6" fill="{COLORS[cat]}"/>')
            out.append(f'<text x="{LEFT + 22}" y="{y + 19}" font-size="12" fill="#15803D">no loss</text>')
            continue
        wbar = max(x(v) - LEFT, 3)
        out.append(f'<rect x="{LEFT}" y="{y + 5}" width="{wbar:.1f}" height="19" rx="3" fill="{COLORS[cat]}"/>')
        out.append(f'<text x="{LEFT + wbar + 8:.1f}" y="{y + 19}" font-size="12" font-weight="600" fill="#1F2937">'
                   f'{v:.2f} s  ({lost} pkts)</text>')
    ly = TOP + ROW * len(DATA) + 50
    legend = [("switch", "planned / ISA switchover (DA to DA)"), ("node", "node failure"),
              ("bad", "node failure without BFD to core"), ("control", "control test: shunting disabled")]
    lx = 30
    for cat, text in legend:
        out.append(f'<rect x="{lx}" y="{ly - 11}" width="16" height="14" rx="3" fill="{COLORS[cat]}"/>')
        out.append(f'<text x="{lx + 24}" y="{ly}" font-size="12" fill="#1F2937">{text}</text>')
        lx += 24 + 8 * len(text) + 40
    out.append("</svg>")
    Path(__file__).with_name("outage-chart.svg").write_text("\n".join(out), encoding="ascii", newline="\n")


if __name__ == "__main__":
    main()
