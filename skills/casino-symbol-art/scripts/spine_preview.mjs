// Loads a rig (spine_idle_rig.py or spine_parts_rig.py) with the OFFICIAL spine-core runtime (no GL needed) and writes
// world-space vertices of every slot over time, so the animation can be checked and rendered without a Spine editor.
// Usage: node spine_preview.mjs rig/mascot.json rig/mascot.atlas idle 3.2 32 > frames.json
// Needs: npm i @esotericsoftware/spine-core@4.2
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(process.cwd() + "/");
const sp = require("@esotericsoftware/spine-core");
const [, , jsonPath, atlasPath, anim, dur, steps] = process.argv;
const atlas = new sp.TextureAtlas(readFileSync(atlasPath, "utf8"));
for (const p of atlas.pages) p.setTexture({ setFilters() {}, setWraps() {}, dispose() {}, getImage() { return null; } });
const data = new sp.SkeletonJson(new sp.AtlasAttachmentLoader(atlas)).readSkeletonData(readFileSync(jsonPath, "utf8"));
const skel = new sp.Skeleton(data);
const a = data.findAnimation(anim);
if (!a) { console.error("no animation " + anim + "; have: " + data.animations.map((x) => x.name)); process.exit(2); }
const n = Number(steps), T = Number(dur);
const verts = (slot) => {
  const att = slot.getAttachment();
  if (att instanceof sp.MeshAttachment) { const v = new Array(att.worldVerticesLength).fill(0); att.computeWorldVertices(slot, 0, att.worldVerticesLength, v, 0, 2); return v; }
  if (att instanceof sp.RegionAttachment) { const v = new Array(8).fill(0); att.computeWorldVertices(slot, v, 0, 2); return v; }
  return null;
};
skel.setToSetupPose(); skel.updateWorldTransform(sp.Physics.update);
const meta = skel.drawOrder.map((slot) => {
  const att = slot.getAttachment();
  if (att instanceof sp.MeshAttachment) return { name: slot.data.name, type: "mesh", triangles: Array.from(att.triangles), uvs: Array.from(att.uvs) };
  if (att instanceof sp.RegionAttachment) return { name: slot.data.name, type: "region", triangles: [0, 1, 2, 2, 3, 0], uvs: Array.from(att.uvs) };
  return { name: slot.data.name, type: "none" };
});
const out = { animation: anim, duration: a.duration, bones: data.bones.map((b) => b.name), slots: meta, frames: [] };
for (let k = 0; k < n; k++) {
  const t = (T * k) / n;
  skel.setToSetupPose();
  a.apply(skel, 0, t, false, [], 1, sp.MixBlend.setup, sp.MixDirection.mixIn);
  skel.updateWorldTransform(sp.Physics.update);
  out.frames.push({ t, slots: skel.drawOrder.map((slot) => { const v = verts(slot); return v ? v.map((x) => Math.round(x * 100) / 100) : null; }) });
}
process.stdout.write(JSON.stringify(out));
