# How a reference game handles animation (timing and structure, not style)

Goal: learn the **quality bar and the way a good studio sequences motion**, then apply it to our own art. Nothing here is about their
characters, palette or art; the numbers and the structure are what to reuse.

Source: Valkyrie Studio's public demo of Loki's Vault, recorded in a headless Chromium (software rendering, 1280x720, about 25 fps, 60
spins, 427 s, 2026-11-08). Frames were read one by one and measured with `scripts/anim_probe.py`; win amounts were read by OCR.
Accuracy is one frame (40 ms) at best, one game, one session. A headless browser can run slower than a phone, so treat the numbers as relative.

## 1. The round cycle (measured, 27 rounds with a clear cycle)
This game does not roll reels. Each round **clears and refills the board**:
| Phase | Median | Spread (p10 to p90) | What you see |
|---|---|---|---|
| Drop-out | 0.32 s | 0.12 to 0.57 | the symbols fall out of the board |
| Empty beat | (included above, 0.24 s to the first entry) | 0.04 to 0.47 | the board is visibly empty: dark carved panel, nothing on it |
| Columns drop in | about 0.16 s apart, left to right | (automatic onset detection was noisy: 0.12, 0.0, 0.16, 0.0; confirmed on a frame montage) | each column falls from above |
| Entry to settled | 0.48 s | 0.28 to 0.77 | the last column lands and the board is complete |
| **Whole cycle** | **1.00 s** | 0.82 to 1.37 | fast: a round feels snappy, not slow |
Principles: give every state change a **beat** (the empty board is a deliberate reset, not a delay); **stagger by column**, about 0.16 s;
keep the whole cycle near one second. Slow cycles are the most common reason slots feel cheap.

## 2. A small win (measured on a 0.70x win)
Timeline from the first highlight frame (80 ms resolution):
- 0 to 0.16 s: each winning symbol flashes into a bright emissive disc, slightly larger than at rest.
- 0.16 to 0.40 s: it settles into a glowing glass-like version of the symbol with a ring glow (scale about 1.1).
- about 0.40 s: a small glint (star sparkle) crosses it.
- 0.40 to about 0.65 s: the glow fades and the symbol returns to rest. One shot, no looping pulse.
- **In this game the other symbols are not dimmed.** The highlight is carried by emission, not by darkening the rest. Dimming is a per-game choice: Odin's Vault, another game of the same studio, was seen
  in one phone frame with the three winning tiles glowing and every other symbol darkened (timing not measured). Pick one behaviour per game and keep winners clearly brighter than the rest.
- A **win amount label** ("0.70") appears at the centre of the winning group for about the same 0.7 s, in the game's own numeral font.
- The HUD WIN field updates **after** the highlight, about 0.85 s after it started, not at the same moment.
Principles: swap to an emissive state rather than scaling a loop (dim the rest only if the design wants it); show the amount where the eye already is (on the group), then let the HUD follow;
keep it short enough that a fast player is never waiting. The recipe `win` in `scripts/symbol_fx.json` follows this shape (the `flash` and
`glint` tracks drive overlays; the old pulse is kept as `win_loop`).

## 3. Special symbols
A Wild that lands gets its own flash and ring pulse that lasts about 0.8 s (a bright disc, then a blue ring that breathes and settles), separate
from the win highlight. Specials announce themselves when they arrive, not only when they pay.

## 4. Bonus (free spins) flow, as recorded
1. **Intro plate** on a themed panel with the rule in a few words ("Sticky multiplier through the entire bonus, every spin +1") and a PRESS TO CONTINUE prompt; it waits for the player.
2. The board clears to an empty panel, then the first round drops in (same cycle as the base game).
3. During the bonus each round is the same cycle plus the same win highlight (the recorded bonus rounds took about 1.4 s including the highlight), with the amount label on winning groups. The sticky multiplier is shown on the board frame.
4. After the last round the board dims, then **themed doors close over the board** (about 0.5 s) and a **TOTAL WIN plate** ("CONGRATULATIONS, TOTAL WIN 12.90") appears on them. It waits for a press, then the base game returns. A 12.9x total did not trigger any separate big-win overlay in this game; the summary plate was the celebration.
Principles: transitions use **one physical metaphor of the game's theme** (here vault doors), consistently; the intro and the summary are plates that wait for the
player; the bonus does not invent a different rhythm, it reuses the base-game cycle.

## 4b. What was not seen
- A big-win tier overlay (Big, Mega, Epic): never reached. Do not infer its timing from this.
- Reel anticipation for scatters, retrigger banners, turbo or skip behaviour, and sound (not recorded).
- Symbol idle animation: **resting symbols were still** in the recording. Our `idle` recipe is therefore optional.

## 5. How to apply it to our game without copying
1. Match the **structure**: board clear, empty beat, column stagger about 0.16 s, cycle near 1 s, emissive win state, label on the group, HUD after, themed transition metaphor, waiting summary plate.
2. Draw all of it with **our own art**: our own emissive states, our own numerals, our own transition metaphor (doors are theirs; choose something that fits our theme).
3. Put the numbers in `scripts/symbol_fx.json` and the cycle timing in the round controller; check with `scripts/symbol_fx_preview.py`.
4. Re-measure on your own build (`scripts/anim_probe.py cycle`) to confirm that you land near one second on a real device.
