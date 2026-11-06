# Math SDK

Repo: `StakeEngine/math-sdk` (MIT). Docs: https://stakeengine.github.io/docs/math-sdk
(and legacy https://stakeengine.github.io/math-sdk/). A community fork with a v2 refactor
exists at `Raw-Fun-Gaming/stake-engine-math`.

## Setup
```sh
git clone https://github.com/StakeEngine/math-sdk.git && cd math-sdk
make setup            # venv + requirements (+ Rust toolchain for the optimiser)
make run GAME=0_0_lines
```
Sample games in `games/`: `0_0_lines` (5×3, 20 lines), `0_0_ways`, `0_0_scatter`
(pay-anywhere + tumble), `0_0_cluster`, `0_0_expwilds`, plus a `template/` to copy.

## Game folder
```
games/<name>/
  run.py               # sim counts, threads, compression, which steps to run
  game_config.py       # GameConfig(Config): symbols, paytable, reels, bet modes
  gamestate.py         # GameState.run_spin() / run_freespin() – one simulation
  game_executables.py  # grouped logic + event emission (draw board, evaluate, tumble…)
  game_calculations.py # custom win evaluation
  game_events.py       # custom events
  game_override.py     # override engine behaviour
  reels/               # reel strips CSV
  library/             # generated: books/, books_compressed/, configs/, forces/,
                       #            lookup_tables/, publish_files/
```

## run.py essentials
```python
num_threads = 10; rust_threads = 20; batching_size = 50000
compression = True            # False → readable .json books for debugging
num_sim_args = {"base": int(1e5), "bonus": int(1e5)}   # keys = bet mode names
run_conditions = {"run_sims": True, "run_optimization": True,
                  "run_analysis": True, "upload_data": False}
```
Debug loop: `compression=False`, 100 sims, `run_optimization=False` → inspect events.
Then scale up. `run_analysis` produces a PAR sheet (hit rates, win ranges).

## Bet modes and distributions
```python
BetMode(name="bonus", cost=100.0, rtp=self.rtp, max_win=self.wincap,
        auto_close_disabled=False, is_feature=False, is_buybonus=True,
        distributions=[
          Distribution(criteria="wincap", quota=0.001, win_criteria=self.wincap,
                       conditions={"reel_weights": {...}, "force_wincap": True,
                                   "force_freegame": True, "mult_values": {...}}),
          Distribution(criteria="freegame", quota=0.999,
                       conditions={"reel_weights": {...}, "force_freegame": True, ...}),
        ])
```
- `quota`: share of the mode's simulations that must satisfy the criteria (normalised).
- Required condition keys: `reel_weights`, `force_wincap`, `force_freegame` (latter two default False).
  Arbitrary extra keys (`mult_values`, `scatter_triggers`, …) are read in game logic via
  `get_random_outcome(betmode.get_distribution_conditions()['mult_values'])`.
- `win_criteria`: 0.0 (forced losses) or `self.wincap` (forced max wins).
- `auto_close_disabled`: if False, round closes automatically (player can't resume);
  set True for games with player decisions mid-round, then call end-round yourself.
- `is_feature`: frontend keeps the mode selected for every spin (feature toggle mode).
- `is_buybonus`: frontend knows the mode was bought (assets/UI may change).

Typical distribution set for a base mode: `wincap`, `freegame` (bonus trigger), `0`
(non-winning, `win_criteria=0.0`), `basegame` (regular wins).

## Events
Each simulation emits events consumed by the frontend; standard ones:
`reveal` (board, paddingPositions, gameType, anticipation), `winInfo` (totalWin, wins[] with
symbol, kind, win, positions, meta), `setWin` (amount, winLevel), `setTotalWin`,
`freeSpinTrigger`, `freeSpinRetrigger`, `enterBonus`, `updateFreeSpin`, `tumbleBoard`,
`setTumbleWin`, `updateTumbleWin`, `updateGlobalMult`, `freeSpinEnd`, `wincap`, `finalWin`
(constants in `src/events/event_constants.py`). Add custom events in `game_events.py`; every custom event type needs a
frontend handler. Keep events minimal but sufficient – books are what the RGS serves, so
size matters.

Wins/amounts inside events are in the same ×100 integer units as `payoutMultiplier`
(e.g. 10 = 0.1x bet).

## Optimisation
The optimiser adjusts LUT weights (initially 1) to hit target RTP per mode and per
distribution criteria while keeping hit-rate/volatility targets (`OptimizationSetup` in
`game_optimization.py`). For finer control there is `StakeEngine/convex-optimizer`.
Force files (`forces/force_<mode>.json`) index which sims contain which recorded features –
useful for finding replay IDs (wincap, bonus trigger) and frontend testing.

## Publish files (what you upload)
`library/publish_files/`:
```
index.json                       {"modes":[{"name","cost","events","weights"},...]}
books_<mode>.jsonl.zst           zstd JSONL, line i has "id": i
lookUpTable_<mode>_0.csv         sim_id,weight,payoutMultiplier  (uint64, no header)
```
Rules enforced at upload: `id` == line index; LUT payout must exactly equal book
`payoutMultiplier` (they are hashed and compared); integers only; one LUT row per book line.
Also generated: `config.json` (backend), `config_fe.json` (frontend: symbols, paytable,
modes), `config_math.json` (optimiser).

Validate with `scripts/validate_math.py library/publish_files`.

## Writing math without the SDK
Allowed – any language – as long as the three file types above are produced exactly.
Simulate many rounds, write events per round, assign weights so that
`RTP = Σ(weight·payout/100) / Σ(weight) / cost` hits the target.
