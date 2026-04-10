import React, { useEffect, useState } from 'react'
import { fetchNews, fetchMarketPulse } from '@/api'
import { useStore } from '@/store'
import { Newspaper, Loader2, AlertTriangle, ExternalLink, TrendingUp, TrendingDown, Minus, Globe } from 'lucide-react'

export default function NewsPanel() {
  const { activeTicker } = useStore()
  const [loading, setLoading] = useState(true)
  const [newsData, setNewsData] = useState(null)
  const [pulseData, setPulseData] = useState(null)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('ticker')

  useEffect(() => {
    let active = true
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [news, pulse] = await Promise.allSettled([
          fetchNews(activeTicker),
          fetchMarketPulse(),
        ])
        if (active) {
          if (news.status === 'fulfilled') setNewsData(news.value)
          if (pulse.status === 'fulfilled') setPulseData(pulse.value)
        }
      } catch (err) {
        if (active) setError(err.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [activeTicker])

  const sentimentIcon = (s) => {
    if (s === 'positive') return <TrendingUp className="w-3.5 h-3.5 text-success" />
    if (s === 'negative') return <TrendingDown className="w-3.5 h-3.5 text-destructive" />
    return <Minus className="w-3.5 h-3.5 text-muted-foreground" />
  }

  const sentimentBadge = (s) => {
    if (s === 'positive') return 'badge-buy'
    if (s === 'negative') return 'badge-sell'
    return 'badge-neutral'
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-32 space-y-4 animate-fade-in">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
        <p className="text-sm text-muted-foreground font-mono">Fetching live news...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="glass-card rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-500/15 flex items-center justify-center">
              <Newspaper className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Live News</h1>
              <p className="text-xs text-muted-foreground">Real-time news with sentiment analysis</p>
            </div>
          </div>
          <div className="flex gap-1 bg-secondary/50 p-1 rounded-lg">
            <button onClick={() => setTab('ticker')} className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${tab === 'ticker' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
              {activeTicker}
            </button>
            <button onClick={() => setTab('market')} className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1 ${tab === 'market' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
              <Globe className="w-3 h-3" /> Market Pulse
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

      {/* Ticker News */}
      {tab === 'ticker' && newsData && (
        <div className="space-y-3 stagger-children">
          <p className="text-xs font-mono text-muted-foreground">{newsData.count} articles found</p>
          {newsData.articles.map((a, i) => (
            <a
              key={i}
              href={a.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-4 border border-border bg-card rounded-xl hover:border-primary/40 transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-2">
                  <h3 className="text-sm font-medium text-foreground group-hover:text-primary transition-colors leading-snug">
                    {a.title}
                  </h3>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="font-mono">{a.source}</span>
                    <span>·</span>
                    <span>{a.time}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono ${sentimentBadge(a.sentiment)}`}>
                    {sentimentIcon(a.sentiment)}
                    {a.sentiment}
                  </span>
                  <ExternalLink className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </a>
          ))}
          {newsData.articles.length === 0 && (
            <div className="p-12 text-center text-muted-foreground">
              <Newspaper className="w-8 h-8 mx-auto mb-3 opacity-40" />
              <p className="text-sm">No recent news found for {activeTicker}</p>
            </div>
          )}
        </div>
      )}

      {/* Market Pulse */}
      {tab === 'market' && pulseData && (
        <div className="space-y-4 stagger-children">
          {Object.entries(pulseData).map(([category, articles]) => (
            <div key={category} className="space-y-2">
              <h3 className="text-sm font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                <Globe className="w-4 h-4 text-primary" />
                {category.replace(/_/g, ' ')}
              </h3>
              {Array.isArray(articles) && articles.map((a, i) => (
                <a
                  key={i}
                  href={a.url || a.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-3 border border-border/50 bg-card/50 rounded-lg hover:border-primary/30 transition-all text-sm text-foreground/80 hover:text-foreground"
                >
                  {a.title}
                  <span className="text-xs text-muted-foreground ml-2">{a.source || ''}</span>
                </a>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
