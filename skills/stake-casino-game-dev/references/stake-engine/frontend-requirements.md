# Frontend requirements

From docs `approval/frontend-requirements`, `approval/rgs-requirements`, `approval/disclaimer`,
`reference/social-mode`, `reference/dimensions`, `architecture/frontend-stack`.

## Build
- Static files only (HTML/CSS/JS + assets). SvelteKit → `adapter-static`; Vite default build is fine.
- Strict XSS policy: no requests to external origins. Bundle fonts (no Google Fonts), no
  analytics, no external CDNs. Images/fonts load from the Stake Engine CDN, i.e. your
  uploaded build. Use relative asset paths (`base: './'` in Vite).
- No console errors and no game information logged to the network tab/console in production.

## Display
- Unique art and audio (Web SDK sample assets are rejected). No visual bugs/missing assets.
- Support desktop, mobile (common devices) and popout/mini-player down to 400×225 without
  distorting the board; all UI usable at every size. Sizes: 1200×675, 1024×576, 800×450,
  400×225, 425×812, 375×667, 320×568.
- Fast-play/turbo (if any) must keep wins, winning combinations and popups legible.

## Rules / info screen (reachable at all times, e.g. `i` or `?`)
- Full rules description; UI guide explaining each button.
- RTP per mode; max win per mode; cost and description of each mode.
- Payouts for every symbol combination; list of win combinations (lines diagram, cluster
  sizes, scatter counts…); all values for special symbols (multipliers, cash prizes).
- How features trigger and retrigger ("3 scatters award 10 free spins, 4 award 15…").
- Disclaimer covering: malfunction voids all wins and plays; stable connection required;
  reload to finish uncompleted rounds; expected return over many plays; display illustrative,
  not a physical device; winnings settled per RGS not browser events; TM/© notice. Template:

  > Malfunction voids all wins and plays. A consistent internet connection is required. In the
  > event of a disconnection, reload the game to finish any uncompleted rounds. The expected
  > return is calculated over many plays. The game display is not representative of any physical
  > device and is for illustrative purposes only. Winnings are settled according to the amount
  > received from the Remote Game Server and not from events within the web browser.
  > TM and © 2025 Stake Engine.

## UI components & behaviour
- Change bet size; every RGS bet level available (min..max, `stepBet`); default from RGS.
- Balance always visible (except replay). Final win shown for non-zero results; when a round
  has several wins, the win counter must increment step by step to the final total.
- Sound on/off toggle.
- **Spacebar = bet/spin button.**
- Autoplay requires a confirmation step – never start consecutive bets with one click.
- Switching to a mode costing more than 2× requires confirmation (e.g. bonus buy dialog).
- Verify 10 wins per mode: displayed win equals RGS payout.

## Languages & currencies
English required. Unsupported `lang` values must fall back cleanly (no broken glyphs/keys).
Tested with many currency/language combinations. Format money from integer minor units with
currency decimals; GC/SC shown without `$`.

## Social mode (stake.us, `social=true`)
Use English with replacements regardless of `lang`. Applies to rules, UI labels, popups,
error messages, replay window and **images** (no "BUY"/"BET" baked into art). Key replacements:

| Restricted | Use |
|---|---|
| bet / bets / betting | play / plays / playing |
| total bet | total play |
| bonus buy / buy bonus / buy / purchase | bonus or feature / get bonus / play / play |
| bought | instantly triggered |
| cash / money / credit | coins |
| currency | token |
| pay / pays / pays out / paid / paid out | win / wins / win / won / won |
| pay table | win table |
| payer | winner |
| stake | play amount |
| wager / gamble | play |
| cost of / at the cost of | can be played for / for |
| deposit / withdraw | get coins / redeem |
| profit | net gain |
| rebet | respin |
| loss limit / loss streak | stop limit / miss streak |
| place your bets | come and play / join in the game |
| win feature | play feature |
| be awarded to player's accounts | appear in player's accounts |

Checklist specifics: bet button not labelled "bet"; bet amount field not labelled "bet amount";
autobet not "AutoBET"; bonus buy label has no "BUY"; its confirmation has no "buy"/"bet";
insufficient-funds message clean. `scripts/check_social_terms.py` scans text files.

## Recommended stack (not required)
Svelte 5 (UI) + PixiJS 8 (2D) + GSAP (timelines); Spine or spritesheets for symbol/character
animation. Alternatives used successfully: React/Vue + Pixi, Phaser, Three.js, pure Pixi.
