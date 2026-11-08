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
