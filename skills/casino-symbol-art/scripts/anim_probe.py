#!/usr/bin/env python3
"""Measure how a reference game animates, from a screen recording of its public demo. For learning timing and structure, not for copying art.

Pipeline: record the demo (Playwright recordVideo, about 25 fps, 1280x720), then
  frames    extract frames:                       anim_probe.py frames rec.webm frames/
  montage   contact sheet around a moment:        anim_probe.py montage frames/ 70.0 3 24 sheet.png [--crop x0,y0,x1,y1 --scale 0.4]
  ocr-win   find win events by reading the WIN box: anim_probe.py ocr-win frames/ --box 560,630,700,670 --from 24
  cycle     board cycle timing over many spins:   anim_probe.py cycle frames/ spins.json --cols 372-462,482-572,587-677,692-782,822-912 --y 140,560
`spins.json` is a list of {"t": seconds} press times logged by the recorder (the video clock lags the page clock by about 0.7 s, handled by --offset).
The `cycle` measure assumes a board that CLEARS between rounds (drop-out, empty board, drop-in); it detects the empty beat as the darkest
moment of the reel area, so it does not apply to games with rolling reels. Accuracy is one frame (40 ms) at best; a headless browser with
software rendering may also run slower than a real device, so treat numbers as relative.
Needs: ffmpeg, pillow, numpy; rapidocr-onnxruntime for ocr-win.
"""
import argparse, glob, json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw


def frames(a):
    os.makedirs(a.out, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.video, "-vf", f"fps={a.fps},scale={a.width}:-2", "-q:v", "3", os.path.join(a.out, "f_%05d.jpg")], check=True)
    print(len(glob.glob(os.path.join(a.out, "f_*.jpg"))), "frames")


def montage(a):
    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    fs = sorted(glob.glob(os.path.join(a.dir, "f_*.jpg"))); fps = a.fps
    im0 = Image.open(fs[0]); crop = crop or (0, 0, im0.width, im0.height)
    w, h = int((crop[2] - crop[0]) * a.scale), int((crop[3] - crop[1]) * a.scale)
    rows = (a.n + a.cols - 1) // a.cols; s = Image.new("RGB", (a.cols * w, rows * h)); d = ImageDraw.Draw(s)
    for k in range(a.n):
        i = int(a.t0 * fps) + k * a.step
        if i >= len(fs): break
        s.paste(Image.open(fs[i]).crop(crop).resize((w, h)), ((k % a.cols) * w, (k // a.cols) * h))
        d.rectangle(((k % a.cols) * w, (k // a.cols) * h, (k % a.cols) * w + 70, (k // a.cols) * h + 13), fill=(0, 0, 0)); d.text(((k % a.cols) * w + 3, (k // a.cols) * h + 1), f"{i / fps:.2f}s", fill=(255, 255, 0))
    s.save(a.out); print(a.out, s.size)


def ocr_win(a):
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(); fs = sorted(glob.glob(os.path.join(a.dir, "f_*.jpg"))); x0, y0, x1, y1 = (int(v) for v in a.box.split(","))
    vals = {}
    for i in range(int(a.start * a.fps), len(fs), a.every):
        r, _ = ocr(np.asarray(Image.open(fs[i]).convert("RGB"))[y0:y1, x0:x1])
        m = re.search(r"\$\s*([\d,]+\.\d\d)", " ".join(x[1] for x in r) if r else "")
        vals[i] = float(m.group(1).replace(",", "")) if m else None
    ev = []
    for i, v in vals.items():
        if v and v > 0:
            if not ev or i - ev[-1]["end"] > 40: ev.append({"start": i, "end": i, "max": v})
            else: ev[-1]["end"] = i; ev[-1]["max"] = max(ev[-1]["max"], v)
    for e in ev: print(f"win at {e['start'] / a.fps:6.1f}s  lasts {(e['end'] - e['start']) / a.fps:5.1f}s  max {e['max']}")
    json.dump(ev, open(a.json, "w")) if a.json else None


def cycle(a):
    fs = sorted(glob.glob(os.path.join(a.dir, "f_*.jpg"))); log = json.load(open(a.spins))
    cols = [tuple(int(v) for v in c.split("-")) for c in a.cols.split(",")]; y0, y1 = (int(v) for v in a.y.split(","))
    xmin = min(c[0] for c in cols); xmax = max(c[1] for c in cols)
    def feat(i):
        g = np.asarray(Image.open(fs[i]).convert("L").crop((xmin, y0, xmax, y1)).reduce(4), dtype=np.float32)
        return g.mean(), [g[:, (c0 - xmin) // 4:(c1 - xmin) // 4].mean() for c0, c1 in cols]
    out = []
    for e in log[1:]:
        p = e["t"] + a.offset; lo, hi = int((p - 1.0) * a.fps), int((p + 4.5) * a.fps)
        if hi >= len(fs): break
        F = [feat(i) for i in range(lo, hi)]; br = np.array([f[0] for f in F]); C = np.array([f[1] for f in F]); base = np.median(br[:8])
        if base - br.min() < 4: continue
        ke = int(np.argmin(br)); pre = [k for k in range(ke) if abs(br[k] - base) < 1.0]
        if not pre: continue
        kx = max(pre); on = []
        for ci in range(len(cols)):
            ks = [k for k in range(ke, len(br)) if C[k, ci] > C[ke][ci] + 5]; on.append(ks[0] if ks else None)
        ks = [k for k in range(ke + 3, len(br)) if abs(br[k] - base) < 1.5]
        if None in on or not ks: continue
        out.append(dict(exit_to_empty=(ke - kx) / a.fps, empty_to_first=(on[0] - ke) / a.fps, stagger=list(np.diff(on) / a.fps), first_to_settle=(ks[0] - on[0]) / a.fps, total=(ks[0] - kx) / a.fps))
    print(len(out), "rounds with a clear exit, empty beat and entry")
    for k in ("exit_to_empty", "empty_to_first", "first_to_settle", "total"):
        v = np.array([o[k] for o in out]); print(f"{k:16} median {np.median(v):.2f}s  p10 {np.percentile(v, 10):.2f}  p90 {np.percentile(v, 90):.2f}")
    st = np.array([o["stagger"] for o in out]); print("column entry onset gaps (s), median per neighbouring pair:", np.median(st, axis=0).round(2).tolist(), "(noisy; confirm on a montage)")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("frames"); p.add_argument("video"); p.add_argument("out"); p.add_argument("--fps", type=int, default=25); p.add_argument("--width", type=int, default=1280); p.set_defaults(f=frames)
    p = sub.add_parser("montage"); p.add_argument("dir"); p.add_argument("t0", type=float); p.add_argument("step", type=int); p.add_argument("n", type=int); p.add_argument("out")
    p.add_argument("--cols", type=int, default=6); p.add_argument("--crop"); p.add_argument("--scale", type=float, default=0.4); p.add_argument("--fps", type=int, default=25); p.set_defaults(f=montage)
    p = sub.add_parser("ocr-win"); p.add_argument("dir"); p.add_argument("--box", required=True); p.add_argument("--from", dest="start", type=float, default=0); p.add_argument("--every", type=int, default=5)
    p.add_argument("--fps", type=int, default=25); p.add_argument("--json"); p.set_defaults(f=ocr_win)
    p = sub.add_parser("cycle"); p.add_argument("dir"); p.add_argument("spins"); p.add_argument("--cols", required=True); p.add_argument("--y", required=True); p.add_argument("--offset", type=float, default=0.67); p.add_argument("--fps", type=int, default=25); p.set_defaults(f=cycle)
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
