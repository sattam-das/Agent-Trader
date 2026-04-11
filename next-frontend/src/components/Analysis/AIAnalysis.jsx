import React, { useEffect, useState } from 'react'
import { RadialBarChart, RadialBar, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts'
import { useStore } from '@/store'
import { fetchAnalysis, calcPositionSize } from '@/api'
import { BrainCircuit, Loader2, CheckCircle2, AlertTriangle, Info, TrendingUp, TrendingDown, Calculator, IndianRupee } from 'lucide-react'

export default function AIAnalysis() {
  const { activeTicker } = useStore()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  // Position Sizer State
  const [sizeInput, setSizeInput] = useState({ account_size: 100000, risk_pct: 1.0, stop_loss: 0 })
  const [sizeResult, setSizeResult] = useState(null)
  const [sizeLoading, setSizeLoading] = useState(false)

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
      <div className="p-4 border border-destructive bg-destructive/10 max-w-2xl mx-auto mt-12 flex items-center gap-2">
        <div className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="w-5 h-5" />
          <h3 className="font-bold text-sm font-mono uppercase tracking-widest">Analysis Failed</h3>
        </div>
        <p className="text-sm font-mono text-destructive ml-2">- {error}</p>
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
    'STRONG BUY': 'bg-success/10 text-success border-success',
    'BUY': 'bg-success/5 text-success border-success',
    'HOLD': 'bg-secondary text-primary border-border',
    'SELL': 'bg-destructive/5 text-destructive border-destructive',
    'STRONG SELL': 'bg-destructive/10 text-destructive border-destructive',
  }
  const statusColor = recColors[result.recommendation] || 'bg-secondary text-foreground border-border'

  // Extract last known historical price
  const priceValues = Object.values(data.historical_prices || {})
  const currentPrice = priceValues.length > 0 ? priceValues[priceValues.length - 1] : 0.0

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-12">
      
      {/* Header Overview Card */}
      <div className="flex flex-col md:flex-row gap-6 p-4 border-b border-border bg-card">
        <div className="flex-1 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-mono text-foreground font-bold">{data.company_name} <span className="text-xl text-primary align-middle ml-2">({data.ticker})</span></h1>
              <p className="text-muted-foreground mt-1 text-sm font-mono flex items-center gap-2">
                <BrainCircuit className="w-4 h-4" /> Synthesized by {data.model} in <span className="text-foreground">{data.latency_ms}ms</span>
              </p>
            </div>
            <div className={`px-4 py-2 border font-bold tracking-widest text-lg font-mono ${statusColor}`}>
              {result.recommendation}
            </div>
          </div>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-border">
             <div className="space-y-1">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">CONVICTION</p>
                <p className="text-lg font-mono text-foreground">{result.conviction || 'N/A'}</p>
             </div>
             <div className="space-y-1 border-l border-border pl-4">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">CONFIDENCE</p>
                <p className="text-lg font-mono text-foreground">{((result.confidence || 0) * 100).toFixed(1)}%</p>
             </div>
             <div className="space-y-1 border-l border-border pl-4">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">CURRENT PRICE</p>
                <p className="text-lg font-mono text-primary">${currentPrice.toFixed(2)}</p>
             </div>
             <div className="space-y-1 border-l border-border pl-4">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">OVERALL SCORE</p>
                <p className="text-lg font-mono text-amber-500">{((result.weighted_score || 0) * 100).toFixed(1)} / 100</p>
             </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Radar Chart Panel */}
        <div className="lg:col-span-1 p-4 border border-border bg-card flex flex-col items-center justify-center min-h-[300px]">
          <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider w-full mb-2">5-Axis Profile</h3>
          <div className="w-full h-full flex-1 min-h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94A3B8', fontSize: 11, fontFamily: 'monospace' }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                <Radar name="Score" dataKey="A" stroke="#3B82F6" strokeWidth={2} fill="#3B82F6" fillOpacity={0.15} />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', color: '#fff', fontFamily: 'monospace' }} itemStyle={{ color: '#3B82F6' }}/>
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Breakdown Panel */}
        <div className="lg:col-span-2 p-4 border border-border bg-card space-y-4">
           <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider w-full mb-4">Detailed Component Scoring</h3>
           <div className="grid grid-cols-2 lg:grid-cols-3 gap-[1px] bg-border border border-border">
              {radarData.map(item => (
                 <div key={item.subject} className="p-4 bg-background flex flex-col items-center justify-center text-center">
                    <span className="text-[10px] uppercase text-muted-foreground tracking-widest block mb-2">{item.subject}</span>
                    <div className="relative w-20 h-20 flex items-center justify-center mx-auto mt-1 mb-1">
                        <svg className="w-full h-full transform -rotate-90">
                           <circle cx="40" cy="40" r="34" fill="none" strokeWidth="8" className="stroke-secondary" />
                           <circle 
                              cx="40" cy="40" r="34" fill="none" strokeWidth="8"
                              className={item.A >= 60 ? 'stroke-success drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]' : item.A <= 40 ? 'stroke-destructive drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]' : 'stroke-primary drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]'}
                              style={{ 
                                 strokeDasharray: 34 * 2 * Math.PI,
                                 strokeDashoffset: 34 * 2 * Math.PI * (1 - Math.max(0, Math.min(100, item.A)) / 100),
                                 strokeLinecap: 'round',
                                 transition: 'stroke-dashoffset 1s ease-out'
                              }}
                           />
                        </svg>
                        <span className="absolute text-sm font-mono font-bold text-foreground">
                          {item.A.toFixed(1)}%
                        </span>
                     </div>
                 </div>
              ))}
              {/* Confluence Bonus Card */}
              <div className="p-4 bg-primary/10 flex flex-col items-center justify-center text-center">
                    <span className="text-[10px] uppercase text-primary tracking-widest block mb-1">Confluence Bonus</span>
                    <div className="flex items-center justify-center w-20 h-20 bg-primary/20 rounded-full border border-primary/50 shadow-[0_0_15px_rgba(139,92,246,0.4)] mt-2">
                       <span className="text-xl font-mono font-bold text-primary">
                         +{((breakdown.confluence_bonus || 0) * 100).toFixed(0)}%
                       </span>
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-3">Rewards cross-agent agreement.</p>
                 </div>
           </div>
        </div>

      </div>

      {/* Rationale Panel */}
      <div className="p-4 border border-border bg-card space-y-4">
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

      {/* Position Size Calculator */}
      <div className="p-4 border border-border bg-card space-y-5">
         <div className="flex items-center gap-3 border-b border-border pb-4">
            <div className="p-2 border border-border bg-secondary text-primary flex items-center justify-center">
               <Calculator className="w-5 h-5" />
            </div>
            <div>
               <h3 className="text-xl uppercase font-mono font-bold text-foreground">Position Sizer</h3>
               <p className="text-[10px] tracking-widest font-mono uppercase text-muted-foreground mr-12 mt-1">Calculate the exact number of shares to buy risking a % of your account balance.</p>
            </div>
         </div>

         <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
               <label className="text-[10px] uppercase text-muted-foreground font-bold tracking-widest">Account Size (₹)</label>
               <input 
                  type="number" className="w-full bg-background border border-border py-2 px-3 focus:outline-none focus:border-primary font-mono text-sm" 
                  value={sizeInput.account_size} onChange={e => setSizeInput({...sizeInput, account_size: Number(e.target.value)})}
               />
            </div>
            <div className="space-y-2">
               <label className="text-[10px] uppercase text-muted-foreground font-bold tracking-widest">Risk (%)</label>
               <input 
                  type="number" step="0.1" className="w-full bg-background border border-border py-2 px-3 focus:outline-none focus:border-primary font-mono text-sm" 
                  value={sizeInput.risk_pct} onChange={e => setSizeInput({...sizeInput, risk_pct: Number(e.target.value)})}
               />
            </div>
            <div className="space-y-2">
               <label className="text-[10px] uppercase text-muted-foreground font-bold tracking-widest">Stop Loss (₹)</label>
               <input 
                  type="number" className="w-full bg-background border border-border py-2 px-3 focus:outline-none focus:border-primary font-mono text-sm" 
                  value={sizeInput.stop_loss} onChange={e => setSizeInput({...sizeInput, stop_loss: Number(e.target.value)})}
               />
            </div>
            <div className="flex items-end">
               <button 
                  onClick={async () => {
                     if (!sizeInput.stop_loss) return;
                     setSizeLoading(true);
                     try {
                        const res = await calcPositionSize({
                           account_size: sizeInput.account_size,
                           risk_pct: sizeInput.risk_pct,
                           entry_price: currentPrice,
                           stop_loss: sizeInput.stop_loss
                        });
                        setSizeResult(res);
                     } catch(e) {
                        console.error(e)
                     } finally {
                        setSizeLoading(false);
                     }
                  }}
                  disabled={sizeLoading || !sizeInput.stop_loss || sizeInput.stop_loss >= currentPrice}
                  className="w-full py-2 bg-primary hover:bg-primary/80 border border-primary text-white font-mono text-sm transition-none uppercase disabled:opacity-50 disabled:border-border disabled:bg-secondary flex items-center justify-center gap-2 h-[38px]"
               >
                  {sizeLoading ? <Loader2 className="w-4 h-4 animate-spin"/> : 'CALCULATE SIZE'}
               </button>
            </div>
         </div>

         {sizeResult && (
            <div className="mt-4 p-4 border border-primary bg-primary/5 flex flex-col md:flex-row items-center justify-between gap-6">
               <div className="text-center md:text-left flex-1 border-r border-violet-500/20 pr-6">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Recommended Shares</p>
                  <p className="text-4xl font-mono text-foreground mt-1">{sizeResult.shares} <span className="text-lg text-violet-400">shares</span></p>
               </div>
               <div className="text-center flex-1">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Amount Risked</p>
                  <p className="text-xl font-mono text-destructive mt-1">₹{sizeResult.risk_amount.toFixed(2)}</p>
               </div>
               <div className="text-center flex-1">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Total Position</p>
                  <p className="text-xl font-mono text-foreground mt-1">₹{sizeResult.position_value.toFixed(2)}</p>
               </div>
               <div className="text-center flex-1">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Risk/Reward</p>
                  <p className="text-xl font-mono text-amber-400 mt-1">{sizeResult.reward_to_risk > 0 ? sizeResult.reward_to_risk.toFixed(2) : 'N/A'}</p>
               </div>
            </div>
         )}
      </div>

    </div>
  )
}
