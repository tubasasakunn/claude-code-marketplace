#!/usr/bin/env python3
"""Crop+upscale a region of a screenshot so you can read small UI (badges,
selection circles, page dots, char counters) and measure exact tap coordinates.

Usage: crop.py <img> <x0> <y0> <x1> <y1> [out] [scale]
Prints the output path. Coordinates are in the ORIGINAL image pixel space, so
whatever you measure in the crop maps back as: real = crop_offset + measured.
"""
import sys
from PIL import Image

def main():
    a = sys.argv
    img, x0, y0, x1, y1 = a[1], int(a[2]), int(a[3]), int(a[4]), int(a[5])
    out = a[6] if len(a) > 6 else img.rsplit(".", 1)[0] + "_crop.png"
    scale = float(a[7]) if len(a) > 7 else 0
    im = Image.open(img).crop((x0, y0, x1, y1))
    if scale and scale != 1:
        im = im.resize((int(im.width * scale), int(im.height * scale)))
    im.save(out)
    print(out)

if __name__ == "__main__":
    main()
