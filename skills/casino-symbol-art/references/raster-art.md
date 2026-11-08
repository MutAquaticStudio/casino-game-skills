# Painterly raster art with code (claude-drawing)

`vendor/claude-drawing/` (MIT, from cloveric/claude-drawing-skill) is a numpy + Pillow painting
library: 83 modules, 82 styles, each with a runnable scene in `examples/`. No image model, no
GPU, no network; the same seed gives the same picture. It fills the gap SVG leaves: textured,
painterly, print-like looks.

**What it is for, honestly.** Each module paints a whole scene on paper or a backdrop (a 1920x1080
render takes ~10 s or more). It is not an icon generator. Use it where a full picture is the
asset; for symbols use the two routes in §3.

## 1. Where it fits
| Asset | Fit | Notes |
|---|---|---|
| Base / bonus background | Best | Calm, low-contrast area behind the reels; render 2 layers (far + near) for parallax; keep the centre quiet |
| Win-title / splash scene, loading screen, thumbnail, key art | Good | Needs a safe area for text; draw the title as SVG paths or bitmap font on top, not inside the render |
| Texture sheets (paper, stone, leather, canvas) for reel frame and panels | Good | Crop or tile; check seams yourself, the library does not guarantee tiling |
| High-pay symbol | Possible | Route A or B below; painterly detail must survive 140 px |
| Low pay, card ranks, HUD icons | Poor | Use SVG (`svg-craft.md`); thick simple shapes read better |
| Animated symbols | No | Raster stills only. `--stages` writes draw-on snapshots for marketing GIFs, not for the game |

## 2. Pick a style by theme
Read the style's own docstring (`head -20 vendor/claude-drawing/lib/<module>.py`), then copy the
closest `examples/<name>.py` and edit it. Modules that suit slot themes:

| Theme / mood | Modules |
|---|---|
| Glossy / flat casino, clean shapes | `flatvector`, `soft3d` (candy balls, puffy letters), `popart` |
| East Asian, ink, lacquer | `inkpaint`, `ukiyoe`, `jiangnan`, `papercut`, `shadowpuppet` |
| Ancient / treasure / myth | `tomb` (Egyptian), `mosaic` (Roman), `stainedglass`, `illuminated`, `petroglyph`, `cave` |
| Painterly fantasy | `oilpaint`, `watercolor`, `gouache`, `storybook`, `dreamhills` |
| Cartoon / comic / mascot | `cartoon`, `comic`, `rubberhose`, `anime`, `sticker` |
| Retro / neon / sci-fi | `synthwave`, `cyberpunk`, `crt`, `vhs`, `pixelart`, `lowpoly`, `isometric` |
| Print / poster | `artdeco`, `constructivism`, `linocut`, `letterpress`, `bauhaus`, `stencil` |

Full list with notes: `vendor/claude-drawing/docs/STYLES.md`. API and the per-style list of real
failure modes: `vendor/claude-drawing/GUIDE.md` (Chinese; §2 API, §3 failure checklist). It is
~700 KB: do not read it whole; `grep -n '^### ' GUIDE.md` and read only the module you use.

## 3. Making symbols
**Route A, transparent sheet (best for symbols).** `sticker.Art` draws flat-vector shapes on a
transparent canvas (masks `circle/ring/ellipse/rrect/poly/blob/line/text`, then `fill`,
`gradient`, `radial`, `speckle`, `texture`). Export to RGBA:
```python
import sys; sys.path.insert(0, "references/vendor/claude-drawing/lib")
import numpy as np
from PIL import Image
from sticker import Art
a = Art(512, 512, seed=3)
gem = a.poly([(256,50),(430,190),(380,430),(130,430),(82,190)])
a.gradient(gem, '#ff5a7a', '#8a0f3c', (256,50), (256,430))
a.fill(a.circle(190,150,28), '#ffffff', 0.7)
rgb = np.where(a.a[..., None] > 1e-4, a.rgb / np.maximum(a.a[..., None], 1e-4), 0) * 255   # un-premultiply, 0-1 -> 0-255
Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a.a * 255]).astype(np.uint8), "RGBA").save("art/svg/ruby.png")
```
(Art stores premultiplied colour in the 0-1 range (`hexc()` divides by 255), so un-premultiply and then
scale by 255; without `* 255` every pixel comes out black.)

**Route B, paint on a key colour, then cut out.** Paint the symbol in any module on a flat
background that does not appear in the symbol (magenta `#ff00ff` works), then:
```bash
python3 scripts/raster_cutout.py art/raw art/svg --cell 512 --key "#ff00ff"
```
It flood-fills from the border (same colour inside the symbol is kept), feathers and
decontaminates the edge, crops and centres into a square cell. Without `--key` it samples the
corners. Raise `--tolerance` for soft or textured backgrounds, lower it if the symbol loses its
rim. Look for halos on the dark and light checker in the preview.

Then the normal pipeline accepts the PNGs next to or instead of SVGs:
```bash
python3 scripts/svg_to_atlas.py preview art/svg --out art/preview.png --shrink 140
python3 scripts/svg_to_atlas.py build   art/svg --out public/assets/symbols --size 160 --scales 1,2
```
`lint` and `layers` still read SVG only. A symbol that exists as both `x.svg` and `x.png` uses
the SVG. Raster symbols cannot be split into Spine layers; if a symbol needs a win animation,
paint the parts as separate PNGs (one per layer) or draw it as layered SVG.

## 4. Quality loop (from the library's own method)
1. Plan composition: focal point, space left for text, one accent colour.
2. Copy the nearest example, edit the scene script.
3. Render, **open the PNG and look**, check against the style's failure list in `GUIDE.md` §3.
   Two to four rounds; keep older renders as `_v1`, `_v2`.
4. Judge at real size: run the result through `preview --shrink 140` and `--shrink 40`.
   Painterly texture that looks rich at 512 px often turns to mud at 140 px; simplify before
   adding detail.
5. Greyscale test, same as for SVG: Wild, Scatter and Bonus must still differ without colour.

## 5. Constraints and pitfalls
- **Originality.** Output must be original art. Do not reproduce a named artist's work, a
  known character or a stock image; styles are techniques, not licences. Upstream example
  scenes are study material only.
- **Consistency.** One module per set (or two at most). Mixing a painterly and a flat set is the
  same drift as skipping `style.json`; lock the module, palette and seed policy there
  (`"engine": "claude-drawing/<module>"`, `"seed"`).
- **Fonts.** Titles in the library need a CJK or Latin system font and no font file is bundled.
  Do not paint game text into backgrounds or titles; localisation needs live text (bitmap font
  or SVG paths per language). Leave the area empty.
- **Size.** Renders are opaque RGB at the size you ask for. Export backgrounds as WebP/JPEG at
  the real stage size (x1 and x2) and check the build against the Stake size rules in
  `stake-casino-game-dev`. Do not ship 1920x1080 PNGs.
- **Speed.** Heavy modules take a long time at full size. Iterate at half size, then render
  the final at full size with the same seed.
- **Static build.** Files are used offline; no CDN fonts or remote images, same as SVG.
