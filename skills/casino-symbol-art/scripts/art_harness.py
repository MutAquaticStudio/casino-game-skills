#!/usr/bin/env python3
"""Theme -> locked style + one prompt per art layer, with a studio-grade structure baked in.

The structure comes from the style study in references/style-valkyrie-hacksaw.md. The theme
supplies only content (place, hero, objects, palette); the harness supplies the grammar
(layers, dark board with faint engraving and column grooves, roundel premiums, rank colour code,
framed Wild, round Scatter, magenta key, light direction), so every theme gets the same quality bar.

Usage:
  python3 art_harness.py theme.json --out art [--preset valkyrie|hacksaw]
  python3 art_harness.py --example > theme.json        # print a filled example theme
Theme field premium_container: "roundel" (default, shared round medallion), "tile" (rounded square),
or "freeform" (each symbol is its own frameless object; stricter silhouette and spacing rules).

Writes:
  art/style.json            palette, warm accent, style_lock, style_check groups
  art/plan.json             ordered generation plan (anchors first), sizes, groups, key colour
  art/prompts/<asset>.txt   the full prompt for each call: style lock first, then the asset part
Then an agent calls the image tool once per prompt file with the exact text, saves results to
art/layers/<asset>.png, and runs style_check.py (see SKILL.md section 1 and the study doc, part 7).
Nothing here calls a model or spends credits.
"""
import argparse, json, os, re, sys

KEY = "flat solid pure magenta (#FF00FF) background, no shadows on the background"
BRANDS = re.compile(r"\b(valkyrie|hacksaw|stake|pragmatic|disney|marvel|nintendo|pokemon|pok[eé]mon|"
                    r"star wars|harry potter|dc comics|netflix|coca[- ]?cola|nike)\b", re.I)

PRESETS = {
    "valkyrie": {
        "grammar": "Painted semi-realistic fantasy illustration, premium casino-slot quality, cinematic depth. "
                   "Light from the top-left, soft rim light, thin dark outline, one sharp specular highlight per object. "
                   "About 70 percent cool, dark and desaturated colour; warm gold, orange or red only on valuable things "
                   "(premium symbols, scatter glow, rewards). No text, no logos, no watermarks.",
        "palette_default": ["#0e121a", "#1b1f29", "#2d3d4f", "#555767", "#7e95a5", "#c4d3d9"],
        "warm_default": ["#d9a53a", "#c0392b", "#e07a2a"],
        "tol": {"palette_de": 28, "lightness": 12, "chroma": 14, "warm_share": 0.25, "outline_l": 14},
    },
    "hacksaw": {
        "grammar": "Bold stylised 2D illustration, flat to lightly shaded shapes, thick dark outlines, exaggerated expressive faces, "
                   "high contrast, a narrow palette of four to six colours with one complementary pop, readable at thumbnail size. "
                   "One strong hero object or character per image. Light from the top-left. No text, no logos, no watermarks.",
        "palette_default": ["#14171f", "#2b3a4a", "#4aa3a0", "#f2e8cf", "#e0533d", "#f2b632"],
        "warm_default": ["#f2b632", "#e0533d"],
        "tol": {"palette_de": 24, "lightness": 14, "chroma": 18, "warm_share": 0.35, "outline_l": 14},
    },
}

# How premium symbols are contained. "roundel" gives one shared silhouette (easy consistency, weaker
# silhouette variety); "freeform" gives every symbol its own outline (stronger shape reading,
# needs stricter outline, scale and spacing rules); "tile" gives a rounded square tile.
CONTAINERS = {
    "roundel": dict(
        sheet=("Eight premium symbols, each a round medallion with a thick metal ring and a dark centre, same size and same "
               "ring style so they read as one family, thin dark outline, one sharp specular highlight each, warm accent colours on a cool dark base: "),
        read="shared round silhouette: tell symbols apart by the object inside and by dominant colour"),
    "tile": dict(
        sheet=("Eight premium symbols, each a rounded-square tile with a thick bevelled metal border and a dark centre, same size and "
               "same border style so they read as one family, thin dark outline, one sharp specular highlight each, warm accent colours on a cool dark base: "),
        read="shared square silhouette: tell symbols apart by the object inside and by dominant colour"),
    "freeform": dict(
        sheet=("Eight premium symbols, each a single free-standing object with NO frame, NO ring, NO tile and NO background plate, "
               "so the outline of the object itself is its silhouette. Every object has a clearly different silhouette from the other seven "
               "(tall, wide, round, spiky, angular, soft), a thick dark outline of equal weight on all eight, strong rim light from the top-left, "
               "one sharp specular highlight, a dominant colour different from its neighbours, and fills about the same visual size as the others "
               "(equal height or width, about 80 percent of its cell). Leave generous empty space between objects so none touch or overlap, and keep "
               "glows and smoke inside the object's own cell: "),
        read="every symbol is its own silhouette: check silhouettes in a solid black fill at real size, they must all differ"),
}

EXAMPLE = {
    "title": "Sun Temple Gold",
    "one_line": "Ancient Egyptian sun-temple treasure hunt, warm sandstone and lapis, golden light",
    "place": "a vast sandstone temple courtyard at dusk with giant columns, hieroglyph-carved walls, a still reflecting pool, "
             "distant pyramids in haze and a huge setting sun, torches glowing orange",
    "cool_base": "deep lapis-blue and teal shadows with desaturated sandstone greys",
    "motif": "lotus columns, sun discs, scarab wings, stepped pyramids, hieroglyph bands",
    "frame_material": "carved dark basalt and gold-inlaid sandstone",
    "frame_detail": "tall lotus-capital columns on both sides, a lintel with a winged sun disc and an empty gold plaque in the middle",
    "hero": "an original female high priestess in white linen and gold collar, lapis headdress with a cobra crest, "
            "holding a tall staff topped with a glowing sun disc, confident three-quarter pose, a small spectral falcon beside her",
    "premiums": ["golden scarab beetle", "eye-shaped amulet in lapis and gold", "ceremonial gold sun disc", "ankh key of life",
                 "canopic jar with a jackal lid", "golden falcon head", "papyrus scroll with a wax seal", "cobra crown"],
    "wild": "a glowing amber sun orb inside a thick ornate gold frame",
    "scatter": "a round lotus-and-sun mandala medallion with a large glowing pearl at the centre",
    "bonus": "an open treasure sarcophagus spilling gold and jewels",
    "rank_flourish": "lotus petals and sun-ray lines",
    "palette": ["#0b1320", "#13283d", "#1f4a5c", "#4f6a78", "#a89a82", "#d8cfb8"],
    "warm_accent": ["#e0a530", "#c2481d", "#f08a24"],
    "cols": 5, "rows": 4,
    "premium_container": "roundel",
}

RANKS = [("A", "gold with red inlay"), ("K", "royal purple with gold edge"), ("Q", "deep red lacquer with gold edge"),
         ("J", "jade teal with gold edge"), ("10", "sapphire blue with gold edge")]


def build(theme, preset):
    P = PRESETS[preset]
    for k in ("title", "place", "hero", "premiums"):
        if k not in theme:
            sys.exit(f"theme is missing required field: {k}")
    if len(theme["premiums"]) != 8:
        sys.exit("theme.premiums must list exactly 8 objects (one 4x2 sheet keeps the family consistent)")
    blob = json.dumps(theme)
    m = BRANDS.search(blob)
    if m:
        sys.exit(f"theme mentions a studio or brand ('{m.group(0)}'). Stake needs original art: describe the idea, not the name.")
    t = theme
    cool = t.get("cool_base", "cool dark desaturated tones")
    motif = t.get("motif", "")
    prefix = (f"{P['grammar']} Theme: {t.get('one_line', t['title'])}. Colour base: {cool}. "
              f"Recurring motifs: {motif}.").replace("  ", " ")
    cols, rows = t.get("cols", 5), t.get("rows", 4)
    container = t.get("premium_container", "roundel")
    if container not in CONTAINERS:
        sys.exit(f"premium_container must be one of {sorted(CONTAINERS)}")
    spec = {
        "backdrop": dict(w=1792, h=1024, group="background", anchor=True, call=1, part=(
            f"Video slot game backdrop, no user interface, no text, no characters. Scene: {t['place']}. "
            "Three depth layers: far elements pale and low contrast, mid elements mid-tone, near foreground dark and detailed. "
            "Dark vignette at the edges, the centre calm and slightly darker so a reel grid can sit over it. Wide 16:9 landscape.")),
        "frame": dict(w=1536, h=1024, group="frame", anchor=True, call=2, part=(
            f"Video slot game reel frame only, front view, centred on a {KEY}, no symbols, no text. "
            f"A heavy ornate frame for a {cols}-column by {rows}-row reel grid made of {t.get('frame_material', 'carved dark stone and metal')}, "
            f"{t.get('frame_detail', 'thick pillars left and right and a wide lintel with an empty plaque in the middle')}. "
            "The inner window (the reel opening) is flat pure magenta (#FF00FF) so it can be cut out. "
            "The frame is the darkest and most ornate element of the whole game.")),
        "board": dict(w=1536, h=1024, group="background", anchor=False, call=3, part=(
            "Video slot reel board background texture, flat front view, filling the whole image edge to edge, no symbols, no text. "
            "Very dark surface (near black, slightly tinted by the colour base) with a faint engraved pattern at 10 to 15 percent contrast: "
            f"a repeating motif drawn from {motif or 'the theme motifs'} plus a large faint circular emblem fading toward the edges. "
            f"{cols} faint vertical column grooves evenly spaced with thin inset metallic lines. Slight inner vignette darker at the edges.")),
        "symbols_premium": dict(w=1792, h=1024, group="symbol", anchor=True, call=4, part=(
            f"Sprite sheet of video slot symbols on a {KEY}, no text, arranged in a clean 4-column by 2-row grid with wide even spacing. "
            + CONTAINERS[container]["sheet"]
            + ", ".join(f"({i + 1}) {p}" for i, p in enumerate(t["premiums"])) + ".")),
        "symbols_ranks": dict(w=1792, h=768, group="symbol", anchor=False, call=5, part=(
            f"Sprite sheet of five video slot card-rank symbols in one row on a {KEY}, wide even spacing, no extra text. "
            "The glyphs A, K, Q, J, 10, each a big bold bevelled 3D letter made of lacquered material with a thin metal edge, a dark outline "
            f"and a flourish of {t.get('rank_flourish', 'ornament from the theme motifs')} worked into the letter shape. "
            "Fixed colour per rank so ranks read by colour alone: " + ", ".join(f"{g} = {c}" for g, c in RANKS)
            + ". Same size, same bevel depth, same outline style for all five. The glyphs must be clearly legible.")),
        "symbols_special": dict(w=1792, h=768, group="special", anchor=False, call=6, part=(
            f"Sprite sheet of three special video slot symbols in one row on a {KEY}, wide even spacing, no text anywhere. "
            f"(1) WILD: a square framed tile, {t.get('wild', 'a glowing crystal inside an ornate frame')}, an empty round badge in the bottom-right corner left blank for a number. "
            f"(2) SCATTER: {t.get('scatter', 'a round mandala medallion with a large glowing pearl')}, a clearly different silhouette from the Wild (round, with petals or rays). "
            f"(3) BONUS: {t.get('bonus', 'an open treasure chest spilling gold')}, tall silhouette. "
            "Each is larger and more ornate than the normal premium symbols, same lighting and outline style."
            + (" Keep the Wild and Scatter inside their own frame or medallion even though the premium symbols have none, so special symbols stay unmistakable."
               if container == "freeform" else ""))),
        "hero": dict(w=1024, h=1024, group="character", anchor=False, call=7, part=(
            f"Single full-body character for a video slot game, centred on a {KEY}, no text. Original character: {t['hero']}. "
            "Dynamic confident pose, slight three-quarter view, whole figure visible from head to feet with space around it. "
            "The character will stand outside the reel window, left of the grid.")),
    }
    # Thumbnail layers for the Stake Tile Editor (background, foreground, gradient, title). The tile must be BRIGHT and have
    # no dark edges, so the dark-and-cool rule of the in-game grammar is dropped from the prefix. The gradient and the title are made
    # in the Tile Editor (the title is live text), so only background and foreground are generated. Square size is a placeholder:
    # read the real size and guidelines in the dashboard.
    tile_prefix = re.sub(r"Colour base:[^.]*\.\s*", "", re.sub(r"About 70 percent[^.]*\.\s*", "", prefix)) + " Bright, high-key, saturated, luminous colours; no dark corners, no vignette."
    spec["tile_background"] = dict(w=1024, h=1024, group="tile", anchor=False, call=8, optional=True, thumb=True, part=(
        "Game tile background, no characters, no text. A simple, uncluttered scene or abstract pattern from the theme with a luminous light-to-warm "
        "colour gradient, centre lighter than the edges, no dark areas anywhere, soft shapes so a character and a title can sit on top. Square."))
    spec["tile_foreground"] = dict(w=1024, h=1024, group="tile", anchor=False, call=9, optional=True, thumb=True, part=(
        f"Game tile foreground, a single key figure centred on a {KEY}, no text. The hero of the game, large, filling about 80 percent of the height, "
        f"strongest contrast and most detail in the centre of the image, bold readable silhouette: {t['hero']}. Leave the top 20 percent empty for the title."))
    return prefix, spec, P, container, tile_prefix


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("theme", nargs="?"); ap.add_argument("--out", default="art")
    ap.add_argument("--preset", default="valkyrie", choices=PRESETS)
    ap.add_argument("--example", action="store_true")
    a = ap.parse_args()
    if a.example:
        print(json.dumps(EXAMPLE, indent=2, ensure_ascii=False)); return
    if not a.theme:
        ap.error("theme.json required (or --example)")
    theme = json.load(open(a.theme))
    prefix, spec, P, container, tile_prefix = build(theme, a.preset)
    os.makedirs(os.path.join(a.out, "prompts"), exist_ok=True)
    pal = theme.get("palette", P["palette_default"]); warm = theme.get("warm_accent", P["warm_default"])
    style = {
        "theme": theme["title"], "preset": a.preset, "palette": pal, "warm_accent": warm, "light": "top-left",
        "premium_container": container, "readability_rule": CONTAINERS[container]["read"],
        "style_lock": {"model": "set once and never change within a set", "prefix": prefix, "key": KEY,
                       "aspect": {"backdrop": "16:9", "sheet": "7:3", "single": "1:1"}},
        "style_check": {"groups": {"symbol": ["symbols_*", "sym_*", "rank_*"], "background": ["backdrop*", "board*"], "tile": ["tile_*"],
                                   "frame": ["frame*"], "character": ["hero*"], "special": ["wild*", "scatter*", "bonus*"]},
                        "tolerances": P["tol"], "exempt": {}},
    }
    json.dump(style, open(os.path.join(a.out, "style.json"), "w"), indent=2, ensure_ascii=False)
    plan = []
    for name, s in sorted(spec.items(), key=lambda kv: kv[1]["call"]):
        text = (tile_prefix if s.get("thumb") else prefix) + " " + s["part"]
        open(os.path.join(a.out, "prompts", name + ".txt"), "w").write(text + "\n")
        plan.append({"call": s["call"], "asset": name, "width": s["w"], "height": s["h"], "group": s["group"],
                     "anchor": s["anchor"], "prompt_file": f"prompts/{name}.txt", "save_as": f"layers/{name}.png",
                     "cut_out_magenta": name not in ("backdrop", "board", "tile_background"),
                     **({"optional": True, "note": "Stake tile: check with scripts/tile_check.py; compose the gradient and the live title in the Tile Editor"} if s.get("optional") else {})})
    json.dump({"preset": a.preset, "order_note": "generate anchors first (anchor=true), have the user approve them, then the rest; "
               "run style_check.py after each call; max 3 regenerations per asset", "plan": plan},
              open(os.path.join(a.out, "plan.json"), "w"), indent=2)
    print(f"wrote {a.out}/style.json, {a.out}/plan.json and {len(plan)} prompts")
    for p in plan:
        print(f"  {p['call']}. {p['asset']:16} {p['width']}x{p['height']}  anchor={p['anchor']}")


if __name__ == "__main__":
    main()
