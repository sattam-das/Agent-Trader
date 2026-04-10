import React, { useEffect, useState } from 'react'
import { runBacktest, runNLBacktest, fetchStrategies } from '@/api'
import { useStore } from '@/store'
import { TestTube, Loader2, AlertTriangle, Sparkles, ArrowUpRight, ArrowDownRight, Minus, Play, MessageSquare } from 'lucide-react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

export default function BacktestPanel() {
  const { activeTicker } = useStore()
  const [mode, setMode] = useState('strategy')
  const [strategies, setStrategies] = useState([])
  const [selectedStrategy, setSelectedStrategy] = useState('sma_crossover')
  const [period, setPeriod] = useState('2y')
  const [capital, setCapital] = useState(100000)
  const [nlPrompt, setNLPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchStrategies().then(setStrategies).catch(() => {})
  }, [])

  const handleRun = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      let res
      if (mode === 'nl') {
        res = await runNLBacktest({
          prompt: nlPrompt,
          ticker: activeTicker,
          period,
          initial_capital: capital,
        })
      } else {
        res = await runBacktest({
          ticker: activeTicker,
          strategy: selectedStrategy,
          period,
          initial_capital: capital,
        })
      }
      setResult(res)
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.error || err.message)
    } finally {
      setLoading(false)
    }
  }

  const periods = ['1y', '2y', '5y']

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Config Panel */}
      <div className="glass-card rounded-xl p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/15 flex items-center justify-center">
              <TestTube className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Backtester</h1>
              <p className="text-xs text-muted-foreground">Test strategies on <span className="text-primary font-mono">{activeTicker}</span></p>
            </div>
          </div>
          {/* Mode Toggle */}
          <div className="flex gap-1 bg-secondary/50 p-1 rounded-lg">
            <button onClick={() => setMode('strategy')} className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${mode === 'strategy' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
              <Play className="w-3 h-3" /> Strategy
            </button>
            <button onClick={() => setMode('nl')} className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${mode === 'nl' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
              <MessageSquare className="w-3 h-3" /> Natural Language
            </button>
          </div>
        </div>

        {mode === 'strategy' ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Strategy</label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50"
              >
                {strategies.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Period</label>
              <div className="flex gap-2">
                {periods.map(p => (
                  <button key={p} onClick={() => setPeriod(p)} className={`flex-1 px-3 py-2 rounded-md text-sm font-mono transition-all ${period === p ? 'bg-primary text-white' : 'bg-secondary text-muted-foreground hover:text-foreground border border-border'}`}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Capital (₹)</label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50"
              />
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Describe Your Strategy in English
            </label>
            <textarea
              value={nlPrompt}
              onChange={(e) => setNLPrompt(e.target.value)}
              rows={3}
              placeholder='e.g. "Buy when RSI drops below 30, sell when it goes above 70" or "Golden cross strategy with 50 and 200 day SMA"'
              className="w-full bg-background border border-border rounded-lg px-4 py-3 text-sm font-mono focus:outline-none focus:border-primary/50 resize-none placeholder:text-muted-foreground/50"
            />
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Period</label>
                <div className="flex gap-2">
                  {periods.map(p => (
                    <button key={p} onClick={() => setPeriod(p)} className={`flex-1 px-3 py-2 rounded-md text-sm font-mono transition-all ${period === p ? 'bg-primary text-white' : 'bg-secondary text-muted-foreground hover:text-foreground border border-border'}`}>
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Capital (₹)</label>
                <input type="number" value={capital} onChange={(e) => setCapital(Number(e.target.value))} className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary/50" />
              </div>
            </div>
          </div>
        )}

        <button
          onClick={handleRun}
          disabled={loading || (mode === 'nl' && !nlPrompt.trim())}
          className="px-6 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {loading ? 'Running Backtest...' : 'Run Backtest'}
        </button>
      </div>

      {error && (
        <div className="p-4 border border-destructive/50 bg-destructive/10 rounded-xl flex items-start gap-2">
          <AlertTriangle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
          <p className="text-sm font-mono text-destructive/80">{typeof error === 'string' ? error : JSON.stringify(error)}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6 stagger-children">
          {/* NL Parsed Strategy */}
          {result.parsed_strategy && (
            <div className="glass-card rounded-xl p-5 space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-foreground">AI Parsed Strategy</h3>
              </div>
              <p className="text-sm text-muted-foreground">{result.parsed_strategy.description}</p>
              <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                <div>
                  <span className="text-muted-foreground">Buy: </span>
                  <span className="text-success">{result.parsed_strategy.buy_logic || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Sell: </span>
                  <span className="text-destructive">{result.parsed_strategy.sell_logic || 'N/A'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {[
              { label: 'Total Return', value: result.total_return_pct != null ? `${result.total_return_pct.toFixed(2)}%` : '—', color: (result.total_return_pct || 0) >= 0 ? 'text-success' : 'text-destructive' },
              { label: 'CAGR', value: result.cagr != null ? `${result.cagr.toFixed(2)}%` : '—', color: (result.cagr || 0) >= 0 ? 'text-success' : 'text-destructive' },
              { label: 'Sharpe Ratio', value: result.sharpe_ratio != null ? result.sharpe_ratio.toFixed(2) : '—', color: (result.sharpe_ratio || 0) >= 1 ? 'text-success' : 'text-foreground' },
              { label: 'Max Drawdown', value: result.max_drawdown_pct != null ? `${result.max_drawdown_pct.toFixed(2)}%` : '—', color: 'text-destructive' },
              { label: 'Total Trades', value: result.total_trades ?? '—', color: 'text-foreground' },
              { label: 'Win Rate', value: result.win_rate != null ? `${(result.win_rate * 100).toFixed(1)}%` : '—', color: (result.win_rate || 0) >= 0.5 ? 'text-success' : 'text-destructive' },
              { label: 'Final Value', value: result.final_value != null ? `₹${result.final_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—', color: 'text-primary' },
              { label: 'Buy & Hold', value: result.buy_hold_return_pct != null ? `${result.buy_hold_return_pct.toFixed(2)}%` : '—', color: 'text-muted-foreground' },
            ].map(m => (
              <div key={m.label} className="p-4 bg-card border border-border rounded-xl space-y-1">
                <p className="text-xs text-muted-foreground uppercase tracking-wider font-bold">{m.label}</p>
                <p className={`text-xl font-mono font-bold ${m.color}`}>{m.value}</p>
              </div>
            ))}
          </div>

          {/* Equity Curve */}
          {result.equity_curve && result.equity_curve.length > 0 && (
            <div className="border border-border bg-card rounded-xl p-6">
              <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4">Equity Curve</h3>
              <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={result.equity_curve.map((v, i) => ({ i, value: v }))}>
                    <defs>
                      <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#34C759" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#34C759" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a243d" />
                    <XAxis dataKey="i" tick={false} />
                    <YAxis tick={{ fill: '#8B95A5', fontSize: 10 }} tickFormatter={(v) => `₹${(v/1000).toFixed(0)}K`} />
                    <Tooltip contentStyle={{ backgroundColor: '#0D1322', borderColor: '#1a243d', color: '#fff', fontFamily: 'monospace', fontSize: 12 }} formatter={(v) => [`₹${v.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, 'Portfolio']} />
                    <ReferenceLine y={capital} stroke="#8B95A5" strokeDasharray="3 3" label={{ fill: '#8B95A5', value: 'Initial', fontSize: 10 }} />
                    <Area type="monotone" dataKey="value" stroke="#34C759" strokeWidth={2} fill="url(#eqGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Trade Log */}
          {result.trades && result.trades.length > 0 && (
            <div className="border border-border rounded-xl overflow-hidden">
              <div className="p-4 bg-secondary/30">
                <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Trade Log ({result.trades.length} trades)</h3>
              </div>
              <div className="overflow-x-auto max-h-[300px] overflow-y-auto custom-scrollbar">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="bg-secondary/50 text-muted-foreground uppercase tracking-wider">
                      <th className="text-left px-3 py-2">#</th>
                      <th className="text-left px-3 py-2">Type</th>
                      <th className="text-left px-3 py-2">Date</th>
                      <th className="text-right px-3 py-2">Price</th>
                      <th className="text-right px-3 py-2">Shares</th>
                      <th className="text-right px-3 py-2">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trades.slice(0, 100).map((t, i) => (
                      <tr key={i} className="border-t border-border/30 hover:bg-card/50">
                        <td className="px-3 py-2 text-muted-foreground">{i + 1}</td>
                        <td className={`px-3 py-2 font-bold ${t.type === 'BUY' ? 'text-success' : 'text-destructive'}`}>{t.type}</td>
                        <td className="px-3 py-2">{t.date}</td>
                        <td className="px-3 py-2 text-right">₹{t.price?.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right">{t.shares}</td>
                        <td className="px-3 py-2 text-right">₹{t.value?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
