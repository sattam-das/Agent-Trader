import React, { useEffect, useState } from 'react'
import { Plus, TrendingUp, TrendingDown, Loader2, X, Trash2 } from 'lucide-react'
import { useStore } from '@/store'
import { fetchWatchlist, addWatchlist, removeWatchlist, fetchQuote } from '@/api'

export default function Sidebar() {
  const { activeTicker, setTicker } = useStore()
  const [watchlist, setWatchlistLocal] = useState([])
  const [quotes, setQuotes] = useState({})
  const [loading, setLoading] = useState(true)
  const [addInput, setAddInput] = useState('')
  const [showAdd, setShowAdd] = useState(false)

  const loadWatchlist = async () => {
    setLoading(true)
    try {
      const items = await fetchWatchlist()
      setWatchlistLocal(items)
      // Fetch quotes for each
      const quoteResults = await Promise.allSettled(
        items.map(async (item) => {
          const q = await fetchQuote(item.ticker)
          return [item.ticker, q]
        })
      )
      const newQuotes = {}
      quoteResults.forEach(r => {
        if (r.status === 'fulfilled' && r.value[1]) {
          newQuotes[r.value[0]] = r.value[1]
        }
      })
      setQuotes(newQuotes)
    } catch {
      // Watchlist might be empty initially, that's fine
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadWatchlist() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    const ticker = addInput.trim().toUpperCase()
    if (!ticker) return
    try {
      await addWatchlist(ticker)
      setAddInput('')
      setShowAdd(false)
      loadWatchlist()
    } catch {}
  }

  const handleRemove = async (ticker) => {
    try {
      await removeWatchlist(ticker)
      loadWatchlist()
    } catch {}
  }

  const quickAdds = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'AAPL', 'NVDA']

  return (
    <aside className="w-[280px] bg-black/40 backdrop-blur-xl border-r border-white/5 flex flex-col fixed left-0 top-[60px] bottom-0 z-10 transition-all duration-300">
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-5 space-y-6 flex flex-col custom-scrollbar">

        {/* Watchlist Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-bold uppercase tracking-widest pl-1">Watchlist</span>
            <button onClick={() => setShowAdd(!showAdd)} className="hover:text-foreground transition-colors p-1">
              <Plus className="w-3 h-3" />
            </button>
          </div>

          {showAdd && (
            <form onSubmit={handleAdd} className="flex gap-1.5 animate-fade-in">
              <input
                type="text"
                value={addInput}
                onChange={(e) => setAddInput(e.target.value)}
                placeholder="AAPL, TCS.NS..."
                className="flex-1 bg-black/50 border border-white/10 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 shadow-inner"
                autoFocus
              />
              <button type="submit" className="px-3 py-1.5 bg-primary hover:bg-primary/90 text-white rounded-lg text-xs transition-colors shadow-[0_0_10px_rgba(139,92,246,0.3)]">Add</button>
              <button type="button" onClick={() => setShowAdd(false)} className="px-1 py-1 text-muted-foreground hover:text-foreground">
                <X className="w-3 h-3" />
              </button>
            </form>
          )}

          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="w-5 h-5 text-primary/50 animate-spin" />
            </div>
          ) : (
            <div className="space-y-1">
              {watchlist.map((item) => {
                const q = quotes[item.ticker]
                const change = q?.change_pct ?? 0
                const price = q?.price

                return (
                  <div key={item.ticker} className="group flex items-center">
                    <button
                      onClick={() => setTicker(item.ticker)}
                      className={`flex-1 flex items-center justify-between px-3 py-2.5 rounded-xl transition-all duration-300 text-sm ${
                        activeTicker === item.ticker
                          ? 'bg-gradient-to-r from-primary/20 to-transparent border border-primary/30 shadow-[0_0_15px_rgba(139,92,246,0.15)] text-foreground'
                          : 'hover:bg-white/5 border border-transparent text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      <div className="flex flex-col items-start">
                        <span className="text-xs font-bold">{item.ticker}</span>
                        {price != null && <span className="text-[10px] text-muted-foreground">{price.toFixed(2)}</span>}
                      </div>
                      <div className={`flex items-center gap-1 text-xs font-bold ${change >= 0 ? 'text-success drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'text-destructive drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]'}`}>
                        {change >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5"/>}
                        <span>{Math.abs(change).toFixed(2)}%</span>
                      </div>
                    </button>
                    <button
                      onClick={() => handleRemove(item.ticker)}
                      className="p-1 text-muted-foreground/30 hover:text-destructive opacity-0 group-hover:opacity-100 transition-all ml-0.5"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                )
              })}
              {watchlist.length === 0 && !loading && (
                <p className="text-xs text-muted-foreground/60 px-3 py-2">No tickers in watchlist. Add some!</p>
              )}
            </div>
          )}
        </div>

        {/* Quick Add Presets */}
        <div className="space-y-3 pt-4 border-t border-border/50">
          <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground pl-1">Quick Add</span>
          <div className="flex flex-wrap gap-2">
            {quickAdds.map(ticker => (
              <button
                key={ticker}
                onClick={() => setTicker(ticker)}
                className={`text-[11px] font-bold px-2.5 py-1.5 transition-all duration-300 rounded-lg ${activeTicker === ticker ? 'bg-primary border-primary text-white shadow-[0_0_12px_rgba(139,92,246,0.5)]' : 'bg-black/30 border border-white/10 text-muted-foreground hover:border-primary/50 hover:text-foreground'}`}
              >
                {ticker}
              </button>
            ))}
          </div>
        </div>

      </div>
    </aside>
  )
}
