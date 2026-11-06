/**
 * Book event player + round controller. Renderer-agnostic: register one async handler
 * per book event type; the player awaits each in order. Same code path is used for live
 * play, resume-after-reload and replay, so all three behave identically.
 */
import {
  RgsClient, RgsError, parseLaunchParams, loadBet, saveBet, winAmount,
  type AuthConfig, type BookEvent, type Round,
} from './rgs-client';

export type Handler = (ev: BookEvent, ctx: PlayContext) => Promise<void> | void;
export type PlayContext = { betRaw: number; mode: string; turbo: boolean; replay: boolean };

export class BookPlayer {
  private handlers = new Map<string, Handler>();
  on(type: string, h: Handler) { this.handlers.set(type, h); return this; }

  async play(events: BookEvent[], ctx: PlayContext, fromIndex = 0, onProgress?: (i: number) => void) {
    for (let i = fromIndex; i < events.length; i++) {
      const ev = events[i];
      const h = this.handlers.get(ev.type);
      if (h) await h(ev, ctx);
      else if (import.meta.env?.DEV) console.warn('No handler for book event', ev.type, ev);
      onProgress?.(i);
    }
  }
}

/** UI hooks your HUD implements (Svelte stores, DOM, Pixi or Three.js HUD...). */
export interface GameUI {
  setBalance(raw: number): void;
  setBet(raw: number, levels: number[]): void;
  setWin(raw: number): void;           // final win display
  setBusy(busy: boolean): void;        // disable bet controls while spinning
  showError(code: string): void;       // map via RGS_ERRORS / RGS_ERRORS_SOCIAL
  showReplayControls(onPlay: () => void): void;
}

export class GameController {
  params = parseLaunchParams();
  rgs = new RgsClient(this.params);
  config!: AuthConfig;
  bet = 0;
  mode = 'base';
  turbo = false;
  private spinning = false;

  constructor(private player: BookPlayer, private ui: GameUI) {}

  async start() {
    if (this.params.replay) return this.startReplay();
    const auth = await this.rgs.authenticate();
    this.config = auth.config;
    this.bet = loadBet(this.params.currency, this.config);
    this.ui.setBalance(auth.balance.amount);
    this.ui.setBet(this.bet, this.config.betLevels);
    // resume an unfinished round (e.g. reload mid-spin)
    if (auth.round && auth.round.active !== false && auth.round.state?.length) {
      await this.finishRound(auth.round, (auth.round.amount as number) ?? this.bet);
    }
    this.bindSpacebar();
  }

  setBet(raw: number) {
    if (!this.config.betLevels.includes(raw)) return;
    this.bet = raw;
    saveBet(this.params.currency, this.config, raw);
    this.ui.setBet(raw, this.config.betLevels);
  }

  /** Call only after any >2x mode confirmation dialog has been accepted. */
  async spin() {
    if (this.spinning) return;
    this.spinning = true;
    this.ui.setBusy(true);
    try {
      const res = await this.rgs.play(this.bet, this.mode);
      this.ui.setBalance(res.balance.amount);
      await this.finishRound(res.round, this.bet);
    } catch (e) {
      this.ui.showError(e instanceof RgsError ? e.code : 'ERR_GEN');
    } finally {
      this.spinning = false;
      this.ui.setBusy(false);
    }
  }

  private async finishRound(round: Round, betRaw: number) {
    await this.player.play(round.state, { betRaw, mode: this.mode, turbo: this.turbo, replay: false });
    const win = winAmount(betRaw, round.payoutMultiplier);
    this.ui.setWin(win);
    if (round.payoutMultiplier > 0) {
      const end = await this.rgs.endRound();
      this.ui.setBalance(end.balance.amount);
    }
  }

  private async startReplay() {
    const round = await this.rgs.replay(); // auto-load
    const betRaw = this.params.amount ?? 1_000_000;
    const run = async () => {
      this.ui.setWin(0);
      await this.player.play(round.state, { betRaw, mode: this.params.mode ?? 'base', turbo: false, replay: true });
      this.ui.setWin(winAmount(betRaw, round.payoutMultiplier));
      this.ui.showReplayControls(run); // "Play again"
    };
    this.ui.showReplayControls(run);   // "Play"
  }

  private bindSpacebar() {
    window.addEventListener('keydown', (e) => {
      if (e.code !== 'Space' || e.repeat) return;
      const t = e.target as HTMLElement;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.closest('[role=dialog]'))) return;
      e.preventDefault();
      this.spin();
    });
  }
}
