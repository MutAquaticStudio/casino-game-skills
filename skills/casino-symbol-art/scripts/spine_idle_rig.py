#!/usr/bin/env python3
"""Build a Spine (4.2 JSON) idle/cheer rig for a mascot from ONE cut-out image. No Spine editor needed.

What it makes: a single weighted mesh over the character, five bones (hip, chest, head, skirt, feet),
an `idle` loop (breathing, head bob and tilt, weight shift, hem sway) and a `cheer` one-shot
(hop, squash and stretch). Output files can be loaded by the official Spine runtimes (spine-pixi-v8
for PixiJS 8) and are validated here with the official spine-core runtime (see spine_preview.mjs).

What it cannot make: limb movement, blinking, mouth or eye changes, anything that needs separate
body parts. For those the character must be generated or painted as separate layers (head, eyes,
arms, hair, tail...) and rigged by hand in Spine, see references/mascot-animation.md.

Usage:
  python3 spine_idle_rig.py character.png --out rig/ --name mascot [--cols 10 --rows 16]
        [--neck 0.16 --chest 0.40 --hip 0.55] [--amp 1.0] [--key "#FF00FF"]
Writes rig/<name>.json, rig/<name>.atlas, rig/<name>.png (cropped, key colour removed).
Spine runtimes are licensed by Esoteric Software; shipping a game with them needs a Spine licence.
"""
import argparse, json, math, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def key_out(im, key):
    a = np.asarray(im.convert("RGBA")).astype(np.int32)
    if key:
        kr, kg, kb = int(key[1:3], 16), int(key[3:5], 16), int(key[5:7], 16)
        d = np.abs(a[..., 0] - kr) + np.abs(a[..., 1] - kg) + np.abs(a[..., 2] - kb)
        # strict key: close to the key colour only, then a thin halo clean-up on pinkish pixels
        m = d < 120
        halo = ndi.binary_dilation(m, iterations=2) & (a[..., 0] > 150) & (a[..., 2] > 120) & (a[..., 1] < 150) \
            & (a[..., 0] - a[..., 1] > 70) & (a[..., 2] - a[..., 1] > 50)
        a[..., 3] = np.where(m | halo, 0, a[..., 3])
    out = Image.fromarray(a.astype(np.uint8), "RGBA")
    bb = out.getchannel("A").point(lambda v: 255 if v > 10 else 0).getbbox()
    return out.crop(bb)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def build(im, name, cols, rows, neck, chest, hip, amp):
    W, H = im.size
    # skeleton space: origin bottom centre, y up
    def sk(x, y): return (x - W / 2.0, H - y)
    bones_world = {"root": (0, 0), "hip": sk(W / 2, hip * H), "chest": sk(W / 2, chest * H),
                   "head": sk(W / 2, neck * H), "skirt": sk(W / 2, hip * H), "feet": sk(W / 2, 0.95 * H)}
    parent = {"hip": "root", "chest": "hip", "head": "chest", "skirt": "hip", "feet": "root"}
    order = ["root", "hip", "chest", "head", "skirt", "feet"]
    idx = {b: i for i, b in enumerate(order)}
    bones = [{"name": "root"}]
    for b in order[1:]:
        px, py = bones_world[parent[b]]; bx, by = bones_world[b]
        bones.append({"name": b, "parent": parent[b], "x": round(bx - px, 3), "y": round(by - py, 3), "length": 40})

    # vertices: perimeter first (hull), then interior
    xs = np.linspace(0, W, cols + 1); ys = np.linspace(0, H, rows + 1)
    grid = {}
    verts = []
    def add(i, j):
        grid[(i, j)] = len(verts); verts.append((xs[i], ys[j]))
    for i in range(cols + 1): add(i, 0)
    for j in range(1, rows + 1): add(cols, j)
    for i in range(cols - 1, -1, -1): add(i, rows)
    for j in range(rows - 1, 0, -1): add(0, j)
    hull = len(verts)
    for j in range(1, rows):
        for i in range(1, cols): add(i, j)
    tris = []
    for j in range(rows):
        for i in range(cols):
            a, b, c, d = grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]
            tris += [a, b, c, a, c, d]

    out_vertices, uvs = [], []
    for (x, y) in verts:
        fy = y / H
        head_w = 1 - smoothstep(neck - 0.04, neck + 0.04, fy)
        skirt_w = smoothstep(hip - 0.04, hip + 0.12, fy)
        chest_w = max(0.0, 1 - head_w - skirt_w)
        feet_w = smoothstep(0.84, 0.95, fy)          # feet stay planted during idle (own bone, hops in cheer)
        ws = {"head": head_w * (1 - feet_w), "chest": chest_w * (1 - feet_w), "skirt": skirt_w * (1 - feet_w), "feet": feet_w}
        ws = {k: v for k, v in ws.items() if v > 0.001}
        tot = sum(ws.values()); ws = {k: v / tot for k, v in ws.items()}
        wx, wy = sk(x, y)
        out_vertices.append(len(ws))
        for b, w in ws.items():
            bx, by = bones_world[b]
            out_vertices += [idx[b], round(wx - bx, 3), round(wy - by, 3), round(w, 5)]
        uvs += [round(x / W, 6), round(y / H, 6)]

    # ---- animations (all offsets are small, authored for a ~600 px tall character, scaled by H)
    s = H / 600.0 * amp
    def sine(period, n_keys, f):
        ks = []
        for k in range(n_keys + 1):
            t = period * k / n_keys
            ks.append((round(t, 4), f(2 * math.pi * k / n_keys)))
        return ks
    P = 3.2; N = 16
    idle = {"bones": {
        "hip": {"translate": [{"time": t, "x": round(1.6 * s * math.sin(a), 3), "y": round(-1.2 * s * (1 - math.cos(a)) / 2, 3)} for t, a in sine(P, N, lambda a: a)],
                "rotate": [{"time": t, "value": round(0.5 * amp * math.sin(a), 3)} for t, a in sine(P, N, lambda a: a)]},
        "chest": {"scale": [{"time": t, "x": round(1 - 0.006 * amp * math.sin(a), 5), "y": round(1 + 0.014 * amp * math.sin(a), 5)} for t, a in sine(P, N, lambda a: a - math.pi / 2)],
                  "rotate": [{"time": t, "value": round(0.7 * amp * math.sin(a), 3)} for t, a in sine(P, N, lambda a: a - 0.6)]},
        "head": {"rotate": [{"time": t, "value": round(1.5 * amp * math.sin(a), 3)} for t, a in sine(P, N, lambda a: a - 1.1)],
                 "translate": [{"time": t, "x": 0, "y": round(1.4 * s * math.sin(a), 3)} for t, a in sine(P, N, lambda a: a - 0.8)]},
        "skirt": {"rotate": [{"time": t, "value": round(1.9 * amp * math.sin(a), 3)} for t, a in sine(P, N, lambda a: a - 1.6)]},
    }}
    # cheer: hop with squash and stretch, head tilt, hem flare; returns to setup pose at the end
    def env(t, T): return math.sin(math.pi * min(1.0, t / T)) ** 2
    T = 1.4; ks = [round(T * k / 14, 4) for k in range(15)]
    cheer = {"bones": {
        "hip": {"translate": [{"time": t, "x": 0, "y": round(22 * s * env(t, T), 3)} for t in ks]},
        "chest": {"scale": [{"time": t, "x": round(1 - 0.03 * env(t, T) * math.cos(6 * t), 5), "y": round(1 + 0.05 * env(t, T) * math.cos(6 * t), 5)} for t in ks],
                  "rotate": [{"time": t, "value": round(-2.5 * env(t, T) * math.sin(5 * t), 3)} for t in ks]},
        "head": {"rotate": [{"time": t, "value": round(5 * env(t, T) * math.sin(5 * t + 0.6), 3)} for t in ks]},
        "skirt": {"rotate": [{"time": t, "value": round(-6 * env(t, T) * math.sin(5 * t - 0.4), 3)} for t in ks]},
        "feet": {"translate": [{"time": t, "x": 0, "y": round(22 * s * env(t, T), 3)} for t in ks]},
    }}
    skel = {"skeleton": {"hash": "", "spine": "4.2.00", "x": -W / 2, "y": 0, "width": W, "height": H, "images": "", "audio": ""},
            "bones": bones, "slots": [{"name": "character", "bone": "root", "attachment": "character"}],
            "skins": [{"name": "default", "attachments": {"character": {"character": {
                "type": "mesh", "uvs": uvs, "triangles": tris, "vertices": out_vertices, "hull": hull, "width": W, "height": H}}}}],
            "animations": {"idle": idle, "cheer": cheer}}
    atlas = f"{name}.png\nsize:{W},{H}\nfilter:Linear,Linear\npma:false\ncharacter\nbounds:0,0,{W},{H}\n"
    return skel, atlas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image"); ap.add_argument("--out", default="rig"); ap.add_argument("--name", default="mascot")
    ap.add_argument("--cols", type=int, default=10); ap.add_argument("--rows", type=int, default=16)
    ap.add_argument("--neck", type=float, default=0.16, help="neck height as fraction from the top (head pivot)")
    ap.add_argument("--chest", type=float, default=0.40, help="chest pivot, fraction from the top")
    ap.add_argument("--hip", type=float, default=0.55, help="hip and hem pivot, fraction from the top")
    ap.add_argument("--amp", type=float, default=0.7, help="animation strength multiplier")
    ap.add_argument("--key", default=None, help='key colour to remove, e.g. "#FF00FF"; omit if already transparent')
    ap.add_argument("--max-height", type=int, default=1024)
    a = ap.parse_args()
    im = key_out(Image.open(a.image), a.key)
    if im.height > a.max_height:
        im = im.resize((int(im.width * a.max_height / im.height), a.max_height), Image.LANCZOS)
    os.makedirs(a.out, exist_ok=True)
    skel, atlas = build(im, a.name, a.cols, a.rows, a.neck, a.chest, a.hip, a.amp)
    im.save(os.path.join(a.out, a.name + ".png"))
    json.dump(skel, open(os.path.join(a.out, a.name + ".json"), "w"))
    open(os.path.join(a.out, a.name + ".atlas"), "w").write(atlas)
    print(f"wrote {a.out}/{a.name}.json/.atlas/.png  ({im.width}x{im.height}, {len(skel['skins'][0]['attachments']['character']['character']['uvs']) // 2} vertices, animations: idle, cheer)")


if __name__ == "__main__":
    main()
