#!/usr/bin/env python3
"""Scan UI text for words restricted on stake.us (social mode).

Usage:
    python check_social_terms.py <path> [<path> ...] [--ext .json,.ts,.svelte,...]

Point it at the files that hold the *social* English strings (e.g. locales/en-social.json)
or the whole src/ to find hardcoded labels. It reports file:line, the restricted phrase and
the required replacement. String literals and JSON values are scanned; code identifiers like
`betLevels` are ignored because matching is on whole words inside quotes/markup text.
Exit code 1 if anything is found.
"""
import argparse
import os
import re
import sys

# longest phrases first so "bonus buy" is reported instead of "buy"
REPLACEMENTS = {
    "be awarded to player's accounts": "appear in player's accounts",
    "place your bets": "come and play / join in the game",
    "at the cost of": "for",
    "buy bonus": "get bonus",
    "bonus buy": "bonus / feature",
    "loss limit": "stop limit",
    "loss streak": "miss streak",
    "total bet": "total play",
    "win feature": "play feature",
    "pay table": "win table",
    "paytable": "win table",
    "pays out": "win",
    "paid out": "won",
    "pay out": "win / won",
    "cost of": "can be played for",
    "betting": "playing",
    "bet/s": "play/s",
    "bets": "plays",
    "bet": "play",
    "bought": "instantly triggered",
    "buy": "play",
    "cash": "coins",
    "credit": "coins",
    "currency": "token",
    "deposit": "get coins",
    "gamble": "play",
    "money": "coins",
    "paid": "won",
    "payer": "winner",
    "pays": "wins",
    "pay": "win",
    "profit": "net gain",
    "purchase": "play",
    "rebet": "respin",
    "stake": "play amount",
    "wager": "play",
    "withdraw": "redeem",
    "autobet": "autoplay",
}
DEFAULT_EXT = ".json,.ts,.js,.svelte,.vue,.tsx,.jsx,.html,.md,.po,.yaml,.yml,.txt"
STRING_RE = re.compile(r"""(["'`])((?:\\.|(?!\1).)*)\1|>([^<>{}]+)<""")
PATTERNS = [(p, r, re.compile(r"(?<![A-Za-z])" + re.escape(p) + r"(?![A-Za-z])", re.I))
            for p, r in REPLACEMENTS.items()]
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".svelte-kit"}


BRAND_RE = re.compile(r"stake\s*engine|stake\.(us|com)", re.I)


def scan_text(text):
    text = BRAND_RE.sub(lambda m: "#" * len(m.group(0)), text)  # brand names are fine
    hits, taken = [], []
    for phrase, repl, rx in PATTERNS:
        for m in rx.finditer(text):
            if any(s <= m.start() < e for s, e in taken):
                continue
            taken.append((m.start(), m.end()))
            hits.append((m.group(0), repl))
    return hits


def scan_file(path, found):
    try:
        lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    except OSError:
        return
    is_plain = path.endswith((".md", ".txt", ".po"))
    for n, line in enumerate(lines, 1):
        chunks = [line] if is_plain else [m.group(2) or m.group(3) or ""
                                          for m in STRING_RE.finditer(line)]
        for chunk in chunks:
            # ignore things that look like code identifiers / keys / paths:
            # camelCase starting lowercase (betLevels), snake_case, dotted or slashed paths
            if re.fullmatch(r"[a-z][a-z0-9]*(?:[A-Z][a-z0-9]+)+|\w*_\w*|[\w-]*[./:][\w./:-]*",
                            chunk):
                continue
            for word, repl in scan_text(chunk):
                found.append((path, n, word, repl, chunk.strip()[:80]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--ext", default=DEFAULT_EXT)
    a = ap.parse_args()
    exts = tuple(a.ext.split(","))
    found = []
    for p in a.paths:
        if os.path.isfile(p):
            scan_file(p, found)
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if f.endswith(exts):
                    scan_file(os.path.join(root, f), found)
    for path, n, word, repl, ctx in found:
        print(f"{path}:{n}: '{word}' -> use '{repl}'   | {ctx}")
    print(f"\n{len(found)} restricted phrase(s) found." if found
          else "No restricted phrases found.")
    print("Remember: images/baked text and the replay window must be clean too.")
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
