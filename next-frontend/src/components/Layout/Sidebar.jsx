import React from 'react'
import { Plus, TrendingUp, TrendingDown } from 'lucide-react'
import { useStore } from '@/store'

export default function Sidebar() {
  const { watchlist, activeTicker, setTicker } = useStore()

  const quickAdds = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'AAPL', 'NVDA']

  return (
    <aside className="w-[280px] bg-secondary/30 border-r border-border flex flex-col fixed left-0 top-[52px] bottom-0">
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-6 flex flex-col custom-scrollbar">
        
        {/* Watchlist Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-bold uppercase tracking-widest pl-1">Watchlist</span>
            <button className="hover:text-foreground transition-colors p-1"><Plus className="w-3 h-3" /></button>
          </div>
          <div className="space-y-1">
            {watchlist.map((item) => (
              <button 
                key={item.ticker}
                onClick={() => setTicker(item.ticker)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-md transition-colors font-mono text-sm ${activeTicker === item.ticker ? 'bg-primary/20 border border-primary/30 text-foreground' : 'hover:bg-card border border-transparent text-muted-foreground hover:text-foreground'}`}
              >
                <span>{item.ticker}</span>
                <div className={`flex items-center gap-1 ${item.change >= 0 ? 'text-success' : 'text-destructive'}`}>
                  {item.change >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3"/>}
                  <span>{Math.abs(item.change)}%</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Quick Add Presets */}
        <div className="space-y-3 pt-4 border-t border-border/50">
          <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground pl-1">Quick Add</span>
          <div className="flex flex-wrap gap-2">
            {quickAdds.map(ticker => (
              <button
                key={ticker}
                onClick={() => setTicker(ticker)}
                className={`text-xs font-mono px-2 py-1 bg-card border transition-all rounded ${activeTicker === ticker ? 'border-primary text-primary' : 'border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'}`}
              >
                {ticker}
              </button>
            ))}
          </div>
        </div>

      </div>
    </aside>
  )
}
