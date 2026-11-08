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

### Seamless legs and skirt (soft mesh) and the ankle seam
A review of the idle found the two lower legs misaligned at the ankle: the legs were part of the swaying
skirt while the feet were planted, so the shin shifted up to **11 px** sideways against the boot. Parts
that must stay continuous between bones that move differently are now weighted meshes: a part with `"soft"`
becomes a Spine mesh whose weights run from the hip (top) through a `hem` bone (middle) to the `feet` bone
(bottom, same motion as the boots). Measured after the fix: the shift at the ankle seam is **0.00 px**
(feet 0.00 px), mid-leg 3.6 px, so nothing tears.

### Advanced rigging for hair and clothing (bone chains and physics)
Hair and cloth need chains of small bones, not one rotating plate.
- **Chains:** `hair1..hair4` hang from the head, `flapR1..flapR4` and `flapL1..flapL3` from the hip. Bone length is the distance
  to the next pivot. **Chain bones are rotated to point along the chain** (toward the next bone): Spine's rotate-physics only
  deflects a bone when it moves perpendicular to the bone's own axis, so a hair bone left pointing +x while the hair hangs down
  barely reacts (found by the audit, see below). Local positions and mesh weights are computed in each bone's rotated frame.
- **Weights:** a soft part uses `"chain": [{"bone", "y"}, ...]` (weights come from projecting each vertex onto the chain's own
  polyline, so weight bands run perpendicular to the strand and do not shear) and `"zones": [{"x": [x0, x1], "falloff", "y_end",
  "chain": [...]}]` that blend a chain into a region of the skirt mesh (the side flaps). **`falloff` is the transition width: strain
  is roughly (flap displacement) / falloff, so keep it wide (60 to 110 px here); 25 px tore the skirt.**
- **Motion:** chain bones are not keyed (a keyed sine looks mechanical). A Spine 4.2 **physics constraint** on each
  (`"physics": "hair" | "cloth" | "tail"`, presets in `PHYSICS`) reacts to the body motion, and a **wind timeline** with two
  harmonics and a different phase per chain (`--sway`, default 0.45) supplies the gentle breeze. Wind is in rotation-physics units and
  accumulates down a chain (each bone adds its angle to its parent's), so a value that looks small is not: 7 shook the hair 186 px
  and folded the mesh; 0.45 gives a 21 px hair tip.
- **Every physics constraint needs a unique `order`.** The builder first wrote all of them as 0 and Spine's update cache then
  activated only ONE of the 11 constraints, so hair and cloth were moving only by keyframes. The audit exposed it (zero reaction to an impulse).

### Audit: `rig_audit.py` (run it before trusting a rig)
```sh
python3 skills/casino-symbol-art/scripts/rig_audit.py art/rig/mascot --anim idle --duration 3.2     # needs spine-core 4.2 installed
python3 skills/casino-symbol-art/scripts/rig_audit.py art/rig/mascot --anim cheer --duration 1.4
```
Uses the official runtime (`spine_audit.mjs`) and prints pass, WARN or FAIL per item (thresholds in `THRESH`):
- **Distortion**, per weighted mesh over the whole animation: triangle area and edge-length ratio against the rest pose (1.00 is untouched)
  and folded triangles. ok: area 0.85 to 1.20 and edges 0.90 to 1.12; WARN beyond that; FAIL beyond 0.70 to 1.40 area, 0.80 to 1.25 edges, or any fold.
- **Physics**, per constraint: swing after a 30 px impulse and how much is left after 2 s and 4 s (settles, does not explode);
  idle travel at 30 Hz and 120 Hz (frame-rate independence, ratio 0.8 to 1.25); lag of each bone behind its physics parent
  (0.02 to 0.40 s with correlation of 0.5 or more: follow-through, not lock-step).

Result on the priestess after the fixes (idle / cheer): 0 FAIL, 3 WARN each. Hair mesh area 0.92 to 1.09 and edges 0.89 to 1.15
(10 to 15 percent strain at worst, WARN); skirt ok in idle (0.93 to 1.09) and WARN in cheer (0.84 to 1.11). Physics: impulse swing grows toward
the tip (12 to 36 px), settles in under 2 s, 30 Hz and 120 Hz travel agree to within 1 percent, lag behind the parent grows along the
chain (hair 0.18, 0.32, 0.38 s). Remaining WARN: the last two cloth bones lag 0.50 s behind their parent, a little heavy. Close-up
renders of hair and flaps show the lotus pattern and face unchanged, no visible stretch. Idle tip travel: hair 21 px, right flap 18 px, left flap 6 px.
Also changed: the cheer hem swing went from 6 to 2.5 degrees because it tore the skirt (edge ratio 0.70).

What the audit cannot judge: whether the motion looks pleasing. It proves the motion is stable, frame-rate independent, continuous with the
art and lagged along the chain; amplitude and style are still a human call on the video.

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
