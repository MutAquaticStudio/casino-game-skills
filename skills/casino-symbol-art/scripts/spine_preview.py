#!/usr/bin/env python3
"""Render a rig from spine_idle_rig.py to a GIF and a strip of key frames, using the official
spine-core runtime for the deformation (via spine_preview.mjs) and OpenCV for drawing.

Usage (run inside a folder where `npm i @esotericsoftware/spine-core@4.2` was done):
  python3 spine_preview.py rig/mascot --anim idle --duration 3.2 --frames 32 --out rig/preview
Needs: node, opencv-python-headless, pillow, numpy.
Prints the largest vertex displacement in pixels per animation, so a rig that barely moves (or
tears) shows up as a number, not a judgement.
"""
import argparse, json, os, subprocess, sys
import cv2, numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def run(base, anim, dur, n):
    r = subprocess.run(["node", os.path.join(HERE, "spine_preview.mjs"), base + ".json", base + ".atlas", anim, str(dur), str(n)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    return json.loads(r.stdout)


def render(img, data, W, H, pad=60):
    tris = np.array(data["triangles"]).reshape(-1, 3); uv = np.array(data["uvs"]).reshape(-1, 2) * [W, H]
    frames = []
    for fr in data["frames"]:
        v = np.array(fr["v"]).reshape(-1, 2)
        dst = np.stack([v[:, 0] + W / 2 + pad, H - v[:, 1] + pad], 1)
        canvas = np.zeros((H + 2 * pad, W + 2 * pad, 4), np.uint8)
        for t in tris:
            s = uv[t].astype(np.float32); d = dst[t].astype(np.float32)
            M = cv2.getAffineTransform(s, d)
            warped = cv2.warpAffine(img, M, (canvas.shape[1], canvas.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
            m = np.zeros(canvas.shape[:2], np.uint8); cv2.fillConvexPoly(m, np.round(d).astype(np.int32), 255)
            canvas[m > 0] = warped[m > 0]
        frames.append(canvas)
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("--anim", default="idle"); ap.add_argument("--duration", type=float, default=3.2)
    ap.add_argument("--frames", type=int, default=32); ap.add_argument("--out", default="preview")
    ap.add_argument("--bg", default="#1b2330")
    a = ap.parse_args()
    img = np.asarray(Image.open(a.base + ".png").convert("RGBA")); H, W = img.shape[:2]
    data = run(a.base, a.anim, a.duration, a.frames)
    v0 = np.array(data["frames"][0]["v"]).reshape(-1, 2)
    disp = max(float(np.abs(np.array(f["v"]).reshape(-1, 2) - v0).max()) for f in data["frames"])
    allv = np.stack([np.array(f["v"]).reshape(-1, 2) for f in data["frames"]])
    foot = v0[:, 1] < 0.06 * H                         # vertices in the bottom 6% of the character
    foot_travel = float(np.abs(allv[:, foot] - v0[foot]).max()) if foot.any() else 0.0
    rng = (allv.max(0) - allv.min(0)).max(0)
    print(f"{a.anim}: {len(data['frames'])} frames over {a.duration}s; largest vertex displacement vs frame 0 = {disp:.1f}px "
          f"(character {W}x{H}); max per-vertex travel x={rng[0]:.1f}px y={rng[1]:.1f}px; "
          f"bottom 6% (feet) max travel = {foot_travel:.1f}px")
    frames = render(img, data, W, H)
    bg = tuple(int(a.bg[i:i + 2], 16) for i in (1, 3, 5))
    ims = []
    for f in frames:
        base = Image.new("RGBA", (f.shape[1], f.shape[0]), bg + (255,)); base.alpha_composite(Image.fromarray(f, "RGBA")); ims.append(base.convert("RGB"))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    ims[0].save(a.out + f"_{a.anim}.gif", save_all=True, append_images=ims[1:], duration=int(a.duration * 1000 / len(ims)), loop=0)
    pick = [0, len(ims) // 4, len(ims) // 2, 3 * len(ims) // 4]
    w, h = ims[0].size; s = 0.5
    strip = Image.new("RGB", (int(w * s) * len(pick), int(h * s)), bg)
    for k, i in enumerate(pick): strip.paste(ims[i].resize((int(w * s), int(h * s))), (k * int(w * s), 0))
    strip.save(a.out + f"_{a.anim}_strip.png"); print("wrote", a.out + f"_{a.anim}.gif", a.out + f"_{a.anim}_strip.png")


if __name__ == "__main__":
    main()
