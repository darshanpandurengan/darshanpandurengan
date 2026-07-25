#!/usr/bin/env python3
"""
prep_photo.py

Turns a normal photo into a clean, background-free, high-contrast
grayscale image that's ready for ASCII conversion. A flatly-lit face
converts to a dark, unreadable blob without this step.

Pipeline:
    1. Remove the background (rembg) so only the subject remains.
    2. Composite onto pure white, so the background maps to the blank
       end of the ASCII density ramp (white -> space).
    3. Boost local contrast with OpenCV's CLAHE, which is what gives a
       flat face real highlights and shadows.

Run this once per photo -- it's not part of the daily automation.

Usage:
    python scripts/prep_photo.py source-photo.jpg [output.png]
"""

import io
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep_photo(input_path: str, output_path: str = "source-prepped.png") -> None:
    input_bytes = open(input_path, "rb").read()

    print("Removing background...")
    no_bg_bytes = remove(input_bytes)
    subject = Image.open(io.BytesIO(no_bg_bytes)).convert("RGBA")

    print("Compositing onto white...")
    white_bg = Image.new("RGBA", subject.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, subject).convert("RGB")

    print("Boosting local contrast (CLAHE)...")
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    boosted = clahe.apply(gray)

    Image.fromarray(boosted).save(output_path)
    print(f"Saved {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <path-to-photo> [output.png]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"
    prep_photo(sys.argv[1], out)
