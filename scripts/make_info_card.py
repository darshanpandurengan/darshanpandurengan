#!/usr/bin/env python3
"""
make_info_card.py

Hand-authored neofetch-style info card. Each row fades + slides in on
a short stagger so the panel looks like it's printing next to the
ASCII portrait, then freezes (plays once, no looping).

Set STATIC=1 to emit a frozen (non-animated) frame -- handy for local
Quick Look / file-preview checks.

Usage:
    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py
"""

import os

# ---- EDIT ME: swap in your own info -----------------------------------
USER = "darshanpandurengan"
HOST = "github"
ROWS = [
    ("Now", "2nd-year B.Tech CSE student at Amrita Vishwa Vidyapeetham (CGPA 9.19)"),
    ("Prev", "Open to internships -- strong in DSA, OOP, and DBMS fundamentals"),
    ("Stack", "Java / Python / JavaScript / SQL / MySQL / Git"),
    ("Highlights", "Oracle Java Foundations cert -- Generative AI Mastermind (Outskill)"),
]
# -------------------------------------------------------------------------

WIDTH = 490
LINE_HEIGHT = 32
TOP_PADDING = 66
BOTTOM_PADDING = 22
FONT = "'JetBrains Mono','Courier New',monospace"
LABEL_COLOR = "#39d353"
VALUE_COLOR = "#c9d1d9"
MUTED_COLOR = "#8b949e"
BG_COLOR = "#0d1117"
TITLEBAR_COLOR = "#161b22"
BORDER_COLOR = "#30363d"
STAGGER = 0.16
DURATION = 0.35
LABEL_X = 24
VALUE_X = 150
VALUE_WRAP_WIDTH = WIDTH - VALUE_X - 20


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def wrap_text(text: str, max_chars: int):
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def build_svg(static: bool) -> str:
    # Monospace advance width at font-size 13 is ~7.83px/char; round up
    # a little further so wrapped lines never brush the card's edge.
    max_chars = max(10, int(VALUE_WRAP_WIDTH / 8.1))

    entries = []
    y = TOP_PADDING
    for i, (label, value) in enumerate(ROWS):
        wrapped = wrap_text(escape_xml(value), max_chars)
        entries.append((escape_xml(label), wrapped, y, i))
        y += LINE_HEIGHT * max(1, len(wrapped))

    height = y + BOTTOM_PADDING

    rows_svg = []
    for label, wrapped_lines, y0, i in entries:
        start = i * STAGGER

        if static:
            group_attrs = 'opacity="1"'
            animate_block = ""
        else:
            group_attrs = 'opacity="0"'
            animate_block = f'''
      <animate attributeName="opacity" from="0" to="1" begin="{start:.2f}s" dur="{DURATION}s" fill="freeze"/>
      <animateTransform attributeName="transform" type="translate"
                         from="-10,0" to="0,0" begin="{start:.2f}s" dur="{DURATION}s"
                         fill="freeze" calcMode="linear"/>'''

        text_lines = []
        for j, line in enumerate(wrapped_lines):
            ly = y0 + j * LINE_HEIGHT
            label_span = (
                f'<text x="{LABEL_X}" y="{ly}" font-family="{FONT}" font-size="14" '
                f'font-weight="bold" fill="{LABEL_COLOR}">{label}</text>'
                if j == 0
                else ""
            )
            text_lines.append(
                f'{label_span}'
                f'<text x="{VALUE_X}" y="{ly}" font-family="{FONT}" font-size="13" fill="{VALUE_COLOR}">{line}</text>'
            )

        rows_svg.append(
            f'<g {group_attrs} transform="translate(-10,0)">{animate_block}{"".join(text_lines)}</g>'
            if not static
            else f'<g {group_attrs}>{"".join(text_lines)}</g>'
        )

    svg = f'''<svg viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg" font-kerning="none">
  <rect width="100%" height="100%" rx="8" fill="{BG_COLOR}" stroke="{BORDER_COLOR}"/>
  <rect width="100%" height="34" rx="8" fill="{TITLEBAR_COLOR}"/>
  <rect y="26" width="100%" height="8" fill="{TITLEBAR_COLOR}"/>
  <circle cx="20" cy="17" r="6" fill="#ff5f56"/>
  <circle cx="40" cy="17" r="6" fill="#ffbd2e"/>
  <circle cx="60" cy="17" r="6" fill="#27c93f"/>
  <text x="{WIDTH / 2}" y="22" font-family="{FONT}" font-size="13" fill="{MUTED_COLOR}" text-anchor="middle">{USER}@{HOST}: neofetch</text>
  {"".join(rows_svg)}
</svg>'''
    return svg


def main():
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(static)
    output_path = "info-card.svg"
    with open(output_path, "w") as f:
        f.write(svg)
    print(f"Wrote {output_path}{' (static)' if static else ''}")


if __name__ == "__main__":
    main()
