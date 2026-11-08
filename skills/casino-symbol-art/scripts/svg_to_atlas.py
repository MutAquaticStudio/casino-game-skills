#!/usr/bin/env python3
"""svg_to_atlas.py - SVG casino symbols -> lint, preview sheet, PixiJS v8 spritesheet.

Subcommands
  lint     <svg_dir>                      static checks for Stake-safe, animation-ready SVGs
  preview  <svg_dir> --out preview.png    contact sheet: full size + "real reel size" thumbnail
  layers   <svg_dir> --out art/layers     each top-level named <g> -> full-canvas PNG (Spine input)
  build    <svg_dir> --out dist/symbols   render + pack -> symbols@1x/@2x .png + .json

`preview` and `build` also accept raster symbols: any `<name>.png` (transparent RGBA, e.g. from
scripts/raster_cutout.py or the painterly toolkit) in the folder is scaled to the cell width and
packed like an SVG. If `<name>.svg` and `<name>.png` both exist, the SVG wins. `lint` and
`layers` only look at SVG files.

Needs Pillow and one SVG renderer: `rsvg-convert` (librsvg) or `pip install cairosvg`
(only when the folder has SVG files; a PNG-only folder needs just Pillow).
Output JSON is the TexturePacker-style format PixiJS reads with Assets.load('symbols.json').
Frames are NOT trimmed on purpose: every symbol keeps the same cell, so anchors, win
animations and reel strips line up without per-frame offsets.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

SVG_NS = "{http://www.w3.org/2000/svg}"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
PAINT_SERVERS = {"linearGradient", "radialGradient", "filter", "clipPath", "mask", "pattern"}


def find_svgs(folder):
    files = sorted(Path(folder).glob("*.svg"))
    if not files:
        sys.exit(f"No .svg files in {folder}")
    return files


def find_sources(folder):
    """SVG and PNG symbols in one folder, sorted by name; an SVG beats a PNG with the same stem."""
    found = {p.stem: p for p in Path(folder).glob("*.png")}
    found.update({p.stem: p for p in Path(folder).glob("*.svg")})
    if not found:
        sys.exit(f"No .svg or .png files in {folder}")
    return [found[k] for k in sorted(found)]


def render_svg(svg, width):
    """Render to an RGBA image `width` px wide (height follows the viewBox / PNG aspect)."""
    if Path(svg).suffix.lower() == ".png":
        im = Image.open(svg).convert("RGBA")
        if im.width == width:
            return im
        return im.resize((width, max(1, round(im.height * width / im.width))), Image.LANCZOS)
    if shutil.which("rsvg-convert"):
        out = subprocess.run(
            ["rsvg-convert", "-w", str(width), "--format", "png", str(svg)],
            capture_output=True, check=True,
        ).stdout
        return Image.open(BytesIO(out)).convert("RGBA")
    try:
        import cairosvg
    except ImportError:
        sys.exit("Need an SVG renderer: install librsvg (rsvg-convert) or `pip install cairosvg`.")
    out = cairosvg.svg2png(url=str(svg), output_width=width)
    return Image.open(BytesIO(out)).convert("RGBA")


# --------------------------------------------------------------------------- lint
def lint(files):
    errors = warnings = 0
    ids_seen = {}
    boxes = {}

    def err(name, msg):
        nonlocal errors
        errors += 1
        print(f"ERROR  {name}: {msg}")

    def warn(name, msg):
        nonlocal warnings
        warnings += 1
        print(f"WARN   {name}: {msg}")

    for f in files:
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError as e:
            err(f.name, f"invalid XML ({e})")
            continue

        vb = root.get("viewBox")
        if not vb:
            warn(f.name, "no viewBox - size will depend on width/height attributes")
        else:
            try:
                nums = [float(n) for n in re.split(r"[ ,]+", vb.strip())]
                boxes[f.name] = tuple(nums[2:4])
            except (ValueError, IndexError):
                err(f.name, f"unreadable viewBox '{vb}'")

        has_named_group = False
        for el in root.iter():
            tag = el.tag.replace(SVG_NS, "")
            if tag in ("script", "foreignObject"):
                err(f.name, f"<{tag}> is not allowed (not portable, can run code)")
            if tag == "text":
                warn(f.name, "<text> depends on installed fonts - convert it to paths")
            if tag == "style" and el.text and re.search(r"@import|url\(\s*['\"]?https?:", el.text):
                err(f.name, "<style> pulls a remote resource (Stake builds must not reach external URLs)")
            for attr in ("href", XLINK_HREF):
                v = el.get(attr)
                if v and re.match(r"(https?:)?//", v.strip()):
                    err(f.name, f"external reference '{v[:60]}' (Stake builds must be self-contained)")
            eid = el.get("id")
            if eid:
                if tag == "g":
                    has_named_group = True  # layer names (body, glow...) may repeat across files
                if tag in PAINT_SERVERS:
                    ids_seen.setdefault(eid, set()).add(f.name)
                    if not eid.startswith(f.stem):
                        warn(f.name, f"id '{eid}' lacks the '{f.stem}-' prefix (collides when inlined or merged)")
        if not has_named_group:
            warn(f.name, "no named <g id=...> layers - it cannot be split into layers for animation later")

    for eid, names in ids_seen.items():
        if len(names) > 1:
            warn(", ".join(sorted(names)), f"duplicate id '{eid}' across files")

    if len(set(boxes.values())) > 1:
        detail = ", ".join(f"{n}={int(w)}x{int(h)}" for n, (w, h) in sorted(boxes.items()))
        warn("all", f"viewBox sizes differ ({detail}) - symbols in one set should share one canvas")

    print(f"\nlint: {len(files)} file(s), {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


# ------------------------------------------------------------------------ preview
def checkerboard(w, h, s=16):
    img = Image.new("RGBA", (w, h), (58, 60, 70, 255))
    d = ImageDraw.Draw(img)
    for y in range(0, h, s):
        for x in range(0, w, s):
            if (x // s + y // s) % 2:
                d.rectangle([x, y, x + s - 1, y + s - 1], fill=(78, 80, 92, 255))
    return img


def preview(files, out, cell, shrink, cols):
    pad, label_h = 10, 18
    strip_h = shrink + 12
    cw, ch = cell + 2 * pad, cell + label_h + strip_h + 2 * pad
    rows = -(-len(files) // cols)
    sheet = Image.new("RGBA", (cols * cw, rows * ch), (24, 26, 34, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, f in enumerate(files):
        x0, y0 = (i % cols) * cw + pad, (i // cols) * ch + pad
        big = render_svg(f, cell)
        bg = checkerboard(cell, cell)
        bg.alpha_composite(big, ((cell - big.width) // 2, (cell - big.height) // 2))
        sheet.paste(bg, (x0, y0))
        draw.text((x0, y0 + cell + 3), f.stem, fill=(235, 235, 240, 255), font=font)
        # thumbnail on a flat dark strip = how it reads inside a real reel
        sy = y0 + cell + label_h
        draw.rectangle([x0, sy, x0 + cell - 1, sy + strip_h - 2], fill=(14, 16, 24, 255))
        small = render_svg(f, shrink)
        sheet.alpha_composite(small, (x0 + 6, sy + 6))
        draw.text((x0 + shrink + 14, sy + 6), f"{shrink}px", fill=(150, 154, 170, 255), font=font)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)
    print(f"preview: {len(files)} symbol(s) -> {out}  ({sheet.width}x{sheet.height})")


# ------------------------------------------------------------------------- layers
def export_layers(files, out_dir, size):
    """Render every top-level <g id="..."> of each SVG as its own full-canvas PNG.

    All layers of a symbol share the same canvas, so they import into Spine (or any
    layered tool) already registered to each other - no per-layer offsets to track.
    """
    ET.register_namespace("", SVG_NS.strip("{}"))
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    out_dir = Path(out_dir)
    total = 0
    for f in files:
        tree = ET.parse(f)
        root = tree.getroot()
        kids = list(root)
        groups = [k for k in kids if k.tag == SVG_NS + "g" and k.get("id")]
        loose = [k for k in kids if k.tag not in (SVG_NS + "defs", SVG_NS + "style", SVG_NS + "title", SVG_NS + "desc")
                 and k not in groups]
        if not groups:
            print(f"skip   {f.name}: no top-level <g id=...> layers")
            continue
        if loose:
            print(f"WARN   {f.name}: {len(loose)} element(s) outside a named layer are not exported")
        dest = out_dir / f.stem
        dest.mkdir(parents=True, exist_ok=True)
        for g in groups:
            clone = ET.fromstring(ET.tostring(root))
            for k in list(clone):
                is_defs = k.tag in (SVG_NS + "defs", SVG_NS + "style")
                if not is_defs and k.get("id") != g.get("id"):
                    clone.remove(k)
            tmp = dest / f"{g.get('id')}.svg"
            tmp.write_bytes(ET.tostring(clone))
            render_svg(tmp, size).save(dest / f"{g.get('id')}.png", optimize=True)
            tmp.unlink()
            total += 1
        # File names sort alphabetically, so record the real stacking order (bottom -> top).
        (dest / "layers.json").write_text(json.dumps(
            {"symbol": f.stem, "width": size, "order_bottom_to_top": [g.get("id") for g in groups]}, indent=2))
        print(f"layers {f.name}: {' < '.join(g.get('id') for g in groups)} -> {dest}")
    print(f"\nlayers: {total} PNG(s) written to {out_dir}")


# -------------------------------------------------------------------------- build
def next_pot(n):
    p = 1
    while p < n:
        p *= 2
    return p


def shelf_pack(sizes, atlas_w):
    """Place rects (w,h incl. gutters) left-to-right in shelves; return positions and height."""
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1])
    pos, x, y, row_h = {}, 0, 0, 0
    for i in order:
        w, h = sizes[i]
        if w > atlas_w:
            return None, None
        if x + w > atlas_w:
            x, y, row_h = 0, y + row_h, 0
        pos[i] = (x, y)
        x += w
        row_h = max(row_h, h)
    return pos, y + row_h


def round_up(n, m):
    return -(-n // m) * m


def choose_layout(sizes, max_size, pot):
    """Pick the smallest atlas. Default: tight, sides rounded to a multiple of 4 (what
    KTX2/BasisU need). pot=True forces power-of-two sides."""
    widest = max(w for w, _ in sizes)
    widths = {1 << k for k in range(7, 14) if (1 << k) <= max_size}
    if not pot:
        widths |= {widest * k for k in range(1, len(sizes) + 1) if widest * k <= max_size}
    candidates = []
    for w in sorted(widths):
        pos, h = shelf_pack(sizes, w)
        if pos is None:
            continue
        aw = w if pot else round_up(w, 4)
        ah = next_pot(h) if pot else round_up(h, 4)
        if aw <= max_size and ah <= max_size:
            candidates.append((aw, ah, pos))
    if not candidates:
        return None
    # Smallest area wins, but areas within 2% count as equal (rounding to a multiple of 4
    # makes near-identical layouts differ by fractions of a percent); among those take the
    # squarest, which is easier to inspect and leaves room to add symbols later.
    smallest = min(aw * ah for aw, ah, _ in candidates)
    near = [c for c in candidates if c[0] * c[1] <= smallest * 1.02]
    return min(near, key=lambda c: (max(c[0], c[1]), c[0] * c[1]))


def extrude_edges(img, n):
    """Return img with its border pixels replicated n px outward (stops texture bleeding)."""
    if n <= 0:
        return img
    w, h = img.size
    out = Image.new("RGBA", (w + 2 * n, h + 2 * n), (0, 0, 0, 0))
    out.paste(img, (n, n))
    out.paste(img.crop((0, 0, 1, h)).resize((n, h)), (0, n))
    out.paste(img.crop((w - 1, 0, w, h)).resize((n, h)), (w + n, n))
    out.paste(out.crop((0, n, w + 2 * n, n + 1)).resize((w + 2 * n, n)), (0, 0))
    out.paste(out.crop((0, h + n - 1, w + 2 * n, h + n)).resize((w + 2 * n, n)), (0, h + n))
    return out


def build(files, out_base, size, scales, padding, extrude, max_size, fmt, quality, anchor, pot):
    out_base = Path(out_base)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    ax, ay = (float(v) for v in anchor.split(","))
    gutter = padding + extrude
    for scale in scales:
        px = int(round(size * scale))
        tiles = [(f.stem, render_svg(f, px)) for f in files]
        sizes = [(t.width + 2 * gutter, t.height + 2 * gutter) for _, t in tiles]
        layout = choose_layout(sizes, max_size, pot)
        if layout is None:
            sys.exit(
                f"{len(files)} symbols at {px}px do not fit in {max_size}x{max_size}. "
                "Lower --size / --scales, raise --max-size (4096 max on mobile), or split the set "
                "(e.g. base symbols vs bonus symbols)."
            )
        aw, ah, pos = layout
        atlas = Image.new("RGBA", (aw, ah), (0, 0, 0, 0))
        frames = {}
        for i, (name, tile) in enumerate(tiles):
            x, y = pos[i]
            atlas.alpha_composite(extrude_edges(tile, extrude), (x + padding, y + padding))
            fx, fy = x + gutter, y + gutter
            frames[name] = {
                "frame": {"x": fx, "y": fy, "w": tile.width, "h": tile.height},
                "rotated": False,
                "trimmed": False,
                "spriteSourceSize": {"x": 0, "y": 0, "w": tile.width, "h": tile.height},
                "sourceSize": {"w": tile.width, "h": tile.height},
                "anchor": {"x": ax, "y": ay},
            }
        # Pixi expands 'name@{1,2}x.json' to name@1x.json + name@2x.json, so with several
        # scales every file needs its suffix; a lone 1x build keeps the plain name.
        suffix = f"@{scale:g}x" if (len(scales) > 1 or scale != 1) else ""
        img_path = Path(f"{out_base}{suffix}.{fmt}")
        json_path = Path(f"{out_base}{suffix}.json")
        if fmt == "webp":
            atlas.save(img_path, "WEBP", quality=quality, method=6)
        else:
            atlas.save(img_path, "PNG", optimize=True)
        sheet = {
            "frames": frames,
            "meta": {
                "app": "casino-symbol-art/svg_to_atlas.py",
                "version": "1.0",
                "image": img_path.name,
                "format": "RGBA8888",
                "size": {"w": aw, "h": ah},
                "scale": f"{scale:g}",
            },
        }
        json_path.write_text(json.dumps(sheet, indent=2))
        kb = img_path.stat().st_size / 1024
        print(f"build: {len(files)} frame(s) @{scale:g}x -> {json_path.name} + {img_path.name} "
              f"({aw}x{ah}, {kb:.0f} KB, cell {px}px)")
    if len(scales) > 1 or scales[0] != 1:
        pattern = ",".join(f"{s:g}" for s in scales)
        src = f"{out_base.name}@{{{pattern}}}x.json"
        init = "  // Assets.init({ texturePreference: { resolution: Math.min(devicePixelRatio, 2) } }) first\n"
    else:
        src, init = f"{out_base.name}.json", ""
    print(
        "\nLoad in Pixi v8:\n" + init +
        f"  Assets.add({{ alias: '{out_base.name}', src: '{src}' }});\n"
        f"  await Assets.load('{out_base.name}');\n"
        f"  const s = Sprite.from('{files[0].stem}');"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint")
    p.add_argument("svg_dir")

    p = sub.add_parser("preview")
    p.add_argument("svg_dir")
    p.add_argument("--out", default="preview.png")
    p.add_argument("--cell", type=int, default=256, help="full-size cell in px (default 256)")
    p.add_argument("--shrink", type=int, default=140, help="real on-screen symbol size in px (default 140)")
    p.add_argument("--cols", type=int, default=4)

    p = sub.add_parser("layers", help="export each top-level named <g> as a full-canvas PNG (for Spine/frame work)")
    p.add_argument("svg_dir")
    p.add_argument("--out", default="art/layers")
    p.add_argument("--size", type=int, default=512, help="PNG width in px (default 512)")

    p = sub.add_parser("build")
    p.add_argument("svg_dir")
    p.add_argument("--out", default="dist/symbols", help="output base path, no extension")
    p.add_argument("--size", type=int, default=256, help="1x cell width in px")
    p.add_argument("--scales", default="1,2", help="comma list, e.g. 1,2")
    p.add_argument("--padding", type=int, default=2, help="transparent gutter around each frame")
    p.add_argument("--extrude", type=int, default=1, help="edge-replicate px (stops bleeding when scaled)")
    p.add_argument("--max-size", type=int, default=2048, help="max atlas side (2048 safe, 4096 upper bound)")
    p.add_argument("--format", choices=["png", "webp"], default="png")
    p.add_argument("--quality", type=int, default=90, help="webp quality")
    p.add_argument("--anchor", default="0.5,0.5", help="default sprite anchor x,y")
    p.add_argument("--pot", action="store_true", help="force power-of-two atlas sides (default: tight, multiple of 4)")

    a = ap.parse_args()
    if a.cmd == "lint":
        sys.exit(lint(find_svgs(a.svg_dir)))
    if a.cmd == "layers":
        export_layers(find_svgs(a.svg_dir), a.out, a.size)
        return
    files = find_sources(a.svg_dir)
    if a.cmd == "preview":
        preview(files, a.out, a.cell, a.shrink, a.cols)
    else:
        scales = [float(s) for s in a.scales.split(",") if s.strip()]
        build(files, a.out, a.size, scales, a.padding, a.extrude, a.max_size, a.format, a.quality, a.anchor, a.pot)


if __name__ == "__main__":
    main()
