import React, { useEffect, useState } from 'react'
import { fetchNews, fetchMarketPulse, fetchSentiment } from '@/api'
import { useStore } from '@/store'
import { Newspaper, Loader2, AlertTriangle, ExternalLink, TrendingUp, TrendingDown, Minus, Globe, MessageSquare } from 'lucide-react'

export default function NewsPanel() {
  const { activeTicker } = useStore()
  const [loading, setLoading] = useState(true)
  const [newsData, setNewsData] = useState(null)
  const [pulseData, setPulseData] = useState(null)
  const [sentimentData, setSentimentData] = useState(null)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('ticker')

  useEffect(() => {
    let active = true
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [news, pulse, sentiment] = await Promise.allSettled([
          fetchNews(activeTicker),
          fetchMarketPulse(),
          fetchSentiment(activeTicker)
        ])
        if (active) {
          if (news.status === 'fulfilled') setNewsData(news.value)
          if (pulse.status === 'fulfilled') setPulseData(pulse.value)
          if (sentiment.status === 'fulfilled') setSentimentData(sentiment.value)
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
    if (s === 'positive' || s === 'bullish') return <TrendingUp className="w-3.5 h-3.5 text-success" />
    if (s === 'negative' || s === 'bearish') return <TrendingDown className="w-3.5 h-3.5 text-destructive" />
    return <Minus className="w-3.5 h-3.5 text-muted-foreground" />
  }

  const sentimentBadge = (s) => {
    if (s === 'positive' || s === 'bullish') return 'badge-buy'
    if (s === 'negative' || s === 'bearish') return 'badge-sell'
    return 'badge-neutral'
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-32 space-y-4 animate-fade-in">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
        <p className="text-[10px] tracking-widest uppercase text-muted-foreground font-mono">Fetching live news & social sentiment...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="bg-card border-b border-border py-4 px-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 border border-border text-primary bg-secondary/30">
              <Newspaper className="w-5 h-5" />
            </div>
            <div>
               <h1 className="text-xl font-bold font-mono text-foreground tracking-tight uppercase">Live News & Sentiment</h1>
               <p className="text-[10px] uppercase tracking-widest text-muted-foreground mt-1">Real-time news and Reddit sentiment analysis</p>
            </div>
          </div>
          <div className="flex bg-secondary border border-border">
            <button onClick={() => setTab('ticker')} className={`px-4 py-2 text-xs font-mono transition-none border-r border-border ${tab === 'ticker' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
              {activeTicker}
            </button>
            <button onClick={() => setTab('market')} className={`px-4 py-2 text-xs font-mono transition-none flex items-center gap-1 ${tab === 'market' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
              <Globe className="w-3 h-3" /> MARKET PULSE
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

      {/* Ticker News */}
      {tab === 'ticker' && (
        <div className="space-y-6 animate-fade-in">
          
          {/* Social Sentiment Widget */}
          {sentimentData && (
            <div className="p-3 bg-secondary/20 border border-border flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                 <div className="p-2 border border-destructive text-destructive bg-destructive/10 shrink-0">
                    <MessageSquare className="w-4 h-4" />
                 </div>
                 <div>
                    <h3 className="text-[10px] font-bold text-destructive uppercase tracking-widest">Reddit Sentiment</h3>
                    <p className="text-[10px] text-muted-foreground mt-0.5">r/IndianStreetBets Analysis for {activeTicker}</p>
                 </div>
              </div>
              <div className="flex gap-4 items-center">
                  <div className="text-right">
                    <p className="text-[10px] text-muted-foreground uppercase">Overall Label</p>
                    <span className={`px-2 py-0.5 mt-1 inline-flex border border-current text-[10px] tracking-widest uppercase font-mono font-bold ${sentimentData.label === 'BULLISH' ? 'badge-buy' : sentimentData.label === 'BEARISH' ? 'badge-sell' : 'badge-neutral'}`}>
                       {sentimentData.label || 'NEUTRAL'}
                    </span>
                 </div>
                 <div className="w-px h-8 bg-border"></div>
                 <div className="text-right">
                    <p className="text-[10px] text-muted-foreground uppercase">Score</p>
                    <p className="text-xl font-mono font-bold text-foreground">{sentimentData.score ? sentimentData.score.toFixed(2) : '0.00'}</p>
                 </div>
                 <div className="w-px h-8 bg-border"></div>
                 <div className="text-right">
                    <p className="text-[10px] text-muted-foreground uppercase">Mentions</p>
                    <p className="text-xl font-mono font-bold text-foreground">{sentimentData.mentions || 0}</p>
                 </div>
              </div>
            </div>
          )}

          {/* Articles */}
          {newsData && (
            <div className="space-y-[1px] bg-border border border-border">
              <div className="bg-card p-2 text-xs font-mono text-muted-foreground">{newsData.count} ARTICLES FOUND</div>
              {newsData.articles.map((a, i) => (
                <a
                  key={i}
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-3 bg-card hover:bg-secondary/40 transition-none group"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                       <h3 className="text-[13px] font-bold text-blue-500 group-hover:text-blue-400 underline transition-colors leading-snug">
                        {a.title}
                      </h3>
                      <div className="flex items-center gap-3 text-[10px] text-muted-foreground uppercase opacity-80">
                        <span className="font-mono text-primary">{a.source}</span>
                        <span>·</span>
                        <span className="font-mono">{a.time}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`flex items-center gap-1 px-2 py-0.5 border border-current text-[10px] uppercase font-bold tracking-widest font-mono ${sentimentBadge(a.sentiment)}`}>
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
        </div>
      )}

      {/* Market Pulse */}
      {tab === 'market' && pulseData && (
        <div className="space-y-4">
          {Object.entries(pulseData).map(([category, articles]) => (
            <div key={category} className="space-y-[1px] bg-border border border-border">
              <div className="bg-card p-2 text-xs font-bold font-mono text-primary uppercase tracking-widest flex items-center gap-2">
                <Globe className="w-3 h-3" />
                {category.replace(/_/g, ' ')}
              </div>
              {Array.isArray(articles) && articles.map((a, i) => (
                <a
                  key={i}
                  href={a.url || a.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-3 bg-card hover:bg-secondary/40 transition-none text-[13px] font-bold text-blue-500 underline hover:text-blue-400"
                >
                  {a.title}
                  <span className="text-[10px] text-muted-foreground font-mono ml-3 opacity-70">{a.source || ''}</span>
                </a>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
