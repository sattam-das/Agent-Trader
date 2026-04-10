import { create } from 'zustand'

export const useStore = create((set, get) => ({
  // ── Active ticker ───────────────────────────────────────────────
  activeTicker: 'RELIANCE.NS',
  setTicker: (ticker) => set({ activeTicker: ticker.toUpperCase() }),

  // ── Navigation ──────────────────────────────────────────────────
  activeTab: 'analysis',
  setTab: (tab) => set({ activeTab: tab }),

  // ── Watchlist (fetched from backend) ────────────────────────────
  watchlist: [],
  watchlistQuotes: {},
  setWatchlist: (items) => set({ watchlist: items }),
  setWatchlistQuotes: (quotes) => set({ watchlistQuotes: quotes }),
  updateWatchlistQuote: (ticker, quote) =>
    set((s) => ({ watchlistQuotes: { ...s.watchlistQuotes, [ticker]: quote } })),

  // ── Live quote for active ticker ────────────────────────────────
  activeQuote: null,
  setActiveQuote: (q) => set({ activeQuote: q }),
}))
