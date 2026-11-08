# Win presentation: screens, behaviour, timing

Second half of SKILL.md section 8 (win celebrations); 8.1 (Stake rules) and 8.2 (tier mapping) stay in SKILL.md because they are compliance rules. Subsection numbers 8.3 to 8.5 are unchanged. Read it when designing or wiring the celebration screens and the round controller.

## 8 (continued)

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
  above) plus a roll-up loop. The art side (asset list per screen, tier escalation rules, file
  names, hand-off) is in `casino-symbol-art/references/win-celebration-art.md`; measured round, win-highlight and bonus-flow timing of a reference game
  is in `casino-symbol-art/references/animation-timing.md` (a whole round near 1 s, a win highlight about 0.65 s with the HUD updating after it).

### 8.5 Round, win-highlight and bonus timing rules (apply these in the round controller)
Basis: measured on one reference game's public demo (60 spins, 25 fps recording, one session; details and limits in
`casino-symbol-art/references/animation-timing.md`). They are **structure and timing to reuse with our own art**, never their art. Items marked authored are our
defaults, not measurements. Re-measure on your own build with `casino-symbol-art/scripts/anim_probe.py cycle`.

Order of one round inside the book-event player (each step awaited, none skipped):
1. **Clear**: symbols leave the board (about 0.3 s). Then an **empty beat** (about 0.25 s). A visible reset, not dead time.
2. **Enter**: columns drop in left to right, about **0.16 s apart**, 0.25 to 0.45 s per column; each symbol plays `land` (authored, 150 to 300 ms).
3. **Specials announce on arrival**: a Wild or Scatter that lands gets its own flash and ring (about 0.8 s), not only when it pays.
4. **Win highlight**: each winning symbol plays `win`, one shot of about **0.65 s** (emissive flash, glow ring, glint, fade). Dimming the others is a design choice (one reference game did not dim, another dimmed non-winners while winners glowed); keep the winners clearly brighter either way.
   Show the **win amount on the winning group** for the same duration; update the **HUD WIN field after** the highlight (about 0.85 s after it started).
   Several wins or cascades: play the highlights in sequence, never overlapping.
5. Only when `winLevel` is Big or above (§8.1): the tier celebration of §8.3, after the highlight and before the next round.

| Rule | Value | Basis |
|---|---|---|
| Whole round, clear to settled | about 1.0 s; investigate above 1.4 s | measured |
| Empty beat between clear and enter | about 0.25 s | measured |
| Column stagger | about 0.16 s | measured (read from frames) |
| Small-win highlight | about 0.65 s, one shot | measured (in the game that did not dim) |
| HUD update after the highlight | about 0.85 s after its start | measured |
| Special symbol arrival flash | about 0.8 s | measured on one symbol |
| `land` squash and stretch | 150 to 300 ms | authored |
| Turbo | scale every duration by about 0.5, keep the order, keep the final amount readable | authored |
| Resting symbols | static; add an idle loop only if the design asks for it | measured (none seen) |

Bonus flow: an **intro plate** with the rule in a few words that **waits for the player**; then the **same round cycle** as the base game (do not invent a second rhythm);
a **summary plate** (TOTAL WIN) that waits for the player and is also the feature summary of §8.3; transitions use **one physical metaphor of the game's theme**, applied
consistently (open and close the same way every time). A mid-size bonus total with no Big-Win level needs the summary plate only.
Not measured, so do not assume numbers for them: big-win tier screens, scatter anticipation, retrigger banners, skip behaviour, audio.
Rolling-reel games have no clear and enter phases; keep the stagger and the one-second target, and judge the rest by feel.
