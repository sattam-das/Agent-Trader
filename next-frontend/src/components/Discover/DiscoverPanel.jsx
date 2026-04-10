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
          <Sparkles className="w-5 h-5 text-amber-400 absolute -top-1 -right-1 animate-pulse" />
        </div>
        <h3 className="text-xl font-mono text-foreground tracking-tight">Scanning Markets with AI</h3>
        <p className="text-muted-foreground text-sm max-w-sm text-center leading-relaxed">
          Discovery agent is analyzing live news, earnings, and market signals to find actionable opportunities...
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 border border-destructive/50 bg-destructive/10 rounded-xl space-y-2 max-w-2xl mx-auto mt-12 animate-fade-in">
        <div className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="w-5 h-5" />
          <h3 className="font-bold">Discovery Failed</h3>
        </div>
        <p className="text-sm font-mono text-destructive/80">{error}</p>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="glass-card rounded-xl p-6 space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-500/15 flex items-center justify-center">
            <Lightbulb className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">AI Market Discovery</h1>
            <p className="text-xs font-mono text-muted-foreground">
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
            ? 'text-success bg-success/10 border-success/20'
            : s.sentiment === 'bearish'
            ? 'text-destructive bg-destructive/10 border-destructive/20'
            : 'text-amber-400 bg-amber-500/10 border-amber-500/20'

          return (
            <button
              key={i}
              onClick={() => handleSelect(s.ticker)}
              className="group text-left p-5 border border-border bg-card rounded-xl hover:border-primary/50 hover:bg-card/80 transition-all duration-300 space-y-3"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-lg font-mono font-bold text-primary">{s.ticker}</span>
                  <p className="text-xs text-muted-foreground mt-0.5">{s.sector || 'Equity'}</p>
                </div>
                <span className={`text-xs font-mono px-2 py-0.5 rounded border uppercase ${sentimentColor}`}>
                  {s.sentiment || 'neutral'}
                </span>
              </div>

              <p className="text-sm text-foreground/90 leading-relaxed line-clamp-3">{s.reason}</p>

              {s.catalyst && (
                <div className="flex items-center gap-2 text-xs text-amber-400">
                  <Zap className="w-3 h-3" />
                  <span className="line-clamp-1">{s.catalyst}</span>
                </div>
              )}

              <div className="flex items-center gap-1.5 text-xs text-primary opacity-0 group-hover:opacity-100 transition-opacity pt-1">
                <span>Analyze</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
