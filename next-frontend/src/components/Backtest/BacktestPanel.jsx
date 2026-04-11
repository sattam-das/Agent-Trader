import React, { useEffect, useState } from 'react'
import { runBacktest, runNLBacktest, fetchStrategies } from '@/api'
import { useStore } from '@/store'
import { TestTube, Loader2, AlertTriangle, Sparkles, ArrowUpRight, ArrowDownRight, Minus, Play, MessageSquare, Info } from 'lucide-react'
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

  // Normalize result fields from backend
  // Backend sends: total_return (decimal), final_capital, buy_hold_return (decimal),
  //                max_drawdown (decimal), equity_curve [{date, equity}], etc.
  const totalReturnPct = result?.total_return != null ? (result.total_return * 100) : null
  const cagrPct = result?.cagr != null ? (result.cagr * 100) : null
  const maxDrawdownPct = result?.max_drawdown != null ? (result.max_drawdown * 100) : null
  const buyHoldPct = result?.buy_hold_return != null ? (result.buy_hold_return * 100) : null
  const finalValue = result?.final_capital ?? result?.final_value ?? null
  const winRate = result?.win_rate ?? null
  const totalTrades = result?.total_trades ?? 0

  // Transform equity curve from [{date, equity}] to [{i, value}] for the chart
  const equityCurveData = result?.equity_curve
    ? result.equity_curve
        .filter((_, i) => i % Math.max(1, Math.floor(result.equity_curve.length / 500)) === 0 || i === result.equity_curve.length - 1)
        .map((point, i) => ({
          i,
          date: typeof point === 'object' ? point.date : null,
          value: typeof point === 'object' ? point.equity : point,
        }))
    : []

  // Normalize trade signals — backend sends `signals` array with {date, type, price, shares}
  const tradeSignals = result?.signals || result?.trades || []

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Config Panel */}
      <div className="bg-card border border-border p-4 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 border border-border bg-secondary text-primary flex items-center justify-center">
              <TestTube className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold font-mono uppercase text-foreground">Backtester</h1>
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest mt-1">Test strategies on <span className="text-primary font-mono">{activeTicker}</span></p>
            </div>
          </div>
          {/* Mode Toggle */}
          <div className="flex border border-border bg-secondary">
            <button onClick={() => setMode('strategy')} className={`px-4 py-2 text-xs font-mono transition-none flex items-center gap-1.5 border-r border-border last:border-r-0 ${mode === 'strategy' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
              <Play className="w-3 h-3" /> STRATEGY
            </button>
            <button onClick={() => setMode('nl')} className={`px-4 py-2 text-xs font-mono transition-none flex items-center gap-1.5 border-r border-border last:border-r-0 ${mode === 'nl' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
              <MessageSquare className="w-3 h-3" /> NL AI
            </button>
          </div>
        </div>

        {mode === 'strategy' ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Strategy</label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="w-full bg-background border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
              >
                {strategies.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Period</label>
              <div className="flex border border-border">
                {periods.map(p => (
                  <button key={p} onClick={() => setPeriod(p)} className={`flex-1 px-3 py-2 text-sm font-mono transition-none border-r border-border last:border-r-0 ${period === p ? 'bg-primary text-white' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Capital (₹)</label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                className="w-full bg-background border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
              />
            </div>
          </div>
        ) : (
          <div className="space-y-3 border-t border-border pt-4">
            <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-primary" /> Describe Your Strategy in English
            </label>
            <textarea
              value={nlPrompt}
              onChange={(e) => setNLPrompt(e.target.value)}
              rows={3}
              placeholder='e.g. "Buy when RSI drops below 30, sell when it goes above 70"'
              className="w-full bg-background border border-border px-4 py-3 text-sm font-mono focus:outline-none focus:border-primary resize-none placeholder:text-muted-foreground/50"
            />
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Period</label>
                <div className="flex border border-border">
                  {periods.map(p => (
                    <button key={p} onClick={() => setPeriod(p)} className={`flex-1 px-3 py-2 text-sm font-mono transition-none border-r border-border last:border-r-0 ${period === p ? 'bg-primary text-white' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}>
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Capital (₹)</label>
                <input type="number" value={capital} onChange={(e) => setCapital(Number(e.target.value))} className="w-full bg-background border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary" />
              </div>
            </div>
          </div>
        )}

        <button
          onClick={handleRun}
          disabled={loading || (mode === 'nl' && !nlPrompt.trim())}
          className="px-6 py-2.5 bg-primary hover:bg-primary/80 text-white font-mono text-sm uppercase transition-none disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 border border-primary w-fit"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {loading ? 'RUNNING BACKTEST...' : 'RUN BACKTEST'}
        </button>
      </div>

      {error && (
        <div className="p-4 border border-destructive bg-destructive/10 flex items-start gap-2">
          <AlertTriangle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
          <p className="text-sm font-mono text-destructive">{typeof error === 'string' ? error : JSON.stringify(error)}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* NL Parsed Strategy */}
          {result.parsed_strategy && (
            <div className="bg-card border border-border p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-bold font-mono text-foreground uppercase">AI Parsed Strategy</h3>
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
              {/* Show buy/sell conditions in detail */}
              {result.parsed_strategy.buy_conditions && (
                <div className="text-xs font-mono space-y-1 pt-2 border-t border-border/50">
                  <p className="text-muted-foreground">Buy conditions:</p>
                  {result.parsed_strategy.buy_conditions.map((c, i) => (
                    <p key={i} className="text-success/80 pl-2">• {c.left} {c.operator} {c.right}</p>
                  ))}
                  {result.parsed_strategy.sell_conditions && (
                    <>
                      <p className="text-muted-foreground mt-2">Sell conditions:</p>
                      {result.parsed_strategy.sell_conditions.map((c, i) => (
                        <p key={i} className="text-destructive/80 pl-2">• {c.left} {c.operator} {c.right}</p>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {/* No Trades Warning */}
          {totalTrades === 0 && (
            <div className="p-4 border border-amber-500/30 bg-amber-500/10 flex items-start gap-3 rounded">
              <Info className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-bold text-amber-400">No trades were generated</p>
                <p className="text-xs text-muted-foreground mt-1">
                  The strategy conditions were never met during the {period} testing period for {activeTicker}. 
                  Try relaxing the thresholds (e.g., RSI {"<"} 35 instead of {"<"} 30), using a longer period, 
                  or simplifying the conditions.
                </p>
              </div>
            </div>
          )}

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {[
              { label: 'Total Return', value: totalReturnPct != null ? `${totalReturnPct.toFixed(2)}%` : '—', color: (totalReturnPct || 0) >= 0 ? 'text-success' : 'text-destructive' },
              { label: 'CAGR', value: cagrPct != null ? `${cagrPct.toFixed(2)}%` : '—', color: (cagrPct || 0) >= 0 ? 'text-success' : 'text-destructive' },
              { label: 'Sharpe Ratio', value: result.sharpe_ratio != null ? result.sharpe_ratio.toFixed(2) : '—', color: (result.sharpe_ratio || 0) >= 1 ? 'text-success' : 'text-foreground' },
              { label: 'Max Drawdown', value: maxDrawdownPct != null ? `${maxDrawdownPct.toFixed(2)}%` : '—', color: 'text-destructive' },
              { label: 'Total Trades', value: totalTrades, color: 'text-foreground' },
              { label: 'Win Rate', value: winRate != null ? `${(winRate * 100).toFixed(1)}%` : '—', color: (winRate || 0) >= 0.5 ? 'text-success' : 'text-destructive' },
              { label: 'Final Value', value: finalValue != null ? `₹${finalValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—', color: 'text-primary' },
              { label: 'Buy & Hold', value: buyHoldPct != null ? `${buyHoldPct.toFixed(2)}%` : '—', color: (buyHoldPct || 0) >= 0 ? 'text-success' : 'text-muted-foreground' },
            ].map(m => (
              <div key={m.label} className="p-4 bg-card border border-border space-y-1">
                <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">{m.label}</p>
                <p className={`text-xl font-mono font-bold ${m.color}`}>{m.value}</p>
              </div>
            ))}
          </div>

          {/* Equity Curve */}
          {equityCurveData.length > 0 && (
            <div className="border border-border bg-card p-4">
              <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-4">Equity Curve</h3>
              <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={equityCurveData}>
                    <defs>
                      <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" tick={{ fill: '#94A3B8', fontSize: 9 }} tickFormatter={(v) => v ? v.slice(5) : ''} interval={Math.floor(equityCurveData.length / 8)} />
                    <YAxis tick={{ fill: '#94A3B8', fontSize: 10 }} tickFormatter={(v) => `₹${(v/1000).toFixed(0)}K`} />
                    <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', color: '#fff', fontFamily: 'monospace', fontSize: 12 }} formatter={(v) => [`₹${v.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, 'Portfolio']} labelFormatter={(_, payload) => payload?.[0]?.payload?.date || ''} />
                    <ReferenceLine y={capital} stroke="#94A3B8" strokeDasharray="3 3" label={{ fill: '#94A3B8', value: 'Initial', fontSize: 10 }} />
                    <Area type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} fill="url(#eqGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Trade Log */}
          {tradeSignals.length > 0 && (
            <div className="border border-border bg-card overflow-hidden">
              <div className="p-3 border-b border-border bg-secondary">
                <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Trade Log ({tradeSignals.length} signals)</h3>
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
                    </tr>
                  </thead>
                  <tbody>
                    {tradeSignals.slice(0, 100).map((t, i) => (
                      <tr key={i} className="border-t border-border/30 hover:bg-card/50">
                        <td className="px-3 py-2 text-muted-foreground">{i + 1}</td>
                        <td className={`px-3 py-2 font-bold ${t.type === 'BUY' ? 'text-success' : 'text-destructive'}`}>{t.type}</td>
                        <td className="px-3 py-2">{t.date || t.entry_date}</td>
                        <td className="px-3 py-2 text-right">₹{(t.price || t.entry_price)?.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right">{t.shares}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Completed Trades */}
          {result.trades && result.trades.length > 0 && result.trades[0].entry_date && (
            <div className="border border-border bg-card overflow-hidden">
              <div className="p-3 border-b border-border bg-secondary">
                <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Completed Trades ({result.trades.length})</h3>
              </div>
              <div className="overflow-x-auto max-h-[300px] overflow-y-auto custom-scrollbar">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="bg-secondary/50 text-muted-foreground uppercase tracking-wider">
                      <th className="text-left px-3 py-2">#</th>
                      <th className="text-left px-3 py-2">Entry</th>
                      <th className="text-left px-3 py-2">Exit</th>
                      <th className="text-right px-3 py-2">Entry ₹</th>
                      <th className="text-right px-3 py-2">Exit ₹</th>
                      <th className="text-right px-3 py-2">P&L</th>
                      <th className="text-right px-3 py-2">Return</th>
                      <th className="text-right px-3 py-2">Days</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trades.map((t, i) => (
                      <tr key={i} className="border-t border-border/30 hover:bg-card/50">
                        <td className="px-3 py-2 text-muted-foreground">{i + 1}</td>
                        <td className="px-3 py-2">{t.entry_date}</td>
                        <td className="px-3 py-2">{t.exit_date}</td>
                        <td className="px-3 py-2 text-right">₹{t.entry_price?.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right">₹{t.exit_price?.toFixed(2)}</td>
                        <td className={`px-3 py-2 text-right font-bold ${(t.pnl || 0) >= 0 ? 'text-success' : 'text-destructive'}`}>
                          {(t.pnl || 0) >= 0 ? '+' : ''}₹{t.pnl?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                        </td>
                        <td className={`px-3 py-2 text-right ${(t.return_pct || 0) >= 0 ? 'text-success' : 'text-destructive'}`}>
                          {((t.return_pct || 0) * 100).toFixed(1)}%
                        </td>
                        <td className="px-3 py-2 text-right text-muted-foreground">{t.holding_days}d</td>
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
