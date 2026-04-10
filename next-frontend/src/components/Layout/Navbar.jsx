import React, { useState, useEffect, useRef } from 'react'
import { BrainCircuit, Search, TrendingUp, TrendingDown, Loader2 } from 'lucide-react'
import { useStore } from '@/store'
import { fetchQuote, searchTickers } from '@/api'

export default function Navbar() {
  const { activeTicker, setTicker, activeQuote, setActiveQuote } = useStore()
  const [searchInput, setSearchInput] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  const searchRef = useRef(null)
  const debounceRef = useRef(null)

  // Fetch live quote for active ticker
  useEffect(() => {
    let active = true
    const loadQuote = async () => {
      try {
        const q = await fetchQuote(activeTicker)
        if (active) setActiveQuote(q)
      } catch {
        if (active) setActiveQuote(null)
      }
    }
    loadQuote()
    // Refresh every 30 seconds
    const interval = setInterval(loadQuote, 30000)
    return () => { active = false; clearInterval(interval) }
  }, [activeTicker, setActiveQuote])

  // Search autocomplete
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (searchInput.trim().length < 1) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }
    debounceRef.current = setTimeout(async () => {
      setSearchLoading(true)
      try {
        const result = await searchTickers(searchInput.trim())
        setSuggestions(result.results || [])
        setShowSuggestions(true)
      } catch {
        setSuggestions([])
      } finally {
        setSearchLoading(false)
      }
    }, 300)
    return () => clearTimeout(debounceRef.current)
  }, [searchInput])

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleSelect = (symbol) => {
    setTicker(symbol)
    setSearchInput('')
    setShowSuggestions(false)
    setSuggestions([])
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchInput.trim()) {
      setTicker(searchInput.trim())
      setSearchInput('')
      setShowSuggestions(false)
    }
  }

  const price = activeQuote?.price
  const changePct = activeQuote?.change_pct ?? 0

  return (
    <header className="h-[52px] border-b border-border bg-card flex items-center justify-between px-6 shrink-0 z-20 w-full fixed top-0">
      <div className="flex items-center gap-2">
        <BrainCircuit className="w-5 h-5 text-primary" />
        <span className="font-mono font-bold tracking-tight text-lg shadow-sm">AgentTrader</span>
        <span className="text-xs font-mono px-1.5 py-0.5 bg-primary/10 text-primary rounded ml-1">v3.1</span>
      </div>

      {/* Search with Autocomplete */}
      <div className="flex-1 max-w-md mx-6 relative" ref={searchRef}>
        <form onSubmit={handleSearch} className="relative group">
          {searchLoading ? (
            <Loader2 className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-primary animate-spin" />
          ) : (
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-foreground transition-colors" />
          )}
          <input
            type="text"
            placeholder="Search symbol (e.g. RELIANCE.NS, AAPL)..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            className="w-full bg-background border border-border rounded-md pl-10 pr-4 py-1.5 text-sm font-mono focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-shadow text-foreground placeholder:text-muted-foreground/50"
          />
        </form>

        {/* Suggestions Dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-card border border-border rounded-lg shadow-2xl overflow-hidden z-50 max-h-[320px] overflow-y-auto custom-scrollbar animate-fade-in">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSelect(s.symbol)}
                className="w-full text-left px-4 py-2.5 hover:bg-primary/10 transition-colors flex items-center justify-between gap-3 border-b border-border/30 last:border-0"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="text-sm">{s.flag}</span>
                  <div className="min-w-0">
                    <div className="font-mono font-bold text-sm text-foreground">{s.symbol}</div>
                    <div className="text-xs text-muted-foreground truncate">{s.name}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-muted-foreground/60 font-mono">{s.exchange}</span>
                  <span className="text-xs text-muted-foreground/40 px-1.5 py-0.5 bg-secondary rounded">{s.type}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Active Ticker Quote */}
      <div className="flex items-center gap-4 bg-background px-3 py-1.5 rounded-md border border-border">
        <span className="font-mono font-bold text-cyan-400">{activeTicker}</span>
        <div className="w-[1px] h-4 bg-border"></div>
        <span className="font-mono text-sm">
          {price != null ? (activeTicker.endsWith('.NS') || activeTicker.endsWith('.BO') ? '₹' : '$') + price.toFixed(2) : '—'}
        </span>
        <div className={`flex items-center gap-1 text-xs font-mono px-1.5 py-0.5 rounded ${changePct >= 0 ? 'bg-success/15 text-success' : 'bg-destructive/15 text-destructive'}`}>
          {changePct >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3"/>}
          <span>{Math.abs(changePct).toFixed(2)}%</span>
        </div>
      </div>
    </header>
  )
}
