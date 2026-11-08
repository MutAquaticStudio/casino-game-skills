// Capture a slot game at phone and PC sizes, for layout review and for comparing what changes between devices.
// Usage: node mobile_capture.mjs --url <game page or game url> --out shots/ [--presets phone-390x844,phone-360x800,phone-375x667,phone-412x915,phone-844x390,pc-1280x720]
//        [--iframe] [--tap-start] [--spins 0] [--log-requests "valkyrie|engine"]
//   --iframe        the page embeds the game in an <iframe>: make the first iframe fill the viewport (a game picks its layout from its own window size)
//   --tap-start     tap the middle of the screen once after load (start / continue screens)
//   --spins N       press Space N times, 6.5 s apart, and save a mid-spin and an after-spin shot
//   --log-requests  regex: write every matching response (url, type, bytes) to <out>/requests_<preset>.json, to diff the asset lists between devices
// Phone presets are emulated: touch, device pixel ratio 2, a mobile user agent. Needs: playwright (node), a browser installed.
import { createRequire } from "node:module";
import fs from "node:fs";
const require = createRequire(process.cwd() + "/");
const { chromium } = require("playwright");
const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => v.startsWith("--") ? [...a, [v.slice(2), arr[i + 1] && !arr[i + 1].startsWith("--") ? arr[i + 1] : true]] : a, []));
if (!args.url || !args.out) { console.error("need --url and --out"); process.exit(2); }
fs.mkdirSync(args.out, { recursive: true });
const presets = String(args.presets || "phone-390x844,phone-360x800,phone-375x667,phone-412x915,phone-844x390,pc-1280x720").split(",");
const UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1";
const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
for (const pr of presets) {
  const m = /^(phone|pc)-(\d+)x(\d+)$/.exec(pr); if (!m) { console.log("skip", pr); continue; }
  const phone = m[1] === "phone", W = +m[2], H = +m[3];
  const ctx = await b.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: phone ? 2 : 1, isMobile: phone, hasTouch: phone, ...(phone ? { userAgent: UA } : {}) });
  const p = await ctx.newPage(); const reqs = [];
  if (args["log-requests"]) { const re = new RegExp(args["log-requests"]); p.on("response", (r) => { const u = r.url(); if (re.test(u)) { const h = r.headers(); reqs.push({ url: u.split("?")[0], type: h["content-type"] || "", bytes: Number(h["content-length"] || 0) }); } }); }
  try {
    await p.goto(args.url, { waitUntil: "domcontentloaded", timeout: 60000 });
    if (args.iframe) {
      await p.waitForSelector("iframe", { timeout: 60000 }); await p.waitForTimeout(8000);
      await p.evaluate(() => { const f = document.querySelector("iframe"); f.style.cssText = "position:fixed;left:0;top:0;width:100vw;height:100vh;z-index:999999;border:0;background:#000"; document.body.style.overflow = "hidden"; });
    }
    await p.waitForTimeout(8000);
    const tap = async () => phone ? p.touchscreen.tap(W / 2, H / 2) : p.mouse.click(W / 2, H / 2);
    if (args["tap-start"]) { await tap(); await p.waitForTimeout(6000); }
    await p.screenshot({ path: `${args.out}/${pr}_idle.png` });
    for (let i = 0; i < Number(args.spins || 0); i++) {
      await p.keyboard.press("Space"); await p.waitForTimeout(700);
      if (i === 0) await p.screenshot({ path: `${args.out}/${pr}_spin.png` });
      await p.waitForTimeout(5800);
    }
    if (Number(args.spins || 0)) await p.screenshot({ path: `${args.out}/${pr}_after.png` });
    console.log(pr, "ok", reqs.length ? `${reqs.length} responses logged` : "");
  } catch (e) { console.log(pr, "fail", String(e.message).slice(0, 120)); }
  if (reqs.length) fs.writeFileSync(`${args.out}/requests_${pr}.json`, JSON.stringify(reqs));
  await ctx.close();
}
await b.close();
