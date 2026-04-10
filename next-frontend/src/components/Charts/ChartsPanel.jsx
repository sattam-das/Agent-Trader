import React, { useEffect, useState } from 'react'
import { fetchIndicators } from '@/api'
import { useStore } from '@/store'
import { LineChart as LineChartIcon, Loader2, AlertTriangle } from 'lucide-react'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts'

export default function ChartsPanel() {
  const { activeTicker } = useStore()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [chartType, setChartType] = useState('price')

  useEffect(() => {
    let active = true
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const result = await fetchIndicators(activeTicker)
        if (active) setData(result)
      } catch (err) {
        if (active) setError(err.response?.data?.detail || err.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [activeTicker])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-32 space-y-4 animate-fade-in">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
        <p className="text-sm text-muted-foreground font-mono">Loading chart data for {activeTicker}...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 border border-destructive/50 bg-destructive/10 rounded-xl space-y-2 max-w-2xl mx-auto mt-12 animate-fade-in">
        <div className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="w-5 h-5" />
          <h3 className="font-bold">Chart Data Error</h3>
        </div>
        <p className="text-sm font-mono text-destructive/80">{error}</p>
      </div>
    )
  }

  if (!data) return null

  const priceData = (data.price_history || []).map((p, i) => ({
    idx: i,
    date: p.date ? new Date(p.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }) : i,
    close: p.close,
    open: p.open,
    high: p.high,
    low: p.low,
    volume: p.volume,
  }))

  // Only show last 120 points for readability
  const displayData = priceData.slice(-120)
  const indicators = data.indicators || {}

  const TABS = [
    { id: 'price', label: 'Price' },
    { id: 'volume', label: 'Volume' },
    { id: 'indicators', label: 'Indicators' },
  ]

  const formatK = (v) => {
    if (v >= 1e7) return `${(v/1e7).toFixed(1)}Cr`
    if (v >= 1e5) return `${(v/1e5).toFixed(1)}L`
    if (v >= 1e3) return `${(v/1e3).toFixed(1)}K`
    return v
  }

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="glass-card rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/15 flex items-center justify-center">
              <LineChartIcon className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">{activeTicker} Charts</h1>
              <p className="text-xs text-muted-foreground font-mono">{displayData.length} data points</p>
            </div>
          </div>

          <div className="flex gap-1 bg-secondary/50 p-1 rounded-lg">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setChartType(tab.id)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  chartType === tab.id ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Price Chart */}
      {chartType === 'price' && (
        <div className="border border-border bg-card rounded-xl p-6">
          <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4">Price History</h3>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={displayData}>
                <defs>
                  <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0066FF" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#0066FF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a243d" />
                <XAxis dataKey="date" tick={{ fill: '#8B95A5', fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fill: '#8B95A5', fontSize: 10 }} domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0D1322', borderColor: '#1a243d', color: '#fff', fontFamily: 'monospace', fontSize: 12 }}
                  formatter={(v) => [typeof v === 'number' ? v.toFixed(2) : v]}
                />
                <Area type="monotone" dataKey="close" stroke="#0066FF" strokeWidth={2} fill="url(#priceGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Volume Chart */}
      {chartType === 'volume' && (
        <div className="border border-border bg-card rounded-xl p-6">
          <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4">Volume</h3>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={displayData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a243d" />
                <XAxis dataKey="date" tick={{ fill: '#8B95A5', fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fill: '#8B95A5', fontSize: 10 }} tickFormatter={formatK} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0D1322', borderColor: '#1a243d', color: '#fff', fontFamily: 'monospace', fontSize: 12 }}
                  formatter={(v) => [formatK(v), 'Volume']}
                />
                <Bar dataKey="volume" fill="#0066FF" fillOpacity={0.6} radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Indicators Summary */}
      {chartType === 'indicators' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 stagger-children">
            {Object.entries(indicators).map(([key, value]) => {
              if (typeof value === 'object' && value !== null) return null
              const numVal = typeof value === 'number' ? value : null
              return (
                <div key={key} className="p-4 border border-border bg-card rounded-xl space-y-1">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider font-bold">
                    {key.replace(/_/g, ' ')}
                  </p>
                  <p className="text-xl font-mono font-bold text-foreground">
                    {numVal !== null ? numVal.toFixed(2) : String(value)}
                  </p>
                </div>
              )
            })}
          </div>

          {/* RSI Chart if available */}
          {indicators.rsi_14 !== undefined && (
            <div className="border border-border bg-card rounded-xl p-6">
              <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">RSI (14)</h3>
              <div className="flex items-center gap-4">
                <div className={`text-3xl font-mono font-bold ${
                  indicators.rsi_14 > 70 ? 'text-destructive' : indicators.rsi_14 < 30 ? 'text-success' : 'text-foreground'
                }`}>
                  {indicators.rsi_14.toFixed(1)}
                </div>
                <div className="flex-1">
                  <div className="w-full bg-secondary h-3 rounded-full overflow-hidden relative">
                    <div className="absolute left-[30%] w-px h-full bg-success/50" />
                    <div className="absolute left-[70%] w-px h-full bg-destructive/50" />
                    <div
                      className={`h-full rounded-full transition-all ${
                        indicators.rsi_14 > 70 ? 'bg-destructive' : indicators.rsi_14 < 30 ? 'bg-success' : 'bg-primary'
                      }`}
                      style={{ width: `${Math.min(100, indicators.rsi_14)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-1 font-mono">
                    <span>Oversold (30)</span>
                    <span>Overbought (70)</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
