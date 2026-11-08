# PixiJS for Stake slots

Moved out of SKILL.md (it is section 12 there; subsections 12.1 to 12.6 are unchanged). Read it when writing the frontend. Official API topics: `references/pixijs/vendor/`.

## 12. PixiJS for Stake slots (v8, latest checked: 8.22.0 – Nov 2026)

PixiJS is the most common Stake Engine renderer. Check the current version with
`npm view pixi.js version` before starting; everything below is v8 API.

### 12.1 Versions and where the API docs are
- **pixi.js 8.22.0** (latest stable, Oct 2026). Stake's Web SDK pins **8.8.1** with
  `@esotericsoftware/spine-pixi-v8` 4.2.x and `pixi-filters` 6.x. New projects: use the latest
  8.x. Web SDK projects: upgrade only after testing animations, text and filters (several
  releases since 8.8 changed behaviour, see 12.6).
- Current ecosystem: `@esotericsoftware/spine-pixi-v8` 4.3.x, `pixi-filters` 6.1.x,
  `@pixi/sound` 6.x, `@pixi/layout` 3.x, `gsap` 3.15.x.
- **Official agent skills ship inside the npm package** since 8.19: after `npm i pixi.js`, read
  `node_modules/pixi.js/skills/pixijs/SKILL.md` (router) and the topic skill you need
  (`pixijs-application`, `-assets`, `-scene-sprite`, `-scene-text`, `-scene-particle-container`,
  `-filters`, `-performance`, `-events`, `-ticker`, `-accessibility`, `-migration-v8`…). The repo
  version of this skill vendors them in `references/pixijs/vendor/`. For anything not covered,
  the always-current API index is `https://pixijs.download/release/docs/llms.txt` (dev-time
  reading only – the game build must not fetch anything external).
- Prefer these sources over memory: v7 patterns (`beginFill`, `@pixi/*` imports, `app.view`,
  `BaseTexture`, constructor options) are wrong in v8.

### 12.2 v8 essentials (the mistakes agents make most)
```ts
import { Application, Assets, Container, Sprite, BitmapText } from 'pixi.js';

const app = new Application();
await app.init({                      // async init – never pass options to the constructor
  resizeTo: hostEl,                   // the game container, not window (popout/mini-player)
  background: '#000000',
  antialias: true,
  autoDensity: true,
  resolution: Math.min(window.devicePixelRatio, 2),
  preference: 'webgl',                // WebGL is the safest default on mobile; WebGPU opt-in
});
hostEl.appendChild(app.canvas);       // app.canvas, not app.view
```
- One import root: `import { … } from 'pixi.js'`. Graphics: `new Graphics().rect(…).fill(…)`.
- Load with `Assets`, never `Texture.from(url)`. Use a manifest with bundles and relative paths:
  ```ts
  await Assets.init({ basePath: './assets', manifest: {
    bundles: [
      { name: 'boot',  assets: [{ alias: 'logo', src: 'logo.webp' }, { alias: 'ui-font', src: 'fonts/ui.woff2' }] },
      { name: 'base',  assets: [{ alias: 'symbols', src: 'symbols.json' }, { alias: 'win-digits', src: 'fonts/digits.fnt' }] },
      { name: 'bonus', assets: [{ alias: 'bonus-bg', src: 'bonus/bg.webp' }] },
    ] } });
  await Assets.loadBundle('boot', p => loader.set(p));   // progress 0..1 for the loading screen
  await Assets.loadBundle('base');
  Assets.backgroundLoadBundle('bonus');                  // prefetch while the player spins
  ```
- Texture atlases (TexturePacker/free-tex-packer JSON) for symbols and UI; `.webp`/`.avif`
  with `.png` fallback; KTX2/Basis only if you bundle the transcoder locally.
- Text: `BitmapText` (or an MSDF font) for everything that changes often – win counters,
  balance, bet value, spin counters. `Text` for static labels (re-rendering `Text` every frame is
  slow). `SplitText`/`SplitBitmapText` for per-letter tier-title animations. Fonts are bundled
  files loaded via `Assets` (no font CDN); for localization install a font per script.
- Containers with `isRenderGroup: true` for big layers that move as a whole (background, reel
  area, HUD) – the GPU handles their transforms. `cacheAsTexture(true)` for static, complex
  sub-trees (frames, paytable pages); call `cacheAsTexture(false)` before destroying.
- `ParticleContainer` + `Particle` (v8 API: `addParticle`, `particleChildren`) for coin showers
  and sparkles – thousands of particles in one draw call. It now inherits tint/alpha/blend
  from ancestor render groups (8.19–8.20).
- Culling is opt-in: `extensions.add(CullerPlugin)` + `container.cullable = true` for
  off-screen symbol strips.
- Filters (glow, blur, displacement, `pixi-filters`) are expensive on mobile: apply them to
  small containers, briefly (win moments), and set `filterArea`/`padding` tightly.

### 12.3 Slot architecture in Pixi
(Round sequence and timing: §8.5. Symbol motion recipes as data: `casino-symbol-art/scripts/symbol_fx.json` with the evaluator `symbol_fx.mjs`.)
```
stage
├─ bgLayer        (isRenderGroup)   background, parallax, ambient particles
├─ boardLayer     (isRenderGroup)   reel frame + mask + reels
│   └─ Reel[]     Container with a vertical strip of SymbolView (visible rows + 1–2 padding rows)
├─ fxLayer                          win lines/cluster outlines, ParticleContainer coin showers
├─ celebrationLayer                 Big Win+ overlays, feature popups, bonus summary (§8)
└─ hudLayer       (or HTML/Svelte overlay)  spin, bet, balance, win, menu
```
- **Reels:** each reel scrolls a strip of pooled `SymbolView`s (Sprite or Spine) inside a
  mask (`Graphics` rect or a sprite mask). Spin = accelerate → constant speed (swap the texture
  of symbols leaving the top, slight vertical stretch/blur while fast) → land on
  `reveal.board[reel]` + `paddingPositions` → overshoot-and-settle (back.out ease). Stop reels
  staggered 120–200 ms, slow down later reels when the book's `anticipation[reel] > 0`. Never
  let random filler decide anything – the final board always comes from the book.
- **Symbols:** one `SymbolView` class with states `idle | spin | land | win | dim` driven by
  Spine animations (`Spine.from({ skeleton: 'h1-data', atlas: 'h1-atlas' })`,
  `state.setAnimation(0, 'win', false)`) or spritesheet `AnimatedSprite`s. Pool them; don't create
  or destroy during spins.
- **Tumble/cascade:** remove winners (pop animation), drop survivors with gravity easing, spawn
  new symbols from above per `tumbleBoard` – await each step before the next book event.
- **Win presentation:** highlight `winInfo.positions` (dim the others, play `win`), draw lines
  with `Graphics` or a glowing sprite trail, roll the HUD counter with `BitmapText`; Big Win and
  above open the celebration layer (§8) – skippable, with tiers chaining from `winLevel`.
- **Timing:** drive sequences with GSAP timelines (GSAP animates Pixi properties directly) or
  `app.ticker` with `ticker.deltaMS`; turbo = `timeline.timeScale(n)`. Await each handler in the
  book player so live, resume and replay behave identically.
- **Layout:** compute a design-space layout (e.g. 1920×1080 landscape, 1080×1920 portrait) and
  scale/letterbox the stage to the host size on resize; switch layouts by aspect ratio or
  `device=mobile`. Test 400×225 popout: board fully visible, HUD still tappable or simplified.
  `@pixi/layout` (Yoga flexbox) can help for HUD panels.
- **HUD choice:** Pixi HUD (consistent look, Web SDK `components-ui-pixi`) or HTML/Svelte overlay
  (crisp text, easier accessibility and social-mode relabeling). Either way: spacebar spins,
  ignore key repeat and focused dialogs.
- **Svelte:** the Web SDK's `pixi-svelte` lets Svelte components declare Pixi objects; outside the
  SDK, create the Application in `onMount`, destroy it in the cleanup
  (`app.destroy({ removeView: true, releaseGlobalResources: true }, { children: true })` – the
  global release avoids stale textures when the app is re-created in the same tab).

### 12.4 Performance budget (mid-range phone, 60 fps)
- < ~50–100 draw calls in the heaviest scene; check with the PixiJS DevTools browser extension
  or `renderer` stats; keep sprites from the same atlas adjacent so they batch (filters, masks,
  `Text` and blend-mode changes break batches).
- Texture memory: atlases ≤ 2048–4096 px; total GPU textures ideally < ~150 MB; unload the
  bonus bundle (`Assets.unloadBundle('bonus')`) when it won't be needed soon.
- Warm-up: render every symbol state, filters and celebration assets once off-screen during
  loading (or `renderer.prepare.upload(container)`) so the first win doesn't hitch.
- Pause rendering when the tab is hidden (`app.ticker.stop()` / `start()` on `visibilitychange`)
  and render on demand when idle.
- Handle WebGL context loss: on restore, Pixi recreates textures (Text/HTMLText regeneration
  was fixed in 8.21) – test it on mobile.

### 12.5 Stake constraints applied to Pixi
- The static build must not reach external URLs: no CDN `pixi.js` script, no font CDNs, assets
  under relative paths (`basePath: './assets'`, Vite `base: './'`).
- `Assets` default loaders are fine; don't use parsers that fetch remote resources.
- Every visual must match the book; final amounts = RGS payout (§8).
- Run `scripts/check_static_build.py dist` after building.

### 12.6 Recent v8 changes that can bite (8.19 → 8.22)
- **8.22:** pressing Tab activates the accessibility layer by default again
  (`accessibilityOptions.activateOnTab`). Test keyboard play: spacebar must still spin and focus
  must not get stuck on hidden accessible buttons; opt out with `activateOnTab: false` if needed.
  New `contextmenu` events on containers; WebGPU `transient` MSAA option.
- **8.21:** `Matrix.decompose()`, `setFromMatrix()`, `reparentChild()` and `replaceChild()`
  now return a real rotation, zero skew and negative `scale.x` for mirrored objects – re-check
  tweens that read these values (e.g. flipped symbols). TypeScript 6/7: use `@types/web` instead
  of `@webgpu/types`. `TexturePool` positional args deprecated.
- **8.20:** `ParticleContainer` inherits tint and alpha from ancestor render groups – remove
  manual compensation. WebGPU render bundles and `flipY` render option.
- **8.19:** `updateTransform({ scaleX: 0 })` now really applies zero scale; `ParticleContainer`
  respects inherited blend modes; `FillPattern` tiles in global space by default;
  HTML-in-canvas via `pixi.js/html-source`; official agent skills shipped in the package.
- **8.17:** `BlurFilter` uses a halving-strength scheme (visual change); Text/BitmapText/
  HTMLText alignment made consistent – re-check text layouts after upgrading.
- **8.16:** tagged text (inline styles in one `Text`) and an experimental Canvas renderer
  fallback.
