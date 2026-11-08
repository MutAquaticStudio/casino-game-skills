#!/usr/bin/env python3
"""raster_cutout.py - turn painted raster art into transparent, same-size symbol cells.

Painterly generators (references/vendor/claude-drawing) usually paint a whole picture on a
paper or key-colour background. A reel symbol needs a transparent PNG on a fixed square cell.
This script does that last step so the result drops into svg_to_atlas.py (preview / build).

  python3 raster_cutout.py art/raw art/svg --cell 512
  python3 raster_cutout.py art/raw/ruby.png art/svg --key "#ff00ff" --tolerance 40

For every input image (a file, or every .png/.jpg/.webp in a folder):
  1. background = --key colour, or the median of the four corners when --key is omitted
  2. flood-fill from the image border over pixels within --tolerance of the background, so the
     same colour *inside* the symbol is kept; those pixels become alpha 0
  3. soften the cut edge (--feather px) and remove the fringe of background colour (--decontaminate)
  4. crop to the symbol, scale it to fit a square --cell with --pad percent of padding, centre it

Images that already have transparency skip steps 1-3. Writes <name>.png into the output folder.
Needs Pillow and numpy. Always open the result on a dark and a light background and look at the
edge before packing: a hard key on busy painterly texture can leave halos.
"""
import argparse
import sys
from collections import deque
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageFilter
except ImportError:
    sys.exit("Pillow and numpy are required: pip install pillow numpy")

EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def parse_hex(s):
    s = s.lstrip("#")
    if len(s) != 6:
        sys.exit(f"--key must be #rrggbb, got {s!r}")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def corner_colour(rgb):
    h, w = rgb.shape[:2]
    k = max(2, min(h, w) // 40)
    patches = [rgb[:k, :k], rgb[:k, -k:], rgb[-k:, :k], rgb[-k:, -k:]]
    return np.median(np.concatenate([p.reshape(-1, 3) for p in patches]), axis=0)


def flood_background(close):
    """True where `close` is True AND connected to the image border (4-neighbourhood)."""
    h, w = close.shape
    seen = np.zeros_like(close)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if close[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if close[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and close[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    return seen


def cutout(im, key, tol, feather, decontaminate):
    im = im.convert("RGBA")
    arr = np.asarray(im, np.float32)
    rgb, alpha = arr[..., :3], arr[..., 3]
    if alpha.min() < 250:  # already transparent: keep as is
        return im
    bg = parse_hex(key) if key else corner_colour(rgb)
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=2))
    bgmask = flood_background(dist <= tol)
    a = np.where(bgmask, 0.0, 255.0).astype(np.float32)
    if feather > 0:
        a_img = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(feather))
        a = np.asarray(a_img, np.float32)
        a[bgmask & (a < 128)] *= 0.0  # keep the far background fully clear
    out = rgb.copy()
    if decontaminate:
        # pixels on the soft edge are a mix of symbol and background: push them away from bg
        edge = (a > 0) & (a < 255)
        t = np.clip(a[edge] / 255.0, 0.05, 1.0)[:, None]
        out[edge] = np.clip((rgb[edge] - bg * (1 - t)) / t, 0, 255)
    res = np.dstack([out, a]).astype(np.uint8)
    return Image.fromarray(res, "RGBA")


def fit_cell(im, cell, pad_pct):
    box = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if box is None:
        raise ValueError("nothing left after cutout; lower --tolerance or set --key")
    im = im.crop(box)
    inner = max(1, round(cell * (1 - 2 * pad_pct / 100)))
    s = inner / max(im.width, im.height)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    sheet = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    sheet.alpha_composite(im, ((cell - im.width) // 2, (cell - im.height) // 2))
    return sheet


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="an image file or a folder of images")
    ap.add_argument("out", help="output folder (created); files are written as <name>.png")
    ap.add_argument("--cell", type=int, default=512, help="square cell size in px (default 512)")
    ap.add_argument("--pad", type=float, default=8.0, help="padding per side in percent of the cell (default 8)")
    ap.add_argument("--key", default=None, help="background colour #rrggbb (default: median of the 4 corners)")
    ap.add_argument("--tolerance", type=float, default=36.0, help="RGB distance counted as background (default 36)")
    ap.add_argument("--feather", type=float, default=0.8, help="edge softening in px (default 0.8, 0 = hard)")
    ap.add_argument("--no-decontaminate", action="store_true", help="keep the original edge colours")
    a = ap.parse_args()

    src = Path(a.src)
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in EXTS) if src.is_dir() else [src]
    if not files:
        sys.exit(f"No images in {src}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for f in files:
        try:
            im = cutout(Image.open(f), a.key, a.tolerance, a.feather, not a.no_decontaminate)
            fit_cell(im, a.cell, a.pad).save(out / f"{f.stem}.png", optimize=True)
            print(f"cutout: {f.name} -> {out / (f.stem + '.png')}")
        except ValueError as e:
            print(f"ERROR  {f.name}: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
