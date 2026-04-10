import React, { useState } from 'react'
import { BrainCircuit, Search, TrendingUp, TrendingDown } from 'lucide-react'
import { useStore } from '@/store'

export default function Navbar() {
  const { activeTicker, setTicker } = useStore()
  const [searchInput, setSearchInput] = useState('')

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchInput.trim()) {
      setTicker(searchInput.trim())
      setSearchInput('')
    }
  }

  // Mock price change for header display
  const priceChange = 1.25 

  return (
    <header className="h-[52px] border-b border-border bg-card flex items-center justify-between px-6 shrink-0 z-10 w-full fixed top-0">
      <div className="flex items-center gap-2">
        <BrainCircuit className="w-5 h-5 text-primary" />
        <span className="font-mono font-bold tracking-tight text-lg shadow-sm">AgentTrader</span>
      </div>

      <div className="flex-1 max-w-md mx-6">
        <form onSubmit={handleSearch} className="relative group">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-foreground transition-colors" />
          <input 
            type="text" 
            placeholder="Search symbol (e.g. RELIANCE.NS, AAPL)..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full bg-background border border-border rounded-md pl-10 pr-4 py-1.5 text-sm font-mono focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-shadow text-foreground placeholder:text-muted-foreground/50"
          />
        </form>
      </div>

      <div className="flex items-center gap-4 bg-background px-3 py-1.5 rounded-md border border-border">
        <span className="font-mono font-bold text-cyan-400">{activeTicker}</span>
        <div className="w-[1px] h-4 bg-border"></div>
        <span className="font-mono text-sm">$---</span>
        <div className={`flex items-center gap-1 text-xs font-mono px-1.5 py-0.5 rounded ${priceChange >= 0 ? 'bg-success/15 text-success' : 'bg-destructive/15 text-destructive'}`}>
          {priceChange >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3"/>}
          <span>{Math.abs(priceChange)}%</span>
        </div>
      </div>
    </header>
  )
}
