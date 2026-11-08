# Symbol animation in code (no Spine)

For reel symbols, a few small tweens carry most of the feel. The recipes live as data so a designer can tune them without touching code:
`scripts/symbol_fx.json` (recipes) and `scripts/symbol_fx.mjs` (a dependency-free evaluator the game calls every frame).

| Recipe | Length | Use |
|---|---|---|
| `idle` | 2.8 s loop | slow breathing (scale +1.5 percent, 1.5 px lift); give each symbol a random start offset so the grid does not pulse in sync |
| `land` | 0.30 s | squash and stretch when a reel stops (1.10 x 0.88, then 0.97 x 1.045, then back to 1) |
| `appear` | 0.22 s | pop-in for tumbles and cascades (0.6 to 1.08 to 1, fade in) |
| `win` | 0.72 s loop | pulse to 1.14, small rotation wiggle (+-2 degrees), glow track 0 to 0.9 |
| `dim` | 0.18 s | the other symbols while a win plays (alpha 0.35, scale 0.96); the game keeps them dimmed until the win ends |
| `tease` | 0.50 s loop | scatter anticipation (scale 1.10, rotation +-3 degrees, glow) |

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
- The numbers are authored defaults, **not measured from a studio**. An attempt to measure Valkyrie's symbol win animation from recorded
  gameplay failed (see `win-celebration-art.md`): the recording had too few wins and the detection was unreliable.
- Not tested inside PixiJS; the evaluator is plain JavaScript and the preview applies the same values with Pillow.
- Spine is only needed for character-like motion (see the shelved mascot work); symbols rarely need it.
- Respect reduced-motion settings and Stake's skippable-celebration rule: the loops here are for win highlights, which end when the
  win sequence ends.
