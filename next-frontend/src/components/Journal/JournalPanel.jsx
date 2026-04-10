import React, { useEffect, useState } from 'react'
import { fetchJournal, addJournal, closeJournal, deleteJournal, fetchJournalStats } from '@/api'
import { useStore } from '@/store'
import { BookOpen, Loader2, AlertTriangle, Plus, X, TrendingUp, TrendingDown, Trophy, Target, Trash2 } from 'lucide-react'

export default function JournalPanel() {
  const { activeTicker } = useStore()
  const [trades, setTrades] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ALL')
  const [showForm, setShowForm] = useState(false)
  const [showClose, setShowClose] = useState(null)
  const [error, setError] = useState(null)

  // Form state
  const [form, setForm] = useState({
    ticker: activeTicker,
    side: 'LONG',
    entry_price: '',
    shares: '',
    entry_date: new Date().toISOString().split('T')[0],
    notes: '',
  })
  const [closeForm, setCloseForm] = useState({ exit_price: '', exit_date: new Date().toISOString().split('T')[0] })

  const loadData = async () => {
    setLoading(true)
    try {
      const [j, s] = await Promise.all([
        fetchJournal(filter === 'ALL' ? null : filter),
        fetchJournalStats(),
      ])
      setTrades(j)
      setStats(s)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [filter])
  useEffect(() => { setForm(f => ({ ...f, ticker: activeTicker })) }, [activeTicker])

  const handleAdd = async (e) => {
    e.preventDefault()
    try {
      await addJournal({
        ...form,
        entry_price: parseFloat(form.entry_price),
        shares: parseInt(form.shares),
      })
      setShowForm(false)
      setForm({ ticker: activeTicker, side: 'LONG', entry_price: '', shares: '', entry_date: new Date().toISOString().split('T')[0], notes: '' })
      loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleClose = async (tradeId) => {
    try {
      await closeJournal(tradeId, parseFloat(closeForm.exit_price), closeForm.exit_date)
      setShowClose(null)
      loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDelete = async (tradeId) => {
    try {
      await deleteJournal(tradeId)
      loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  const statCards = stats && stats.total_trades > 0 ? [
    { label: 'Total Trades', value: stats.total_trades, color: 'text-foreground' },
    { label: 'Win Rate', value: `${(stats.win_rate * 100).toFixed(1)}%`, color: stats.win_rate >= 0.5 ? 'text-success' : 'text-destructive' },
    { label: 'Total P&L', value: `₹${stats.total_pnl?.toLocaleString('en-IN')}`, color: stats.total_pnl >= 0 ? 'text-success' : 'text-destructive' },
    { label: 'Avg Return', value: `${(stats.avg_return * 100).toFixed(2)}%`, color: stats.avg_return >= 0 ? 'text-success' : 'text-destructive' },
    { label: 'Best Trade', value: `${(stats.best_trade * 100).toFixed(2)}%`, color: 'text-success' },
    { label: 'Worst Trade', value: `${(stats.worst_trade * 100).toFixed(2)}%`, color: 'text-destructive' },
  ] : []

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="glass-card rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/15 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Trade Journal</h1>
              <p className="text-xs text-muted-foreground">Track and analyze your trades</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex gap-1 bg-secondary/50 p-1 rounded-lg">
              {['ALL', 'OPEN', 'CLOSED'].map(f => (
                <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${filter === f ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
                  {f}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all"
            >
              <Plus className="w-4 h-4" /> New Trade
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

      {/* Stats */}
      {statCards.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 stagger-children">
          {statCards.map(s => (
            <div key={s.label} className="p-3 bg-card border border-border rounded-xl space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wider font-bold">{s.label}</p>
              <p className={`text-lg font-mono font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Add Trade Form */}
      {showForm && (
        <form onSubmit={handleAdd} className="border border-primary/30 bg-card rounded-xl p-5 space-y-4 animate-fade-in">
          <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
            <Plus className="w-4 h-4 text-primary" /> Log New Trade
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-bold uppercase">Ticker</label>
              <input value={form.ticker} onChange={(e) => setForm({ ...form, ticker: e.target.value })} className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50" required />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-bold uppercase">Side</label>
              <select value={form.side} onChange={(e) => setForm({ ...form, side: e.target.value })} className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50">
                <option value="LONG">LONG</option>
                <option value="SHORT">SHORT</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-bold uppercase">Entry Price</label>
              <input type="number" step="any" value={form.entry_price} onChange={(e) => setForm({ ...form, entry_price: e.target.value })} className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50" required />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-bold uppercase">Shares</label>
              <input type="number" value={form.shares} onChange={(e) => setForm({ ...form, shares: e.target.value })} className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50" required />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-bold uppercase">Date</label>
              <input type="date" value={form.entry_date} onChange={(e) => setForm({ ...form, entry_date: e.target.value })} className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50" required />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-bold uppercase">Notes</label>
              <input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Optional" className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="px-4 py-2 bg-success hover:bg-success/90 text-white rounded-lg text-sm font-medium transition-all">Add Trade</button>
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground rounded-lg text-sm transition-all">Cancel</button>
          </div>
        </form>
      )}

      {/* Trades Table */}
      {loading ? (
        <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 text-primary animate-spin" /></div>
      ) : trades.length > 0 ? (
        <div className="border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-secondary/50 text-muted-foreground text-xs uppercase tracking-widest">
                  <th className="text-left px-4 py-3 font-bold">Ticker</th>
                  <th className="text-center px-4 py-3 font-bold">Side</th>
                  <th className="text-right px-4 py-3 font-bold">Entry</th>
                  <th className="text-right px-4 py-3 font-bold">Exit</th>
                  <th className="text-right px-4 py-3 font-bold">Shares</th>
                  <th className="text-right px-4 py-3 font-bold">P&L</th>
                  <th className="text-right px-4 py-3 font-bold">Return</th>
                  <th className="text-center px-4 py-3 font-bold">Status</th>
                  <th className="text-center px-4 py-3 font-bold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {trades.map(t => (
                  <tr key={t.id} className="border-t border-border/50 hover:bg-card/50 transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-primary">{t.ticker}</td>
                    <td className={`px-4 py-3 text-center font-mono text-xs font-bold ${t.side === 'LONG' ? 'text-success' : 'text-destructive'}`}>{t.side}</td>
                    <td className="px-4 py-3 text-right font-mono">₹{t.entry_price}</td>
                    <td className="px-4 py-3 text-right font-mono">{t.exit_price ? `₹${t.exit_price}` : '—'}</td>
                    <td className="px-4 py-3 text-right font-mono">{t.shares}</td>
                    <td className={`px-4 py-3 text-right font-mono font-bold ${(t.pnl || 0) >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {t.pnl != null ? `₹${t.pnl.toLocaleString('en-IN')}` : '—'}
                    </td>
                    <td className={`px-4 py-3 text-right font-mono ${(t.return_pct || 0) >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {t.return_pct != null ? `${(t.return_pct * 100).toFixed(2)}%` : '—'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${t.status === 'OPEN' ? 'bg-primary/15 text-primary border border-primary/20' : 'bg-secondary text-muted-foreground border border-border'}`}>
                        {t.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        {t.status === 'OPEN' && (
                          showClose === t.id ? (
                            <div className="flex items-center gap-1">
                              <input type="number" step="any" placeholder="Exit ₹" value={closeForm.exit_price} onChange={(e) => setCloseForm({ ...closeForm, exit_price: e.target.value })} className="w-20 bg-background border border-border rounded px-2 py-1 text-xs font-mono focus:outline-none focus:border-primary/50" />
                              <button onClick={() => handleClose(t.id)} className="px-2 py-1 bg-success/20 text-success rounded text-xs hover:bg-success/30 transition-colors">✓</button>
                              <button onClick={() => setShowClose(null)} className="px-2 py-1 bg-secondary text-muted-foreground rounded text-xs hover:text-foreground transition-colors">✕</button>
                            </div>
                          ) : (
                            <button onClick={() => setShowClose(t.id)} className="px-2 py-1 text-xs text-success hover:bg-success/10 rounded transition-colors">
                              Close
                            </button>
                          )
                        )}
                        <button onClick={() => handleDelete(t.id)} className="p-1 text-muted-foreground hover:text-destructive transition-colors">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center text-muted-foreground border border-border rounded-xl border-dashed">
          <BookOpen className="w-8 h-8 mx-auto mb-3 opacity-40" />
          <p className="text-sm">No trades logged yet. Click "New Trade" to start tracking.</p>
        </div>
      )}
    </div>
  )
}
