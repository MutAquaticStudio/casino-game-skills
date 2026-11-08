# Bet UI / HUD design

Moved out of SKILL.md (it is section 13 there; subsections 13.0 to 13.5 are unchanged). Phone layout numbers and tools: `references/mobile-ui.md`; desktop wireframe: `references/layout-wireframes.md`.

## 13. Bet UI / HUD design

Learned from a reference set of live slots from four different studios (Nov 2026). Use the
patterns, not the look: build an original skin – copying another studio's UI risks rejection.

### 13.0 Simplicity first (the common thread in all four references)
All four studios ship a **very plain** Bet UI: a handful of flat controls, one dominant spin
button, no ornate frames. The theme lives in the board, symbols, background and effects – not
in the HUD. This is a design guideline from the samples, not a Stake rule, but treat it as the
default; every extra element has to earn its place.
- **Control budget:** about 5–8 persistent elements on screen (spin, bet, balance, win,
  autoplay, menu, plus at most one of turbo / mode button). Everything else (sound, info, paytable,
  settings, history, turbo on small screens) goes inside the menu.
- **One hero:** spin is the only large, high-contrast element; nothing else competes with it.
- **Values are plain text:** balance, win and bet are a label + number on a flat translucent
  panel or a scrim – no gem/metal/wood frames around numbers, no per-value ornaments.
- **Flat, consistent shapes:** one corner radius, one icon style (filled or outline, not both),
  one accent colour for spin and one for the feature/mode button.
- **Quiet at idle:** no looping decorative animation, glow or particles on the HUD while the
  player isn't interacting; motion is reserved for state changes (spin, win roll-up, mode switch).
- **Skin lightly:** tint the panel colour, accent and icon glyphs to the theme; keep standard
  positions and shapes. If a themed HUD makes the player hunt for spin or bet, it is over-designed.
- **Progressive disclosure:** pickers (bet levels, autoplay setup, mode list) open on demand;
  don't permanently show options the player uses once per session.
- Test: cover the board – can a new player still name each control within two seconds?

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
- **Desktop / laptop** (nine games measured, wireframes and table in `references/layout-wireframes.md`): board frame centred (about 53% of the width, 83% of the height, it may run under the dock);
  the **mascot stands on one outer side** (about 20% of the width, full body; 5 of 9 on the left, 3 on the right) with the feature meter or panel on the opposite side; logo above the mascot or centred on the
  frame top; one HUD dock at 83 to 96% of the height (menu, balance, win, bet with arrows, autoplay, spin about 12% of the height, emblem at the right end), turbo floating at the left. On a phone the
  same blocks move: mascot to a bust above the board, meter to a bar below it (§ below, `references/mobile-ui.md`).
- **Popout L/S (800×450, 400×225):** compress the dock – values without labels, merge
  balance/win into one cell, move secondary buttons into the menu, spin stays ≥ 44 px, board
  keeps ≥ ~65% of the height.
- **Mobile portrait** (measured on five games of one studio and on the owner's game; full evidence, tables and tools in `references/mobile-ui.md`):
  the board frame bleeds to the full width and is anchored just below a **hero zone** (16 to 25% of the height on a 19.5:9 phone, mascot overlapping the board's top edge with its
  lower body hidden behind the frame); the feature meter sits directly under the board (horizontal); a decorated **scene band of 11 to 13%** holds two floating buttons
  (turbo or bonus left, emblem right); the HUD is pinned to the bottom: control bar (menu, bet −, spin about 18% of the width, bet +, autoplay) at 88 to 94%, a footer of three
  values (balance, bet, win) at 95 to 100%. Never centre the stack in the free space and never leave a dark empty band: dead bands above 26% in total (`scripts/mobile_layout.py report`)
  look unfinished. One asset set serves PC and phone; the layout comes from the window size. Test 360x800, 375x667, 390x844, 412x915 and a landscape phone with `scripts/mobile_capture.mjs`.
- **Mobile landscape:** side-rail variant (spin right-middle, settings left).

### 13.5 Visual rules
- Text and icons over art always get a backing (panel, disk or gradient scrim); thin outline
  icons straight on busy art fail contrast. Values need ≥ 4.5:1 contrast.
- Colour roles: one accent for the primary action (spin), one for feature/buy; states via
  fill vs outline; disabled ≈ 40% opacity; animate the spin ring while spinning.
- Typography: a sturdy UI sans for labels/values; the theme display font only for logo/titles.
- Skin with restraint (see §13.0): a subtle material hint on the dock edge and themed icon
  glyphs are enough; keep the conventional positions and shapes so players instantly find spin,
  bet and balance.
- Localization: labels grow (de/fi/ru); test the longest value (e.g. "¥150,000,000"). Social mode:
  "BET" → "PLAY AMOUNT"/"PLAY", "CREDIT" → "BALANCE"/"COINS", "BUY" → "GET"; no "AutoBET".
