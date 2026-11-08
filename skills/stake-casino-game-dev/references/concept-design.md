# Concept design: depth, many modes, engagement

Moved out of SKILL.md (it is section 7 there; subsection numbers 7.1 to 7.6 are unchanged). Read it in Phase 1 (concept) before any math or art.

## 7. Concept design: depth, many modes, engagement

The goal is a game players want to come back to because it is *rich*, not because it pressures
them. On Stake Engine every round is independent, so nothing can persist between rounds (no XP,
collections, saved meters, missions, streak rewards). Depth and retention therefore have to be
built from five things: a layered mechanic, a varied mode set, tension inside each round,
strong identity (art, audio, fantasy), and moments worth sharing (replay links).

### 7.1 Shallow vs deep
A concept is **shallow** if a round is a single evaluation with one win type and the bonus is
"same thing, more spins". A concept is **deep** when 3 or more systems interact *inside one
round*, so that the result of one layer feeds the next and players learn to read the board.
Build the concept as a **depth stack** and state how each layer amplifies the others:

| Layer | Examples |
|---|---|
| 1. Core pay | lines, ways, cluster, scatter-pays, custom (pathways, connected regions) |
| 2. Board modifiers | tumble/cascade, mystery symbols, transforms, splitting/doubling symbols, walking or expanding wilds, grid expansion (rows unlock on wins), symbol upgrades |
| 3. Multipliers | spot multipliers that grow on repeat wins in the same cell, global multiplier rising with each cascade, multiplier symbols (state whether they add or multiply) |
| 4. In-round meter | collect symbols during the round/bonus to unlock upgrades (bigger multipliers, extra rows, sticky wilds) – resets when the round ends, so it is stateless-safe |
| 5. Bonus escalation | levels inside free spins, retriggers that add spins *and* upgrade, sticky elements that last until the bonus ends, a final "super" phase |

For every concept write: the **interaction chain** (e.g. cascade → raises spot multiplier →
multiplier also boosts the meter → meter unlocks a row → more ways → more cascades), the
**common round** feel, the **typical bonus** feel, and the **dream path** to wincap. If you can't
describe a dream path that uses 3 or more layers, the concept is too shallow – add a layer or
make two layers interact.

Keep it readable: every layer must be visible on screen (meter UI, multiplier labels on
cells), explainable in one rules paragraph with an example, and legible in the 400×225 popout.
As a rule of thumb: at most 3 layers active in the base game and up to 5 in the bonus.
Complexity costs math effort (more events, more distribution tuning), so scope it accordingly.

### 7.2 Mode ladder (design all modes up front – none can be added after approval)
Each mode must make a **different promise** to the player, not just change the numbers. A
typical ladder:

| Mode | Cost | Promise | Notes |
|---|---|---|---|
| BASE | 1x | Full mechanic, frequent small wins, bonus about 1 in 150–400 spins | Sets the RTP anchor |
| BOOST / ANTE | 1.25–2x | Higher bonus chance or a guaranteed special symbol each spin | `is_feature=True`; ≤2x avoids the confirmation dialog |
| BONUS | ~80–150x | Straight into the standard bonus | `is_buybonus=True`, confirmation needed |
| SUPER BONUS | ~300–600x | Bonus that starts upgraded (starting multiplier, sticky wilds, meter pre-filled, extra row) | Distinct visuals/music |
| Alt-volatility (optional) | 1x or more | Same mechanic, sharper or smoother distribution | Only if the experience truly differs |

Constraints: every mode within 0.5% RTP of the others; each has its own wincap, its own
distributions and its own events; each needs a one-sentence description, cost and max win in
the rules; 3–5 modes is usually the sweet spot. The price of a buy mode is roughly the expected
bonus value divided by the target RTP – tune the distributions so the price stays a clean number.
Player "choices" (e.g. pick volatile vs steady free spins) are best offered as separate modes
chosen *before* the round: a mid-round choice cannot change a pre-computed outcome, and
presenting a choice that doesn't matter is misleading.

### 7.3 Engagement levers to use
- **Rhythm through the math.** Shape the distribution, not just the RTP: a base hit-rate around
  1 in 3–5; smooth win ranges with no gaps; a bonus frequency that lets a typical session see a
  bonus. Check this with `P(≥1 bonus in N spins) = 1 − (1 − p)^N`; aim for roughly 40–60% at
  N = 150 for medium volatility. Include mid-size wins so the experience isn't only dust or jackpot.
- **Anticipation and tension:** staggered reveals, reel slowdowns and music builds. Trigger them
  only from real book data (`anticipation`, scatter counts), so the tension is honest.
- **Escalation inside the round:** meters filling, multipliers climbing, rows unlocking, a final
  phase – a visible arc of build-up → peak → release in every bonus.
- **Mastery and readability:** players can always see *why* they won (highlighted positions,
  chain counters, the multiplier math shown). Rules include worked examples.
- **Discovery:** rare but real events (special transforms, a unique max-win sequence) that exist
  in the books, with visual moments that are distinct for each tier.
- **Mode variety** as the main long-term draw: each mode feels like a different game in the
  same world.
- **Identity:** a coherent fantasy, signature symbol animations and an audio motif; the bonus has
  its own scene.
- **Shareability:** big-win and wincap screens designed to look great in replay links.
- **Respect the player's time:** turbo mode, skippable celebrations, fast load.

### 7.4 Responsible-design check (also protects approval)
Don't design or implement these, and flag them if the user asks:
- **Losses disguised as wins:** no celebration for payouts smaller than the stake. Show them
  neutrally. Full celebration screens only from Big Win upward (§8); wins between the stake and
  Big Win get a position highlight and a HUD roll-up only.
- **Fabricated near-misses:** the frontend must never invent near-misses that aren't in the book,
  and the math must not inflate near-miss boards beyond what the mechanic naturally produces.
- Pressure tactics: countdown timers, "win it back" prompts after losses, nudges to buy a bonus
  after a dry streak, one-click autoplay, hidden or hard-to-find costs and RTP.
- Anything appealing to minors, and fake persistence ("you're close to unlocking…") – which is
  also impossible in a stateless system.
Retention here should come from quality and variety. Reviewers rate polish and originality, and
manipulative patterns put both approval and players at risk.

### 7.5 Ideation process
1. Generate **3 concepts with different depth signatures** (e.g. cascade + spot multipliers;
   grid expansion + collection meter; walking wilds + transforms), each with a theme that
   explains the mechanic (the fantasy should make the rules intuitive).
2. Score each from 1 to 5 on: depth (layer interaction), readability, originality vs existing
   slots, math feasibility, mobile/popout legibility, art/animation cost, and mode-ladder
   potential. Recommend one and say why.
3. Expand the chosen concept into the concept doc below.

### 7.6 Concept doc template
```
# <Title> – <fantasy in one line>
Core loop (1 sentence):
Grid / pay type:
Depth stack: layer | mechanic | feeds into
Interaction chain + dream path to wincap:
Base round feel / bonus feel / super bonus feel:
Modes: name | cost | promise | changes vs base | RTP target | wincap | is_feature / is_buybonus
Round archetypes + target frequency per mode:
  dead spin, small win (< stake, neutral), win ≥ stake, chain/cascade, bonus trigger, big bonus, wincap
Math targets: hit-rate, bonus 1-in-X per mode, P(bonus in 150 spins), RTP split base/free, volatility
Engagement beats: anticipation → escalation → peak → release (per mode)
Book events needed (standard + custom):
Rules text outline incl. worked example:
Responsible-design check (7.4): pass / issues
Risks + scope (math effort, readability at 400×225, asset count):
```
