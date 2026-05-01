/**
 * Agent Alpha — Main Application Logic
 */
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    updateMarketStatus();
    loadDashboard();
    setInterval(updateMarketStatus, 60000);
});

/* ─── Navigation ─────────────────────────────────────── */
function initNavigation() {
    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            switchPage(page);
            // Close mobile sidebar
            document.getElementById('sidebar').classList.remove('open');
        });
    });

    // Mobile menu
    const menuBtn = document.getElementById('menu-btn');
    if (menuBtn) {
        menuBtn.addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('open');
        });
    }

    // Button handlers
    setupButtonHandlers();
}

function switchPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

    const pageEl = document.getElementById(`page-${page}`);
    const navEl = document.getElementById(`nav-${page}`);
    if (pageEl) pageEl.classList.add('active');
    if (navEl) navEl.classList.add('active');

    // Load page data
    const loaders = {
        dashboard: loadDashboard,
        portfolio: loadPortfolio,
        paper: loadPaperTrading,
        screener: () => {},
        signals: loadSignals,
        analysis: () => {},
        news: loadFullNews,
    };
    if (loaders[page]) loaders[page]();
}

function setupButtonHandlers() {
    const handlers = {
        'btn-refresh-portfolio': loadPortfolio,
        'btn-run-screener': runScreener,
        'btn-generate-signals': generateSignals,
        'btn-analyse': () => analyseStock(document.getElementById('analysis-search').value.trim()),
        'btn-send-alert': sendTelegramAlert,
    };

    Object.entries(handlers).forEach(([id, fn]) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('click', fn);
    });

    // Paper Trading Buttons
    const btnBuy = document.getElementById('btn-paper-buy');
    const btnSell = document.getElementById('btn-paper-sell');
    if (btnBuy) btnBuy.addEventListener('click', () => executeTrade('BUY'));
    if (btnSell) btnSell.addEventListener('click', () => executeTrade('SELL'));

    const searchInput = document.getElementById('analysis-search');
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') analyseStock(searchInput.value.trim());
        });
    }
}

/* ─── Market Status ──────────────────────────────────── */
function updateMarketStatus() {
    const now = new Date();
    const hours = now.getHours();
    const mins = now.getMinutes();
    const day = now.getDay();
    const time = hours * 60 + mins;
    const isOpen = day >= 1 && day <= 5 && time >= 555 && time <= 930; // 9:15-15:30

    const dot = document.querySelector('.status-dot');
    const text = document.querySelector('.market-status span:last-child');
    if (dot && text) {
        dot.className = `status-dot ${isOpen ? 'open' : 'closed'}`;
        text.textContent = isOpen ? 'Market Open' : 'Market Closed';
    }

    const timeEl = document.getElementById('dashboard-time');
    if (timeEl) {
        timeEl.textContent = now.toLocaleDateString('en-IN', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    }
}

/* ─── Dashboard ──────────────────────────────────────── */
async function loadDashboard() {
    // Show loading state
    const grid = document.getElementById('indices-grid');
    if (grid) grid.innerHTML = '<div class="loading-skeleton"><span class="spinner"></span> Loading market data...</div>';

    const data = await api.getMarketOverview();
    if (!data) {
        if (grid) grid.innerHTML = '<div class="error-state"><p>⚠️ Could not load market data</p><button class="btn btn-primary" onclick="loadDashboard()">↻ Retry</button></div>';
        return;
    }

    renderIndices(data.indices);
    renderSentiment(data.sentiment);
    renderNewsItems(data.news, 'news-feed', 5);
    loadNiftyChart();

    // Auto-refresh every 5 minutes during market hours
    if (!window._dashboardRefreshTimer) {
        window._dashboardRefreshTimer = setInterval(() => {
            const now = new Date();
            const time = now.getHours() * 60 + now.getMinutes();
            const day = now.getDay();
            if (day >= 1 && day <= 5 && time >= 555 && time <= 930) {
                loadDashboard();
            }
        }, 300000);
    }
}

function renderIndices(indices) {
    const grid = document.getElementById('indices-grid');
    if (!grid || !indices) return;

    if (Object.keys(indices).length === 0) {
        grid.innerHTML = '<div class="index-card" style="grid-column: 1 / -1; text-align: center; color: var(--text-muted);"><div class="card-value" style="font-size: 16px;">Market Data Unavailable</div><div class="card-label">Market may be closed today, or data feed is temporarily offline.</div></div>';
        return;
    }

    const displayNames = {
        'NIFTY_50': 'Nifty 50', 'SENSEX': 'Sensex', 'NIFTY_BANK': 'Bank Nifty',
        'S&P_500': 'S&P 500', 'NASDAQ': 'Nasdaq', 'INDIA_VIX': 'India VIX',
        'GOLD_USD': 'Gold (USD)', 'CRUDE_OIL': 'Crude Oil', 'USD_INR': 'USD/INR',
    };

    grid.innerHTML = Object.entries(indices).map(([key, val]) => {
        const isPos = val.change >= 0;
        const cls = key === 'INDIA_VIX' ? (val.change >= 0 ? 'negative' : 'positive') : (isPos ? 'positive' : 'negative');
        return `
            <div class="index-card">
                <div class="card-label">${displayNames[key] || key}</div>
                <div class="card-value">${formatNumber(val.value)}</div>
                <div class="card-change ${cls}">
                    ${isPos ? '▲' : '▼'} ${Math.abs(val.change).toFixed(2)} (${Math.abs(val.change_pct).toFixed(2)}%)
                </div>
            </div>
        `;
    }).join('');
}

function renderSentiment(sentiment) {
    if (!sentiment) return;
    const scoreEl = document.getElementById('sentiment-score');
    const labelEl = document.getElementById('sentiment-label');
    const posBar = document.getElementById('sentiment-positive');
    const negBar = document.getElementById('sentiment-negative');
    const posPct = document.getElementById('pos-pct');
    const negPct = document.getElementById('neg-pct');

    if (scoreEl) scoreEl.textContent = (sentiment.score > 0 ? '+' : '') + sentiment.score.toFixed(3);
    if (labelEl) {
        labelEl.textContent = sentiment.label;
        labelEl.className = 'sentiment-label ' +
            (sentiment.label.includes('Bull') ? 'positive' : sentiment.label.includes('Bear') ? 'negative' : '');
    }
    if (posBar) posBar.style.width = sentiment.positive_pct + '%';
    if (negBar) negBar.style.width = sentiment.negative_pct + '%';
    if (posPct) posPct.textContent = sentiment.positive_pct;
    if (negPct) negPct.textContent = sentiment.negative_pct;
}

async function loadNiftyChart() {
    const container = document.getElementById('nifty-chart');
    if (container) container.innerHTML = '<div class="loading-skeleton"><span class="spinner"></span> Loading chart...</div>';
    
    try {
        const data = await api.getIndexData('^NSEI', '6mo');
        if (data && data.data && data.data.length > 0) {
            if (container) container.innerHTML = '';
            Charts.createAreaChart('nifty-chart', data.data, '#3b82f6');
        } else {
            if (container) container.innerHTML = '<div class="error-state"><p>Chart data unavailable for today.</p></div>';
        }
    } catch (e) {
        if (container) container.innerHTML = '<div class="error-state"><p>Chart data unavailable for today.</p></div>';
    }
}

/* ─── Portfolio ──────────────────────────────────────── */
async function loadPortfolio() {
    const data = await api.getPortfolio();
    if (!data) return;

    renderPortfolioSummary(data.summary);
    renderMfTable(data.mutual_funds);
    renderStockTable(data.stocks);
}

function renderPortfolioSummary(summary) {
    const grid = document.getElementById('portfolio-summary');
    if (!grid || !summary) return;

    const isPos = summary.total_returns >= 0;
    grid.innerHTML = `
        <div class="summary-card">
            <div class="card-label">Total Invested</div>
            <div class="card-value">₹${formatNumber(summary.total_invested)}</div>
        </div>
        <div class="summary-card">
            <div class="card-label">Current Value</div>
            <div class="card-value">₹${formatNumber(summary.total_current)}</div>
        </div>
        <div class="summary-card">
            <div class="card-label">Total Returns</div>
            <div class="card-value ${isPos ? 'positive' : 'negative'}">
                ${isPos ? '+' : ''}₹${formatNumber(summary.total_returns)}
            </div>
        </div>
        <div class="summary-card">
            <div class="card-label">Returns %</div>
            <div class="card-value ${isPos ? 'positive' : 'negative'}">
                ${isPos ? '+' : ''}${summary.total_returns_pct.toFixed(2)}%
            </div>
        </div>
    `;
}

function renderMfTable(mfData) {
    const tbody = document.getElementById('mf-table-body');
    if (!tbody || !mfData || !mfData.holdings) return;

    tbody.innerHTML = mfData.holdings.map(h => {
        const isPos = h.returns >= 0;
        return `
            <tr>
                <td style="font-family: var(--font-main); max-width: 250px;">${h.scheme_name || h.scheme_code}</td>
                <td>₹${formatNumber(h.invested)}</td>
                <td>₹${formatNumber(h.current_value)}</td>
                <td class="${isPos ? 'positive' : 'negative'}">${isPos ? '+' : ''}₹${formatNumber(h.returns_abs)}</td>
                <td class="${isPos ? 'positive' : 'negative'}">${isPos ? '+' : ''}${h.returns.toFixed(2)}%</td>
            </tr>
        `;
    }).join('');
}

function renderStockTable(stocks) {
    const tbody = document.getElementById('stock-table-body');
    if (!tbody) return;
    if (!stocks || stocks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted)">No stocks yet. Use the Screener to find opportunities! 🚀</td></tr>';
        return;
    }
    tbody.innerHTML = stocks.map(s => {
        const isPos = s.returns >= 0;
        return `
            <tr>
                <td>${s.symbol}</td>
                <td>${s.quantity}</td>
                <td>₹${s.buy_price}</td>
                <td>₹${s.ltp}</td>
                <td class="${isPos ? 'positive' : 'negative'}">${isPos ? '+' : ''}₹${formatNumber(s.returns)}</td>
            </tr>
        `;
    }).join('');
}

/* ─── Screener ───────────────────────────────────────── */
async function runScreener() {
    const btn = document.getElementById('btn-run-screener');
    const info = document.getElementById('screener-info');
    if (btn) btn.disabled = true;
    if (info) info.innerHTML = '<span class="spinner"></span> Analysing Nifty 50 stocks... This takes 1-2 minutes';

    const data = await api.getScreenerTop(50);

    if (btn) btn.disabled = false;

    if (!data || !data.stocks || data.stocks.length === 0) {
        if (info) info.innerHTML = data?.error ? `⚠️ ${data.error}` : '⚠️ No results. <button class="btn btn-primary" style="padding:4px 12px;font-size:12px" onclick="runScreener()">Retry</button>';
        return;
    }

    if (info) info.textContent = `Found ${data.count} stocks`;

    const tbody = document.getElementById('screener-table-body');
    if (!tbody) return;

    tbody.innerHTML = data.stocks.map((s, i) => {
        const scoreClass = s.score >= 60 ? 'score-high' : s.score >= 40 ? 'score-mid' : 'score-low';
        const signalClass = s.signal.includes('BUY') ? 'positive' : s.signal.includes('SELL') ? 'negative' : '';
        return `
            <tr style="cursor:pointer" onclick="analyseFromScreener('${s.symbol}')">
                <td>${i + 1}</td>
                <td><strong>${s.symbol}</strong></td>
                <td>₹${formatNumber(s.price)}</td>
                <td><span class="score-badge ${scoreClass}">${s.score}</span></td>
                <td class="${signalClass}">${s.signal.replace('_', ' ')}</td>
                <td>${s.indicators.rsi || '-'}</td>
                <td>₹${formatNumber(s.entry)}</td>
                <td class="positive">₹${formatNumber(s.target)}</td>
                <td class="negative">₹${formatNumber(s.stop_loss)}</td>
            </tr>
        `;
    }).join('');
}

function analyseFromScreener(symbol) {
    switchPage('analysis');
    document.getElementById('analysis-search').value = symbol;
    analyseStock(symbol);
}

/* ─── Signals ────────────────────────────────────────── */
async function loadSignals() {
    const data = await api.getSignals();
    if (!data || !data.signals || data.signals.length === 0) {
        document.getElementById('signals-grid').innerHTML =
            '<div class="loading-skeleton">No active signals. Click "Generate New" to analyse the market.</div>';
        return;
    }
    renderSignalCards(data.signals);
}

async function generateSignals() {
    const btn = document.getElementById('btn-generate-signals');
    if (btn) btn.disabled = true;
    document.getElementById('signals-grid').innerHTML = '<div class="loading-skeleton"><span class="spinner"></span> Generating signals...</div>';

    const data = await api.generateSignals();
    if (btn) btn.disabled = false;

    if (!data || !data.signals || data.signals.length === 0) {
        document.getElementById('signals-grid').innerHTML =
            '<div class="loading-skeleton">No strong signals found right now. Market may be sideways.</div>';
        return;
    }
    renderSignalCards(data.signals);
}

function renderSignalCards(signals) {
    const grid = document.getElementById('signals-grid');
    if (!grid) return;

    grid.innerHTML = signals.map(s => {
        const type = (s.signal || s.signal_type || '').toLowerCase();
        const cardClass = type.includes('buy') ? 'buy' : type.includes('sell') ? 'sell' : 'hold';
        const badgeClass = type.replace(/_/g, '-');
        const confidence = s.score || s.confidence || 50;
        const confColor = confidence >= 60 ? '#10b981' : confidence >= 40 ? '#f59e0b' : '#ef4444';

        return `
            <div class="signal-card ${cardClass}">
                <div class="signal-header">
                    <span class="signal-symbol">${s.symbol}</span>
                    <span class="signal-badge ${badgeClass}">${(s.signal || s.signal_type || '').replace(/_/g, ' ')}</span>
                </div>
                <div class="signal-metrics">
                    <div class="signal-metric">
                        <div class="label">Entry</div>
                        <div class="value">₹${formatNumber(s.entry || s.entry_price)}</div>
                    </div>
                    <div class="signal-metric">
                        <div class="label">Target</div>
                        <div class="value positive">₹${formatNumber(s.target || s.target_price)}</div>
                    </div>
                    <div class="signal-metric">
                        <div class="label">Stop Loss</div>
                        <div class="value negative">₹${formatNumber(s.stop_loss)}</div>
                    </div>
                </div>
                <div class="signal-confidence">
                    <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);margin-bottom:4px">
                        <span>Confidence</span><span style="color:${confColor}">${confidence}/100</span>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width:${confidence}%;background:${confColor}"></div>
                    </div>
                </div>
                ${s.reasoning ? `<div class="signal-reasoning">💡 ${s.reasoning}</div>` : ''}
            </div>
        `;
    }).join('');
}

/* ─── Paper Trading ──────────────────────────────────── */
async function loadPaperTrading() {
    const data = await api.getPaperPortfolio();
    if (!data) return;

    renderPaperMetrics(data.metrics);
    renderPaperPositions(data.positions);
}

function renderPaperMetrics(m) {
    const pnlEl = document.getElementById('paper-pnl');
    const feesEl = document.getElementById('paper-fees');
    if (pnlEl) {
        pnlEl.textContent = `₹${formatNumber(m.net_realized_pnl)}`;
        pnlEl.className = 'card-value ' + (m.net_realized_pnl >= 0 ? 'positive' : 'negative');
    }
    if (feesEl) feesEl.textContent = `₹${formatNumber(m.total_fees)}`;
}

function renderPaperPositions(positions) {
    const tbody = document.getElementById('paper-positions-body');
    if (!tbody) return;
    
    if (!positions || positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4">No active positions. Find a signal and trade! 🚀</td></tr>';
        return;
    }

    tbody.innerHTML = positions.map(p => `
        <tr>
            <td><strong>${p.symbol}</strong></td>
            <td>${p.quantity}</td>
            <td>₹${formatNumber(p.avg_price)}</td>
            <td>₹${formatNumber(p.invested)}</td>
        </tr>
    `).join('');
}

async function executeTrade(type) {
    const symbol = document.getElementById('paper-symbol').value.toUpperCase().trim();
    const quantity = parseFloat(document.getElementById('paper-qty').value);
    const price = parseFloat(document.getElementById('paper-price').value) || null;
    const msg = document.getElementById('paper-msg');

    if (!symbol || !quantity || quantity <= 0) {
        if (msg) msg.textContent = '❌ Please enter a valid symbol and quantity';
        return;
    }

    if (msg) msg.textContent = '⏳ Executing trade...';

    const result = await api.executePaperTrade({
        symbol,
        trade_type: type,
        quantity,
        price
    });

    if (result && result.status === 'ok') {
        if (msg) msg.textContent = `✅ ${type} ${quantity} ${symbol} at ₹${result.price.toFixed(2)}`;
        loadPaperTrading();
    } else {
        if (msg) msg.textContent = '❌ Trade failed. Check if symbol is valid.';
    }
}

/* ─── Stock Analysis ─────────────────────────────────── */
async function analyseStock(symbol) {
    if (!symbol) return;
    symbol = symbol.toUpperCase().trim();
    const container = document.getElementById('analysis-result');
    container.innerHTML = '<div class="loading-skeleton"><span class="spinner"></span> Analysing ' + symbol + '...</div>';

    const data = await api.getStockDetail(symbol);
    if (!data || !data.technical) {
        container.innerHTML = `<div class="glass-card"><p>Could not analyse ${symbol}. Check if the symbol is correct.</p></div>`;
        return;
    }

    const t = data.technical;
    const info = data.info || {};
    const scoreClass = t.score >= 60 ? 'positive' : t.score >= 40 ? '' : 'negative';

    container.innerHTML = `
        <div class="glass-card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
                <div>
                    <h2 style="font-size:24px;margin-bottom:4px">${info.name || symbol}</h2>
                    <span style="color:var(--text-muted);font-size:13px">${info.sector || ''} • ${info.industry || ''}</span>
                </div>
                <div style="text-align:right">
                    <div style="font-size:32px;font-weight:700;font-family:var(--font-mono)">₹${formatNumber(t.price)}</div>
                    <div class="${scoreClass}" style="font-size:18px;font-weight:600">${t.signal.replace(/_/g, ' ')} (${t.score}/100)</div>
                </div>
            </div>

            <div class="signal-metrics" style="margin-bottom:20px">
                <div class="signal-metric">
                    <div class="label">Entry</div>
                    <div class="value">₹${formatNumber(t.entry)}</div>
                </div>
                <div class="signal-metric">
                    <div class="label">Target</div>
                    <div class="value positive">₹${formatNumber(t.target)}</div>
                </div>
                <div class="signal-metric">
                    <div class="label">Stop Loss</div>
                    <div class="value negative">₹${formatNumber(t.stop_loss)}</div>
                </div>
            </div>

            <div style="margin-bottom:20px">
                <h3 style="margin-bottom:12px">Technical Indicators</h3>
                <div class="indicator-grid">
                    ${renderIndicator('RSI (14)', t.indicators.rsi, t.indicators.rsi < 30 ? 'positive' : t.indicators.rsi > 70 ? 'negative' : '')}
                    ${renderIndicator('MACD', t.indicators.macd)}
                    ${renderIndicator('MACD Signal', t.indicators.macd_signal)}
                    ${renderIndicator('MACD Hist', t.indicators.macd_histogram, t.indicators.macd_histogram > 0 ? 'positive' : 'negative')}
                    ${renderIndicator('EMA 20', t.indicators.ema_20)}
                    ${renderIndicator('EMA 50', t.indicators.ema_50)}
                    ${renderIndicator('EMA 200', t.indicators.ema_200)}
                    ${renderIndicator('BB Upper', t.indicators.bb_upper)}
                    ${renderIndicator('BB Lower', t.indicators.bb_lower)}
                    ${renderIndicator('ATR', t.indicators.atr)}
                    ${renderIndicator('ADX', t.indicators.adx)}
                    ${renderIndicator('Stoch %K', t.indicators.stoch_k)}
                </div>
            </div>

            <div>
                <h3 style="margin-bottom:12px">Signal Breakdown</h3>
                ${t.signals.map(s => `
                    <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border-glass);font-size:13px">
                        <span><strong>${s.indicator}</strong>: ${s.signal}</span>
                        <span class="${s.weight > 0 ? 'positive' : s.weight < 0 ? 'negative' : ''}">${s.weight > 0 ? '+' : ''}${s.weight}</span>
                    </div>
                `).join('')}
            </div>
        </div>

        ${info.pe_ratio ? `
        <div class="glass-card">
            <h3>Fundamentals</h3>
            <div class="indicator-grid">
                ${renderIndicator('P/E Ratio', info.pe_ratio)}
                ${renderIndicator('P/B Ratio', info.pb_ratio)}
                ${renderIndicator('ROE', info.roe ? (info.roe * 100).toFixed(1) + '%' : null)}
                ${renderIndicator('EPS', info.eps)}
                ${renderIndicator('Div Yield', info.dividend_yield ? (info.dividend_yield * 100).toFixed(2) + '%' : null)}
                ${renderIndicator('52W High', info.fifty_two_week_high)}
                ${renderIndicator('52W Low', info.fifty_two_week_low)}
                ${renderIndicator('Debt/Equity', info.debt_to_equity)}
            </div>
        </div>` : ''}

        <div class="glass-card">
            <h3>Price Chart (1 Year)</h3>
            <div id="analysis-chart" class="chart-container" style="height:400px"></div>
        </div>
    `;

    // Load chart
    const chartData = await api.getStockChart(symbol, '1y');
    if (chartData && chartData.data) {
        Charts.createCandlestickChart('analysis-chart', chartData.data);
    }

    // Load news
    if (data.news && data.news.length) {
        const newsHtml = `<div class="glass-card"><h3>Latest News</h3><div class="news-feed">${
            data.news.map(n => renderNewsItem(n)).join('')
        }</div></div>`;
        container.innerHTML += newsHtml;
    }
}

function renderIndicator(label, value, cls = '') {
    return `
        <div class="indicator-item">
            <div class="label">${label}</div>
            <div class="value ${cls}">${value != null ? (typeof value === 'number' ? value.toFixed(2) : value) : '—'}</div>
        </div>
    `;
}

/* ─── News ───────────────────────────────────────────── */
function renderNewsItems(articles, containerId, limit = 10) {
    const container = document.getElementById(containerId);
    if (!container || !articles) return;
    container.innerHTML = articles.slice(0, limit).map(a => renderNewsItem(a)).join('');
}

function renderNewsItem(a) {
    return `
        <div class="news-item">
            <div class="news-sentiment-dot ${a.sentiment}"></div>
            <div class="news-content">
                <div class="news-title"><a href="${a.link}" target="_blank" rel="noopener">${a.title}</a></div>
                <div class="news-meta">${a.source} • Score: ${a.sentiment_score?.toFixed(2) || '0.00'}</div>
            </div>
        </div>
    `;
}

async function loadFullNews() {
    const data = await api.getMarketOverview();
    if (data && data.news) {
        renderNewsItems(data.news, 'news-full', 20);
    }
}

/* ─── Helpers ────────────────────────────────────────── */
function formatNumber(n) {
    if (n == null) return '—';
    n = parseFloat(n);
    if (isNaN(n)) return '—';
    if (Math.abs(n) >= 10000000) return (n / 10000000).toFixed(2) + ' Cr';
    if (Math.abs(n) >= 100000) return (n / 100000).toFixed(2) + ' L';
    return n.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

async function sendTelegramAlert() {
    const btn = document.getElementById('btn-send-alert');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ Sending...';
    }
    
    const res = await api.sendTelegramAlert();
    
    if (btn) {
        btn.disabled = false;
        btn.textContent = res ? '✅ Sent!' : '❌ Failed';
        setTimeout(() => { btn.textContent = '📱 Send Telegram Alert'; }, 3000);
    }
}
