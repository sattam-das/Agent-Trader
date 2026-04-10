import React from 'react'
import { useStore } from '@/store'
import { Lightbulb, Scale, Radar, LineChart, TestTube, Newspaper, Filter, BookOpen, Briefcase } from 'lucide-react'

const TABS = [
  { id: 'discover', label: 'Discover', icon: Lightbulb },
  { id: 'compare', label: 'Compare', icon: Scale },
  { id: 'analysis', label: 'Analysis', icon: Radar },
  { id: 'charts', label: 'Charts', icon: LineChart },
  { id: 'backtest', label: 'Backtest', icon: TestTube },
  { id: 'news', label: 'News', icon: Newspaper },
  { id: 'screener', label: 'Screener', icon: Filter },
  { id: 'journal', label: 'Journal', icon: BookOpen },
  { id: 'portfolio', label: 'Portfolio', icon: Briefcase },
]

export default function TabBar() {
  const { activeTab, setTab } = useStore()

  return (
    <div className="h-[42px] border-b border-border bg-card flex items-center px-2 overflow-x-auto fixed top-[52px] left-[280px] right-0 z-10 select-none">
      <div className="flex items-center gap-1 min-w-max">
        {TABS.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded transition-all ${
                isActive 
                  ? 'bg-secondary/80 text-foreground border border-border/80 shadow-sm' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary/40 border border-transparent'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-primary' : ''}`} />
              {tab.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
