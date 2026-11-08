---
name: "casino-game-audit"
description: "Audit a casino/slot game build for visual quality: graphics, render quality, effects, mode transitions, bet UI, spacing and typography, Stake-compliant win celebrations, audio and localization. Produces a scored report with prioritized fixes."
---

# Casino game quality audit

The goal: find what makes a casino game look and feel cheap or broken, and tell the developer
exactly what to fix, in priority order. Stake Engine reviewers give 0–3 stars for quality
(an average below 1 is not published; 3 stars gets featured), so this audit is about
visibility and approval, not just taste. Answer in the user's language; keep technical terms
in English.

## 1. Gather evidence first
Work from real evidence and say what you could not check.
- **Running build** (best): serve `dist/` locally and capture screenshots/video with a browser
  tool at the sizes below. Use URL params (`lang`, `currency`, `social`, `device`, `replay`)
  and forced books/replay IDs to reach rare states (bonus, retrigger, each win tier, max win).
- **Screenshots/video from the user**: ask for base idle, a spin in motion, a normal win, each
  win tier, bonus intro, a bonus spin, bonus summary, every modal, the rules pages, mobile and
  popout views.
- **Source code**: render setup, asset loading, layout code, locale files, audio manager.
- Sizes: Desktop 1200×675, Laptop 1024×576, Popout L 800×450, Popout S 400×225, Mobile
  L 425×812, M 375×667, S 320×568.

Look at the screenshots yourself (open the images) rather than guessing from code.

## 2. Audit areas and what to check

### A. Graphics & art direction
- One coherent style: same light direction, outline weight, palette and rendering style across
  symbols, background, UI and popups. Mixed styles look cheap. When the layers are available,
  run `casino-symbol-art/scripts/style_check.py` and report FAIL/WARN rows; from screenshots only,
  compare a contact sheet of symbol, frame, backdrop and win title side by side. Metrics miss shape
  language and line quality, so always add your own judgement.
- Symbol hierarchy: high/low/special symbols readable at a glance by shape and colour;
  distinguishable for colour-blind players (test with a deuteranopia filter).
- Symbols fill their cells consistently; none blurry or upscaled.
- The background supports the board (lower contrast/saturation behind the reels).
- Originality: no sample-pack assets, no IP lookalikes, no Stake branding, nothing child-appealing.

### B. Render quality
- Sharpness: canvas resolution matches `devicePixelRatio` (capped ~2); no blurry text/sprites on
  retina; textures sized for their display size; mipmaps where scaled down.
- No artefacts: atlas bleeding (pad/extrude), jagged edges (AA/FXAA/SMAA), gradient banding
  (dither), z-fighting, flicker, alpha halos (premultiplied alpha), jitter on moving text.
- Colour: consistent colour space (Three.js `outputColorSpace = SRGBColorSpace`, sRGB textures),
  deliberate tone mapping, no washed-out or over-dark scenes.
- Performance: steady 60 fps on desktop, ≥30 (ideally 60) on mid-range phones during the heaviest
  moment (max-win celebration in the bonus). Measure draw calls, triangles, texture memory and long
  frames; check hitches on the first win (shader compile – warm up) and on bonus scene load.
- Load: first-play size, loading screen with progress, no layout pop-in.
- Mini-player 400×225 not distorted; resizing mid-spin doesn't break the board.

### C. Effects (VFX) and motion
- Important events get layered feedback (symbol animation + particles + light + sound + counter)
  that settles back to rest; nothing loops forever or stacks without limit.
- Intensity scales with importance; big FX are reserved for Big Win and above, features and
  Max Win. Small and sub-stake wins stay subtle.
- Motion: eased tweens, anticipation/overshoot on reel stops, staggered stops, consistent timing;
  particles never cover numbers or winning symbols.
- Reels: motion blur/speed stretch while spinning, clean bounce on stop, no visible symbol swap.
- Turbo keeps essential FX and keeps results legible.
- **Timing check** (from a recording or the live build; reference values from one game, so flag a deviation of about 2x, not 20 percent):
  a whole round from clear to settled near 1.0 s (rolling reels: stops staggered about 0.16 s, spin plus stops near 1 to 1.5 s); columns or reels
  entering with a visible stagger; a small-win highlight of 0.5 to 0.9 s, played once, that does not hide the symbols (dimming the non-winners is a legitimate choice, but winners must stay clearly brighter); the win amount near
  the winning group and the HUD WIN field updating after the highlight, not before; special symbols (Wild, Scatter) that announce themselves when they land; a bonus that
  keeps the base-game rhythm, with an intro plate and a TOTAL WIN plate that wait for the player. Measure with `casino-symbol-art/scripts/anim_probe.py` (`frames`, `montage`, `cycle`);
  state the method and the frame rate in the report, and say which items could not be checked.

### D. Transitions between modes and scenes
Check: base → feature trigger → bonus intro → bonus → retrigger → bonus summary → base;
bet mode switches (base ↔ boost ↔ bonus buy); entering/leaving replay.
- A themed transition exists (no hard cut), ~0.6–1.5s, skippable/turbo-aware.
- Music crossfades; the HUD changes state clearly (spins remaining, meter, bet controls disabled
  in the bonus).
- The selected mode is always obvious; buy modes show the real cost; modes costing >2x ask for
  confirmation.
- Returning to base restores bet and mode; no leftover particles or sounds.

### E. Bet UI / HUD
- Required: spin button (spacebar bound), bet selector with all RGS bet levels incl. min/max,
  balance, win field, sound toggle, rules/info, autoplay with confirmation, turbo if present,
  mode/bonus-buy access.
- Hierarchy: spin button dominant, bet value next, secondary controls grouped and quieter.
- Touch targets ≥ 44×44 px; thumb reach in portrait; hover/pressed/disabled states; clear
  disabled state while spinning.
- Bet values formatted per currency (JPY 0 decimals, GC/SC without `$`); long values fit.
- Modals consistent, readable, closable, and never hiding the result just shown.
- Social mode labels without restricted words (Bet, Buy, Cash…).
- Layout archetype identified (bottom dock / floating cluster / side rails) and applied
  consistently; order settings → balance → win → bet → spin → modes; bet next to spin.
- Measure against `stake-casino-game-dev` §13: dock ≈ 9–12% H, spin ≈ 1.3–1.6× dock height and
  the most prominent element, secondary buttons ≈ 0.5–0.65× spin, value text ≈ 1.5× label text,
  win cell reserved at 0 (no layout jump).
- Simplicity (`stake-casino-game-dev` §13.0): about 5–8 persistent controls, spin is the single
  hero element, values are plain label + number (no ornate frames), one icon style and one corner
  radius, no idle HUD animation, secondary options live in the menu. Deduct for an over-designed
  HUD: decorative frames around numbers, many competing buttons or accents, looping glow or
  particles on the HUD, a themed layout where spin/bet are hard to find (cover-the-board test).
- Text/icons over art have a backing or scrim; no thin outline icons straight on busy art.
- Flag as blockers: ante/feature toggles costing > 2× without a confirmation step,
  hold-to-spin / hold-space continuous spinning, autoplay that starts on one tap, missing bet
  levels, missing sound toggle; flag operator widgets (lobby, tournaments) inside the game.
- Popout 400×225 and mobile portrait/landscape variants exist and keep spin, bet and balance usable.
- **Phone portrait composition** (reference values from five games of one studio, `stake-casino-game-dev/references/mobile-ui.md`): board frame at the full width and anchored just below a hero
  zone; a mascot or hero above the board rather than an empty top band; feature meter directly under the board; no dark or empty band between the board and the HUD (dead bands up to 26% of the
  height in total is the reference range; measure with `scripts/mobile_layout.py report`); HUD pinned to the bottom with a spin of about 18% of the width; layout recomputed from the window size
  at 360x800, 375x667, 390x844, 412x915 and a landscape phone (capture with `scripts/mobile_capture.mjs`).

### F. Spacing, layout & typography
- A spacing scale (4/8 px grid) used consistently; equal margins around the board; HUD on a
  grid; nothing touching edges or notch safe areas.
- At most 2 font families (display + UI); a clear size scale; minimum ~12 px CSS at Popout S and
  ~14 px on mobile; **tabular digits** for counters (no jitter); contrast WCAG AA 4.5:1 for body
  text; outline/shadow on text over busy art.
- Display fonts only for titles; fonts bundled (no font CDN) and covering every shipped
  language (Vietnamese diacritics, Cyrillic, CJK, Arabic, Devanagari).
- Rules/paytable: scannable headings, paytable grid with symbol images, worked examples,
  RTP/max win/cost per mode easy to find, disclaimer present.

### G. Win celebrations (Stake-compliant)
- Celebration screens **only from Big Win upward** (`winLevel` ≥ 5): Big → Mega → Epic → … →
  Max Win, driven by the book's `winLevel`, chaining upward during the roll-up. Flag any popup,
  banner, fanfare or coin shower on wins below Big Win as an issue (and below the stake as a
  responsible-design blocker).
- Wins below Big Win: highlight of winning positions + HUD win field roll-up only.
- The HUD win amount updates incrementally across multiple wins and ends exactly on the RGS
  payout; the final win is visible for every non-zero result.
- Celebrations skippable (tap/space) and turbo-aware; still legible in fast-play.
- Buy modes: tiers judged against the real cost.
- Feature trigger, retrigger, bonus summary and Max Win screens exist and match the visual
  language; text fits at all sizes and languages.
- No jackpot imagery or wording; social mode wording clean.

### H. Audio
(Use `casino-audio-design` for depth.)
- Unique music for base and bonus; SFX for spin, reel stops, anticipation, wins, triggers,
  buttons; tier stings only for Big Win and above; mute toggle that persists.
- Mix: no clipping; ~−16 to −14 LUFS integrated; music ducks under big moments; variations
  for repeated sounds.
- Sync ≤ ~50 ms; audio stops when the tab is hidden; nothing before the first interaction.

### I. Localization
- Pseudo-locale shows no hardcoded text; no clipping at de/fi/ru lengths; Arabic RTL correct;
  CJK line height fine; unknown `lang` falls back to English; `social=true` shows social English;
  Stake uses `po` for Polish.

## 3. Scoring and report
Score each area 0–5 (0 broken, 1 amateur, 2 below market, 3 market standard, 4 polished,
5 studio/flagship) and estimate the Stake star range: mostly ≤2 → risk of <1★; mostly 3 →
~1–2★; mostly 4 with strong art/FX → 2–3★; 5s in art, FX and win celebrations → 3★ contender.

ALWAYS use this report structure:
```
# Quality audit – <game> (<build/version>, <date>)
Evidence reviewed: <screens/sizes/langs/modes checked; what could not be checked>
## Scorecard
| Area | Score /5 | Summary |
## Blockers (approval risk or broken)
| # | Area | Issue | Where (screen/size/file) | Fix |
## High-impact polish (biggest star-rating gain per effort)
## Minor issues
## What already works well
## Suggested order of work (1–2 week plan)
```
Each issue must be concrete (screen, size, element, measured value) with a specific fix (e.g.
"Win counter uses proportional digits → jitters; use `font-variant-numeric: tabular-nums` or a
bitmap font"), not generic advice. Separate approval blockers from taste.

## 4. Useful tools
- DevTools Performance panel, `stats.js`, `renderer.info` (Three.js), Pixi devtools.
- Lighthouse for load size; Chrome Rendering panel for colour-vision emulation.
- Contrast checker; a screenshot grid (screen × size × language).
- Loudness: `ffmpeg -i file.mp3 -af ebur128 -f null -` (LUFS, true peak).
