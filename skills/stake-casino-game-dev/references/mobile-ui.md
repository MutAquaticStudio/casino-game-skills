# Phone (portrait) UI: layouts measured on real games, what changes from PC, and a layout recipe

Why this exists: a game whose board is small and floats in the middle of a tall phone screen, with empty bands above it and between it and
the controls, looks unfinished. This file gives measured examples, what a good studio changes between PC and phone **beyond layout**,
and a recipe with tools. Everything is evidence from public demos plus two phone screenshots from the owner; thresholds are calibrated on
that evidence, not on a standard. Re-measure on your own build.

Method: Playwright with phone emulation (390x844 CSS px, device pixel ratio 2, touch, mobile user agent) on five public demos of one
studio, plus 360x800 and 375x667 for one of them, plus a PC viewport (1280x720); a phone screenshot of Odin's Vault taken by the game's owner
(366x710); and the owner's own game, Inkblade Ronin (780x1688 screenshot, measured by eye). Tools: `scripts/mobile_capture.mjs` (capture, request
logs), `scripts/mobile_layout.py` (`grid` to read rectangles, `report` to check them, `solve` to compute a layout). The measured rectangles of every game in the table are in `references/examples/mobile_specs/*.json`; run `report` on any of them to see the numbers (the screenshots themselves are not kept in the repo).

## 1. Measured phone layouts (percent of the viewport height, portrait)
| Game (grid) | Hero + logo | Board frame | Feature meter | HUD starts | Spin button |
|---|---|---|---|---|---|
| Loki's Vault (5x4) | 11 to 23 | 27 to 68 | none | 80 | 70 px, 18% of width |
| Angel of Asgard (5x4, rank row) | 13 to 34 | 30 to 69 | none | 80 | 70 px, 18% |
| Red Strike (5x4, multiplier track on top) | 12 to 26 | 28 to 67 | none | 80 | 70 px, 18% |
| Tome of Hades (5x5) | 11 to 29 | 28 to 64 | 63 to 78 | 80 | 70 px, 18% |
| Odin's Vault (5 + rank column, 6 rows), 390x844 | 7 to 24 | 19 to 65 | 66 to 77 | 80 | 70 px, 18% |
| Odin's Vault, owner's phone 366x710 | 3 to 16 | 16 to 69 | 70 to 82 | 87 | 62 px, 17% |
| **Inkblade Ronin (6x5), owner's game as it is** | 13 to 23 | 23 to 57 | 55 to 60 | 79 | 98 px, 25% |

What all the reference games share on a phone:
- **The board frame bleeds to the full width** (97 to 100 percent); the **reel window is about 75 percent of the width** and the decoration (pillars, torches,
  runes) takes the rest. Inkblade Ronin has the same 74 percent window, so its board size is not the difference.
- **Board height follows the grid shape**: 36 to 41 percent for a 5x4 or 5x5 grid, 46 to 53 percent for the tall Odin's Vault grid; a wide 6x5 grid gives about 34.
- **A hero or mascot zone above the board** (the hero 12 to 34 percent in four of the five) with the mascot **overlapping the top edge of the board**:
  its lower body is hidden behind the frame, only the bust, the spear and the ravens show. The logo sits beside it. Nothing important starts below 7 percent.
- **HUD pinned to the bottom, identical in every game**: two floating round buttons (turbo or bonus on the left, a studio emblem on the right) at about 80 to 86
  percent; the control bar at 88 to 94 percent (menu on the left, minus, the big spin in the centre, plus, autoplay on the right); a footer row at 95 to 100 percent with
  three values (balance left, bet centre, win right). The spin is 70 px, 18 percent of the width, centred at about 90 percent of the height.
- **A scene band of 11 to 20 percent between the board (or meter) and the HUD**, never empty: scenery with detail, the floating buttons, and in two games the feature meter.
  In the two games that carry a meter (Odin's Vault, Tome of Hades) the distance from the board to the HUD is only 2 to 3 percent of free space after the meter.

The owner's game against the same measures (`mobile_layout.py report`): dead bands total **34 percent** (13 above the logo, 19 between the meter and the HUD), against 13 and 16
for Odin's Vault and Tome of Hades (and 27 to 30 for the three games without a meter). Board height 34 percent is fine for a wide grid. The problem is what fills the rest.

## 2. What changes between PC and phone in Odin's Vault, beyond the layout
Same game, 1280x720 PC against 390x844 phone (both loaded and compared):
| | PC | Phone |
|---|---|---|
| Mascot | full body, standing to the right of the board | **the same character art** (the package holds one character skeleton, `assets/spines/character/`) at the top edge of the board: only the bust, the spear and the ravens show, so the lower body is hidden behind the frame |
| Feature meter | tall vertical panel to the left of the board (wing eye on top, 2 columns x 4 slots, coin below) | **horizontal bar below the board** (eye on the left, 2 rows x 4 slots, coin on the right); same parts, rearranged |
| HUD | one dock: menu, BALANCE, WIN, BET with up and down arrows, autoplay, spin | bar: menu, **minus, spin, plus**, autoplay; a separate **footer of three values**; floating turbo and emblem buttons above it |
| Logo | top right | top right, smaller, next to the mascot |
| Background | wide scene (trees, a glowing portal, rocks) | portrait recomposition of a layered scene (the same layers, with stairs and snow filling the lower part); see below |
| Board and symbols | grid of the same size and the same symbols | same grid scaled to the full width; symbol detail unchanged |
| Behaviour while a round plays | not measured | the minus, plus and autoplay icons **dim to about 38 percent brightness** (brightest pixel 255 at rest, 96 in two frames taken mid-round and after it); the spin button stays fully bright |
| Win highlight | not captured on PC | winners glow and **the other symbols are dimmed** (seen in one phone frame; 3 winning tiles, the rest darker) |

**There are no phone-specific assets.** Loading the game frame with `device=mobile` and with `device=desktop` on a 390x844 phone viewport requested the same 181 files, 32.5 MB,
and a PC run and a phone run requested the same files too (236 and 234 URLs, 32.83 MB, only session identifiers differ). The layout is computed from the size of the game window at
runtime, from one asset set. So the art must be built to be recomposed: layered backgrounds, a mascot that survives being half-hidden, widgets that can be rearranged.
Side note, not a Stake rule: the whole 32.5 MB is downloaded on a phone as well (22.7 MB of images, 7.9 MB of audio in one audio sprite, a 0.5 MB loader video).

## 3. How the reference game's art is packaged (file inventory, structure only)
From the file names and sizes in the network log of Odin's Vault v13 (names and sizes only; no art was copied):
- `assets/spines/background/` bg_basegame and bg_freegame1 to 4 (Spine skeletons, with matching static sprites in `assets/sprites/background/` as a fallback): **backgrounds are layered and animated**, one per bonus level.
- `assets/spines/character/` the mascot as a Spine character. Seen in play: the hero region moves while the reels are still (see `casino-symbol-art/references/animation-timing.md`).
- `assets/spines/win_popups/` nice_win, big_win, mega_win, insane_win, max_win (with `_2` and `_3` variants): **five win tiers, each its own Spine animation**.
- `assets/spines/intro_outro/` intro, intro_freegame2 to 4, totalwin: bonus intros per level and a TOTAL WIN plate.
- `assets/sprites/reels`, `symbols`, `misc` (sprite sheets), `assets/spines/symbols/` (coins, highs, specials such as a staff): static symbols as sheets, animated ones as Spine.
- One audio sprite, one loader video, 28 PNG UI files (buttons and icons), fonts, JSON per Spine.
Plan the same split for our own game: sheets for static things, Spine for backgrounds, the mascot, win tiers and bonus plates, one audio sprite.

## 4. Rules (calibrated on the above)
1. Board frame at the full viewport width (at least 95 percent), anchored **just below a hero zone**, not centred in the screen.
2. **Hero zone above the board** of about 16 to 25 percent of the height on a 19.5:9 phone, about 12 percent on a 16:9 phone (clip the top of the mascot, keep the face).
   The mascot overlaps the board's top edge and is hidden behind the frame below the chest; its art must read as a bust (see `casino-symbol-art/SKILL.md`).
3. **Feature meter directly under the board** if the game has one (horizontal on a phone), 2 to 3 percent of space below it.
4. **Scene band between the meter or board and the HUD of 11 to 13 percent**, decorated, holding the floating buttons; it takes the height left over on tall phones. Do not leave it empty or dark.
5. **HUD pinned to the bottom**: floating buttons at 80 to 86 percent, control bar at 88 to 94 percent with the spin centred (at least 56 px and 14 percent of the width; 18 percent in the references),
   footer of three values at 95 to 100 percent. Every touch target at least 44 x 44 CSS px. Keep the spin in the bottom 30 percent.
6. **Never centre the stack in the free space**; fill the free space in this order: scene band (to about 12 percent), then the hero zone, then a taller frame (reel window of 90 percent of the width
   or more with the decoration bleeding off the edges).
7. Compute the layout from the **window size**, not from a device flag, and test 360x800, 375x667, 390x844, 412x915 and a landscape phone.
8. Dimming the non-winning symbols is a per-game choice (see `animation-timing.md`); on a phone either way, keep winners clearly brighter than the rest.

## 5. Recipe and tools
```sh
# 1. capture the game at phone and PC sizes (own build: drop --iframe; add --log-requests to diff the asset lists)
node skills/stake-casino-game-dev/scripts/mobile_capture.mjs --url https://your.game/ --out shots/ --tap-start --presets phone-390x844,phone-360x800,phone-375x667,phone-412x915,phone-844x390,pc-1280x720
# 2. read the rectangles off a screenshot with a 10 percent grid
python3 skills/stake-casino-game-dev/scripts/mobile_layout.py grid shots/phone-390x844_idle.png --out shots/grid.png
# 3. write spec.json (see the docstring of mobile_layout.py) and check it
python3 skills/stake-casino-game-dev/scripts/mobile_layout.py report spec.json --png report.png
# 4. compute the recommended layout from the sizes of your own blocks
python3 skills/stake-casino-game-dev/scripts/mobile_layout.py solve --viewport 390x844 --board-aspect 1.34 --meter-h 0.12 --hud 0.206 --png solved.png
```
`solve` reproduces the reference: for Odin's Vault (board aspect 0.97, meter 0.25 of the width, HUD 0.2) it gives a board of 47 percent of the height and a hero zone of 16 percent against the
measured 46 and 17 to 24. A layout function for the game (TypeScript, in the design space of the window):
```ts
export function phoneLayout(vw: number, vh: number, a: { boardAspect: number; meterH: number; hud: number; heroMin: number; scene: number }) {
  const hud = a.hud * vh, boardW = vw, boardH = boardW / a.boardAspect, meter = a.meterH * vw, gap = 0.02 * vh;
  const free = vh - (boardH + meter + hud + gap * 2) - a.heroMin * vh;              // negative on short screens: shrink the hero zone first
  const scene = Math.max(0, Math.min(free, a.scene * vh));
  const hero = Math.max(0, vh - (boardH + meter + hud + gap * 2) - scene);          // everything else goes to the hero zone
  const board = { x: 0, y: hero, w: boardW, h: boardH };
  return { hero: { y: 0, h: hero }, board, meter: { y: board.y + boardH + gap, h: meter }, scene: { h: scene }, hud: { y: vh - hud, h: hud } };
}
```

## 6. Applying it to Inkblade Ronin (the owner's game, 390x844)
Current: hero zone empty above the logo (13 percent), board 23 to 57, the meter bar at 55 to 60, then 19 percent of dark mountains before the balance row at 79.
With the recipe (`solve --viewport 390x844 --board-aspect 1.34 --meter-h 0.12 --hud 0.206`): hero zone 0 to 24 percent holding a **mascot (the ronin) overlapping the torii and the top of the frame**,
board 24 to 58, meter 60 to 65, scene band 66 to 78 (about 12 percent) with the floating buttons, HUD from 79. Results to check with `report`: dead bands from 34 down to under 20 percent.
Other changes the references suggest: spin button from 98 px (25 percent of the width) to about 70 px so the bar stays slimmer; put the footer values below the control bar, as in the reference;
use the 11 to 13 percent scene band for floating turbo and emblem buttons. This needs code and art changes in the game itself (not in this repo): a mascot bust that can sit behind the frame, a
horizontal meter, and layers in the background that extend over the taller screen.

## 7. Limits
- Five games of one studio, one session each; layouts of other studios differ. Percentages are read off screenshots (about 1 to 2 percent error); the owner's Inkblade numbers are from an inline image.
- Win and spin behaviour on a phone was seen in single frames, not measured as timing.
- No real device was used (Chromium emulation, software rendering): fonts, safe areas (notch, home indicator) and browser chrome are not reproduced, and the status text at the top of the frame belongs to the browser.
- The asset comparison shows the same files are requested; it does not prove the game never switches textures at runtime.
