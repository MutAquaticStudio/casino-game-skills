---
name: "casino-symbol-art"
description: "Create and export 2D art for casino/slot games on PixiJS: slot symbols (low/high pay, Wild, Scatter, Bonus, card ranks), state variants, win-title art, reel frames, backgrounds and icons as layered SVG or painterly raster (code-painted, 80+ styles), with a style guide, readability checks at real reel size, lint for Stake-safe files, background cutout, and spritesheet export for Pixi v8. Use for any request to design, draw, redo or produce symbols or other 2D assets for a slot, even if the user does not say SVG or Pixi."
---

# Casino symbol art

Players judge a slot by its art in the first two seconds, and Stake reviewers reject art that is
not unique. This skill produces the assets: a style guide, layered SVG symbols, a checked
preview, and a Pixi-ready atlas. `casino-game-audit` scores the result;
`stake-casino-game-dev` wires it into the game (§12 Pixi, §8 win celebrations). Answer in the
user's language; keep file names, code and Stake terms in English.

**Hard constraints (Stake approval)**
- Unique, IP-clean art. No copyrighted characters, logos or mascots, no Stake/Kick branding, no
  Web SDK sample assets. If the user asks for a known character or brand, decline that part and
  offer an original design with the same spirit.
- Static build: assets under relative paths, no remote images, no font CDNs. Text becomes
  paths (or a bitmap font), never `<text>`.
- Readable in the 400×225 popout and on a phone: judge every symbol at its real on-screen size.

**What this makes, and what it doesn't.** Three routes. **Vector SVG** (default): flat, glossy
casino, bevelled gems and coins, ornate frames, card ranks, icons, themed titles. **Code-painted
raster** (`references/raster-art.md`): textured looks such as ink, oil, watercolour, mosaic,
stained glass, comic, pixel art, mostly for backgrounds and title scenes, and for high-pay
symbols via a transparent sheet or cutout. **Model-generated layers**
(`references/style-valkyrie-hacksaw.md` §6): painted semi-realistic art at the level of
studio-grade slots (backdrop, hero, frame, board, symbols), one image-model call per layer,
keyed out and composited by code. Use it only when an image-generation tool is available and the
user has agreed to the cost; otherwise fall back to the first two routes, which do not replace
true hand-painted art. For that look without a generator, write an art brief for an artist (see
`references/symbol-design.md` §7) and use this skill for the pipeline.

| Need | Route | Read |
|---|---|---|
| Symbols, icons, frames, flat or glossy look | SVG | §3 below, `references/svg-craft.md` |
| Background, win-title scene, loading screen, key art, textured look | Raster | `references/raster-art.md` |
| High-pay symbol with painterly texture | Raster (transparent sheet or cutout) | `references/raster-art.md` §3 |
| "Premium slot look", "like Valkyrie / Hacksaw": scene structure, palette split, roundel premiums, rank colour code | Either | `references/style-valkyrie-hacksaw.md` §1–5 (principles only; never copy their characters or logos) |
| Painted, studio-grade art (backdrop, hero, frame, board, full symbol set) | Model-generated layers | `references/style-valkyrie-hacksaw.md` §6, `scripts/compose_layered_screen.py`, `scripts/build_symbol_set.py` |

## 1. Style guide first
Lock these before the first symbol, then save them as `art/style.json` so every later asset
reuses the same values. Skipping this is the main reason a set looks like five different games.

| Field | Decide |
|---|---|
| Theme + mood | one line, e.g. "Viet myth, warm lacquer and gold" |
| Render style | flat · glossy casino (rim light + gradient + gloss) · outlined chibi |
| Palette | 6–8 hex values + one accent reserved for Wild/Bonus |
| Outline | width on the source canvas and colour (dark tone of the fill, not pure black) |
| Light | one direction for every highlight and shadow (default top-left) |
| Canvas | symbol cell on the source art, e.g. 256×256 with ≥ 8% padding for glow |
| Real size | on-screen px of a symbol (e.g. 140) and the popout size; this is the readability target |

Palette starters per theme and a `style.json` template: `references/symbol-design.md` §1.

**Theme harness (model-generated route):** `scripts/art_harness.py theme.json --out art` turns a
theme (place, hero, 8 premium objects, palette) into `art/style.json` plus one locked prompt per
layer, with the studio-grade structure built in (presets `valkyrie`, `hacksaw`). Premium symbol
container is a theme choice, `premium_container`: `roundel` (shared round medallion), `tile`
(rounded square) or `freeform` (each symbol its own frameless silhouette). For `freeform`, run
`scripts/silhouette_check.py` and fix any pair above IoU 0.80 before compositing. The harness
refuses brand or studio names in the theme.

**Symbol animation in code:** `scripts/symbol_fx.json` + `symbol_fx.mjs` hold drop_in, land, win, win_loop, appear, tease (and optional dim, idle) recipes as
data (no Spine needed); `scripts/symbol_fx_preview.py` checks them and renders a demo video. Usage and status: `references/symbol-fx.md`. The `win` shape,
the board-cycle timing and the bonus flow come from measuring a reference game's demo: `references/animation-timing.md` (timing and structure to reuse, never their art);
`scripts/anim_probe.py` repeats that measurement on any demo recording or on our own build.

**Mascot placement on PC:** the mascot stands on ONE outer side of the board (a column of about 20% of the width and 60 to 90% of the height, full body, feet near the dock line; in the reference studio 5 of 9
games left, 3 right), the feature meter or panel on the opposite side, the logo above the mascot or centred on the frame top. Choose the side once per game; wireframes and measures:
`stake-casino-game-dev/references/layout-wireframes.md`. The same mascot art then has to work as a bust on the phone (below).

**Phone portrait composition (art deliverables):** the reference game ships one asset set and recomposes it for PC and phone at runtime, so build the art to be recomposed
(`stake-casino-game-dev/references/mobile-ui.md`): the **mascot must read as a bust** (face, shoulders, held item and companions in the top 60 percent of the figure) because on a phone only that part shows above the
board frame and the lower body is hidden behind it; the **feature meter is made of parts** that can sit in a vertical panel on PC and a horizontal bar on a phone; the **background is layered** (sky, middle, ground,
plus a detailed ground band for tall phones) so the crop can change, with the key scene in the middle and 15 percent of spare art at the top and bottom; the logo works small, next to the mascot. Plan a hero zone of 16 to 25 percent of
the phone's height and a decorated scene band of 11 to 13 percent below the meter. Check a composition with `stake-casino-game-dev/scripts/mobile_layout.py`.

**Style lock (required for the model-generated route, useful for all):** add a `style_lock` block
to `style.json` (model, verbatim prompt prefix, key colour, aspect per asset type), paste the
prefix first in every generation prompt, generate anchors first, and run
`scripts/style_check.py` before compositing. Protocol and measured results:
`references/style-valkyrie-hacksaw.md` §7.

## 2. Plan the set
List every asset with its role before drawing. Role sets the detail level and the visual weight.

| Tier | Typical count | Treatment |
|---|---|---|
| Low pay (card ranks or simple glyphs) | 4–5 | Flat, one or two colours, thick shapes, least detail |
| High pay (theme objects/characters) | 4–5 | More detail, richer gradient, rim light |
| Wild | 1 (+ variants) | Accent colour, glow, fills the cell |
| Scatter / Bonus | 1–2 | Unique silhouette, distinct from Wild even in greyscale |
| Specials from the concept (multiplier, coin, mystery) | per design | Follow the mechanic; show its value legibly |

Every symbol needs the states the Pixi `SymbolView` uses (`idle | spin | land | win | dim`,
see `stake-casino-game-dev` §12.3). Most states are code (blur, scale, tint, glow). **Win-state art (deliverable):**
the `win` recipe (`scripts/symbol_fx.json`, shape measured in `references/animation-timing.md`) needs three shared sprites that match the set's style:
a **flash disc** (soft bright circle), a **glow ring** and a **glint** (small star sparkle); premium symbols may also get a "lit" variant (brighter, more saturated, the
glass-like glow state). Everything else (drop in, land, scale, timing) is code. Do not draw dim or idle variants unless the design asks for them. Details and timings:
`references/symbol-design.md` §4; round timing and rules: `stake-casino-game-dev` §8.5.

## 3. Draw each symbol as SVG
One file per asset, `art/svg/<name>.svg`:
- Fixed `viewBox` shared by the whole set (e.g. `0 0 256 256`). A mixed set cannot be packed
  with consistent anchors.
- Named layers as `<g id="body|shade|highlight|glow|detail">`. These names let the same file be
  split into layers later for Spine or frame animation, so use them even for static symbols.
- Gradients, filters and clip paths get an id prefixed with the file name (`ruby-body`).
  Duplicate ids make colours wrong when SVGs are inlined or merged.
- Filter regions wide enough (`x="-20%" y="-20%" width="140%" height="140%"`) and a canvas
  with padding, otherwise glows are cut to a hard box.
- Use palette values from `style.json`; do not invent hex codes mid-set.
- Silhouette first: the shape must identify the symbol before colour or detail does.
- Hard parts (arc flags, gradients, masks, filters, icon grids, SVGO without breaking layer
  ids): `references/svg-craft.md` routes to the vendored svg-design guides and lists where this
  skill overrides them.

## 4. Check before showing anyone
```bash
python3 scripts/svg_to_atlas.py lint    art/svg
python3 scripts/svg_to_atlas.py preview art/svg --out art/preview.png --cell 256 --shrink 140
```
`lint` flags remote references, `<text>`, scripts, missing viewBox, id collisions and a mixed
canvas. `preview` draws each symbol full size on a checkerboard and again at the real reel size
on a dark strip. **Open `preview.png` and look at it**; code that renders is not the same as
art that works. Check:
1. Each symbol still reads at the real size (shrink strip) and at popout size. In a 400×225
   popout a 3–5 row board leaves roughly 36–60 px per symbol (assuming the board fills ~80%
   of the height), so re-run `preview` with `--shrink 40` as the harsh test.
2. Contrast against the reel background; nothing disappears into it.
3. Same light direction, outline width and level of finish across the set.
4. Hierarchy: high pay clearly richer than low pay; Wild and Scatter unmistakable.
5. Greyscale test: Wild, Scatter and Bonus stay distinguishable without colour.
6. No clipped glow or outline at the cell edge.

Send the preview to the user after the first two or three symbols, not at the end. Direction
changes are cheap early and expensive after twelve symbols.

## 5. Export for Pixi
```bash
python3 scripts/svg_to_atlas.py build art/svg --out public/assets/symbols --size 160 --scales 1,2
```
`build` and `preview` also pack raster symbols: any `<name>.png` (transparent RGBA) in the
folder is scaled to the cell and packed like an SVG; an SVG with the same name wins.
Writes `symbols@1x.json/.png` and `symbols@2x.json/.png`, TexturePacker-style JSON with
`meta.scale`, a default 0.5/0.5 anchor and untrimmed frames, so every symbol shares one cell.
Frame names are the file names (`ruby`, `wild`). Validated against PixiJS 8.22: `Assets` resolves
`symbols@{1,2}x.json` by device pixel ratio and sprites keep their logical size.

- **Pick `--size` from the real on-screen size**: logical cell ≈ on-screen px; the `@2x` file
  covers retina. A 140px reel symbol needs `--size 160 --scales 1,2` (320px sheet), not 256/512.
  Oversized cells are the usual reason an atlas will not fit.
- Atlas budget: ≤ 2048 px per side is safe on mobile, 4096 is the upper bound. The script says
  so and stops when a set does not fit; split base symbols from bonus symbols into separate
  atlases and bundles (`Assets.loadBundle('bonus')` lazily).
- `--format webp` is much smaller than PNG and fine for symbols. Add `--pot` only for tools that
  need power-of-two sides; the default is tight and a multiple of 4 (KTX2-friendly).
- Raster atlases beat live SVG in Pixi for reels (batching, no re-rasterising). Pixi's
  Graphics mode for SVG skips filters, clip paths and `<style>`, which glossy symbols rely on,
  so rasterise (`references/export-and-pixi.md` §4).
- Need a real animation (Spine or frames)? `python3 scripts/svg_to_atlas.py layers art/svg
  --out art/layers` exports each named `<g>` as a full-canvas PNG, already registered to the
  others, ready to import as Spine slots (`references/export-and-pixi.md` §6).

Loading code, a `SymbolView` sketch, Spine hand-off and the bundle layout:
`references/export-and-pixi.md`.

## 6. Other 2D assets
Same loop (style guide → SVG or raster → preview → export), different canvases. Sizes and rules per asset
are in `references/symbol-design.md` §6:
reel frame and board (9-slice friendly), background (≥ 2 parallax layers, kept calm behind the
reels), win-tier title art (Big / Mega / Epic / Legendary / Max Win, from `stake-casino-game-dev`
§8; asset list and style rules in `references/win-celebration-art.md`), HUD icons (follow the simplicity-first rule in §13.0 there), loading logo, thumbnail (tile: `references/tile-thumbnail.md`, check with `scripts/tile_check.py`).

## 7. Hand-off
Deliver the folder, not loose files: `art/motion.json` (a copy of `scripts/symbol_fx.json`, tuned; the round controller reads it), `art/fx/` (`flash_disc`, `glow_ring`,
`glint` sprites, plus premium "lit" variants), `art/style.json` (with `style_lock` for generated sets),
`art/prompts/` (final prompt per generated asset), `art/svg/` (SVG and any PNG symbols),
`art/preview.png`, the `style_check.py` report,
`public/assets/symbols*.{json,png|webp}`. Give two or three sentences: what was made, anything
that needs a decision (a symbol that fails the greyscale test, an atlas near the budget), and
one next step (animation pass, win title art, or running `casino-game-audit` on a build).

## Pitfalls
- No style guide, so the set drifts. Fix by writing `style.json` first.
- Generated set drifts between calls (palette, outline weight, light direction). Do not reword
  the prompt per asset: reuse `style_lock.prefix` verbatim, one family per call, same model,
  then run `style_check.py` and reject FAILs (max three regenerations, then fix in code).
- Judging symbols at 256px on a big monitor; they fail at 140px on a phone. Always view the
  shrink strip.
- Glow or shadow outside the viewBox gets cut. Pad the canvas.
- Duplicate gradient ids across files give the wrong colours.
- `@2x` file with `meta.scale` "1" (or the reverse) renders at the wrong size in Pixi v8; the
  script writes them consistently, so do not hand-edit the JSON.
- Many near-identical high-pay symbols. Vary silhouette and dominant colour, not just detail.
- Mixing routes or painting engines inside one symbol set. Pick SVG or one raster module per set
  and record it in `style.json`.
- Painted text in backgrounds or title art. Text must stay live (bitmap font or paths) for
  localisation; leave the area empty in the render.
- Halo of the key colour after `raster_cutout.py`. Re-run with a different `--key`, higher
  `--tolerance`, or paint on a key colour far from the symbol palette; check on dark and light.
- Copying an example scene or a reference image from the vendored toolkits as game art. Stake
  needs original art; the examples are for learning the API.
