# Mascot animation (idle, cheer) and Spine

The big studios keep a large character beside the reels alive with a looping idle. Measured on
recorded Angel of Asgard gameplay (Valkyrie): the pixels around the hero change about 4 to 10 times
more between frames than the backdrop does, concentrated in the upper third (head, wings, hair); in
Loki's Vault, which has no hero, the same region is static. The footage was sampled at 4 fps, so
amplitude and period were not recovered; only "continuous, mostly upper body" is established.

## What an agent can and cannot produce

| Tier | What | Input | Status |
|---|---|---|---|
| 1. Mesh idle from one image | breathing, head bob and tilt, weight shift, hem sway, feet planted; plus a `cheer` hop | one cut-out character PNG (the `hero` layer) | **Built and checked** with the official Spine 4.2 runtime (see below) |
| 2. Layered parts rig | blinking, arm and tail motion, hair and cloth with their own bones | the character generated or painted as separate parts (head, eyes open and closed, torso, arms, hair, tail, cloth) | **Not built.** Image models do not reliably produce a character as clean separate parts that re-assemble exactly; untested here |
| 3. Hand-rigged Spine | full animation set, mesh deform per part, constraints | layered PSD or part PNGs from an artist | Out of scope for generation: write an artist brief (`symbol-design.md` §7) listing parts, pivots and animation set |

Tier 1 cannot do eyes, mouth, fingers or separate limbs, because the character is one mesh. If the
game design needs a blink or a waving hand, go to tier 2 or 3 for that character.

## Tier 1: how to use
```sh
# 1. cut-out hero (the harness plan already asks for a flat magenta key)
python3 skills/casino-symbol-art/scripts/spine_idle_rig.py art/layers/hero.png --out art/rig --name mascot --key "#FF00FF"
#    pivots are fractions of the character height from the top: --neck 0.16 --chest 0.40 --hip 0.55
#    strength: --amp 0.7 (default). Check the pivots on the character: head above --neck, hem below --hip.

# 2. verify with the official runtime and look at it (needs: npm i @esotericsoftware/spine-core@4.2,
#    pip install opencv-python-headless)
python3 skills/casino-symbol-art/scripts/spine_preview.py art/rig/mascot --anim idle --duration 3.2 --frames 32 --out art/rig/preview
python3 skills/casino-symbol-art/scripts/spine_preview.py art/rig/mascot --anim cheer --duration 1.4 --frames 28 --out art/rig/preview
```
Output: `mascot.json` (Spine 4.2 skeleton, one weighted mesh, bones root, hip, chest, head, skirt, feet),
`mascot.atlas`, `mascot.png`, and a GIF plus a key-frame strip per animation. Pass: no torn or folded
mesh in the strip, feet travel 0.0 px in `idle`, idle displacement about 2 to 3 percent of the
character height (subtle), `cheer` clearly larger and returning to the setup pose.

Result on the generated priestess (721×997 px): idle largest vertex displacement 26.7 px (2.7 percent
of height), feet 0.0 px; cheer 47.9 px, feet hop 25.6 px; the rig loads and evaluates in
spine-core 4.2.120 for both animations.

## Wiring into the Pixi build (not tested here)
Use the Spine runtime that matches the data version: `@esotericsoftware/spine-pixi-v8` 4.2.x for
PixiJS 8. Typical pattern from its documentation:
```ts
Assets.add({ alias: 'mascotData', src: 'assets/mascot.json' });
Assets.add({ alias: 'mascotAtlas', src: 'assets/mascot.atlas' });
await Assets.load(['mascotData', 'mascotAtlas']);
const mascot = Spine.from({ skeleton: 'mascotData', atlas: 'mascotAtlas' });
mascot.state.setAnimation(0, 'idle', true);
// on a Big Win: mascot.state.setAnimation(0, 'cheer', false); mascot.state.addAnimation(0, 'idle', true, 0);
```
Place the mascot outside the reel window, left of the grid (see `style-valkyrie-hacksaw.md` §1).
The atlas is non-premultiplied (`pma:false`). The Spine runtimes are licensed by Esoteric Software;
shipping a game with them needs a Spine licence, which this repo does not grant. Stake builds must
stay static: bundle the three files, no remote loading.

## Limits and honest notes
- Weights are height bands (head, chest, skirt, feet), not painted per body part. Anything that
  crosses a band (a spear, a long cape, a flying creature beside the body) deforms with the band it
  sits in; check the strip for stretching on such parts, and raise `--rows` or mask them out.
- Idle and cheer amplitudes are authored values, not copied from a studio.
- One character per rig. Several mascots mean several runs and a consistent pivot choice.
