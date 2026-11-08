#!/usr/bin/env python3
"""Measure how far each art asset drifts from the locked style of a set.

Why: image models drift between calls (palette, light direction, outline tone, saturation).
This script makes the drift visible so an agent can reject and regenerate before assets are
composited into a game.

Usage:
  python3 style_check.py art/style.json art/layers/*.png [--anchors a.png b.png] [--json out.json]

style.json fields read (all optional except palette):
  "palette":      ["#0e2a3a", ...]           6-8 hex colours of the set
  "warm_accent":  ["#d9a53a", ...]           colours reserved for value (gold, red, orange)
  "light":        "top-left"                 expected light direction
  "style_check":  {"groups": {"symbol": ["sym_*", "rank_*"], "background": ["backdrop*", "board*"]},
                   "tolerances": {"palette_de": 28, "lightness": 12, "chroma": 14, "warm_share": 0.25, "outline_l": 14},
                   "exempt": {"rank_K.png": ["palette"]}}

Groups: a board is darker than a symbol by design, so lightness, chroma, warm share and outline
are compared only inside a group (glob patterns in style_check.groups; assets matching no group
form their own group). A group needs 3+ members to give a median; smaller groups are judged on the
absolute metrics only (palette distance, light direction). Anchors (--anchors) override the median
of a group with the assets you approved first. A metric outside tolerance is WARN, beyond 1.8x FAIL.

Metrics (all in CIELAB, on pixels where alpha > 10; magenta key pixels are ignored):
  palette_de  mean distance from the asset's dominant colours to the nearest palette colour
  lightness   mean L* vs anchors
  chroma      mean chroma vs anchors
  warm_share  share of pixels that are warm (hue 20-70 deg, chroma > 25): gold/red value colour
  outline_l   mean L* of the 2 px rim of the alpha shape (outline tone); skipped for full-frame art
  light_bias  sign of (top-left minus bottom-right lightness); must match the set
Exit code 1 if any FAIL.
"""
import argparse, fnmatch, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def hex_to_rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def srgb_to_lab(rgb):
    a = np.asarray(rgb, dtype=np.float64) / 255.0
    a = np.where(a > 0.04045, ((a + 0.055) / 1.055) ** 2.4, a / 12.92)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = a @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def load(path):
    im = Image.open(path).convert('RGBA')
    im.thumbnail((384, 384))
    a = np.asarray(im).astype(np.int32)
    R, G, B, A = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    key = (R > 175) & (B > 175) & (G < 115) & (np.abs(R - B) < 60)
    mask = (A > 10) & ~key
    return a[..., :3], mask


def features(path, palette_lab):
    rgb, mask = load(path)
    if mask.sum() < 200:
        return None
    lab = srgb_to_lab(rgb)
    px = lab[mask]
    L, ab = px[:, 0], px[:, 1:]
    chroma = np.hypot(ab[:, 0], ab[:, 1])
    hue = (np.degrees(np.arctan2(ab[:, 1], ab[:, 0])) + 360) % 360
    warm = ((hue > 20) & (hue < 70) & (chroma > 25)).mean()
    # dominant colours via coarse quantisation
    q = (rgb[mask] // 32).astype(np.int32)
    keys = q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2]
    u, inv, cnt = np.unique(keys, return_inverse=True, return_counts=True)
    top = np.argsort(-cnt)[:8]
    cols = np.stack([rgb[mask][inv == t].mean(0) for t in top]); w = cnt[top] / cnt[top].sum()
    dl = srgb_to_lab(cols)
    de = np.sqrt(((dl[:, None, :] - palette_lab[None, :, :]) ** 2).sum(-1)).min(1)
    pal_de = float((de * w).sum())
    # outline tone: 2 px rim of the alpha shape (only meaningful when the shape does not fill the frame)
    fill = mask.mean()
    rim_l = None
    if fill < 0.85:
        rim = mask & ~ndi.binary_erosion(mask, iterations=2)
        if rim.sum() > 50:
            rim_l = float(lab[..., 0][rim].mean())
    h, w_ = mask.shape
    tl = lab[..., 0][: h // 2, : w_ // 2][mask[: h // 2, : w_ // 2]]
    br = lab[..., 0][h // 2:, w_ // 2:][mask[h // 2:, w_ // 2:]]
    bias = float(tl.mean() - br.mean()) if len(tl) > 50 and len(br) > 50 else 0.0
    return dict(palette_de=pal_de, lightness=float(L.mean()), chroma=float(chroma.mean()),
                warm_share=float(warm), outline_l=rim_l, light_bias=bias)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('style'); ap.add_argument('assets', nargs='+')
    ap.add_argument('--anchors', nargs='*'); ap.add_argument('--json')
    args = ap.parse_args()
    st = json.load(open(args.style))
    pal = np.array([hex_to_rgb(c) for c in st['palette'] + st.get('warm_accent', [])])
    pal_lab = srgb_to_lab(pal)
    tol = dict(palette_de=28, lightness=12, chroma=14, warm_share=0.25, outline_l=14)
    tol.update(st.get('style_check', {}).get('tolerances', {}))
    exempt = st.get('style_check', {}).get('exempt', {})
    feats = {p: features(p, pal_lab) for p in args.assets}
    feats = {p: f for p, f in feats.items() if f}
    groups_cfg = st.get('style_check', {}).get('groups', {})
    def group_of(p):
        n = os.path.basename(p)
        for g, pats in groups_cfg.items():
            if any(fnmatch.fnmatch(n, pat) for pat in pats):
                return g
        return 'solo:' + n
    by_group = {}
    for p in feats:
        by_group.setdefault(group_of(p), []).append(p)
    anchor_set = set(args.anchors or [])
    def medians(paths):
        pool = [feats[p] for p in paths if (not anchor_set or p in anchor_set)] or [feats[p] for p in paths]
        m = {k: float(np.median([a[k] for a in pool])) for k in ('lightness', 'chroma', 'warm_share')}
        o = [a['outline_l'] for a in pool if a['outline_l'] is not None]
        m['outline_l'] = float(np.median(o)) if o else None
        return m
    gmed = {g: (medians(ps) if len(ps) >= 3 else None) for g, ps in by_group.items()}
    all_bias = [f['light_bias'] for f in feats.values() if abs(f['light_bias']) > 4]
    set_bias_sign = np.sign(np.median(all_bias)) if all_bias else 0
    rows, fails = [], 0
    for p, f in feats.items():
        name = os.path.basename(p); ex = exempt.get(name, []); res = {}
        g = group_of(p); med = gmed[g]
        def judge(metric, val, ref, tolv, absolute=False):
            if metric in ex:
                return 'exempt'
            if val is None or (ref is None and not absolute):
                return 'skip'
            d = val if absolute else abs(val - ref)
            return 'FAIL' if d > tolv * 1.8 else ('WARN' if d > tolv else 'ok')
        res['palette'] = judge('palette', f['palette_de'], None, tol['palette_de'], absolute=True)
        res['lightness'] = judge('lightness', f['lightness'], med and med['lightness'], tol['lightness'])
        res['chroma'] = judge('chroma', f['chroma'], med and med['chroma'], tol['chroma'])
        res['warm'] = judge('warm', f['warm_share'], med and med['warm_share'], tol['warm_share'])
        res['outline'] = judge('outline', f['outline_l'], med and med['outline_l'], tol['outline_l'])
        lb = np.sign(f['light_bias']) if abs(f['light_bias']) > 4 else 0
        res['light'] = 'exempt' if 'light' in ex else ('WARN' if (lb != 0 and set_bias_sign != 0 and lb != set_bias_sign) else 'ok')
        worst = 'FAIL' if 'FAIL' in res.values() else ('WARN' if 'WARN' in res.values() else 'ok')
        fails += worst == 'FAIL'
        rows.append((name, f, res, worst))
    hdr = f"{'asset':26} {'palΔE':>6} {'L*':>5} {'chroma':>6} {'warm':>5} {'rimL':>5} {'light':>6}  verdict"
    print(hdr); print('-' * len(hdr))
    for name, f, res, worst in rows:
        flag = ' '.join(f"{k}:{v}" for k, v in res.items() if v in ('WARN', 'FAIL'))
        rim = f"{f['outline_l']:.0f}" if f['outline_l'] is not None else '-'
        print(f"{name[:26]:26} {f['palette_de']:6.1f} {f['lightness']:5.0f} {f['chroma']:6.0f} {f['warm_share']:5.2f} {rim:>5} {f['light_bias']:6.1f}  {worst} {flag}")
    print("\ngroups: " + "; ".join(f"{g} ({len(ps)})" + ("" if gmed[g] else " absolute only") for g, ps in by_group.items())
          + f"; light bias sign={int(set_bias_sign)}")
    if args.json:
        json.dump([dict(asset=n, **f, **{'res_' + k: v for k, v in r.items()}, verdict=w) for n, f, r, w in rows], open(args.json, 'w'), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
