# RGS API

Base URL comes from the `rgs_url` query parameter (hostname, no scheme) – **never hardcode**
(staging, production and replay differ). Docs: https://stakeengine.github.io/docs/api

## Launch URL
```
https://{team}.live.stake-engine.com/{game}/v{version}/?sessionID=…&rgs_url=…&lang=en
  &currency=USD&device=desktop&social=false&demo=false
```
| Param | Notes |
|---|---|
| `sessionID` | required for all wallet calls |
| `rgs_url` | required; base for all calls: `https://${rgs_url}` |
| `lang` | ISO 639-1; English is the only required language, but other values must not break text |
| `currency` | display only |
| `device` | `desktop` / `mobile` |
| `social` | `true` on stake.us → apply restricted-phrase replacements, English |
| `demo` | free play |
| `replay` | `true` + `game`, `version`, `mode`, `event`, optional `amount`, `currency`, `lang`, `device`, `social` |

## Endpoints (POST JSON bodies)
| Endpoint | Body | Returns |
|---|---|---|
| `/wallet/authenticate` | `{sessionID, language}` | `balance{amount,currency}`, `round` (active or last round, may be null), `config{gameID,minBet,maxBet,stepBet,defaultBetLevel,betLevels[],betModes}` (`jurisdiction`, `meta`: ignore) |
| `/wallet/balance` | `{sessionID}` | `balance` |
| `/wallet/play` | `{sessionID, amount, mode, currency}` | `balance` (after debit), `round{payoutMultiplier, costMultiplier, state}` – `state` is the book events |
| `/wallet/end-round` | `{sessionID}` | `balance` (after payout). Only for payout > 0 – zero-payout rounds auto-complete |
| `/bet/event` | `{sessionID, event: "<index>"}` | records progress inside a round for resume |
| `GET /bet/replay/{game}/{version}/{mode}/{event}` | – | `{payoutMultiplier, costMultiplier, state}`; no session needed |

Must authenticate first; otherwise `ERR_IS`.

## Money
All amounts are integers with **6 decimal places**: `1_000_000` = 1.00 unit. Bet sent to
`/wallet/play` = display amount × 1,000,000. Win = bet × payoutMultiplier (play response is a
float multiplier; book values are ×100 integers). Display decimals per currency: USD 2,
JPY 0, XGC "GC" 2, XSC "SC" 2 (no `$` prefix for GC/SC). See docs `reference/currencies`.

Bet levels: use `config.betLevels`, `minBet`, `maxBet`, `stepBet`, `defaultBetLevel` from
authenticate. All levels incl. min and max must be selectable. Example checks used in
review: USD $0.10–$1,000 default $1; JPY ¥10–¥150,000 default ¥100; MXN 1–15,000 default 10.
Refreshing mid-spin must keep the selected bet (persist it per currency, e.g. localStorage
wrapped in try/catch, falling back to `defaultBetLevel`).

Mode cost: the real debit is `amount × mode.cost`; show it ("BONUS 1 USD – 100 USD real cost").

## Errors
400: `ERR_VAL` invalid request, `ERR_IPB` insufficient balance, `ERR_IS` invalid/expired
session, `ERR_ATE` auth failed/token expired, `ERR_GLE` gambling limits exceeded,
`ERR_LOC` invalid location. 500: `ERR_GEN`, `ERR_MAINTENANCE`.
Show a clear, localisable message for each; for stake.us the insufficient-funds text must
use social wording (no "bet", "money", etc.).

## Round lifecycle
```
load → parse URL → (replay? → replay flow)
     → authenticate → if round active and not finished: resume it (replay its state, then end-round)
     → idle → play → animate events sequentially → if payoutMultiplier > 0: end-round
     → update balance → idle
```
For multi-step rounds with `auto_close_disabled=True`, send `/bet/event` with the index of
the last completed event so a reload can resume from there.

## Replay (mandatory for approval)
- Detect `replay=true`; skip authenticate/balance; fetch replay endpoint automatically.
- Show a "Play" button when loaded, play round with full animation/sound, then
  "Play again"; keep final win visible.
- Hide balance, bet button, bet selector, autoplay. Show win, replay controls, bet amount
  (from `amount`), currency, and real cost including mode multiplier.
- Must honour optional params (currency, language, amount, social).
- Reviewers replay: normal win, big win, wincap, loss, bonus trigger – for every mode.
