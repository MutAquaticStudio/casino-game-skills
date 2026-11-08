# Win celebration art (connects casino-symbol-art to stake-casino-game-dev §8)

`stake-casino-game-dev` §8 defines **what** is shown and **when** (tiers from `winLevel`, screens,
behaviour rules). This file defines **which art assets** to make for it, in the style of the set.
Status: asset list and rules are specified; **not yet produced end to end**, and not validated against
a live Valkyrie or Hacksaw celebration (their celebrations were not captured, see
`style-valkyrie-hacksaw.md` §5). Treat the visual direction below as design guidance.

A longer capture (60 spins of Loki's Vault, 2026-11-08) recorded a small-win highlight, a free-spins bonus and its TOTAL WIN summary (12.9x), but still no
big-win tier overlay: the 12.9x total was celebrated only by the summary plate. Timing and structure of what WAS recorded is in `animation-timing.md`;
do not describe the tier screens (Big, Mega, Epic, Max) until a clip of one exists.
One related observation that is evidenced: inside a game Valkyrie escalates Wild multiplier tiers by hue and finish
(`style-valkyrie-hacksaw.md` §9), which supports escalating win tiers the same way.

## 1. Asset list per screen (from §8.3)
| Screen | Art assets | Made by |
|---|---|---|
| Win highlight (every win) | symbol win frame/glow sprite, win-line or cluster outline, per-win label plate | code (Graphics) + 1 glow sprite |
| HUD roll-up | bitmap number font (digits 0–9, `,` `.` currency signs), win plate | code or generated font sheet, keyed |
| Big / Mega / Epic / Legendary / Max Win | one title plate per tier (wordless emblem + empty banner; **the word is live text** for localisation), tier colour ramp, ray/burst sprite, backdrop dim layer | generated emblem + code text |
| Particles | coin, gem, spark, ember sprites (3 sizes each), 2 intensity presets | generated sheet, keyed |
| Feature trigger / retrigger / meter banner | banner plate with empty text area, scatter burst sprite | code + 1 generated plate |
| Bonus intro / transition | one full-frame transition art (wipe or portal), hero pose | generated, keyed |
| Bonus summary | total-win plate, hero celebration pose | generated, keyed |

## 2. Style rules (so celebrations match the set)
- Use the same `style_lock.prefix` and run `style_check.py`; emblems belong to the `symbol` or `special` group.
- Tier escalation by **warm colour share and size**, not by changing style: Big = gold on the set's
  base hue; Mega adds the accent; Epic adds a second glow hue from the palette; Legendary and Max
  Win use the Wild/Scatter special treatment and fill the frame. Never introduce a colour outside
  `palette` + `warm_accent`.
- Text is never painted: leave the banner empty, draw the word with a bitmap or live font.
- Emblems are generated on a flat magenta key, one tier per cell in a single sheet so the five
  read as a family; plates and banners are cheaper and cleaner in code.
- Particles: three sizes per type, same light direction, soft outline; the emitter, not the
  art, carries the energy.
- Keep a calm centre: the roll-up number must stay readable over the burst (contrast ≥ 4.5:1 against the dim layer).

## 3. Hand-off to the Pixi build
Name files by screen and tier: `win_title_big.png`, `win_title_mega.png`, …, `win_burst.png`,
`particle_coin_s.png`, `plate_total_win.png`, `font_digits.png/.fnt`. Pack with `svg_to_atlas.py build`
as a second atlas (`win@1x/@2x.json`). Durations, skip behaviour and the exact roll-up rules stay
as in `stake-casino-game-dev` §8.4; this file only supplies the art.

## 4. Check before hand-off
- [ ] Every tier title readable at 400×225 and on a phone in portrait with the longest localised word.
- [ ] Tier order is visible without reading the word (size and warm share rise monotonically).
- [ ] No asset contains painted text.
- [ ] `style_check.py` has no FAIL on the win assets.
- [ ] Particles and emblems pass the same greyscale and shrink test as symbols.
