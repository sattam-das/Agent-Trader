import React, { useState } from 'react'
import { fetchCompare } from '@/api'
import { useStore } from '@/store'
import { Scale, Loader2, AlertTriangle, Plus, X, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts'

export default function ComparePanel() {
  const { activeTicker } = useStore()
  const [tickers, setTickers] = useState([activeTicker])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const addTicker = () => {
    const t = input.trim().toUpperCase()
    if (t && !tickers.includes(t) && tickers.length < 5) {
      setTickers([...tickers, t])
      setInput('')
    }
  }

  const removeTicker = (t) => {
    setTickers(tickers.filter(x => x !== t))
  }

  const handleCompare = async () => {
    if (tickers.length < 1) return
    setLoading(true)
    setError(null)
    try {
      const result = await fetchCompare(tickers)
      setData(result)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const recBadge = (rec) => {
    if (rec?.includes('BUY')) return 'badge-buy'
    if (rec?.includes('SELL')) return 'badge-sell'
    if (rec === 'HOLD') return 'badge-hold'
    return 'badge-neutral'
  }

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Input Section */}
      <div className="bg-card border border-border p-4 space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2 border border-border bg-secondary text-primary flex items-center justify-center">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold font-mono uppercase text-foreground">Compare Stocks</h1>
            <p className="text-[10px] text-muted-foreground uppercase tracking-widest mt-1">Add up to 5 tickers for side-by-side AI analysis</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          {tickers.map(t => (
            <span key={t} className="flex items-center gap-1.5 px-3 py-1.5 bg-secondary text-foreground border border-border font-mono text-sm">
              {t}
              <button onClick={() => removeTicker(t)} className="hover:text-destructive transition-none">
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          {tickers.length < 5 && (
            <form onSubmit={(e) => { e.preventDefault(); addTicker() }} className="flex">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="ADD TICKER..."
                className="bg-background border border-border border-r-0 px-3 py-1.5 text-sm font-mono focus:outline-none focus:border-primary w-36 uppercase placeholder:text-muted-foreground/50"
              />
              <button type="submit" className="px-3 py-1.5 bg-secondary border border-border hover:bg-secondary/80 transition-none">
                <Plus className="w-4 h-4 text-primary" />
              </button>
            </form>
          )}
        </div>

        <button
          onClick={handleCompare}
          disabled={loading || tickers.length < 1}
          className="px-6 py-2.5 bg-primary hover:bg-primary/80 text-white font-mono text-sm uppercase transition-none disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 border border-primary w-fit"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scale className="w-4 h-4" />}
          {loading ? 'ANALYZING...' : `COMPARE ${tickers.length} STOCK${tickers.length > 1 ? 'S' : ''}`}
        </button>
      </div>

      {error && (
        <div className="p-4 border border-destructive bg-destructive/10 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-destructive shrink-0" />
          <p className="text-sm font-mono text-destructive">{error}</p>
        </div>
      )}

      {/* Results */}
      {data && data.items && (
        <div className="space-y-6 stagger-children">
          <p className="text-xs font-mono text-muted-foreground">Completed in {data.latency_ms}ms</p>

          {/* Comparison Table */}
          <div className="border border-border bg-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-secondary/50 text-muted-foreground text-xs uppercase tracking-widest">
                    <th className="text-left px-4 py-3 font-bold">Ticker</th>
                    <th className="text-left px-4 py-3 font-bold">Company</th>
                    <th className="text-center px-4 py-3 font-bold">Verdict</th>
                    <th className="text-center px-4 py-3 font-bold">Conviction</th>
                    <th className="text-center px-4 py-3 font-bold">Confidence</th>
                    <th className="text-center px-4 py-3 font-bold">News</th>
                    <th className="text-center px-4 py-3 font-bold">Financial</th>
                    <th className="text-center px-4 py-3 font-bold">Technical</th>
                    <th className="text-center px-4 py-3 font-bold">Risk</th>
                    <th className="text-center px-4 py-3 font-bold">Macro</th>
                    <th className="text-right px-4 py-3 font-bold">Price</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item, i) => (
                    <tr key={item.ticker} className="border-t border-border/50 hover:bg-card/50 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-primary">{item.ticker}</td>
                      <td className="px-4 py-3 text-foreground/80">{item.company_name}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-0.5 border text-xs font-bold ${recBadge(item.recommendation)}`}>
                          {item.recommendation}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center font-mono text-xs">{item.conviction}</td>
                      <td className="px-4 py-3 text-center font-mono">{(item.confidence * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-center font-mono">{(item.news_score * 100).toFixed(0)}</td>
                      <td className="px-4 py-3 text-center font-mono">{(item.financial_score * 100).toFixed(0)}</td>
                      <td className="px-4 py-3 text-center font-mono">{(item.technical_score * 100).toFixed(0)}</td>
                      <td className="px-4 py-3 text-center font-mono">{(item.risk_score * 100).toFixed(0)}</td>
                      <td className="px-4 py-3 text-center font-mono">{(item.macro_score * 100).toFixed(0)}</td>
                      <td className="px-4 py-3 text-right font-mono">
                        {item.current_price ? `₹${item.current_price.toFixed(2)}` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Radar Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.items.map(item => {
              const chartData = [
                { subject: 'News', A: item.news_score * 100 },
                { subject: 'Financial', A: item.financial_score * 100 },
                { subject: 'Technical', A: item.technical_score * 100 },
                { subject: 'Macro', A: item.macro_score * 100 },
                { subject: 'Risk', A: item.risk_score * 100 },
              ]
              return (
                <div key={item.ticker} className="p-4 border border-border bg-card">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono font-bold text-primary">{item.ticker}</span>
                    <span className={`px-2 py-0.5 border text-[10px] tracking-widest font-bold ${recBadge(item.recommendation)}`}>
                      {item.recommendation}
                    </span>
                  </div>
                  <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
                        <PolarGrid stroke="#334155" />
                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#94A3B8', fontSize: 10, fontFamily: 'monospace' }} />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                        <Radar dataKey="A" stroke="#3B82F6" strokeWidth={2} fill="#3B82F6" fillOpacity={0.15} />
                        <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', color: '#fff', fontSize: 12, fontFamily: 'monospace' }} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
