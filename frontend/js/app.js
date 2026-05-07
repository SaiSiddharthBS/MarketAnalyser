/**
 * Agent Alpha — Main Application Logic
 */
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    updateMarketStatus();
    loadDashboard();
    loadSegments();
    loadMarketRegime();
    setInterval(updateMarketStatus, 60000);
    setInterval(loadMarketRegime, 300000); // Refresh every 5 min
});

async function loadMarketRegime() {
    try {
        const res = await fetch('/api/market/regime');
        const d = await res.json();
        const bar = document.getElementById('regime-bar');
        const txt = document.getElementById('regime-text');
        if (bar && txt) {
            if (d.status && d.status !== 'UNKNOWN') {
                bar.style.borderColor = d.color;
                txt.innerHTML = `${d.emoji} Market Regime: <strong style="color:${d.color}">${d.status}</strong> 
                    <span style="margin:0 12px;opacity:0.5">|</span> VIX: ${d.vix || 'N/A'} (${d.vix_level}) 
                    <span style="margin:0 12px;opacity:0.5">|</span> Nifty: ${d.nifty_trend}
                    <span style="margin:0 12px;opacity:0.5">|</span> <span style="font-style:italic">${d.message}</span>`;
            } else {
                bar.style.borderColor = '#6b7280';
                txt.innerHTML = `⚪ Market Regime: <strong style="color:#6b7280">UNKNOWN</strong> <span style="margin:0 12px;opacity:0.5">|</span> <span style="font-style:italic">Data: ${JSON.stringify(d)}</span>`;
            }
        }
    } catch(e) {
        const txt = document.getElementById('regime-text');
        if (txt) {
            txt.innerHTML = `⚪ Error Loading Regime: ${e.message}`;
        }
    }
}

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
        rotation: () => {},
        accuracy: loadAccuracy,
        watchlist: loadWatchlist,
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
    
    // Check for holidays (YYYY-MM-DD)
    const holidays2026 = [
        '2026-01-26', // Republic Day
        '2026-03-03', // Maha Shivaratri
        '2026-03-20', // Holi
        '2026-04-03', // Good Friday
        '2026-04-14', // Ambedkar Jayanti
        '2026-05-01', // Maharashtra Day
        '2026-08-15', // Independence Day
        '2026-09-17', // Ganesh Chaturthi
        '2026-10-02', // Gandhi Jayanti
        '2026-10-20', // Dussehra
        '2026-11-09', // Diwali
        '2026-12-25'  // Christmas
    ];
    
    // Format current date as YYYY-MM-DD
    const dateStr = now.getFullYear() + '-' + 
                    String(now.getMonth() + 1).padStart(2, '0') + '-' + 
                    String(now.getDate()).padStart(2, '0');
    
    const isHoliday = holidays2026.includes(dateStr);
    const isTradingHours = day >= 1 && day <= 5 && time >= 555 && time <= 930; // 9:15-15:30
    const isOpen = isTradingHours && !isHoliday;

    const dot = document.querySelector('.status-dot');
    const text = document.querySelector('.market-status span:last-child');
    if (dot && text) {
        dot.className = `status-dot ${isOpen ? 'open' : 'closed'}`;
        text.textContent = isHoliday ? 'Market Closed (Holiday)' : (isOpen ? 'Market Open' : 'Market Closed');
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
    const selector = document.getElementById('segment-selector');
    const segment = selector ? selector.value : 'NIFTY_50';
    const segName = selector ? selector.options[selector.selectedIndex].text : 'Nifty 50';

    if (btn) btn.disabled = true;
    if (info) info.innerHTML = `<span class="spinner"></span> Analysing ${segName}... This may take 1-3 minutes`;

    const data = await api.getScreenerTop(50, segment);

    if (btn) btn.disabled = false;

    if (!data || !data.stocks || data.stocks.length === 0) {
        if (info) info.innerHTML = data?.error ? `⚠️ ${data.error}` : '⚠️ No results. <button class="btn btn-primary" style="padding:4px 12px;font-size:12px" onclick="runScreener()">Retry</button>';
        return;
    }

    if (info) info.textContent = `${data.segment_name || segment}: ${data.count} stocks analysed`;

    const signalLabels = data.signal_labels || {};
    const tbody = document.getElementById('screener-table-body');
    if (!tbody) return;

    tbody.innerHTML = data.stocks.map((s, i) => {
        const scoreClass = s.score >= 80 ? 'score-strong-buy' : s.score >= 60 ? 'score-high' : s.score >= 45 ? 'score-mid' : s.score >= 25 ? 'score-weak' : 'score-low';
        const signalLabel = signalLabels[s.signal] || s.signal.replace('_', ' ');
        let signalClass = 'signal-watch';
        if (s.signal === 'EARLY_MOMENTUM') signalClass = 'signal-early';
        else if (s.signal === 'CONTINUATION') signalClass = 'signal-cont';
        else if (s.signal === 'EXTENDED') signalClass = 'signal-extended';
        else if (s.signal === 'PULLBACK') signalClass = 'signal-pullback';
        else if (s.signal === 'WEAK') signalClass = 'signal-weak';
        else if (s.signal === 'AVOID') signalClass = 'negative';

        const riskPerShare = s.entry - s.stop_loss;
        const recQty = riskPerShare > 0 ? Math.floor((500000 * 0.01) / riskPerShare) : 0;
        
        return `
            <tr style="cursor:pointer" onclick="analyseFromScreener('${s.symbol}')">
                <td>${i + 1}</td>
                <td><strong>${s.symbol}</strong></td>
                <td>₹${formatNumber(s.price)}</td>
                <td><span class="score-badge ${scoreClass}">${s.score}</span></td>
                <td class="${signalClass}" style="font-weight:600">${signalLabel}</td>
                <td>${s.indicators.rsi || '-'}</td>
                <td>${s.rvol || '-'}x</td>
                <td>
                    <div>${s.risk_reward || '-'}</div>
                    <div style="font-size:10px; color:var(--text-muted); margin-top:2px;">[R: <span class="positive">+${s.reward_pct || 0}%</span> | L: <span class="negative">-${s.risk_pct || 0}%</span>]</div>
                </td>
                <td>₹${formatNumber(s.entry)}</td>
                <td class="positive">₹${formatNumber(s.target)}</td>
                <td class="negative">₹${formatNumber(s.stop_loss)}</td>
                <td>${recQty}</td>
                <td class="holding-label">${s.holding_period || '-'}</td>
            </tr>
        `;
    }).join('');
}

// Load segment dropdown on page init
async function loadSegments() {
    try {
        const res = await fetch('/api/screener/segments');
        const segments = await res.json();
        const selector = document.getElementById('segment-selector');
        if (selector && segments.length) {
            selector.innerHTML = '<option value="ALL_SECTORS">🔥 All Sectors — Top Picks</option>' +
                segments.map(s =>
                    `<option value="${s.key}">${s.name} (${s.count})</option>`
                ).join('');
        }
    } catch (e) {
        console.error('Failed to load segments:', e);
    }
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
    const signalColors = { 
        EARLY_MOMENTUM: '#06b6d4', // Cyan
        CONTINUATION: '#f59e0b',   // Orange/Amber
        EXTENDED: '#f43f5e',       // Red/Pink
        PULLBACK: '#3b82f6',       // Blue
        WEAK: '#f97316',           // Orange
        AVOID: '#ef4444'           // Red
    };
    const signalEmojis = { 
        EARLY_MOMENTUM: '🚀', 
        CONTINUATION: '🔥', 
        EXTENDED: '⚠️', 
        PULLBACK: '👀', 
        WEAK: '🟠', 
        AVOID: '🔴' 
    };
    const sigColor = signalColors[t.signal] || '#64748b';
    const sigEmoji = signalEmojis[t.signal] || '⚫';

    // Position sizing (default ₹5L capital, 1% risk)
    const riskPerShare = t.entry - t.stop_loss;
    const recQty = riskPerShare > 0 ? Math.floor((500000 * 0.01) / riskPerShare) : 0;
    const capitalNeeded = recQty * t.entry;

    // Score breakdown bars
    const bd = t.score_breakdown || {};
    const breakdownHTML = [
        { label: 'Trend', val: bd.trend || 0, max: 25 },
        { label: 'Volume', val: bd.volume || 0, max: 20 },
        { label: 'RSI', val: bd.rsi || 0, max: 15 },
        { label: 'Sector', val: bd.sector || 0, max: 15 },
        { label: 'Regime', val: bd.regime || 0, max: 15 },
        { label: 'R/R', val: bd.risk_reward || 0, max: 10 },
    ].map(b => `
        <div class="breakdown-row">
            <span class="bd-label">${b.label}</span>
            <div class="bd-bar-wrap"><div class="bd-bar" style="width:${(b.val/b.max)*100}%;background:${sigColor}"></div></div>
            <span class="bd-val">${b.val}/${b.max}</span>
        </div>
    `).join('');

    container.innerHTML = `
        <div class="glass-card" style="border-top:3px solid ${sigColor}">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px">
                <div>
                    <h2 style="font-size:24px;margin-bottom:4px">${info.name || symbol}</h2>
                    <span style="color:var(--text-muted);font-size:13px">${info.sector || ''} • ${info.industry || ''}</span>
                </div>
                <div style="text-align:right">
                    <div style="font-size:32px;font-weight:700;font-family:var(--font-mono)">₹${formatNumber(t.price)}</div>
                    <div style="font-size:18px;font-weight:700;color:${sigColor}">${sigEmoji} ${t.signal.replace(/_/g, ' ')} (${t.score}/100)</div>
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
                <div class="signal-metric">
                    <div class="label">R/R Ratio</div>
                    <div class="value">${t.risk_reward || '—'}:1</div>
                </div>
                <div class="signal-metric">
                    <div class="label">RVOL</div>
                    <div class="value">${t.rvol || '—'}x</div>
                </div>
                <div class="signal-metric">
                    <div class="label">Holding</div>
                    <div class="value">${t.holding_period || '—'}</div>
                </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
                <div>
                    <h3 style="margin-bottom:12px">Score Breakdown</h3>
                    ${breakdownHTML}
                </div>
                <div>
                    <h3 style="margin-bottom:12px">📊 Position Sizing</h3>
                    <div style="font-size:14px;line-height:2">
                        <div>Recommended Qty: <strong>${recQty} shares</strong></div>
                        <div>Capital Needed: <strong>₹${formatNumber(capitalNeeded)}</strong></div>
                        <div>Max Risk: <strong class="negative">₹${formatNumber(recQty * riskPerShare)}</strong></div>
                        <div style="color:var(--text-muted);font-size:11px;margin-top:4px">Based on ₹5L capital, 1% risk per trade</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="glass-card">
            <h3>📈 Predicted Range & Accuracy</h3>
            <p style="font-size:11px;color:var(--text-muted);margin-bottom:12px">ATR-based intraday volatility estimate for the next trading session</p>
            
            <h4 style="margin-bottom:12px;color:var(--text-muted);font-size:12px;text-transform:uppercase;letter-spacing:1px">Prediction for Tomorrow</h4>
            <div class="signal-metrics">
                <div class="signal-metric">
                    <div class="label">Expected High</div>
                    <div class="value positive">₹${formatNumber(t.predicted_range?.high || 0)}</div>
                </div>
                <div class="signal-metric">
                    <div class="label">Expected Low</div>
                    <div class="value negative">₹${formatNumber(t.predicted_range?.low || 0)}</div>
                </div>
                <div class="signal-metric">
                    <div class="label">Support</div>
                    <div class="value">₹${formatNumber(t.predicted_range?.support || 0)}</div>
                </div>
                <div class="signal-metric">
                    <div class="label">Resistance</div>
                    <div class="value">₹${formatNumber(t.predicted_range?.resistance || 0)}</div>
                </div>
            </div>

            <div style="margin-top:24px;border-top:1px solid rgba(255,255,255,0.1);padding-top:16px">
                <h4 style="margin-bottom:12px;color:var(--text-muted);font-size:12px;text-transform:uppercase;letter-spacing:1px">Yesterday's Prediction vs Today's Reality</h4>
                ${data.recent_verification && data.recent_verification.actual_high ? `
                <table class="data-table" style="font-size:13px;width:100%;text-align:left">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Predicted</th>
                            <th>Actual</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding:8px">Peak (High)</td>
                            <td style="padding:8px">₹${formatNumber(data.recent_verification.pred_high)}</td>
                            <td style="padding:8px">₹${formatNumber(data.recent_verification.actual_high)}</td>
                            <td style="padding:8px">${data.recent_verification.actual_high <= data.recent_verification.pred_high ? '✅ Held' : '📈 Breached Up'}</td>
                        </tr>
                        <tr>
                            <td style="padding:8px">Floor (Low)</td>
                            <td style="padding:8px">₹${formatNumber(data.recent_verification.pred_low)}</td>
                            <td style="padding:8px">₹${formatNumber(data.recent_verification.actual_low)}</td>
                            <td style="padding:8px">${data.recent_verification.actual_low >= data.recent_verification.pred_low ? '✅ Held' : '📉 Breached Down'}</td>
                        </tr>
                        <tr>
                            <td style="padding:8px">Volatility Range</td>
                            <td style="padding:8px">₹${formatNumber(data.recent_verification.pred_high - data.recent_verification.pred_low)}</td>
                            <td style="padding:8px">₹${formatNumber(data.recent_verification.actual_high - data.recent_verification.actual_low)}</td>
                            <td style="padding:8px">—</td>
                        </tr>
                        <tr>
                            <td style="padding:8px">Daily Direction</td>
                            <td style="padding:8px">${data.recent_verification.pred_direction}</td>
                            <td style="padding:8px">${data.recent_verification.actual_close > data.recent_verification.actual_open ? 'Bullish' : (data.recent_verification.actual_close < data.recent_verification.actual_open ? 'Bearish' : 'Neutral')}</td>
                            <td style="padding:8px">${data.recent_verification.status.includes('Direction Hit') ? '✅ Accurate' : '❌ Missed'}</td>
                        </tr>
                    </tbody>
                </table>
                ` : `
                <div style="background:rgba(255,255,255,0.03);padding:16px;border-radius:8px;text-align:center;color:var(--text-muted);font-size:13px">
                    <span style="font-size:24px;display:block;margin-bottom:8px">⏳</span>
                    Prediction logged! Verification pending market close.<br>
                    <span style="font-size:11px;opacity:0.7">The accuracy table will appear here tomorrow once actual market data is available to grade today's prediction.</span>
                </div>
                `}
            </div>
        </div>

        <div class="glass-card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
                <h3>Price Chart</h3>
                <div id="chart-period-btns" style="display:flex;gap:4px">
                    <button class="btn-small" onclick="reloadChart('${symbol}','1d')">1D</button>
                    <button class="btn-small" onclick="reloadChart('${symbol}','5d')">1W</button>
                    <button class="btn-small" onclick="reloadChart('${symbol}','1mo')">1M</button>
                    <button class="btn-small" onclick="reloadChart('${symbol}','6mo')">6M</button>
                    <button class="btn-small active" onclick="reloadChart('${symbol}','1y')">1Y</button>
                    <button class="btn-small" onclick="reloadChart('${symbol}','5y')">5Y</button>
                    <button class="btn-small" onclick="reloadChart('${symbol}','max')">ALL</button>
                </div>
            </div>
            <div id="analysis-chart" class="chart-container" style="height:400px"></div>
        </div>

        <div class="glass-card" id="why-trade-panel">
            <h3>🧠 Why This Trade?</h3>
            <div id="why-trade-content"><span class="spinner"></span> Loading AI explanation...</div>
        </div>

        <div class="glass-card">
            <h3>📚 Understanding This Analysis</h3>
            <div class="legend-grid">
                ${t.signals.map(s => {
                    const icon = s.weight >= 10 ? '✅' : s.weight >= 5 ? '🟡' : '⚠️';
                    return `<div class="legend-item">
                        <span>${icon} <strong>${s.indicator}</strong>: ${s.signal}</span>
                        <span style="color:var(--text-muted)">+${s.weight} pts</span>
                    </div>`;
                }).join('')}
            </div>
            <div style="margin-top:16px;padding:12px;background:var(--bg-glass);border-radius:8px;font-size:12px;color:var(--text-muted);line-height:1.8">
                <strong>📖 Quick Guide:</strong><br>
                • <strong>RSI</strong> = Momentum (30-40 = oversold bounce, 70+ = overbought)<br>
                • <strong>MACD</strong> = Trend direction (bullish crossover = buying signal)<br>
                • <strong>EMA</strong> = Price above 20/50/200 EMA = stronger uptrend<br>
                • <strong>RVOL</strong> = Volume vs average (>1.5x = institutional interest)<br>
                • <strong>ATR</strong> = Volatility (higher = wider stop loss needed)<br>
                • <strong>R/R</strong> = Risk-Reward ratio (>2:1 = good trade setup)
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
    `;

    // Load chart
    const chartData = await api.getStockChart(symbol, '1y');
    if (chartData && chartData.data) {
        Charts.createCandlestickChart('analysis-chart', chartData.data);
    } else {
        document.getElementById('analysis-chart').innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted)">Chart data unavailable. Try a different timeframe.</div>';
    }

    // Load "Why This Trade?" (Native rendering from technical signals)
    const el = document.getElementById('why-trade-content');
    if (el && t.signals && t.signals.length > 0) {
        const reasonsHTML = t.signals.map(s => {
            const icon = s.weight >= 10 ? '✅' : s.weight >= 5 ? '🟡' : s.signal.includes('🚫') || s.signal.includes('❌') ? '🔴' : '⚠️';
            const color = s.weight >= 10 ? '#10b981' : s.weight >= 5 ? '#f59e0b' : s.signal.includes('🚫') || s.signal.includes('❌') ? '#ef4444' : '#f43f5e';
            return `<div style="margin-bottom:8px; display:flex; gap:12px; align-items:flex-start">
                <span style="font-size:16px">${icon}</span>
                <span style="font-size:14px; line-height:1.5">
                    <strong style="color:${color}">${s.indicator}</strong>: ${s.signal.replace('✅','').replace('❌','').replace('⚠️','').replace('🚫','')}
                </span>
            </div>`;
        }).join('');
        
        el.innerHTML = `
            <div style="background:rgba(255,255,255,0.02); padding:16px; border-radius:8px;">
                ${reasonsHTML}
            </div>
        `;
    } else if (el) {
        el.innerHTML = '<div style="color:var(--text-muted)">Explanation unavailable.</div>';
    }
}

async function reloadChart(symbol, period) {
    const chartDiv = document.getElementById('analysis-chart');
    if (chartDiv) chartDiv.innerHTML = '<div style="padding:40px;text-align:center"><span class="spinner"></span></div>';
    const chartData = await api.getStockChart(symbol, period);
    if (chartData && chartData.data && chartData.data.length > 0) {
        Charts.createCandlestickChart('analysis-chart', chartData.data);
    } else {
        if (chartDiv) chartDiv.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted)">No data for this period.</div>';
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

/* ─── Sector Rotation ───────────────────────────────── */
async function loadRotation() {
    const info = document.getElementById('rotation-info');
    const btn = document.getElementById('btn-load-rotation');
    if (btn) btn.disabled = true;
    if (info) info.innerHTML = '<span class="spinner"></span> Analysing all sectors...';

    try {
        const res = await fetch('/api/screener/rotation');
        const data = await res.json();

        if (btn) btn.disabled = false;
        if (!data || !data.sectors || data.sectors.length === 0) {
            if (info) info.textContent = '⚠️ Could not load sector data';
            return;
        }
        if (info) info.textContent = `${data.sectors.length} sectors analysed`;

        const heatmap = document.getElementById('sector-heatmap');
        heatmap.innerHTML = data.sectors.map(s => `
            <div class="sector-tile" style="border-left: 4px solid ${s.color}">
                <div class="sector-tile-header">
                    <span class="sector-name">${s.name}</span>
                    <span class="sector-class" style="color:${s.color}">${s.classification}</span>
                </div>
                <div class="sector-tile-stats">
                    <div><span class="stat-label">5D</span> <span class="${s.returns['5d'] >= 0 ? 'positive' : 'negative'}">${s.returns['5d']}%</span></div>
                    <div><span class="stat-label">10D</span> <span class="${s.returns['10d'] >= 0 ? 'positive' : 'negative'}">${s.returns['10d']}%</span></div>
                    <div><span class="stat-label">20D</span> <span class="${s.returns['20d'] >= 0 ? 'positive' : 'negative'}">${s.returns['20d']}%</span></div>
                    <div><span class="stat-label">RS</span> <span>${s.relative_strength}</span></div>
                    <div><span class="stat-label">Breadth</span> <span>${s.breadth}%</span></div>
                    <div><span class="stat-label">RVOL</span> <span>${s.rvol}x</span></div>
                </div>
                <button class="btn btn-small" onclick="scanSector('${s.key}')">🔍 Scan</button>
            </div>
        `).join('');
    } catch (e) {
        if (btn) btn.disabled = false;
        if (info) info.textContent = '⚠️ Error loading sectors';
    }
}

function scanSector(key) {
    switchPage('screener');
    const sel = document.getElementById('segment-selector');
    if (sel) { sel.value = key; }
    runScreener();
}

/* ─── Accuracy Dashboard ────────────────────────────── */
async function loadAccuracy() {
    try {
        const res = await fetch('/api/accuracy/stats');
        const d = await res.json();

        const el = (id, val) => { const e = document.getElementById(id); if (e) e.textContent = val; };
        el('acc-win-rate', d.win_rate ? `${d.win_rate}%` : 'No data yet');
        el('acc-total', d.total_signals || 0);
        el('acc-wins', d.hit_target || 0);
        el('acc-losses', d.hit_sl || 0);
        el('acc-open', d.still_open || 0);
        el('acc-avg-days', d.avg_holding_days || '—');

        // Average return
        const avgRetEl = document.getElementById('acc-avg-return');
        if (avgRetEl) avgRetEl.textContent = d.avg_return ? `${d.avg_return}%` : '—';

        // By signal type
        const sigEl = document.getElementById('acc-by-signal');
        if (d.by_signal_type && d.by_signal_type.length > 0) {
            sigEl.innerHTML = d.by_signal_type.map(s => `
                <div class="acc-row">
                    <span>${s.signal.replace('_', ' ')}</span>
                    <div class="acc-bar-wrap">
                        <div class="acc-bar" style="width:${s.win_rate}%;background:${s.win_rate >= 50 ? 'var(--accent-green)' : 'var(--accent-red)'}"></div>
                    </div>
                    <span>${s.win_rate}% (${s.wins}/${s.total})</span>
                </div>
            `).join('');
        } else {
            sigEl.innerHTML = '<div class="loading-skeleton">No evaluated signals yet. Data will appear as signals hit their targets or stop losses.</div>';
        }

        // By segment
        const segEl = document.getElementById('acc-by-segment');
        if (d.by_segment && d.by_segment.length > 0) {
            segEl.innerHTML = d.by_segment.map(s => `
                <div class="acc-row">
                    <span>${s.segment || 'Unknown'}</span>
                    <div class="acc-bar-wrap">
                        <div class="acc-bar" style="width:${s.win_rate}%;background:${s.win_rate >= 50 ? 'var(--accent-green)' : 'var(--accent-red)'}"></div>
                    </div>
                    <span>${s.win_rate}% (${s.wins}/${s.total})</span>
                </div>
            `).join('');
        } else {
            segEl.innerHTML = '<div class="loading-skeleton">No segment data yet.</div>';
        }

        // Signal history table
        const logEl = document.getElementById('acc-signal-log');
        if (logEl && d.recent_signals && d.recent_signals.length > 0) {
            const outcomeColors = { hit_target: '#10b981', hit_sl: '#ef4444', open: '#f59e0b' };
            const outcomeLabels = { hit_target: '✅ Hit Target', hit_sl: '❌ Hit SL', open: '⏳ Open' };
            logEl.innerHTML = `<table class="data-table"><thead><tr>
                <th>Date</th><th>Symbol</th><th>Signal</th><th>Score</th><th>Entry</th><th>Target</th><th>SL</th><th>Outcome</th><th>Days</th>
            </tr></thead><tbody>${d.recent_signals.map(s => `<tr>
                <td>${(s.date || '').substring(0, 10)}</td>
                <td><strong>${s.symbol}</strong></td>
                <td>${(s.signal || '').replace('_', ' ')}</td>
                <td>${s.score || '—'}</td>
                <td>₹${formatNumber(s.entry)}</td>
                <td class="positive">₹${formatNumber(s.target)}</td>
                <td class="negative">₹${formatNumber(s.sl)}</td>
                <td style="color:${outcomeColors[s.outcome] || '#94a3b8'}">${outcomeLabels[s.outcome] || s.outcome}</td>
                <td>${s.days || '—'}</td>
            </tr>`).join('')}</tbody></table>`;
        } else if (logEl) {
            logEl.innerHTML = '<div class="loading-skeleton">Signals will appear here once the screener runs.</div>';
        }
    } catch (e) {
        console.error('Accuracy load error:', e);
    }
}

/* ─── Manual Portfolio Entry ────────────────────────── */
function toggleAddHolding() {
    const form = document.getElementById('add-holding-form');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

async function submitHolding() {
    const symbol = document.getElementById('new-symbol').value.trim().toUpperCase();
    const qty = parseFloat(document.getElementById('new-qty').value);
    const price = parseFloat(document.getElementById('new-price').value);
    const date = document.getElementById('new-date').value || new Date().toISOString().split('T')[0];
    const notes = document.getElementById('new-notes').value.trim();

    if (!symbol || !qty || !price) {
        alert('Please fill Symbol, Quantity, and Price');
        return;
    }

    try {
        const res = await fetch('/api/portfolio/holdings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol, quantity: qty, buy_price: price,
                buy_date: date, notes, asset_type: 'stock'
            })
        });
        const data = await res.json();
        if (data.success) {
            toggleAddHolding();
            document.getElementById('new-symbol').value = '';
            document.getElementById('new-qty').value = '';
            document.getElementById('new-price').value = '';
            document.getElementById('new-notes').value = '';
            loadPortfolio();
        } else {
            alert('Failed to add: ' + (data.error || 'Unknown error'));
        }
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

async function deleteHolding(id) {
    if (!confirm('Remove this holding?')) return;
    try {
        await fetch(`/api/portfolio/holdings/${id}`, { method: 'DELETE' });
        loadPortfolio();
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

/* ─── CSV Import/Export ─────────────────────────────── */
function exportCSV() {
    const rows = [];
    const table = document.getElementById('stock-table');
    if (!table) return;
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent);
    rows.push(headers.join(','));
    table.querySelectorAll('tbody tr').forEach(tr => {
        const cells = Array.from(tr.querySelectorAll('td')).map(td => td.textContent.replace(/[₹,]/g, ''));
        rows.push(cells.join(','));
    });
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `agent_alpha_portfolio_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
}

async function importCSV(event) {
    const file = event.target.files[0];
    if (!file) return;
    const text = await file.text();
    const lines = text.trim().split('\n');
    let imported = 0;
    for (let i = 1; i < lines.length; i++) {
        const parts = lines[i].split(',');
        if (parts.length >= 3) {
            const symbol = parts[0].trim().toUpperCase();
            const qty = parseFloat(parts[1]);
            const price = parseFloat(parts[2]);
            if (symbol && qty && price) {
                try {
                    await fetch('/api/portfolio/holdings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            symbol, quantity: qty, buy_price: price,
                            buy_date: new Date().toISOString().split('T')[0],
                            asset_type: 'stock'
                        })
                    });
                    imported++;
                } catch (e) { /* skip */ }
            }
        }
    }
    alert(`Imported ${imported} holdings from CSV`);
    event.target.value = '';
    loadPortfolio();
}

/* ─── Watchlist ──────────────────────────────────────── */
function getWatchlist() {
    try { return JSON.parse(localStorage.getItem('agent_alpha_watchlist') || '[]'); }
    catch(e) { return []; }
}
function saveWatchlist(list) {
    localStorage.setItem('agent_alpha_watchlist', JSON.stringify(list));
}

function addToWatchlist() {
    const input = document.getElementById('watchlist-input');
    if (!input) return;
    const sym = input.value.trim().toUpperCase();
    if (!sym) return;
    const list = getWatchlist();
    if (list.includes(sym)) { alert(sym + ' already in watchlist'); return; }
    list.push(sym);
    saveWatchlist(list);
    input.value = '';
    loadWatchlist();
}

function removeFromWatchlist(sym) {
    const list = getWatchlist().filter(s => s !== sym);
    saveWatchlist(list);
    loadWatchlist();
}

async function loadWatchlist() {
    const list = getWatchlist();
    const tbody = document.getElementById('watchlist-body');
    if (!tbody) return;
    if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7">Add stocks to your watchlist above</td></tr>';
        return;
    }
    tbody.innerHTML = '<tr><td colspan="7"><span class="spinner"></span> Loading watchlist...</td></tr>';

    const rows = [];
    for (const sym of list) {
        try {
            const res = await fetch(`/api/stock/${sym}`);
            const data = await res.json();
            const t = data.technical;
            if (t) {
                const pr = t.predicted_range || {};
                rows.push(`<tr style="cursor:pointer" onclick="analyseFromScreener('${sym}')">
                    <td><strong>${sym}</strong></td>
                    <td>₹${formatNumber(t.price)}</td>
                    <td>${t.score}</td>
                    <td>${t.signal.replace(/_/g,' ')}</td>
                    <td>${t.rvol || '-'}x</td>
                    <td>₹${formatNumber(pr.low||0)} - ₹${formatNumber(pr.high||0)}</td>
                    <td><button class="btn-small" onclick="event.stopPropagation();removeFromWatchlist('${sym}')">✕</button></td>
                </tr>`);
            } else {
                rows.push(`<tr><td><strong>${sym}</strong></td><td colspan="5">Data unavailable</td>
                    <td><button class="btn-small" onclick="removeFromWatchlist('${sym}')">✕</button></td></tr>`);
            }
        } catch(e) {
            rows.push(`<tr><td><strong>${sym}</strong></td><td colspan="5">Error loading</td>
                <td><button class="btn-small" onclick="removeFromWatchlist('${sym}')">✕</button></td></tr>`);
        }
    }
    tbody.innerHTML = rows.join('');
}
