# Three.js for Stake Engine casino games

Three.js is an accepted Stake Engine frontend (docs list it under alternative stacks). This
file covers what is *specific* to casino games on the platform. For API details open the
vendored guides in `vendor/` (MIT, CloudAI-X/threejs-skills):
`threejs-fundamentals`, `threejs-loaders`, `threejs-asset-pipeline`, `threejs-materials`,
`threejs-lighting`, `threejs-textures`, `threejs-animation`, `threejs-interaction`,
`threejs-postprocessing`, `threejs-shaders`, `threejs-performance`, `threejs-geometry`,
`threejs-react-three-fiber`. Also `../gamedev/vendor/threejs-scene-setup|threejs-gltf-loading|threejs-materials-lighting`.

## When 3D is worth it
Good fits: 3D reels / rotating symbol cylinders, physical-looking plinko, dice, wheels, coin
showers, depth-heavy bonus scenes, camera fly-ins for big wins. If the game is a flat 5×3 slot,
PixiJS will look as good with less GPU cost – say so. A hybrid is common: Three.js scene +
HTML/Svelte HUD overlay (crisp text, easy accessibility, easy social-mode text swaps).

## Rule 1: the book drives the scene, physics never decides outcomes
For plinko/dice/wheel/coins, the outcome is already in the book. Animate *towards* it:
- Pre-baked paths: precompute or author a path per outcome bucket (e.g. plinko slot index)
  and play it, adding small noise that does not change the end state.
- Or simulate deterministically with a seeded RNG and pick a seed known to land in the right
  bucket (search offline, ship a seed table) – never let a live physics engine choose.
- Final win shown = RGS `payoutMultiplier × bet`, independent of what the animation did.

## Rule 2: static, self-contained build
- Bundle `three` via npm (no CDN `<script>`), plus addons from `three/examples/jsm/...`.
- Draco/Basis/KTX2 decoders: copy the decoder files into your build and set
  `dracoLoader.setDecoderPath('./draco/')` / `ktx2Loader.setTranscoderPath('./basis/')` –
  the defaults point at external CDNs and will violate the XSS policy.
- Fonts for `TextGeometry`/troika must be bundled. HDR env maps bundled (prefer small 1k `.hdr`
  or prefiltered PMREM ktx2).
- Vite: `base: './'`; run `scripts/check_static_build.py dist/` after each build.

## Rule 3: fit every viewport, including popout 400×225
- Renderer canvas fills the container; resize with a `ResizeObserver` on the container
  (the mini-player resizes without a window resize event).
- Fix the board's *visible* bounds: compute camera distance from the board size and current
  aspect so the whole board always fits (`dist = (boardHeight/2) / tan(fov/2)`, and for
  narrow aspects use width: `boardWidth/2 / (tan(fov/2) * aspect)`; take the max).
- Separate layouts for `device=mobile` portrait (board top, HUD bottom) vs 16:9.
- `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))`; drop to 1.5 or 1 on low FPS.

## Rule 4: mobile GPU budget
Targets for a mid-range phone at 60 fps: < ~100 draw calls, < ~300k triangles visible,
texture memory < ~150 MB. Techniques:
- `InstancedMesh` for symbols on reels and for coin/particle showers.
- Texture atlases for symbol faces; KTX2/Basis compressed textures; mipmaps.
- Bake lighting into textures/lightmaps for static set pieces; 1 directional + ambient/
  hemisphere + environment map is plenty. Avoid many shadow-casting lights; if shadows,
  one light, small shadow map, `shadowMap.autoUpdate = false` when static.
- Postprocessing (bloom for wins) only in short bursts, or use selective emissive tricks;
  a full composer chain every frame is the #1 mobile fps killer.
- Dispose geometries/materials/textures when leaving bonus scenes.

## Rule 5: render loop discipline
- Use `renderer.setAnimationLoop`. When idle and nothing animates, render on demand
  (or at a low rate) to save battery; resume full-rate during spins.
- Pause on `document.visibilitychange` (hidden tab) – also stop audio.
- Drive game timing from your own timeline (GSAP timelines work on Three.js object props),
  not from frame counts, so turbo/fast-play is just `timeline.timeScale(n)`.

## Rule 6: input and accessibility
- Spacebar must trigger spin (bind on `keydown` with `e.code === 'Space'`, `preventDefault`,
  ignore when a modal or input is focused, ignore key repeat).
- Raycast only for in-scene interactive objects (pick-a-box bonus); keep core buttons in the
  HTML HUD so they're crisp, focusable and easy to re-label for social mode.

## Reel implementation sketch (3D cylinder reels)
```ts
// Each reel: a group rotating around X; N symbol slots placed on a cylinder of radius r.
const anglePer = (Math.PI * 2) / slotsPerReel;
for (let i = 0; i < slotsPerReel; i++) {
  const m = new THREE.Mesh(symbolPlane, symbolMaterial(i));
  m.position.set(0, Math.sin(i * anglePer) * r, Math.cos(i * anglePer) * r);
  m.rotation.x = -i * anglePer;
  reel.add(m);
}
// Spin: tween reel.rotation.x by k full turns, then land so the 3 visible slots show the
// book's `reveal.board[reelIndex]` (+ paddingPositions for symbols above/below).
// Swap the materials of the slots that will land in view *before* they rotate into view.
// Stagger reel stops (≈120–200 ms) and slow the last reels when `anticipation[reel] > 0`.
```

## Win presentation
- Highlight winning `positions` from `winInfo` (emissive pulse / outline pass), animate
  the win counter from 0 to `setWin.amount` (tick up across multiple `winInfo` events),
  tier celebrations by `winLevel` (big/mega/epic) with skippable animations.
- Show final amount = `round.payoutMultiplier × bet` in the HUD at `finalWin`.

## Loading
- Show a lightweight HTML loading screen with progress from `THREE.LoadingManager`; load
  only base-game assets first, lazy-load bonus scene assets during idle time.
- Keep the initial download small (aim < ~10 MB compressed for first play).
