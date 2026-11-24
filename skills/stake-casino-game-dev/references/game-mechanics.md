# Game mechanics catalogue

Section 14 of SKILL.md. The catalogue follows the studio's mechanic lists, under the 12-category taxonomy in §14.0: core mechanics, basic bonus and feature
mechanics, advanced slot mechanics, advanced bonus and progression mechanics, reel and symbol modifiers, win calculation, bonus and special rounds. Read it in Phase 1 when choosing mechanics (the selection
process is §14.10 and `references/concept-design.md` §7.5), in Phase 2 when writing `gamestate.py`, and in Phase 3 when writing event handlers.

**The one rule.** Stake Engine rounds are pre-computed and independent (SKILL.md §1). A mechanic is usable only if it **starts and ends inside
one round** (one book line). Several mechanics on the list are normally built on memory between spins or on player decisions; they are
marked and come with a conversion that keeps the player-facing idea.

Status used below:
- ✅ **Allowed** as described.
- ⚠️ **Conditional**: allowed only in the stateless form given in the card (usually: inside one round, inside the bonus, or as a bet mode).
- ❌ **Not allowed** on Stake Engine: use the alternative.

## 14.0 Taxonomy and master table

### iGaming mechanics taxonomy (12 categories)
The studio classifies every mechanic into 12 categories. Categories 1–5 are slot mechanics and are the catalogue below. Categories 6–12
cover other products; most of them depend on shared pools, live play, player decisions or memory between rounds, which Stake Engine's
pre-computed, stateless model does not support. §14.12 gives the detail and the alternatives.

| # | Category | Scope | Stake Engine fit | Catalogue entries |
|---|---|---|---|---|
| 1 | Reel Mechanics | reel, grid, symbol movement | ✅ (inside the round) | 1, 3, 15–19, 29–38, 44 |
| 2 | Symbol Mechanics | wild, transform, merge, split | ✅ | 9, 11–14, 27, 39–50 |
| 3 | Win Mechanics | paylines, cluster, ways | ✅ | 1–5, 51–65 |
| 4 | Bonus Mechanics | free spins, pick, retrigger | ✅ / ⚠️ (picks and choices) | 6–8, 23–24, 26, 66–81 |
| 5 | Multiplier Mechanics | fixed, progressive, symbol multiplier | ✅ | 21, 22, 63, 77, wild multipliers (§14.2.4) |
| 6 | Jackpot Mechanics | progressive, mystery, shared | ❌ | 10, 78 → Max Win tier, fixed prizes |
| 7 | Risk Mechanics | crash, cashout, double or nothing | ❌ cashout and gamble; ⚠️ crash only without live cashout | 25, 67 (risk ladder) |
| 8 | Instant Win Mechanics | mines, plinko, keno, scratch | ✅ plinko, scratch; ⚠️ mines, keno | §14.12 |
| 9 | Table Game Mechanics | blackjack, baccarat, roulette | ⚠️ only games without mid-round decisions | §14.12 |
| 10 | Live Mechanics | live betting, game show, dealer | ❌ | §14.12 |
| 11 | Multiplayer Mechanics | PvP, tournament, leaderboard | ❌ inside the game (operator-level promotions are outside it) | §14.12 |
| 12 | Meta-game Mechanics | quest, collection, progression | ❌ between rounds; ✅ inside the bonus | 20, 26, 28 |

When the user names a mechanic, first place it in a category, then find its row in the master table. A mechanic that is not listed:
classify it, apply the one rule (stateless, from the math, no fake choice) and add a row in the same format.

### Master table

| # | Mechanic | Group | Status | Where it lives | Nearest Math SDK sample | Card |
|---|---|---|---|---|---|---|
| 1 | Megaways (variable reel heights) | Core | ⚠️ name only | base + bonus | `0_0_ways` + height draw | §14.1.1 |
| 2 | Cluster Pays | Core | ✅ | base + bonus | `0_0_cluster` | §14.1.2 |
| 3 | Cascading / Tumbling Reels | Core | ✅ | base + bonus | `0_0_scatter`, `0_0_cluster` | §14.1.3 |
| 4 | Paylines | Core | ✅ | base + bonus | `0_0_lines` | §14.1.4 |
| 5 | 243 Ways / All Ways | Core | ✅ | base + bonus | `0_0_ways` | §14.1.5 |
| 6 | Hold & Win | Basic bonus | ✅ (no jackpot labels) | feature inside the round | `0_0_lines` + respin loop | §14.2.1 |
| 7 | Free Spins | Basic bonus | ✅ | bonus | all samples | §14.2.2 |
| 8 | Pick & Win | Basic bonus | ⚠️ reveal, not a real choice | bonus stage | custom | §14.2.3 |
| 9 | Wild / Expanding Wild / Sticky Wild | Basic bonus | ✅ (sticky: inside round/bonus) | base + bonus | `0_0_expwilds` | §14.2.4 |
| 10 | Progressive Jackpot | Basic bonus | ❌ | – | – | §14.2.5 |
| 11 | Mystery Symbols | Advanced slot | ✅ | base + bonus | custom step | §14.3.1 |
| 12 | Symbol Transformation | Advanced slot | ✅ | base + bonus | custom step | §14.3.2 |
| 13 | Expanding Wild | Advanced slot | ✅ | base + bonus | `0_0_expwilds` | §14.3.3 |
| 14 | Sticky Symbols | Advanced slot | ⚠️ inside round/bonus | respins, bonus | custom | §14.3.4 |
| 15 | Walking Wild | Advanced slot | ⚠️ respins inside the round | respins, bonus | custom | §14.3.5 |
| 16 | Shifting Symbols | Advanced slot | ✅ (from the math) | base + bonus | custom step | §14.3.6 |
| 17 | Cascading / Avalanche | Advanced slot | ✅ | base + bonus | `0_0_scatter` | §14.3.7 |
| 18 | Expanding Reels | Advanced slot | ⚠️ resets at round end | base round, bonus | custom | §14.3.8 |
| 19 | Nudge Mechanic | Advanced slot | ⚠️ only if simulated | base + bonus | custom step | §14.3.9 |
| 20 | Symbol Collection | Advanced slot | ⚠️ inside round/bonus | bonus, long base rounds | custom | §14.3.10 |
| 21 | Progressive Multiplier | Advanced bonus | ✅ (resets at round end) | cascades, bonus | `0_0_scatter` (`updateGlobalMult`) | §14.4.1 |
| 22 | Multiplier Symbols | Advanced bonus | ✅ | base + bonus | `0_0_scatter` + `mult_values` | §14.4.2 |
| 23 | Feature Upgrade | Advanced bonus | ✅ inside the bonus | bonus | custom | §14.4.3 |
| 24 | Multi-stage Bonus | Advanced bonus | ✅ one round, all stages | bonus | custom | §14.4.4 |
| 25 | Gamble Feature | Advanced bonus | ❌ | – | – | §14.4.5 |
| 26 | Feature Meter / Charge Meter | Advanced bonus | ⚠️ inside round/bonus, or a bet mode | bonus, ante mode | custom | §14.4.6 |
| 27 | Split Symbols | Advanced bonus | ✅ | base + bonus | custom evaluation | §14.4.7 |
| 28 | Persistent Progression | Advanced bonus | ❌ | – | – | §14.4.8 |
| 29 | Reel Modifier (umbrella) | Reel & symbol | ✅ | base + bonus | custom step | §14.5.1 |
| 30 | Reel Lock | Reel & symbol | ⚠️ inside round/bonus | respins, bonus | custom | §14.5.1 |
| 31 | Reel Respins | Reel & symbol | ⚠️ free respins only, never paid | respins | custom loop | §14.5.1 |
| 32 | Reel Swap | Reel & symbol | ✅ | base + bonus | custom step | §14.5.1 |
| 33 | Reel Reorder | Reel & symbol | ✅ | base + bonus | custom step | §14.5.1 |
| 34 | Sticky Reels | Reel & symbol | ⚠️ inside round/bonus | respins, bonus | custom | §14.5.1 |
| 35 | Reel Expansion | Reel & symbol | ⚠️ resets at round end | base round, bonus | custom | §14.5.1 |
| 36 | Hidden Reels | Reel & symbol | ⚠️ unlocked inside round/bonus | base round, bonus | custom | §14.5.1 |
| 37 | Split Reels | Reel & symbol | ✅ | base + bonus | custom evaluation | §14.5.1 |
| 38 | Bonus Reel | Reel & symbol | ✅ | base + bonus | custom | §14.5.1 |
| 39 | Symbol Upgrade | Reel & symbol | ✅ | base + bonus | custom step | §14.5.2 |
| 40 | Symbol Downgrade | Reel & symbol | ✅ | base + bonus | custom step | §14.5.2 |
| 41 | Symbol Merge | Reel & symbol | ✅ | base + bonus | custom step | §14.5.2 |
| 42 | Symbol Split | Reel & symbol | ✅ | base + bonus | custom evaluation | §14.5.2 (= §14.4.7) |
| 43 | Symbol Multiplication | Reel & symbol | ✅ | base + bonus | custom step | §14.5.2 |
| 44 | Symbol Migration | Reel & symbol | ✅ (from the math) | base + bonus | custom step | §14.5.2 |
| 45 | Symbol Evolution | Reel & symbol | ⚠️ inside round/bonus | cascades, bonus | custom | §14.5.2 |
| 46 | Symbol Removal | Reel & symbol | ✅ | base + bonus | custom step | §14.5.2 |
| 47 | Symbol Substitution | Reel & symbol | ✅ | base + bonus | custom step | §14.5.2 |
| 48 | Random Wild | Reel & symbol | ✅ (from the math) | base + bonus | custom step | §14.5.3 |
| 49 | Mega Wild | Reel & symbol | ✅ | base + bonus | custom | §14.5.3 |
| 50 | Multi-Wild | Reel & symbol | ✅ | base + bonus | custom step | §14.5.3 |
| 51 | Left-to-Right Pays | Win calculation | ✅ | all pay types | `0_0_lines`, `0_0_ways` | §14.6 |
| 52 | Right-to-Left Pays | Win calculation | ✅ | all pay types | custom evaluation | §14.6 |
| 53 | Both-Way Pays | Win calculation | ✅ | all pay types | custom evaluation | §14.6 |
| 54 | All-Ways Pays | Win calculation | ✅ | base + bonus | `0_0_ways` | §14.6 (= §14.1.5) |
| 55 | Adjacent Pays | Win calculation | ✅ | base + bonus | custom evaluation | §14.6 |
| 56 | Cluster Pays | Win calculation | ✅ | base + bonus | `0_0_cluster` | §14.6 (= §14.1.2) |
| 57 | Scatter Pays | Win calculation | ✅ | base + bonus | `0_0_scatter` | §14.6 |
| 58 | Ways-to-Win | Win calculation | ✅ | base + bonus | `0_0_ways` | §14.6 |
| 59 | Payline Pays | Win calculation | ✅ | base + bonus | `0_0_lines` | §14.6 (= §14.1.4) |
| 60 | Multi-line Wins | Win calculation | ✅ | base + bonus | `0_0_lines` | §14.6 |
| 61 | Overlapping Wins | Win calculation | ✅ (rule stated) | base + bonus | custom evaluation | §14.6 |
| 62 | Highest Win Only | Win calculation | ✅ | base + bonus | `0_0_lines` | §14.6 |
| 63 | Win Combination Multiplication | Win calculation | ✅ | base + bonus | custom evaluation | §14.6 |
| 64 | Win Cap | Win calculation | ✅ required | every mode | all samples (`wincap`) | §14.6 |
| 65 | Win Streak | Win calculation | ⚠️ inside round/bonus | cascades, bonus | custom | §14.6 |
| 66 | Bonus Wheel | Bonus & special | ✅ (lands on the book result) | bonus stage | custom | §14.7 |
| 67 | Bonus Ladder | Bonus & special | ⚠️ progress, not a gamble | bonus stage | custom | §14.7 |
| 68 | Bonus Pick | Bonus & special | ⚠️ reveal | bonus stage | custom | §14.7 (= §14.2.3) |
| 69 | Bonus Upgrade | Bonus & special | ✅ inside the bonus | bonus | custom | §14.7 (= §14.4.3) |
| 70 | Bonus Respins | Bonus & special | ✅ | bonus | custom loop | §14.7 |
| 71 | Bonus Buy | Bonus & special | ✅ as a bet mode | buy modes | `is_buybonus` | §14.7 |
| 72 | Bonus Choice | Bonus & special | ⚠️ as modes chosen before the round | buy modes | separate BetModes | §14.7 |
| 73 | Bonus Branching | Bonus & special | ✅ (branch from the math) | bonus | custom | §14.7 |
| 74 | Bonus Fusion | Bonus & special | ✅ | bonus | custom | §14.7 |
| 75 | Bonus Retrigger | Bonus & special | ✅ (capped) | bonus | `freeSpinRetrigger` | §14.7 |
| 76 | Bonus Extension | Bonus & special | ✅ (capped) | bonus | custom | §14.7 |
| 77 | Bonus Multiplication | Bonus & special | ✅ | bonus | custom | §14.7 |
| 78 | Bonus Jackpot | Bonus & special | ❌ | – | – | §14.7 |
| 79 | Bonus Survival | Bonus & special | ⚠️ no skill, outcome from the book | bonus | custom | §14.7 |
| 80 | Bonus Countdown | Bonus & special | ⚠️ counted in spins, never a real-time timer | bonus | custom | §14.7 |
| 81 | Bonus Collection | Bonus & special | ✅ inside the bonus | bonus | custom | §14.7 (= §14.3.10) |

Rows 9/13, 3/17, 14/34, 18/35, 27/42, 16/44, 54/5, 56/2, 59/4, 68/8, 69/23 and 81/20 overlap on purpose (the lists name them twice); the later card adds the variants or points back.

Each card: **Works** (what the player sees), **Stake** (status and conversion), **Math** (Math SDK side, volatility), **Events**
(standard events, or *custom* names to define in `game_events.py`, each needing a frontend handler; custom names are suggestions, not SDK
constants), **Show** (presentation and timing), **Watch** (rules text, readability, pitfalls), **Assets** (art and sound to order).

---

## 14.1 Core mechanics (layer 1: core pay, plus the cascade engine)

### 14.1.1 Megaways (variable reel heights)
- **Works:** each reel shows a different number of symbols every spin (commonly 2–7), so the ways count changes per spin (6 reels × 7 = 117,649 ways).
- **Stake:** ⚠️ the mechanic is allowed; the **name is not**. "Megaways" is a trademark (licensed by its owner), and Stake rejects
  "Megaways"/"Xways"-type names (SKILL.md §2). Use "variable reels", "shifting ways" or a themed name in the title, rules and UI.
- **Math:** ways evaluation plus a per-reel height draw from a weighted table carried in a distribution condition (like `mult_values`).
  Often a horizontal top reel adds symbols over reels 2–5. Volatility rises with the max ways; tune heights per mode.
- **Events:** `reveal` with ragged columns (keep `paddingPositions` and board shape explicit); *custom* `setReelHeights` if the frontend cannot infer them.
- **Show:** resize cells per reel, a ways counter above the board that rolls to the new value each spin.
- **Watch:** smallest cell (7-high) must read in the 400×225 popout; test it first.
- **Assets:** symbols drawn to stay legible at the smallest size; counter font; sound for the counter tick.

### 14.1.2 Cluster Pays
- **Works:** 5+ identical symbols touching horizontally or vertically pay; bigger clusters pay more; grids 6×5 to 8×8.
- **Stake:** ✅
- **Math:** `0_0_cluster`; paytable by size bands (5–6, 7–8, 9–10, 11–12, 13+). Medium-high volatility, usually with cascade.
- **Events:** `reveal`, `winInfo` (one entry per cluster, all positions), then cascade events.
- **Show:** outline the cluster as one shape, pulse, then burst into the cascade.
- **Watch:** rules show a picture of a 5-cluster; diagonal does not count (say so).
- **Assets:** cluster outline FX, burst sprite, a rising win tick per cluster size.

### 14.1.3 Cascading / Tumbling Reels
- **Works:** winning symbols vanish, the rest fall, new ones drop in, evaluate again, repeat.
- **Stake:** ✅ every step is part of the same round.
- **Math:** `0_0_scatter` / `0_0_cluster`; the book carries every intermediate board. The number of steps per round is the main tuning dial
  (read the step-count distribution in the PAR sheet).
- **Events:** `tumbleBoard`, `setTumbleWin`, `updateTumbleWin`; `updateGlobalMult` if a multiplier climbs.
- **Show:** pop ≈0.25s → fall with a small bounce ≈0.3s → next evaluation; chain counter from step 2; running total near the board; the HUD
  win updates incrementally (§8.1).
- **Watch:** turbo shortens steps but shows every board; skip jumps to the final board and total. Stop conditions in §14.3.7.
- **Assets:** pop FX, landing dust, pitch-stepped cascade sounds (cap the pitch at ~6 steps).

### 14.1.4 Paylines
- **Works:** fixed lines (10–25 on 5×3, 20 in `0_0_lines`), left to right from reel 1, 3+ of a kind.
- **Stake:** ✅
- **Math:** `0_0_lines`; lowest base volatility of the pay types.
- **Events:** `reveal`, `winInfo` (one entry per line, positions = the line cells), `setWin`, `setTotalWin`, `finalWin`.
- **Show:** draw the line, highlight its cells; cycle several lines at ~0.6–0.8s each, skippable.
- **Watch:** paylines diagram in the rules.
- **Assets:** line art per colour, line win tick.

### 14.1.5 243 Ways / All Ways
- **Works:** matching symbols on adjacent reels from reel 1 pay in any row; ways = product of matches per reel (3^5 = 243 on 5×3, 1024 on 5×4).
- **Stake:** ✅
- **Math:** `0_0_ways`; frequent small wins, volatility from wilds and multipliers.
- **Events:** as paylines; `winInfo.positions` holds every contributing cell, `meta` can carry the ways count.
- **Show:** highlight all contributing cells at once with "3 × 2 × 1 = 6 ways".
- **Assets:** same as paylines without line art.

## 14.2 Basic bonus and feature mechanics

### 14.2.1 Hold & Win
- **Works:** 6+ special symbols (coins with values) trigger respins; they lock; respins reset to 3 whenever a new one lands; ends when respins
  run out or the board fills; total = sum of values (often ×2 on a full board).
- **Stake:** ✅ the whole feature runs inside one round. **No jackpot labels** (§14.2.5): fixed top prizes show their multiplier ("1000x")
  or a themed name clearly listed as a fixed value in the rules.
- **Math:** respin loop in `gamestate.py`; value weights in a distribution condition; full board is the natural wincap path. The distribution
  is lumpy: check win-range gaps with `validate_math.py`.
- **Events:** *custom* `holdTrigger`, `addCoins` (positions, values), `updateRespins` (remaining), `collect` (total); then `setWin`.
- **Show:** darken non-coin cells, three respin dots that refill with a sound, a final sweep counting coins into the total.
- **Watch:** variants worth adding: collector symbol (sums all coins), coin upgraders, extra-row unlock (§14.3.8).
- **Assets:** coin set with value labels (bitmap font), lock FX, respin dots, collect sweep, lock and reset sounds.

### 14.2.2 Free Spins
- **Works:** 3+ scatters award N spins, with their own rules (multiplier, sticky wilds, different reels).
- **Stake:** ✅ the free spins are part of the round that triggered them (or of a bought round).
- **Math:** separate bonus reel strips; retriggers capped so the book stays bounded; bonus frequency per mode is a concept target (§7.3).
- **Events:** `freeSpinTrigger`, `enterBonus`, `updateFreeSpin`, `freeSpinRetrigger`, `freeSpinEnd`.
- **Show:** trigger on the scatters → intro card → bonus scene and music → spin counter → summary card → back to base (`references/win-presentation.md` §8.5).
- **Watch:** variants: progressive multiplier (§14.4.1), sticky symbols (§14.3.4), feature upgrades (§14.4.3), super bonus as a separate mode.
- **Assets:** bonus scene, intro and summary cards, bonus music, trigger sting.

### 14.2.3 Pick & Win
- **Works:** the player taps items to reveal prizes until a stop item.
- **Stake:** ⚠️ the result is fixed before the first tap; a tap cannot change it. Present it as a **reveal** ("tap to reveal"), not as a
  choice or skill, and never show "what you could have won" unless that is also in the book. A **real** choice (e.g. 10 spins at 3x or 5 spins
  at 6x) must be a separate bet mode picked before the round (`concept-design.md` §7.2). If the round waits for taps, set
  `auto_close_disabled=True` and call end-round (Phase 2).
- **Math:** the prize sequence is drawn in the simulation; the frontend assigns the next prize to whatever tile is tapped.
- **Events:** *custom* `pickStart` (tile count), `pickReveal` (index, prize) per step, `pickEnd` (total).
- **Show:** clear tiles, each tap reveals in ≈0.4s; an auto-reveal button and turbo; replay reveals in order without waiting.
- **Assets:** tile art (closed/open), prize icons, reveal and collect sounds.

### 14.2.4 Wild / Expanding Wild / Sticky Wild
- **Works:** wild substitutes for paying symbols (not usually scatter); expanding covers its reel (§14.3.3); sticky stays in place (§14.3.4).
- **Stake:** ✅; sticky only inside the round or the bonus.
- **Math:** wild density per reel strip and per mode; restrict wilds to reels 2–5 (or 2–4) to protect the hit rate.
- **Events:** `reveal`; expanding and sticky use the custom events in their cards.
- **Assets:** wild base, expanded (full-reel) version, sticky frame.

### 14.2.5 Progressive Jackpot
- **Stake:** ❌ jackpots are not allowed: there is no shared pool and nothing grows between rounds.
- **Alternative:** the **Max Win** tier (the mode's wincap, §8.2) as the top moment; fixed-value top prizes in Hold & Win labelled by their
  multiplier; a super-bonus mode for "the big chase". Never use the words "jackpot", "Grand", "Major" as prize names that imply a pool.

## 14.3 Advanced slot mechanics

### 14.3.1 Mystery Symbols
- **Works:** mystery tiles land; when the reels stop they all turn into the same symbol (e.g. 5 mysteries become Wild).
- **Stake:** ✅
- **Math:** reveal symbol drawn by weight after the board draw; the book stores both boards. The chance of "mystery → wild" is a strong volatility dial.
- **Events:** `reveal` (with mystery tiles), *custom* `mysteryReveal` (symbol, positions), then `winInfo`.
- **Show:** shimmer, then all flip at once (≈0.5s); flip together, never one by one with a fake suspense pause.
- **Assets:** mystery tile, flip FX, reveal sting.

### 14.3.2 Symbol Transformation
- **Works:** symbols turn into another type on a condition (low pay becomes high pay after a win; a trigger symbol turns cells wild).
- **Stake:** ✅
- **Math:** a step between `reveal` (or a win) and the next evaluation; transformations after a win need a re-evaluation or a respin.
- **Events:** *custom* `transformSymbols` (positions, from, to).
- **Show:** source → beam → target cells morph (≈0.4s), then evaluate.
- **Assets:** morph FX, transform sound.

### 14.3.3 Expanding Wild
- **Works:** a wild grows from its cell to the whole reel or an area (wild on reel 3 fills the column).
- **Stake:** ✅
- **Math:** `0_0_expwilds`; expand chance and reel restriction set the volatility.
- **Events:** `reveal`, *custom* `expandWild` (reel, rows), then `winInfo`.
- **Show:** stretch outward (≈0.4s), then evaluate.
- **Assets:** full-reel wild art (one tall image, not three stacked cells).

### 14.3.4 Sticky Symbols
- **Works:** symbols stay in place across several spins (e.g. a wild held for 3 free spins).
- **Stake:** ⚠️ only across spins **inside the same round**: free spins, or respins awarded by the sticky symbol itself. Sticky across
  paid base spins would carry state between bets and is not allowed.
- **Math:** list of sticky positions (with remaining life, if limited) in the gamestate; cap the count or lower the symbol weight in bonus reels.
- **Events:** *custom* `addSticky` (positions, life), `updateSticky` (life left), `removeSticky`; each `reveal` includes the sticky cells.
- **Show:** lock animation, a frame and a life counter on the cell; reels spin behind sticky cells.
- **Assets:** sticky frame, lock sound, life pips.

### 14.3.5 Walking Wild
- **Works:** a wild moves one reel each spin (column 2 → column 3) until it leaves the board.
- **Stake:** ⚠️ the steps must be respins inside the round (each move awards a respin), or free spins. A wild that walks across paid spins is
  not allowed.
- **Math:** respin loop; each step is a new board with the moved wild; direction rule stated (left, right, toward a target).
- **Events:** *custom* `moveWild` (from, to), then `reveal` + `winInfo` per step.
- **Show:** hop animation and a respin counter.
- **Assets:** walking pose or trail FX, footstep sound.

### 14.3.6 Shifting Symbols
- **Works:** symbols move by a rule (e.g. same-type symbols slide together to form a win, wilds shift one cell per respin, a row rotates).
- **Stake:** ✅ when the shift is part of the simulated outcome; the frontend only animates moves from the book. Do not shift to tease near-misses.
- **Math:** a deterministic rule applied in the simulation (gravity toward a side, gather same symbols, rotate a row), followed by evaluation.
- **Events:** *custom* `shiftSymbols` (list of from → to moves).
- **Show:** all moves together with easing (≈0.35s), then evaluate.
- **Assets:** slide trail FX, shift sound.

### 14.3.7 Cascading / Avalanche
Same engine as §14.1.3. Add here the **stop conditions**: no new win, a step cap (e.g. 20), or a reached wincap (stop the round and show Max Win).
Write the cap into the rules. Avalanche is a themed name for the same mechanic: falling blocks instead of reels.

### 14.3.8 Expanding Reels
- **Works:** rows or columns unlock when a condition is met (5×3 → 5×5), giving more ways or lines.
- **Stake:** ⚠️ the grid resets when the round ends; it may grow during cascades of one spin, during respins, or through the bonus.
- **Math:** board size in the gamestate; condition (each cascade, each collected item, each retrigger); evaluate with the current size.
- **Events:** *custom* `expandGrid` (rows, cols).
- **Show:** the frame grows, locked cells crack open; the full grid must still fit the phone width (§13.4, `scripts/mobile_layout.py`).
- **Assets:** locked-cell art, frame pieces that stretch, unlock sound.

### 14.3.9 Nudge Mechanic
- **Works:** a reel moves up or down one position to complete a win or a trigger.
- **Stake:** ⚠️ only when the nudge is part of the simulated outcome and the rules describe it. The frontend never invents a nudge, and the
  math does not inflate near-miss boards to sell nudges (§7.4).
- **Math:** after the board draw, apply the nudge rule (e.g. a wild partly visible nudges into view) and record both boards.
- **Events:** *custom* `nudge` (reel, steps), then `reveal` of the new board.
- **Show:** a single clear step with a click (≈0.3s).
- **Assets:** nudge arrow FX, click sound.

### 14.3.10 Symbol Collection
- **Works (as listed):** collect symbols over many spins to fill progress and open a bonus ("10 coins → Free Spins").
- **Stake:** ⚠️ collecting **across paid spins** is not allowed (it is state between bets). Stateless forms:
  - collect **inside the bonus**: each 10 coins in free spins award +spins or an upgrade (§14.4.3);
  - collect **inside one base round**: during a cascade chain, or with respins awarded by the collect symbols;
  - collect in **one spin**: N coins anywhere on the board trigger the bonus (a scatter-count trigger with a collection look).
- **Math:** counter in the gamestate, reset at round end; thresholds in config.
- **Events:** *custom* `collect` (positions, count), `updateMeter` (value, target).
- **Show:** items fly into a counter next to the board.
- **Assets:** collectable icon, counter art, fly-in sound.

## 14.4 Advanced bonus and progression mechanics

### 14.4.1 Progressive Multiplier
- **Works:** the multiplier climbs with each cascade step or each bonus spin (x2 → x3 → x5 → x10).
- **Stake:** ✅ resets at the end of the round (base) or at the end of the bonus.
- **Math:** a ladder table in config (linear 1,2,3… or stepped 2,3,5,10); in the bonus a persisting multiplier is the main volatility source,
  so cap the ladder and tune the trigger rate.
- **Events:** `updateGlobalMult`; `winInfo.meta` carries the applied multiplier.
- **Show:** a large counter beside the board that pulses on each step; show "win × mult = total" once per round.
- **Assets:** ladder art showing the next steps, step-up sound with rising pitch.

### 14.4.2 Multiplier Symbols
- **Works:** a symbol with its own value (x2–x500) applies when it is part of a win or lands on a winning spin.
- **Stake:** ✅
- **Math:** value weights per mode in `mult_values`; they shape the top of the distribution. State whether several values **add** or **multiply**.
- **Events:** `reveal` with values per cell (custom field), `winInfo.meta` with the total multiplier.
- **Show:** values on the symbol; at the end of the cascade they fly into the win and the sum/product is shown.
- **Assets:** multiplier symbol per value tier (colour by size), bitmap digits, fly sound.

### 14.4.3 Feature Upgrade
- **Works:** a feature gets better during play (a normal wild becomes a sticky wild; +1 to the multiplier step; a low symbol removed).
- **Stake:** ✅ inside the bonus (or inside one round). Upgrades that stay for later paid spins are not allowed.
- **Math:** upgrade conditions (retrigger, collection threshold) and the upgrade order in config.
- **Events:** *custom* `featureUpgrade` (name, level).
- **Show:** a short upgrade card between spins (≈1.2s, skippable) and a permanent indicator of the current level.
- **Assets:** upgrade card, level icons, upgrade sting.

### 14.4.4 Multi-stage Bonus
- **Works:** the bonus has stages with their own goal and rules (collect keys → open the vault → reveal the reward).
- **Stake:** ✅ when all stages happen inside the triggering round. Any choice in a stage follows §14.2.3.
- **Math:** each stage is a function in `gamestate.py` that hands its result to the next (keys collected decide the vault tier); the book holds
  every stage. Watch book size: long bonuses produce large books (keep events lean).
- **Events:** *custom* `stageStart` (stage, goal), stage-specific events, `stageEnd` (result).
- **Show:** a transition card per stage with the goal; a progress strip showing all stages; total win carried across stages.
- **Assets:** one scene or overlay per stage, stage transition FX, music that builds per stage.

### 14.4.5 Gamble Feature
- **Stake:** ❌ gamble/double-up is forbidden (SKILL.md §1).
- **Alternative:** a higher-volatility bet mode chosen **before** the round, or a super-bonus buy for players who want risk.

### 14.4.6 Feature Meter / Charge Meter
- **Works (as listed):** a bar fills with energy or points; full bar triggers a feature ("full bar → Super Spin").
- **Stake:** ⚠️ a bar that fills across paid spins is not allowed. Stateless forms:
  - the meter fills **inside the bonus** and fires its feature there;
  - the meter fills **inside one round** (cascades, respins);
  - "Super Spin" as a **bet mode** (ante or buy) that guarantees the charged state, with its cost in the rules.
- **Math:** meter value and thresholds in the gamestate; tune so the top level is reachable in a good bonus, not in every bonus.
- **Events:** *custom* `updateMeter` (value, level), `meterLevelUp` (level, reward).
- **Show:** a permanent meter near the board (vertical on PC, horizontal on phone: `references/mobile-ui.md`); items fly into it; the level-up
  gets a short sting, not a full celebration.
- **Assets:** meter built from parts (frame, fill, caps, level marks) so it can rotate between layouts.

### 14.4.7 Split Symbols
- **Works:** a symbol splits into several (a wild splits into 3 wilds) or counts double.
- **Stake:** ✅
- **Math:** two kinds, state which one: **count split** (one cell counts as 2 or 3 symbols for ways/cluster/scatter counts) or **spawn split**
  (the symbol creates copies in other cells by a rule, e.g. adjacent cells). Define how splits combine with wilds and multipliers.
- **Events:** count split: a per-cell marker in `reveal`; spawn split: *custom* `splitSymbol` (source, targets).
- **Show:** count split shows two copies in one cell with a "×2" badge; spawn split throws copies from the source (≈0.4s).
- **Assets:** split variants of the affected symbols, split FX.

### 14.4.8 Persistent Progression
- **Stake:** ❌ progress kept between rounds or sessions is impossible (stateless) and reads as fake persistence (§7.4).
- **Alternative:** progression **inside the bonus** (levels, upgrades, stages); a mode ladder where higher modes start further along
  (super bonus with a pre-filled meter, `concept-design.md` §7.2); depth from mechanics and mode variety instead of long-term unlocks.

## 14.5 Reel and symbol modifiers

Short cards in table form. Shared rules for this group:
- Every modifier is **decided in the simulation** and written into the book; the frontend never rolls a modifier itself (a "random" wild
  that the client picks would show something the RGS did not return).
- Each modifier that changes the board is followed by a fresh evaluation (or a `reveal` of the new board), so `winInfo` always matches what is on screen.
- Modifiers that last across spins only last **inside the round** (respins it awards, free spins); reset point stated in the rules.
- A base-game "random modifier" feature usually fires on 1 in 5–15 spins; set the rate per modifier in the spec card (§14.11) and check it with `mechanic_stats.py`.

### 14.5.1 Reel modifiers

| # | Mechanic | Works | Stake | Math + events | Show / assets |
|---|---|---|---|---|---|
| 29 | Reel Modifier | umbrella: anything that changes reel rules or structure (the rows below) for one spin or the rest of the round | ✅ | pick the modifier by weight per mode (distribution condition); *custom* `reelModifier` (type, reels, params) | a modifier banner before the reels stop (≈0.6s) so the player knows what changed |
| 30 | Reel Lock | one or more reels freeze while the others respin | ⚠️ inside the round: locks come with free respins (or in free spins), released at round end | locked reel indexes in the gamestate; *custom* `lockReels` / `unlockReels` | chain or ice frame over the reel; lock sound |
| 31 | Reel Respins | only chosen reels spin again | ⚠️ awarded free inside the round (e.g. 2 scatters → respin the other reels once). A **paid** respin of selected reels is a continuation and not allowed | respin loop; *custom* `respinReels` (reels) then `reveal` | highlight respinning reels, dim the held ones (keep held symbols readable) |
| 32 | Reel Swap | two reels exchange places (e.g. a wild reel swaps with a weak reel) | ✅ | swap in the simulation, then evaluate; *custom* `swapReels` (a, b) | both reels slide past each other (≈0.4s) |
| 33 | Reel Reorder | the reel order changes (shuffle, sort, rotate) | ✅ | apply the order, then evaluate; *custom* `reorderReels` (order[]) | reels lift and drop in the new order; rules show the order rule |
| 34 | Sticky Reels | a whole reel stays as it is across spins (often a full wild reel) | ⚠️ only through respins or free spins of the same round | sticky reel list with life; *custom* `stickyReel` (reel, life) | frame + life pips on the reel; reuse §14.3.4 assets |
| 35 | Reel Expansion | a reel gets taller (more rows), e.g. 3 → 5 | ⚠️ resets at round end | per-reel height in the gamestate; *custom* `expandReel` (reel, rows); see §14.3.8 and variable reels §14.1.1 | frame stretches on that reel only; check phone width |
| 36 | Hidden Reels | extra reels behind covers open when a condition is met (5 reels → 6 or 7) | ⚠️ opened inside the round or the bonus; closed again after | evaluate with the current reel count; more ways or lines; *custom* `unlockReel` (reel) | cover breaks open; the board must fit with all reels open on phone and popout |
| 37 | Split Reels | one reel is divided into zones (e.g. the middle reel split into an upper and lower half with their own strips, or a reel divided into 2 sub-columns) | ✅ | each zone has its own strip; evaluation counts zones as separate positions (state how ways are counted); custom field in `reveal` | a visible divider; zones spin independently |
| 38 | Bonus Reel | an extra special reel with its own rules (a top or side reel of modifiers, multipliers or prizes that applies to the main board) | ✅ | its own strip drawn in the simulation; result applied to the main win; *custom* `bonusReel` (result) | its own frame, lands last with a short pause; outcome shown as text ("x5 to all wins") |

### 14.5.2 Symbol modifiers

| # | Mechanic | Works | Stake | Math + events | Show / assets |
|---|---|---|---|---|---|
| 39 | Symbol Upgrade | a symbol moves up the pay ladder by levels (low → mid → high) | ✅ | upgrade path in config; trigger (upgrade symbol, each cascade, each bonus retrigger); *custom* `upgradeSymbols` (positions, from, to) | morph with a rising sparkle; upgrade levels shown in the paytable |
| 40 | Symbol Downgrade | a symbol moves down the ladder | ✅ | usually paired with something positive (downgrade highs to lows but add wilds); *custom* `downgradeSymbols` | a neutral effect, not a "loss" moment; explain the trade in the rules |
| 41 | Symbol Merge | several identical symbols combine into one bigger or better symbol (3 adjacent → one 2×2 or one higher tier) | ✅ | merge rule (adjacency, count) in the simulation, then evaluate; *custom* `mergeSymbols` (sources, target, size) | sources pull into the target; colossal art for merged sizes (§14.5.3 Mega Wild) |
| 42 | Symbol Split | one symbol splits into several | ✅ | see §14.4.7 (count split or spawn split) | see §14.4.7 |
| 43 | Symbol Multiplication | a symbol copies itself to other cells (duplicate to adjacent cells or a whole row) | ✅ | copy rule in the simulation; *custom* `cloneSymbol` (source, targets) | copies fly out of the source |
| 44 | Symbol Migration | symbols move between positions by a rule (fly to a target cell, gather on one reel) | ✅ when the move is from the math | moves recorded; *custom* `migrateSymbols` (from → to list); see Shifting §14.3.6 | all moves together (≈0.4s), then evaluate |
| 45 | Symbol Evolution | a symbol grows through stages (egg → chick → bird), each stage pays more or gains a power | ⚠️ stages advance inside the round: per cascade, per respin or per free spin; resets at round end | stage per cell in the gamestate; *custom* `evolveSymbol` (position, stage) | stage pips on the symbol; one art variant per stage |
| 46 | Symbol Removal | symbols are removed by a condition (all low pays leave the bonus reels, a bomb clears a symbol type) | ✅ | removal in the simulation or by using bonus reel strips without those symbols; *custom* `removeSymbols` (symbol or positions) | removed symbols fade out of the paytable or board; show "Low symbols removed" |
| 47 | Symbol Substitution | symbols are replaced by a rule (all 10s become Queens, a symbol stands in for another) | ✅ | substitution table in config; *custom* `substituteSymbols` (from, to, positions) | swap morph; rules list the substitution table |

### 14.5.3 Wild variants

| # | Mechanic | Works | Stake | Math + events | Show / assets |
|---|---|---|---|---|---|
| 48 | Random Wild | wilds are added to random cells (before or after the stop) | ✅ only from the simulation; the client never chooses the cells | count and cells drawn in the simulation; *custom* `addWilds` (positions) | a character or effect "throws" wilds onto cells; fires on its own rate, not after a dry streak |
| 49 | Mega Wild | one wild covers several cells (2×2, 3×3, a full reel block) | ✅ | the board stores each covered cell as wild; a block descriptor for the frontend; *custom* `megaWild` (top-left, size) | one large sprite masked to the grid, not tiled small wilds |
| 50 | Multi-Wild | one symbol creates several wilds (a spreading wild, a wild that turns its row or neighbours wild) | ✅ | spread rule in the simulation; *custom* `spawnWilds` (source, targets) | wilds burst out from the source; see Split/Multiplication for shared FX |

## 14.6 Win calculation mechanics

How a board turns into a payout. These are rules of the evaluation in `game_calculations.py` (or the SDK's built-in evaluators); they change
the hit rate and the paytable, not the round structure. Whatever the rule, every win is reported as a `winInfo` entry (symbol, kind, win,
positions, meta), so one frontend win handler serves all of them. **Every rule here must be written in the rules page with an example**, and
the paytable must say which direction and which combination rule applies.

| # | Mechanic | Works | Stake | Math + events | Show / rules text |
|---|---|---|---|---|---|
| 51 | Left-to-Right Pays | a combination counts from reel 1 rightward, consecutive reels | ✅ (the default) | standard evaluators | "Wins pay left to right from the leftmost reel" |
| 52 | Right-to-Left Pays | the same from the last reel leftward | ✅ | mirror the evaluation; usually only as part of Both-Way | arrow icon in the paytable |
| 53 | Both-Way Pays | combinations pay from either side | ✅ | evaluate both directions; a full-width combination (5 of 5) is paid **once**, not twice; hit rate rises a lot, scale the paytable down | `meta.direction`; draw the line from the side it paid |
| 54 | All-Ways Pays | every valid adjacent-reel combination in any row | ✅ | §14.1.5 | ways count shown |
| 55 | Adjacent Pays | matching symbols must sit next to each other (on adjacent reels and rows), not just anywhere on a line | ✅ | define adjacency (orthogonal only, or diagonal too); adjacency evaluation | rules picture of a valid and an invalid shape |
| 56 | Cluster Pays | groups of touching symbols | ✅ | §14.1.2 | – |
| 57 | Scatter Pays | pay by the number of a symbol anywhere (8+ of a kind, or 3+ scatters pay x total bet) | ✅ | count evaluation; scatter wins usually pay on total bet and add to line wins | pop all instances together |
| 58 | Ways-to-Win | wins = matches per reel multiplied (243, 1024, variable) | ✅ | §14.1.1, §14.1.5 | ways counter |
| 59 | Payline Pays | fixed lines | ✅ | §14.1.4 | line diagram |
| 60 | Multi-line Wins | several lines win in the same spin; all are paid and summed | ✅ | sum of `winInfo` entries; `setWin` = the total | cycle lines after a quick "all wins" flash; HUD shows the sum incrementally (§8.1) |
| 61 | Overlapping Wins | the same cells may be part of more than one win (two lines through one wild, a symbol in two ways) | ✅ with the rule stated | decide: overlap allowed (each line pays) or each cell pays once; for clusters a cell belongs to one cluster | rules state it; highlight overlaps without double-counting the shown total |
| 62 | Highest Win Only | per line (or per symbol), only the highest combination pays | ✅ | standard on lines: a line with 5 wilds and 3 cherries pays the higher one; per-symbol for ways | rules: "Only the highest win per line is paid" |
| 63 | Win Combination Multiplication | the spin win is multiplied by the number of winning combinations (3 lines win → ×3), or each extra combination raises a multiplier | ✅ | apply after the sum; feeds volatility hard, cap the factor; `winInfo.meta` carries the factor | show "3 wins × 3 = …" once; the shown total is the book's |
| 64 | Win Cap | the maximum win per round (the mode's wincap); reaching it ends the round | ✅ **required** | `max_win` / `wincap` per BetMode; when reached the simulation stops and emits `wincap`; force a share of sims to reach it (`force_wincap` distribution) so it is obtainable (math thresholds in Phase 2) | Max Win celebration (§8.2 level 10); rules list the cap per mode |
| 65 | Win Streak | consecutive winning steps raise a reward (multiplier, extra spin) | ⚠️ streaks of **paid spins** are state between bets and not allowed; count streaks of cascade steps in one spin, of respins, or of consecutive winning free spins | streak counter in the gamestate; *custom* `updateStreak` (count, reward) | streak counter near the board, reset clearly shown |

## 14.7 Bonus and special round mechanics

Everything in a bonus round happens inside the triggering (or bought) round and is in the book. Bonus flow and timing:
`references/win-presentation.md` §8.5. Choices and challenges follow the Pick & Win rule (§14.2.3): a pre-computed outcome may be **revealed**
in a playful way but must never be presented as depending on the player's skill, speed or choice.

| # | Mechanic | Works | Stake | Math + events | Show / assets |
|---|---|---|---|---|---|
| 66 | Bonus Wheel | a wheel decides the prize, spins count, multiplier or which bonus | ✅ | segment weights in a distribution condition; *custom* `wheelSpin` (segment index, prize); the wheel animation must land exactly on that segment | segment sizes may differ visually from their weights only if the rules do not imply equal chances; spin ≤3s, skippable |
| 67 | Bonus Ladder | climb prize levels; each step raises the prize | ⚠️ the climb is the math's result (the book says how high it goes). A ladder where the player risks the prize to climb is a **gamble** (❌, §14.4.5) | final level drawn in the simulation; *custom* `ladderStep` (level, prize) per step | ladder beside the board, each step lights up; final level glows |
| 68 | Bonus Pick | pick hidden prizes | ⚠️ reveal only | §14.2.3 | – |
| 69 | Bonus Upgrade | the bonus gets better while it runs (more spins, higher multiplier, better symbols) | ✅ inside the bonus | §14.4.3 | – |
| 70 | Bonus Respins | the bonus gives respins (e.g. a free spin with no win repeats; Hold & Win respins) | ✅ | respin loop inside the bonus; cap; *custom* `bonusRespin` | respin counter |
| 71 | Bonus Buy | pay a fixed cost to start the bonus directly | ✅ as a **bet mode** (`is_buybonus=True`, cost in `BetMode`) | own distribution, RTP within 0.5% of base, price ≈ E[bonus] / target RTP (`concept-design.md` §7.2); confirmation dialog for costs above 2x | social mode (stake.us) may not say "Bonus Buy" (`scripts/check_social_terms.py`); cost shown before purchase |
| 72 | Bonus Choice | the player chooses one of several bonuses (more spins at a low multiplier vs fewer at a high one) | ⚠️ a choice **after** the trigger cannot change a pre-computed result. Build it as separate bet modes chosen before the round (several buy modes, or an ante mode per bonus type) | one BetMode per choice, each with its own distribution and RTP in the band | a bonus menu next to the bet button; never a fake choice screen after triggering |
| 73 | Bonus Branching | the bonus takes a path depending on what happens (3 scatters → path A, 4 → path B; a stage result opens stage X or Y) | ✅ the branch follows the math result | branch decided in the simulation; *custom* `bonusBranch` (path) | a map or fork showing the chosen path |
| 74 | Bonus Fusion | two bonuses combine (free spins and Hold & Win trigger together, or a super bonus that merges two features) | ✅ | combined state machine in `gamestate.py`; define order and how values combine; heavy on book size | a fusion intro card; both feature UIs visible at once (plan the layout on phone) |
| 75 | Bonus Retrigger | new triggers during the bonus add spins | ✅ capped | `freeSpinRetrigger`; cap total spins to keep the book bounded | +N spins banner |
| 76 | Bonus Extension | the bonus lasts longer (extra spins, an extra stage, extra respins) through a symbol or a level | ✅ capped | *custom* `bonusExtend` (amount, reason) | counter grows with an effect |
| 77 | Bonus Multiplication | the bonus total (or each bonus win) is multiplied (end-of-bonus multiplier, multiplier applied to all bonus wins) | ✅ | multiplier weights per mode; applied before `freeSpinEnd`; respect the wincap | the summary card shows "total × mult = final" |
| 78 | Bonus Jackpot | a bonus that can award a jackpot | ❌ no jackpots (§14.2.5) | – | top fixed prize labelled by its multiplier; the Max Win tier |
| 79 | Bonus Survival | complete a challenge to win (survive N rounds of a boss, keep a token alive) | ⚠️ the outcome comes from the book; the player does not act to survive (no skill, no reaction input) | rounds drawn in the simulation; *custom* `survivalRound` (round, alive, prize) | a themed "battle" that plays out the book; lives shown; skippable |
| 80 | Bonus Countdown | reach a goal before the countdown ends | ⚠️ count in **spins or steps** ("collect 5 keys in 10 spins"); a **real-time** timer is a pressure tactic (§7.4) and implies skill: not allowed | goal and spin budget in config; *custom* `updateCountdown` (left, progress) | spins-left counter, never a clock |
| 81 | Bonus Collection | collect items during the bonus for rewards | ✅ inside the bonus | §14.3.10 | – |

## 14.8 Combination recipes

Starting points for the three concepts in `concept-design.md` §7.5, built only from the list above.

| Signature | Mechanics (by #) | Interaction chain | Volatility |
|---|---|---|---|
| Cascade engine | Cluster (2), Cascade (3), Progressive Multiplier (21), Multiplier Symbols (22) | win → cascade → mult steps → multiplier symbols land on the new board → bigger chain | high |
| Variable ways chase | Variable reels (1), Cascade (3), Expanding Reels (18) | win → cascade → reel heights grow → more ways → more wins | high |
| Wild workshop | All Ways (5), Expanding Wild (13), Sticky Symbols (14), Feature Upgrade (23) | wild expands → in the bonus wilds become sticky → upgrade adds a multiplier to sticky wilds | medium |
| Walking hunter | Paylines (4), Walking Wild (15), Multiplier Symbols (22) | wild lands → respins as it walks → multiplier symbols boost each step | medium |
| Coin vault | Hold & Win (6), Symbol Collection inside the feature (20), Expanding Reels (18), Multi-stage Bonus (24) | coins lock → collected coins unlock rows → full board opens the vault stage | high, lumpy |
| Mystery forge | All Ways (5), Mystery (11), Transformation (12), Split Symbols (27) | mystery stack → reveals one symbol → transform turns it wild → wilds split | medium |
| Charged free spins | Paylines or Ways, Free Spins (7), Feature Meter in the bonus (26), Feature Upgrade (23) | collect in bonus → meter levels → each level upgrades wilds / multiplier | medium-high |
| Reel workshop | All Ways (5), Reel Modifier (29) picking from Reel Swap (32), Hidden Reels (36), Random Wild (48) | random modifier each 1 in 8 spins → hidden reel opens → more ways → random wilds land on the new reel | medium |
| Evolving swarm | Cluster (2), Cascade (3), Symbol Evolution (45), Symbol Merge (41), Mega Wild (49) | each cascade evolves survivors → 3 top-stage symbols merge into a mega wild → bigger clusters | high |
| Respin lock | Paylines (4), Reel Respins (31), Reel Lock (30), Sticky Reels (34) | 2 scatters → free respin of the other reels with the scatter reels locked → a full wild reel sticks for the respins | medium |
| Branching quest | Both-Way Pays (53), Free Spins (7), Bonus Branching (73), Bonus Ladder (67), Bonus Multiplication (77) | scatter count picks the path → ladder steps in the bonus raise the end multiplier → total × multiplier | medium-high |
| Fusion vault | Paylines (4), Hold & Win (6), Free Spins (7), Bonus Fusion (74), Win Cap (64) | both features trigger together → coins collected during free spins → fused summary, capped at wincap | high |
| Bonus menu | any core pay, Bonus Choice as modes (72), Bonus Buy (71), Bonus Countdown in spins (80) | player picks a bonus type before the round → each type has its own goal and spin budget | per mode |

Rule of thumb from §7.1: at most 3 layers active in the base game, up to 5 in the bonus.

## 14.9 Cost and risk per mechanic

| Mechanic (#) | Math effort | Frontend effort | Readability risk at 400×225 |
|---|---|---|---|
| Paylines (4), All Ways (5) | low | low | low |
| Cluster (2), Cascade (3, 17) | medium | medium (cascade choreography) | medium |
| Variable reels (1) | medium | high (per-reel resizing) | high |
| Wilds (9, 13), Sticky (14), Walking (15) | low–medium | medium | low |
| Mystery (11), Transformation (12), Shifting (16), Split (27) | low–medium | medium | medium |
| Expanding Reels (18) | medium | high (layout changes) | high on phone |
| Nudge (19) | low | low | low (approval risk if misused) |
| Hold & Win (6) | medium-high (lumpy distribution) | medium | low |
| Free Spins (7), Feature Upgrade (23) | medium | medium | low |
| Pick & Win (8), Multi-stage Bonus (24) | medium | high (separate scenes) | low |
| Collection (20), Meter (26) | medium | medium (two layouts) | medium |
| Progressive Multiplier (21), Multiplier Symbols (22) | medium (distribution top) | medium | medium |
| Reel Swap/Reorder/Lock/Respins (30–33), Sticky Reels (34) | low–medium | medium | low |
| Reel Expansion (35), Hidden Reels (36), Split Reels (37) | medium | high (layout changes) | high on phone |
| Bonus Reel (38) | medium | medium (extra frame) | medium |
| Symbol modifiers (39–47) | low–medium | medium (one art variant per level/stage) | medium |
| Random / Mega / Multi-Wild (48–50) | low–medium | medium | low |
| Direction and combination rules (51–63) | low–medium (paytable rebalance) | low | low (rules text matters) |
| Win Streak (65) | low | low | low |
| Wheel, Ladder, Branching (66, 67, 73) | medium | high (separate scenes) | low |
| Bonus Buy / Choice as modes (71, 72) | medium (one distribution per mode) | medium (mode menu) | low |
| Bonus Fusion (74), Survival (79), Countdown (80) | high | high | medium |

## 14.10 Mechanic selection process

Run this in Phase 1, inside `concept-design.md` §7.5 step 1.

1. **Collect the wish list.** Write down every mechanic the user or the concept wants, using the names in §14.0, and tag each with its
   taxonomy category (1–12). Anything in categories 6–12 goes through §14.12 first.
2. **Screen each one** against the status column. ❌ → replace with its alternative now. ⚠️ → write the stateless form you will build
   (e.g. "Symbol Collection, inside free spins only"). Tell the user what changed and why in one line each.
3. **Fill the depth stack** (`concept-design.md` §7.1): exactly one core pay (14.1) with its win-calculation rules (14.6), then board modifiers (14.3, 14.5), multipliers, meters, bonus escalation.
   Check the base game has at most 3 active layers.
4. **Write the interaction chain** and the dream path to wincap; use §14.8 as a reference. Each mechanic must feed another; a mechanic that feeds
   nothing is decoration: drop it or connect it.
5. **Write one spec card per mechanic** (§14.11) in the concept doc.
6. **Derive the event list** from the cards (standard + custom). This list is the contract for math, frontend, art and audio.
7. **Set a frequency target per mechanic and per mode** (e.g. "mystery reveal 1 in 12 base spins", "hold & win 1 in 180"). After the math
   runs, `scripts/mechanic_stats.py` measures the same numbers from the books.
8. **Cost check** with §14.9: total effort fits the scope; nothing with high readability risk without a phone and popout plan.

## 14.11 Mechanic spec card (template for the concept doc)

```
### <Mechanic name> (#<n> in §14.0) – status ✅/⚠️ (stateless form: ...)
Layer: core pay | board modifier (incl. reel/symbol modifier) | multiplier | in-round meter | bonus escalation
Modes: base / ante / bonus / super bonus (and how it differs per mode)
Trigger: what starts it, and its target frequency per mode (1 in X rounds)
Rule: exact behaviour, incl. add vs multiply, caps, reset point (end of cascade / spin / bonus / round)
Feeds into: which other mechanic it powers
Events: standard + custom (name, payload)
Presentation: animation, duration, turbo and skip behaviour, phone and popout notes
Assets: art (casino-symbol-art) and sound (casino-audio-design) to order
Rules text: one paragraph + a worked example with numbers
Risks: math (volatility, win-range gaps), readability, approval
```

## 14.12 Non-slot categories (taxonomy 6–12)

Stake Engine's model (SKILL.md §1) is a static book of pre-computed rounds per bet mode. The Web SDK ships sample apps for lines, ways,
scatter, cluster, price and number-picker games, so some non-slot games fit; anything that needs live data, a shared pool, other players or a
decision that changes the outcome after the bet does not. For any game outside the slot categories, **re-check the live docs**
(https://stakeengine.github.io/docs/) before designing, and state the assumption in the concept doc.

| Category | Mechanic | Fit | Why / how to make it fit |
|---|---|---|---|
| 6 Jackpot | progressive, mystery, shared jackpot | ❌ | no pools, nothing grows between rounds. Use the Max Win tier, fixed top prizes labelled by multiplier, a super-bonus mode |
| 7 Risk | double or nothing / gamble | ❌ | continuation is forbidden. Offer a higher-volatility mode chosen before the round |
| 7 Risk | cashout (early or partial) | ❌ | early cashout is forbidden; the round is one fixed outcome |
| 7 Risk | crash | ⚠️ | a crash game depends on when the player cashes out, a live decision. A stateless form fixes the target before the bet (e.g. one mode per target multiplier, or a fixed auto-cashout) and reveals the pre-computed crash point; check the docs, then the math is a simple distribution of crash points |
| 8 Instant win | plinko | ✅ | the book holds the landing slot (and the path); risk levels and row counts are separate modes; the ball animation is chosen to land in that slot, never simulated live |
| 8 Instant win | scratch card | ✅ | the book holds the card; scratching is a reveal (§14.2.3 rule) |
| 8 Instant win | mines | ⚠️ | classic mines lets the player pick tiles and cash out at any time (continuation). Stateless form: the number of picks and mines fixed by the mode before the round, the result revealed; check the docs |
| 8 Instant win | keno / number picks | ⚠️ | the payout depends on numbers the player chose. Study the Web SDK number-picker sample and the docs for how player picks are passed before building |
| 9 Table | baccarat, dice, wheel-style roulette on one bet | ⚠️ | no decision after the bet, so a round is pre-computable; each bet type (or bet layout) needs its own mode and RTP in the 0.5% band, which limits complex layouts |
| 9 Table | blackjack, poker with draws | ❌ | hit/stand/draw decisions change the outcome after the bet |
| 10 Live | live betting, game shows, dealers | ❌ | needs live video and real-time data; the build is static with no external requests (Phase 3, `check_static_build.py`). A game-show *look* with a pre-computed wheel or bonus is fine (§14.7) |
| 11 Multiplayer | PvP, tournaments, leaderboards | ❌ in the game | rounds are single-player and independent; tournaments and leaderboards are operator promotions run outside the game, not part of the build |
| 12 Meta-game | quests, collections, progression across rounds | ❌ | fake persistence (§7.4) and impossible without state. Move the idea inside the bonus (§14.3.10, §14.4.6, §14.4.8) or into the mode ladder |

3D presentation for dice, wheels, plinko and coins: `references/threejs/casino-3d.md`.

## 14.13 Checklist per mechanic (before moving to the next phase)

- [ ] Category (taxonomy §14.0) and status checked; ❌ replaced, ⚠️ built in its stateless form.
- [ ] Starts and ends inside one round; the reset point is stated.
- [ ] In the depth stack with what it feeds into; has a spec card (§14.11).
- [ ] Every event it emits has a frontend handler; `scripts/mechanic_stats.py` shows it in the books at the target frequency.
- [ ] Visible on screen (counter, label, meter) and readable in the 400×225 popout and on a phone.
- [ ] Rules explain it in one paragraph with a worked example.
- [ ] Turbo and skip keep it legible; replay plays it identically.
- [ ] Art and sound ordered (`casino-symbol-art` §2, `casino-audio-design` §2).
- [ ] No jackpot wording, no gamble or risk ladder, no real-time countdown, no fabricated near-miss or nudge, no choice presented as mattering when it does not.
- [ ] Win-calculation rules (direction, overlap, highest-only, cap) written in the paytable and rules page.
