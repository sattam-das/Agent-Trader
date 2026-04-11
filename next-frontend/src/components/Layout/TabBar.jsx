import React from 'react'
import { useStore } from '@/store'
import { LayoutDashboard, Lightbulb, Scale, Radar, LineChart, TestTube, Newspaper, Filter, BookOpen, Briefcase } from 'lucide-react'

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'discover', label: 'Discover', icon: Lightbulb },
  { id: 'compare', label: 'Compare', icon: Scale },
  { id: 'analysis', label: 'Analysis', icon: Radar },
  { id: 'charts', label: 'Charts', icon: LineChart },
  { id: 'backtest', label: 'Backtest', icon: TestTube },
  { id: 'news', label: 'News', icon: Newspaper },
  { id: 'screener', label: 'Screener', icon: Filter },
  { id: 'journal', label: 'Journal', icon: BookOpen },
]

export default function TabBar() {
  const { activeTab, setTab } = useStore()

  return (
    <div className="h-[52px] border-b border-white/5 bg-black/40 backdrop-blur-md flex items-center px-4 overflow-x-auto fixed top-[60px] left-[280px] right-0 z-10 select-none transition-all duration-300">
      <div className="flex items-center gap-2 min-w-max">
        {TABS.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-1.5 text-sm font-bold rounded-full transition-all duration-300 ${
                isActive 
                  ? 'bg-gradient-to-r from-primary to-primary/80 text-white shadow-[0_0_12px_rgba(139,92,246,0.3)]' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-white/5'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : ''}`} />
              {tab.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
