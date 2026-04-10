import { create } from 'zustand'

export const useStore = create((set) => ({
  activeTicker: 'AAPL',
  setTicker: (ticker) => set({ activeTicker: ticker.toUpperCase() }),

  watchlist: [
    { ticker: 'RELIANCE.NS', price: 1350.2, change: 1.59 },
    { ticker: 'AAPL', price: 172.5, change: -0.4 },
    { ticker: 'TSLA', price: 180.1, change: 2.1 },
  ],
  setWatchlist: (items) => set({ watchlist: items }),

  activeTab: 'analysis',
  setTab: (tab) => set({ activeTab: tab }),
}))
