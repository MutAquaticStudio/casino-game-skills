---
name: "stake-casino-game-dev"
description: "Ideate, build, balance, review and submit casino/slot games for Stake Engine: concept and mode ladder, Math SDK, RGS API, PixiJS 8 and Three.js frontends, Bet UI with measured phone and desktop layouts, win celebrations and round timing rules, localization, approval checklist. Use for any Stake Engine slot task, from idea to submission."
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

### Workflow map (what each step hands to the next)
| Step | Skill | Needs | Produces | Gate before moving on |
|---|---|---|---|---|
| 1 Concept | this skill, §7 (`references/concept-design.md`) | idea or brief | concept doc: depth stack, mode ladder, event list, theme, grid, target RTP/wincap | §2 screen passed; mode ladder final (no modes can be added after approval) |
| 2 Math | this skill, Phase 2 | concept doc | game_config.py, books, lookup tables, `winLevel` per outcome | `validate_math.py` clean |
| 3 Art | `casino-symbol-art` | concept theme + mode list + real symbol size | `art/style.json` (with `style_lock`), symbol atlas, frame, board, backdrop, win/transition art | `style_check.py` no FAIL; shrink and greyscale tests; `silhouette_check.py` for frameless symbols; `tile_check.py` on the tile; originality |
| 4 Frontend | this skill, Phase 3, §12–13 (`references/pixi-slots.md`, `references/bet-ui-hud.md`) | books, atlas, `art/motion.json` + `art/fx/`, event list | static build wired to RGS, HUD, win celebration, locales | check_static_build.py clean; every book event type has a handler |
| 5 Audio | `casino-audio-design` | event list, tier table | audio files + AudioManager | event → sound table complete |
| 6 Integration | this skill, Phase 4 | build | test results across currencies, modes, sizes | 10 wins per mode match RGS payout; phone layouts pass `mobile_layout.py report` (§13.4) |
| 7 Audit | `casino-game-audit` | build or screenshots | scored report | no blockers; Graphics & art direction (area A) ≥ 4 |
| 8 Submit | this skill, Phase 5 | audited build | replay IDs, tile, submission | Stake checklist all ✅ |
Handoff files travel with the project: concept doc → `art/style.json` + event list → atlas and win
art → build. If a later step finds a problem owned by an earlier one (e.g. a tier with no art, a
symbol unreadable at popout size), go back to that step and re-run its gate, do not patch around it.

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

## 6. Useful links
Docs https://stakeengine.github.io/docs/ (Approval, API, Math SDK, Web SDK, Reference) ·
Math SDK `github.com/StakeEngine/math-sdk` · Web SDK `github.com/StakeEngine/web-sdk` ·
ts-client `github.com/StakeEngine/ts-client` · optimiser `github.com/StakeEngine/convex-optimizer` ·
docs + MCP server `github.com/StakeEngine/docs`.

## 7. Concept design: depth, many modes, engagement

Depth and retention must come from five things, because every round is independent (no XP, collections, saved meters, missions or streaks):
a layered mechanic, a varied mode set, tension inside each round, strong identity (art, audio, fantasy) and moments worth sharing (replay links).
The whole mode ladder is designed up front: no mode can be added after approval.

**Full detail in `references/concept-design.md`** (§7.1 shallow vs deep, §7.2 mode ladder, §7.3 engagement levers, §7.4 responsible-design check, §7.5 ideation process, §7.6 concept doc template). Read it before writing the concept doc.

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

Screens (§8.3), behaviour rules (§8.4) and the round, win-highlight and bonus timing rules (§8.5) are in **`references/win-presentation.md`**; read it when designing the celebration screens or writing the round controller.

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
- `casino-symbol-art` – style guide, layered SVG symbols, readability checks at real reel size,
  Pixi atlas export and Spine layer hand-off, plus win-title, reel-frame and background art.

## 11. Bundled resources (when installed from the repo)
Full package: https://github.com/MutAquaticStudio/casino-game-skills. If these folders sit next
to this file, prefer them over the inline snippets; if they don't, use the inline versions above
(or suggest cloning the repo when working in a terminal):
- `scripts/validate_math.py <publish_files>` – full math validator (format + approval stats, win-range gaps, `--json` output)
- `scripts/check_social_terms.py <dir>` – stake.us restricted-wording scan
- `scripts/check_static_build.py <dist>` – external requests, hardcoded RGS, absolute paths, console logs
- `assets/rgs-client.ts`, `assets/book-player.ts` – typed RGS client, money helpers, round controller (live/resume/replay)
- `references/concept-design.md` (§7), `references/win-presentation.md` (§8.3–8.5), `references/pixi-slots.md` (§12), `references/bet-ui-hud.md` (§13), `references/mobile-ui.md` and `references/layout-wireframes.md` (phone and desktop layouts, with `scripts/mobile_layout.py` and `scripts/mobile_capture.mjs`)
- `references/stake-engine/*.md` – detailed notes per topic (overview, math SDK, math requirements, RGS API, frontend requirements, approval checklist)
- `references/pixijs/vendor/` – the official PixiJS v8 agent skills (26 topics, MIT), see §12
- `references/threejs/casino-3d.md` + `references/threejs/vendor/` (CloudAI-X Three.js guides, MIT)
- `references/gamedev/vendor/` (awesome-gamedev-agent-skills guides, Apache-2.0: game feel, UI/UX, audio, performance…)

## 12. PixiJS for Stake slots (v8, latest checked: 8.22.0 – Nov 2026)

PixiJS is the most common Stake renderer. Check the version with `npm view pixi.js version`; everything is v8 API (`await app.init`, `app.canvas`, `Assets`, `Graphics` shape-then-fill, `Container` for children).
Rules that matter most for approval: the static build must not reach external URLs (no CDN, relative asset paths, Vite `base: './'`); every visual and amount must match the book (final amounts = RGS payout, §8); run `scripts/check_static_build.py dist` after building.

**Full detail in `references/pixi-slots.md`**: §12.1 versions and doc locations, §12.2 v8 essentials (the mistakes agents make most), §12.3 slot architecture (layer tree, reel/symbol views, round controller), §12.4 performance budget, §12.5 Stake constraints applied to Pixi, §12.6 recent v8 changes. Official API topics: `references/pixijs/vendor/`. Read it before writing any Pixi code.

## 13. Bet UI / HUD design

Use the patterns of live studio slots, not their look. The common thread is **simplicity first**: a handful of flat controls, one dominant spin button, no ornate frames; the theme lives in the board, symbols, background and effects, not in the HUD (§13.0 is a guideline from samples, not a Stake rule).

**Full detail in `references/bet-ui-hud.md`**: §13.0 simplicity first, §13.1 layout archetypes, §13.2 anatomy and measurements, §13.3 mode and feature controls, §13.4 responsive variants (phone portrait and desktop, with `mobile_layout.py`), §13.5 visual rules. Phone numbers: `references/mobile-ui.md`; desktop wireframe: `references/layout-wireframes.md`.
