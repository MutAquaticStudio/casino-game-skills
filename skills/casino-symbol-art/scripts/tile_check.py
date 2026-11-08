#!/usr/bin/env python3
"""Check a game tile (thumbnail) against the Stake Engine approval checklist items that can be measured.

Checklist (stake-casino-game-dev/references/stake-engine/approval-checklist.md, "Game thumbnail"):
  - tile generally bright, does not clash with the Stake background (watch dark edges)
  - background bright and appropriate
  - foreground appropriate, key focus area filled
  - gradient similar colour to the background
  - title inside the inner guidelines, not near the edges
The Tile Editor in the Stake dashboard composes background, foreground, gradient and title; the exact pixel size and
guideline positions are shown there and are NOT known to this script, so pass them in.

Usage:
  python3 tile_check.py tile.png [--title-box X,Y,W,H] [--margin 0.12] [--min-l 52] [--out report.png]
Measures (CIELAB L*, 0 black to 100 white, on the whole tile):
  brightness   mean L* of the tile (default minimum 52)
  edge_dark    mean L* of the outer 6 percent ring versus the tile mean: a ring much darker than the rest is a "dark edge"
  corners      darkest corner patch (any corner below 30 L* is a dark corner)
  focus        share of the centre region (middle 50 percent) that is high-contrast detail rather than flat colour
  title        if --title-box is given, whether the box lies inside the inner guideline margin (default 12 percent per side)
Exit code 1 if any FAIL. WARN means look at it. Thresholds are starting points; the final judge is the Tile Editor preview.
"""
import argparse, sys
import numpy as np
from PIL import Image, ImageDraw


def lab_l(rgb):
    a = rgb.astype(np.float64) / 255.0
    a = np.where(a > 0.04045, ((a + 0.055) / 1.055) ** 2.4, a / 12.92)
    y = a @ np.array([0.2126729, 0.7151522, 0.0721750])
    f = np.where(y > 0.008856, np.cbrt(y), 7.787 * y + 16 / 116)
    return 116 * f - 16


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tile"); ap.add_argument("--title-box"); ap.add_argument("--margin", type=float, default=0.12)
    ap.add_argument("--min-l", type=float, default=52.0); ap.add_argument("--out")
    a = ap.parse_args()
    im = Image.open(a.tile).convert("RGB"); W, H = im.size
    L = lab_l(np.asarray(im))
    res = []
    def add(name, value, verdict, note=""):
        res.append((name, value, verdict, note))
    mean = float(L.mean())
    add("brightness", f"{mean:.0f}", "ok" if mean >= a.min_l else ("WARN" if mean >= a.min_l - 12 else "FAIL"), f"mean L*, minimum {a.min_l:.0f}")
    b = int(min(W, H) * 0.06)
    ring = np.ones((H, W), bool); ring[b:H - b, b:W - b] = False
    ring_l = float(L[ring].mean()); gap = mean - ring_l
    add("edge_dark", f"ring {ring_l:.0f}, tile {mean:.0f}", "ok" if gap < 10 else ("WARN" if gap < 22 else "FAIL"), "outer ring much darker than the tile = dark edge")
    p = int(min(W, H) * 0.12)
    corners = [L[:p, :p].mean(), L[:p, -p:].mean(), L[-p:, :p].mean(), L[-p:, -p:].mean()]
    add("corners", " / ".join(f"{c:.0f}" for c in corners), "ok" if min(corners) >= 40 else ("WARN" if min(corners) >= 30 else "FAIL"), "darkest corner patch")
    cy0, cy1, cx0, cx1 = H // 4, 3 * H // 4, W // 4, 3 * W // 4
    gy, gx = np.gradient(L)
    mag = np.hypot(gx, gy)
    focus = float((mag[cy0:cy1, cx0:cx1] > 4.0).mean()); outer = float((mag > 4.0).mean())
    add("focus", f"detail {focus:.2f} centre vs {outer:.2f} whole", "ok" if focus >= 0.18 else ("WARN" if focus >= 0.08 else "FAIL"), "centre should carry the detail (key focus area filled)")
    if a.title_box:
        x, y, w, h = [float(v) for v in a.title_box.split(",")]
        mx, my = W * a.margin, H * a.margin
        inside = x >= mx and y >= my and x + w <= W - mx and y + h <= H - my
        near = min(x, y, W - (x + w), H - (y + h))
        add("title", f"nearest edge {near:.0f}px, margin {min(mx, my):.0f}px", "ok" if inside else "FAIL", "title box must sit inside the inner guideline")
    print(f"{W}x{H}")
    for n, v, vd, note in res: print(f"{n:11} {v:34} {vd:5} {note}")
    if a.out:
        o = im.copy(); d = ImageDraw.Draw(o)
        d.rectangle((W * a.margin, H * a.margin, W * (1 - a.margin), H * (1 - a.margin)), outline=(255, 255, 0), width=2)
        d.rectangle((b, b, W - b, H - b), outline=(0, 255, 255), width=1)
        if a.title_box:
            x, y, w, h = [float(v) for v in a.title_box.split(",")]; d.rectangle((x, y, x + w, y + h), outline=(255, 0, 255), width=2)
        o.save(a.out)
    sys.exit(1 if any(r[2] == "FAIL" for r in res) else 0)


if __name__ == "__main__":
    main()
