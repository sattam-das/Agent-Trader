import React from 'react'
import Navbar from './Navbar'
import Sidebar from './Sidebar'
import TabBar from './TabBar'
import AIAnalysis from '../Analysis/AIAnalysis'
import DiscoverPanel from '../Discover/DiscoverPanel'
import ComparePanel from '../Compare/ComparePanel'
import ChartsPanel from '../Charts/ChartsPanel'
import BacktestPanel from '../Backtest/BacktestPanel'
import NewsPanel from '../News/NewsPanel'
import ScreenerPanel from '../Screener/ScreenerPanel'
import JournalPanel from '../Journal/JournalPanel'
import PortfolioPanel from '../Portfolio/PortfolioPanel'
import { useStore } from '@/store'

const TAB_COMPONENTS = {
  discover: DiscoverPanel,
  compare: ComparePanel,
  analysis: AIAnalysis,
  charts: ChartsPanel,
  backtest: BacktestPanel,
  news: NewsPanel,
  screener: ScreenerPanel,
  journal: JournalPanel,
  portfolio: PortfolioPanel,
}

export default function Shell() {
  const { activeTab } = useStore()
  const ActiveComponent = TAB_COMPONENTS[activeTab] || AIAnalysis

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      <Navbar />
      <Sidebar />
      <TabBar />
      <main className="fixed top-[94px] left-[280px] right-0 bottom-0 overflow-y-auto p-8 bg-background custom-scrollbar">
        <div className="max-w-[1400px] mx-auto w-full">
          <ActiveComponent />
        </div>
      </main>
    </div>
  )
}
