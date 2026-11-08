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
             # a part that must stay seamless between a swaying and a planted bone (skirt and legs between hip and feet):
             #   {"name": "skirt", "bone": "hem", "catch_all": true,
             #    "soft": {"top": "hip", "mid": "hem", "bottom": "feet", "y_top": 430, "y_bottom": 840, "cols": 8, "rows": 16}}
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
    "hem":    dict(rot=1.3, phase=-1.6),
    "flap":   dict(rot=2.6, phase=-1.8),
    "cape":   dict(rot=2.0, phase=-1.9),
    "tail":   dict(rot=2.5, phase=-2.2),
    "feet":   dict(),
}


# Spine 4.2 physics constraint presets (rotate-mode secondary motion). The constraint reacts to the movement of its
# parent bones (inertia) and springs back (strength, damping); wind adds a steady breeze. Tune on the preview.
PHYSICS = {
    "hair":  dict(rotate=1, inertia=0.70, strength=30, damping=0.88, mass=1.1, wind=0.0, gravity=0.0, mix=1),
    "cloth": dict(rotate=1, inertia=0.70, strength=38, damping=0.86, mass=1.4, wind=0.0, gravity=0.0, mix=1),
    "tail":  dict(rotate=1, inertia=0.70, strength=28, damping=0.88, mass=1.3, wind=0.0, gravity=0.0, mix=1),
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


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def chain_weights(y, chain, x=None, pivot=None):
    """Weights of a bone chain (list of {"bone","y"}) for a vertex. With x and pivot given, the vertex is projected onto the
    chain's own polyline (bone pivots), so the weight bands run PERPENDICULAR to the strand or flap instead of horizontally;
    that keeps neighbouring weights aligned with the bending direction and avoids shear. Without them: bands by height."""
    if x is not None and pivot is not None and all(c["bone"] in pivot for c in chain):
        P = [np.array(pivot[c["bone"]], float) for c in chain]; v = np.array([x, y], float)
        best = None
        for i in range(len(P) - 1):
            d = P[i + 1] - P[i]; L2 = float(d @ d)
            t = float((v - P[i]) @ d) / L2 if L2 > 0 else 0.0
            tc = min(1.0, max(0.0, t)); dist = float(np.linalg.norm(v - (P[i] + d * tc)))
            # prefer the segment whose projection is inside [0, 1]; ties by distance
            score = dist + (0 if 0 <= t <= 1 else 1e3)
            if best is None or score < best[0]: best = (score, i, t)
        _, i, t = best
        if i == 0 and t < 0: return {chain[0]["bone"]: 1.0}
        if i == len(P) - 2 and t > 1: return {chain[-1]["bone"]: 1.0}
        t = smoothstep(0.0, 1.0, min(1.0, max(0.0, t)))
        return {chain[i]["bone"]: 1 - t, chain[i + 1]["bone"]: t}
    ys = [float(c["y"]) for c in chain]
    if y <= ys[0]: return {chain[0]["bone"]: 1.0}
    if y >= ys[-1]: return {chain[-1]["bone"]: 1.0}
    for i in range(len(ys) - 1):
        if ys[i] <= y <= ys[i + 1]:
            t = smoothstep(0.0, 1.0, (y - ys[i]) / (ys[i + 1] - ys[i]))
            return {chain[i]["bone"]: 1 - t, chain[i + 1]["bone"]: t}


def soft_mesh(box, cfg, sk, pivot, bone_index, wrot):
    """Weighted mesh for a part that must stay continuous while several bones move differently.
    Base weighting by image height, either
      top / mid / bottom bones with y_top and y_bottom (skirt and legs between a swaying hip and planted feet), or
      "chain": [{"bone": b1, "y": y1}, {"bone": b2, "y": y2}, ...] (hair strand, tail, long cloth hanging from b1).
    Optional "zones": [{"x": [x0, x1], "falloff": 30, "chain": [...]}] blend a bone chain into a horizontal region
    of the base weighting (a cloth flap or a ribbon on the side of a skirt); the blend ramps in between the
    first two chain joints so the top of the flap stays attached."""
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    cols, rows = int(cfg.get("cols", 8)), int(cfg.get("rows", 16))
    xs = np.linspace(x0, x1, cols + 1); ys = np.linspace(y0, y1, rows + 1)
    grid, verts = {}, []
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
    def base(y, x_=None):
        if "chain" in cfg:
            return chain_weights(y, cfg["chain"], x_, pivot)
        top, mid, bot = cfg["top"], cfg.get("mid"), cfg["bottom"]
        yt, yb = float(cfg["y_top"]), float(cfg["y_bottom"])
        t = (y - yt) / (yb - yt)
        w_bot = smoothstep(0.55, 1.0, t) if mid else smoothstep(0.0, 1.0, t)
        w_top = 1 - smoothstep(0.0, 0.5, t) if mid else 1 - w_bot
        ws = {top: w_top, bot: w_bot}
        if mid: ws[mid] = max(0.0, 1 - w_top - w_bot)
        return ws
    out, uvs = [], []
    for (x, y) in verts:
        ws = dict(base(y, x))
        for z in cfg.get("zones", []):
            zx0, zx1, fo = z["x"][0], z["x"][1], float(z.get("falloff", 30))
            zw = min(smoothstep(zx0 - fo, zx0, x), 1 - smoothstep(zx1, zx1 + fo, x))
            ch = z["chain"]
            if len(ch) > 1 and all(c["bone"] in pivot for c in ch[:2]):
                p0, p1 = np.array(pivot[ch[0]["bone"]], float), np.array(pivot[ch[1]["bone"]], float); dd = p1 - p0
                ramp = smoothstep(0.0, 1.0, float((np.array([x, y]) - p0) @ dd) / max(float(dd @ dd), 1e-6))
            else:
                ramp = smoothstep(float(ch[0]["y"]), float(ch[1]["y"]), y) if len(ch) > 1 else 1.0
            amt = zw * ramp
            if "y_end" in z:                    # fade the blend out below the end of the cloth (do not drag legs or feet)
                amt *= 1 - smoothstep(float(z["y_end"]) - 30, float(z["y_end"]), y)
            if amt > 0:
                cw = chain_weights(y, ch, x, pivot)
                ws = {k: v * (1 - amt) for k, v in ws.items()}
                for k, v in cw.items(): ws[k] = ws.get(k, 0.0) + v * amt
        ws = {k: v for k, v in ws.items() if v > 0.001}
        tot = sum(ws.values()); ws = {k: v / tot for k, v in ws.items()}
        wx, wy = sk((x, y))
        out.append(len(ws))
        for b, wt in ws.items():
            bx, by = sk(pivot[b]); c_, s_ = math.cos(math.radians(-wrot[b])), math.sin(math.radians(-wrot[b]))
            dx_, dy_ = wx - bx, wy - by                      # vertex in the bone's own (rotated) frame
            out += [bone_index[b], round(c_ * dx_ - s_ * dy_, 3), round(s_ * dx_ + c_ * dy_, 3), round(wt, 5)]
        uvs += [round((x - x0) / w, 6), round((y - y0) / h, 6)]
    return {"type": "mesh", "uvs": uvs, "triangles": tris, "vertices": out, "hull": hull, "width": w, "height": h}


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
    ap.add_argument("--wind", type=float, default=0.0, help="extra steady wind added to every physics constraint (tune on the preview)")
    ap.add_argument("--sway", type=float, default=0.45, help="amplitude of the oscillating breeze keyed on every physics constraint in `idle` (0 = off)")
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
    # World rotation of every bone (degrees, y up). Chain bones (physics or "orient": true) point along their chain, toward
    # the first child, because Spine's physics deflects a bone only when it moves PERPENDICULAR to the bone's own axis: a
    # hair bone left pointing +x while the hair hangs down would barely react. The last bone of a chain keeps its
    # parent's direction (or an explicit "angle"). Other bones stay at 0 so the rest of the rig is unchanged.
    by_name0 = {b["name"]: b for b in bones}
    wrot = {"root": 0.0}
    for b in bones:
        kids = [c for c in bones if c["parent"] == b["name"]]
        if b.get("physics") or b.get("orient"):
            if "angle" in b: wrot[b["name"]] = float(b["angle"])
            elif kids:
                dx = pivot[kids[0]["name"]][0] - pivot[b["name"]][0]; dy = -(pivot[kids[0]["name"]][1] - pivot[b["name"]][1])
                wrot[b["name"]] = math.degrees(math.atan2(dy, dx))
            else:
                wrot[b["name"]] = wrot.get(b["parent"], 0.0)
        else:
            wrot[b["name"]] = 0.0
    def rot(vx, vy, deg):                                # rotate a vector by deg (counter-clockwise, y up)
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg)); return (c * vx - s * vy, s * vx + c * vy)
    spine_bones = [{"name": "root"}]
    for b in bones:
        px, py = sk(pivot[b["parent"]]); bx, by = sk(pivot[b["name"]])
        lx, ly = rot(bx - px, by - py, -wrot[b["parent"]])          # position in the parent's rotated frame
        kids = [c for c in bones if c["parent"] == b["name"]]
        ln = math.hypot(pivot[kids[0]["name"]][0] - pivot[b["name"]][0], pivot[kids[0]["name"]][1] - pivot[b["name"]][1]) if kids else float(b.get("length", 60))
        e = {"name": b["name"], "parent": b["parent"], "x": round(lx, 3), "y": round(ly, 3), "length": round(ln, 2)}
        if wrot[b["name"]] - wrot[b["parent"]]: e["rotation"] = round(wrot[b["name"]] - wrot[b["parent"]], 4)
        spine_bones.append(e)

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
        tiles.append(dict(name=p["name"], img=Image.fromarray(tile, "RGBA"), box=(x0, y0, x1, y1), bone=p["bone"], soft=p.get("soft")))
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
        if t["soft"]:
            bone_index = {n: i for i, n in enumerate(names)}
            atts[t["name"]] = {t["name"]: soft_mesh(t["box"], t["soft"], sk, pivot, bone_index, wrot)}
        else:
            rx_, ry_ = rot(sx - bx, sy - by, -wrot[t["bone"]])
            att = {"x": round(rx_, 3), "y": round(ry_, 3), "width": x1 - x0, "height": y1 - y0}
            if wrot[t["bone"]]: att["rotation"] = round(-wrot[t["bone"]], 4)   # keep the image upright on a rotated bone
            atts[t["name"]] = {t["name"]: att}
    page.save(os.path.join(a.out, a.name + ".png"))

    # ---------------- animations
    s = H / 600.0 * a.amp
    ov_idle = spec.get("idle", {})
    P, N = 3.2, 16
    idle = {"bones": {}}
    physics = []
    for b in bones:
        if b.get("physics"):
            cfg = dict(PHYSICS[b["physics"]] if isinstance(b["physics"], str) else {**PHYSICS["hair"], **b["physics"]})
            if isinstance(b["physics"], str) and "physics_override" in b: cfg.update(b["physics_override"])
            cfg["wind"] = cfg.get("wind", 0.0) + a.wind * (1.0 if cfg.get("wind", 0) >= 0 else -1.0)
            # `order` must be unique across all constraints of the skeleton: Spine's update cache looks constraints up by order,
            # so with every order = 0 only ONE physics constraint is ever active (found by rig_audit.py).
            physics.append({"name": b["name"] + "_phys", "bone": b["name"], "order": len(physics), **cfg})
    pbones = {p["bone"] for p in physics}
    by_name = {b["name"]: b for b in bones}
    def depth_of(n):                                 # how many physics bones above this one in its chain
        d = 0
        while by_name[n]["parent"] in by_name and by_name[by_name[n]["parent"]].get("physics"):
            n = by_name[n]["parent"]; d += 1
        return d
    for b in bones:
        q = idle_params(b["name"], ov_idle)
        if not q: continue
        if b["name"] in pbones and not b.get("keyed"):   # physics-driven bones are not keyed (a keyed sine looks mechanical);
            continue                                     # the breeze (wind timeline) and the body motion drive them
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
    # breeze: every physics constraint gets a wind timeline made of two harmonics (so it never looks like one sine), with a
    # different phase per chain, and a small delay along the chain. Amplitude is `--sway` (rotation-physics wind units).
    if physics and a.sway > 0:
        idle["physics"] = {}
        for p in physics:
            nm = p["bone"]; depth = depth_of(nm)
            kind = by_name[nm]["physics"] if isinstance(by_name[nm]["physics"], str) else "hair"
            amp = a.sway * (1.0 if kind == "hair" else 0.8)
            chain_phase = 0.0 if nm.startswith("hair") else (1.3 if nm.endswith("R1") or "R" in nm[-2:] else 2.2)
            ph = chain_phase - 0.35 * depth
            idle["physics"][p["name"]] = {"wind": [{"time": t, "value": round(p["wind"] + amp * (math.sin(x + ph) + 0.4 * math.sin(2 * x + 1.7 * ph + 0.6)), 3)} for t, x in smooth_keys(P, N)]}
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
        elif n in pbones:
            continue
        elif n.startswith(("head", "hem", "hair", "arm", "forearm", "spear", "weapon", "dragon", "pet", "skirt", "cape", "tail")):
            amp = {"head": 5, "hem": -2.5, "hair": -9, "arm": 7, "forearm": 9, "spear": 3, "weapon": 3, "dragon": 8, "pet": 8, "skirt": -6, "cape": -9, "tail": -9}
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
            "bones": spine_bones, "slots": slots, **({"physics": physics} if physics else {}), "skins": [{"name": "default", "attachments": atts}],
            "animations": {"idle": idle, "cheer": cheer, "joint_test": jt}}
    json.dump(skel, open(os.path.join(a.out, a.name + ".json"), "w"))
    open(os.path.join(a.out, a.name + ".atlas"), "w").write(atlas)
    print(f"wrote {a.out}/{a.name}.json/.atlas/.png: {len(tiles)} parts, {len(bones)} bones, atlas {page.width}x{page.height}, animations idle, cheer")


if __name__ == "__main__":
    main()
