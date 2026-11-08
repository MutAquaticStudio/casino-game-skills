#!/usr/bin/env python3
"""Compose a preview screen from the generated layers: backdrop, framed reel board, symbols, hero, HUD.

A preview to judge the set as one picture before wiring it into Pixi; not the game's renderer. Reads the
art folder written by art_harness.py and slice_symbols.py:
  art/layers/backdrop.png, frame.png, board.png, hero.png   art/symbols/*.png + manifest.json   art/style.json (grid)

  python3 compose_screen.py [art] [--layout pc|phone] [--out art/preview_pc.png] [--seed 7] [--dividers]

Layouts follow the measured references in stake-casino-game-dev references/layout-wireframes.md:
  pc     1280x720: frame right of centre (about 60 percent of the width), hero standing outside the frame on the left, dock at the bottom
  phone  780x1688 (390x844 at 2x): frame full width, hero bust overlapping the top of the frame, meter strip under it, HUD pinned bottom
The HUD is drawn by code with placeholder values. Wild and Scatter are placed in the grid so the special
symbols can be judged against the rest.
"""
import argparse, json, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi
from artlib import key_out, crop_alpha, font, fit, layer, load_art


def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    r = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (r.width - w) // 2, (r.height - h) // 2
    return r.crop((x, y, x + w, y + h))


def window_of(frame):
    """Largest enclosed transparent region of the keyed frame = the reel opening."""
    al = np.asarray(frame.getchannel("A"))
    filled = ndi.binary_fill_holes(al > 10)
    hole = filled & (al <= 10)
    lab, n = ndi.label(hole)
    if not n:
        raise SystemExit("frame has no enclosed opening: the frame prompt must leave the window magenta so it keys out")
    sizes = ndi.sum(hole, lab, range(1, n + 1))
    big = lab == (1 + int(np.argmax(sizes)))
    ys, xs = np.where(big)
    return big, (xs.min(), ys.min(), xs.max(), ys.max())


def hud(canvas, layout, W, H):
    d = ImageDraw.Draw(canvas, "RGBA")
    if layout == "pc":
        y0, x0, x1 = int(H * 0.86), int(W * 0.20), int(W * 0.90)
        d.rounded_rectangle((x0, y0, x1, int(H * 0.97)), 12, fill=(10, 14, 20, 235))
        cx, cy, r = int(W * 0.93), int(H * 0.915), int(H * 0.06)
        cells = [(0.23, "BALANCE", "$1,000.00"), (0.46, "WIN", "$0.00"), (0.68, "BET", "$1.00")]
        fs, fv = font(int(H * 0.017)), font(int(H * 0.028))
        for fx, lab, val in cells:
            d.text((int(W * fx), y0 + int(H * 0.018)), lab, fill=(150, 160, 170, 255), font=fs)
            d.text((int(W * fx), y0 + int(H * 0.048)), val, fill=(255, 255, 255, 255), font=fv)
    else:
        y0 = int(H * 0.88)
        d.rectangle((0, y0, W, int(H * 0.94)), fill=(10, 14, 20, 240))
        d.rectangle((0, int(H * 0.94), W, H), fill=(6, 8, 12, 255))
        cx, cy, r = int(W * 0.5), int(H * 0.905), int(W * 0.09)
        fs, fv = font(int(H * 0.012)), font(int(H * 0.02))
        for fx, lab, val in [(0.05, "BALANCE", "$1,000.00"), (0.38, "BET", "$1.00"), (0.72, "WIN", "$0.00")]:
            d.text((int(W * fx), y0 + int(H * 0.008)), lab, fill=(150, 160, 170, 255), font=fs)
            d.text((int(W * fx), y0 + int(H * 0.026)), val, fill=(255, 255, 255, 255), font=fv)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(10, 14, 20, 245), outline=(255, 255, 255, 255), width=max(3, r // 9))
    d.arc((cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2), 40, 330, fill=(255, 255, 255, 255), width=max(3, r // 7))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("art", nargs="?", default="art")
    ap.add_argument("--layout", choices=["pc", "phone"], default="pc")
    ap.add_argument("--out"); ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--dividers", action="store_true", help="draw thin column dividers (only if the board texture has none)")
    a = ap.parse_args()
    style, _ = load_art(a.art)
    grid = style.get("grid", {"cols": 5, "rows": 4})
    cols, rows = grid["cols"], grid["rows"]
    W, H = (1280, 720) if a.layout == "pc" else (780, 1688)

    mpath = os.path.join(a.art, "symbols", "manifest.json")
    if not os.path.exists(mpath):
        raise SystemExit(f"{mpath} missing: run slice_symbols.py first")
    ids = [s["id"] for s in json.load(open(mpath))["symbols"]]
    syms = {i: Image.open(os.path.join(a.art, "symbols", i + ".png")).convert("RGBA") for i in ids}
    normal = [i for i in ids if i.startswith(("prem_", "rank_"))]
    rnd = random.Random(a.seed)

    canvas = cover(layer(a.art, "backdrop").convert("RGB"), W, H).convert("RGBA")

    # frame placement
    fr = crop_alpha(key_out(layer(a.art, "frame")))
    fw = int(W * (0.62 if a.layout == "pc" else 1.0))
    fh = int(fr.height * fw / fr.width)
    max_h = int(H * (0.83 if a.layout == "pc" else 0.5))
    if fh > max_h:
        fh, fw = max_h, int(fr.width * max_h / fr.height)
    fr = fr.resize((fw, fh), Image.LANCZOS)
    fx = int(W * 0.30) if a.layout == "pc" else 0
    fy = int(H * 0.04) if a.layout == "pc" else int(H * 0.52 - fh / 2)   # phone: centred between the hero zone and the HUD
    big, (x0, y0, x1, y1) = window_of(fr)

    # board texture inside the opening
    tex = cover(layer(a.art, "board").convert("RGB"), x1 - x0 + 1, y1 - y0 + 1)
    tex = Image.eval(tex, lambda v: min(255, int(v * 1.35) + 6))
    board = Image.new("RGBA", fr.size, (0, 0, 0, 0))
    board.paste(tex.convert("RGBA"), (x0, y0))
    mask = Image.fromarray((big * 255).astype(np.uint8))
    board.putalpha(mask)
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    if a.dividers:
        bd = ImageDraw.Draw(board, "RGBA")
        for k in range(1, cols):
            x = int(x0 + k * cw)
            bd.line((x - 2, y0, x - 2, y1), fill=(0, 0, 0, 150), width=3)
            bd.line((x, y0, x, y1), fill=(214, 170, 80, 190), width=2)
    vig = Image.new("L", fr.size, 0)
    ImageDraw.Draw(vig).rectangle((x0, y0, x1, y1), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(max(8, fw // 40)))
    shade = Image.new("RGBA", fr.size, (0, 0, 0, 150))
    inv = 255 - np.asarray(vig).astype(np.int32)
    shade.putalpha(Image.fromarray((inv * np.asarray(mask) // 255).astype(np.uint8)))
    board.alpha_composite(shade)
    canvas.alpha_composite(board, (fx, fy))

    # symbols: random normal ones, one Wild and one Scatter placed to judge them in context
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    special = {}
    for sid in ("wild", "scatter"):
        if sid in syms and cells:
            special[cells.pop(rnd.randrange(len(cells)))] = sid
    sz = int(min(cw, ch) * 0.94)
    for r in range(rows):
        for c in range(cols):
            sid = special.get((r, c)) or rnd.choice(normal)
            s2 = syms[sid].resize((sz, sz), Image.LANCZOS)
            canvas.alpha_composite(s2, (int(fx + x0 + c * cw + (cw - sz) / 2), int(fy + y0 + r * ch + (ch - sz) / 2)))
    canvas.alpha_composite(fr, (fx, fy))

    # hero
    hero = crop_alpha(key_out(layer(a.art, "hero", required=False) or Image.new("RGB", (8, 8), (255, 0, 255))))
    if hero.width > 8:
        if a.layout == "pc":
            hh = int(H * 0.82); hw = int(hero.width * hh / hero.height)
            canvas.alpha_composite(hero.resize((hw, hh), Image.LANCZOS), (-int(hw * 0.06), H - hh - int(H * 0.02)))
        else:
            bust = hero.crop((0, 0, hero.width, int(hero.height * 0.55)))
            bw = int(W * 0.62); bh = int(bust.height * bw / bust.width)
            canvas.alpha_composite(bust.resize((bw, bh), Image.LANCZOS), (int(W * 0.02), fy - int(bh * 0.72)))
    hud(canvas, a.layout, W, H)
    out = a.out or os.path.join(a.art, f"preview_{a.layout}.png")
    canvas.convert("RGB").save(out)
    print("wrote", out)
    if a.layout == "phone":
        print(f"board window is {int((x1 - x0) * 100 / W)} percent of the width and the frame fills {int(fh * 100 / H)} percent of the height. "
              "A landscape frame leaves dead bands above and below on a phone: judge it with stake-casino-game-dev scripts/mobile_layout.py, "
              "and generate a second, taller frame (set a squarer grid or ask for a portrait window) if the bands exceed 14 percent each.")


if __name__ == "__main__":
    main()
