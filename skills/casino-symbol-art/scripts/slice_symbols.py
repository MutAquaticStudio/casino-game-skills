#!/usr/bin/env python3
"""Cut the generated symbol sheets into one PNG per symbol, with a readability strip.

Reads art/layers/symbols_premium.png (4x2 sheet), symbols_ranks.png (5 glyphs in a row) and
symbols_special.png (Wild, Scatter, Bonus), the names art_harness.py writes. Keys out the magenta
background, finds each symbol as a blob, and writes square 512 px canvases:

  art/symbols/prem_1..prem_8.png, rank_A/K/Q/J/10.png, wild.png, scatter.png, bonus.png
  art/symbols/manifest.json            id, file, source bbox, kind (read by compose_screen.py)
  art/symbols/_readability.png         every symbol at 96 px in colour and in greyscale

Text is never generated: the Wild multiplier badge (default x5) and the SCATTER tag are drawn by code
here (--no-badges to skip, --wild-mult x10 to change). Then run style_check.py on art/symbols/*.png and
silhouette_check.py on the premiums. Exit code 1 if a sheet does not yield the expected count
(regenerate that sheet with more spacing, or cut it by hand).

Usage: python3 slice_symbols.py [art] [--wild-mult x5] [--no-badges]
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from artlib import key_out, crop_alpha, font, fit, layer, components

CANVAS = 512


def blobs(sheet, expect, closing):
    found = sorted(components(sheet, closing=closing), key=lambda t: -t[0])[:expect]
    return [sl for _, sl in found]


def crop_blob(sheet, sl):
    return crop_alpha(sheet.crop((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop)))


def to_canvas(im, pad=0.06):
    box = int(CANVAS * (1 - 2 * pad))
    f = fit(im, box)
    c = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    c.alpha_composite(f, ((CANVAS - f.width) // 2, (CANVAS - f.height) // 2))
    return c


def split_row_by_valleys(sheet, n):
    """Fallback for glyphs that touch: cut at the emptiest columns near the even split points."""
    sheet = crop_alpha(sheet)
    col = (np.asarray(sheet.getchannel("A")) > 10).sum(0)
    W = sheet.width
    cuts = []
    for i in range(1, n):
        e = W * i / n
        lo, hi = int(e - W * 0.05), int(e + W * 0.05)
        cuts.append(lo + int(np.argmin(col[lo:hi])))
    edges = [0] + cuts + [W]
    return [crop_alpha(sheet.crop((edges[i], 0, edges[i + 1], sheet.height))) for i in range(n)]


def add_wild_badge(img, text):
    d = ImageDraw.Draw(img)
    r = int(CANVAS * 0.11)
    cx, cy = int(CANVAS * 0.80), int(CANVAS * 0.80)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(20, 40, 70, 255), outline=(240, 200, 90, 255), width=5)
    f = font(int(r * 1.05))
    tw = d.textlength(text, font=f)
    d.text((cx - tw / 2, cy - r * 0.62), text, fill=(255, 255, 255, 255), font=f)


def add_scatter_tag(img, text="SCATTER"):
    d = ImageDraw.Draw(img)
    f = font(int(CANVAS * 0.07))
    tw = d.textlength(text, font=f)
    bx, by = (CANVAS - tw) / 2, CANVAS * 0.84
    d.rounded_rectangle((bx - 12, by - 5, bx + tw + 12, by + f.size + 7), 9, fill=(20, 26, 40, 235), outline=(240, 200, 90, 255), width=3)
    d.text((bx, by), text, fill=(255, 230, 150, 255), font=f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("art", nargs="?", default="art")
    ap.add_argument("--wild-mult", default="x5")
    ap.add_argument("--no-badges", action="store_true")
    a = ap.parse_args()
    out = os.path.join(a.art, "symbols")
    os.makedirs(out, exist_ok=True)
    items, problems = [], []

    # premiums: 4x2 grid -> two rows, left to right
    prem_sheet = key_out(layer(a.art, "symbols_premium"))
    pb = blobs(prem_sheet, 8, 6)
    if len(pb) != 8:
        problems.append(f"symbols_premium: found {len(pb)} symbols, expected 8")
    else:
        pb.sort(key=lambda s: (s[0].start + s[0].stop) / 2)
        rows = [sorted(pb[:4], key=lambda s: s[1].start), sorted(pb[4:], key=lambda s: s[1].start)]
        for i, sl in enumerate(rows[0] + rows[1]):
            items.append((f"prem_{i + 1}", "premium", crop_blob(prem_sheet, sl)))

    # ranks: A K Q J 10 left to right
    rank_sheet = key_out(layer(a.art, "symbols_ranks"))
    rb = blobs(rank_sheet, 5, 10)
    ranks = [crop_blob(rank_sheet, sl) for sl in sorted(rb, key=lambda s: s[1].start)] if len(rb) == 5 else split_row_by_valleys(rank_sheet, 5)
    if len(rb) != 5:
        print("ranks: glyphs touch, cut at column valleys instead (check the result)")
    for name, im in zip(["A", "K", "Q", "J", "10"], ranks):
        items.append((f"rank_{name}", "rank", im))

    # specials: Wild, Scatter, Bonus left to right
    sp_sheet = key_out(layer(a.art, "symbols_special"))
    sb = blobs(sp_sheet, 3, 4)
    if len(sb) != 3:
        problems.append(f"symbols_special: found {len(sb)} symbols, expected 3")
    else:
        for name, sl in zip(["wild", "scatter", "bonus"], sorted(sb, key=lambda s: s[1].start)):
            items.append((name, "special", crop_blob(sp_sheet, sl)))

    if problems:
        print("\n".join(problems))
        print("regenerate that sheet with wider spacing between symbols, or cut it by hand; nothing written")
        sys.exit(1)

    manifest = []
    canvases = {}
    for name, kind, im in items:
        c = to_canvas(im)
        if not a.no_badges and name == "wild":
            add_wild_badge(c, a.wild_mult)
        if not a.no_badges and name == "scatter":
            add_scatter_tag(c)
        c.save(os.path.join(out, name + ".png"))
        canvases[name] = c
        manifest.append({"id": name, "file": f"symbols/{name}.png", "kind": kind, "source_size": list(im.size)})
    json.dump({"canvas": CANVAS, "symbols": manifest}, open(os.path.join(out, "manifest.json"), "w"), indent=1)

    # readability strip: colour on top, greyscale below, 96 px each, on the board colour
    n, s, g = len(items), 96, 8
    strip = Image.new("RGB", (n * (s + g) + g, 2 * (s + g) + g), (16, 20, 30))
    for i, (name, _, _) in enumerate(items):
        f = fit(canvases[name], s)
        strip.paste(f, (g + i * (s + g) + (s - f.width) // 2, g + (s - f.height) // 2), f)
    top = strip.crop((0, 0, strip.width, s + 2 * g))
    strip.paste(ImageOps.grayscale(top).convert("RGB"), (0, s + 2 * g))
    strip.save(os.path.join(out, "_readability.png"))
    print(f"wrote {n} symbols, manifest.json and _readability.png to {out}")
    print("next: style_check.py art/style.json art/symbols/*.png ; silhouette_check.py on prem_*.png ; view _readability.png (ranks must differ in the greyscale row)")


if __name__ == "__main__":
    main()
