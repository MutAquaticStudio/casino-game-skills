# Style study: Valkyrie Studio and Hacksaw Gaming

Use this when the user asks for "premium slot art like Valkyrie / Hacksaw". It captures
**principles and measurements**, not their characters or logos. Stake rejects copied art, so
never reproduce a named character, mascot or logo (a red panda in a number-10 shirt, Odin, a
raccoon in a green hat are theirs). Take the structure, build an original subject.

Sources: demos of Valkyrie Loki's Vault, Angel of Asgard and Red Strike played in a headless
browser on 2026-11-08 (screenshots, 901×505 game frame, palettes measured from the frames);
Hacksaw official cover thumbnails (20 titles). Hacksaw in-game demos could not be played
(wallet connection error from third-party launchers), so Hacksaw in-game claims below come from
public write-ups, not from pixels. Re-check against fresh screenshots when the user supplies them.

## 1. Valkyrie Studio (Norse / dark fantasy, "cinematic")

**Scene structure (back to front)**
1. Painted backdrop, 3–4 depth layers: far mountains → mid forest/fog → near rocks/props.
   Loki's Vault: snowy peaks, dead trees, cold haze. Angel of Asgard: violet aurora sky, red
   moon, pink-lit snow, longship at the edge.
2. Hero character or mascot standing **outside** the reels on the left, large (≈ 40–50% of the
   frame height), overlapping the frame edge slightly. Painted, soft rim light.
3. Heavy reel frame: carved stone (rune pillars, thick lintel) or metal. Snow or moss on the
   top edge. Frame is darker than the backdrop so the reels read as a "window".
4. Reel board: near-black tile (#12161c–#1b1424) so symbols pop. Faint engraved pattern only.
5. Symbols nearly fill the cell. High pays sit in a **roundel** (round metal/leather medallion
   with a gold or silver ring), which gives every premium the same silhouette family.
6. Control bar: flat dark panels, small caps labels, one big circular spin button (white arrow
   ring), minimal line icons. No ornament here; all ornament is spent on the frame.
7. Logo top-left, bevelled metallic/gold lettering with a dark outline, sits on the backdrop.
8. Multiplier plate (stone/metal) centred above the reels; Red Strike uses a horizontal track
   of x1…x128 tokens with a gold ring on the active step.

**Palette (measured)**
| Game | Darks | Mids | Lights / accent |
|---|---|---|---|
| Loki's Vault | #12161c, #1b1f29, #2d2532 | #555767, #2d3d4f, #7e95a5 | #c4d3d9 snow; gold ring accents |
| Angel of Asgard | #1b1424, #2f333f | #43124f, #801559, #803776 | #b5aaac ivory; gold hammers, red moon |
| Red Strike (cartoon branch) | #041d5d, #0d2852, #3d303d | #1e5983, #678a8f | #afc7cf; grass green, red/white kit |

Rule: 70% cool, desaturated darks and mids; the warm colour (gold, orange, red) is reserved for
value (premium symbols, scatter glow, win highlights). Angel of Asgard swaps cool for magenta
but keeps the same split: dark violet field, one warm metal accent.

**Symbol language**
- Card ranks are not flat letters. Each rank is a bevelled, themed glyph with a **fixed colour
  per rank** (Loki: A gold, K purple, Q red, J ice-blue; Angel: teal/red/purple outlines with a
  white highlight). The colour code lets players read ranks without reading letters.
- Premiums are objects in roundels: axe+shield, horned helmet, hammer, raven, bearded god in a
  framed portrait tile. Gold/red accents on a dark metal body; light from top-left; thin dark
  outline; one specular hit.
- Scatter/special: glowing orb with a swirling inner light inside a dark ring. Different
  silhouette (round, cold glow) from the warm premiums.
- Typeface: chunky fantasy serif/rune style with a 3D bevel for the logo; clean sans for UI.

**Branch: cartoon sports (Red Strike, Waylanders Cup)**: brighter saturated blues, grass
green, textured symbols (ball-pattern letters), oversized props, large expressive mascot,
stadium crowd as soft backdrop. Same structure (backdrop → mascot outside frame → board).

## 2. Hacksaw Gaming (house discipline, not one look)

From the 20-cover sheet. There is **no single rendering style**; the catalogue spans:
- Rubber-hose monochrome with one cyan accent (666).
- Low-poly / papercut on paper texture (Frutz).
- Pastel flat vector (Blocks, Colors, a sheep-dot-grid scratchcard).
- Neon graffiti / street (Klowns, Nitro Nights).
- Gritty painted realism with a glowing eye or accent (Hand of Anubis, Bloodthirst, 2 Wild 2 Die).
- Chunky chibi cartoon with a big face (Pug Life, Tiger Legends, Le Prechaun-type heroes).
- Glossy 3D slot-machine look (Max Win Machine).

**What stays constant (copy this, not a look):**
1. **One hero**: a single character or object, centred, big, with an exaggerated expression.
2. **Title lettering is the art**: thick, gradient-filled, heavily outlined, sometimes tilted or
   stacked; it carries as much weight as the character.
3. **High contrast, narrow palette**: 4–6 colours per game, one dominant hue family, one
   complementary pop. Reads at 250 px thumbnail size.
4. **Flat or lightly shaded**: strong outline and big shapes beat fine rendering. Detail is
   spent on the face and on the key props.
5. **Portrait-first**: composition survives a phone held upright.
6. **Theme-true texture**: paper for papercut, halftone dots for comic, grain for gritty.
   The texture is applied to the whole kit (symbols, frame, UI), so the world feels coherent.
7. Animation (public write-ups, not verified here): purposeful, with weight, anticipation and
   impact; no decorative idle motion.

## 3. How to apply this when generating assets

1. Pick the branch first: **Valkyrie-cinematic** (painted depth, roundel premiums, cool field +
   warm value) or **Hacksaw-bold** (one hero, chunky outlined lettering, flat, narrow palette).
   Do not blend them inside one game.
2. Write the choice into `art/style.json` with: palette (6–8 hex, mark which one is the warm
   "value" colour), outline width/colour, light direction (top-left), roundel Y/N, rank colour
   code Y/N, title lettering spec.
3. Build in this order: logo + frame → board tile → high pays → rank glyphs → scatter/wild →
   backdrop layers → mascot/hero. Frame and board decide how dark and how cool everything else
   must be.
4. Check at the real size (symbol ≈ 90–110 px on the 901×505 frame; 400×225 popout). Premiums
   must still differ in silhouette; ranks must differ by colour alone in greyscale-squint test.
5. Original subject, same grammar. Replace Norse props with the user's own theme (e.g. Viet
   myth: lacquer + gold, dragon-scale roundels, lotus scatter). Do not reuse their characters.

## 4. Quality bar checklist
- [ ] Backdrop has ≥ 3 depth layers with decreasing contrast toward the back.
- [ ] Frame is the darkest, most ornamented element; control bar is the plainest.
- [ ] One warm accent family only, used for value.
- [ ] Every premium has a distinct silhouette in a common container (roundel or tile).
- [ ] Rank colours are fixed and unique.
- [ ] Logo is bevelled, outlined, and readable at 40% size.
- [ ] Hero/mascot sits outside the reel window and does not cover any symbol.
- [ ] No text as `<text>`; no copied character, logo or brand.

## 5. Studio-wide template and catalogue survey (Valkyrie, 10 public demos played)

Played or screenshotted: Loki's Vault, Angel of Asgard, Red Strike, Castle of Ymir, Four-Leaf
Fortune, High Elf, Waylander's Forge, Wings of Valhalla, Tiki Wiki Wild, Tome of Hades, Tome of
Hercules, Waylanders Cup. About 40 other titles listed on the studio site have no public demo.

**The template never changes; only the art theme does.** This is what makes a catalogue look like
one studio.
| Slot | Fixed position / behaviour |
|---|---|
| Logo | top-left (or top-centre on the frame for Four-Leaf Fortune, High Elf), bevelled, outlined |
| Hero / mascot | big, full body, left of the reels (right on Tome series), partly overlapping the frame |
| Frame | themed material wrapping the grid: carved stone/ice, timber, vines, iron, marble |
| Reel board | dark tile, grid varies (5×4, 6×4, 6×5, 7×7, 5×5) |
| Side widget | one framed panel for a mechanic (wild upgrade table, multiplier plate, orb meter) |
| Bottom bar | identical in every game: bonus-buy icon, menu, balance, win, bet stepper, autoplay, big circular spin button |
| Backdrop | full painted scene, one clear location per game |

**Observed range per theme (copy the range, not the content):**
- Ice/Norse: desaturated blue-grey, snow on frame, rune carving (Loki, Castle of Ymir).
- Aurora/valkyrie: violet-magenta sky, red or cyan moon, warm gold on metal (Angel, Wings).
- Fairy-tale pastoral: saturated greens/orange, rainbow, mushrooms and flowers in the foreground
  (Four-Leaf Fortune, High Elf), timber frame with vines.
- Underworld/Greek: dark stone, torches, red/blue gemstone symbols, hero on the right (Tome series).
- Tropical: tiki totem mascot, fruit symbols, bamboo frame (Tiki Wiki Wild).
- Sport/cartoon: stadium crowd backdrop, grass, kit-coloured symbols, mascot (Red Strike, Waylanders Cup).

**Symbol families observed:** card ranks as themed glyphs with fixed colour per rank; premiums
as objects in a consistent container; gems as faceted shapes in 4–5 hues (Tome series); Wild as
a framed glowing tile carrying a multiplier badge (x5, x10, x15) in an ice-blue or gold variant;
Scatter with a text tag ("SCATTER", "SUPER SCATTER") on the symbol.

**Not captured, do not assume:** the win celebration (big-win titles, count-up, coin bursts) and
bonus-round transitions. The recording only caught base-game spins with small wins; the studio
site then stopped serving the game frame (rate limit) before the bonus-buy menu could be opened.
Treat celebrations as an open item; verify with a fresh capture before writing a spec.

## 6. Reaching painted quality: what an agent can and cannot do

The art above is painted semi-realistic illustration. Code-drawn SVG cannot reach it; the gap is
in the rendering, not in the planning. A realistic pipeline for an agent:
1. Lock the template (table in §5) and the style guide (`art/style.json`) first.
2. Generate **separate layers** with an image model, never one flat screenshot: backdrop (no
   UI), hero on a flat key colour, frame (empty centre), each premium symbol on a flat key colour,
   logo. One prompt per layer, same style sentence reused verbatim, same light direction.
3. Cut out with `scripts/raster_cutout.py`, normalise to the cell size, pack with
   `svg_to_atlas.py`-style atlas export, wire in Pixi (`export-and-pixi.md`).
4. Draw by code what code does well: bottom bar, bet stepper, spin button, rank glyphs,
   multiplier badges, win text, particles.
5. Judge at real size against the checklist in §4. Reject and regenerate any layer whose
   silhouette, palette or light direction drifts from the guide.

Limits: image models drift between calls (palette, outline weight, light), so consistency
needs the same reference image passed to every call plus a rejection loop; transparent
backgrounds usually need a key colour and a cutout; originality still has to be checked (no
known characters, no studio logos). Generation costs credits per call: ask before spending.
Status: run end to end once (2026-11-08, original Vietnamese-myth theme, Figma `generate_image`
with `gpt-image-2.5-flare`, 4 calls, no reference image). Result: backdrop, hero, frame and an
8-medallion symbol sheet all came out at painted quality in one shot each, and a code-composited
screen (`scripts/compose_layered_screen.py`) reached Valkyrie-like layout and finish. What was
learned:
- Ask for the reel opening and the background of hero/symbols as **flat pure magenta (#FF00FF)**.
  Key it with a *strict* test (R>175, B>175, G<115, |R-B|<60, plus a 2 px halo only on pinkish
  pixels). A loose colour-distance key eats lacquer reds/purples and leaves the frame speckled
  with backdrop colour (first attempt failed this way).
- One 4×2 sheet of symbols in a single call gave a consistent family (same ring, same light).
  Split the sheet by connected components after closing small gaps.
- Request the frame with an **empty magenta window**, then fill that window with a dark tile in
  code and composite the frame on top of the symbols.
- Reel board is its own layer: generate a dark texture with a **faint engraved motif** (10–15%
  contrast, centred ring fading to the edges) and add **column dividers** (thin gold line with a
  dark shadow either side) plus an inner edge vignette. Valkyrie boards are near-black but never
  flat: Loki has an engraved ring, Red Strike a hex pattern, Tome of Hades/Hercules and Waylanders
  Cup have metal or groove dividers between columns. A plain fill (first mockup) reads as unfinished.
- Draw by code: bottom bar, balance/win/bet text, spin button. The placeholder spin button in the
  script is crude; replace it with a generated or hand-built icon.
- Still open: reference-image conditioning for cross-call consistency (not tried), win
  celebration art/animation, Spine-ready layer splitting of the hero, multi-theme repeatability.
- Cost: ~4 generation calls for one screen. Always ask before spending credits.
