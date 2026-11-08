# SVG craft for slot art (svg-design guides)

The vendored `vendor/svg-design/` guides (MIT, from tryopendata/skills, plugin `opendesign`) cover
how to write clean SVG by hand. This file says what to read for casino work and where the
guide's defaults must be overridden. The guide is written for icons and logos; a slot symbol is
an illustration with more layers and gradients.

Read `vendor/svg-design/GUIDE.md` once for the principle ("SVGs are code: clean, minimal,
every element earns its place"), then load only the reference that matches the problem:

| Problem | Read (under `vendor/svg-design/references/`) |
|---|---|
| Curves look wrong, arcs flip, rounded shapes | `path-patterns.md` (arc flag table), `advanced-techniques.md` |
| Gloss, rim light, gem facets, soft glow | `advanced-techniques.md` (gradients, masks, clips, filters) |
| Edit or merge an existing SVG, boolean shapes | `editing-workflow.md` |
| Small HUD / UI icons (bet, sound, menu, info) | `icon-design.md` (grid, pixel alignment, stroke width) |
| Loading logo, game logo, title lettering | `logo-techniques.md` (negative space, typography to paths) |
| File size, SVGO config | `optimization.md` |
| Render glitches across engines | `accessibility-and-pitfalls.md` |
| Animated SVG for a preview or marketing page | `animation.md` |

## Overrides for casino symbols

| Upstream default | In this skill |
|---|---|
| Logo process step 0: always ask design-direction questions first | Skip for symbols. `style.json` (SKILL.md §1) is the brief. Keep the idea of showing 3-5 distinct directions for a **game logo** or a hero symbol only if the user has not chosen a style |
| Preview via `assets/preview.html` + `variants.js` | Use `svg_to_atlas.py preview` instead; it shows the real reel size, which the HTML preview does not |
| `stroke="currentColor"`, 24x24 grid, 2px stroke | Icons only. Symbols use the shared 256x256 canvas, palette hex from `style.json`, outline width from `style.json` |
| Flatten transforms, strip all `id`s, SVGO defaults | **Keep** the named layer `<g id="body|shade|highlight|glow|detail">` and the file-prefixed gradient/filter ids. In SVGO set `cleanupIds: false`, `collapseGroups: false`, `removeHiddenElems: false`. Run `lint` after optimising |
| `<text>` is fine in-page, convert to paths for distribution | Always paths (Stake static build; no font fetch). `lint` errors on `<text>` |
| 2 decimals on icons, 3 max for complex art | Same; 1 decimal is fine at 256 canvas. Do not round gradient stops |
| CSS keyframe animation in the SVG, `<style>` blocks | Not for game assets. Pixi rasterises the atlas and ignores CSS animation; animate in code or Spine (`layers` export). Use it only for web previews or a landing page |
| `-dark.svg` variants for light/dark backgrounds | Not needed; reels have one background. A `dim` state is a code tint |

## Workflow with the lint/preview loop
1. Write the SVG using the guide for the tricky part (arcs, gradients, masks).
2. `svg_to_atlas.py lint` then `preview`; view the PNG, including the shrink strip.
3. Optimise only at the end and only if size matters (atlas export rasterises anyway, so
   SVG file size rarely affects the game; it matters for repo size and diffs).
