# Game mechanics catalogue

Section 14 of SKILL.md. Read it in Phase 1 when filling the depth stack (`references/concept-design.md` §7.1), again in Phase 2 when writing
`gamestate.py`, and in Phase 3 when writing event handlers. Every mechanic here is **stateless-safe**: it starts and ends inside one round
(one book line). Anything that needs memory between rounds is in §14.9 with a stateless alternative.

How each card is laid out:
- **Works:** what the player sees and how it pays.
- **Math:** where it lives in the Math SDK (nearest sample game, which distribution condition drives it), its effect on volatility.
- **Events:** standard events it uses; *custom* events are names to define in `game_events.py` (each one needs a frontend handler).
- **Show:** frontend presentation and timing.
- **Watch:** readability, rules text and approval pitfalls.

Sample games referred to: `0_0_lines`, `0_0_ways`, `0_0_cluster`, `0_0_scatter` (pay anywhere + tumble), `0_0_expwilds`,
`0_0_lines_feature_match`. Open the nearest one before writing a mechanic from scratch; its executables show the event order the SDK expects.
Custom event names below are suggestions, not SDK constants.

## 14.1 Pay systems (layer 1: core pay)

### Lines
- **Works:** fixed paylines (10–25 on 5×3), left to right from reel 1, 3+ of a kind. Wild substitutes.
- **Math:** `0_0_lines`. Lowest base volatility of the pay types; the paytable and the line count set the hit rate.
- **Events:** `reveal`, `winInfo` (one entry per line, `positions` = the line cells), `setWin`, `setTotalWin`, `finalWin`.
- **Show:** draw the winning line, then highlight its cells; cycle lines only when there are several, one line per ~0.6–0.8s, skippable.
- **Watch:** paylines diagram in the rules; line numbers on the frame are optional and cost popout space.

### Ways (all-ways)
- **Works:** any adjacent-reel match from reel 1 pays; ways = product of matching symbols per reel (3 on each of 5 reels = 243 ways).
- **Math:** `0_0_ways`. Wins are frequent and small; volatility comes from wild density and multipliers.
- **Events:** as lines; `winInfo.positions` holds every contributing cell, `meta` can carry the ways count.
- **Show:** highlight all contributing cells at once with the ways count ("3 × 2 × 1 = 6 ways"); no line drawing.
- **Watch:** do not name the variable-height variant after trademarked systems ("Megaways", "Xways" are rejected). Call it "variable reels"
  or a themed name.

### Variable reel heights
- **Works:** each reel shows 2–7 symbols per spin, so the ways count changes every spin (up to 117,649 on 6 reels of 7).
- **Math:** ways evaluation with a per-spin reel-height draw (a weighted table read from a distribution condition, like `mult_values`).
  The `reveal` board has ragged columns: pad with the `paddingPositions` the frontend expects and keep the board shape explicit.
- **Events:** `reveal` (ragged board), *custom* `setReelHeights` if the frontend cannot infer heights from the board.
- **Show:** resize symbols per reel (cell height = reel height / count); show the ways counter above the board; animate the counter on change.
- **Watch:** symbols at 7 high must still read at 400×225; test the smallest cell size in the popout.

### Cluster pays
- **Works:** 5+ identical symbols touching horizontally or vertically pay; bigger clusters pay more; usually 6×5 to 8×8 grids, tumble on win.
- **Math:** `0_0_cluster`. Paytable by cluster size bands (5–6, 7–8, 9–10, 11–12, 13+). Medium-high volatility with tumble.
- **Events:** `reveal`, `winInfo` (one entry per cluster, all positions), then the tumble events (§14.2).
- **Show:** outline the cluster as one shape, pulse it, explode it into the tumble.
- **Watch:** cluster size in the paytable, a worked example with a picture of a 5-cluster in the rules.

### Scatter pays (pay anywhere)
- **Works:** 8+ of a symbol anywhere on the board pays, position does not matter; nearly always paired with tumble.
- **Math:** `0_0_scatter`. Count bands (8–9, 10–11, 12+). High volatility when combined with multiplier symbols.
- **Events:** `reveal`, `winInfo` (symbol + all positions), tumble events.
- **Show:** pop all instances at once, show the count and the band payout.
- **Watch:** the trigger scatter and the paying symbols must differ clearly in greyscale.

### Custom pay shapes
Pathways (a connected path from left to right), connected regions of one colour, row/column completions, pattern pays (a shape
on a grid). Allowed if they are fully computed in the math and explained with a picture. Write them in `game_calculations.py`, emit
`winInfo` in the same shape as standard wins (symbol, kind, win, positions, meta) so the standard win handler keeps working.

## 14.2 Board modifiers (layer 2)

### Tumble / cascade
- **Works:** winning symbols are removed, symbols above fall, new ones drop in, evaluate again; repeat until no win.
- **Math:** `0_0_scatter` / `0_0_cluster`. Each step is part of the same simulation; the book carries every intermediate board. Raises hit
  size and variance; the number of steps per round is the main tuning dial (watch the PAR sheet for step-count distribution).
- **Events:** `tumbleBoard` (removed positions + new symbols), `setTumbleWin` / `updateTumbleWin` (running total), `updateGlobalMult` if
  the multiplier climbs per step.
- **Show:** pop (≈0.25s) → fall with easing and a small bounce (≈0.3s) → next evaluation; show a chain counter after step 2; the running
  tumble win sits near the board, the HUD updates incrementally (§8.1).
- **Watch:** turbo shortens each step but must still show each board; skip jumps to the final board and total.

### Expanding wilds
- **Works:** a wild that lands expands to cover its whole reel.
- **Math:** `0_0_expwilds`. Wild frequency per reel strip and the expand chance set the volatility; usually restricted to reels 2–4.
- **Events:** `reveal`, *custom* `expandWild` (reel, rows) before `winInfo`.
- **Show:** stretch from the landing cell outward (≈0.4s), then evaluate.

### Sticky wilds (bonus only)
- **Works:** wilds that land during free spins stay in place until the bonus ends.
- **Math:** the free-spin loop keeps a list of sticky positions in the gamestate and re-applies them each spin; they reset when the round
  ends, so it is stateless-safe. Strongly increases bonus value; cap the count or lower the wild weight in the bonus reels.
- **Events:** *custom* `addSticky` (positions) at landing; every later `reveal` includes them on the board.
- **Show:** lock animation and a persistent frame on the cell; spinning reels pass behind sticky cells.

### Walking / moving wilds
- **Works:** a wild moves one reel (left or toward a target) each respin or free spin until it leaves the board, awarding a respin each step.
- **Math:** respin loop inside the round; each step is a new evaluation with the moved wild.
- **Events:** *custom* `moveWild` (from, to), then `reveal` + `winInfo` per step.
- **Show:** step animation with a footstep/hop, the respin counter shown.

### Wild multipliers
- **Works:** a wild carries 2x/3x/5x; several wilds in one win **add** or **multiply** (say which, in the rules).
- **Math:** multiplier weights in a distribution condition (`mult_values`). Multiplying wilds explode volatility; cap or prefer adding.
- **Events:** `reveal` with the value on the symbol (or a custom field), `winInfo.meta` carrying the applied multiplier.
- **Show:** the value printed on the wild; on a win, fly the value to the win amount and show "base × mult = total".

### Mystery symbols
- **Works:** mystery tiles land, then all reveal into the same random symbol.
- **Math:** reveal symbol drawn by weight after the board draw; the book stores both the mystery board and the revealed board.
- **Events:** `reveal` (with mystery tiles), *custom* `mysteryReveal` (symbol, positions).
- **Show:** a short shimmer, then flip all at once (≈0.5s), then evaluate.

### Transforms and upgrades
- **Works:** a trigger symbol turns low pays into a high pay, or upgrades a symbol one tier, or turns cells into wilds.
- **Math:** a step between `reveal` and evaluation.
- **Events:** *custom* `transformSymbols` (positions, from, to).
- **Show:** source → beam → target cells, then evaluate.

### Splitting / doubling symbols
- **Works:** a symbol counts as 2 (or 3) of itself for ways or scatter counts.
- **Math:** the evaluation counts weight per cell; state the rule for wild + split combinations.
- **Events:** `reveal` with a split marker per cell (custom field), `winInfo` reports the counted total.
- **Show:** the symbol shows two copies in one cell with a "×2" badge.

### Grid expansion
- **Works:** each win (or each collected item) unlocks a row or column, more ways, up to a maximum; resets at round end.
- **Math:** board size is gamestate inside the round; evaluate with the current size. Pairs with tumble.
- **Events:** *custom* `expandGrid` (new rows/cols).
- **Show:** the frame grows, locked cells crack open; the layout must keep the full grid inside the phone width (§13.4).

### Colossal / oversized symbols
- **Works:** 2×2 or 3×3 blocks of one symbol land as one image.
- **Math:** the board stores each cell individually; a block descriptor tells the frontend where to draw the big image.
- **Events:** `reveal` plus *custom* `colossal` (top-left, size, symbol) or a board-level field.
- **Show:** one large sprite masked to the grid; it splits into cells when it wins and tumbles.

### Nudges and respins
- **Works:** a reel nudges one step to complete a win or a trigger; or a respin of some reels.
- **Math:** only if the nudge is part of the simulated outcome. **Never** fabricate a nudge in the frontend or bias boards toward
  near-misses (§7.4).
- **Events:** *custom* `nudge` (reel, steps) between two `reveal`s.

## 14.3 Multipliers (layer 3)

| Type | Works | Math note | Show |
|---|---|---|---|
| Global cascade multiplier | rises 1x → 2x → 3x… with each tumble step; resets each spin (base) or persists through the bonus | progression table in config; in the bonus, persisting is the main volatility source | `updateGlobalMult`; a big counter beside the board, pulses on change |
| Spot (cell) multipliers | a cell that wins gets a marker; a second win there sets 2x, then doubles each time (cap 128x–1024x) | per-cell values in the gamestate; reset per base spin, may persist in the bonus | values drawn on the cells; *custom* `updateSpotMult` (position, value) |
| Multiplier symbols | land with a value (2x–500x); **add** their values and apply to the total win of the spin | value weights per mode in `mult_values`; drives the top of the distribution | the symbol stays until the end of the tumble, then values fly into the total |
| Random win multiplier | after a win, a wheel or meter applies a multiplier to that win | weight table; keep the animation honest (it shows the book value) | brief wheel or meter, ≤1.5s, skippable |
| Bonus starting multiplier | super-bonus mode begins at a higher multiplier | the mode's distribution, not the frontend | shown on the bonus intro card |

Always say in the rules whether multipliers add or multiply, when they reset, and give one worked example with numbers. Show the
calculation on screen at least once per round ("12.50 × 8x = 100.00"). The amount shown must be the book's amount.

## 14.4 Collect and hold-and-win (coin respins)

- **Works:** 6+ cash symbols (coins with multiplier values) trigger respins; coins stick; respins reset to 3 each time a new coin lands;
  the feature ends when respins run out or the board fills; total = sum of coin values (often ×2 for a full board).
- **Math:** a respin loop inside one round; coin values from a weight table; the full-board prize is the natural wincap path. Very
  "lumpy" distribution: check win-range gaps carefully (`validate_math.py`).
- **Events:** *custom* `holdTrigger`, `addCoins` (positions, values), `updateRespins` (remaining), `collect` (total), then `setWin`.
- **Show:** dark board with only coins lit; respin counter of 3 dots; each new coin resets the dots with a sound; final sweep that
  counts coins into the total.
- **Watch:** **no jackpots on Stake Engine.** Do not label coins "Mini/Minor/Major/Grand Jackpot". Fixed top coins are fine if they show
  their multiplier ("1000x") or a themed name that is clearly a fixed prize, and the rules list the fixed value. Collector symbols
  (a symbol that collects all coin values on the board) are fine and add a strong moment.

## 14.5 Free spins and bonus structures (layer 5)

| Variant | Works | Implementation note |
|---|---|---|
| Standard | 3/4/5 scatters → 10/12/15 spins | `freeSpinTrigger`, `enterBonus`, `updateFreeSpin`, `freeSpinEnd`; separate bonus reel strips |
| Retrigger | scatters in the bonus add spins | `freeSpinRetrigger`; cap total spins so the book stays bounded |
| Progressive levels | collecting N items in the bonus upgrades (more spins + higher multiplier, or removes a low pay) | in-bonus meter (§14.6); level-up card between spins |
| Persistent modifiers | multiplier, sticky wilds or spot multipliers kept across all bonus spins | gamestate inside the round; reset at `freeSpinEnd` |
| Super bonus | a rarer trigger (or a buy mode) starting upgraded | own reels and distribution; own scene/music (`concept-design.md` §7.2) |
| Pick / reveal bonus | tiles reveal prizes until a "collect" tile | the prizes are already in the book; see the warning below |
| Wheel bonus | a wheel lands on a prize, spins or an upgrade | the stop segment comes from the book; the wheel must land exactly on it |
| Trail / board bonus | a token moves along a path collecting prizes | each move and prize is an event; skippable |

**Pick bonuses on a pre-computed RGS.** The outcome is fixed before the player taps, so picks cannot change the result. Present it as a
reveal ("tap to reveal"), not as a skill or a choice that matters, and do not show "what you could have won" unless that is also from the
book. If a design needs a real player decision mid-round, split it into separate bet modes chosen before the round
(`concept-design.md` §7.2). Rounds that wait for player input need `auto_close_disabled=True` and an end-round call (Phase 2).

Bonus flow on screen: trigger celebration on the scatters → intro card (spins, starting modifiers, press to start) → bonus scene and
music → per-spin counter → summary card with the total → return to base. Timing and card rules: `references/win-presentation.md` §8.5.

## 14.6 In-round meters (layer 4)

- **Works:** collect symbols during the round or the bonus to fill a meter; each level unlocks something (a row, +1x, sticky wilds, extra
  spins). The meter **resets when the round ends**; showing a meter that carries over between paid spins is fake persistence and is
  impossible on Stake Engine.
- **Math:** meter value in the gamestate; level thresholds in config; tune so the top level is reachable in a good bonus, not in every bonus.
- **Events:** *custom* `updateMeter` (value, level), `meterLevelUp` (level, reward).
- **Show:** the meter is a permanent HUD element near the board (vertical panel on PC, horizontal bar on phone: `references/mobile-ui.md`);
  items fly from the cell to the meter; level-up gets a short sting (`casino-audio-design`), not a full celebration.

## 14.7 Feature modes

Mechanics that live in the mode ladder rather than on the board: ante/boost (higher cost for more scatters or a guaranteed special
symbol, `is_feature=True`), bonus buy and super bonus buy (`is_buybonus=True`), alternative volatility modes. Design rules and pricing:
`references/concept-design.md` §7.2. Social mode (stake.us) renames "Bonus Buy" (`scripts/check_social_terms.py`).

## 14.8 Other game types

Stake Engine is not slot-only. The Web SDK sample apps include price and number-picker games. Crash-style, plinko, dice, wheel, mines-like and
scratch-card games fit the same model if every round is pre-computed into a book: the frontend animates the path or the reveal the book
contains (for physics-like games such as plinko, the ball path is chosen to land in the book's slot, never simulated live). Mid-round
cash-out ("early cashout") and continuation are forbidden (§1); a multi-step game must be a single fixed outcome revealed step by step.
Three.js notes for 3D variants: `references/threejs/casino-3d.md`.

## 14.9 Forbidden mechanics and stateless alternatives

| Asked for | Why it fails | Offer instead |
|---|---|---|
| Progressive or fixed **jackpots** | jackpots are not allowed; no shared pool | Max Win tier (wincap), fixed-value top coins labelled with their multiplier |
| **Gamble / double-up** after a win | forbidden (continuation) | an alt-volatility mode chosen before the round |
| **Early cashout** / continuation | forbidden; the round is one fixed outcome | shorter rounds, a bonus buy |
| Meters, collections, XP or missions **between spins** | no state between rounds | in-round meters (§14.6), persistence inside the bonus (§14.5) |
| "Must-hit-by" or hot/cold displays | implies state and misleads | none; honest bonus frequency in the rules |
| Near-miss teasing not in the book | misleading; see §7.4 | anticipation only from `reveal.anticipation` and real scatter counts |
| Skill-based outcomes, real choices that change the result | outcome is pre-computed | separate modes chosen before the round |

## 14.10 Combination recipes (depth signatures)

Use these as starting points for the three concepts in `concept-design.md` §7.5. Each has an interaction chain where one layer feeds the next.

| Signature | Stack | Interaction chain | Volatility |
|---|---|---|---|
| Cascade + global multiplier | cluster or scatter pays, tumble, global mult (persists in bonus) | win → tumble → mult +1 → bigger next win → more tumbles | high |
| Spot multipliers | cluster 7×7, tumble, cell multipliers doubling, kept in bonus | repeated wins in one area → cell mult climbs → bonus board "heats up" | high |
| Grid growth + meter | ways, tumble, rows unlock per win, meter unlocks sticky wilds | win → row → more ways → more wins → meter level → sticky wilds | medium-high |
| Walking wilds + multiplier wilds | lines or ways, wild with value walks each respin | wild lands → respins → value applies on each step | medium |
| Hold-and-win + collector | 5×3 base, coin respins, collector symbol, full-board ×2 | coins stick → respins reset → collector sums → full board doubles | high, lumpy |
| Mystery + transform | ways, mystery reveal, transform to wild | mystery block → reveal → transform symbol turns them wild | medium |
| Variable reels + multiplier symbols | 6 variable-height reels, tumble, multiplier symbols added at the end | more ways → more tumbles → more multiplier symbols collected | high |

Keep the rule of thumb from §7.1: at most 3 layers active in the base game, up to 5 in the bonus.

## 14.11 Cost and risk per mechanic

| Mechanic | Math effort | Frontend effort | Art needs | Readability risk at 400×225 |
|---|---|---|---|---|
| Lines / ways | low | low | line art (lines only) | low |
| Cluster / scatter pays + tumble | medium | medium (tumble choreography) | pop and drop FX | medium (many cells) |
| Variable reel heights | medium | high (per-reel resizing) | symbols that read very small | high |
| Expanding / sticky / walking wilds | low–medium | medium | wild variants, lock frame | low |
| Multiplier symbols / spot multipliers | medium (distribution top) | medium (value labels, fly-to-total) | bitmap font for values | medium |
| Mystery / transform / split | low | medium | reveal FX, split variants | medium |
| Grid expansion | medium | high (layout changes) | locked-cell art, frame growth | high on phone |
| Hold-and-win | medium-high (lumpy distribution) | medium | coin set with values, respin dots | low |
| In-round meter | medium | medium | meter parts for PC and phone | medium |
| Pick / wheel / trail bonus | medium | high | a separate scene | low |

## 14.12 Checklist per mechanic (before moving to the next phase)

- [ ] It starts and ends inside one round (no state between bets).
- [ ] It appears in the concept doc's depth stack with what it feeds into.
- [ ] Every event it emits has a frontend handler; `scripts/mechanic_stats.py` shows it in the books at the intended frequency.
- [ ] It is visible on screen (counter, label, meter) and readable in the 400×225 popout and on a phone.
- [ ] Rules explain it in one paragraph with a worked example; add/multiply and reset behaviour stated.
- [ ] Turbo and skip keep it legible; replay plays it identically.
- [ ] It has sound (`casino-audio-design` feature list) and art (`casino-symbol-art` §2 specials).
- [ ] No jackpot wording, no fabricated near-miss, no implied choice that does not change anything.
