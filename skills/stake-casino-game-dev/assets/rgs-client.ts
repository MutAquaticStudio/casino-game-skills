/**
 * Minimal, dependency-free Stake Engine RGS client (TypeScript).
 * Works with any renderer (PixiJS, Three.js, Phaser...). Mirrors the official
 * web-sdk `rgs-requests` package endpoints.
 *
 * Money: the RGS uses integers with 6 decimals (1_000_000 = 1.00). Keep amounts as
 * integers internally; convert only for display.
 */

export const API_AMOUNT_MULTIPLIER = 1_000_000;

export type LaunchParams = {
  sessionID: string;
  rgsUrl: string; // full https base
  lang: string;
  currency: string;
  device: 'desktop' | 'mobile';
  social: boolean;
  demo: boolean;
  replay: boolean;
  // replay-only
  game?: string;
  version?: string;
  mode?: string;
  event?: string;
  amount?: number; // raw units (integer, 6 decimals)
};

export function parseLaunchParams(search = window.location.search): LaunchParams {
  const q = new URLSearchParams(search);
  const host = q.get('rgs_url') ?? '';
  const rgsUrl = /^https?:\/\//.test(host) ? host : `https://${host}`;
  const amount = q.get('amount');
  return {
    sessionID: q.get('sessionID') ?? '',
    rgsUrl: rgsUrl.replace(/\/$/, ''),
    lang: q.get('lang') ?? 'en',
    currency: q.get('currency') ?? 'USD',
    device: q.get('device') === 'mobile' ? 'mobile' : 'desktop',
    social: q.get('social') === 'true',
    demo: q.get('demo') === 'true',
    replay: q.get('replay') === 'true',
    game: q.get('game') ?? undefined,
    version: q.get('version') ?? undefined,
    mode: q.get('mode') ?? undefined,
    event: q.get('event') ?? undefined,
    amount: amount ? Number(amount) : undefined,
  };
}

export type Balance = { amount: number; currency: string };
export type BookEvent = { index?: number; type: string; [k: string]: unknown };
export type Round = {
  payoutMultiplier: number;
  costMultiplier: number;
  state: BookEvent[];
  active?: boolean;
  mode?: string;
  amount?: number;
  [k: string]: unknown;
};
export type AuthConfig = {
  gameID: string;
  minBet: number;
  maxBet: number;
  stepBet: number;
  defaultBetLevel: number;
  betLevels: number[];
  betModes: Record<string, unknown>;
};
export type AuthResponse = { balance: Balance; round: Round | null; config: AuthConfig };

export const RGS_ERRORS: Record<string, string> = {
  ERR_VAL: 'Invalid request.',
  ERR_IPB: 'Insufficient balance.',
  ERR_IS: 'Session expired. Please reload the game.',
  ERR_ATE: 'Authentication failed. Please reload the game.',
  ERR_GLE: 'Gambling limits exceeded.',
  ERR_LOC: 'Not available in your location.',
  ERR_GEN: 'Server error. Please try again.',
  ERR_MAINTENANCE: 'The game is under maintenance.',
};
// stake.us wording – no "bet", "money", "gambling", etc.
export const RGS_ERRORS_SOCIAL: Record<string, string> = {
  ...RGS_ERRORS,
  ERR_IPB: 'Not enough coins.',
  ERR_GLE: 'Play limits reached.',
};

export class RgsError extends Error {
  constructor(public code: string, public status: number) {
    super(code);
  }
}

export class RgsClient {
  constructor(private p: LaunchParams) {}

  private async post<T>(path: string, body: Record<string, unknown>): Promise<T> {
    const res = await fetch(`${this.p.rgsUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      // error shape isn't strictly documented: accept {code}, {error:"ERR_.."} or {error:{code}}
      const d = data as any;
      const code = d?.code ?? d?.error?.code ?? (typeof d?.error === 'string' ? d.error : 'ERR_GEN');
      throw new RgsError(code, res.status);
    }
    return data as T;
  }

  authenticate() {
    return this.post<AuthResponse>('/wallet/authenticate', {
      sessionID: this.p.sessionID,
      language: this.p.lang,
    });
  }

  balance() {
    return this.post<{ balance: Balance }>('/wallet/balance', { sessionID: this.p.sessionID });
  }

  /** amount = bet level in raw integer units (as returned in config.betLevels). */
  play(amount: number, mode: string) {
    return this.post<{ balance: Balance; round: Round }>('/wallet/play', {
      sessionID: this.p.sessionID,
      amount,
      mode,
      currency: this.p.currency,
    });
  }

  /** Only needed when round.payoutMultiplier > 0 (zero-payout rounds auto-complete). */
  endRound() {
    return this.post<{ balance: Balance }>('/wallet/end-round', { sessionID: this.p.sessionID });
  }

  /** Record progress inside a long round so a reload can resume. */
  event(eventIndex: number) {
    return this.post('/bet/event', { sessionID: this.p.sessionID, event: String(eventIndex) });
  }

  async replay(): Promise<Round> {
    const { game, version, mode, event } = this.p;
    const res = await fetch(`${this.p.rgsUrl}/bet/replay/${game}/${version}/${mode}/${event}`);
    if (!res.ok) throw new RgsError('ERR_GEN', res.status);
    return res.json();
  }
}

/* ---------- money helpers ---------- */

const CURRENCY: Record<string, { symbol: string; decimals: number; suffix?: boolean }> = {
  USD: { symbol: '$', decimals: 2 },
  CAD: { symbol: 'CA$', decimals: 2 },
  EUR: { symbol: '€', decimals: 2 },
  JPY: { symbol: '¥', decimals: 0 },
  RUB: { symbol: '₽', decimals: 2 },
  CNY: { symbol: 'CN¥', decimals: 2 },
  XGC: { symbol: 'GC', decimals: 2, suffix: true }, // Stake.us Gold Coins – no "$"
  XSC: { symbol: 'SC', decimals: 2, suffix: true }, // Stake.us Stake Cash – no "$"
  // extend from docs reference/currencies
};

export function formatMoney(raw: number, currency: string, locale = 'en'): string {
  const c = CURRENCY[currency] ?? { symbol: currency + ' ', decimals: 2 };
  const v = raw / API_AMOUNT_MULTIPLIER;
  const s = v.toLocaleString(locale, {
    minimumFractionDigits: c.decimals,
    maximumFractionDigits: c.decimals,
  });
  return c.suffix ? `${s} ${c.symbol}` : `${c.symbol}${s}`;
}

/** Win in raw units from a bet (raw) and the RGS float multiplier. */
export const winAmount = (betRaw: number, payoutMultiplier: number) =>
  Math.round(betRaw * payoutMultiplier);

/** Book amounts (winInfo.totalWin, setWin.amount...) are x100 integers of the base bet. */
export const bookAmountToRaw = (betRaw: number, bookAmount: number) =>
  Math.round((betRaw * bookAmount) / 100);

/* ---------- bet persistence (refresh mid-spin keeps bet) ---------- */

export function loadBet(currency: string, cfg: AuthConfig): number {
  try {
    const v = Number(localStorage.getItem(`bet:${cfg.gameID}:${currency}`));
    if (cfg.betLevels.includes(v)) return v;
  } catch {}
  // defaultBetLevel is an amount in raw units (e.g. 1000000 = 1.00), not an index
  return cfg.betLevels.includes(cfg.defaultBetLevel) ? cfg.defaultBetLevel : cfg.betLevels[0];
}

export function saveBet(currency: string, cfg: AuthConfig, amount: number) {
  try {
    localStorage.setItem(`bet:${cfg.gameID}:${currency}`, String(amount));
  } catch {}
}
