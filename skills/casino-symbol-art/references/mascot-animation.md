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
| 2a. Parts rig cut from one image | each joint on its own bone: head at the neck, shoulder, elbow, held item, hair, pet, hem, feet; independent follow-through | one cut-out character PNG plus a small spec of part shapes and joint pivots | **Built and checked** (`spine_parts_rig.py`, below) |
| 2b. Parts rig from separately generated or painted parts | blinking, mouth, hands, anything that needs hidden areas painted | the character as separate parts (head, eyes open and closed, torso, arms, hair, tail, cloth) | **Not built.** Image models do not reliably produce clean separate parts that re-assemble exactly; untested here |
| 3. Hand-rigged Spine | full animation set, mesh deform per part, constraints | layered PSD or part PNGs from an artist | Out of scope for generation: write an artist brief (`symbol-design.md` §7) listing parts, pivots and animation set |

Tier 1 cannot do eyes, mouth, fingers or separate limbs, because the character is one mesh, and it
has a second weakness that was reported on review: it **stretches the art** and cannot tell which
joint is moving, since weights are height bands rather than bones at real joints. Use tier 1 only
for a quick subtle idle on a character you do not need to articulate. For anything with limbs, held
items or a pet, use tier 2a.

## Tier 2a: parts rig with real joints (`spine_parts_rig.py`)
Rigid parts (Spine region attachments) on a bone hierarchy placed at the joints, so nothing stretches;
a part only rotates around its own joint. Steps:
1. Cut the character out (flat key colour, then `spine_idle_rig.py`'s key step or `raster_cutout.py`).
2. Draw a coordinate grid over the image and read pixel coordinates for each joint and part. Example
   spec: `references/examples/mascot_parts_spec.example.json` (priestess with spear and spirit dragon,
   12 bones: hip, chest, head, hair, shoulder and elbow per arm, spear, dragon, skirt, feet).
   Parts are polygons, `capsules` (thin long shapes: spear, limbs) or `circles`, listed back to front.
   One part is `catch_all` and gets every pixel nobody claimed.
3. Build, then check the cut with the colour-coded ownership image:
```sh
python3 skills/casino-symbol-art/scripts/spine_parts_rig.py spec.json --out art/rig --name mascot --debug
```
4. **Joint test** (this is how you see that each bone moves at the right joint): the rig contains a
   `joint_test` animation that swings each bone alone by 18 degrees.
```sh
python3 skills/casino-symbol-art/scripts/spine_preview.py art/rig/mascot --joint-sheet --out art/rig/prev            # all bones
python3 skills/casino-symbol-art/scripts/spine_preview.py art/rig/mascot --joint-sheet --only head,forearm_L --scale 0.8 --out art/rig/key
```
   Each panel marks the pivot (yellow ring). Pass: the part swings around the ring, with no stretched
   art, no piece left behind, and neighbouring parts still overlap. Fix pivots and polygons, rebuild.
5. `idle` and `cheer` previews as in tier 1 (`--anim idle`, `--anim cheer`), then look at the strip for
   doubled shapes.

How it avoids gaps and ghosts: each part is extended `overlap` px (default 8) underneath its neighbours,
so small rotations do not open a seam; stray pieces of the catch-all part that are not connected to its
main body (a missed spear ornament, a hair wisp) are handed to the nearest part automatically, because
otherwise they stay behind as a ghost when that object moves (`--no-adopt` turns this off).

Results on the priestess (721×997): the first cut left a doubled spear in `cheer` (my spear polygon was
too narrow); capsules plus the stray-piece rule fixed it, and the joint test now shows head, shoulder,
elbow and held spear each turning at their own pivot. Final numbers: idle largest vertex displacement
32.5 px (3.3% of height, `--amp 0.5`), feet 0.0 px; cheer 131 px with feet hopping 18 px; no ghost
in the rendered cheer strip. The crack check (new thin seams during motion) reads 237 px in idle and
989 px in cheer against about 5,500 px of seams already present at rest in the artwork itself (hair strands,
cloth edges); it is a number to watch, not a pass or fail on its own.

Limits of 2a: parts are rigid, so cloth and hair bend only as separate parts; the area hidden under a
part is a copy of neighbouring pixels (the overlap), not painted art, so rotations beyond about 10 degrees
show edges (the 18 degree joint test is deliberately harsh); polygons are hand-authored from a grid and
need one or two correction rounds; a tiny stray speck remained near one foot in `cheer`. Blinking and
hands need 2b.

## Tier 1: how to use
```sh
# 1. cut-out hero (the harness plan already asks for a flat magenta key)
python3 skills/casino-symbol-art/scripts/spine_idle_rig.py art/layers/hero.png --out art/rig --name mascot --key "#FF00FF"
#    pivots are fractions of the character height from the top: --neck 0.16 --chest 0.40 --hip 0.55
#    strength: --amp 0.7 (default). Check the pivots on the character: head above --neck, hem below --hip.

# 2. verify with the official runtime and look at it (needs: npm i @esotericsoftware/spine-core@4.2,
#    pip install opencv-python-headless)
python3 skills/casino-symbol-art/scripts/spine_preview.py art/rig/mascot --anim idle --duration 3.2 --frames 32 --out art/rig/preview   # works for tier 1 and tier 2a rigs
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
