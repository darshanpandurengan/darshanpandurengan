#!/usr/bin/env python3
"""
render_heatmap_svg.py

Renders data/contributions.json as the classic 53-week x 7-day
calendar of rounded, colored boxes. The grid reveals itself once with
a diagonal, line-after-line slide-down (plain CSS keyframes, single
play-through, then freeze -- no looping "glow").

Usage:
    python scripts/render_heatmap_svg.py
"""

import json
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

DATA_PATH = Path("data/contributions.json")
OUTPUT_PATH = Path("contrib-heatmap.svg")

# none -> brightest; level 5 is a neon top end reserved for standout days
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT_MARGIN = 32
TOP_MARGIN = 24
BOTTOM_MARGIN = 56
RIGHT_MARGIN = 12

COL_STAGGER = 0.018   # seconds added per week-column (left -> right)
ROW_STAGGER = 0.035   # seconds added per day-row (top -> bottom), creates the diagonal
CELL_DURATION = 0.28

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Monday=0 ... Sunday=6 (python weekday())


def load_days():
    if not DATA_PATH.exists():
        print(f"{DATA_PATH} not found -- run fetch_contributions.py first.", file=sys.stderr)
        sys.exit(1)
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return payload


def bump_outliers(days):
    """Promote the year's standout days to a level-5 'neon' top end."""
    counts = sorted((d["count"] for d in days if d["count"] > 0), reverse=True)
    if not counts:
        return
    threshold = counts[2] if len(counts) >= 3 else counts[0]
    for d in days:
        if d["count"] > 0 and d["count"] >= threshold and d["level"] >= 4:
            d["level"] = 5


def build_grid(days):
    """Arrange days into 53 week-columns x 7 day-rows, GitHub-style
    (columns run Sun-Sat top to bottom, weeks left to right)."""
    by_date = {d["date"]: d for d in days}
    ordered_dates = sorted(by_date)
    if not ordered_dates:
        return [], []

    first = datetime.strptime(ordered_dates[0], "%Y-%m-%d").date()
    # Back up to the preceding Sunday so week columns align like GitHub's.
    first_sunday = first
    while first_sunday.weekday() != 6:  # Monday=0 ... Sunday=6
        first_sunday = date.fromordinal(first_sunday.toordinal() - 1)

    last = datetime.strptime(ordered_dates[-1], "%Y-%m-%d").date()

    weeks = []
    month_labels = []  # (col_index, "Mon")
    cursor = first_sunday
    col = 0
    last_month = None
    while cursor <= last:
        week = []
        for row in range(7):
            d_str = cursor.isoformat()
            cell = by_date.get(d_str)
            week.append(cell if cell else {"date": d_str, "level": -1, "count": 0})
            if row == 0 and (last_month != cursor.month):
                month_labels.append((col, MONTH_ABBR[cursor.month - 1]))
                last_month = cursor.month
            cursor = date.fromordinal(cursor.toordinal() + 1)
        weeks.append(week)
        col += 1

    return weeks, month_labels


def main():
    payload = load_days()
    days = payload["days"]
    bump_outliers(days)
    weeks, month_labels = build_grid(days)

    n_cols = len(weeks)
    width = LEFT_MARGIN + n_cols * STEP + RIGHT_MARGIN
    height = TOP_MARGIN + 7 * STEP + BOTTOM_MARGIN

    cells_svg = []
    for col, week in enumerate(weeks):
        for row, cell in enumerate(week):
            level = cell["level"]
            if level < 0:
                continue  # padding day outside the real data range
            x = LEFT_MARGIN + col * STEP
            y = TOP_MARGIN + row * STEP
            color = PALETTE[max(level, 0)]
            delay = col * COL_STAGGER + row * ROW_STAGGER
            title = f"{cell['count']} contributions on {cell['date']}" if cell["count"] else f"No contributions on {cell['date']}"
            cells_svg.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" fill="{color}" style="--d:{delay:.3f}s">'
                f'<title>{title}</title></rect>'
            )

    month_svg = []
    for col, label in month_labels:
        x = LEFT_MARGIN + col * STEP
        month_svg.append(
            f'<text x="{x}" y="{TOP_MARGIN - 8}" font-size="10" fill="#8b949e" '
            f'font-family="\'JetBrains Mono\',monospace">{label}</text>'
        )

    dow_svg = []
    for row, label in DOW_LABELS.items():
        y = TOP_MARGIN + row * STEP + CELL
        dow_svg.append(
            f'<text x="0" y="{y}" font-size="10" fill="#8b949e" '
            f'font-family="\'JetBrains Mono\',monospace">{label}</text>'
        )

    # Position the legend cleanly on the bottom right
    legend_x = width - RIGHT_MARGIN - (len(PALETTE) * (CELL + 3) + 70)
    legend_y = height - 20

    legend_svg = [
        f'<text x="{legend_x}" y="{legend_y + 8}" font-size="10" fill="#8b949e" font-family="\'JetBrains Mono\',monospace">Less</text>'
    ]
    swatch_x = legend_x + 32
    for i, color in enumerate(PALETTE):
        legend_svg.append(
            f'<rect x="{swatch_x + i * (CELL + 3)}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>'
        )
    legend_svg.append(
        f'<text x="{swatch_x + len(PALETTE) * (CELL + 3) + 6}" y="{legend_y + 8}" font-size="10" fill="#8b949e" font-family="\'JetBrains Mono\',monospace">More</text>'
    )

    total = payload.get("total_contributions", sum(d["count"] for d in days))
    stats = payload.get("stats", {})
    footer_bits = [f"{total:,} contributions in the last year"]
    if stats.get("longest_streak"):
        footer_bits.append(f"longest streak {stats['longest_streak']}d")
    if stats.get("current_streak"):
        footer_bits.append(f"current streak {stats['current_streak']}d")
    footer_text = "  ·  ".join(footer_bits)

    svg = f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" font-kerning="none">
  <style>
    .cell {{
      opacity: 0;
      transform: translateY(-8px);
      transform-box: fill-box;
      transform-origin: center;
      animation: reveal {CELL_DURATION}s ease-out forwards;
      animation-delay: var(--d);
    }}
    @keyframes reveal {{
      to {{ opacity: 1; transform: translateY(0); }}
    }}
  </style>
  <rect width="100%" height="100%" fill="#0d1117"/>
  {"".join(month_svg)}
  {"".join(dow_svg)}
  {"".join(cells_svg)}
  {"".join(legend_svg)}
  <text x="{LEFT_MARGIN}" y="{height - 12}" font-size="11" fill="#c9d1d9" font-family="'JetBrains Mono',monospace">{footer_text}</text>
</svg>'''

    OUTPUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({n_cols} weeks x 7 days, {total} total)")


if __name__ == "__main__":
    main()