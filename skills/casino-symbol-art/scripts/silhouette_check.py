#!/usr/bin/env python3
"""Check that symbols differ by silhouette (shape), the first thing a player reads.

Each symbol is fitted into a square cell at its real on-screen size, filled solid, and compared
with every other symbol by intersection-over-union (IoU) of the filled masks. High IoU means two
symbols have the same outline and will be confused at a glance.

Usage:
  python3 silhouette_check.py art/layers/sym_*.png [--size 96] [--max-iou 0.80] [--out art/silhouettes.png]

Reading the result:
  - freeform premiums (no frame): every pair should be below --max-iou; fix pairs that exceed it.
  - roundel or tile premiums share one outline on purpose, so every pair scores high. That is not a
    defect; tell them apart by the object inside and the dominant colour, and check greyscale
    readability instead (slice_symbols.py makes that strip).
Exit code 1 if any pair exceeds --max-iou.
"""
import argparse, itertools, os, sys
import numpy as np
from PIL import Image


def mask_of(path, size):
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).astype(np.int32)
    R, G, B, A = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    key = (R > 175) & (B > 175) & (G < 115) & (np.abs(R - B) < 60)   # magenta key
    m = ((A > 10) & ~key).astype(np.uint8) * 255
    ys, xs = np.where(m > 0)
    if len(xs) == 0:
        return np.zeros((size, size), bool)
    m = Image.fromarray(m).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    s = (size - 8) / max(m.width, m.height)
    m = m.resize((max(1, int(m.width * s)), max(1, int(m.height * s))), Image.LANCZOS)
    cell = Image.new("L", (size, size), 0)
    cell.paste(m, ((size - m.width) // 2, (size - m.height) // 2))
    return np.asarray(cell) > 127


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+"); ap.add_argument("--size", type=int, default=96)
    ap.add_argument("--max-iou", type=float, default=0.80); ap.add_argument("--out")
    a = ap.parse_args()
    names = [os.path.basename(f) for f in a.files]
    masks = [mask_of(f, a.size) for f in a.files]
    bad = []
    rows = []
    for (i, mi), (j, mj) in itertools.combinations(enumerate(masks), 2):
        u = (mi | mj).sum()
        iou = float((mi & mj).sum() / u) if u else 0.0
        rows.append((iou, names[i], names[j]))
        if iou > a.max_iou:
            bad.append((iou, names[i], names[j]))
    rows.sort(reverse=True)
    print(f"{len(masks)} silhouettes at {a.size}px; closest pairs:")
    for iou, x, y in rows[:6]:
        print(f"  IoU {iou:.2f}  {x} ~ {y}" + ("   <-- too similar" if iou > a.max_iou else ""))
    print(f"median IoU {np.median([r[0] for r in rows]):.2f}; pairs over {a.max_iou}: {len(bad)}")
    if a.out:
        sheet = Image.new("L", (len(masks) * (a.size + 6) + 6, a.size + 12), 40)
        for k, m in enumerate(masks):
            sheet.paste(Image.fromarray((m * 255).astype(np.uint8)), (6 + k * (a.size + 6), 6))
        sheet.save(a.out)
        print("wrote", a.out)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
