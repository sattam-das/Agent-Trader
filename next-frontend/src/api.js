import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 120000,
})

// ── Analysis ──────────────────────────────────────────────────────
export const fetchAnalysis = async (ticker) => {
  const { data } = await api.post('/analyze', { ticker })
  return data
}

// ── Discovery ─────────────────────────────────────────────────────
export const fetchDiscover = async () => {
  const { data } = await api.get('/discover')
  return data
}

// ── Compare ───────────────────────────────────────────────────────
export const fetchCompare = async (tickers) => {
  const { data } = await api.post('/compare', { tickers })
  return data
}

// ── Quote ─────────────────────────────────────────────────────────
export const fetchQuote = async (ticker) => {
  const { data } = await api.get(`/api/quote/${ticker}`)
  return data
}

// ── Indicators ────────────────────────────────────────────────────
export const fetchIndicators = async (ticker) => {
  const { data } = await api.get(`/api/indicators/${ticker}`)
  return data
}

// ── News ──────────────────────────────────────────────────────────
export const fetchNews = async (ticker) => {
  const { data } = await api.get(`/api/news/${ticker}`)
  return data
}

// ── Search / Autocomplete ─────────────────────────────────────────
export const searchTickers = async (q) => {
  const { data } = await api.get('/api/search', { params: { q } })
  return data
}

// ── Backtest ──────────────────────────────────────────────────────
export const runBacktest = async (params) => {
  const { data } = await api.post('/api/backtest', params)
  return data
}

export const runNLBacktest = async (params) => {
  const { data } = await api.post('/api/nl-backtest', params)
  return data
}

export const fetchStrategies = async () => {
  const { data } = await api.get('/api/strategies')
  return data
}

// ── Screener ──────────────────────────────────────────────────────
export const fetchScreener = async (preset = 'nifty50', filter = 'rsi_oversold') => {
  const { data } = await api.get('/api/screener', { params: { preset, filter } })
  return data
}

export const fetchScreenerPresets = async () => {
  const { data } = await api.get('/api/screener/presets')
  return data
}

// ── Watchlist ─────────────────────────────────────────────────────
export const fetchWatchlist = async () => {
  const { data } = await api.get('/api/watchlist')
  return data
}

export const addWatchlist = async (ticker, notes = '') => {
  const { data } = await api.post('/api/watchlist', { ticker, notes })
  return data
}

export const removeWatchlist = async (ticker) => {
  const { data } = await api.delete(`/api/watchlist/${ticker}`)
  return data
}

// ── Journal ───────────────────────────────────────────────────────
export const fetchJournal = async (status) => {
  const params = status ? { status } : {}
  const { data } = await api.get('/api/journal', { params })
  return data
}

export const addJournal = async (trade) => {
  const { data } = await api.post('/api/journal', trade)
  return data
}

export const closeJournal = async (tradeId, exitPrice, exitDate) => {
  const { data } = await api.post(`/api/journal/${tradeId}/close`, {
    exit_price: exitPrice,
    exit_date: exitDate,
  })
  return data
}

export const deleteJournal = async (tradeId) => {
  const { data } = await api.delete(`/api/journal/${tradeId}`)
  return data
}

export const fetchJournalStats = async () => {
  const { data } = await api.get('/api/journal/stats')
  return data
}

// ── Portfolio ─────────────────────────────────────────────────────
export const fetchPortfolio = async () => {
  const { data } = await api.get('/api/portfolio')
  return data
}

export const addPortfolio = async (holding) => {
  const { data } = await api.post('/api/portfolio', holding)
  return data
}

export const removePortfolio = async (holdingId) => {
  const { data } = await api.delete(`/api/portfolio/${holdingId}`)
  return data
}

// ── Intelligence Hub ──────────────────────────────────────────────
export const fetchHeatmap = async (market = 'india') => {
  const { data } = await api.get('/api/heatmap', { params: { market } })
  return data
}

export const fetchSentiment = async (ticker) => {
  const { data } = await api.get(`/api/sentiment/${ticker}`)
  return data
}

export const fetchCalendar = async (days = 30) => {
  const { data } = await api.get('/api/calendar', { params: { days } })
  return data
}

export const fetchMarketPulse = async () => {
  const { data } = await api.get('/api/market-pulse')
  return data
}

export const calcPositionSize = async (params) => {
  const { data } = await api.post('/api/position-size', params)
  return data
}
