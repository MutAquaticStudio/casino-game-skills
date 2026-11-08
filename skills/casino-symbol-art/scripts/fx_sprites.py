#!/usr/bin/env python3
"""Generate the three shared win sprites the `win` recipe in symbol_fx.json expects, tinted from the set's warm accent.

  art/fx/flash_disc.png   soft bright disc, drawn additively over the symbol (flash 0-0.16 s)
  art/fx/glow_ring.png    ring of light around the symbol (glow, to 0.40 s)
  art/fx/glint.png        four-point star sparkle (about 0.40 s)

Drawn by code, so they are original, identical across games and cost nothing. Use blendMode 'add' in Pixi.
Premium "lit" variants (the symbol itself rendered emissive) are made per symbol: see references/symbol-fx.md.

Usage: python3 fx_sprites.py [art] [--size 256] [--tint "#ffd27a"]   (default tint: warm_accent[0] of art/style.json, lightened)
"""
import argparse, json, os
import numpy as np
from PIL import Image


def hex_rgb(h):
    h = h.lstrip("#"); return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def lighten(rgb, k=0.55):
    return [int(c + (255 - c) * k) for c in rgb]


def rgba(shape_alpha, tint):
    a = np.clip(shape_alpha, 0, 1)
    img = np.zeros(a.shape + (4,), np.uint8)
    img[..., :3] = tint
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("art", nargs="?", default="art")
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--tint")
    a = ap.parse_args()
    tint = hex_rgb(a.tint) if a.tint else None
    if tint is None:
        sp = os.path.join(a.art, "style.json")
        warm = json.load(open(sp)).get("warm_accent", ["#d9a53a"]) if os.path.exists(sp) else ["#d9a53a"]
        tint = lighten(hex_rgb(warm[0]))
    n = a.size
    y, x = np.mgrid[0:n, 0:n]
    r = np.hypot(x - (n - 1) / 2, y - (n - 1) / 2) / (n / 2)          # 0 centre, 1 edge
    os.makedirs(os.path.join(a.art, "fx"), exist_ok=True)
    # flash disc: bright core, smooth falloff, zero at the edge
    disc = np.clip(1 - r, 0, 1) ** 1.6
    # ring: gaussian band at 0.78 of the radius
    ring = np.exp(-((r - 0.78) / 0.09) ** 2)
    ring[r > 1] = 0
    # glint: two thin crossed streaks fading outward, brightest in the centre
    dx, dy = np.abs(x - (n - 1) / 2) / (n / 2), np.abs(y - (n - 1) / 2) / (n / 2)
    streak = np.maximum(np.exp(-(dy / 0.035) ** 2) * np.clip(1 - dx, 0, 1) ** 1.5,
                        np.exp(-(dx / 0.035) ** 2) * np.clip(1 - dy, 0, 1) ** 1.5)
    core = np.clip(1 - r / 0.18, 0, 1) ** 2
    glint = np.clip(streak + core, 0, 1)
    white = [255, 255, 255]
    for name, shape, col in (("flash_disc", disc, tint), ("glow_ring", ring, tint), ("glint", glint, white)):
        rgba(shape, col).save(os.path.join(a.art, "fx", name + ".png"))
    print(f"wrote flash_disc.png, glow_ring.png, glint.png ({n}px, tint #{''.join('%02x' % c for c in tint)}) to {a.art}/fx; blend mode: add")


if __name__ == "__main__":
    main()
