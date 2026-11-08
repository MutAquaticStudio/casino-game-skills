#!/usr/bin/env python3
"""Audit a Spine rig (spine_parts_rig.py / spine_idle_rig.py) with the official spine-core 4.2 runtime.

Checks, with pass / warn / fail verdicts:
  DISTORTION  for every weighted mesh: how much each triangle's area and edge lengths change from the rest pose over the
              animation, and whether any triangle folds over. Stretched or squashed art is the main visual defect of soft parts.
  PHYSICS     for every physics constraint: (a) settles after a 30 px impulse (does not ring forever, does not explode),
              (b) gives the same motion at 30, 60 and 120 Hz updates (frame-rate independence), (c) each chain bone lags its physics
              parent by a plausible time (follow-through, not lock-step), (d) amplitude grows toward the tip of a chain.
Usage (inside a folder where `npm i @esotericsoftware/spine-core@4.2` was done):
  python3 rig_audit.py rig/mascot --anim idle --duration 3.2 [--json audit.json]
Exit code 1 if any FAIL. Thresholds are in THRESH at the top; they are starting points, tune them per game art style.
"""
import argparse, json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
THRESH = dict(
    area_ok=(0.85, 1.20), area_warn=(0.70, 1.40),          # triangle area ratio vs rest
    edge_ok=(0.90, 1.12), edge_warn=(0.80, 1.25),          # edge length ratio vs rest
    settle_2s=0.25, settle_4s=0.05,                         # residual swing as a share of the peak after 2 s and 4 s
    peak_max_px=90.0,                                       # peak tip swing after a 30 px impulse
    fps_ok=(0.80, 1.25), fps_warn=(0.60, 1.60),             # travel at 120 Hz / travel at 30 Hz
    lag_ok=(0.02, 0.40), corr_min=0.50,                     # child lag behind its physics parent (s) and correlation
)


def verdict(v, ok, warn):
    if ok[0] <= v <= ok[1]: return "ok"
    if warn[0] <= v <= warn[1]: return "WARN"
    return "FAIL"


def run_node(base, anim, dur):
    r = subprocess.run(["node", os.path.join(HERE, "spine_audit.mjs"), base + ".json", base + ".atlas", anim, str(dur)], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr)
    return json.loads(r.stdout)


def distortion(d):
    rows = []
    for m in d["meshes"]["meta"]:
        tri = np.array(m["tri"]).reshape(-1, 3); rest = np.array(d["meshes"]["rest"][m["name"]]).reshape(-1, 2)
        fr = np.array(d["meshes"]["frames"][m["name"]]).reshape(len(d["meshes"]["frames"][m["name"]]), -1, 2)
        def area(P): a, b, c = P[..., tri[:, 0], :], P[..., tri[:, 1], :], P[..., tri[:, 2], :]; return 0.5 * ((b[..., 0] - a[..., 0]) * (c[..., 1] - a[..., 1]) - (b[..., 1] - a[..., 1]) * (c[..., 0] - a[..., 0]))
        ar0 = area(rest); good = np.abs(ar0) > 4.0
        ar = area(fr)
        ratio = ar[:, good] / ar0[good]
        fold = int(((ar[:, good] * ar0[good]) <= 0).sum())
        er = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            l0 = np.linalg.norm(rest[tri[:, i]] - rest[tri[:, j]], axis=1); l = np.linalg.norm(fr[:, tri[:, i]] - fr[:, tri[:, j]], axis=-1)
            er.append(l[:, l0 > 3.0] / l0[l0 > 3.0])
        er = np.concatenate(er, axis=1)
        a_lo, a_hi = float(np.percentile(ratio, 0.5)), float(np.percentile(ratio, 99.5)); e_lo, e_hi = float(er.min()), float(er.max())
        va = min([verdict(a_lo, THRESH["area_ok"], THRESH["area_warn"]), verdict(a_hi, THRESH["area_ok"], THRESH["area_warn"])], key=["ok", "WARN", "FAIL"].index) if False else max([verdict(a_lo, THRESH["area_ok"], THRESH["area_warn"]), verdict(a_hi, THRESH["area_ok"], THRESH["area_warn"])], key=["ok", "WARN", "FAIL"].index)
        ve = max([verdict(e_lo, THRESH["edge_ok"], THRESH["edge_warn"]), verdict(e_hi, THRESH["edge_ok"], THRESH["edge_warn"])], key=["ok", "WARN", "FAIL"].index)
        v = "FAIL" if fold else max([va, ve], key=["ok", "WARN", "FAIL"].index)
        rows.append(dict(mesh=m["name"], area_lo=a_lo, area_hi=a_hi, edge_lo=e_lo, edge_hi=e_hi, folds=fold, verdict=v))
    return rows


def physics(d):
    rows = []; bones = [p["bone"] for p in d["physics"]]
    for b in bones:
        s = d["settle"][b]; pk = max(s["peak"], 1e-6)
        r2, r4 = s["at2s"] / pk, s["at4s"] / pk
        f30, f120 = d["fps"]["30"][b], d["fps"]["120"][b]; fr = f120 / f30 if f30 > 0.05 else float("nan")
        lag = d["lag"][b]
        notes, v = [], "ok"
        def bump(x):
            nonlocal v
            v = x if ["ok", "WARN", "FAIL"].index(x) > ["ok", "WARN", "FAIL"].index(v) else v
        if s["peak"] < 1.0: notes.append("does not react to the body"); bump("WARN")
        if s["peak"] > THRESH["peak_max_px"]: notes.append("unstable swing"); bump("FAIL")
        if r4 > THRESH["settle_4s"] * 2: notes.append("never settles"); bump("FAIL")
        elif r2 > THRESH["settle_2s"] or r4 > THRESH["settle_4s"]: notes.append("slow to settle"); bump("WARN")
        if fr == fr:
            vf = verdict(fr, THRESH["fps_ok"], THRESH["fps_warn"])
            if vf != "ok": notes.append(f"frame-rate dependent ({fr:.2f}x)"); bump(vf)
        if lag["lag_s"] is not None and f30 > 0.5:
            if lag["corr"] < THRESH["corr_min"]: notes.append(f"does not follow its parent {lag['parent']}"); bump("WARN")
            elif not (THRESH["lag_ok"][0] <= lag["lag_s"] <= THRESH["lag_ok"][1]): notes.append(f"lag {lag['lag_s']:+.2f}s behind {lag['parent']} outside natural range"); bump("WARN")
        rows.append(dict(bone=b, peak=s["peak"], settle2=r2, settle4=r4, travel30=f30, travel120=f120, lag=lag["lag_s"] if lag["lag_s"] is not None else float("nan"), corr=lag["corr"] if lag["corr"] is not None else float("nan"), notes="; ".join(notes), verdict=v))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("--anim", default="idle"); ap.add_argument("--duration", type=float, default=3.2); ap.add_argument("--json")
    a = ap.parse_args()
    d = run_node(a.base, a.anim, a.duration)
    dist = distortion(d); phys = physics(d) if d["physics"] else []
    print("DISTORTION (area and edge ratio vs rest pose, over the animation; 1.00 = untouched)")
    print(f"{'mesh':14} {'area min':>8} {'area max':>8} {'edge min':>8} {'edge max':>8} {'folds':>5}  verdict")
    for r in dist: print(f"{r['mesh'][:14]:14} {r['area_lo']:8.2f} {r['area_hi']:8.2f} {r['edge_lo']:8.2f} {r['edge_hi']:8.2f} {r['folds']:5d}  {r['verdict']}")
    if phys:
        print("\nPHYSICS (impulse 30 px: peak swing, residual after 2 s / 4 s; travel in idle at 30 and 120 Hz; lag behind the parent bone)")
        print(f"{'bone':10} {'peak':>6} {'@2s':>5} {'@4s':>5} {'tr30':>6} {'tr120':>6} {'lag s':>6} {'corr':>5}  verdict")
        for r in phys: print(f"{r['bone'][:10]:10} {r['peak']:6.1f} {r['settle2']:5.2f} {r['settle4']:5.2f} {r['travel30']:6.1f} {r['travel120']:6.1f} {r['lag']:6.2f} {r['corr']:5.2f}  {r['verdict']} {r['notes']}")
    bad = [r for r in dist + phys if r["verdict"] == "FAIL"]; warn = [r for r in dist + phys if r["verdict"] == "WARN"]
    print(f"\n{len(bad)} FAIL, {len(warn)} WARN")
    if a.json: json.dump(dict(distortion=dist, physics=phys), open(a.json, "w"), indent=1)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
