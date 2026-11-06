---
name: "stake-casino-game-dev"
description: "Ideate, build, balance, review and submit casino/slot games for Stake Engine: deep multi-mode gameplay, Stake-compliant win celebrations, localization, Math SDK, RGS API, PixiJS 8 (latest) and Three.js frontends, approval checklist."
---

# Casino game development for Stake Engine

Turns a game idea into a game that can pass Stake Engine approval. Combines: Stake Engine
rules/process (official docs https://stakeengine.github.io/docs/, repo `StakeEngine/docs`,
summarised Nov 2026), rendering with PixiJS 2D or Three.js 3D, and general game-dev craft
(game feel, UI/UX, audio, performance – in the spirit of `gamedev-skills/awesome-gamedev-agent-skills`
and `CloudAI-X/threejs-skills`).

Answer in the user's language (often Vietnamese); keep code, file names and Stake terms in English.
When a rule is decisive and network access exists, re-check the live docs (or clone
`StakeEngine/docs` and grep `src/routes/docs/`; it also ships an MCP server in `mcp-server/`).

---

## 1. The mental model everything depends on

Stake Engine games are **pre-computed and stateless**. The developer simulates every round
offline and uploads static files per bet mode: a **lookup table** (CSV, no header:
`sim_id,weight,payoutMultiplier`) and a zstd-compressed JSONL **book** (line i =
`{"id": i, "payoutMultiplier": p, "events": [...]}`), listed in `index.json`. On `/wallet/play`
the RGS picks one sim by weighted random selection and returns its events. The **frontend is
only an animation layer**: render exactly what the book says, show the payout the RGS
returned, never compute or change a win in the browser.

Consequences:
- **Forbidden**: jackpots, gamble/double-up, continuation, early cashout, any state carried
  between rounds. Each bet is independent. If asked, explain and offer a stateless
  alternative (bonus-buy mode, multipliers inside one round, feature mode).
- Multipliers have 2-decimal granularity: integers ×100 (150 = 1.5x).
- RTP is fully determined by LUT weights: `RTP = Σ w·p / (100 · cost · Σ w)`.
- After approval only minor visual fixes are allowed – no math, mode or mechanic changes.
  Get the math right before submitting.

## 2. Hard restrictions (rejection)
- Original game only; no pre-purchased/licensed games that exist elsewhere.
- IP-clean names, titles, assets; title unique, no "Megaways"/"Xways"-type trademarks.
- No Stake™/Kick™ branding or themes. Unique art and audio – Web SDK sample assets are rejected.
- Nothing offensive, explicit, discriminatory, in poor taste; nothing appealing to minors
  (incl. child-like characters). Reviewer discretion applies.

## 3. Workflow

### Phase 1 – Concept & compliance pre-check
Design the concept with §7 (depth stack, full mode ladder, engagement beats, responsible-design
check) – never stop at "spin → line win → done". Then pin down grid, theme, target RTP
(90–98%), wincap, volatility, and screen against §2. Deliver the §7 concept doc. For "make me a
slot game", do this in a short exchange before code – unless the user wants a quick visual
prototype, in which case say clearly it uses mock books and is not approval-ready.

### Phase 2 – Math (Math SDK, Python; repo `StakeEngine/math-sdk`, MIT)
Setup: `git clone https://github.com/StakeEngine/math-sdk && cd math-sdk && make setup`,
then `make run GAME=0_0_lines`. Copy `games/template/`, or the nearest sample:
`0_0_lines` (5×3, 20 lines), `0_0_ways`, `0_0_scatter` (pay-anywhere + tumble), `0_0_cluster`,
`0_0_expwilds`, `0_0_lines_feature_match`, `fifty_fifty`.

Game folder: `run.py` (sim counts, threads, compression, which steps run), `game_config.py`
(symbols, paytable, reels, bet modes), `gamestate.py` (`run_spin()`/`run_freespin()` = one
simulation), `game_executables.py`, `game_calculations.py`, `game_events.py`,
`game_override.py`, `reels/`, generated `library/{books,books_compressed,configs,forces,lookup_tables,publish_files}`.

```python
# run.py
num_threads = 10; rust_threads = 20; batching_size = 50000
compression = True                       # False → readable .json books for debugging
num_sim_args = {"base": int(1e5), "bonus": int(1e5)}   # keys = bet mode names
run_conditions = {"run_sims": True, "run_optimization": True,
                  "run_analysis": True, "upload_data": False}
```
Loop: 100 uncompressed sims, no optimisation → inspect events → 1e4 with optimisation →
final 100k–1M per mode, compressed. `run_analysis` writes a PAR sheet.

Bet modes and distributions:
```python
BetMode(name="bonus", cost=100.0, rtp=self.rtp, max_win=self.wincap,
        auto_close_disabled=False, is_feature=False, is_buybonus=True,
        distributions=[
          Distribution(criteria="wincap", quota=0.001, win_criteria=self.wincap,
                       conditions={"reel_weights": {...}, "force_wincap": True,
                                   "force_freegame": True, "mult_values": {...}}),
          Distribution(criteria="freegame", quota=0.999,
                       conditions={"reel_weights": {...}, "force_freegame": True}),
        ])
```
- `quota` = share of the mode's sims meeting the criteria. Base modes typically use
  `wincap`, `freegame`, `0` (`win_criteria=0.0`), `basegame`.
- Required condition keys `reel_weights`, `force_wincap`, `force_freegame`; extra keys are read
  via `get_random_outcome(betmode.get_distribution_conditions()['mult_values'])`.
- `auto_close_disabled=True` for rounds with player decisions (then the frontend calls end-round
  and should send `/bet/event` progress). `is_feature`: mode stays selected each spin.
  `is_buybonus`: frontend knows it was bought.
- Standard events (`src/events/event_constants.py`): `reveal` (board, paddingPositions,
  gameType, anticipation), `winInfo` (totalWin, wins[symbol, kind, win, positions, meta]),
  `setWin` (amount, winLevel), `setTotalWin`, `freeSpinTrigger`, `freeSpinRetrigger`,
  `enterBonus`, `updateFreeSpin`, `tumbleBoard`, `setTumbleWin`, `updateTumbleWin`,
  `updateGlobalMult`, `freeSpinEnd`, `wincap`, `finalWin`. Amounts are ×100 of base bet.
  Each custom event needs a frontend handler; keep books lean.
- Optimiser adjusts LUT weights to hit RTP/hit-rate targets (`game_optimization.py`;
  advanced: `StakeEngine/convex-optimizer`). `forces/force_<mode>.json` lists sims by feature –
  use it to find replay IDs (wincap, bonus trigger).

Upload files (`library/publish_files/`): `index.json`
`{"modes":[{"name":"base","cost":1.0,"events":"books_base.jsonl.zst","weights":"lookUpTable_base_0.csv"}, ...]}`,
the books and LUTs. Enforced: book `id` == line index, LUT payout == book payout exactly
(hashed), uint64 integers, one LUT row per book line. Math may be written without the SDK if
it produces exactly these files.

**Math approval thresholds**

| Check | Threshold |
|---|---|
| RTP per mode | 90.0–98.0% |
| Spread between modes | ≤ 0.5% (base 97% → others 96.5–97.5%) |
| Max win | matches rules; obtainable – checklist: ≥ 1 in 20,000,000 (docs text: typically more often than 1 in 10M) |
| Sims (slot-type) | 100k–1M per mode |
| Non-zero win hit-rate | ≥ 1 in 20; base typically 1 in 3–8 |
| Losing share | not overwhelming (90k losses / 100k may be rejected) |
| Dominant outcome | no single sim dominating if visuals imply variety |
| Base volatility | std dev within industry norms |
| Zero-weight rows | must not dominate; report count of non-zero-weight payouts |
| Win ranges | no gaps between small wins and max win |
| Mode cost | correctly stated in rules |

Balancing levers: distribution quotas, reel strips and `reel_weights`, multiplier weights,
scatter trigger weights, paytable, optimiser targets. Bonus-buy price ≈ E[bonus payout] /
target RTP; tune the distribution, not the price, to stay in the 0.5% band.

Validate after every full run – write this script to `tools/validate_math.py` and run
`python tools/validate_math.py games/<g>/library/publish_files` (needs `pip install zstandard`):

```python
import csv, io, json, math, os, sys
d = sys.argv[1]; fails = []
def say(lvl, m, msg):
    print(f"[{lvl}] {m}: {msg}"); fails.append(msg) if lvl == "FAIL" else None
idx = json.load(open(os.path.join(d, "index.json"))); rtps = {}
for md in idx["modes"]:
    name, cost = md["name"], float(md["cost"])
    lut = [tuple(int(x) for x in r) for r in csv.reader(open(os.path.join(d, md["weights"]))) if r]
    if [r[0] for r in lut] != list(range(len(lut))): say("FAIL", name, "LUT ids not 0..N-1")
    bp = os.path.join(d, md["events"])
    if os.path.exists(bp):
        if bp.endswith(".zst"):
            import zstandard
            fh = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(open(bp, "rb")), encoding="utf-8")
        else: fh = open(bp, encoding="utf-8")
        n = bad = 0
        for i, line in enumerate(l for l in fh if l.strip()):
            o = json.loads(line); n += 1
            if o["id"] != i or i >= len(lut) or o["payoutMultiplier"] != lut[i][2]: bad += 1
        if bad or n != len(lut): say("FAIL", name, f"book/LUT mismatch: {bad} bad, {n} lines vs {len(lut)} rows")
    W = sum(w for _, w, _ in lut); m = [(w, p / 100 / cost) for _, w, p in lut]
    rtp = sum(w * x for w, x in m) / W; rtps[name] = rtp
    std = math.sqrt(sum(w * (x - rtp) ** 2 for w, x in m) / W)
    hit = W / max(1, sum(w for _, w, p in lut if p > 0))
    maxp = max(p for _, w, p in lut if w > 0); maxhit = W / sum(w for _, w, p in lut if p == maxp)
    say("PASS" if .90 <= rtp <= .98 else "FAIL", name, f"RTP {rtp*100:.3f}%")
    say("PASS" if maxhit <= 2e7 else "FAIL", name, f"max win {maxp/100:.2f}x, 1 in {maxhit:,.0f}")
    if cost == 1: say("PASS" if hit <= 20 else "FAIL", name, f"hit-rate 1 in {hit:.2f}")
    if len(lut) < 1e5: say("WARN", name, f"only {len(lut):,} sims")
    top = max(w for _, w, _ in lut) / W
    if top > .05: say("WARN", name, f"top single outcome {top*100:.1f}% of weight")
    print(f"    std {std:.2f}, zero-weight rows {sum(1 for _, w, _ in lut if w == 0):,}")
if len(rtps) > 1:
    s = max(rtps.values()) - min(rtps.values())
    say("PASS" if s <= .005 else "FAIL", "all", f"RTP spread {s*100:.3f}%")
sys.exit(1 if fails else 0)
```
Also eyeball win-range gaps in the PAR sheet. Fix math failures before frontend work.

### Phase 3 – Frontend
The build must be **static** (HTML/CSS/JS + assets; SvelteKit → `adapter-static`; Vite →
`base: './'`). Any framework works. Choose the renderer:
- **PixiJS 8 + Svelte 5 + GSAP** – ecosystem default and the official Web SDK
  (`StakeEngine/web-sdk`: Turborepo, Storybook to play each book event, XState, sample apps
  lines/ways/scatter/cluster/price/number-picker). Spine or spritesheets for animation.
  See §12 for current PixiJS (8.22) patterns, slot architecture and performance.
- **Three.js** – for real 3D (cylinder reels, plinko, dice, wheels, coin showers, camera
  moves); see §5. If the game is a flat 5×3 slot, recommend Pixi (same look, less GPU).

Architecture: **RGS client → round controller → book event player → handlers → renderer**,
with HUD/UI state separate. One async handler per event `type`, awaited in order; unknown types
log in dev and are skipped. Use the same code path for live play, resume-after-reload and replay.

Minimal RGS client (TypeScript, no deps):
```ts
export const AMOUNT_MULT = 1_000_000;            // money = integers with 6 decimals
const q = new URLSearchParams(location.search);
const host = q.get('rgs_url') ?? '';
export const P = {
  sessionID: q.get('sessionID') ?? '', rgsUrl: /^https?:/.test(host) ? host : `https://${host}`,
  lang: q.get('lang') ?? 'en', currency: q.get('currency') ?? 'USD',
  device: q.get('device') === 'mobile' ? 'mobile' : 'desktop',
  social: q.get('social') === 'true', demo: q.get('demo') === 'true', replay: q.get('replay') === 'true',
  game: q.get('game'), version: q.get('version'), mode: q.get('mode'), event: q.get('event'),
  amount: q.get('amount') ? Number(q.get('amount')) : undefined,
};
async function post<T>(path: string, body: object): Promise<T> {
  const r = await fetch(P.rgsUrl + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const d: any = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d?.code ?? d?.error?.code ?? (typeof d?.error === 'string' ? d.error : 'ERR_GEN'));
  return d;
}
export const rgs = {
  authenticate: () => post<any>('/wallet/authenticate', { sessionID: P.sessionID, language: P.lang }),
  balance: () => post<any>('/wallet/balance', { sessionID: P.sessionID }),
  play: (amountRaw: number, mode: string) => post<any>('/wallet/play', { sessionID: P.sessionID, amount: amountRaw, mode, currency: P.currency }),
  endRound: () => post<any>('/wallet/end-round', { sessionID: P.sessionID }),   // only if payout > 0
  event: (i: number) => post<any>('/bet/event', { sessionID: P.sessionID, event: String(i) }),
  replay: () => fetch(`${P.rgsUrl}/bet/replay/${P.game}/${P.version}/${P.mode}/${P.event}`).then(r => r.json()),
};
export const winRaw = (betRaw: number, payoutMultiplier: number) => Math.round(betRaw * payoutMultiplier);
export const bookToRaw = (betRaw: number, bookAmount: number) => Math.round(betRaw * bookAmount / 100);
```
Round flow: parse URL → replay? (Phase 5) → `authenticate` (balance, `round` = active or last round,
`config{minBet,maxBet,stepBet,defaultBetLevel,betLevels,betModes}`; ignore `jurisdiction`/`meta`)
→ if `round` is active, replay its state then end-round → idle → `play` (debit; `round.state` =
events) → animate → `end-round` only if `payoutMultiplier > 0` (zero-payout rounds auto-complete)
→ update balance. Bet levels: offer every value in `betLevels` incl. min/max; `defaultBetLevel`
is an amount (e.g. 1000000), not an index; persist the chosen bet per currency (localStorage in
try/catch) so a refresh mid-spin keeps it. Real debit = amount × mode cost – show it.

Errors (400): `ERR_VAL` invalid request, `ERR_IPB` insufficient balance, `ERR_IS` invalid/expired
session, `ERR_ATE` auth failed, `ERR_GLE` gambling limits, `ERR_LOC` location; (500) `ERR_GEN`,
`ERR_MAINTENANCE`. Show a clear message for each (social wording on stake.us, e.g. "Not enough coins").

Money display: amount / 1e6 with currency decimals – USD 2, EUR 2, JPY 0, Gold Coins `XGC` →
"10.00 GC", Stake Cash `XSC` → "10.00 SC" (no `$`). Full list: docs `reference/currencies`.

**Required UI / behaviour** (layout and sizing of the bet UI: §13)
- Rules/info screen reachable anytime: full rules; UI guide for every button; RTP and max win
  per mode; cost + description of each mode; payout for every symbol combination; win
  combinations (line diagram, cluster sizes, scatter counts); all special-symbol values;
  feature trigger/retrigger rules ("3 scatters award 10 free spins, 4 award 15…").
- Disclaimer covering malfunction voids, connection required, reload to finish rounds, return
  over many plays, display illustrative, settled by RGS not browser, TM/©. Template:
  "Malfunction voids all wins and plays. A consistent internet connection is required. In the
  event of a disconnection, reload the game to finish any uncompleted rounds. The expected
  return is calculated over many plays. The game display is not representative of any
  physical device and is for illustrative purposes only. Winnings are settled according to the
  amount received from the Remote Game Server and not from events within the web browser.
  TM and © 2025 Stake Engine."
- Change bet; balance visible; final win shown; with several wins the counter ticks up step by
  step to the total; sound on/off; **spacebar = bet button** (ignore key repeat and focused
  inputs/dialogs); autoplay needs a confirmation step; switching to a mode costing > 2× needs
  confirmation; turbo/fast-play keeps wins legible.
- Viewports: Desktop 1200×675, Laptop 1024×576, Popout L 800×450, **Popout S 400×225**,
  Mobile L 425×812, M 375×667, S 320×568. Mini-player must not distort the board.
- English required; unsupported `lang` must not corrupt text. Tested with many currencies.
- No external requests (strict XSS policy): bundle fonts (no Google Fonts), no CDNs/analytics;
  no console errors; no game info logged.

**Social mode (stake.us, `social=true`)** – English with replacements regardless of `lang`, in
rules, labels, popups, errors, replay window and images (no "BUY"/"BET" baked into art):
bet/bets/betting → play/plays/playing; total bet → total play; bonus buy → bonus/feature;
buy bonus → get bonus; buy/purchase → play; bought → instantly triggered; cash/money/credit →
coins; currency → token; pay/pays/pays out → win/wins/win; paid/paid out → won; pay table →
win table; payer → winner; stake → play amount; wager/gamble → play; cost of → can be played
for; at the cost of → for; deposit → get coins; withdraw → redeem; profit → net gain; rebet →
respin; loss limit → stop limit; loss streak → miss streak; place your bets → come and play;
win feature → play feature; be awarded to player's accounts → appear in player's accounts.
Checklist: bet button not "Bet", bet field not "Bet amount", no "AutoBET", bonus-buy label and
its confirmation without buy/bet, clean insufficient-funds text, GC/SC without `$`.
Quick scan: `grep -rniwE "bet|bets|betting|buy|purchase|bought|cash|money|credit|pay|pays|paid|payout|wager|gamble|stake|deposit|withdraw|profit|rebet|autobet|paytable" src/locales/en-social*`
(brand "Stake Engine" in the disclaimer is fine).

Build check before every upload:
`grep -rnoE "https?://[^\"' )]+" dist | grep -vE "w3.org|svelte.dev/e|threejs.org/docs"`
must print nothing fetchable (watch `fonts.googleapis`, `cdn.jsdelivr`, `unpkg`, gstatic Draco
decoders, hardcoded `rgs.stake-engine.com`); asset paths must be relative.

Polish (affects star rating): anticipation on late reels when `anticipation[reel] > 0`, staggered
reel stops (120–200 ms), skippable win celebrations only for Big Win and above (§8), layered feedback
(sound + particles + brief flash + counter) within ~100 ms, easing via GSAP timelines (turbo =
`timeline.timeScale(n)`), unique music/SFX with ducking, 60 fps on mid-range phones.

### Phase 4 – Integration testing
Test: currencies USD / JPY / MXN / XGC / XSC; bet levels (USD $0.10–$1,000 default $1; JPY
¥10–¥150,000 default ¥100; MXN 1–15,000 default 10); refresh mid-spin; changed `rgs_url` is
honoured; unsupported `lang`; `social=true`; `demo=true`; `replay=true`; desktop/mobile/popout;
10 wins per mode where displayed win == RGS payout.

### Phase 5 – Replay (mandatory) and submission
Replay: on `replay=true` skip authenticate/balance; auto-fetch
`GET {rgs_url}/bet/replay/{game}/{version}/{mode}/{event}` → `{payoutMultiplier, costMultiplier, state}`;
show "Play", run the round with full animation and sound, then "Play again"; keep final win
visible; hide balance, bet button, bet selector, autoplay; show win, bet amount (`amount`),
currency, and real cost incl. mode multiplier ("BONUS 1 USD – 100 USD real cost"); honour
`currency`, `lang`, `amount`, `social`. Prepare event IDs per mode: normal win, big win,
wincap, loss, bonus trigger.

Process: register at stake-engine.com → team + provider logo (Team Settings → Branding) →
upload math → upload static frontend (served at `{team}.live.stake-engine.com/{game}/v{n}/`)
→ game tile in dashboard Tile Editor (bright, no dark edges, gradient matches background,
title inside safe area) → submit math + frontend requests. Review: 3 anonymous reviewers score
0–3 in thirds; average < 1.0 → not approved, thread locked 7 days; otherwise rounded to
1★ (bottom of New Releases), 2★ (placement by popularity), 3★ (featured, Burst Games, Stake
Exclusives). Final: bet-level templates applied (Stake.us uses a `us_` template), both requests
Approved & Active, game appears in approved channels, live (🚀).

When reviewing a game, output a table **item | ✅/❌/⚠️ | evidence** over: PreChecks (auth on
launch, play request works, unique title, appropriate assets) · Thumbnail · Math (table above) ·
RGS (bet levels, refresh keeps bet, `rgs_url`) · Rules (payouts, RTP/max win per mode, win
combinations, mode costs, free-spin conditions, disclaimer) · Responsive (desktop, mobile,
popout S/M) · Behaviour (>2× confirmation, autoplay confirmation, sound toggle, spacebar, 10-win
check) · Stake.us wording + GC/SC · Replay · Final. Separate blockers from quality improvements.

## 4. Requests that conflict with the rules
Jackpots, gamble, carry-over meters, frontend-decided wins, physics that chooses outcomes, cloned
IP or Stake branding: explain the rule in one or two sentences and propose the closest compliant
design.

## 5. Three.js specifics
- **Book drives the scene; physics never decides outcomes.** For plinko/dice/wheels/coins play a
  pre-authored path per outcome bucket (add noise that doesn't change the end state) or use a
  seeded deterministic sim with an offline seed table per bucket. Final win = RGS payout.
- **Self-contained build**: `three` from npm, addons from `three/examples/jsm/...`; copy Draco/
  KTX2 decoders into the build and set `setDecoderPath('./draco/')` / `setTranscoderPath('./basis/')`
  (defaults hit external CDNs); bundle fonts and HDRs.
- **Fit every viewport**: canvas follows its container via `ResizeObserver` (popout resizes without
  window resize); fit the board: `dist = max((boardH/2)/tan(fov/2), (boardW/2)/(tan(fov/2)·aspect))`;
  portrait layout for `device=mobile`; `setPixelRatio(min(devicePixelRatio, 2))`, lower on low fps.
- **Mobile budget** (~60 fps mid-range): < ~100 draw calls, < ~300k visible tris, compressed
  textures (KTX2), symbol atlases, `InstancedMesh` for reels/coins/particles, baked lighting,
  1 directional + hemisphere + env map, at most one small shadow map, bloom only in short win
  bursts, dispose bonus-scene resources.
- **Loop**: `renderer.setAnimationLoop`; render on demand when idle; pause on `visibilitychange`;
  time with GSAP timelines, not frame counts.
- **HUD in HTML/Svelte overlay** (crisp text, easy social relabeling); raycast only for in-scene
  picks (pick-a-box bonus).
- **Cylinder reels**: each reel a group rotating on X with N slots on radius r
  (`y = sin(i·a)·r, z = cos(i·a)·r, rotation.x = -i·a`); tween k full turns, land so visible slots
  show `reveal.board[reel]` (+ padding symbols), swap slot materials before they rotate into view,
  slow last reels on anticipation. Highlight `winInfo.positions` with emissive pulse/outline.
- Loading: HTML loader fed by `THREE.LoadingManager`; base assets first, lazy-load bonus scene;
  aim < ~10 MB first load.
For deeper Three.js API help (materials, loaders, shaders, postprocessing, performance), the
`CloudAI-X/threejs-skills` repo is a good companion skill set.

## 7. Concept design: depth, many modes, engagement

The goal is a game players want to come back to because it is *rich*, not because it pressures
them. On Stake Engine every round is independent, so nothing can persist between rounds (no XP,
collections, saved meters, missions, streak rewards). Depth and retention therefore have to be
built from five things: a layered mechanic, a varied mode set, tension inside each round,
strong identity (art, audio, fantasy), and moments worth sharing (replay links).

### 7.1 Shallow vs deep
A concept is **shallow** if a round is a single evaluation with one win type and the bonus is
"same thing, more spins". A concept is **deep** when 3 or more systems interact *inside one
round*, so that the result of one layer feeds the next and players learn to read the board.
Build the concept as a **depth stack** and state how each layer amplifies the others:

| Layer | Examples |
|---|---|
| 1. Core pay | lines, ways, cluster, scatter-pays, custom (pathways, connected regions) |
| 2. Board modifiers | tumble/cascade, mystery symbols, transforms, splitting/doubling symbols, walking or expanding wilds, grid expansion (rows unlock on wins), symbol upgrades |
| 3. Multipliers | spot multipliers that grow on repeat wins in the same cell, global multiplier rising with each cascade, multiplier symbols (state whether they add or multiply) |
| 4. In-round meter | collect symbols during the round/bonus to unlock upgrades (bigger multipliers, extra rows, sticky wilds) – resets when the round ends, so it is stateless-safe |
| 5. Bonus escalation | levels inside free spins, retriggers that add spins *and* upgrade, sticky elements that last until the bonus ends, a final "super" phase |

For every concept write: the **interaction chain** (e.g. cascade → raises spot multiplier →
multiplier also boosts the meter → meter unlocks a row → more ways → more cascades), the
**common round** feel, the **typical bonus** feel, and the **dream path** to wincap. If you can't
describe a dream path that uses 3 or more layers, the concept is too shallow – add a layer or
make two layers interact.

Keep it readable: every layer must be visible on screen (meter UI, multiplier labels on
cells), explainable in one rules paragraph with an example, and legible in the 400×225 popout.
As a rule of thumb: at most 3 layers active in the base game and up to 5 in the bonus.
Complexity costs math effort (more events, more distribution tuning), so scope it accordingly.

### 7.2 Mode ladder (design all modes up front – none can be added after approval)
Each mode must make a **different promise** to the player, not just change the numbers. A
typical ladder:

| Mode | Cost | Promise | Notes |
|---|---|---|---|
| BASE | 1x | Full mechanic, frequent small wins, bonus about 1 in 150–400 spins | Sets the RTP anchor |
| BOOST / ANTE | 1.25–2x | Higher bonus chance or a guaranteed special symbol each spin | `is_feature=True`; ≤2x avoids the confirmation dialog |
| BONUS | ~80–150x | Straight into the standard bonus | `is_buybonus=True`, confirmation needed |
| SUPER BONUS | ~300–600x | Bonus that starts upgraded (starting multiplier, sticky wilds, meter pre-filled, extra row) | Distinct visuals/music |
| Alt-volatility (optional) | 1x or more | Same mechanic, sharper or smoother distribution | Only if the experience truly differs |

Constraints: every mode within 0.5% RTP of the others; each has its own wincap, its own
distributions and its own events; each needs a one-sentence description, cost and max win in
the rules; 3–5 modes is usually the sweet spot. The price of a buy mode is roughly the expected
bonus value divided by the target RTP – tune the distributions so the price stays a clean number.
Player "choices" (e.g. pick volatile vs steady free spins) are best offered as separate modes
chosen *before* the round: a mid-round choice cannot change a pre-computed outcome, and
presenting a choice that doesn't matter is misleading.

### 7.3 Engagement levers to use
- **Rhythm through the math.** Shape the distribution, not just the RTP: a base hit-rate around
  1 in 3–5; smooth win ranges with no gaps; a bonus frequency that lets a typical session see a
  bonus. Check this with `P(≥1 bonus in N spins) = 1 − (1 − p)^N`; aim for roughly 40–60% at
  N = 150 for medium volatility. Include mid-size wins so the experience isn't only dust or jackpot.
- **Anticipation and tension:** staggered reveals, reel slowdowns and music builds. Trigger them
  only from real book data (`anticipation`, scatter counts), so the tension is honest.
- **Escalation inside the round:** meters filling, multipliers climbing, rows unlocking, a final
  phase – a visible arc of build-up → peak → release in every bonus.
- **Mastery and readability:** players can always see *why* they won (highlighted positions,
  chain counters, the multiplier math shown). Rules include worked examples.
- **Discovery:** rare but real events (special transforms, a unique max-win sequence) that exist
  in the books, with visual moments that are distinct for each tier.
- **Mode variety** as the main long-term draw: each mode feels like a different game in the
  same world.
- **Identity:** a coherent fantasy, signature symbol animations and an audio motif; the bonus has
  its own scene.
- **Shareability:** big-win and wincap screens designed to look great in replay links.
- **Respect the player's time:** turbo mode, skippable celebrations, fast load.

### 7.4 Responsible-design check (also protects approval)
Don't design or implement these, and flag them if the user asks:
- **Losses disguised as wins:** no celebration for payouts smaller than the stake. Show them
  neutrally. Full celebration screens only from Big Win upward (§8); wins between the stake and
  Big Win get a position highlight and a HUD roll-up only.
- **Fabricated near-misses:** the frontend must never invent near-misses that aren't in the book,
  and the math must not inflate near-miss boards beyond what the mechanic naturally produces.
- Pressure tactics: countdown timers, "win it back" prompts after losses, nudges to buy a bonus
  after a dry streak, one-click autoplay, hidden or hard-to-find costs and RTP.
- Anything appealing to minors, and fake persistence ("you're close to unlocking…") – which is
  also impossible in a stateless system.
Retention here should come from quality and variety. Reviewers rate polish and originality, and
manipulative patterns put both approval and players at risk.

### 7.5 Ideation process
1. Generate **3 concepts with different depth signatures** (e.g. cascade + spot multipliers;
   grid expansion + collection meter; walking wilds + transforms), each with a theme that
   explains the mechanic (the fantasy should make the rules intuitive).
2. Score each from 1 to 5 on: depth (layer interaction), readability, originality vs existing
   slots, math feasibility, mobile/popout legibility, art/animation cost, and mode-ladder
   potential. Recommend one and say why.
3. Expand the chosen concept into the concept doc below.

### 7.6 Concept doc template
```
# <Title> – <fantasy in one line>
Core loop (1 sentence):
Grid / pay type:
Depth stack: layer | mechanic | feeds into
Interaction chain + dream path to wincap:
Base round feel / bonus feel / super bonus feel:
Modes: name | cost | promise | changes vs base | RTP target | wincap | is_feature / is_buybonus
Round archetypes + target frequency per mode:
  dead spin, small win (< stake, neutral), win ≥ stake, chain/cascade, bonus trigger, big bonus, wincap
Math targets: hit-rate, bonus 1-in-X per mode, P(bonus in 150 spins), RTP split base/free, volatility
Engagement beats: anticipation → escalation → peak → release (per mode)
Book events needed (standard + custom):
Rules text outline incl. worked example:
Responsible-design check (7.4): pass / issues
Risks + scope (math effort, readability at 400×225, asset count):
```

## 8. Win presentation system (win celebrations)

Casino games use a family of screens usually called **win celebrations** (also known as big-win
presentation, win-tier popups or win banners). Design them as one Stake-compliant system.

### 8.1 Stake rules that shape it
- **Full celebrations only for Big Win and above** (the book's `winLevel` ≥ 5, i.e. ≥ 5x the
  stake on the `standard` scale). Smaller wins get no popup, banner, fanfare or coin shower.
- **No jackpots** (stateless rule) – the top tier is **Max Win** (the mode's wincap).
- Shown amounts = the RGS payout (`payoutMultiplier × bet`), formatted per currency; the
  frontend never invents or alters wins.
- With several wins in one round, the HUD win amount must **update incrementally** to the
  final total; the final win must be clearly shown for every non-zero result.
- Fast-play/turbo must keep wins, winning combinations and popups legible.
- In replay mode celebrations play exactly as in the original round.
- Social mode (stake.us): wording without restricted terms ("BIG WIN" is fine; "BONUS BUY",
  "BET", "PAID" are not); GC/SC without `$`.

### 8.2 Tier mapping (Math SDK `winLevel`, `standard` scale, × stake)
| winLevel | Range | Presentation |
|---|---|---|
| 1–2 | < 1x (below the stake) | Neutral: amount shown in the HUD win field, winning cells marked, at most a soft tick sound |
| 3–4 | 1x–5x | Normal win: winning positions highlighted + roll-up in the HUD win field only. **No celebration screen** |
| 5 | 5–15x | **BIG WIN** celebration |
| 6 | 15–30x | **MEGA WIN** |
| 7 | 30–50x | **EPIC WIN** (or Super Mega Win) |
| 8–9 | 50x–wincap | **LEGENDARY / INSANE WIN** (themed names allowed) |
| 10 | wincap | **MAX WIN** |

Bonus totals use the `endFeature` scale (wider ranges up to 2000x+); map it the same way
(Big Win from level 5). Use the `winLevel` from the book instead of recomputing thresholds on
the client, so math and frontend stay consistent. For buy modes, compare against the **real
cost** (amount × mode cost): a 100x buy that returns 120x is a modest result, not "Legendary".
If you change thresholds, change them in the Math SDK config (`get_win_level`) so books and
frontend agree.

### 8.3 Screens to design
| Screen | When | Content |
|---|---|---|
| Win highlight | Every `winInfo` | Winning positions/lines/clusters animate, per-win amount label |
| HUD roll-up | Every win | Win field counts up step by step to the new total |
| Big-Win-and-above celebration | `winLevel` ≥ 5 | Overlay: tier title, big rolling number, particles/coins, music sting; tiers chain upward (Big → Mega → Epic …) as the number passes thresholds |
| Feature trigger | `freeSpinTrigger` | "10 FREE SPINS" popup, scatter celebration, then bonus intro (a feature message, not a win celebration) |
| Bonus intro / transition | Entering the bonus | Scene change, short rules hint, press-to-start or auto-continue |
| Retrigger banner | `freeSpinRetrigger` | "+5 SPINS" |
| Meter / upgrade banner | In-round upgrades | "LEVEL 2 – x3 MULTIPLIER" |
| Bonus summary (total win) | `freeSpinEnd` | Total bonus win, spins played; if the total is ≥ Big Win, chain into the tier celebration; then return transition |
| Max Win | `wincap` | Unique, longest celebration; the round ends at the cap; "MAX WIN 5,000x" |
| System modals | Bet/autoplay confirmation, errors | Same visual language, calm and readable |

### 8.4 Behaviour rules
- Duration scales with tier (~2–3s Big → ~8–12s Max Win); **always skippable** – the first
  tap/space jumps to the final amount, the second closes. Turbo shortens it but keeps the final
  amount visible for at least ~1s.
- The roll-up ends exactly on the RGS payout; never overshoot and correct back.
- Autoplay: celebrations still play (shortened); Max Win may stop autoplay.
- Layout works at 400×225 popout and mobile portrait: titles scale, numbers never clip; test
  long strings (e.g. "¥150,000,000") and every shipped language.
- Asset plan: tier title art (or one animated title with variants), particle emitters with
  intensity levels, background dim, a bitmap number font, audio stings per tier (Big Win and
  above) plus a roll-up loop.

## 9. Localization (multi-language versions)

The `lang` URL param selects the language. English is required; others are optional but improve
reach. Stake Engine codes: `ar` Arabic, `zh` Chinese, `en` English, `fi` Finnish, `fr` French,
`de` German, `hi` Hindi, `id` Indonesian, `ja` Japanese, `ko` Korean, **`po` Polish (not `pl`)**,
`pt` Portuguese, `ru` Russian, `es` Spanish, `tr` Turkish, `vi` Vietnamese. Unknown codes fall
back to English without broken text. When `social=true`, use the English social strings
regardless of `lang`.

Workflow:
1. **No hardcoded text.** All strings in `locales/<code>.json` (or lingui `.po` – the Web SDK uses
   lingui) with stable keys (`ui.spin`, `rules.freespins.trigger`, `win.tier.mega`), plus an
   `en-social.json` for stake.us.
2. **ICU messages** for plurals/variables: `"{count, plural, one {# free spin} other {# free spins}}"`;
   format numbers with `Intl.NumberFormat` while following the currency decimals rule.
3. **Translate in context.** For each key give the translator (human or Claude) the screen, the max
   length and the tone. Keep a per-language glossary so casino terms stay consistent (e.g. vi:
   Free Spins → "Vòng Quay Miễn Phí"; Wild/Scatter often stay in English). Keep symbol names and
   the title consistent; keep the disclaimer's legal meaning intact.
4. **Rules text:** translate from the final English rules; numbers (RTP, max win, costs, paytable)
   are inserted from config, never typed by hand.
5. **Fonts:** bundle fonts covering each script (Latin-ext incl. Vietnamese diacritics, Cyrillic,
   Arabic, Devanagari, CJK); subset per language and lazy-load the active one; no font CDNs.
   Bitmap fonts for win numbers only need digits and currency symbols.
6. **Layout:** allow ~30–40% expansion (de, fi, ru, pt), auto-shrink or wrap labels; **Arabic is
   right-to-left** (mirror text blocks, keep reels left-to-right); larger line height for CJK; no
   text baked into images – if unavoidable, one image per language.
7. **Pseudo-localization test:** a `qps` mode that lengthens and accents every string to expose
   hardcoded or clipped text; then screenshot every screen × language × device size.
8. Run the `casino-game-audit` skill (localization section) before submission.

## 10. Companion skills
- `casino-game-audit` – visual, render, FX, transitions, bet UI, spacing/typography, win
  celebrations, audio and localization audit with a scored report.
- `casino-audio-design` – sound design, music, win stings, mixing and implementation.

## 6. Useful links
Docs https://stakeengine.github.io/docs/ (Approval, API, Math SDK, Web SDK, Reference) ·
Math SDK `github.com/StakeEngine/math-sdk` · Web SDK `github.com/StakeEngine/web-sdk` ·
ts-client `github.com/StakeEngine/ts-client` · optimiser `github.com/StakeEngine/convex-optimizer` ·
docs + MCP server `github.com/StakeEngine/docs`.

## 11. Bundled resources (when installed from the repo)
Full package: https://github.com/MutAquaticStudio/casino-game-skills. If these folders sit next
to this file, prefer them over the inline snippets; if they don't, use the inline versions above
(or suggest cloning the repo when working in a terminal):
- `scripts/validate_math.py <publish_files>` – full math validator (format + approval stats, win-range gaps, `--json` output)
- `scripts/check_social_terms.py <dir>` – stake.us restricted-wording scan
- `scripts/check_static_build.py <dist>` – external requests, hardcoded RGS, absolute paths, console logs
- `assets/rgs-client.ts`, `assets/book-player.ts` – typed RGS client, money helpers, round controller (live/resume/replay)
- `references/stake-engine/*.md` – detailed notes per topic (overview, math SDK, math requirements, RGS API, frontend requirements, approval checklist)
- `references/pixijs/vendor/` – the official PixiJS v8 agent skills (26 topics, MIT), see §12
- `references/threejs/casino-3d.md` + `references/threejs/vendor/` (CloudAI-X Three.js guides, MIT)
- `references/gamedev/vendor/` (awesome-gamedev-agent-skills guides, Apache-2.0: game feel, UI/UX, audio, performance…)

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

## 13. Bet UI / HUD design

Learned from a reference set of live slots from four different studios (Nov 2026). Use the
patterns, not the look: build an original skin – copying another studio's UI risks rejection.

### 13.1 Three proven layout archetypes
| Archetype | Layout | Strengths | Watch out for |
|---|---|---|---|
| **A. Bottom dock** (segmented bar) | One dark translucent dock, bottom-centre: `[turbo/mode] [≡ · BALANCE · WIN] [BET ▲▼] [autoplay] (SPIN) [feature/buy]` | Most readable, scales best to popout, players know it | Generic – skin it with a light touch of the game's materials |
| **B. Floating cluster** | Bottom-left: menu, sound, info + balance/bet printed on the art; centre: hint/win line; bottom-right: `−  (SPIN)  +` with an autoplay pill under the spin | Immersive, more art visible | Legibility over art – needs a scrim/gradient behind text |
| **C. Side rails** | Vertical icon columns left/right, big spin at right-middle, bet/balance as a thin text strip on the bottom edge | Best thumb reach in landscape mobile, maximum board space | Tiny values and outline icons get lost on busy art; needs a separate portrait layout |

Default for Stake games: **A** for desktop/popout (safest for approval and the 400×225 popout),
**B** when the art is calm, **C** only as the mobile-landscape variant.

### 13.2 Anatomy and measurements (16:9 landscape, H = viewport height)
- **Order, left → right:** settings/navigation → balance → win → bet → spin → modes/feature.
  Bet sits next to spin (adjust, then spin); balance is farthest away.
- **Dock:** height ≈ 9–12% H, bottom margin ≈ 2–3% H, width ≤ ~70% W, centred; it must not
  cover the board's bottom row. Panels black at 70–85% opacity, radius 6–10 px, gaps 4–8 px
  between cells.
- **Spin button:** diameter ≈ 1.3–1.6× dock height (≈ 14–17% H), overlapping the dock's top
  edge; the single most prominent element (ring + circular-arrow icon is the convention);
  shows a clear spinning/disabled state and can become a stop/skip button.
- **Secondary buttons** (turbo, autoplay, menu, sound): ≈ 0.5–0.65× the spin diameter,
  icon-only (explained in the UI guide), hit areas ≥ 44 CSS px even if the icon is smaller.
- **Label/value pairs:** label uppercase ≈ 1.6–2% H, value ≈ 2.6–3.2% H (≈ 1.5× the label),
  bold sans, **tabular digits**, currency formatted per currency (JPY 0 decimals, GC/SC without `$`).
- **Bet cell:** its own panel, slightly brighter than the rest; ▲▼ stepper (or −/+ flanking the
  spin); tapping the value opens a picker grid with **every** RGS bet level incl. min/max.
- **Win cell:** reserve its space even at 0 (no layout jump); the roll-up happens here; Big Win
  and above escalate to the celebration layer (§8).

### 13.3 Mode and feature controls
- **Ante/boost toggle** (panel beside the board): state price and benefit explicitly
  ("Play 1.25× – double chance of free spins") with a clear ON/OFF switch. If the mode costs
  **more than 2×**, switching needs a confirmation dialog – not a one-tap toggle (Stake rule).
- **Mode / bonus-buy button:** a distinct accent-colour circle at the dock end showing the
  current mode name; opens a sheet listing every mode with cost, promise, RTP and max win,
  then a confirm step.
- **Turbo:** lightning icon with an obvious on/off state (filled vs outline).
- **Autoplay:** icon next to the spin opens a panel (number of spins, optional stop
  conditions) with a confirm button – it never starts on the first tap. Do **not** implement
  "hold space / hold spin for continuous spins": it places consecutive bets without
  confirmation. Space = one spin.
- **Feature hint banner** (e.g. "4 scatters award free spins") is fine; keep it short, localized
  and social-safe.
- Don't put operator widgets (lobby button, tournaments, promos) inside the game – the platform
  wraps the game itself.

### 13.4 Responsive variants
- **Desktop / laptop:** full dock with labels.
- **Popout L/S (800×450, 400×225):** compress the dock – values without labels, merge
  balance/win into one cell, move secondary buttons into the menu, spin stays ≥ 44 px, board
  keeps ≥ ~65% of the height.
- **Mobile portrait:** board on top; controls in the bottom ~30%: big spin centred, bet −/+ on
  either side, turbo/autoplay small beside them, balance/win row above, menu in a top corner;
  the spin sits in the natural thumb zone.
- **Mobile landscape:** side-rail variant (spin right-middle, settings left).

### 13.5 Visual rules
- Text and icons over art always get a backing (panel, disk or gradient scrim); thin outline
  icons straight on busy art fail contrast. Values need ≥ 4.5:1 contrast.
- Colour roles: one accent for the primary action (spin), one for feature/buy; states via
  fill vs outline; disabled ≈ 40% opacity; animate the spin ring while spinning.
- Typography: a sturdy UI sans for labels/values; the theme display font only for logo/titles.
- Skin with restraint: wood/metal/fabric trims and themed icons are welcome, but keep the
  conventional positions and shapes so players instantly find spin, bet and balance.
- Localization: labels grow (de/fi/ru); test the longest value (e.g. "¥150,000,000"). Social mode:
  "BET" → "PLAY AMOUNT"/"PLAY", "CREDIT" → "BALANCE"/"COINS", "BUY" → "GET"; no "AutoBET".
