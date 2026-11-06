#!/usr/bin/env python3
"""Validate Stake Engine math publish files and report approval statistics.

Usage:
    python validate_math.py <publish_files_dir> [--max-book-lines N] [--json out.json]

Checks
  Format : index.json schema, files exist, LUT rows are 3 uint columns, book line i has id == i,
           book payoutMultiplier == LUT payout, row counts match.
  Stats  : RTP per mode (90-98%), cross-mode RTP spread (<=0.5%), hit-rate, max-win frequency,
           share of zero-weight rows, dominant single outcome, std dev, win-range gaps.

Books may be .jsonl.zst (needs `pip install zstandard`) or plain .jsonl/.json lines.
Exit code 1 if any FAIL.
"""
import argparse
import csv
import io
import json
import math
import os
import sys

RTP_MIN, RTP_MAX, RTP_SPREAD = 0.90, 0.98, 0.005
MAXWIN_HIT_LIMIT = 20_000_000          # checklist: 1 in 20M or more frequent
HIT_RATE_BASE_LIMIT = 20               # non-zero win at least 1 in 20
WIN_BUCKETS = [0, 0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000,
               10000, 25000, 50000, 100000, float("inf")]

results = []


def report(level, mode, msg):
    results.append({"level": level, "mode": mode, "msg": msg})
    print(f"[{level}] {mode or '-'}: {msg}")


def open_book(path):
    if path.endswith(".zst"):
        try:
            import zstandard
        except ImportError:
            report("WARN", None, "zstandard not installed; skipping book checks "
                                 "(pip install zstandard)")
            return None
        fh = open(path, "rb")
        reader = zstandard.ZstdDecompressor().stream_reader(fh)
        return io.TextIOWrapper(reader, encoding="utf-8")
    return open(path, encoding="utf-8")


def load_lut(path, mode):
    rows = []
    with open(path, newline="") as fh:
        for i, row in enumerate(csv.reader(fh)):
            if not row:
                continue
            if len(row) != 3:
                report("FAIL", mode, f"LUT line {i} has {len(row)} columns (need 3)")
                return None
            try:
                sid, w, p = (int(x) for x in row)
            except ValueError:
                report("FAIL", mode, f"LUT line {i} not integers: {row} (no header, uint64 only)")
                return None
            if w < 0 or p < 0:
                report("FAIL", mode, f"LUT line {i} negative value")
                return None
            rows.append((sid, w, p))
    return rows


def check_book(path, lut, mode, max_lines):
    fh = open_book(path)
    if fh is None:
        return
    lut_by_id = {sid: p for sid, _, p in lut}
    n = 0
    mismatches = 0
    with fh:
        for i, line in enumerate(fh):
            if max_lines and i >= max_lines:
                report("INFO", mode, f"book check stopped after {max_lines} lines")
                return
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                report("FAIL", mode, f"book line {i} is not valid JSON")
                return
            for key in ("id", "payoutMultiplier", "events"):
                if key not in obj:
                    report("FAIL", mode, f"book line {i} missing '{key}'")
                    return
            if obj["id"] != i:
                report("FAIL", mode, f"book line {i} has id {obj['id']} (must equal line index)")
                return
            if lut_by_id.get(i) != obj["payoutMultiplier"]:
                mismatches += 1
                if mismatches <= 5:
                    report("FAIL", mode, f"sim {i}: book payout {obj['payoutMultiplier']} "
                                         f"!= LUT {lut_by_id.get(i)}")
            n += 1
    if n != len(lut):
        report("FAIL", mode, f"book has {n} lines, LUT has {len(lut)} rows")
    elif not mismatches:
        report("PASS", mode, f"book/LUT consistent ({n} sims)")


def stats(lut, cost, mode):
    W = sum(w for _, w, _ in lut)
    if W == 0:
        report("FAIL", mode, "total weight is 0")
        return None
    mult = [(w, p / 100.0 / cost) for _, w, p in lut]   # return per unit of cost
    rtp = sum(w * m for w, m in mult) / W
    var = sum(w * (m - rtp) ** 2 for w, m in mult) / W
    win_w = sum(w for _, w, p in lut if p > 0)
    maxp = max(p for _, w, p in lut if w > 0)
    max_w = sum(w for _, w, p in lut if p == maxp)
    zero_weight = sum(1 for _, w, _ in lut if w == 0)
    nonzero_payouts = sum(1 for _, w, p in lut if w > 0 and p > 0)
    top_w = max(w for _, w, _ in lut)
    s = {
        "mode": mode, "cost": cost, "sims": len(lut), "rtp": rtp, "std": math.sqrt(var),
        "hit_rate_1_in": (W / win_w) if win_w else float("inf"),
        "max_win_x_bet": maxp / 100.0, "max_win_1_in": W / max_w,
        "zero_weight_rows": zero_weight, "nonzero_weight_paying_rows": nonzero_payouts,
        "top_single_outcome_share": top_w / W,
    }
    # win-range distribution (in x of base bet, payout/100)
    buckets = [0] * (len(WIN_BUCKETS) - 1)
    for _, w, p in lut:
        x = p / 100.0
        if p == 0 or w == 0:
            continue
        for b in range(len(WIN_BUCKETS) - 1):
            if WIN_BUCKETS[b] < x <= WIN_BUCKETS[b + 1]:
                buckets[b] += w
                break
    s["win_ranges"] = {f"({WIN_BUCKETS[b]},{WIN_BUCKETS[b+1]}]": (W / c if c else None)
                       for b, c in enumerate(buckets)}
    return s


def judge(s, is_base):
    m = s["mode"]
    report("PASS" if RTP_MIN <= s["rtp"] <= RTP_MAX else "FAIL", m,
           f"RTP {s['rtp']*100:.3f}% (allowed 90-98%)")
    report("PASS" if s["max_win_1_in"] <= MAXWIN_HIT_LIMIT else "FAIL", m,
           f"max win {s['max_win_x_bet']:.2f}x hit 1 in {s['max_win_1_in']:,.0f} "
           f"(must be <= 1 in {MAXWIN_HIT_LIMIT:,})")
    if is_base:
        hr = s["hit_rate_1_in"]
        lvl = "PASS" if hr <= HIT_RATE_BASE_LIMIT else "FAIL"
        note = " (typical 3-8)" if lvl == "PASS" else ""
        report(lvl, m, f"non-zero win hit-rate 1 in {hr:.2f}{note}")
    if s["sims"] < 100_000:
        report("WARN", m, f"only {s['sims']:,} sims; slot-type games should have 100k-1M")
    if s["top_single_outcome_share"] > 0.05:
        report("WARN", m, f"single most likely sim has {s['top_single_outcome_share']*100:.1f}% "
                          "of weight - may look repetitive")
    if s["zero_weight_rows"] > s["sims"] / 2:
        report("WARN", m, f"{s['zero_weight_rows']:,} zero-weight rows dominate the books")
    # gaps: empty bucket between first and last non-empty
    keys = list(s["win_ranges"])
    filled = [i for i, k in enumerate(keys) if s["win_ranges"][k]]
    if filled:
        gaps = [keys[i] for i in range(filled[0], filled[-1]) if not s["win_ranges"][keys[i]]]
        if gaps:
            report("WARN", m, f"no wins in ranges {gaps} between small wins and max win")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--max-book-lines", type=int, default=0,
                    help="limit lines checked per book (0 = all)")
    ap.add_argument("--json", help="write stats to this file")
    a = ap.parse_args()

    idx_path = os.path.join(a.dir, "index.json")
    if not os.path.exists(idx_path):
        report("FAIL", None, "index.json missing")
        sys.exit(1)
    idx = json.load(open(idx_path))
    modes = idx.get("modes")
    if not isinstance(modes, list) or not modes:
        report("FAIL", None, "index.json must have non-empty 'modes' list")
        sys.exit(1)

    all_stats = []
    for i, md in enumerate(modes):
        missing = [k for k in ("name", "cost", "events", "weights") if k not in md]
        if missing:
            report("FAIL", None, f"mode #{i} missing keys {missing}")
            continue
        name, cost = md["name"], float(md["cost"])
        lut_p = os.path.join(a.dir, md["weights"])
        book_p = os.path.join(a.dir, md["events"])
        for p in (lut_p, book_p):
            if not os.path.exists(p):
                report("FAIL", name, f"file not found: {os.path.basename(p)}")
        if not os.path.exists(lut_p):
            continue
        if not md["events"].endswith(".jsonl.zst"):
            report("WARN", name, "events file should be .jsonl.zst for upload")
        lut = load_lut(lut_p, name)
        if lut is None:
            continue
        ids = [r[0] for r in lut]
        if ids != list(range(len(lut))):
            report("FAIL", name, "LUT sim_ids are not 0..N-1 in order")
        if os.path.exists(book_p):
            check_book(book_p, lut, name, a.max_book_lines)
        s = stats(lut, cost, name)
        if s:
            judge(s, is_base=(cost == 1.0))
            all_stats.append(s)

    if len(all_stats) > 1:
        rtps = [s["rtp"] for s in all_stats]
        spread = max(rtps) - min(rtps)
        report("PASS" if spread <= RTP_SPREAD + 1e-9 else "FAIL", None,
               f"RTP spread across modes {spread*100:.3f}% (max 0.5%)")

    print("\nSummary")
    print(f"{'mode':<14}{'cost':>8}{'sims':>10}{'RTP%':>9}{'hit 1in':>9}{'maxwin x':>11}"
          f"{'max 1in':>14}{'std':>9}")
    for s in all_stats:
        print(f"{s['mode']:<14}{s['cost']:>8g}{s['sims']:>10,}{s['rtp']*100:>9.3f}"
              f"{s['hit_rate_1_in']:>9.2f}{s['max_win_x_bet']:>11.2f}"
              f"{s['max_win_1_in']:>14,.0f}{s['std']:>9.2f}")
    if a.json:
        json.dump({"stats": all_stats, "results": results}, open(a.json, "w"), indent=2,
                  default=str)
    sys.exit(1 if any(r["level"] == "FAIL" for r in results) else 0)


if __name__ == "__main__":
    main()
