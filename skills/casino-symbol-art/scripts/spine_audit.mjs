// Audit of a Spine 4.2 rig with the OFFICIAL spine-core runtime: physics behaviour and mesh distortion data.
// Usage: node spine_audit.mjs rig/mascot.json rig/mascot.atlas idle 3.2 > audit.json   (run where spine-core 4.2 is installed)
// Output (JSON): { physics: [...], meshes: {...}, settle: {...}, fps: {...}, lag: {...} } consumed by rig_audit.py
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(process.cwd() + "/");
const sp = require("@esotericsoftware/spine-core");
const [, , jsonPath, atlasPath, animName, durS] = process.argv;
const T = Number(durS);
const load = () => {
  const atlas = new sp.TextureAtlas(readFileSync(atlasPath, "utf8"));
  for (const p of atlas.pages) p.setTexture({ setFilters() {}, setWraps() {}, dispose() {}, getImage() { return null; } });
  return new sp.SkeletonJson(new sp.AtlasAttachmentLoader(atlas)).readSkeletonData(readFileSync(jsonPath, "utf8"));
};
const data = load();
const anim = data.findAnimation(animName);
const pBones = data.physicsConstraints.map((c) => c.bone.name);
const tip = (b) => { const L = b.data.length; return [b.worldX + b.a * L, b.worldY + b.c * L]; };
const stepper = (skel, dt, loopT) => {
  let t = 0;
  return () => {
    skel.update(dt); skel.setToSetupPose();
    anim.apply(skel, 0, t % T, false, [], 1, sp.MixBlend.setup, sp.MixDirection.mixIn);
    skel.updateWorldTransform(sp.Physics.update);
    t += dt;
  };
};
const out = { physics: data.physicsConstraints.map((c) => ({ name: c.name, bone: c.bone.name, inertia: c.inertia, strength: c.strength, damping: c.damping, mass: 1 / c.massInverse, wind: c.wind, gravity: c.gravity, mix: c.mix, step: c.step })), fps: {}, settle: {}, lag: {}, meshes: {} };

// 1. frame-rate independence: same animation sampled/updated at different rates, tip travel per physics bone
for (const fps of [30, 60, 120]) {
  const skel = new sp.Skeleton(data); const dt = 1 / fps; const step = stepper(skel, dt);
  const r = {}; pBones.forEach((n) => r[n] = [1e9, -1e9, 1e9, -1e9]);
  const total = Math.round(T * fps);
  for (let w = 0; w < 4; w++) for (let k = 0; k < total; k++) {
    step();
    if (w === 3) pBones.forEach((n) => { const [x, y] = tip(skel.findBone(n)); const q = r[n]; q[0] = Math.min(q[0], x); q[1] = Math.max(q[1], x); q[2] = Math.min(q[2], y); q[3] = Math.max(q[3], y); });
  }
  out.fps[fps] = Object.fromEntries(pBones.map((n) => [n, Math.hypot(r[n][1] - r[n][0], r[n][3] - r[n][2])]));
}

// 2. settle after an impulse: the root of the skeleton hip-bone jumps 30 px, then holds; chain must swing and come to rest
{
  const skel = new sp.Skeleton(data); const dt = 1 / 60;
  const root = skel.findBone("hip") || skel.bones[1];
  const restX = root.data.x; const series = {}; pBones.forEach((n) => series[n] = []);
  let base = null;
  for (let k = 0; k < 60 * 6; k++) {
    skel.update(dt); skel.setToSetupPose();
    const t = k * dt; root.x = restX + (t < 0.15 ? 30 * (t / 0.15) : 30);
    skel.updateWorldTransform(sp.Physics.update);
    pBones.forEach((n) => { const b = skel.findBone(n); const [x, y] = tip(b); series[n].push(x - root.x); });
  }
  for (const n of pBones) {
    const s = series[n]; const rest = s[s.length - 1];
    const dev = s.map((v) => Math.abs(v - rest));
    const peak = Math.max(...dev); const at = (sec) => Math.max(...dev.slice(Math.round(60 * sec) - 5, Math.round(60 * sec) + 5));
    out.settle[n] = { peak, at1s: at(1), at2s: at(2), at4s: at(4), final_vs_start: Math.abs(rest - s[0]) };
  }
}

// 3. follow-through: lag of each physics bone's tip behind its physics PARENT's tip (cross-correlation within +-0.5 s)
//    positive = the child lags the parent, which is what secondary motion looks like
{
  const skel = new sp.Skeleton(data); const fps = 60, dt = 1 / fps; const step = stepper(skel, dt);
  const total = Math.round(T * fps); const ser = {};
  pBones.forEach((n) => ser[n] = []);
  for (let w = 0; w < 4; w++) for (let k = 0; k < total; k++) {
    step();
    if (w === 3) pBones.forEach((n) => { const b = skel.findBone(n); const [x, y] = tip(b); ser[n].push(Math.atan2(b.c, b.a)); });   // bone direction angle
  }
  const unwrap = (a) => a.map((v, i) => { let d = v - a[0]; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; return d; });
  const zs = (a) => { const m = a.reduce((s, v) => s + v, 0) / a.length; return a.map((v) => v - m); };
  for (const n of pBones) {
    const par = skel.findBone(n).parent; const pn = par && pBones.includes(par.data.name) ? par.data.name : null;
    if (!pn) { out.lag[n] = { lag_s: null, corr: null, parent: null }; continue; }
    const c0 = zs(unwrap(ser[pn])), c1 = zs(unwrap(ser[n])); let best = -2, bl = 0;
    for (let L = -30; L <= 30; L++) { let c = 0, e1 = 0, e2 = 0; for (let k = 0; k < total; k++) { const a = c0[k], b = c1[(k + L + total) % total]; c += a * b; e1 += a * a; e2 += b * b; } const r = c / Math.sqrt(e1 * e2 + 1e-12); if (r > best) { best = r; bl = L; } }
    out.lag[n] = { lag_s: bl / fps, corr: best, parent: pn };
  }
}

// 4. mesh distortion data: world vertices over the animation (30 fps) plus rest vertices
{
  const skel = new sp.Skeleton(data); const dt = 1 / 30; const step = stepper(skel, dt);
  const slotsMeta = [];
  skel.setToSetupPose(); skel.updateWorldTransform(sp.Physics.update);
  skel.drawOrder.forEach((slot) => { const a = slot.getAttachment(); if (a instanceof sp.MeshAttachment) slotsMeta.push({ name: slot.data.name, tri: Array.from(a.triangles), n: a.worldVerticesLength / 2 }); });
  const rest = {};
  skel.drawOrder.forEach((slot) => { const a = slot.getAttachment(); if (a instanceof sp.MeshAttachment) { const v = new Array(a.worldVerticesLength).fill(0); a.computeWorldVertices(slot, 0, a.worldVerticesLength, v, 0, 2); rest[slot.data.name] = v; } });
  const frames = {}; slotsMeta.forEach((m) => frames[m.name] = []);
  const total = Math.round(T * 30);
  for (let w = 0; w < 4; w++) for (let k = 0; k < total; k++) {
    step();
    if (w === 3) skel.drawOrder.forEach((slot) => { const a = slot.getAttachment(); if (a instanceof sp.MeshAttachment) { const v = new Array(a.worldVerticesLength).fill(0); a.computeWorldVertices(slot, 0, a.worldVerticesLength, v, 0, 2); frames[slot.data.name].push(v.map((x) => Math.round(x * 100) / 100)); } });
  }
  out.meshes = { meta: slotsMeta, rest, frames };
}
process.stdout.write(JSON.stringify(out));
