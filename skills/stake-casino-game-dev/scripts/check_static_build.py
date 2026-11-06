#!/usr/bin/env python3
"""Check a production build for Stake Engine static/XSS-policy problems.

Usage:
    python check_static_build.py <dist_dir>

Flags:
  FAIL  external URLs in HTML/CSS/JS that would be fetched (fonts.googleapis, CDNs, http(s)://
        in src/href/url()/import/fetch), hardcoded Stake RGS hosts, absolute asset paths
        starting with "/" (break under /{game}/v{n}/), server-only files.
  WARN  console.log calls left in bundles, very large files, total size, source maps.
Known-harmless URLs (XML namespaces, license comments) are ignored.
"""
import os
import re
import sys

IGNORE_URL = re.compile(r"https?://(www\.w3\.org|schemas\.|ns\.adobe\.com|purl\.org|"
                        r"github\.com/[^\s'\"]*/(blob|issues)|opensource\.org|"
                        r"reactjs\.org/docs/error-decoder|svelte\.dev/e/|threejs\.org/docs|"
                        r"developer\.mozilla\.org|localhost)")
FETCH_PATTERNS = [
    re.compile(r"""(?:src|href)\s*=\s*["'](https?:)?//[^"']+""", re.I),
    re.compile(r"""url\(\s*["']?(https?:)?//[^)"']+""", re.I),
    re.compile(r"""@import\s+["'](https?:)?//[^"']+""", re.I),
    re.compile(r"""(?:fetch|import|setDecoderPath|setTranscoderPath|load)\(\s*["'`]https?://[^"'`]+""", re.I),
]
KNOWN_CDNS = re.compile(r"fonts\.googleapis|fonts\.gstatic|cdn\.jsdelivr|unpkg\.com|cdnjs|"
                        r"gstatic\.com/draco|google-analytics|googletagmanager", re.I)
HARDCODED_RGS = re.compile(r"""["'`](https?://)?rgs[\w.-]*\.stake-engine\.com""", re.I)
ABS_ASSET = re.compile(r"""(?:src|href)\s*=\s*["']/(?!/)[^"']+\.(png|jpe?g|webp|svg|js|css|"""
                       r"""woff2?|ttf|json|mp3|ogg|glb|gltf|ktx2)""", re.I)
TEXT_EXT = (".html", ".js", ".mjs", ".css", ".json", ".svg")
issues = []


def add(level, path, msg):
    issues.append(level)
    print(f"[{level}] {path}: {msg}")


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__)
        sys.exit(2)
    root = sys.argv[1]
    total = 0
    has_index = os.path.exists(os.path.join(root, "index.html"))
    if not has_index:
        add("FAIL", root, "no index.html at build root")
    for dp, _, files in os.walk(root):
        for f in files:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root)
            size = os.path.getsize(p)
            total += size
            if size > 15 * 1024 * 1024:
                add("WARN", rel, f"large file {size/1e6:.1f} MB")
            if f.endswith(".map"):
                add("WARN", rel, "source map shipped (exposes source; usually remove)")
            if f in ("server.js", "package.json") or f.endswith((".php", ".py")):
                add("WARN", rel, "server-side file in static build")
            if not f.endswith(TEXT_EXT):
                continue
            text = open(p, encoding="utf-8", errors="ignore").read()
            seen = set()
            for rx in FETCH_PATTERNS:
                for m in rx.finditer(text):
                    s = m.group(0)
                    if IGNORE_URL.search(s) or s in seen:
                        continue
                    seen.add(s)
                    add("FAIL", rel, f"external resource: {s[:120]}")
            for m in KNOWN_CDNS.finditer(text):
                if m.group(0) not in seen:
                    seen.add(m.group(0))
                    add("FAIL", rel, f"references external CDN/service '{m.group(0)}'")
            if HARDCODED_RGS.search(text):
                add("FAIL", rel, "hardcoded RGS host - read rgs_url from the query string")
            if f.endswith(".html"):
                for m in ABS_ASSET.finditer(text):
                    add("FAIL", rel, f"absolute asset path {m.group(0)[:80]} - use relative "
                                     "paths (Vite base: './')")
            n_log = len(re.findall(r"console\.(log|debug)\(", text))
            if n_log and f.endswith((".js", ".mjs")):
                add("WARN", rel, f"{n_log} console.log/debug call(s) - strip game info logging")
    print(f"\nTotal build size: {total/1e6:.1f} MB")
    print("FAIL" if "FAIL" in issues else "OK (review WARNs)" if issues else "OK")
    sys.exit(1 if "FAIL" in issues else 0)


if __name__ == "__main__":
    main()
