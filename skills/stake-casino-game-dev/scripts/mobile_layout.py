#!/usr/bin/env python3
"""Phone (portrait) layout tools for slot games: measure a screenshot's layout against the rules, or compute a recommended layout.

Why: a board that is small and floats in the middle of a tall phone screen, with empty bands above it and between it and the controls,
looks unfinished and puts the spin button far from the board. These tools turn that into numbers.

  report   measure rectangles you read off a screenshot (use `grid` to read them) and check them against the rules:
           python3 mobile_layout.py report spec.json [--png report.png]
  solve    compute a layout for a viewport from the sizes of your art blocks:
           python3 mobile_layout.py solve --viewport 390x844 --board-aspect 1.34 --meter-h 0.12 --hud 0.2 [--hero-min 0.16] [--scene 0.12] [--gap 0.02] [--png solved.png]
           (meter-h is a fraction of the viewport WIDTH; hud, hero-min, scene and gap are fractions of the HEIGHT; board-aspect = board frame width / height.
            hero-min is the smallest hero zone you accept; the reference at 390x844 had about 0.16 to 0.18, at 375x667 about 0.12)
  grid     draw a 10 percent grid with pixel and percent labels on a screenshot, to read rectangles:
           python3 mobile_layout.py grid shot.png --out shot_grid.png

spec.json:
  {"name": "...", "viewport": [390, 844], "dpr": 2, "image": [780, 1688],            # image size in px (dpr x viewport for a native screenshot)
   "rects": {"logo": [x, y, w, h], "board": [x, y, w, h], "meter": [..], "balance": [..], "controls": [..], "spin": [..]},   # image px
   "buttons": {"spin": [x, y, w, h], "bet_minus": [..]}}                                  # optional: touch targets, image px
Names used by the rules: `board` (frame including its decoration), `meter` (feature panel), `logo` (logo and hero block), `float_*` (floating buttons), `controls`, `balance`, `spin`.
Rules (see references/mobile-ui.md; thresholds are calibrated on five reference games, not on a standard): board frame width >= 95 percent of the viewport
width (warn from 88); board height >= 34 percent (warn from 28), which a wide grid may not reach; dead bands (vertical gaps between listed blocks, top and between)
each <= 14 percent, total <= 26 percent (warn up to 20 and 32, fail beyond); gap from the last block above the HUD to the HUD <= 14 percent (floating buttons
count as HUD); HUD block 12 to 26 percent of the height; spin button >= 44 css px (fail) and >= 56 css px and >= 14 percent of the width (warn) and in the bottom 30 percent;
every button >= 44 css px; nothing important within 12 css px of the left or right edge except frame decoration.
Exit code 1 if any FAIL.
"""
import argparse, json, sys
from PIL import Image, ImageDraw, ImageFont


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()


def check(spec):
    vw, vh = spec["viewport"]; iw, ih = spec["image"]; sx, sy = vw / iw, vh / ih       # image px -> css px
    R = {k: tuple(v) for k, v in spec["rects"].items()}
    out = []
    def add(name, value, verdict, note=""): out.append((name, value, verdict, note))
    bx, by, bw, bh = R["board"]
    wf, hf = bw * sx / vw, bh * sy / vh
    add("board width", f"{100*wf:.0f}% of width", "ok" if wf >= 0.95 else ("WARN" if wf >= 0.88 else "FAIL"), "frame including decoration; the reference games bleed the frame to the full width")
    add("board height", f"{100*hf:.0f}% of height", "ok" if hf >= 0.34 else ("WARN" if hf >= 0.28 else "FAIL"), "set by the grid shape (a wide 6 x 5 grid cannot reach 45 percent); fill the rest with art, see the dead-band rule")
    # vertical stack of blocks, top to bottom
    blocks = sorted(((k, v) for k, v in R.items() if k not in ("spin",)), key=lambda kv: kv[1][1])
    gaps = []; cursor = 0.0
    for k, (x, y, w, h) in blocks:
        top = y * sy / vh
        if top - cursor > 0.003: gaps.append((("top edge" if cursor == 0 else "previous block"), k, top - cursor))
        cursor = max(cursor, (y + h) * sy / vh)
    worst = max((g[2] for g in gaps), default=0.0); total = sum(g[2] for g in gaps)
    gdesc = "; ".join(f"{a} to {b}: {100*g:.0f}%" for a, b, g in gaps if g > 0.02) or "none above 2%"
    add("dead bands", f"worst {100*worst:.0f}%, total {100*total:.0f}%", "ok" if worst <= 0.14 and total <= 0.26 else ("WARN" if worst <= 0.20 and total <= 0.32 else "FAIL"), gdesc)
    hud_names = [k for k in R if k in ("balance", "controls", "spin", "hud") or k.startswith("float")]
    if hud_names:
        hy = min(R[k][1] for k in hud_names); hudh = (vh - hy * sy) / vh
        add("HUD block", f"{100*hudh:.0f}% of height", "ok" if 0.12 <= hudh <= 0.26 else "WARN", "everything from the top of the balance/controls to the bottom edge")
        gap = (hy - (by + bh) if hy > by + bh else 0) * sy / vh
        meter = R.get("meter")
        if meter:
            gap_hud = (hy - (meter[1] + meter[3])) * sy / vh if hy > meter[1] + meter[3] else 0
            add("board to HUD gap", f"{100*gap_hud:.0f}% (after the meter)", "ok" if gap_hud <= 0.14 else ("WARN" if gap_hud <= 0.20 else "FAIL"), "distance from the last block above the HUD (floating buttons count as HUD) to the HUD")
        else:
            add("board to HUD gap", f"{100*gap:.0f}%", "ok" if gap <= 0.14 else ("WARN" if gap <= 0.20 else "FAIL"), "distance from the board to the HUD")
    spin = spec.get("buttons", {}).get("spin") or R.get("spin")
    if spin:
        x, y, w, h = spin; d = min(w * sx, h * sy)
        add("spin button", f"{d:.0f} css px, {100*d/vw:.0f}% of width", "ok" if d >= 56 and d / vw >= 0.14 else ("WARN" if d >= 44 else "FAIL"), "min 44; 56 and 14 percent of the width recommended")
        cy = (y + h / 2) * sy / vh
        add("spin position", f"centre at {100*cy:.0f}% of height", "ok" if cy >= 0.70 else "WARN", "thumb zone: bottom 30 percent")
    small = [(n, min(r[2] * sx, r[3] * sy)) for n, r in spec.get("buttons", {}).items() if min(r[2] * sx, r[3] * sy) < 44]
    if spec.get("buttons"):
        add("touch targets", "all >= 44 css px" if not small else ", ".join(f"{n} {d:.0f}px" for n, d in small), "ok" if not small else "FAIL", "every button 44 x 44 css px or more")
    return out


def draw(spec, rects, title, size=(390, 844), scale=0.55):
    vw, vh = size; iw, ih = spec["image"] if "image" in spec else size
    sx, sy = vw / iw, vh / ih
    im = Image.new("RGB", (int(vw * scale) + 2, int(vh * scale) + 26), (24, 28, 38)); d = ImageDraw.Draw(im); f = font(11)
    d.rectangle((1, 25, int(vw * scale) + 1, int(vh * scale) + 25), outline=(120, 130, 150))
    cols = {"logo": (240, 200, 90), "board": (90, 180, 240), "meter": (180, 140, 240), "balance": (120, 220, 150), "controls": (120, 220, 150), "spin": (255, 120, 90), "hud": (120, 220, 150)}
    d.text((4, 5), title, fill=(255, 255, 255), font=f)
    for k, (x, y, w, h) in rects.items():
        c = cols.get(k, (200, 200, 200)); X, Y, W, H = x * sx * scale, y * sy * scale + 25, w * sx * scale, h * sy * scale
        d.rectangle((X, Y, X + W, Y + H), outline=c, width=2, fill=tuple(int(v * 0.25) for v in c)); d.text((X + 3, Y + 2), k, fill=c, font=f)
    return im


def solve(a):
    """Layout recipe measured on Odin's Vault at three phone aspect ratios (375x667, 390x844, 360x800): the board is always the full viewport width
    and is anchored just below a top hero zone; the HUD is pinned to the bottom; the height left over goes first to a short decorated SCENE band
    between the feature meter and the HUD (11 to 13 percent in the reference, it holds the floating buttons), and only then to the top hero zone.
    On short screens the hero zone shrinks and may clip its top (keep the face visible)."""
    vw, vh = (int(v) for v in a.viewport.split("x"))
    hud = a.hud * vh; side = a.side * vw
    board_w = vw - 2 * side; board_h = board_w / a.board_aspect
    meter_h = a.meter_h * vw; hero_min = a.hero_min * vh; gap = a.gap * vh
    fixed = board_h + meter_h + hud + gap * (2 if meter_h else 1)
    free = vh - fixed - hero_min
    notes = []
    if free < 0:
        notes.append(f"short screen: the hero zone shrinks to {max(vh - fixed, 0):.0f} px ({100*max(vh - fixed, 0)/vh:.0f}% of the height); clip the top of the mascot, keep the face")
        hero = max(vh - fixed, 0); scene = 0.0
        if vh - fixed < 0.06 * vh:
            k = (vh - hud - hero_min * 0.5 - meter_h - gap * (2 if meter_h else 1)) / board_h
            board_h *= k; board_w = board_h * a.board_aspect; side = (vw - board_w) / 2; hero = hero_min * 0.5
            notes.append(f"very short: the board is scaled to {100*board_w/vw:.0f}% of the width")
    else:
        scene = min(free, a.scene * vh); hero = hero_min + (free - scene)
        notes.append(f"{free:.0f} css px ({100*free/vh:.0f}% of the height) left over: {scene:.0f} px to the scene band, {free - scene:.0f} px to the top hero zone")
        if (free - scene) / vh > 0.12:
            notes.append("the hero zone is large: use a bigger mascot overlapping the top edge of the board (its lower body hidden behind the frame), or a taller frame")
    R = {}; y = 0.0
    R["logo"] = (side, y, board_w, hero); y += hero
    R["board"] = (side, y, board_w, board_h); y += board_h
    if meter_h: y += gap; R["meter"] = (side, y, board_w, meter_h); y += meter_h
    if scene > 1: R["scene"] = (0, y + gap / 2, vw, scene)
    R["hud"] = (0, vh - hud, vw, hud)
    print(f"viewport {vw}x{vh}: board {board_w:.0f} x {board_h:.0f} ({100*board_w/vw:.0f}% x {100*board_h/vh:.0f}%), hero zone {hero:.0f} px ({100*hero/vh:.0f}%), scene band {scene:.0f} px ({100*scene/vh:.0f}%), HUD {hud:.0f} px ({100*hud/vh:.0f}%)")
    for n in notes: print("  -", n)
    for k, (x, yy, w, h) in R.items(): print(f"  {k:6} x {x:5.0f}  y {yy:5.0f}  w {w:5.0f}  h {h:5.0f}   ({100*yy/vh:.0f}% to {100*(yy+h)/vh:.0f}% of the height)")
    if a.png: draw({"image": (vw, vh)}, R, f"solved {vw}x{vh}", (vw, vh)).save(a.png); print("wrote", a.png)


def grid(a):
    im = Image.open(a.shot).convert("RGB"); W, H = im.size; d = ImageDraw.Draw(im, "RGBA"); f = font(max(12, W // 40))
    for i in range(1, 10):
        y = H * i // 10; x = W * i // 10
        d.line((0, y, W, y), fill=(255, 255, 0, 150), width=2); d.line((x, 0, x, H), fill=(0, 255, 255, 110), width=1)
        d.text((4, y + 2), f"{i*10}%  y={y}", fill=(255, 255, 0, 255), font=f); d.text((x + 2, 4), f"{i*10}%", fill=(0, 255, 255, 255), font=f)
    im.save(a.out); print("wrote", a.out, f"({W}x{H})")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("report"); p.add_argument("spec"); p.add_argument("--png")
    p = sub.add_parser("solve"); p.add_argument("--viewport", required=True); p.add_argument("--board-aspect", type=float, required=True, help="board frame width / height")
    p.add_argument("--meter-h", type=float, default=0.0, help="feature meter height as a fraction of the viewport width"); p.add_argument("--hero-min", type=float, default=0.16, help="smallest hero zone, fraction of the height"); p.add_argument("--scene", type=float, default=0.12, help="scene band between meter and HUD, fraction of the height")
    p.add_argument("--hud", type=float, default=0.125, help="HUD height as a fraction of the viewport height"); p.add_argument("--gap", type=float, default=0.02, help="gap between blocks as a fraction of the height")
    p.add_argument("--side", type=float, default=0.01, help="side margin as a fraction of the width"); p.add_argument("--png")
    p = sub.add_parser("grid"); p.add_argument("shot"); p.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "solve": return solve(a)
    if a.cmd == "grid": return grid(a)
    spec = json.load(open(a.spec)); res = check(spec)
    print(spec.get("name", ""), "viewport", "x".join(str(v) for v in spec["viewport"]))
    for n, v, vd, note in res: print(f"{n:16} {v:36} {vd:5} {note}")
    if a.png:
        draw(spec, {k: tuple(v) for k, v in spec["rects"].items()}, spec.get("name", ""), tuple(spec["viewport"])).save(a.png); print("wrote", a.png)
    sys.exit(1 if any(r[2] == "FAIL" for r in res) else 0)


if __name__ == "__main__":
    main()
