# Approval checklist

Reproduced in structure from the official interactive checklist
(https://stakeengine.github.io/docs/approval/checklist, data in `static/mockchecklist.json`
of `StakeEngine/docs`). When reviewing a game, output a table: item | ✅/❌/⚠️ | evidence.

## PreChecks
- [ ] Game authenticates with RGS on launch
- [ ] Bet button sends a successful play request
- [ ] Title unique; no "Megaways", "Xways" or similar trademarked terms
- [ ] No offensive, discriminatory or inappropriate assets

## Game thumbnail (Tile Editor)
- [ ] Tile generally bright, doesn't clash with Stake background (watch dark edges)
- [ ] Background bright and appropriate
- [ ] Foreground appropriate, key focus area filled
- [ ] Gradient similar colour to background
- [ ] Title inside inner guidelines, not near edges

## Math
- [ ] RTP 90–98% per mode
- [ ] All modes within 0.5% RTP of each other
- [ ] Advertised max win achievable (≥ 1 in 20,000,000)
- [ ] Reasonable >0 win hit-rate (~1 in 3–8, not > 1 in 20 for base)

## RGS
- [ ] Bet levels respected: USD $0.10–$1,000 default $1.00
- [ ] JPY ¥10–¥150,000 default ¥100
- [ ] MXN 1–15,000 default 10
- [ ] Refresh mid-spin keeps selected bet amount
- [ ] Uses `rgs_url` query param (changing it changes the server called)

## Frontend – game rules
- [ ] Payout per symbol clearly communicated
- [ ] Max multiplier and RTP shown (per mode if several)
- [ ] Win combinations shown (lines, cluster sizes, scatter counts, prizes…)
- [ ] Description and cost of every mode
- [ ] Free-game trigger and retrigger conditions stated
- [ ] Disclaimer present (see frontend-requirements.md)

## Frontend – responsive
- [ ] Desktop
- [ ] Mobile
- [ ] Popout S / M

## Frontend – behaviour
- [ ] Confirmation when switching to modes costing > 2×
- [ ] Autoplay needs a confirmation step
- [ ] Sound can be disabled
- [ ] Spacebar bound to bet button
- [ ] 10 wins per mode checked: displayed win == payout

## Jurisdiction – Stake.us (social)
- [ ] Bet button doesn't say "bet"
- [ ] Game info has no restricted words
- [ ] Bet amount field not labelled "bet amount"
- [ ] Autobet not labelled AutoBET; popups without "bet"
- [ ] Bonus buy label without "BUY"; confirmation without "buy"/"bet"
- [ ] Insufficient funds error without restricted words
- [ ] Supports SC and GC, shown without `$`
- [ ] Replay window without restricted words

## Replay
- [ ] Replay URLs load and play the requested event
- [ ] Optional params honoured (currency, language, amount)
- [ ] Can replay again at end
- [ ] Shows bet cost incl. mode multiplier and real cost ("BONUS 1 USD, 250 USD real cost")
- [ ] Event IDs prepared per mode: normal win, big win, wincap, loss, bonus trigger

## Quality (affects star rating)
- [ ] Original, cohesive theme; polished animation, anticipation, win tiers
- [ ] Unique audio with music/SFX balance
- [ ] Smooth performance on mid-range mobile

## Final
- [ ] Bet-level templates applied (Stake.us: `us_`-prefixed template)
- [ ] Math and frontend requests both Approved & Active
- [ ] Game visible in approved channels; requests closed once live (🚀)
