# Math approval requirements

From docs `approval/math-requirements` and the approval checklist. `scripts/validate_math.py`
checks most of these automatically.

| Requirement | Threshold |
|---|---|
| RTP per mode | 90.0% – 98.0% |
| Spread between modes | all modes within 0.5% of each other (base 97% → others 96.5–97.5%) |
| Max win | equals what rules say; realistically obtainable – checklist says hit-rate 1 in 20,000,000 or more frequent (docs text: typically more often than 1 in 10,000,000) |
| Simulations (slot-type) | 100,000 – 1,000,000 per mode, enough diversity to avoid repeats in a session |
| Non-zero win hit-rate | industry norm: 1 in 20 or more frequent; checklist: typically ~1 in 3–8 for base, not >20 |
| Share of paying sims | a reasonable portion – e.g. 90k losses of 100k sims may be rejected |
| Dominant outcome | most likely single sim should not dominate when visuals imply variety |
| BASE mode volatility | std. deviation within industry norms |
| Zero-weight payouts | must not dominate the simulations; report count of non-zero-weight payouts |
| Win-range gaps | intermediate wins must exist between small payouts and max payout |
| Mode cost | correctly stated in rules |

## Formulas (LUT payout p in cents, weight w, mode cost c)
- `RTP = Σ w·p / (100 · c · Σ w)`
- `hit_rate = Σw / Σ_{p>0} w` (report as "1 in X")
- `max_win_hit = Σw / Σ_{p=max} w`
- std dev of `p/100/c` weighted by w → compare across modes

## Balancing levers
- Distribution quotas (how often wincap / bonus / zero / basegame criteria occur)
- Reel strip composition and `reel_weights`
- Multiplier value weights (`mult_values`)
- Scatter trigger weights
- Paytable values
- Optimiser targets (per-criteria RTP split, hit-rate targets)

Typical RTP split for a base mode with free spins: ~60–70% from base game wins, ~30–40%
from free games (game-dependent). Bonus-buy modes have cost = expected bonus value / target RTP.

Bonus-buy cost check: `cost ≈ E[bonus payout] / RTP_target`. If the bonus mode RTP drifts
outside the 0.5% band, tune the bonus distribution rather than the price, so the price on
the button stays a clean number.
