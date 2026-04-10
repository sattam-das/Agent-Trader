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
    <aside className="w-[280px] bg-secondary/30 border-r border-border flex flex-col fixed left-0 top-[52px] bottom-0 z-10">
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-6 flex flex-col custom-scrollbar">

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
                className="flex-1 bg-background border border-border rounded px-2 py-1 text-xs font-mono focus:outline-none focus:border-primary/50"
                autoFocus
              />
              <button type="submit" className="px-2 py-1 bg-primary/20 text-primary rounded text-xs hover:bg-primary/30 transition-colors">Add</button>
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
                      className={`flex-1 flex items-center justify-between px-3 py-2 rounded-md transition-colors font-mono text-sm ${
                        activeTicker === item.ticker
                          ? 'bg-primary/20 border border-primary/30 text-foreground'
                          : 'hover:bg-card border border-transparent text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      <div className="flex flex-col items-start">
                        <span className="text-xs font-bold">{item.ticker}</span>
                        {price != null && <span className="text-[10px] text-muted-foreground">{price.toFixed(2)}</span>}
                      </div>
                      <div className={`flex items-center gap-1 text-xs ${change >= 0 ? 'text-success' : 'text-destructive'}`}>
                        {change >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3"/>}
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
                className={`text-xs font-mono px-2 py-1 bg-card border transition-all rounded ${activeTicker === ticker ? 'border-primary text-primary' : 'border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'}`}
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
