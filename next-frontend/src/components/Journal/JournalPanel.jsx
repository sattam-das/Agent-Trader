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
      <div className="bg-card border border-border p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 border border-border bg-secondary text-primary flex items-center justify-center">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground font-mono uppercase">Trade Journal</h1>
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest mt-1">Track and analyze your trades</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex border border-border bg-secondary">
              {['ALL', 'OPEN', 'CLOSED'].map(f => (
                <button key={f} onClick={() => setFilter(f)} className={`px-4 py-2 text-xs font-mono transition-none border-r border-border last:border-r-0 ${filter === f ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
                  {f}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-4 py-2 bg-primary hover:bg-primary/80 text-white text-sm font-mono flex items-center gap-1.5 transition-none uppercase border border-primary"
            >
              <Plus className="w-4 h-4" /> NEW TRADE
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 border border-destructive bg-destructive/10 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-destructive" />
          <p className="text-sm font-mono text-destructive">{error}</p>
        </div>
      )}

      {/* Stats */}
      {statCards.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {statCards.map(s => (
            <div key={s.label} className="p-3 bg-card border border-border space-y-1">
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">{s.label}</p>
              <p className={`text-lg font-mono font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Add Trade Form */}
      {showForm && (
        <form onSubmit={handleAdd} className="border border-border bg-card p-5 space-y-4">
          <h3 className="text-sm font-bold font-mono text-foreground uppercase tracking-widest flex items-center gap-2">
            <Plus className="w-4 h-4 text-primary" /> LOG NEW TRADE
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Ticker</label>
              <input value={form.ticker} onChange={(e) => setForm({ ...form, ticker: e.target.value })} className="w-full bg-background border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary" required />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Side</label>
              <select value={form.side} onChange={(e) => setForm({ ...form, side: e.target.value })} className="w-full bg-background border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary">
                <option value="LONG">LONG</option>
                <option value="SHORT">SHORT</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Entry Price</label>
              <input type="number" step="any" value={form.entry_price} onChange={(e) => setForm({ ...form, entry_price: e.target.value })} className="w-full bg-background border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary" required />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Shares</label>
              <input type="number" value={form.shares} onChange={(e) => setForm({ ...form, shares: e.target.value })} className="w-full bg-background border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary" required />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Date</label>
              <input type="date" value={form.entry_date} onChange={(e) => setForm({ ...form, entry_date: e.target.value })} className="w-full bg-background border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary" required />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Notes</label>
              <input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Optional" className="w-full bg-background border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="px-4 py-2 bg-success hover:bg-success/80 text-white font-mono text-sm transition-none border border-success">ADD TRADE</button>
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground font-mono text-sm transition-none border border-border">CANCEL</button>
          </div>
        </form>
      )}

      {/* Trades Table */}
      {loading ? (
        <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 text-primary animate-spin" /></div>
      ) : trades.length > 0 ? (
        <div className="border border-border bg-card overflow-hidden">
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
                      <span className={`px-2 py-0.5 border text-[10px] font-bold uppercase tracking-widest ${t.status === 'OPEN' ? 'bg-primary/10 text-primary border-primary' : 'bg-transparent text-muted-foreground border-border'}`}>
                        {t.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        {t.status === 'OPEN' && (
                          showClose === t.id ? (
                            <div className="flex items-center gap-1">
                              <input type="number" step="any" placeholder="Exit ₹" value={closeForm.exit_price} onChange={(e) => setCloseForm({ ...closeForm, exit_price: e.target.value })} className="w-20 bg-background border border-border px-2 py-1 text-xs font-mono focus:outline-none focus:border-primary" />
                              <button onClick={() => handleClose(t.id)} className="px-2 py-1 bg-success/10 border border-success text-success text-xs hover:bg-success/20 transition-none">✓</button>
                              <button onClick={() => setShowClose(null)} className="px-2 py-1 bg-secondary border border-border text-muted-foreground text-xs hover:text-foreground transition-none">✕</button>
                            </div>
                          ) : (
                            <button onClick={() => setShowClose(t.id)} className="px-2 py-1 text-[10px] uppercase tracking-widest font-bold border border-success text-success hover:bg-success/10 transition-none">
                              CLOSE
                            </button>
                          )
                        )}
                        <button onClick={() => handleDelete(t.id)} className="p-1 px-2 border border-transparent text-muted-foreground hover:text-destructive hover:border-destructive transition-none">
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
