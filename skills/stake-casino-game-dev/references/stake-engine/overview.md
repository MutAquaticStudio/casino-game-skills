# Stake Engine – overview, rules and process

Source: https://stakeengine.github.io/docs/ (repo `StakeEngine/docs`, pages under
`src/routes/docs/`). Summarised November 2026 – re-check the live docs for anything decisive.

## What it is
A platform for independent studios to build and publish casino games (mostly slots) on
Stake.com (real money) and Stake.us (social casino, Gold Coins / Stake Cash). Two official SDKs:

| SDK | Tech | Role |
|---|---|---|
| Math SDK (`StakeEngine/math-sdk`) | Python (+ Rust optimiser) | Game rules, simulation, optimisation, publish files |
| Web SDK (`StakeEngine/web-sdk`) | Svelte 5, PixiJS 8, Turborepo, Storybook, XState | Browser client that renders books |
| ts-client (`StakeEngine/ts-client`) | TypeScript | Thin RGS client |

Neither SDK is mandatory. The math only has to produce valid static files; the frontend can
be any stack (React/Vue + Pixi, Phaser, **Three.js**, plain Pixi) as long as the build is static.

## Architecture
1. Developer simulates N rounds per bet mode → **books** (`.jsonl.zst`, one JSON per line:
   `id`, `payoutMultiplier`, `events[]`) and **lookup table** (CSV, no header:
   `sim_id,weight,payoutMultiplier`), plus `index.json` listing modes.
2. Uploaded to the RGS ("Carrot" Remote Gaming Server).
3. On `/wallet/play` the RGS does weighted random selection over the LUT (cumulative
   weights + binary search), debits the bet, returns the chosen book's events as `round.state`.
4. Frontend animates the events; for payout > 0 it calls `/wallet/end-round` to credit.

Key properties: stateless (no history between rounds), only outcomes present in the books can
ever happen, RTP is fully determined by LUT weights. **Wincap** = max win per round per mode.
**Bet modes** each have their own LUT + books, cost multiplier, RTP, wincap.

## Hard restrictions (rejection if violated)
- Stateless only: no jackpots, gamble features, continuation, early cashout.
- Original game only – no pre-purchased/licensed games that exist elsewhere.
- IP/copyright-clean team names, titles and assets. Title must be unique and must not use
  terms like "Megaways" or "Xways".
- No Stake™/Kick™ branding or themes in assets.
- Nothing offensive, explicit, discriminatory or in poor taste; reviewer discretion.
- Nothing that promotes or appeals to minors, including child-like characters.
- Unique art/audio – Web SDK sample assets will not be approved.
- Post-release: only minor visual fixes; no math, mode or mechanic changes.

## Process
1. Register at stake-engine.com, create team profile, set provider logo (Team Settings →
   Branding; square PNG/JPG/GIF ≤10 MB).
2. Build math → upload math files (dashboard runs format checks + summary stats).
3. Build frontend → upload static build (served from `{team}.live.stake-engine.com/{game}/v{n}/`
   or the CDN path; all assets must come from the Stake Engine CDN/your build).
4. Create game tile in the dashboard Tile Editor (background, foreground, gradient, title).
5. Submit math + frontend approval requests. Provide replay event IDs per mode
   (normal win, big win, wincap, loss, bonus trigger).
6. Review: 3 anonymous reviewers score 0–3 in thirds; average <1.0 → not approved, thread
   locked 7 days, then resubmit. Rounded average gives star tier:
   - 3★ studio quality → featured / Burst Games / Stake Exclusives eligible
   - 2★ creative, less polished → placement by popularity
   - 1★ meets requirements → bottom of New Releases
7. Final: bet-level templates applied (Stake.us uses a `us_`-prefixed template), both
   requests Approved & Active, game appears in approved channels, goes live (🚀).

## Viewport sizes to support
Desktop 1200×675, Laptop 1024×576, Popout L 800×450, Popout S 400×225 (all 16:9),
Mobile L 425×812, Mobile M 375×667, Mobile S 320×568.

## Useful links
- Docs: https://stakeengine.github.io/docs/ (Approval, API, Math SDK, Web SDK, Reference)
- Legacy Math SDK docs: https://stakeengine.github.io/math-sdk/
- Docs MCP server: `StakeEngine/docs/mcp-server` (search_docs, get_page, list_pages)
- Community: Discord linked from the docs footer
