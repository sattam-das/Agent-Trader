import React, { useEffect, useState } from 'react'
import { LayoutDashboard, Layers, Calendar, Globe, AlertTriangle, Loader2 } from 'lucide-react'
import { useStore } from '@/store'
import { fetchHeatmap, fetchCalendar, fetchMarketPulse } from '@/api'

export default function DashboardPanel() {
  const { setTab } = useStore()
  const [data, setData] = useState({
    heatmap: null,
    calendar: null,
    pulse: null
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    const loadAll = async () => {
      setLoading(true)
      try {
        const [heatmapRes, calendarRes, pulseRes] = await Promise.all([
           fetchHeatmap('india').catch(() => null),
           fetchCalendar(30).catch(() => null),
           fetchMarketPulse().catch(() => null)
        ])
        if (active) {
           setData({
             heatmap: heatmapRes,
             calendar: calendarRes,
             pulse: pulseRes
           })
        }
      } finally {
        if (active) setLoading(false)
      }
    }
    loadAll()
    return () => { active = false }
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-32 space-y-6 animate-in fade-in">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
        <h3 className="text-xl font-mono text-foreground tracking-tight">Loading Intelligence Hub...</h3>
        <p className="text-muted-foreground text-sm max-w-sm text-center">
          Synthesizing live maps, calendars, and breaking news feeds.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-12 w-full">
      <div className="text-left space-y-2 pt-2 pb-6 border-b border-white/5">
        <h1 className="text-2xl font-bold text-foreground tracking-tight flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-primary/20 to-primary/5 text-primary rounded-xl border border-primary/20 shadow-[0_0_20px_rgba(139,92,246,0.2)]">
            <LayoutDashboard className="w-5 h-5"/>
          </div>
          Intelligence Hub
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Market Pulse Feed (Left 4 Cols) */}
        <div className="lg:col-span-4 flex flex-col">
           <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/5 px-1">
             <Globe className="w-4 h-4 text-accent" />
             <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">Market Pulse</h2>
           </div>
           
           <div className="glass-card p-4 h-[400px] overflow-y-auto custom-scrollbar space-y-4">
              {!data.pulse ? (
                 <div className="p-8 text-center text-muted-foreground border border-dashed border-white/10 rounded-xl flex flex-col items-center">
                   <AlertTriangle className="w-6 h-6 mb-2 opacity-50 text-accent" />
                   <p className="text-xs">MARKET PULSE UNAVAILABLE</p>
                 </div>
              ) : (
                 data.pulse?.categories?.map((cat, idx) => (
                    <div key={idx} className="space-y-3 pb-4 border-b border-white/5 last:border-0 last:pb-0">
                       <h3 className="text-[11px] font-bold text-accent uppercase tracking-widest">{cat.name}</h3>
                       {cat.articles.map((art, i) => (
                          <a key={i} href={art.link} target="_blank" rel="noreferrer" className="block p-3.5 bg-black/20 rounded-xl border border-white/5 hover:border-primary/50 hover:bg-black/40 hover:-translate-y-0.5 transition-all duration-300">
                             <p className="text-sm font-medium text-foreground leading-snug line-clamp-2">{art.title}</p>
                             <div className="flex justify-between items-center mt-3">
                                <span className="text-[10px] text-muted-foreground bg-white/5 px-2 py-0.5 rounded-full">{art.source}</span>
                                <span className="text-[10px] text-muted-foreground/60">{art.time}</span>
                             </div>
                          </a>
                       ))}
                    </div>
                 ))
              )}
           </div>
        </div>

        {/* Calendar Feed (Middle 4 Cols) */}
        <div className="lg:col-span-4 flex flex-col">
           <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/5 px-1">
             <Calendar className="w-4 h-4 text-primary" />
             <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">Economic Calendar</h2>
           </div>
           
           <div className="glass-card p-4 h-[400px] overflow-y-auto custom-scrollbar space-y-3">
              {!data.calendar || !data.calendar.events || data.calendar.events.length === 0 ? (
                 <div className="p-8 text-center text-muted-foreground border border-dashed border-white/10 rounded-xl flex flex-col items-center">
                   <p className="text-xs uppercase">No upcoming economic events.</p>
                 </div>
              ) : (
                 data.calendar.events.map((ev, i) => (
                    <div key={i} className="p-3 bg-black/20 rounded-xl border border-white/5 flex gap-4 items-center hover:border-primary/30 transition-all duration-300">
                        <div className="text-center w-14 shrink-0 border-r border-white/10 pr-2">
                           <p className="text-[10px] font-bold text-primary tracking-widest">{new Date(ev.date).toLocaleString('en-US', { month: 'short'}).toUpperCase()}</p>
                           <p className="text-xl font-bold text-foreground font-mono">{new Date(ev.date).getDate()}</p>
                        </div>
                        <div className="flex-1 space-y-1">
                           <h4 className="text-[13px] font-medium text-foreground/90">{ev.event}</h4>
                           <div className="flex justify-between items-center text-[10px] sm:flex-row flex-col sm:items-center gap-1 sm:gap-0 font-medium">
                              <span className="flex items-center gap-1">
                                <span className={`w-1.5 h-1.5 rounded-full ${ev.impact === 'High' ? 'bg-destructive shadow-[0_0_8px_rgba(239,68,68,0.6)]' : ev.impact === 'Medium' ? 'bg-amber-500' : 'bg-muted-foreground'}`}></span>
                                <span className="text-muted-foreground uppercase">{ev.impact}</span>
                              </span>
                              <span className="bg-white/5 text-muted-foreground px-2 py-0.5 rounded-full">{ev.country.toUpperCase()}</span>
                           </div>
                        </div>
                    </div>
                 ))
              )}
           </div>
        </div>

        {/* Sector Heatmap (Right 4 Cols) */}
        <div className="lg:col-span-4 flex flex-col">
           <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/5 px-1">
             <Layers className="w-4 h-4 text-success" />
             <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">Sector Heatmap</h2>
           </div>
           
           <div className="glass-card p-3 h-[400px] overflow-y-auto custom-scrollbar">
              {!data.heatmap || !data.heatmap.sectors || data.heatmap.sectors.length === 0 ? (
                 <div className="p-8 text-center text-muted-foreground border border-dashed border-white/10 rounded-xl flex flex-col items-center">
                    <p className="text-xs uppercase">Heatmap data currently unavailable.</p>
                 </div>
              ) : (
                 <div className="grid grid-cols-2 gap-1">
                    {data.heatmap.sectors.map((sec, i) => {
                       const change = sec.change_pct || 0;
                       
                        // Glassy premium colors
                       let colorClass = 'bg-white/5 text-muted-foreground border-white/5'
                       if (change >= 1) colorClass = 'bg-success/20 text-success border-success/30 shadow-[0_4px_12px_rgba(16,185,129,0.1)]'
                       else if (change > 0) colorClass = 'bg-success/10 text-success border-success/10'
                       else if (change <= -1) colorClass = 'bg-destructive/20 text-destructive border-destructive/30 shadow-[0_4px_12px_rgba(239,68,68,0.1)]'
                       else if (change < 0) colorClass = 'bg-destructive/10 text-destructive border-destructive/10'

                       return (
                          <div key={i} className={`p-4 rounded-xl border ${colorClass} text-center space-y-1 hover:brightness-125 cursor-pointer hover:scale-[1.02] transition-all duration-300`} onClick={() => setTab('screener')}>
                             <p className="text-[11px] font-bold tracking-wider line-clamp-1 truncate">{sec.name}</p>
                             <p className="text-lg font-bold font-mono tracking-tight">
                                {change > 0 ? '+' : ''}{change.toFixed(2)}%
                             </p>
                          </div>
                      )
                    })}
                 </div>
              )}
           </div>
        </div>

      </div>
    </div>
  )
}
