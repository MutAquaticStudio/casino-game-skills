---
name: "casino-audio-design"
description: "Design and implement audio for casino/slot games: base/bonus music, reel and win SFX, Big Win-and-above stings and roll-ups, anticipation, mixing/loudness, Web Audio/Howler implementation, composer briefs and audio QA."
---

# Casino audio design

Audio carries much of how a slot "feels": the weight of a reel stop, the tension of
anticipation, the payoff of a big win. It is heard thousands of times, so it must satisfy
without fatiguing. Answer in the user's language.

Stake Engine constraints: unique audio (no Web SDK sample sounds); a mute toggle is required;
all assets ship inside the static build (no external URLs); no sound before the first user
gesture (autoplay policy). **Celebration stings only for Big Win and above** (`winLevel` ≥ 5);
smaller wins get short win sounds, and wins below the stake get at most a soft tick.

## 1. Audio direction (write first)
Theme and instrument palette (e.g. "Ancient Viet: đàn tranh, sáo trúc, taiko, warm pads"),
tempo/key for base and bonus (bonus faster or a fourth/fifth up), a **signature motif**
(3–5 notes reused in music, trigger sting and Max Win), mix priorities (big wins > features >
anticipation > reels > music > ambience).

## 2. Asset list
| Group | Assets | Notes |
|---|---|---|
| Music | base loop (60–120s, seamless), bonus loop, super-bonus loop (if the mode exists), bonus intro/outro stingers | Sample-accurate loop points; stems if adaptive |
| Reels | spin start, subtle spin loop, reel stop ×5–6 variations, last-reel stop, quick-stop | Round-robin variations |
| Anticipation | riser/loop per reel (pitch up per extra scatter), scatter land 1/2/3 rising | Only when the book has `anticipation` |
| Small wins | soft tick (< stake), short win ping (1–5x), line/cluster highlight ticks, HUD roll-up tick | Short, musical, no fanfare |
| Win celebrations | **Big / Mega / Epic / Legendary / Max Win** stings, celebration roll-up loop, end "ka-ching" | Only ≥ Big Win; each tier adds a layer; Max Win uses the motif |
| Features | feature trigger, free spins awarded, retrigger, multiplier up (stepped pitch), meter level-up, tumble drop, wild expand, transform | Pitch-step on chains = escalation |
| Bonus flow | intro transition, bonus summary, return to base | Crossfade music |
| UI | click, hover (desktop), bet up/down (pitch follows value), toggle, modal open/close, soft error | Quiet and crisp |
| Ambience | optional low world bed | Very low |

## 3. Design rules
- **Variation:** 3–6 variants for frequent sounds; random pitch ±2–3%, small volume jitter.
- **Escalation:** cascades, multipliers and scatter lands step up per step (cap ~6); during a
  celebration the stings chain Big → Mega → Epic as the number crosses thresholds.
- **Proportion:** intensity matches win size; no fanfare under Big Win.
- **Musical coherence:** stings and wins in the music's key or neutral percussion; quantize big
  stings to the beat when possible.
- **Ducking:** music ducks 4–8 dB under celebrations and triggers, recovering over ~1s.
- **Turbo/skip-aware:** short variants; skipping jumps to the end sting.
- **Honest anticipation:** only when the round data contains it.

## 4. Technical specs
- `.webm` (Opus) + `.mp3`/`.m4a` fallback; 44.1/48 kHz; music ~96–128 kbps, SFX ~64–96 kbps;
  mono SFX, stereo music and big stings.
- Loudness ~−16 to −14 LUFS integrated, true peak ≤ −1 dBTP; a mix table for relative levels.
- Budget < 3–5 MB at first load; lazy-load bonus music and big stings; audio sprites for short SFX.
- Naming: `sfx_reel_stop_01.webm`, `mus_base_loop.webm`, `sting_win_mega.webm`.

## 5. Implementation (Web)
- Howler.js (sprites, fallbacks), `@pixi/sound` (Pixi), or raw Web Audio for sample-accurate
  loops and stems.
- `AudioManager` with buses (master, music, sfx, ui), random-variant `play`, `duck`, `crossfade`.
- Unlock the AudioContext on the first pointer/key event; persist mute (localStorage in try/catch).
- Suspend on `visibilitychange` and mute; resume cleanly.
- Trigger sounds from the same book-event handlers/timelines as the visuals (e.g. GSAP timeline
  calls `audio.play('reel_stop')` at each stop) so sync survives turbo and skip. Choose the
  celebration sting from the book's `winLevel` (≥ 5 only).
- Mobile: ~16–24 voices max, preload before spins, note iOS silent switch.
- Replay: full audio, starting after the user presses Play.

```ts
import { Howl, Howler } from 'howler';
const sfx = new Howl({ src: ['audio/sfx.webm', 'audio/sfx.mp3'], sprite: SPRITE_MAP });
const music: Record<string, Howl> = {
  base: new Howl({ src: ['audio/mus_base.webm', 'audio/mus_base.mp3'], loop: true, volume: 0.5 }),
  bonus: new Howl({ src: ['audio/mus_bonus.webm', 'audio/mus_bonus.mp3'], loop: true, volume: 0 }),
};
const TIER_STING: Record<number, string> = { 5: 'sting_big', 6: 'sting_mega', 7: 'sting_epic', 8: 'sting_legendary', 9: 'sting_legendary', 10: 'sting_max' };
export const audio = {
  play(id: string, variants = 1) {
    const n = variants > 1 ? `${id}_${1 + Math.floor(Math.random() * variants)}` : id;
    const h = sfx.play(n); sfx.rate(0.97 + Math.random() * 0.06, h);
  },
  win(winLevel: number) {               // celebration stings only from Big Win
    if (winLevel >= 5) { audio.duck(); audio.play(TIER_STING[winLevel]); }
    else if (winLevel >= 3) audio.play('sfx_win_small', 3);
    else if (winLevel >= 1) audio.play('sfx_tick');
  },
  crossfade(from: string, to: string, ms = 1000) {
    music[to].play(); music[to].fade(0, 0.5, ms); music[from].fade(music[from].volume(), 0, ms);
  },
  duck(ms = 1500) { const m = Object.values(music).find(h => h.playing()); m?.fade(0.5, 0.2, 150); setTimeout(() => m?.fade(0.2, 0.5, 800), ms); },
  mute(on: boolean) { Howler.mute(on); try { localStorage.setItem('mute', String(on)); } catch {} },
};
document.addEventListener('visibilitychange', () => {
  let muted = false; try { muted = localStorage.getItem('mute') === 'true'; } catch {}
  Howler.mute(document.hidden || muted);
});
```

## 6. Briefing a composer / sound designer
Provide the direction doc, the asset list with durations and loop/sync notes, reference tracks
(describe qualities, not "make it like X"), a gameplay video with timestamps, loudness/format
specs, and the book event → sound map. Ask for music stems and dry + processed key stings.
Ensure the licence covers commercial online-gambling use (exclusive if possible).

## 7. Audio QA checklist
- [ ] Mute works everywhere (modals, replay) and persists
- [ ] No sound before the first interaction; no console errors
- [ ] No clipping; loudness on target; consistent across devices/headphones
- [ ] Seamless loops; crossfades base ↔ bonus; nothing cuts abruptly
- [ ] Every visual book event has its sound, in sync (≤ ~50 ms)
- [ ] Celebration stings only for Big Win and above, chaining correctly; roll-up loop stops on the final amount
- [ ] Wins below the stake are not celebrated
- [ ] Turbo/skip leaves no hanging loops or stacked sounds
- [ ] Hidden tab suspends audio; return resumes
- [ ] Still pleasant after 200 spins (fatigue test)
- [ ] All audio original/licensed; no Web SDK sample sounds