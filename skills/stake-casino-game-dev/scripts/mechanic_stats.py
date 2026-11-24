#!/usr/bin/env python3
"""Count how often each book event type (= each mechanic) appears, per bet mode, weighted by the lookup table.

Usage: python mechanic_stats.py <publish_files dir> [--mode NAME] [--handlers handlers.txt] [--json]

For each mode prints, per event type: the share of rounds (by LUT weight) containing it, "1 in X", the mean count
per round when present, and the max count in one round. Compare with the round archetypes and frequencies in the
concept doc (references/concept-design.md §7.6) and the mechanic checklist (references/game-mechanics.md §14.12).

--handlers: a text file with one handled event type per line (e.g. grep your frontend's handler map into it); event
types found in the books but missing from the file are reported as FAIL (exit code 1).

Needs `pip install zstandard` for .jsonl.zst books. Reads the whole book; for a quick look on huge books use
--max-lines N (unweighted sample of the first N lines).
"""
import argparse, csv, io, json, os, sys
from collections import defaultdict


def open_book(path):
    if path.endswith(".zst"):
        import zstandard
        return io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(open(path, "rb")), encoding="utf-8")
    return open(path, encoding="utf-8")


def event_type(ev):
    return ev.get("type") or ev.get("name") or "?"


def mode_stats(d, md, max_lines):
    weights = {}
    for row in csv.reader(open(os.path.join(d, md["weights"]))):
        if row:
            weights[int(row[0])] = int(row[1])
    present = defaultdict(int)      # event type -> summed weight of rounds containing it
    count_sum = defaultdict(int)    # event type -> summed weight * count
    count_max = defaultdict(int)
    total_w = 0
    with open_book(os.path.join(d, md["events"])) as fh:
        for i, line in enumerate(l for l in fh if l.strip()):
            if max_lines and i >= max_lines:
                break
            o = json.loads(line)
            w = 1 if max_lines else weights.get(o["id"], 0)
            total_w += w
            counts = defaultdict(int)
            for ev in o.get("events", []):
                counts[event_type(ev)] += 1
            for t, c in counts.items():
                present[t] += w
                count_sum[t] += w * c
                count_max[t] = max(count_max[t], c)
    rows = []
    for t in sorted(present, key=lambda k: -present[k]):
        share = present[t] / total_w if total_w else 0
        rows.append({"event": t, "share": share, "one_in": (1 / share) if share else None,
                     "mean_when_present": count_sum[t] / present[t] if present[t] else 0, "max": count_max[t]})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dir")
    ap.add_argument("--mode")
    ap.add_argument("--handlers")
    ap.add_argument("--max-lines", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    idx = json.load(open(os.path.join(a.dir, "index.json")))
    handled = None
    if a.handlers:
        handled = {l.strip() for l in open(a.handlers) if l.strip() and not l.startswith("#")}
    out, missing = {}, set()
    for md in idx["modes"]:
        if a.mode and md["name"] != a.mode:
            continue
        rows = mode_stats(a.dir, md, a.max_lines)
        out[md["name"]] = rows
        if handled is not None:
            missing |= {r["event"] for r in rows} - handled
    if a.json:
        print(json.dumps({"modes": out, "unhandled": sorted(missing)}, indent=2))
    else:
        for name, rows in out.items():
            print(f"== {name}" + (" (unweighted sample)" if a.max_lines else ""))
            print(f"  {'event':<24}{'rounds %':>10}{'1 in':>12}{'mean':>8}{'max':>6}")
            for r in rows:
                one_in = f"{r['one_in']:,.1f}" if r["one_in"] else "-"
                print(f"  {r['event']:<24}{r['share']*100:>9.3f}%{one_in:>12}{r['mean_when_present']:>8.2f}{r['max']:>6}")
        for t in sorted(missing):
            print(f"[FAIL] event type '{t}' appears in books but has no handler")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
