import React from 'react'
import Navbar from './Navbar'
import Sidebar from './Sidebar'
import TabBar from './TabBar'
import AIAnalysis from '../Analysis/AIAnalysis'
import { useStore } from '@/store'

export default function Shell() {
  const { activeTab, activeTicker } = useStore()

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      <Navbar />
      <Sidebar />
      <TabBar />
      <main className="fixed top-[94px] left-[280px] right-0 bottom-0 overflow-y-auto p-8 bg-background custom-scrollbar">
        <div className="max-w-[1400px] mx-auto w-full">
          {activeTab === 'analysis' ? (
            <AIAnalysis />
          ) : (
            <div className="animate-in fade-in duration-300">
              <h1 className="text-2xl font-sans text-foreground mb-6 font-semibold flex items-center gap-3">
                <span className="capitalize">{activeTab} Dashboard</span>
                <span className="text-xs font-mono px-2 py-0.5 bg-primary/20 text-primary uppercase rounded border border-primary/30 tracking-widest">{activeTicker}</span>
              </h1>
              
              <div className="p-12 border border-border border-dashed rounded-xl flex flex-col items-center justify-center text-center space-y-4 bg-card/10">
                <p className="text-muted-foreground">The <strong className="text-foreground">{activeTab}</strong> module for <strong className="text-cyan-400 font-mono">{activeTicker}</strong> is physically being built right now.</p>
                <p className="text-xs font-mono text-muted-foreground/60 p-2 bg-background/50 rounded border border-border leading-relaxed max-w-sm">
                  c:\Users\rishi\...\Agent-Trader\next-frontend
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
