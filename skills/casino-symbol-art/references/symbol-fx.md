# Symbol animation in code (no Spine)

For reel symbols, a few small tweens carry most of the feel. The recipes live as data so a designer can tune them without touching code:
`scripts/symbol_fx.json` (recipes) and `scripts/symbol_fx.mjs` (a dependency-free evaluator the game calls every frame).

| Recipe | Length | Use | Basis |
|---|---|---|---|
| `drop_in` | 0.34 s | a symbol falls into its column; start columns about 0.16 s apart, left to right; follow with `land` | cycle and stagger measured, fall curve authored |
| `land` | 0.30 s | squash and stretch on landing (1.10 x 0.88, then 0.97 x 1.045, then 1) | authored |
| `win` | 0.65 s, one shot | flash to an emissive state, ring glow, glint at 0.4 s, fade; tracks `scaleX`, `scaleY`, `glow`, `flash`, `glint`; does not dim the others | shape measured (`animation-timing.md` §2) |
| `win_loop` | 0.72 s loop | repeating pulse for a highlight that must stay on screen | authored |
| `appear` | 0.22 s | pop-in for tumbles and cascades | authored |
| `tease` | 0.50 s loop | scatter anticipation | authored |
| `dim` | 0.18 s | optional: darken the others when an overlay needs contrast; the reference game does not dim | authored |
| `idle` | 2.8 s loop | optional: slow breathing; the reference game's resting symbols were still, so skip it by default | authored |

```ts
import { evalRecipe } from './symbol_fx.mjs'; import recipes from './symbol_fx.json';
app.ticker.add(() => {
  const fx = evalRecipe(recipes.win, (performance.now() - start) / 1000);
  sprite.scale.set(fx.scaleX, fx.scaleY); sprite.angle = fx.rotation; glowSprite.alpha = fx.glow;   // y and alpha when the recipe has them
});
```
The `glow` track drives a separate pre-blurred sprite (additive blend); the preview script fakes it with a blurred copy.
`scaleY` is in the cell's own space: the pivot must be the symbol centre (or the bottom for `land` if symbols sit on a floor).

## Check and preview
```sh
python3 skills/casino-symbol-art/scripts/symbol_fx_preview.py [symbol.png] [--fill 0.84] [--out fx_preview.mp4]
```
Checks (the same evaluator the game uses): one-shot recipes end on their rest values (`dim` and `appear` end where they are meant to); loops
start and end on the same value on every track; `land` keeps volume (scaleX x scaleY within 0.92 to 1.12); peak scale x symbol fill stays at or
under 1.0, so a winning symbol does not cover its neighbours (`win` peaks at 1.15 and the style guide's 84 percent fill gives 0.97). All six recipes
pass. With a symbol image it renders the six side by side as an mp4.

## Status and honesty
- `win`, the column stagger and the whole-cycle length come from measurements of one reference game (`animation-timing.md`: 60 spins, 25 fps
  footage, one game, one session). Everything marked authored in the table is an informed default, not a studio measurement.
- Not tested inside PixiJS; the evaluator is plain JavaScript and the preview applies the same values with Pillow.
- Spine is only needed for character-like motion (see the shelved mascot work); symbols rarely need it.
- Respect reduced-motion settings and Stake's skippable-celebration rule: the loops here are for win highlights, which end when the
  win sequence ends.
