# Symbol design reference

Detail for `casino-symbol-art`. Sections are cited from `SKILL.md`.

## 1. Style guide template and palette starters

Save as `art/style.json` and read it before drawing anything.

```json
{
  "theme": "Viet myth, warm lacquer and gold",
  "render": "glossy-casino",
  "engine": "svg",
  "canvas": 256,
  "padding": 20,
  "realSize": 140,
  "popoutSize": 40,
  "light": "top-left",
  "outline": { "width": 8, "color": "#2a0f08" },
  "palette": {
    "ink":     "#2a0f08",
    "base":    "#8f1d14",
    "mid":     "#d4452a",
    "light":   "#ff9b6a",
    "gold":    "#f2c14e",
    "jade":    "#1f8a70",
    "accent":  "#ffd84a"
  },
  "accentRole": "Wild and Bonus only"
}
```

`engine` is `"svg"` or, for code-painted raster sets, `"claude-drawing/<module>"` (for example
`"claude-drawing/oilpaint"`) together with `"seed": <int>` so the set can be re-rendered
(`raster-art.md`). Keep one engine per set.

Palette starters (adjust to the concept; these are starting points, not rules):

| Mood | Base darks | Mids | Lights | Accent |
|---|---|---|---|---|
| Lacquer and gold (East Asian) | `#2a0f08` `#8f1d14` | `#d4452a` `#1f8a70` | `#ff9b6a` `#f2c14e` | `#ffd84a` |
| Deep ocean | `#06213a` `#0b4a6f` | `#12899b` `#7a3fa0` | `#6fe0d0` `#f4f1de` | `#ffb703` |
| Sand and turquoise (Egypt) | `#2b1d0e` `#7a4a1d` | `#d9a441` `#1b9aaa` | `#f6e2a8` `#fff6dc` | `#37e0c8` |
| Neon fruit | `#1b0b2e` `#42125f` | `#e63c8f` `#27c46b` | `#ffe14d` `#5ee7ff` | `#fff35c` |
| Frost and ember | `#0e1a2b` `#27425f` | `#5aa9e6` `#e4572e` | `#d7f0ff` `#ffb26b` | `#fff1a8` |

Rules that make a palette work in a reel: keep darks for outlines and shade, keep one accent
for the symbols that must pop (Wild, Bonus, special), and avoid giving two neighbouring pay
tiers the same dominant hue.

## 2. Set hierarchy and silhouette

Players scan the board for patterns and for specials. The art should make both effortless.

- **Detail budget by tier.** Low pay: 1–2 shapes, one outline, one highlight. High pay: 3–5
  shapes, rim light, an inner detail. Wild/Scatter/Bonus: the most saturated and the most
  distinct, never just a recoloured high-pay symbol.
- **Silhouette first.** Fill each symbol solid black and look at the set; every shape should
  still be a different thing. If two silhouettes are similar (two round coins, two shields),
  change the outline, not only the colour.
- **One dominant hue per symbol.** Within a tier, no two symbols share a dominant hue and
  value. Accent colour belongs to the specials.
- **Fill the cell consistently.** Keep the visual mass of every symbol within the same
  bounding area (roughly 70–85% of the canvas) so some symbols do not look smaller than others.
  Wild may exceed this; low pay may sit slightly below it.
- **Outline and light.** One outline width for the set, a dark tone of the fill rather than
  pure black, one light direction. These three carry most of "the set looks like one game".

## 3. Readability and contrast

- Judge at the real on-screen size, not on the source canvas. Shrinking a 256 px drawing to
  140 px erases fine detail; as a rule of thumb, strokes that end up under about 2–3 px on
  screen stop reading, so check the shrink strip rather than trusting the large view.
- Test again at popout size. In a 400×225 popout a board of 3–5 rows leaves about 36–60 px
  per symbol (assuming the board fills ~80% of the height). Use `preview --shrink 40`.
- **Value contrast.** Convert to greyscale: the symbol must separate from the reel background
  and its own parts must separate from each other. Colour alone is not enough.
- **Greyscale and colour-blind check.** Wild, Scatter and Bonus must differ by shape and
  value, not just hue (red/green pairs are the usual failure).
- **Background.** Test on the actual reel colour. A glow that looks great on a checkerboard can
  vanish on a bright reel, and a dark outline can vanish on a dark one. Put a thin light rim
  inside a dark outline when the reel is dark.
- **Numbers on art** (multipliers, coin values) get a backing disk or outline and use a bitmap
  font; thin text straight over art fails contrast.

## 4. States and timings

`SymbolView` states from `stake-casino-game-dev` §12.3. Most are code; draw art only where
noted. Timings are starting values to tune by feel.

| State | What it looks like | Art or code | Start values |
|---|---|---|---|
| `enter` | Symbol falls into its column, columns about 0.16 s apart left to right | Code (`drop_in` in `scripts/symbol_fx.json`) | 0.25–0.45 s per column; whole round about 1.0 s |
| `idle` | Static; the reference game's resting symbols did not move. Optional slow shimmer on special symbols only | Static art | Shimmer loop 2–4 s, low amplitude |
| `spin` | Vertical stretch or blur while the reel is fast | Code (scale.y), optional blurred variant in atlas | scale.y ≈ 1.06–1.1 |
| `land` | Small overshoot and settle | Code (`land`) | 150–300 ms, squash 1.10 x 0.88 then back to 1 |
| `win` | **One-shot emissive swap**: flash disc (0 to 0.16 s), glow ring (to 0.40 s), glint (about 0.40 s), fade (by 0.65 s); dimming the others is a per-game choice; high pay may add a drawn action on top | Code (`win`) plus three shared sprites: flash disc, glow ring, glint; a per-symbol "lit" variant only for premiums | about 0.65 s, measured on one reference game (`animation-timing.md` §2) |
| `win` (long) | Repeating pulse for a highlight that must stay on screen | Code (`win_loop`) | 0.6–1.2 s loop |
| `dim` | Optional: others recede. One reference game did not dim, another dimmed non-winners while the winners glowed | Code (tint and alpha) | alpha ≈ 0.35–0.5, tint grey |

Special symbols (Wild expand, Scatter land, Bonus trigger) usually need drawn animation. Plan
their layers early (SKILL.md §3); `svg_to_atlas.py layers` exports them for Spine.

Prefer tint and alpha over per-sprite filters for `dim`: filters break batching on a mobile GPU
(`stake-casino-game-dev` §12.4).

## 5. Special symbols

- **Wild.** Fills the cell, carries the accent colour, usually has the strongest glow. Readable
  as "substitute" at a glance (the word WILD as vector paths on a banner is common and clear).
- **Scatter.** A silhouette no other symbol shares. Players count scatters, so it must read in
  one frame, including while spinning.
- **Bonus.** Distinct from Scatter even in greyscale. If the game has both, give them different
  shapes (e.g. round vs angular), not just different colours.
- **Value symbols** (coin, multiplier, mystery). The value is the point: large numerals on a
  contrasting disk, in the game's bitmap font, with room for the longest value.
- **Card ranks (9, 10, J, Q, K, A).** One type treatment for all six, themed outline or fill,
  no pure white (it outshines high pay). They are the lowest tier: simple and quiet.
- **Original characters only.** Design theme characters from scratch. No known characters,
  brands or mascots, and no look-alikes of them.

## 6. Other 2D assets

Source canvases (design space 1920×1080 landscape unless noted; keep the same ratios for the
portrait layout):

| Asset | Canvas / guidance |
|---|---|
| Reel frame / board | Build as a 9-slice (fixed corners, stretchable edges), so one asset fits 3×3 to 7×7 boards. Keep the inner window flat and dark so symbols stay the brightest thing |
| Background | 2+ layers (far, mid) for parallax, 1920×1080 or wider, low contrast and low detail behind the board; bonus mode gets its own set |
| Win tier titles | One title per tier (Big, Mega, Epic, Legendary, Max Win) at ~1200×400, legible at 30% size, same style rules as symbols; each tier visibly richer than the last (`stake-casino-game-dev` §8) |
| HUD icons | Simple and few; follow §13.0 (simplicity first) in `stake-casino-game-dev`; 64–128 px source, outline icons need a backing disk |
| Logo / title | Vector paths, no live fonts; also a one-colour variant for loading screens |
| Thumbnail | Finished in Stake's Tile Editor. The approval checklist (`stake-casino-game-dev/references/stake-engine/approval-checklist.md`) asks for a bright tile that does not clash with Stake's background (watch dark edges), the key focus area filled, and the title inside the inner guidelines. Draw the art with that in mind; it does not give a pixel size, so take it from the editor |
| Particles (coins, sparkles, rays) | 64–128 px source, soft and additive-friendly, 3–6 variants so streams do not look cloned |

## 7. Art brief for an artist

Use when the user wants hand-painted or 3D-rendered art that vector cannot give. Keep it to
one page:

1. Game name, theme in one line, mood references (descriptions or the user's own links; never
   another studio's characters).
2. Render style and palette (paste `style.json`).
3. Asset list with tier, role and states needed (§2 table), and which need animation layers.
4. Technical spec: source canvas, padding, real on-screen size, popout size, light direction,
   outline rule, transparent PNG or layered PSD with named layers (`body`, `shade`,
   `highlight`, `glow`).
5. Readability tests the deliverable must pass (real size, popout, greyscale) and the
   uniqueness rule (no third-party IP).
6. Delivery: one folder per symbol, file naming (`ruby.png`, `ruby_win_01.png`), schedule.

`svg_to_atlas.py build` and `preview` read SVG and transparent PNG. For PNGs delivered by an
artist, put them in `art/svg/` (square, same canvas, transparent) and run `build`; if they
come on an opaque background run `scripts/raster_cutout.py` first. Raster symbols cannot use
the `layers` export, so ask for named layers as separate PNGs when a symbol needs animation.
TexturePacker or free-tex-packer also work, with the same settings as `export-and-pixi.md` §1
(padding, extrude, `@1x`/`@2x` naming, `meta.scale` matching the image).
