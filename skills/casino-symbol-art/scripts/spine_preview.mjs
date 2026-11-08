// Loads a rig made by spine_idle_rig.py with the OFFICIAL spine-core runtime (no GL needed) and writes
// the world-space mesh vertices over time, so the animation can be checked (and rendered) without a Spine editor.
// Usage: node spine_preview.mjs rig/mascot.json rig/mascot.atlas idle 3.2 16 > frames.json
// Needs: npm i @esotericsoftware/spine-core@4.2
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(process.cwd() + "/");
const sp = require("@esotericsoftware/spine-core");
const [, , jsonPath, atlasPath, anim, dur, steps] = process.argv;
const atlas = new sp.TextureAtlas(readFileSync(atlasPath, "utf8"));
for (const p of atlas.pages) p.setTexture({ setFilters() {}, setWraps() {}, dispose() {}, getImage() { return null; } });
const loader = new sp.AtlasAttachmentLoader(atlas);
const data = new sp.SkeletonJson(loader).readSkeletonData(readFileSync(jsonPath, "utf8"));
const skel = new sp.Skeleton(data);
const a = data.findAnimation(anim);
if (!a) { console.error("no animation " + anim + "; have: " + data.animations.map((x) => x.name)); process.exit(2); }
const n = Number(steps), T = Number(dur);
const out = { animation: anim, duration: a.duration, bones: data.bones.map((b) => b.name), frames: [] };
const slot = skel.slots[0];
for (let k = 0; k < n; k++) {
  const t = (T * k) / n;
  skel.setToSetupPose();
  a.apply(skel, 0, t, false, [], 1, sp.MixBlend.setup, sp.MixDirection.mixIn);
  skel.updateWorldTransform(sp.Physics.update);
  const mesh = slot.getAttachment();
  const v = new Array(mesh.worldVerticesLength).fill(0);
  mesh.computeWorldVertices(slot, 0, mesh.worldVerticesLength, v, 0, 2);
  out.frames.push({ t, v: v.map((x) => Math.round(x * 100) / 100) });
}
out.triangles = Array.from(slot.getAttachment().triangles);
out.uvs = Array.from(slot.getAttachment().uvs);
process.stdout.write(JSON.stringify(out));
