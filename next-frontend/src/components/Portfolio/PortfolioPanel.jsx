import React, { useEffect, useState } from 'react'
import { fetchPortfolio, addPortfolio, removePortfolio, fetchQuote } from '@/api'
import { useStore } from '@/store'
import { Briefcase, Loader2, AlertTriangle, Plus, Trash2, TrendingUp, TrendingDown, RefreshCw, PieChart } from 'lucide-react'

export default function PortfolioPanel() {
  const { activeTicker, setTicker, setTab } = useStore()
  const [holdings, setHoldings] = useState([])
  const [quotes, setQuotes] = useState({})
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  const [form, setForm] = useState({
    ticker: activeTicker,
    shares: '',
    avg_price: '',
    notes: '',
  })

  const loadData = async () => {
    setLoading(true)
    try {
      const h = await fetchPortfolio()
      setHoldings(h)
      // Fetch quotes for all holdings
      const quotePromises = h.map(async (holding) => {
        try {
          const q = await fetchQuote(holding.ticker)
          return [holding.ticker, q]
        } catch {
          return [holding.ticker, null]
        }
      })
      const quoteResults = await Promise.allSettled(quotePromises)
      const newQuotes = {}
      quoteResults.forEach(r => {
        if (r.status === 'fulfilled' && r.value[1]) {
          newQuotes[r.value[0]] = r.value[1]
        }
      })
      setQuotes(newQuotes)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])
  useEffect(() => { setForm(f => ({ ...f, ticker: activeTicker })) }, [activeTicker])

  const refreshQuotes = async () => {
    setRefreshing(true)
    const quotePromises = holdings.map(async (h) => {
      try {
        const q = await fetchQuote(h.ticker)
        return [h.ticker, q]
      } catch {
        return [h.ticker, null]
      }
    })
    const results = await Promise.allSettled(quotePromises)
    const newQuotes = {}
    results.forEach(r => {
      if (r.status === 'fulfilled' && r.value[1]) {
        newQuotes[r.value[0]] = r.value[1]
      }
    })
    setQuotes(newQuotes)
    setRefreshing(false)
  }

  const handleAdd = async (e) => {
    e.preventDefault()
    try {
      await addPortfolio({
        ticker: form.ticker.toUpperCase(),
        shares: parseFloat(form.shares),
        avg_price: parseFloat(form.avg_price),
        notes: form.notes,
      })
      setShowForm(false)
      setForm({ ticker: activeTicker, shares: '', avg_price: '', notes: '' })
      loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleRemove = async (id) => {
    try {
      await removePortfolio(id)
      loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  // Calculate totals
  const enriched = holdings.map(h => {
    const q = quotes[h.ticker]
    const currentPrice = q?.price || null
    const invested = h.shares * h.avg_price
    const currentValue = currentPrice ? h.shares * currentPrice : null
    const pnl = currentValue ? currentValue - invested : null
    const pnlPct = pnl != null ? pnl / invested : null
    return { ...h, currentPrice, invested, currentValue, pnl, pnlPct, changePct: q?.change_pct || 0 }
  })

  const totalInvested = enriched.reduce((s, h) => s + h.invested, 0)
  const totalValue = enriched.reduce((s, h) => s + (h.currentValue || h.invested), 0)
  const totalPnl = totalValue - totalInvested
  const totalReturn = totalInvested > 0 ? totalPnl / totalInvested : 0

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="glass-card rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/15 flex items-center justify-center">
              <Briefcase className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Portfolio</h1>
              <p className="text-xs text-muted-foreground">Track your holdings with live prices</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={refreshQuotes}
              disabled={refreshing}
              className="px-3 py-2 bg-secondary hover:bg-secondary/80 rounded-lg text-sm flex items-center gap-1.5 transition-all text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all"
            >
              <Plus className="w-4 h-4" /> Add Holding
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 border border-destructive/50 bg-destructive/10 rounded-xl flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-destructive" />
          <p className="text-sm font-mono text-destructive/80">{error}</p>
        </div>
      )}

      {/* Summary Cards */}
      {holdings.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 stagger-children">
          <div className="p-4 bg-card border border-border rounded-xl space-y-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-bold">Total Invested</p>
            <p className="text-xl font-mono font-bold text-foreground">₹{totalInvested.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
          </div>
          <div className="p-4 bg-card border border-border rounded-xl space-y-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-bold">Current Value</p>
            <p className="text-xl font-mono font-bold text-primary">₹{totalValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
          </div>
          <div className="p-4 bg-card border border-border rounded-xl space-y-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-bold">Total P&L</p>
            <p className={`text-xl font-mono font-bold ${totalPnl >= 0 ? 'text-success' : 'text-destructive'}`}>
              {totalPnl >= 0 ? '+' : ''}₹{totalPnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div className="p-4 bg-card border border-border rounded-xl space-y-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-bold">Return</p>
            <p className={`text-xl font-mono font-bold flex items-center gap-1 ${totalReturn >= 0 ? 'text-success' : 'text-destructive'}`}>
              {totalReturn >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              {(totalReturn * 100).toFixed(2)}%
            </p>
          </div>
        </div>
      )}

      {/* Add Holding Form */}
      {showForm && (
        <form onSubmit={handleAdd} className="border border-primary/30 bg-card rounded-xl p-5 space-y-4 animate-fade-in">
          <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
            <Plus className="w-4 h-4 text-primary" /> Add Holding
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-bold uppercase">Ticker</label>
              <input value={form.ticker} onChange={(e) => setForm({ ...form, ticker: e.target.value })} className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50" required />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-bold uppercase">Shares</label>
              <input type="number" step="any" value={form.shares} onChange={(e) => setForm({ ...form, shares: e.target.value })} className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50" required />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-bold uppercase">Avg Price</label>
              <input type="number" step="any" value={form.avg_price} onChange={(e) => setForm({ ...form, avg_price: e.target.value })} className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50" required />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-bold uppercase">Notes</label>
              <input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Optional" className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg text-sm font-medium transition-all">Add</button>
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground rounded-lg text-sm transition-all">Cancel</button>
          </div>
        </form>
      )}

      {/* Holdings Table */}
      {loading ? (
        <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 text-primary animate-spin" /></div>
      ) : enriched.length > 0 ? (
        <div className="border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-secondary/50 text-muted-foreground text-xs uppercase tracking-widest">
                  <th className="text-left px-4 py-3 font-bold">Ticker</th>
                  <th className="text-right px-4 py-3 font-bold">Shares</th>
                  <th className="text-right px-4 py-3 font-bold">Avg Price</th>
                  <th className="text-right px-4 py-3 font-bold">Current</th>
                  <th className="text-right px-4 py-3 font-bold">Day Chg</th>
                  <th className="text-right px-4 py-3 font-bold">Invested</th>
                  <th className="text-right px-4 py-3 font-bold">Value</th>
                  <th className="text-right px-4 py-3 font-bold">P&L</th>
                  <th className="text-right px-4 py-3 font-bold">Return</th>
                  <th className="text-center px-4 py-3 font-bold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {enriched.map(h => (
                  <tr key={h.id} className="border-t border-border/50 hover:bg-card/50 transition-colors">
                    <td className="px-4 py-3">
                      <button onClick={() => { setTicker(h.ticker); setTab('analysis') }} className="font-mono font-bold text-primary hover:underline">
                        {h.ticker}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right font-mono">{h.shares}</td>
                    <td className="px-4 py-3 text-right font-mono">₹{h.avg_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right font-mono">{h.currentPrice ? `₹${h.currentPrice.toFixed(2)}` : '—'}</td>
                    <td className={`px-4 py-3 text-right font-mono ${h.changePct >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {h.changePct ? `${h.changePct.toFixed(2)}%` : '—'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-muted-foreground">₹{h.invested.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                    <td className="px-4 py-3 text-right font-mono">{h.currentValue ? `₹${h.currentValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—'}</td>
                    <td className={`px-4 py-3 text-right font-mono font-bold ${(h.pnl || 0) >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {h.pnl != null ? `${h.pnl >= 0 ? '+' : ''}₹${h.pnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—'}
                    </td>
                    <td className={`px-4 py-3 text-right font-mono ${(h.pnlPct || 0) >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {h.pnlPct != null ? `${(h.pnlPct * 100).toFixed(2)}%` : '—'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button onClick={() => handleRemove(h.id)} className="p-1 text-muted-foreground hover:text-destructive transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center text-muted-foreground border border-border rounded-xl border-dashed">
          <Briefcase className="w-8 h-8 mx-auto mb-3 opacity-40" />
          <p className="text-sm">No holdings yet. Click "Add Holding" to start building your portfolio.</p>
        </div>
      )}
    </div>
  )
}
