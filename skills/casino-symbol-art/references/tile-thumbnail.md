# Game tile (thumbnail) for the Stake Tile Editor

The tile is the first thing a reviewer and a player see. The approval checklist ("Game thumbnail (Tile Editor)") asks for:
a generally bright tile that does not clash with the Stake background (watch dark edges); a bright, appropriate background; a foreground
with the key focus area filled; a gradient of similar colour to the background; the title inside the inner guidelines, not near the edges.
The dashboard Tile Editor composes four layers: background, foreground, gradient, title. Its pixel size and guideline positions are shown
only in the dashboard; they are not documented in this repo, so read them there first and pass them to the tools.

## What to make
| Layer | Made by | Notes |
|---|---|---|
| Background | generated (`tile_background`) | bright, high-key, uncluttered, centre lighter than the edges, no dark corners |
| Foreground | generated (`tile_foreground`, flat magenta key, then cut out) | the game's hero or key object, about 80 percent of the height, strongest contrast and detail in the centre, top 20 percent left empty |
| Gradient | Tile Editor | pick a colour close to the background so it blends |
| Title | Tile Editor (live text) | inside the inner guideline; never paint the title into the art |
`art_harness.py` writes the two prompts (calls 8 and 9, `optional: true`). They drop the in-game "dark and cool" rule on purpose: a dark
in-game backdrop fails the tile.

## Check
```sh
python3 skills/casino-symbol-art/scripts/tile_check.py tile.png --title-box X,Y,W,H [--margin 0.12] [--out tile_report.png]
```
Measures mean brightness (L*), the outer ring against the tile (dark edge), the darkest corner patch, detail density in the centre (key area
filled) and whether the title box lies inside the inner margin. The margin default (12 percent per side) is a placeholder for the real guideline.
Tested on two tiles: the dark Egyptian in-game backdrop with a title near the top edge FAILED brightness (L* 17), corners (1 to 21) and title
(20 px from the edge, margin 123 px); a bright gradient tile with the Hacksaw-preset hero and a title inside the margin passed every item
(L* 78, corners 72 to 87, centre detail 0.25 against 0.09 overall).

Limits: the check does not know the Tile Editor's guidelines, cannot judge whether the gradient colour matches the background, or whether the
foreground is "appropriate". Final judge is the Tile Editor preview and a look next to neighbouring tiles. The two generated tile layers were not
run through a model in this round (only the tile composition above, built with code and an earlier generated hero).
