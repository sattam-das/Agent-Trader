import React, { useEffect, useState } from 'react'
import { RadialBarChart, RadialBar, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts'
import { useStore } from '@/store'
import { fetchAnalysis } from '@/api'
import { BrainCircuit, Loader2, CheckCircle2, AlertTriangle, Info, TrendingUp, TrendingDown } from 'lucide-react'

export default function AIAnalysis() {
  const { activeTicker } = useStore()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let active = true
    const loadAnalysis = async () => {
      setLoading(true)
      setError(null)
      try {
        const result = await fetchAnalysis(activeTicker)
        if (active) setData(result)
      } catch (err) {
        if (active) setError(err.response?.data?.detail || err.message)
      } finally {
        if (active) setLoading(false)
      }
    }

    loadAnalysis()
    return () => { active = false }
  }, [activeTicker])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-32 space-y-6 animate-in fade-in duration-500">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
        <h3 className="text-xl font-mono text-foreground tracking-tight">Running 5-Agent Analysis</h3>
        <p className="text-muted-foreground text-sm max-w-sm text-center leading-relaxed">
          Reading live market data, dynamically extracting news sentiment, and computing deep financial probabilities for <strong className="text-primary font-mono">{activeTicker}</strong>...
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 border border-destructive/50 bg-destructive/10 rounded-xl space-y-2 max-w-2xl mx-auto mt-12 animate-in fade-in">
        <div className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="w-5 h-5" />
          <h3 className="font-bold">Analysis Failed</h3>
        </div>
        <p className="text-sm font-mono text-destructive/80">{error}</p>
      </div>
    )
  }

  if (!data) return null

  // Process data from backend
  const result = data.result || {}
  const breakdown = result.score_breakdown || {}

  const radarData = [
    { subject: 'News', A: (breakdown.news_component || 0) * 100 },
    { subject: 'Financial', A: (breakdown.financial_component || 0) * 100 },
    { subject: 'Technical', A: (breakdown.technical_component || 0) * 100 },
    { subject: 'Macro', A: (breakdown.macro_component || 0) * 100 },
    { subject: 'Risk', A: (breakdown.risk_component || 0) * 100 },
  ]

  const recColors = {
    'STRONG BUY': 'bg-success/20 text-success border-success/30',
    'BUY': 'bg-success/15 text-success border-success/20',
    'HOLD': 'bg-amber-500/15 text-amber-500 border-amber-500/20',
    'SELL': 'bg-destructive/15 text-destructive border-destructive/20',
    'STRONG SELL': 'bg-destructive/20 text-destructive border-destructive/30',
  }
  const statusColor = recColors[result.recommendation] || 'bg-secondary text-foreground border-border'

  // Extract last known historical price
  const priceValues = Object.values(data.historical_prices || {})
  const currentPrice = priceValues.length > 0 ? priceValues[priceValues.length - 1] : 0.0

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-12">
      
      {/* Header Overview Card */}
      <div className="flex flex-col md:flex-row gap-6 p-6 border border-border bg-card rounded-xl shadow-sm">
        <div className="flex-1 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-mono text-foreground font-bold">{data.company_name} <span className="text-xl text-primary align-middle ml-2">({data.ticker})</span></h1>
              <p className="text-muted-foreground mt-1 text-sm font-mono flex items-center gap-2">
                <BrainCircuit className="w-4 h-4" /> Synthesized by {data.model} in <span className="text-foreground">{data.latency_ms}ms</span>
              </p>
            </div>
            <div className={`px-4 py-2 border rounded-md font-bold tracking-widest text-lg ${statusColor}`}>
              {result.recommendation}
            </div>
          </div>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-border/50">
             <div className="space-y-1">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Conviction</p>
                <p className="text-lg font-mono text-foreground">{result.conviction || 'N/A'}</p>
             </div>
             <div className="space-y-1">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Confidence</p>
                <p className="text-lg font-mono text-foreground">{((result.confidence || 0) * 100).toFixed(1)}%</p>
             </div>
             <div className="space-y-1">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Current Price</p>
                <p className="text-lg font-mono text-foreground">${currentPrice.toFixed(2)}</p>
             </div>
             <div className="space-y-1">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Overall Score</p>
                <p className="text-lg font-mono text-foreground">{((result.weighted_score || 0) * 100).toFixed(1)} / 100</p>
             </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Radar Chart Panel */}
        <div className="lg:col-span-1 p-6 border border-border bg-card rounded-xl flex flex-col items-center justify-center min-h-[300px]">
          <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider w-full mb-2">5-Axis Profile</h3>
          <div className="w-full h-full flex-1 min-h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="#1a243d" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#8B95A5', fontSize: 11, fontFamily: 'monospace' }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                <Radar name="Score" dataKey="A" stroke="#0066FF" strokeWidth={2} fill="#0066FF" fillOpacity={0.15} />
                <Tooltip contentStyle={{ backgroundColor: '#0D1322', borderColor: '#1a243d', color: '#fff' }} itemStyle={{ color: '#0066FF' }}/>
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Breakdown Panel */}
        <div className="lg:col-span-2 p-6 border border-border bg-card rounded-xl space-y-4">
           <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider w-full mb-4">Detailed Component Scoring</h3>
           <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {radarData.map(item => (
                 <div key={item.subject} className="p-4 rounded-lg bg-background border border-border/50 space-y-1 flex flex-col">
                    <span className="text-xs uppercase text-muted-foreground tracking-widest">{item.subject}</span>
                    <span className={`text-2xl font-mono font-bold ${item.A >= 60 ? 'text-success' : item.A <= 40 ? 'text-destructive' : 'text-foreground'}`}>
                      {item.A.toFixed(1)}%
                    </span>
                    <div className="w-full bg-secondary h-1.5 mt-3 rounded overflow-hidden">
                       <div className={`h-full ${item.A >= 60 ? 'bg-success' : item.A <= 40 ? 'bg-destructive' : 'bg-primary'}`} style={{ width: `${item.A}%` }}></div>
                    </div>
                 </div>
              ))}
              {/* Confluence Bonus Card */}
              <div className="p-4 rounded-lg bg-background border border-border/50 space-y-1 flex flex-col bg-primary/5 border-primary/20">
                    <span className="text-xs uppercase text-primary/80 tracking-widest">Confluence Bonus</span>
                    <span className="text-2xl font-mono font-bold text-primary">
                      {((breakdown.confluence_bonus || 0) * 100).toFixed(1)}%
                    </span>
                    <p className="text-xs text-muted-foreground mt-2">Rewards cross-agent agreement.</p>
                 </div>
           </div>
        </div>

      </div>

      {/* Rationale Panel */}
      <div className="p-6 border border-border bg-card rounded-xl space-y-4">
        <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
          <Info className="w-4 h-4 text-primary"/> AI Orchestrator Rationale
        </h3>
        <ul className="space-y-4 mt-4">
          {(result.rationale || []).map((point, idx) => (
            <li key={idx} className="flex gap-3 text-sm text-foreground/90">
              <CheckCircle2 className="w-5 h-5 text-primary shrink-0 opacity-70 mt-0.5" />
              <span className="leading-relaxed">{point}</span>
            </li>
          ))}
        </ul>

        {result.risk_factors && result.risk_factors.length > 0 && (
          <div className="mt-8 pt-6 border-t border-border/50">
             <h4 className="text-sm font-bold text-destructive flex items-center gap-2 mb-4">
               <AlertTriangle className="w-4 h-4"/> Identified Risk Factors
             </h4>
             <ul className="space-y-3">
              {result.risk_factors.map((risk, idx) => (
                <li key={idx} className="flex gap-3 text-sm text-destructive/80 items-start">
                  <div className="w-1.5 h-1.5 rounded-full bg-destructive mt-1.5 shrink-0" />
                  <span className="leading-relaxed">{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

    </div>
  )
}
