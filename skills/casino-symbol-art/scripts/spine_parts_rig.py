#!/usr/bin/env python3
"""Multi-bone Spine 4.2 rig from ONE cut-out character image, split into parts by a small spec.

Each part is cut out of the image by polygons, attached to its own bone, and animated with
follow-through (child bones lag their parents), so the head, hair, arms, held items and cloth
move independently. Parts are rigid regions (Spine region attachments), which suits subtle idle
motion; every part is extended under its neighbours by `overlap` px so small rotations never open a gap.

Spec (JSON, coordinates are pixels of the image, y down):
{
  "image": "hero.png",                     # RGBA cut-out (alpha = character)
  "overlap": 8,                            # px each part extends beneath neighbours
  "bones": [ {"name": "hip",  "parent": "root", "pivot": [390, 400]}, ... ],
  "parts": [ {"name": "torso", "bone": "chest", "polygons": [[[x,y], ...]]},     # back to front order
             {"name": "spear", "bone": "spear", "capsules": [{"p0": [0,905], "p1": [330,380], "r": 30}]},   # also "circles"
             {"name": "skirt", "bone": "skirt", "catch_all": true} ],             # gets all unclaimed pixels
  "idle":  { "head": {"rot": 1.2, "phase": -1.1, "ty": 1.2} }                     # optional overrides
}
Draw order is the order of `parts` (first = back). A pixel belongs to the LAST part whose polygon contains it;
unclaimed pixels go to the part with "catch_all": true (exactly one).

Usage: python3 spine_parts_rig.py spec.json --out rig --name mascot [--amp 0.7] [--debug]
Writes rig/<name>.json, .atlas, .png and (with --debug) rig/<name>_parts.png (colour-coded ownership).
Check it with spine_preview.py. Spine runtimes need an Esoteric Software licence for shipped games.
"""
import argparse, json, math, os
import cv2
import numpy as np
from PIL import Image

# Default idle motion per bone (rotation in degrees, scale-y amount, translate in px at 600 px height,
# phase in radians: more negative = lags more = follow-through). Matched by bone name prefix.
DEFAULT_IDLE = {
    "hip":    dict(rot=0.4, tx=1.2, ty=-1.0, phase=0.0),
    "chest":  dict(rot=0.6, sy=0.013, sx=-0.005, phase=-0.5),
    "head":   dict(rot=1.2, ty=1.2, phase=-1.1),
    "hair":   dict(rot=2.2, phase=-2.0),
    "arm":    dict(rot=0.9, phase=-1.4),
    "forearm": dict(rot=1.4, phase=-2.1),
    "spear":  dict(rot=0.8, phase=-2.0),
    "weapon": dict(rot=0.8, phase=-2.0),
    "dragon": dict(rot=1.8, ty=4.0, phase=-0.9),
    "pet":    dict(rot=1.8, ty=4.0, phase=-0.9),
    "skirt":  dict(rot=1.3, phase=-1.6),
    "cape":   dict(rot=2.0, phase=-1.9),
    "tail":   dict(rot=2.5, phase=-2.2),
    "feet":   dict(),
}


def idle_params(name, overrides):
    if name in overrides:
        return overrides[name]
    for k, v in DEFAULT_IDLE.items():
        if name.startswith(k):
            return v
    return dict(rot=0.5, phase=-1.0)


def smooth_keys(period, n):
    return [(round(period * k / n, 4), 2 * math.pi * k / n) for k in range(n + 1)]


def pack(tiles, pad=2, width=2048):
    order = sorted(tiles, key=lambda t: -t["img"].height)
    x = y = row_h = 0
    for t in order:
        w, h = t["img"].width + pad, t["img"].height + pad
        if x + w > width:
            x, y, row_h = 0, y + row_h, 0
        t["ax"], t["ay"] = x, y
        x += w; row_h = max(row_h, h)
    H = y + row_h
    page_h = 1
    while page_h < H: page_h *= 2
    page = Image.new("RGBA", (width, page_h), (0, 0, 0, 0))
    for t in order:
        page.alpha_composite(t["img"], (t["ax"], t["ay"]))
    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--out", default="rig"); ap.add_argument("--name", default="mascot")
    ap.add_argument("--amp", type=float, default=0.5); ap.add_argument("--debug", action="store_true")
    ap.add_argument("--no-adopt", action="store_true", help="keep stray catch-all pieces where they are")
    a = ap.parse_args()
    spec = json.load(open(a.spec)); base = os.path.dirname(os.path.abspath(a.spec))
    im = Image.open(os.path.join(base, spec["image"])).convert("RGBA"); W, H = im.size
    arr = np.asarray(im); alpha = arr[..., 3] > 8
    overlap = int(spec.get("overlap", 8))
    parts = spec["parts"]
    owner = np.full((H, W), -1, np.int16)
    catch = [i for i, p in enumerate(parts) if p.get("catch_all")]
    if len(catch) != 1:
        raise SystemExit("exactly one part must have catch_all: true")
    for i, p in enumerate(parts):
        if p.get("catch_all"): continue
        m = np.zeros((H, W), np.uint8)
        for poly in p.get("polygons", []):
            cv2.fillPoly(m, [np.round(np.array(poly)).astype(np.int32)], 255)
        for c in p.get("capsules", []):        # thin long shapes (spear, limb): {"p0": [x,y], "p1": [x,y], "r": radius}
            cv2.line(m, tuple(int(v) for v in c["p0"]), tuple(int(v) for v in c["p1"]), 255, int(2 * c["r"]))
            for e in (c["p0"], c["p1"]):
                cv2.circle(m, tuple(int(v) for v in e), int(c["r"]), 255, -1)
        for c in p.get("circles", []):         # blobs: {"c": [x,y], "r": radius}
            cv2.circle(m, tuple(int(v) for v in c["c"]), int(c["r"]), 255, -1)
        owner[(m > 0)] = i                     # later parts overwrite earlier ones (front wins)
    owner[(owner < 0) & alpha] = catch[0]
    owner[~alpha] = -1
    # stray pieces: parts of the catch-all that are not connected to its main body are almost always fragments of a
    # moving object that a polygon missed (a spear ornament, a hair wisp). Left alone they would stay behind as
    # ghosts, so each is handed to the nearest other part. Disable with --no-adopt.
    n_cc, lab_cc, stats, _ = cv2.connectedComponentsWithStats((owner == catch[0]).astype(np.uint8), connectivity=8)
    comps = sorted(((int(stats[k, cv2.CC_STAT_AREA]), k) for k in range(1, n_cc)), reverse=True)
    adopted = []
    if not a.no_adopt and len(comps) > 1:
        dist = {}
        for i, p in enumerate(parts):
            if i == catch[0]: continue
            mi = (owner == i)
            if mi.any(): dist[i] = cv2.distanceTransform((~mi).astype(np.uint8), cv2.DIST_L2, 3)
        for area, k in comps[1:]:
            if area < 12: continue
            sel = lab_cc == k
            best = min(dist, key=lambda i: float(dist[i][sel].min()))
            owner[sel] = best; adopted.append((area, parts[best]["name"]))
    if adopted:
        print(f"adopted {len(adopted)} stray piece(s) from '{parts[catch[0]]['name']}' into nearest parts: "
              + ", ".join(f"{n} +{ar}px" for ar, n in adopted[:8]) + (" ..." if len(adopted) > 8 else ""))
    bones = spec["bones"]; names = ["root"] + [b["name"] for b in bones]
    pivot = {"root": (W / 2.0, float(H))}
    for b in bones: pivot[b["name"]] = tuple(b["pivot"])
    def sk(p): return (p[0] - W / 2.0, H - p[1])           # image px -> skeleton space (y up)
    spine_bones = [{"name": "root"}]
    for b in bones:
        px, py = sk(pivot[b["parent"]]); bx, by = sk(pivot[b["name"]])
        spine_bones.append({"name": b["name"], "parent": b["parent"], "x": round(bx - px, 3), "y": round(by - py, 3), "length": 30})

    tiles, slots, atts = [], [], {}
    kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * overlap + 1, 2 * overlap + 1))
    dbg = np.zeros((H, W, 3), np.uint8); rng = np.random.RandomState(3)
    for i, p in enumerate(parts):
        own = (owner == i).astype(np.uint8)
        if own.sum() == 0:
            print(f"warning: part {p['name']} owns no pixels, skipped"); continue
        grown = cv2.dilate(own, kern) > 0
        keep = grown & alpha                                  # own pixels + underlay beneath neighbours
        ys, xs = np.where(keep)
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
        tile = arr[y0:y1, x0:x1].copy(); tile[~keep[y0:y1, x0:x1]] = 0
        tiles.append(dict(name=p["name"], img=Image.fromarray(tile, "RGBA"), box=(x0, y0, x1, y1), bone=p["bone"]))
        if a.debug:
            col = rng.randint(60, 255, 3); dbg[own > 0] = col
    page = pack(tiles)
    os.makedirs(a.out, exist_ok=True)
    if a.debug:
        ov = np.asarray(im.convert("RGB")).astype(np.float32) * 0.45 + dbg.astype(np.float32) * 0.55
        Image.fromarray(ov.astype(np.uint8)).save(os.path.join(a.out, a.name + "_parts.png"))
    atlas = f"{a.name}.png\nsize:{page.width},{page.height}\nfilter:Linear,Linear\npma:false\n"
    for t in tiles:
        atlas += f"{t['name']}\nbounds:{t['ax']},{t['ay']},{t['img'].width},{t['img'].height}\n"
        x0, y0, x1, y1 = t["box"]; cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        bx, by = sk(pivot[t["bone"]]); sx, sy = sk((cx, cy))
        slots.append({"name": t["name"], "bone": t["bone"], "attachment": t["name"]})
        atts[t["name"]] = {t["name"]: {"x": round(sx - bx, 3), "y": round(sy - by, 3), "width": x1 - x0, "height": y1 - y0}}
    page.save(os.path.join(a.out, a.name + ".png"))

    # ---------------- animations
    s = H / 600.0 * a.amp
    ov_idle = spec.get("idle", {})
    P, N = 3.2, 16
    idle = {"bones": {}}
    for b in bones:
        q = idle_params(b["name"], ov_idle)
        if not q: continue
        tl = {}
        ks = smooth_keys(P, N)
        if q.get("rot"): tl["rotate"] = [{"time": t, "value": round(q["rot"] * a.amp * math.sin(ph + q.get("phase", 0)), 3)} for t, ph in ks]
        if q.get("tx") or q.get("ty"):
            tl["translate"] = [{"time": t, "x": round(q.get("tx", 0) * s * math.sin(ph + q.get("phase", 0)), 3),
                                "y": round(q.get("ty", 0) * s * math.sin(ph + q.get("phase", 0)), 3)} for t, ph in ks]
        if q.get("sx") or q.get("sy"):
            tl["scale"] = [{"time": t, "x": round(1 + q.get("sx", 0) * a.amp * math.sin(ph + q.get("phase", 0) - math.pi / 2), 5),
                            "y": round(1 + q.get("sy", 0) * a.amp * math.sin(ph + q.get("phase", 0) - math.pi / 2), 5)} for t, ph in ks]
        if tl: idle["bones"][b["name"]] = tl
    T = 1.4; ks = [round(T * k / 14, 4) for k in range(15)]
    env = lambda t: math.sin(math.pi * min(1.0, t / T)) ** 2
    cheer = {"bones": {}}
    top = [b["name"] for b in bones if b["parent"] == "root"]
    for b in bones:
        n = b["name"]; tl = {}
        if n.startswith("hip") or n.startswith("feet"):
            tl["translate"] = [{"time": t, "x": 0, "y": round(22 * s * env(t), 3)} for t in ks]
        elif n.startswith("chest"):
            tl["scale"] = [{"time": t, "x": round(1 - 0.03 * env(t) * math.cos(6 * t), 5), "y": round(1 + 0.05 * env(t) * math.cos(6 * t), 5)} for t in ks]
        elif n.startswith(("head", "hair", "arm", "forearm", "spear", "weapon", "dragon", "pet", "skirt", "cape", "tail")):
            amp = {"head": 5, "hair": -9, "arm": 7, "forearm": 9, "spear": 3, "weapon": 3, "dragon": 8, "pet": 8, "skirt": -6, "cape": -9, "tail": -9}
            k = next(v for kk, v in amp.items() if n.startswith(kk))
            tl["rotate"] = [{"time": t, "value": round(k * env(t) * math.sin(5 * t + 0.4 * (len(n) % 5)), 3)} for t in ks]
        if tl: cheer["bones"][n] = tl
    # joint test: each bone alone swings 18 degrees and back in its own 0.8 s window; used to prove that every bone
    # rotates at its own joint (see spine_preview.py --joint-sheet). Not for shipping.
    jt = {"bones": {}}
    for i, b in enumerate(bones):
        t0 = i * 0.8
        keys = [{"time": round(t0, 3), "value": 0}, {"time": round(t0 + 0.4, 3), "value": 18}, {"time": round(t0 + 0.8, 3), "value": 0}]
        jt["bones"][b["name"]] = {"rotate": keys}
    skel = {"skeleton": {"hash": "", "spine": "4.2.00", "x": -W / 2, "y": 0, "width": W, "height": H, "images": "", "audio": ""},
            "bones": spine_bones, "slots": slots, "skins": [{"name": "default", "attachments": atts}],
            "animations": {"idle": idle, "cheer": cheer, "joint_test": jt}}
    json.dump(skel, open(os.path.join(a.out, a.name + ".json"), "w"))
    open(os.path.join(a.out, a.name + ".atlas"), "w").write(atlas)
    print(f"wrote {a.out}/{a.name}.json/.atlas/.png: {len(tiles)} parts, {len(bones)} bones, atlas {page.width}x{page.height}, animations idle, cheer")


if __name__ == "__main__":
    main()
