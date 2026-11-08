#!/usr/bin/env python3
"""Render a rig (spine_idle_rig.py or spine_parts_rig.py) to a GIF and a key-frame strip, using the official
spine-core runtime for the deformation (via spine_preview.mjs) and OpenCV for drawing.

Usage (run inside a folder where `npm i @esotericsoftware/spine-core@4.2` was done):
  python3 spine_preview.py rig/mascot --anim idle --duration 3.2 --frames 32 --out rig/preview
Needs: node, opencv-python-headless, pillow, numpy.
Prints per-animation numbers: largest vertex displacement, feet travel, and a crack check (new thin see-through
seams that open between parts during motion, compared with the pose at rest).
"""
import argparse, json, os, re, subprocess, sys
import cv2, numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def run(base, anim, dur, n):
    r = subprocess.run(["node", os.path.join(HERE, "spine_preview.mjs"), base + ".json", base + ".atlas", anim, str(dur), str(n)], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    return json.loads(r.stdout)


def render(atlas_img, data, W, H, pad=60):
    A = atlas_img.shape[:2]
    out = []
    metas = data["slots"]
    for fr in data["frames"]:
        canvas = np.zeros((H + 2 * pad, W + 2 * pad, 4), np.float32)
        for meta, v in zip(metas, fr["slots"]):
            if v is None or meta["type"] == "none":
                continue
            v = np.array(v).reshape(-1, 2); uv = np.array(meta["uvs"]).reshape(-1, 2) * [A[1], A[0]]
            dst = np.stack([v[:, 0] + W / 2 + pad, H - v[:, 1] + pad], 1)
            tris = np.array(meta["triangles"]).reshape(-1, 3)
            layer = np.zeros_like(canvas); mask = np.zeros(canvas.shape[:2], np.uint8)
            for t in tris:
                s = uv[t].astype(np.float32); d = dst[t].astype(np.float32)
                x0, y0 = np.floor(d.min(0)).astype(int) - 1; x1, y1 = np.ceil(d.max(0)).astype(int) + 2
                x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, canvas.shape[1]), min(y1, canvas.shape[0])
                if x1 <= x0 or y1 <= y0: continue
                M = cv2.getAffineTransform(s, (d - [x0, y0]).astype(np.float32))
                w = cv2.warpAffine(atlas_img, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
                m = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.fillConvexPoly(m, np.round(d - [x0, y0]).astype(np.int32), 255)
                sel = m > 0
                layer[y0:y1, x0:x1][sel] = w[sel]; mask[y0:y1, x0:x1][sel] = 255
            al = layer[..., 3:4] / 255.0
            ca = canvas[..., 3:4] / 255.0
            outa = al + ca * (1 - al)
            rgb = np.where(outa > 0, (layer[..., :3] * al + canvas[..., :3] * ca * (1 - al)) / np.maximum(outa, 1e-6), 0)
            canvas[..., :3] = rgb; canvas[..., 3:4] = outa * 255
        out.append(canvas.astype(np.uint8))
    return out


def joint_sheet(a):
    sk = json.load(open(a.base + ".json")); W, H = int(sk["skeleton"]["width"]), int(sk["skeleton"]["height"])
    bones = sk["bones"][1:]; nb = len(bones)
    if "joint_test" not in sk["animations"]:
        sys.exit("rig has no joint_test animation (build it with spine_parts_rig.py)")
    world = {"root": (0.0, 0.0)}
    for b in sk["bones"][1:]:
        px, py = world[b["parent"]]; world[b["name"]] = (px + b.get("x", 0), py + b.get("y", 0))
    per = 8; dur = 0.8 * nb
    data = run(a.base, "joint_test", dur, per * nb)
    atlas_img = np.asarray(Image.open(a.base + ".png").convert("RGBA"))
    want = [x for x in a.only.split(",") if x] or [b["name"] for b in bones]
    idxs = [i for i, b in enumerate(bones) if b["name"] in want]
    pick = [i * per + per // 2 for i in idxs]
    bones = [bones[i] for i in idxs]; nb = len(bones)
    data["frames"] = [data["frames"][i] for i in pick]
    frames = render(atlas_img, data, W, H)
    bg = tuple(int(a.bg[i:i + 2], 16) for i in (1, 3, 5)); pad = 60; cols = 5 if nb > 6 else 2; s = a.scale
    from PIL import ImageDraw
    tiles = []
    for b, f in zip(bones, frames):
        im = Image.new("RGBA", (f.shape[1], f.shape[0]), bg + (255,)); im.alpha_composite(Image.fromarray(f, "RGBA")); im = im.convert("RGB")
        d = ImageDraw.Draw(im); x, y = world[b["name"]]; cx, cy = x + W / 2 + pad, H - y + pad
        d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), outline=(255, 255, 0), width=4); d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(255, 255, 0))
        d.text((14, 12), f"{b['name']} (parent {b['parent']}) +18 deg", fill=(255, 255, 0))
        tiles.append(im.resize((int(im.width * s), int(im.height * s))))
    w, h = tiles[0].size; rows = (nb + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), bg)
    for k, t in enumerate(tiles): sheet.paste(t, ((k % cols) * w, (k // cols) * h))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); sheet.save(a.out + "_joints.png"); print("wrote", a.out + "_joints.png", f"({nb} bones)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("--anim", default="idle"); ap.add_argument("--duration", type=float, default=3.2)
    ap.add_argument("--frames", type=int, default=32); ap.add_argument("--out", default="preview"); ap.add_argument("--bg", default="#1b2330")
    ap.add_argument("--only", default="", help="with --joint-sheet: comma-separated bone names to include")
    ap.add_argument("--scale", type=float, default=0.42, help="with --joint-sheet: panel scale")
    ap.add_argument("--joint-sheet", action="store_true", help="render the rig's joint_test animation: one panel per bone at the peak of its 18 degree swing, pivot marked")
    a = ap.parse_args()
    if a.joint_sheet:
        return joint_sheet(a)
    sk = json.load(open(a.base + ".json")); W, H = int(sk["skeleton"]["width"]), int(sk["skeleton"]["height"])
    atlas_img = np.asarray(Image.open(a.base + ".png").convert("RGBA"))
    data = run(a.base, a.anim, a.duration, a.frames)
    pts = [np.array(v).reshape(-1, 2) for f in data["frames"] for v in f["slots"] if v is not None]
    n_s = sum(1 for m in data["slots"] if m["type"] != "none")
    per = [np.stack([np.array(f["slots"][i]).reshape(-1, 2) for f in data["frames"]]) for i, m in enumerate(data["slots"]) if m["type"] != "none"]
    disp = max(float(np.abs(p - p[0]).max()) for p in per)
    foot = [float(np.abs(p - p[0]).max()) for p, m in zip(per, [m for m in data["slots"] if m["type"] != "none"]) if re.search(r"feet|foot", m["name"])]
    print(f"{a.anim}: {len(data['frames'])} frames over {a.duration}s, {n_s} slot(s); largest vertex displacement vs frame 0 = {disp:.1f}px (character {W}x{H}, {100*disp/H:.1f}% of height)"
          + (f"; feet parts max travel = {max(foot):.1f}px" if foot else ""))
    frames = render(atlas_img, data, W, H)
    # crack check: thin see-through seams (transparent pixels with opaque pixels on both sides within ~3 px)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    def cracks(f):
        solid = (f[..., 3] > 20).astype(np.uint8)
        return int(((cv2.morphologyEx(solid, cv2.MORPH_CLOSE, k) > 0) & (solid == 0)).sum())
    base_c = cracks(frames[0]); worst = max(cracks(f) for f in frames) - base_c
    print(f"   crack check: thin see-through seams at rest {base_c}px; worst extra seam pixels during motion {max(worst, 0)}px")
    bg = tuple(int(a.bg[i:i + 2], 16) for i in (1, 3, 5)); ims = []
    for f in frames:
        b = Image.new("RGBA", (f.shape[1], f.shape[0]), bg + (255,)); b.alpha_composite(Image.fromarray(f, "RGBA")); ims.append(b.convert("RGB"))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    ims[0].save(a.out + f"_{a.anim}.gif", save_all=True, append_images=ims[1:], duration=int(a.duration * 1000 / len(ims)), loop=0)
    pick = [0, len(ims) // 4, len(ims) // 2, 3 * len(ims) // 4]; w, h = ims[0].size; s = 0.5
    strip = Image.new("RGB", (int(w * s) * len(pick), int(h * s)), bg)
    for k, i in enumerate(pick): strip.paste(ims[i].resize((int(w * s), int(h * s))), (k * int(w * s), 0))
    strip.save(a.out + f"_{a.anim}_strip.png"); print("wrote", a.out + f"_{a.anim}.gif", a.out + f"_{a.anim}_strip.png")


if __name__ == "__main__":
    main()
