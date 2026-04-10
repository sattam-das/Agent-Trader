/* ============================================================
   AgentTrader v3 — Trading Terminal Application
   ============================================================ */

const API = window.location.origin;
let activeTicker = '';
let mainChart = null;
let rsiChart = null;
let macdChart = null;

// ------------------------------------------------------------------
// Clock
// ------------------------------------------------------------------
function updateClock() {
    const now = new Date();
    const el = document.getElementById('clock');
    if (el) el.textContent = now.toLocaleTimeString('en-IN', { hour12: true });
}
setInterval(updateClock, 1000);
updateClock();

// ------------------------------------------------------------------
// Tab switching
// ------------------------------------------------------------------
function switchTab(tab) {
    document.querySelectorAll('.module-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`)?.classList.add('active');
    document.getElementById(`tab-${tab}`)?.classList.add('active');

    // Lazy-load on tab switch
    if (tab === 'charts' && activeTicker) renderCharts(activeTicker);
    if (tab === 'news' && activeTicker) loadNews();
    if (tab === 'journal') loadJournal();
    if (tab === 'portfolio') loadPortfolio();
}

// ------------------------------------------------------------------
// Ticker selection
// ------------------------------------------------------------------
function selectTicker(raw) {
    const ticker = raw.trim().toUpperCase();
    if (!ticker) return;
    activeTicker = ticker;
    document.getElementById('nav-ticker').textContent = ticker;
    document.getElementById('search-input').value = '';
    document.getElementById('bt-ticker').value = ticker;

    // Load price
    fetchQuote(ticker);
    // Load charts if on charts tab
    const chartsTab = document.getElementById('tab-charts');
    if (chartsTab.classList.contains('active')) renderCharts(ticker);
}

async function fetchQuote(ticker) {
    try {
        const r = await fetch(`${API}/api/quote/${ticker}`);
        const d = await r.json();
        if (d.price) {
            const priceEl = document.getElementById('nav-price');
            const changeEl = document.getElementById('nav-change');
            const isINR = ticker.endsWith('.NS') || ticker.endsWith('.BO');
            const sym = isINR ? '₹' : '$';
            priceEl.textContent = `${sym}${d.price.toFixed(2)}`;
            if (d.change_pct !== undefined) {
                const cls = d.change_pct >= 0 ? 'positive' : 'negative';
                const arrow = d.change_pct >= 0 ? '▲' : '▼';
                changeEl.innerHTML = `<span class="badge badge-${d.change_pct >= 0 ? 'green' : 'red'}">${arrow} ${d.change_pct.toFixed(2)}%</span>`;
            }
        }
    } catch (e) { console.error('Quote fetch error:', e); }
}

// ------------------------------------------------------------------
// Charts (TradingView Lightweight Charts)
// ------------------------------------------------------------------
async function renderCharts(ticker) {
    try {
        const r = await fetch(`${API}/api/indicators/${ticker}`);
        const data = await r.json();
        if (data.error) { console.error(data.error); return; }

        renderCandlestick(data);
        renderRSI(data);
        renderMACD(data);
    } catch (e) { console.error('Chart render error:', e); }
}

function renderCandlestick(data) {
    const container = document.getElementById('tv-chart-container');
    container.innerHTML = '';

    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 480,
        layout: { background: { color: '#1a1f2e' }, textColor: '#94a3b8' },
        grid: { vertLines: { color: 'rgba(42,51,69,0.5)' }, horzLines: { color: 'rgba(42,51,69,0.5)' } },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        rightPriceScale: { borderColor: '#2a3345' },
        timeScale: { borderColor: '#2a3345', timeVisible: false },
    });

    const ph = data.price_history || [];
    if (!ph.length) return;

    // Candlestick
    const candlestick = chart.addCandlestickSeries({
        upColor: '#22c55e', downColor: '#ef4444',
        borderUpColor: '#22c55e', borderDownColor: '#ef4444',
        wickUpColor: '#22c55e', wickDownColor: '#ef4444',
    });
    candlestick.setData(ph.map(p => ({
        time: p.date, open: p.open, high: p.high, low: p.low, close: p.close
    })));

    // Volume
    const vol = chart.addHistogramSeries({
        priceFormat: { type: 'volume' },
        priceScaleId: '',
    });
    vol.priceScale().applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });
    vol.setData(ph.map(p => ({
        time: p.date, value: p.volume,
        color: p.close >= p.open ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'
    })));

    // SMA overlays
    const indicators = data.indicators || {};
    if (indicators.sma_20?.length) {
        const sma20 = chart.addLineSeries({ color: '#f59e0b', lineWidth: 1 });
        sma20.setData(buildLineSeries(ph, indicators.sma_20));
    }
    if (indicators.sma_50?.length) {
        const sma50 = chart.addLineSeries({ color: '#3b82f6', lineWidth: 1 });
        sma50.setData(buildLineSeries(ph, indicators.sma_50));
    }

    // Bollinger Bands
    if (indicators.bb_upper?.length) {
        const bbU = chart.addLineSeries({ color: 'rgba(168,85,247,0.4)', lineWidth: 1, lineStyle: 2 });
        bbU.setData(buildLineSeries(ph, indicators.bb_upper));
        const bbL = chart.addLineSeries({ color: 'rgba(168,85,247,0.4)', lineWidth: 1, lineStyle: 2 });
        bbL.setData(buildLineSeries(ph, indicators.bb_lower));
    }

    chart.timeScale().fitContent();
    mainChart = chart;

    // Resize observer
    new ResizeObserver(() => {
        chart.applyOptions({ width: container.clientWidth });
    }).observe(container);
}

function renderRSI(data) {
    const container = document.getElementById('rsi-chart');
    container.innerHTML = '';
    const indicators = data.indicators || {};
    const ph = data.price_history || [];
    if (!indicators.rsi_14?.length) return;

    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth, height: 180,
        layout: { background: { color: '#1a1f2e' }, textColor: '#94a3b8' },
        grid: { vertLines: { color: 'rgba(42,51,69,0.3)' }, horzLines: { color: 'rgba(42,51,69,0.3)' } },
        rightPriceScale: { borderColor: '#2a3345' },
        timeScale: { borderColor: '#2a3345', visible: false },
    });

    const rsi = chart.addLineSeries({ color: '#a855f7', lineWidth: 2, priceFormat: { precision: 1, minMove: 0.1 } });
    rsi.setData(buildLineSeries(ph, indicators.rsi_14));

    // Overbought/Oversold lines
    const ob = chart.addLineSeries({ color: 'rgba(239,68,68,0.4)', lineWidth: 1, lineStyle: 2 });
    ob.setData(ph.map(p => ({ time: p.date, value: 70 })));
    const os = chart.addLineSeries({ color: 'rgba(34,197,94,0.4)', lineWidth: 1, lineStyle: 2 });
    os.setData(ph.map(p => ({ time: p.date, value: 30 })));

    chart.timeScale().fitContent();
    rsiChart = chart;
    new ResizeObserver(() => chart.applyOptions({ width: container.clientWidth })).observe(container);
}

function renderMACD(data) {
    const container = document.getElementById('macd-chart');
    container.innerHTML = '';
    const indicators = data.indicators || {};
    const ph = data.price_history || [];
    if (!indicators.macd_line?.length) return;

    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth, height: 180,
        layout: { background: { color: '#1a1f2e' }, textColor: '#94a3b8' },
        grid: { vertLines: { color: 'rgba(42,51,69,0.3)' }, horzLines: { color: 'rgba(42,51,69,0.3)' } },
        rightPriceScale: { borderColor: '#2a3345' },
        timeScale: { borderColor: '#2a3345', visible: false },
    });

    const ml = chart.addLineSeries({ color: '#3b82f6', lineWidth: 2 });
    ml.setData(buildLineSeries(ph, indicators.macd_line));
    const sl = chart.addLineSeries({ color: '#f59e0b', lineWidth: 1 });
    sl.setData(buildLineSeries(ph, indicators.macd_signal));

    if (indicators.macd_histogram?.length) {
        const hist = chart.addHistogramSeries({});
        hist.setData(ph.map((p, i) => {
            const v = indicators.macd_histogram[i];
            if (v == null) return null;
            return { time: p.date, value: v, color: v >= 0 ? 'rgba(34,197,94,0.6)' : 'rgba(239,68,68,0.6)' };
        }).filter(Boolean));
    }

    chart.timeScale().fitContent();
    macdChart = chart;
    new ResizeObserver(() => chart.applyOptions({ width: container.clientWidth })).observe(container);
}

function buildLineSeries(priceHistory, values) {
    const result = [];
    for (let i = 0; i < priceHistory.length && i < values.length; i++) {
        if (values[i] != null) {
            result.push({ time: priceHistory[i].date, value: values[i] });
        }
    }
    return result;
}

// ------------------------------------------------------------------
// AI Analysis
// ------------------------------------------------------------------
async function runAnalysis() {
    if (!activeTicker) { showToast('Select a ticker first'); return; }
    const btn = document.getElementById('btn-analyze');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Analyzing...';

    try {
        const r = await fetch(`${API}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: activeTicker })
        });
        const data = await r.json();
        renderAnalysis(data);
    } catch (e) {
        document.getElementById('analysis-results').innerHTML =
            `<div class="card" style="color:var(--red)">Error: ${e.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🔍 Run AI Analysis';
    }
}

function renderAnalysis(data) {
    const result = data.result || {};
    const breakdown = result.score_breakdown || {};
    const rec = result.recommendation || 'N/A';
    const conv = result.conviction || 'N/A';
    const conf = (result.confidence || 0) * 100;

    const recColors = {
        'STRONG BUY': { bg: 'var(--green-dim)', color: 'var(--green)', icon: '🚀' },
        'BUY': { bg: 'var(--green-dim)', color: 'var(--green)', icon: '📈' },
        'HOLD': { bg: 'var(--amber-dim)', color: 'var(--amber)', icon: '⏸️' },
        'SELL': { bg: 'var(--red-dim)', color: 'var(--red)', icon: '📉' },
        'STRONG SELL': { bg: 'var(--red-dim)', color: 'var(--red)', icon: '🔻' },
    };
    const rc = recColors[rec] || { bg: 'var(--blue-dim)', color: 'var(--blue)', icon: '❓' };

    const html = `
        <div class="card" style="text-align:center;padding:24px">
            <div class="rec-badge-large" style="background:${rc.bg};color:${rc.color};margin:0 auto">
                ${rc.icon} ${rec} · ${conv} · ${conf.toFixed(0)}%
            </div>
        </div>
        <div class="metrics-grid">
            ${metricCard('News', breakdown.news_component, true)}
            ${metricCard('Financial', breakdown.financial_component, true)}
            ${metricCard('Risk', breakdown.risk_component, true)}
            ${metricCard('Technical', breakdown.technical_component, true)}
            ${metricCard('Macro', breakdown.macro_component, true)}
            ${metricCard('Confluence', breakdown.confluence_bonus, false, true)}
        </div>
        <div class="card">
            <div class="card-title">💡 Rationale</div>
            <ul style="padding-left:20px;color:var(--text-secondary);font-size:0.85rem;line-height:1.8">
                ${(result.rationale || []).map(r => `<li>${r}</li>`).join('')}
            </ul>
        </div>
        <div class="split-row">
            <div class="card">
                <div class="card-title">📰 News Summary</div>
                <p style="color:var(--text-secondary);font-size:0.85rem">${result.news_analysis?.summary || 'N/A'}</p>
            </div>
            <div class="card">
                <div class="card-title">💰 Financial Summary</div>
                <p style="color:var(--text-secondary);font-size:0.85rem">${result.financial_analysis?.summary || 'N/A'}</p>
            </div>
        </div>
    `;
    document.getElementById('analysis-results').innerHTML = html;
}

function metricCard(label, value, isScore = false, isSigned = false) {
    let display = value != null ? (isScore ? (value * 100).toFixed(0) + '%' : (value > 0 ? '+' : '') + (value * 100).toFixed(1) + '%') : 'N/A';
    let cls = 'neutral';
    if (isScore && value != null) cls = value >= 0.6 ? 'positive' : value <= 0.4 ? 'negative' : 'neutral';
    if (isSigned && value != null) cls = value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
    return `<div class="metric-card"><div class="metric-label">${label}</div><div class="metric-value ${cls}">${display}</div></div>`;
}

// ------------------------------------------------------------------
// Backtesting
// ------------------------------------------------------------------
async function runBacktest() {
    const ticker = document.getElementById('bt-ticker').value.trim().toUpperCase();
    const strategy = document.getElementById('bt-strategy').value;
    const period = document.getElementById('bt-period').value;
    const capital = parseFloat(document.getElementById('bt-capital').value) || 100000;

    if (!ticker) { showToast('Enter a ticker'); return; }

    const btn = document.getElementById('btn-backtest');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Running...';

    try {
        const r = await fetch(`${API}/api/backtest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, strategy, period, initial_capital: capital })
        });
        const data = await r.json();
        renderBacktestResults(data);
    } catch (e) {
        document.getElementById('backtest-results').innerHTML =
            `<div class="card" style="color:var(--red)">Error: ${e.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 Run Backtest';
    }
}

function renderBacktestResults(data) {
    if (data.error) {
        document.getElementById('backtest-results').innerHTML =
            `<div class="card" style="color:var(--red)">Error: ${data.error}</div>`;
        return;
    }

    const pct = (v) => (v * 100).toFixed(2) + '%';
    const html = `
        <div class="metrics-grid">
            ${btMetric('Total Return', pct(data.total_return), data.total_return)}
            ${btMetric('CAGR', pct(data.cagr), data.cagr)}
            ${btMetric('Sharpe', data.sharpe_ratio.toFixed(2), data.sharpe_ratio)}
            ${btMetric('Sortino', data.sortino_ratio.toFixed(2), data.sortino_ratio)}
            ${btMetric('Max Drawdown', pct(data.max_drawdown), data.max_drawdown)}
            ${btMetric('Win Rate', pct(data.win_rate), data.win_rate - 0.5)}
            ${btMetric('Trades', data.total_trades, 1)}
            ${btMetric('Profit Factor', data.profit_factor.toFixed(2), data.profit_factor - 1)}
            ${btMetric('Buy & Hold', pct(data.buy_hold_return), data.buy_hold_return)}
            ${btMetric('Excess Return', pct(data.excess_return), data.excess_return)}
            ${btMetric('Best Trade', pct(data.best_trade), data.best_trade)}
            ${btMetric('Worst Trade', pct(data.worst_trade), data.worst_trade)}
        </div>
        <div class="card">
            <div class="card-title">📈 Equity Curve</div>
            <div id="equity-chart" style="height:350px"></div>
        </div>
        <div class="card">
            <div class="card-title">📉 Drawdown</div>
            <div id="drawdown-chart" style="height:200px"></div>
        </div>
        ${data.trades?.length ? `
        <div class="card" style="padding:0;overflow:hidden">
            <div style="padding:16px;border-bottom:1px solid var(--border)">
                <div class="card-title" style="margin:0">Trade Log (${data.trades.length} trades)</div>
            </div>
            <div style="overflow-x:auto;max-height:400px">
                <table class="data-table">
                    <thead><tr><th>Entry</th><th>Exit</th><th>Entry ₹/$</th><th>Exit ₹/$</th><th>Shares</th><th>P&L</th><th>Return</th><th>Days</th></tr></thead>
                    <tbody>
                        ${data.trades.map(t => `
                            <tr>
                                <td>${t.entry_date}</td><td>${t.exit_date}</td>
                                <td>${t.entry_price}</td><td>${t.exit_price}</td>
                                <td>${t.shares}</td>
                                <td style="color:${t.pnl >= 0 ? 'var(--green)' : 'var(--red)'}">${t.pnl.toFixed(2)}</td>
                                <td style="color:${t.return_pct >= 0 ? 'var(--green)' : 'var(--red)'}">${(t.return_pct*100).toFixed(2)}%</td>
                                <td>${t.holding_days}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>` : ''}
    `;
    document.getElementById('backtest-results').innerHTML = html;

    // Render equity chart
    if (data.equity_curve?.length) {
        setTimeout(() => {
            const ec = document.getElementById('equity-chart');
            const ch = LightweightCharts.createChart(ec, {
                width: ec.clientWidth, height: 350,
                layout: { background: { color: '#1a1f2e' }, textColor: '#94a3b8' },
                grid: { vertLines: { color: 'rgba(42,51,69,0.3)' }, horzLines: { color: 'rgba(42,51,69,0.3)' } },
                rightPriceScale: { borderColor: '#2a3345' },
                timeScale: { borderColor: '#2a3345' },
            });
            const s = ch.addAreaSeries({ topColor: 'rgba(59,130,246,0.4)', bottomColor: 'rgba(59,130,246,0.02)', lineColor: '#3b82f6', lineWidth: 2 });
            s.setData(data.equity_curve.map(e => ({ time: e.date, value: e.equity })));
            ch.timeScale().fitContent();
            new ResizeObserver(() => ch.applyOptions({ width: ec.clientWidth })).observe(ec);
        }, 100);
    }

    // Render drawdown chart
    if (data.drawdown_series?.length) {
        setTimeout(() => {
            const dc = document.getElementById('drawdown-chart');
            const ch = LightweightCharts.createChart(dc, {
                width: dc.clientWidth, height: 200,
                layout: { background: { color: '#1a1f2e' }, textColor: '#94a3b8' },
                grid: { vertLines: { color: 'rgba(42,51,69,0.3)' }, horzLines: { color: 'rgba(42,51,69,0.3)' } },
                rightPriceScale: { borderColor: '#2a3345' },
                timeScale: { borderColor: '#2a3345' },
            });
            const s = ch.addAreaSeries({ topColor: 'rgba(239,68,68,0.02)', bottomColor: 'rgba(239,68,68,0.3)', lineColor: '#ef4444', lineWidth: 1 });
            s.setData(data.drawdown_series.map(d => ({ time: d.date, value: d.drawdown * 100 })));
            ch.timeScale().fitContent();
            new ResizeObserver(() => ch.applyOptions({ width: dc.clientWidth })).observe(dc);
        }, 150);
    }
}

function btMetric(label, display, value) {
    let cls = 'neutral';
    if (typeof value === 'number') cls = value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
    return `<div class="metric-card"><div class="metric-label">${label}</div><div class="metric-value ${cls}">${display}</div></div>`;
}

// ------------------------------------------------------------------
// News
// ------------------------------------------------------------------
async function loadNews() {
    const ticker = activeTicker || 'market';
    const container = document.getElementById('news-container');
    container.innerHTML = '<div class="loading-overlay"><span class="spinner"></span> Loading news...</div>';

    try {
        const r = await fetch(`${API}/api/news/${ticker}`);
        const data = await r.json();
        const articles = data.articles || [];

        if (!articles.length) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📰</div><div class="empty-state-text">No news found</div></div>';
            return;
        }

        container.innerHTML = articles.map(a => {
            const sentColor = a.sentiment === 'positive' ? 'green' : a.sentiment === 'negative' ? 'red' : 'amber';
            return `
                <div class="news-card" onclick="window.open('${a.url || '#'}','_blank')">
                    <div class="news-meta">
                        <span class="news-source">${a.source || 'News'}</span>
                        <span class="badge badge-${sentColor}">${a.sentiment || 'neutral'}</span>
                        <span class="news-time">${a.time || ''}</span>
                    </div>
                    <div class="news-title">${a.title || 'Untitled'}</div>
                </div>
            `;
        }).join('');
    } catch (e) {
        container.innerHTML = `<div class="card" style="color:var(--red);padding:20px">Error loading news: ${e.message}</div>`;
    }
}

// ------------------------------------------------------------------
// Screener
// ------------------------------------------------------------------
async function runScreener() {
    const preset = document.getElementById('scr-preset').value;
    const filter = document.getElementById('scr-filter').value;
    const btn = document.getElementById('btn-screener');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Scanning...';

    try {
        const r = await fetch(`${API}/api/screener?preset=${preset}&filter=${filter}`);
        const data = await r.json();
        renderScreenerResults(data);
    } catch (e) {
        document.getElementById('screener-results').innerHTML =
            `<div class="card" style="color:var(--red)">Error: ${e.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🔍 Scan';
    }
}

function renderScreenerResults(data) {
    const results = data.results || [];
    if (!results.length) {
        document.getElementById('screener-results').innerHTML =
            `<div class="card"><div class="empty-state"><div class="empty-state-icon">📈</div><div class="empty-state-text">No stocks match this filter. Try a different market or filter.</div></div></div>`;
        return;
    }

    const html = `
        <div class="card" style="padding:0;overflow:hidden">
            <div style="padding:16px;border-bottom:1px solid var(--border)">
                <div class="card-title" style="margin:0">Results (${results.length} matches)</div>
            </div>
            <table class="data-table">
                <thead><tr><th>Ticker</th><th>Signal</th><th>Value</th><th>Price</th><th>Change</th><th></th></tr></thead>
                <tbody>
                    ${results.map(r => `
                        <tr>
                            <td style="font-weight:700;color:var(--cyan);cursor:pointer" onclick="selectTicker('${r.ticker}')">${r.ticker}</td>
                            <td><span class="badge badge-blue">${r.signal}</span></td>
                            <td>${r.value}</td>
                            <td>${r.price}</td>
                            <td style="color:${r.change_pct >= 0 ? 'var(--green)' : 'var(--red)'}">${r.change_pct}%</td>
                            <td><button class="btn btn-outline btn-sm" onclick="selectTicker('${r.ticker}');switchTab('charts')">📊</button></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>`;
    document.getElementById('screener-results').innerHTML = html;
}

// ------------------------------------------------------------------
// Journal
// ------------------------------------------------------------------
async function loadJournal() {
    try {
        const [trR, stR] = await Promise.all([
            fetch(`${API}/api/journal`),
            fetch(`${API}/api/journal/stats`)
        ]);
        const trades = await trR.json();
        const stats = await stR.json();
        renderJournalStats(stats);
        renderJournalTable(trades);
    } catch (e) { console.error('Journal load error:', e); }
}

function renderJournalStats(stats) {
    if (!stats.total_trades) {
        document.getElementById('journal-stats').innerHTML = '';
        return;
    }
    document.getElementById('journal-stats').innerHTML = `
        ${btMetric('Total Trades', stats.total_trades, 1)}
        ${btMetric('Win Rate', (stats.win_rate * 100).toFixed(1) + '%', stats.win_rate - 0.5)}
        ${btMetric('Total P&L', stats.total_pnl.toFixed(2), stats.total_pnl)}
        ${btMetric('Avg Return', (stats.avg_return * 100).toFixed(2) + '%', stats.avg_return)}
        ${btMetric('Best Trade', (stats.best_trade * 100).toFixed(2) + '%', stats.best_trade)}
        ${btMetric('Worst Trade', (stats.worst_trade * 100).toFixed(2) + '%', stats.worst_trade)}
    `;
}

function renderJournalTable(trades) {
    const tbody = document.querySelector('#journal-table tbody');
    if (!trades.length) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:var(--text-dim);padding:30px">No trades logged yet</td></tr>';
        return;
    }
    tbody.innerHTML = trades.map(t => `
        <tr>
            <td style="font-weight:600">${t.ticker}</td>
            <td><span class="badge badge-${t.side === 'LONG' ? 'green' : 'red'}">${t.side}</span></td>
            <td>${t.entry_price}</td>
            <td>${t.exit_price || '—'}</td>
            <td>${t.shares}</td>
            <td style="color:${(t.pnl||0) >= 0 ? 'var(--green)' : 'var(--red)'}">${t.pnl != null ? t.pnl.toFixed(2) : '—'}</td>
            <td style="color:${(t.return_pct||0) >= 0 ? 'var(--green)' : 'var(--red)'}">${t.return_pct != null ? (t.return_pct*100).toFixed(2)+'%' : '—'}</td>
            <td><span class="badge badge-${t.status === 'OPEN' ? 'amber' : 'blue'}">${t.status}</span></td>
            <td>
                ${t.status === 'OPEN' ? `<button class="btn btn-sm btn-danger" onclick="closeJournalTrade(${t.id})">Close</button>` : ''}
                <button class="btn btn-sm btn-outline" onclick="deleteJournalTrade(${t.id})">×</button>
            </td>
        </tr>
    `).join('');
}

async function addJournalEntry() {
    const ticker = document.getElementById('j-ticker').value.trim().toUpperCase();
    const side = document.getElementById('j-side').value;
    const entry = parseFloat(document.getElementById('j-entry').value);
    const shares = parseInt(document.getElementById('j-shares').value);
    const date = document.getElementById('j-date').value;

    if (!ticker || !entry || !shares || !date) { showToast('Fill all fields'); return; }

    await fetch(`${API}/api/journal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, side, entry_price: entry, shares, entry_date: date })
    });
    showToast('Trade logged ✅');
    loadJournal();
}

async function closeJournalTrade(id) {
    const exitPrice = prompt('Enter exit price:');
    if (!exitPrice) return;
    await fetch(`${API}/api/journal/${id}/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exit_price: parseFloat(exitPrice), exit_date: new Date().toISOString().split('T')[0] })
    });
    showToast('Trade closed ✅');
    loadJournal();
}

async function deleteJournalTrade(id) {
    if (!confirm('Delete this trade?')) return;
    await fetch(`${API}/api/journal/${id}`, { method: 'DELETE' });
    loadJournal();
}

// ------------------------------------------------------------------
// Portfolio
// ------------------------------------------------------------------
async function loadPortfolio() {
    try {
        const r = await fetch(`${API}/api/portfolio`);
        const holdings = await r.json();
        renderPortfolioTable(holdings);
    } catch (e) { console.error('Portfolio load error:', e); }
}

function renderPortfolioTable(holdings) {
    const tbody = document.querySelector('#portfolio-table tbody');
    if (!holdings.length) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-dim);padding:30px">No holdings added yet</td></tr>';
        return;
    }
    tbody.innerHTML = holdings.map(h => {
        const value = h.shares * h.avg_price;
        return `
            <tr>
                <td style="font-weight:600;color:var(--cyan);cursor:pointer" onclick="selectTicker('${h.ticker}')">${h.ticker}</td>
                <td>${h.shares}</td>
                <td>${h.avg_price.toFixed(2)}</td>
                <td>—</td>
                <td>${value.toFixed(2)}</td>
                <td>—</td>
                <td>—</td>
                <td><button class="btn btn-sm btn-outline" onclick="removePortfolioHolding(${h.id})">×</button></td>
            </tr>
        `;
    }).join('');
}

async function addPortfolioHolding() {
    const ticker = document.getElementById('p-ticker').value.trim().toUpperCase();
    const shares = parseFloat(document.getElementById('p-shares').value);
    const price = parseFloat(document.getElementById('p-price').value);
    if (!ticker || !shares || !price) { showToast('Fill all fields'); return; }

    await fetch(`${API}/api/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, shares, avg_price: price })
    });
    showToast('Holding added ✅');
    loadPortfolio();
}

async function removePortfolioHolding(id) {
    if (!confirm('Remove this holding?')) return;
    await fetch(`${API}/api/portfolio/${id}`, { method: 'DELETE' });
    loadPortfolio();
}

// ------------------------------------------------------------------
// Watchlist
// ------------------------------------------------------------------
async function loadWatchlist() {
    try {
        const r = await fetch(`${API}/api/watchlist`);
        const items = await r.json();
        renderWatchlist(items);
    } catch (e) { console.error('Watchlist load error:', e); }
}

function renderWatchlist(items) {
    const container = document.getElementById('watchlist-container');
    if (!items.length) {
        container.innerHTML = '<div style="padding:20px 0;text-align:center;font-size:0.8rem;color:var(--text-dim)">Add tickers below</div>';
        return;
    }
    container.innerHTML = items.map(item => `
        <div class="watchlist-item ${item.ticker === activeTicker ? 'active' : ''}" onclick="selectTicker('${item.ticker}')">
            <span class="wl-ticker">${item.ticker.replace('.NS','').replace('.BO','')}</span>
            <div class="wl-price">
                <div id="wl-p-${item.ticker.replace('.','_')}" style="font-size:0.8rem">···</div>
            </div>
        </div>
    `).join('');

    // Fetch prices for each
    items.forEach(item => fetchWatchlistPrice(item.ticker));
}

async function fetchWatchlistPrice(ticker) {
    try {
        const r = await fetch(`${API}/api/quote/${ticker}`);
        const d = await r.json();
        const el = document.getElementById(`wl-p-${ticker.replace('.','_')}`);
        if (el && d.price) {
            const isINR = ticker.endsWith('.NS') || ticker.endsWith('.BO');
            const chg = d.change_pct || 0;
            el.innerHTML = `
                <div>${isINR?'₹':'$'}${d.price.toFixed(2)}</div>
                <div class="wl-change ${chg >= 0 ? 'positive' : 'negative'}">${chg >= 0 ? '▲' : '▼'} ${Math.abs(chg).toFixed(2)}%</div>
            `;
        }
    } catch (e) { /* silent */ }
}

async function addToWatchlist(ticker) {
    const t = ticker || document.getElementById('add-ticker-input').value.trim().toUpperCase();
    if (!t) return;
    document.getElementById('add-ticker-input').value = '';

    await fetch(`${API}/api/watchlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: t })
    });
    loadWatchlist();
    if (!activeTicker) selectTicker(t);
}

// ------------------------------------------------------------------
// Toast
// ------------------------------------------------------------------
function showToast(msg) {
    const t = document.createElement('div');
    t.className = 'toast';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3000);
}

// ------------------------------------------------------------------
// Init
// ------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    loadWatchlist();
    // Set today's date as default for journal
    const dateInput = document.getElementById('j-date');
    if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];
});
