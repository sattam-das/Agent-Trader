import React, { useEffect, useRef, useState } from 'react'
import { fetchIndicators } from '@/api'
import { useStore } from '@/store'
import { createChart, CandlestickSeries, AreaSeries, LineSeries, HistogramSeries, ColorType, CrosshairMode } from 'lightweight-charts'
import { LineChart as LineChartIcon, Loader2, AlertTriangle, CandlestickChart, TrendingUp } from 'lucide-react'

export default function ChartsPanel() {
  const { activeTicker } = useStore()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('chart')
  const [chartStyle, setChartStyle] = useState('candlestick')
  const [showSMA, setShowSMA] = useState({ sma20: true, sma50: true, sma200: false })
  const [showVolume, setShowVolume] = useState(true)
  const chartContainerRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    let active = true
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const result = await fetchIndicators(activeTicker)
        if (active) setData(result)
      } catch (err) {
        if (active) setError(err.response?.data?.detail || err.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [activeTicker])

  // Build chart with lightweight-charts v5 API
  useEffect(() => {
    if (!data || activeTab !== 'chart' || !chartContainerRef.current) return

    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const container = chartContainerRef.current
    const priceHistory = data.price_history || []
    if (priceHistory.length === 0) return

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: '#0a0e1a' },
        textColor: '#8B95A5',
        fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#151c2e' },
        horzLines: { color: '#151c2e' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#0066FF44', width: 1, style: 2, labelBackgroundColor: '#0066FF' },
        horzLine: { color: '#0066FF44', width: 1, style: 2, labelBackgroundColor: '#0066FF' },
      },
      rightPriceScale: {
        borderColor: '#1a243d',
        scaleMargins: { top: 0.05, bottom: showVolume ? 0.25 : 0.05 },
      },
      timeScale: {
        borderColor: '#1a243d',
        timeVisible: false,
        rightOffset: 5,
        barSpacing: 6,
        minBarSpacing: 3,
      },
      width: container.clientWidth,
      height: container.clientHeight,
    })

    chartRef.current = chart

    const ohlcData = priceHistory.map(p => ({
      time: p.date,
      open: p.open,
      high: p.high,
      low: p.low,
      close: p.close,
    }))

    // v5 API: chart.addSeries(SeriesType, options)
    if (chartStyle === 'candlestick') {
      const mainSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#00DC82',
        downColor: '#FF4757',
        borderUpColor: '#00DC82',
        borderDownColor: '#FF4757',
        wickUpColor: '#00DC8288',
        wickDownColor: '#FF475788',
      })
      mainSeries.setData(ohlcData)
    } else {
      const mainSeries = chart.addSeries(AreaSeries, {
        topColor: '#0066FF40',
        bottomColor: '#0066FF05',
        lineColor: '#0066FF',
        lineWidth: 2,
      })
      mainSeries.setData(ohlcData.map(d => ({ time: d.time, value: d.close })))
    }

    // SMA overlays
    if (showSMA.sma20) {
      const sma = chart.addSeries(LineSeries, {
        color: '#FFB800',
        lineWidth: 1,
        crosshairMarkerVisible: false,
        priceLineVisible: false,
        lastValueVisible: false,
      })
      sma.setData(calcSMA(priceHistory, 20))
    }

    if (showSMA.sma50) {
      const sma = chart.addSeries(LineSeries, {
        color: '#00BFFF',
        lineWidth: 1,
        crosshairMarkerVisible: false,
        priceLineVisible: false,
        lastValueVisible: false,
      })
      sma.setData(calcSMA(priceHistory, 50))
    }

    if (showSMA.sma200) {
      const sma = chart.addSeries(LineSeries, {
        color: '#FF6B81',
        lineWidth: 1,
        crosshairMarkerVisible: false,
        priceLineVisible: false,
        lastValueVisible: false,
      })
      sma.setData(calcSMA(priceHistory, 200))
    }

    // Volume
    if (showVolume) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      })

      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
        drawTicks: false,
      })

      volumeSeries.setData(priceHistory.map(p => ({
        time: p.date,
        value: p.volume,
        color: p.close >= p.open ? '#00DC8233' : '#FF475733',
      })))
    }

    chart.timeScale().fitContent()

    const resizeObserver = new ResizeObserver(() => {
      if (chartRef.current && container) {
        chartRef.current.applyOptions({ width: container.clientWidth, height: container.clientHeight })
      }
    })
    resizeObserver.observe(container)

    return () => {
      resizeObserver.disconnect()
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
      }
    }
  }, [data, activeTab, chartStyle, showSMA, showVolume])

  const indicators = data?.indicators || {}
  const lastPrice = data?.price_history?.slice(-1)[0]

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-32 space-y-4 animate-fade-in">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
        <p className="text-sm text-muted-foreground font-mono">Loading chart for {activeTicker}...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 border border-destructive/50 bg-destructive/10 rounded-xl space-y-2 max-w-2xl mx-auto mt-12 animate-fade-in">
        <div className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="w-5 h-5" />
          <h3 className="font-bold">Chart Error</h3>
        </div>
        <p className="text-sm font-mono text-destructive/80">{error}</p>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-4 animate-fade-in pb-12">
      {/* Header */}
      <div className="bg-card border border-border p-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 border border-border bg-secondary text-primary flex items-center justify-center">
              <LineChartIcon className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold font-mono uppercase text-foreground">{activeTicker}</h1>
              {lastPrice && (
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-muted-foreground">O:{lastPrice.open?.toFixed(2)}</span>
                  <span className="text-muted-foreground">H:{lastPrice.high?.toFixed(2)}</span>
                  <span className="text-muted-foreground">L:{lastPrice.low?.toFixed(2)}</span>
                  <span className={`font-bold ${lastPrice.close >= lastPrice.open ? 'text-success' : 'text-destructive'}`}>
                    C:{lastPrice.close?.toFixed(2)}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex border border-border bg-secondary">
              <button onClick={() => setActiveTab('chart')}
                className={`px-4 py-2 text-xs font-mono transition-none flex items-center gap-1.5 border-r border-border last:border-r-0 ${activeTab === 'chart' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
                <CandlestickChart className="w-3.5 h-3.5" /> CHART
              </button>
              <button onClick={() => setActiveTab('indicators')}
                className={`px-4 py-2 text-xs font-mono transition-none flex items-center gap-1.5 border-r border-border last:border-r-0 ${activeTab === 'indicators' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
                <TrendingUp className="w-3.5 h-3.5" /> INDICATORS
              </button>
            </div>
          </div>
        </div>

        {activeTab === 'chart' && (
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border flex-wrap">
            <div className="flex border border-border bg-card">
              <button onClick={() => setChartStyle('candlestick')}
                className={`px-3 py-1.5 text-xs font-mono transition-none border-r border-border last:border-r-0 ${chartStyle === 'candlestick' ? 'bg-primary text-white' : 'bg-secondary text-muted-foreground'}`}>
                CANDLESTICK
              </button>
              <button onClick={() => setChartStyle('area')}
                className={`px-3 py-1.5 text-xs font-mono transition-none border-r border-border last:border-r-0 ${chartStyle === 'area' ? 'bg-primary text-white' : 'bg-secondary text-muted-foreground'}`}>
                AREA
              </button>
            </div>
            <div className="h-4 w-px bg-border/50" />
            <div className="flex gap-2">
              <Chip label="SMA 20" color="#FFB800" active={showSMA.sma20} onClick={() => setShowSMA(s => ({ ...s, sma20: !s.sma20 }))} />
              <Chip label="SMA 50" color="#00BFFF" active={showSMA.sma50} onClick={() => setShowSMA(s => ({ ...s, sma50: !s.sma50 }))} />
              <Chip label="SMA 200" color="#FF6B81" active={showSMA.sma200} onClick={() => setShowSMA(s => ({ ...s, sma200: !s.sma200 }))} />
            </div>
            <div className="h-4 w-px bg-border/50" />
            <Chip label="Volume" color="#0066FF" active={showVolume} onClick={() => setShowVolume(v => !v)} />
          </div>
        )}
      </div>

      {/* Chart */}
      {activeTab === 'chart' && (
        <div className="border border-border bg-[#0a0e1a] overflow-hidden" style={{ height: '520px' }}>
          <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />
        </div>
      )}

      {/* Indicators */}
      {activeTab === 'indicators' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <IndCard label="RSI (14)" value={indicators.rsi_14} fmt={v => v.toFixed(1)} color={indicators.rsi_14 > 70 ? '#FF4757' : indicators.rsi_14 < 30 ? '#00DC82' : '#0066FF'} />
            <IndCard label="SMA 20" value={indicators.sma_20} fmt={v => v.toFixed(2)} color="#FFB800" />
            <IndCard label="SMA 50" value={indicators.sma_50} fmt={v => v.toFixed(2)} color="#00BFFF" />
            <IndCard label="SMA 200" value={indicators.sma_200} fmt={v => v.toFixed(2)} color="#FF6B81" />
            <IndCard label="MACD" value={indicators.macd_line} fmt={v => v.toFixed(2)} color={indicators.macd_line >= 0 ? '#00DC82' : '#FF4757'} />
            <IndCard label="Signal" value={indicators.macd_signal} fmt={v => v.toFixed(2)} color="#8B95A5" />
            <IndCard label="ATR (14)" value={indicators.atr_14} fmt={v => v.toFixed(2)} color="#9B59B6" />
            <IndCard label="BB Width" value={indicators.bb_upper && indicators.bb_lower ? indicators.bb_upper - indicators.bb_lower : null} fmt={v => v.toFixed(2)} color="#E67E22" />
          </div>

          {indicators.rsi_14 !== undefined && (
            <div className="border border-border bg-card p-4">
              <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-3">RSI (14)</h3>
              <div className="flex items-center gap-4">
                <div className={`text-4xl font-mono font-bold ${indicators.rsi_14 > 70 ? 'text-destructive' : indicators.rsi_14 < 30 ? 'text-success' : 'text-primary'}`}>
                  {indicators.rsi_14.toFixed(1)}
                </div>
                <div className="flex-1">
                  <div className="w-full bg-secondary h-4 overflow-hidden relative border border-border">
                    <div className="absolute left-[30%] w-px h-full bg-success/60 z-10" />
                    <div className="absolute left-[70%] w-px h-full bg-destructive/60 z-10" />
                    <div className={`h-full transition-none ${indicators.rsi_14 > 70 ? 'bg-destructive' : indicators.rsi_14 < 30 ? 'bg-success' : 'bg-primary'}`}
                      style={{ width: `${Math.min(100, indicators.rsi_14)}%` }} />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-1 font-mono">
                    <span>Oversold</span><span>Neutral</span><span>Overbought</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Chip({ label, color, active, onClick }) {
  return (
    <button onClick={onClick}
      className={`px-3 py-1.5 text-[10px] border transition-none flex items-center tracking-widest uppercase gap-1.5 font-mono ${active ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground'}`}>
      <span className="w-2 h-2" style={{ backgroundColor: active ? color : '#334155' }} />
      {label}
    </button>
  )
}

function IndCard({ label, value, fmt, color }) {
  if (value === null || value === undefined) return null
  return (
    <div className="p-3 border border-border bg-card">
      <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold mb-1">{label}</p>
      <p className="text-xl font-mono font-bold" style={{ color }}>{fmt(value)}</p>
    </div>
  )
}

function calcSMA(priceHistory, period) {
  const result = []
  for (let i = period - 1; i < priceHistory.length; i++) {
    let sum = 0
    for (let j = i - period + 1; j <= i; j++) sum += priceHistory[j].close
    result.push({ time: priceHistory[i].date, value: sum / period })
  }
  return result
}
