// Evaluator for symbol_fx.json recipes. No dependencies; use it in a PixiJS ticker or in node.
//   import { evalRecipe } from "./symbol_fx.mjs";
//   const fx = evalRecipe(recipes.win, elapsedSeconds);   // { scaleX, scaleY, rotation, alpha, y, glow } (only tracks the recipe has)
//   sprite.scale.set(fx.scaleX ?? 1, fx.scaleY ?? 1); sprite.angle = fx.rotation ?? 0; sprite.alpha = fx.alpha ?? 1;
// Looping recipes wrap around their duration; one-shot recipes hold their last value. Give each symbol a random start
// offset for `idle` so the whole grid does not breathe in sync.
export const ease = {
  linear: (t) => t,
  sine: (t) => 0.5 - 0.5 * Math.cos(Math.PI * t),
  outQuad: (t) => 1 - (1 - t) * (1 - t),
  outBack: (t) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
};
export function evalRecipe(r, time) {
  const T = r.duration; const t = r.loop ? ((time % T) + T) % T : Math.min(Math.max(time, 0), T);
  const out = {};
  for (const [name, keys] of Object.entries(r.tracks)) {
    let v = keys[keys.length - 1][1];
    for (let i = 1; i < keys.length; i++) {
      if (t <= keys[i][0]) {
        const [t0, v0] = keys[i - 1]; const [t1, v1, e] = keys[i];
        const u = t1 > t0 ? (t - t0) / (t1 - t0) : 1; v = v0 + (v1 - v0) * (ease[e] || ease.linear)(u); break;
      }
    }
    out[name] = v;
  }
  return out;
}
// CLI: node symbol_fx.mjs recipes.json recipeName fps  -> JSON array of samples over one duration (plus the end point)
if (import.meta.url === `file://${process.argv[1]}`) {
  const fs = await import("node:fs"); const [, , file, name, fps] = process.argv;
  const rec = JSON.parse(fs.readFileSync(file, "utf8"))[name]; const n = Math.round(rec.duration * Number(fps));
  const s = []; for (let k = 0; k <= n; k++) s.push({ t: (rec.duration * k) / n, ...evalRecipe(rec, (rec.duration * k) / n) });
  process.stdout.write(JSON.stringify({ name, loop: rec.loop, duration: rec.duration, samples: s }));
}
