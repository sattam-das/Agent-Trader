import React, { useEffect, useState } from 'react'
import { fetchDiscover } from '@/api'
import { useStore } from '@/store'
import { Lightbulb, Loader2, AlertTriangle, TrendingUp, Zap, ArrowRight, Sparkles } from 'lucide-react'

export default function DiscoverPanel() {
  const { setTicker, setTab } = useStore()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const result = await fetchDiscover()
        setData(result)
      } catch (err) {
        setError(err.response?.data?.detail || err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleSelect = (ticker) => {
    setTicker(ticker)
    setTab('analysis')
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-32 space-y-6 animate-fade-in">
        <div className="relative">
          <Loader2 className="w-12 h-12 text-primary animate-spin" />
          <Sparkles className="w-5 h-5 text-primary absolute -top-1 -right-1" />
        </div>
        <h3 className="text-xl font-mono text-foreground uppercase tracking-widest">Scanning Markets with AI</h3>
        <p className="text-muted-foreground text-[10px] uppercase tracking-widest max-w-sm text-center">
          Discovery agent is analyzing live news, earnings, and market signals to find actionable opportunities...
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 border border-destructive bg-destructive/10 flex items-center gap-2 max-w-2xl mx-auto mt-12">
        <AlertTriangle className="w-5 h-5 text-destructive" />
        <h3 className="font-bold text-destructive text-sm font-mono uppercase">Discovery Failed</h3>
        <p className="text-sm font-mono text-destructive ml-2">- {error}</p>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="bg-card border border-border p-4 space-y-3">
        <div className="flex items-center gap-3">
          <div className="p-2 border border-border bg-secondary text-primary flex items-center justify-center">
            <Lightbulb className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold font-mono uppercase text-foreground">AI Market Discovery</h1>
            <p className="text-[10px] tracking-widest font-mono text-muted-foreground uppercase mt-1">
              Powered by {data.model} · {data.latency_ms}ms
            </p>
          </div>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">{data.summary}</p>
      </div>

      {/* Suggestions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 stagger-children">
        {data.suggestions.map((s, i) => {
          const sentimentColor = s.sentiment === 'bullish'
            ? 'text-success bg-success/5 border-success'
            : s.sentiment === 'bearish'
            ? 'text-destructive bg-destructive/5 border-destructive'
            : 'text-primary bg-primary/5 border-primary'

          return (
            <button
              key={i}
              onClick={() => handleSelect(s.ticker)}
              className="group text-left p-4 border border-border bg-card hover:border-primary transition-none space-y-3"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-lg font-mono font-bold text-primary">{s.ticker}</span>
                  <p className="text-[10px] text-muted-foreground mt-0.5 tracking-widest uppercase">{s.sector || 'Equity'}</p>
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 border uppercase font-bold tracking-widest ${sentimentColor}`}>
                  {s.sentiment || 'neutral'}
                </span>
              </div>

              <p className="text-sm font-mono text-foreground/90 line-clamp-3">{s.reason}</p>

              {s.catalyst && (
                <div className="flex items-center gap-2 text-[10px] uppercase font-bold text-primary border-t border-border pt-2">
                  <Zap className="w-3 h-3" />
                  <span className="line-clamp-1">{s.catalyst}</span>
                </div>
              )}

              <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-primary opacity-0 group-hover:opacity-100 transition-none pt-2">
                <span>ANALYZE</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
