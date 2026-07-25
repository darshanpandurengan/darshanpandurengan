#!/usr/bin/env python3
"""
make_ascii_svg.py

Converts a prepped grayscale photo (see prep_photo.py) into a
self-typing, monochrome ASCII-art SVG. Each row wipes in left-to-right
behind a small block "cursor", staggered top to bottom. The whole
portrait prints once and freezes -- no looping.

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png] [ascii-portrait.svg]
"""

import sys

from PIL import Image

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space clears the background
COLS = 100
ROWS = 53
CELL_W = 7.2
CELL_H = 13
FONT_SIZE = 13
FILL_COLOR = "#c9d1d9"  # one light-gray fill, on purpose -- monochrome reads as art, not noise
ROW_DURATION = 0.55      # seconds each row takes to wipe fully in
ROW_STAGGER = 0.045      # seconds between each row's start (top -> bottom cascade)


def image_to_grid(path: str, cols: int, rows: int):
    img = Image.open(path).convert("L")
    img = img.resize((cols, rows))
    pixels = list(img.getdata())

    ramp_len = len(RAMP) - 1
    grid = []
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            brightness = pixels[r * cols + c]  # 0 (black) - 255 (white)
            idx = int((255 - brightness) / 255 * ramp_len)
            row_chars.append(RAMP[idx])
        grid.append("".join(row_chars))
    return grid


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def build_svg(grid, cols: int, rows: int) -> str:
    row_width = cols * CELL_W
    width = row_width
    height = rows * CELL_H + 12

    defs = []
    body = []

    for r, row_text in enumerate(grid):
        clip_id = f"clip-row-{r}"
        start = r * ROW_STAGGER
        row_y = r * CELL_H

        # A clip rect grows from width 0 -> full, which "types in" the
        # row of text sitting beneath it.
        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{row_y}" width="0" height="{CELL_H + 2}">'
            f'<animate attributeName="width" from="0" to="{row_width:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" calcMode="linear"/>'
            f'</rect></clipPath>'
        )

        safe_text = escape_xml(row_text)
        body.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="0" y="{row_y + CELL_H - 3:.1f}" '
            f'font-family="\'JetBrains Mono\',\'Courier New\',monospace" '
            f'font-size="{FONT_SIZE}" fill="{FILL_COLOR}" xml:space="preserve">{safe_text}</text>'
            # the "cursor" block rides the wipe edge, then fades once its row is done
            f'<rect x="0" y="{row_y}" width="{CELL_W}" height="{CELL_H}" fill="{FILL_COLOR}">'
            f'<animate attributeName="x" from="0" to="{row_width:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" calcMode="linear"/>'
            f'<animate attributeName="opacity" from="1" to="0" '
            f'begin="{start + ROW_DURATION:.3f}s" dur="0.15s" fill="freeze"/>'
            f'</rect></g>'
        )

    svg = (
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg" font-kerning="none">'
        f'<defs>{"".join(defs)}</defs>'
        f'<rect width="100%" height="100%" fill="#0d1117"/>'
        f'{"".join(body)}'
        f'</svg>'
    )
    return svg


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "ascii-portrait.svg"

    grid = image_to_grid(input_path, COLS, ROWS)
    svg = build_svg(grid, COLS, ROWS)

    with open(output_path, "w") as f:
        f.write(svg)
    print(f"Wrote {output_path} ({COLS}x{ROWS} chars)")


if __name__ == "__main__":
    main()
