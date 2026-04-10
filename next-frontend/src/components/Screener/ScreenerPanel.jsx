import React, { useEffect, useState } from 'react'
import { fetchScreener, fetchScreenerPresets } from '@/api'
import { useStore } from '@/store'
import { Filter, Loader2, AlertTriangle, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react'

const FILTERS = [
  { id: 'rsi_oversold', label: 'RSI Oversold (<30)', desc: 'Potential reversal candidates' },
  { id: 'rsi_overbought', label: 'RSI Overbought (>70)', desc: 'May be due for pullback' },
  { id: 'golden_cross', label: 'Golden Cross', desc: 'SMA 50 crossed above SMA 200' },
  { id: 'death_cross', label: 'Death Cross', desc: 'SMA 50 crossed below SMA 200' },
  { id: 'volume_spike', label: 'Volume Spike', desc: 'Unusual volume activity' },
  { id: 'new_high', label: '52-Week High', desc: 'Near all-time highs' },
  { id: 'new_low', label: '52-Week Low', desc: 'Near all-time lows' },
]

export default function ScreenerPanel() {
  const { setTicker, setTab } = useStore()
  const [presets, setPresets] = useState({})
  const [selectedPreset, setSelectedPreset] = useState('nifty50')
  const [selectedFilter, setSelectedFilter] = useState('rsi_oversold')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchScreenerPresets().then(setPresets).catch(() => {})
  }, [])

  const handleScan = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchScreener(selectedPreset, selectedFilter)
      setData(result)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Config */}
      <div className="glass-card rounded-xl p-6 space-y-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-pink-500/15 flex items-center justify-center">
            <Filter className="w-5 h-5 text-pink-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Stock Screener</h1>
            <p className="text-xs text-muted-foreground">Scan markets using technical filters</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Market Preset</label>
            <div className="flex flex-wrap gap-2">
              {Object.entries(presets).map(([key, count]) => (
                <button
                  key={key}
                  onClick={() => setSelectedPreset(key)}
                  className={`px-3 py-1.5 text-xs font-mono rounded-md transition-all ${
                    selectedPreset === key
                      ? 'bg-primary text-white'
                      : 'bg-secondary text-muted-foreground hover:text-foreground border border-border'
                  }`}
                >
                  {key.replace(/_/g, ' ').toUpperCase()} ({count})
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Filter</label>
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value)}
              className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50"
            >
              {FILTERS.map(f => (
                <option key={f.id} value={f.id}>{f.label}</option>
              ))}
            </select>
            <p className="text-xs text-muted-foreground">{FILTERS.find(f => f.id === selectedFilter)?.desc}</p>
          </div>
        </div>

        <button
          onClick={handleScan}
          disabled={loading}
          className="px-6 py-2.5 bg-pink-500 hover:bg-pink-600 text-white rounded-lg font-medium text-sm transition-all disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {loading ? 'Scanning...' : 'Run Screener'}
        </button>
      </div>

      {error && (
        <div className="p-4 border border-destructive/50 bg-destructive/10 rounded-xl flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-destructive" />
          <p className="text-sm font-mono text-destructive/80">{error}</p>
        </div>
      )}

      {/* Results */}
      {data && (
        <div className="space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <p className="text-xs font-mono text-muted-foreground">
              {data.count} stocks matched · {data.preset} · {data.filter}
            </p>
          </div>

          {data.results && data.results.length > 0 ? (
            <div className="border border-border rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-secondary/50 text-muted-foreground text-xs uppercase tracking-widest">
                      <th className="text-left px-4 py-3 font-bold">Ticker</th>
                      <th className="text-right px-4 py-3 font-bold">Price</th>
                      <th className="text-right px-4 py-3 font-bold">Change %</th>
                      <th className="text-right px-4 py-3 font-bold">RSI</th>
                      <th className="text-right px-4 py-3 font-bold">Volume</th>
                      <th className="text-center px-4 py-3 font-bold">Signal</th>
                      <th className="text-center px-4 py-3 font-bold">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.results.map((r, i) => (
                      <tr key={i} className="border-t border-border/50 hover:bg-card/50 transition-colors">
                        <td className="px-4 py-3 font-mono font-bold text-primary">{r.ticker}</td>
                        <td className="px-4 py-3 text-right font-mono">
                          {r.price ? `₹${r.price.toFixed(2)}` : '—'}
                        </td>
                        <td className={`px-4 py-3 text-right font-mono flex items-center justify-end gap-1 ${
                          (r.change_pct || 0) >= 0 ? 'text-success' : 'text-destructive'
                        }`}>
                          {(r.change_pct || 0) >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {r.change_pct != null ? `${r.change_pct.toFixed(2)}%` : '—'}
                        </td>
                        <td className={`px-4 py-3 text-right font-mono ${
                          r.rsi < 30 ? 'text-success' : r.rsi > 70 ? 'text-destructive' : 'text-foreground'
                        }`}>
                          {r.rsi != null ? r.rsi.toFixed(1) : '—'}
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                          {r.volume ? (r.volume / 1e5).toFixed(1) + 'L' : '—'}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-0.5 rounded text-xs font-mono ${
                            r.signal === 'bullish' ? 'badge-buy' : r.signal === 'bearish' ? 'badge-sell' : 'badge-neutral'
                          }`}>
                            {r.signal || 'match'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={() => { setTicker(r.ticker); setTab('analysis') }}
                            className="px-2 py-1 text-xs text-primary hover:bg-primary/10 rounded transition-colors font-medium"
                          >
                            Analyze →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-muted-foreground border border-border rounded-xl">
              <Filter className="w-8 h-8 mx-auto mb-3 opacity-40" />
              <p className="text-sm">No stocks matched the current filter</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
