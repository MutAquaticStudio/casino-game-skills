#!/usr/bin/env python3
"""Check and preview the symbol animation recipes in symbol_fx.json (evaluated by symbol_fx.mjs, the same code a game uses).

Checks (FAIL = fix the recipe):
  - one-shot recipes end exactly on their rest value (scale 1, alpha 1, rotation 0) except `dim`, which ends dimmed by design
  - looping recipes start and end on the same value on every track (no pop when the loop wraps)
  - squash and stretch keeps volume: scaleX * scaleY stays in [0.92, 1.12] for `land`
  - peak scale times symbol fill (share of the cell the artwork covers) stays <= 1.0, so a winning symbol does not cover its neighbours
Usage: python3 symbol_fx_preview.py symbol.png [--fill 0.84] [--fps 30] [--out fx_preview.mp4] [--cell 200]
Needs: node, pillow, numpy, ffmpeg (for the mp4).
"""
import argparse, json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REST = {"scaleX": 1.0, "scaleY": 1.0, "alpha": 1.0, "rotation": 0.0, "y": 0.0, "glow": 0.0}


def sample(name, fps):
    r = subprocess.run(["node", os.path.join(HERE, "symbol_fx.mjs"), os.path.join(HERE, "symbol_fx.json"), name, str(fps)], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr)
    return json.loads(r.stdout)


def checks(fill):
    rec = json.load(open(os.path.join(HERE, "symbol_fx.json"))); fails = 0
    print(f"{'recipe':8} {'dur':>5} {'loop':>5}  checks")
    for name, r in rec.items():
        if name.startswith("_"): continue
        s = sample(name, 120)["samples"]; first, last = s[0], s[-1]; notes = []
        if r["loop"]:
            for k in r["tracks"]:
                if abs(first[k] - last[k]) > 1e-6: notes.append(f"loop mismatch on {k}"); fails += 1
        elif name != "dim" and name != "appear":
            for k in r["tracks"]:
                if abs(last[k] - REST[k]) > 1e-6: notes.append(f"does not end at rest on {k} ({last[k]:.3f})"); fails += 1
        if name == "appear":
            for k in ("scaleX", "scaleY", "alpha"):
                if abs(last[k] - 1.0) > 1e-6: notes.append(f"appear ends at {last[k]:.3f} on {k}"); fails += 1
        if name == "land":
            vol = [x["scaleX"] * x["scaleY"] for x in s]
            if not (0.92 <= min(vol) and max(vol) <= 1.12): notes.append(f"volume {min(vol):.2f}..{max(vol):.2f} outside 0.92..1.12"); fails += 1
        peak = max([x.get("scaleX", 1) for x in s] + [x.get("scaleY", 1) for x in s])
        if peak * fill > 1.0: notes.append(f"peak scale {peak:.2f} x fill {fill} = {peak*fill:.2f} covers the neighbours"); fails += 1
        print(f"{name:8} {r['duration']:5.2f} {str(r['loop']):>5}  {'; '.join(notes) if notes else 'ok'}  (peak scale {peak:.2f})")
    return fails


def render(sym, name, fps, cell, loops):
    data = sample(name, fps); s = data["samples"][:-1] if data["loop"] else data["samples"]
    frames = []
    for _ in range(loops if data["loop"] else 1):
        for x in s:
            im = Image.new("RGBA", (cell, cell), (27, 35, 48, 255))
            base = sym.copy(); sc = cell * 0.84 / max(base.size); base = base.resize((int(base.width * sc), int(base.height * sc)), Image.LANCZOS)
            w, h = int(base.width * x.get("scaleX", 1)), int(base.height * x.get("scaleY", 1))
            t = base.resize((max(1, w), max(1, h)), Image.LANCZOS).rotate(-x.get("rotation", 0), expand=True, resample=Image.BICUBIC)
            if x.get("glow", 0) > 0:
                halo = t.copy().resize((int(t.width * 1.18), int(t.height * 1.18)), Image.LANCZOS)
                a = halo.getchannel("A").point(lambda v: int(v * 0.55 * x["glow"])).filter(ImageFilter.GaussianBlur(max(2, cell * 0.035)))
                tint = Image.new("RGBA", halo.size, (255, 225, 140, 255)); tint.putalpha(a)
                im.alpha_composite(tint, ((cell - halo.width) // 2, (cell - halo.height) // 2 - int(x.get("y", 0) * cell / 140)))
            if x.get("alpha", 1) < 1:
                t.putalpha(t.getchannel("A").point(lambda v: int(v * x["alpha"])))
            im.alpha_composite(t, ((cell - t.width) // 2, (cell - t.height) // 2 - int(x.get("y", 0) * cell / 140)))
            frames.append(im)
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol", nargs="?"); ap.add_argument("--fill", type=float, default=0.84); ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default="fx_preview.mp4"); ap.add_argument("--cell", type=int, default=240)
    a = ap.parse_args()
    fails = checks(a.fill)
    if a.symbol:
        sym = Image.open(a.symbol).convert("RGBA"); names = ["idle", "land", "appear", "win", "dim", "tease"]
        tracks = [render(sym, n, a.fps, a.cell, 3 if n in ("idle", "win", "tease") else 1) for n in names]
        n = max(len(t) for t in tracks); d = 8   # hold the first frame
        sheet = []
        for i in range(n + d):
            row = Image.new("RGBA", (a.cell * len(names), a.cell + 22), (14, 18, 26, 255)); dr = ImageDraw.Draw(row)
            for k, t in enumerate(tracks):
                fr = t[min(max(i - d // 2, 0), len(t) - 1)] if len(t) else None
                if len(t) > 1 and tracks[k] is not None and names[k] in ("idle", "win", "tease"): fr = t[(i % len(t))]
                row.alpha_composite(fr, (k * a.cell, 22)); dr.text((k * a.cell + 8, 5), names[k], fill=(255, 220, 120, 255))
            sheet.append(row.convert("RGB"))
        os.makedirs("_fx_frames", exist_ok=True)
        for i, f in enumerate(sheet): f.save(f"_fx_frames/f_{i:04d}.png")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(a.fps), "-i", "_fx_frames/f_%04d.png", "-vf", "format=yuv420p", a.out], check=True)
        print("wrote", a.out)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
