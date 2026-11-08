# Export and Pixi integration reference

Detail for `casino-symbol-art`. Code here targets PixiJS 8.22 (the version the repo documents)
and was run against it. Official API notes live next to the main skill in
`stake-casino-game-dev/references/pixijs/vendor/` (`pixijs-assets`, `pixijs-scene-sprite`).

## 1. `svg_to_atlas.py` commands and flags

```bash
python3 scripts/svg_to_atlas.py lint    <svg_dir>
python3 scripts/svg_to_atlas.py preview <svg_dir> [--out preview.png] [--cell 256] [--shrink 140] [--cols 4]
python3 scripts/svg_to_atlas.py layers  <svg_dir> [--out art/layers] [--size 512]
python3 scripts/svg_to_atlas.py build   <svg_dir> --out <base> [flags]
```

Needs Pillow and either `rsvg-convert` (librsvg) or `pip install cairosvg`.

| `build` flag | Default | Meaning |
|---|---|---|
| `--size` | 256 | Cell width at 1x, in px. Set it from the real on-screen size (§2) |
| `--scales` | `1,2` | Resolutions to write. Several scales produce `<base>@1x.*` and `<base>@2x.*`; a lone `1` writes `<base>.*` |
| `--padding` | 2 | Transparent gutter around each frame |
| `--extrude` | 1 | Edge pixels replicated outward; stops dark or light fringes when sprites are scaled |
| `--max-size` | 2048 | Largest atlas side. 2048 is safe on mobile, 4096 is the upper bound |
| `--format` | png | `webp` is far smaller and fine for symbols |
| `--quality` | 90 | WebP quality |
| `--anchor` | `0.5,0.5` | Default anchor written into every frame |
| `--pot` | off | Power-of-two sides. Default is tight and a multiple of 4 (what KTX2/Basis encoders expect) |

Properties worth knowing: frames are **not trimmed** (every symbol keeps the same cell, so
anchors and strips line up); frame names are the SVG file names; `meta.scale` always matches the
image resolution (Pixi v8 uses it as the texture resolution, and a mismatch renders at the
wrong size); when the set does not fit `--max-size` the script stops with advice instead of
writing a partial atlas.

If an artist delivers PNGs instead, pack them with TexturePacker or free-tex-packer using the
same rules: padding ≥ 2, extrude 1, one cell size per set, `@1x`/`@2x` file names, `meta.scale`
matching the image.

## 2. Sizing the cell

Logical cell ≈ on-screen px, and the `@2x` file covers retina. Do not draw bigger "to be
safe": a bigger cell multiplies atlas size by its square.

| On-screen symbol | Build with | Pixels in the `@2x` file |
|---|---|---|
| 100 px | `--size 112 --scales 1,2` | 224 |
| 140 px | `--size 160 --scales 1,2` | 320 |
| 200 px | `--size 224 --scales 1,2` | 448 |

Capacity check (measured with this script): with `--size 160` at `@2x`, 36 symbols fill a
2048×2048 atlas (1956×1956) and the 37th does not fit. A 12-symbol set at the same settings is
980×1304 at `@2x` (about 190 KB as PNG). If a set does not fit, lower `--size`, drop the `@2x`
file for the lowest-tier symbols, or split the set (§6).

## 3. Loading in Pixi v8

Use `Assets`, a manifest and bundles (see `stake-casino-game-dev` §12.2). The resolver expands
`@{1,2}x` into both files and picks one from `texturePreference.resolution`; sprites keep their
logical size either way.

```ts
import { Application, Assets, Sprite } from 'pixi.js';

const dpr = Math.min(window.devicePixelRatio, 2);
const app = new Application();
await app.init({ resizeTo: window, resolution: dpr, autoDensity: true });

await Assets.init({
  basePath: './assets',
  texturePreference: { resolution: dpr },
  manifest: {
    bundles: [
      { name: 'base',  assets: [{ alias: 'symbols',       src: 'symbols@{1,2}x.json' }] },
      { name: 'bonus', assets: [{ alias: 'bonus-symbols', src: 'bonus-symbols@{1,2}x.json' }] },
    ],
  },
});
await Assets.loadBundle('base');
Assets.backgroundLoadBundle('bonus'); // prefetch while the player spins

const ruby = Sprite.from('ruby'); // frame name = SVG file name; anchor already 0.5
```

Notes:
- Asset paths stay relative (`./assets`) because Stake builds are static and must not reach
  external URLs (`stake-casino-game-dev` §12.5). Run `scripts/check_static_build.py dist` on
  the built game.
- The image name sits inside the JSON (`meta.image`), so there is no per-format fallback
  pattern for spritesheets. Choose WebP or PNG for the set.
- Frame names are global in Pixi's cache. If two atlases could contain the same frame name,
  load them with a `cachePrefix` (`Spritesheet` option) or keep names unique per set.

## 4. SVG directly in Pixi (and why symbols are rasterised)

Pixi can load an `.svg` two ways. Texture mode rasterises once through the browser, with full
SVG fidelity. Graphics mode (`data: { parseAsGraphicsContext: true }`) keeps vectors but
**skips** filters, `<clipPath>`, `<mask>`, `<pattern>`, `<style>` blocks, `gradientTransform`,
`stop-opacity`, `<text>`, `<image>`, `<use>` and `transform` attributes. Glossy casino
symbols lean on exactly those, so build the atlas and use it for reels.

Direct SVG is reasonable for a few large UI pieces: texture mode for a fixed-size logo
(`Assets.load('logo.svg')`, optionally `data: { resolution: 2 }`), Graphics mode for simple
icons that must scale. Details: `pixijs-assets/references/svg.md`.

## 5. `SymbolView` sketch

States match `stake-casino-game-dev` §12.3 and `symbol-design.md` §4. One class, pooled, never
created or destroyed during a spin. Type-checked with `tsc --strict` against pixi.js 8.22 and
gsap, and exercised in a browser.

```ts
import { Container, Sprite, Texture } from 'pixi.js';
import { gsap } from 'gsap';

// Motion values for these states live in scripts/symbol_fx.json (recipes `drop_in`, `land`, `win`, `win_loop`; `idle` and `dim` are optional);
// evaluate them with scripts/symbol_fx.mjs in the ticker. Round order and timing rules: stake-casino-game-dev §8.5.
export type SymbolState = 'idle' | 'spin' | 'land' | 'win' | 'dim';

export class SymbolView extends Container {
  private art = new Sprite({ anchor: 0.5 }); // the atlas also stores a 0.5 anchor
  private tween: gsap.core.Animation | null = null;

  constructor() {
    super();
    this.addChild(this.art);
  }

  /** `name` is the frame name = the SVG file name, e.g. 'ruby'. */
  setSymbol(name: string) {
    this.art.texture = Texture.from(name);
  }

  setState(state: SymbolState) {
    this.tween?.kill();
    this.art.scale.set(1);
    this.art.alpha = 1;
    this.art.tint = 0xffffff;

    switch (state) {
      case 'spin': // slight vertical stretch while the reel is fast
        this.art.scale.y = 1.08;
        break;
      case 'land': // overshoot and settle
        this.tween = gsap
          .timeline()
          .to(this.art.scale, { x: 1.08, y: 1.08, duration: 0.08, ease: 'power2.out' })
          .to(this.art.scale, { x: 1, y: 1, duration: 0.16, ease: 'back.out(2)' });
        break;
      case 'win': // pulse; high-pay symbols swap in a real animation
        this.tween = gsap.to(this.art.scale, {
          x: 1.1, y: 1.1, duration: 0.3, yoyo: true, repeat: -1, ease: 'sine.inOut',
        });
        break;
      case 'dim': // tint + alpha, no filter, so the batch is not broken
        this.art.alpha = 0.45;
        this.art.tint = 0x777777;
        break;
    }
  }
}
```

Turbo: scale timelines with `timeScale`. If a symbol must be fitted to the reel cell, scale a
wrapper `Container`, not `art`, so the state tweens keep working from `scale = 1`.

## 6. Animation hand-off

Choose by budget and by how much the symbol must act.

**Tween on a static sprite** (§5): cheapest, enough for most low pay and many high pay symbols.

**Spine** (high-pay win actions, Wild expand, Scatter land): export the layers and import them
as images.

```bash
python3 scripts/svg_to_atlas.py layers art/svg --out art/layers --size 512
# -> art/layers/ruby/glow.png, body.png, highlight.png, layers.json (same canvas)
```

Every layer of a symbol shares the canvas of its SVG, so if the tool places each image at the
same origin they register with no manual offsets (checked: the layers composite back to the
full render, within antialiasing rounding). Check one symbol before importing the whole set.
Only top-level `<g id="...">` elements become layers; the script warns about loose elements
outside a named group. File names sort alphabetically, so take the stacking order from
`layers.json` (`order_bottom_to_top`), which follows the group order in the SVG. In Pixi use
`@esotericsoftware/spine-pixi-v8` (`stake-casino-game-dev` §12.1, §12.3).

**Frame animation** (pet or character loops, short win bursts): draw each frame as an SVG named
`<symbol>_<state>_<nn>.svg`, build them into the same atlas, then:

```ts
import { AnimatedSprite, Texture } from 'pixi.js';

const textures = Array.from({ length: 12 }, (_, i) =>
  Texture.from(`ruby_win_${String(i + 1).padStart(2, '0')}`));

const win = new AnimatedSprite({ textures, animationSpeed: 0.5, loop: false });
win.anchor.set(0.5);
win.onComplete = () => { /* return to idle */ };
win.play();
```

Frame count multiplies atlas size; keep win loops short (8–16 frames) and only for the symbols
that earn it. `AnimatedSprite` details: `pixijs-scene-sprite/references/animated-sprite.md`.

## 7. Bundles and budget

- Base symbols and shared UI in a `base` bundle loaded before the first spin; bonus symbols,
  bonus background and big-win art in a `bonus` bundle loaded in the background and unloaded
  with `Assets.unloadBundle('bonus')` when it will not be needed soon.
- Budget from `stake-casino-game-dev` §12.4: atlases ≤ 2048–4096 px, GPU textures ideally
  under ~150 MB in total, fewer than ~50–100 draw calls in the heaviest scene. Keep symbols of
  one atlas adjacent in the display list so they batch; filters, masks and blend-mode changes
  break batches.
- GPU-compressed textures (KTX2/Basis) cut texture memory sharply but need a side-effect
  import (`pixi.js/ktx2`) and an encoder step outside this script. The default atlas sides
  (multiple of 4) are already compatible. See `pixijs-assets/references/compressed-textures.md`.
- Warm-up: draw every symbol state once off-screen during loading so the first win does not
  hitch.

## 8. Test checklist before hand-off

1. `lint` clean, `preview` opened and checked at real size and at `--shrink 40`.
2. Atlas loads with `Assets`, `Sprite.from('<name>')` works for every symbol, logical size is
   the same at DPR 1 and DPR 2 (force it with `texturePreference.resolution`).
3. Board visible and readable at 400×225 and on a phone portrait layout.
4. All five states (`idle spin land win dim`) look right on the real reel background.
5. No remote URL anywhere (`lint` and `check_static_build.py`), atlas under the budget.
