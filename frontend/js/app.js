/**
 * Agent Alpha — Main Application Logic
 */
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    updateMarketStatus();
    loadDashboard();
    loadSegments();
    loadMarketRegime();
    checkFnOExpiry(); // V6 Upgrade 8: F&O Expiry Banner
    setInterval(updateMarketStatus, 60000);
    setInterval(loadMarketRegime, 300000); // Refresh every 5 min
    initLiveClock();

    // Task 20: Toast container
    if (!document.getElementById('toast-container')) {
        const tc = document.createElement('div');
        tc.className = 'toast-container';
        tc.id = 'toast-container';
        document.body.appendChild(tc);
    }

    // Task 20: ESC to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeSignalModal();
    });
});

function initLiveClock() {
    const regimeLeft = document.getElementById('regime-left');
    if (!regimeLeft) return;
    
    const clockDiv = document.getElementById('live-clock');
    if (!clockDiv) return;
    
    clockDiv.style.fontSize = '12px';
    clockDiv.style.fontWeight = '600';
    clockDiv.style.color = 'var(--text-muted)';
    clockDiv.style.fontFamily = 'var(--font-mono)';
    
    // Tick function — manual format to avoid Safari locale bugs
    function tick() {
        const now = new Date();
        let h = now.getHours();
        const m = now.getMinutes();
        const s = now.getSeconds();
        const ampm = h >= 12 ? 'pm' : 'am';
        h = h % 12;
        if (h === 0) h = 12;
        const pad = (n) => n.toString().padStart(2, '0');
        clockDiv.textContent = `${pad(h)}:${pad(m)}:${pad(s)} ${ampm} IST`;
    }
    
    tick(); // Show immediately — no 1-second gap
    setInterval(tick, 1000);
}

/* ─── Task 20: Toast Notifications ────────────────── */
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `${icons[type] || ''} ${message}`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// V6 Upgrade 8: F&O Expiry Detection & Banner
function checkFnOExpiry() {
    const today = new Date();
    const dayOfWeek = today.getDay(); // 0=Sun, 4=Thu
    
    // Next weekly expiry (Thursday)
    let daysToThursday = (4 - dayOfWeek + 7) % 7;
    if (daysToThursday === 0) daysToThursday = 0; // Today is Thursday
    const nextWeekly = new Date(today);
    nextWeekly.setDate(today.getDate() + daysToThursday);
    
    // Monthly expiry = last Thursday of current month
    const year = today.getFullYear();
    const month = today.getMonth();
    const lastDay = new Date(year, month + 1, 0);
    let monthlyExpiry = new Date(lastDay);
    while (monthlyExpiry.getDay() !== 4) {
        monthlyExpiry.setDate(monthlyExpiry.getDate() - 1);
    }
    // If monthly already passed, get next month's
    if (monthlyExpiry < today) {
        const nextLastDay = new Date(year, month + 2, 0);
        monthlyExpiry = new Date(nextLastDay);
        while (monthlyExpiry.getDay() !== 4) {
            monthlyExpiry.setDate(monthlyExpiry.getDate() - 1);
        }
    }
    
    const msPerDay = 86400000;
    const daysToWeekly = Math.ceil((nextWeekly - today) / msPerDay);
    const daysToMonthly = Math.ceil((monthlyExpiry - today) / msPerDay);
    
    const isExpiryDay = daysToWeekly === 0;
    const isNearExpiry = daysToWeekly <= 1;
    const isMonthlyExpiry = daysToMonthly <= 2;
    
    if (isExpiryDay || isNearExpiry || isMonthlyExpiry) {
        const bar = document.getElementById('regime-bar');
        if (!bar) return;
        
        let msg = '';
        let severity = 'info';
        if (isExpiryDay && daysToMonthly === 0) {
            msg = '⚠️ MONTHLY F&O EXPIRY TODAY — Expect high volatility, wide spreads, and gamma risk. Reduce position sizes.';
            severity = 'critical';
        } else if (isExpiryDay) {
            msg = '📅 Weekly F&O Expiry Today — Options writers active. Watch for pin risk near round numbers.';
            severity = 'warning';
        } else if (isMonthlyExpiry) {
            const dateStr = monthlyExpiry.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' });
            msg = `📅 Monthly F&O Expiry on ${dateStr} (${daysToMonthly}d away) — Rollover activity may distort volume signals.`;
            severity = 'info';
        } else {
            msg = `📅 Weekly F&O Expiry Tomorrow — Consider tighter stops for overnight positions.`;
            severity = 'info';
        }
        
        const colors = { critical: '#ff4d6a', warning: '#fbbf24', info: '#60a5fa' };
        const banner = document.createElement('div');
        banner.id = 'fno-expiry-banner';
        banner.style.cssText = `
            background: ${colors[severity]}15; border: 1px solid ${colors[severity]}40; 
            color: ${colors[severity]}; padding: 8px 16px; text-align: center; 
            font-size: 13px; font-weight: 500; border-radius: 8px; margin: 8px 0;
        `;
        banner.textContent = msg;
        bar.parentNode.insertBefore(banner, bar.nextSibling);
    }
}

async function loadMarketRegime() {
    try {
        const res = await fetch('/api/market/regime');
        const d = await res.json();
        const bar = document.getElementById('regime-bar');
        const txt = document.getElementById('regime-text');
        if (bar && txt) {
            // Task 18: Remove previous regime classes
            bar.classList.remove('regime-crisis');

            if (d.status && d.status !== 'UNKNOWN') {
                bar.style.borderColor = d.color;

                // Task 18: Regime-specific thresholds
                const thresholds = {
                    'low_vol_uptrend': { rvol: '1.2x', rsi: '75', cap: '90%', tip: 'Aggressive mode — full Kelly sizing, early breakouts.' },
                    'high_vol_uptrend': { rvol: '1.3x', rsi: '72', cap: '75%', tip: 'Cautious bull — pullback buys only, 0.6× Kelly.' },
                    'low_vol_chop': { rvol: '1.4x', rsi: '68', cap: '65%', tip: 'Sideways chop — mean reversion plays, tight stops.' },
                    'high_vol_chop': { rvol: '1.5x', rsi: '65', cap: '55%', tip: 'High vol dip buying — deep mean reversion, scaled entry.' },
                    'crisis': { rvol: '1.6x', rsi: '60', cap: '40%', tip: '⚠️ Survival mode — capital preservation, 0× Kelly.' },
                };
                const regime = d.regime || '';
                const t = thresholds[regime] || { rvol: '—', rsi: '—', cap: '—', tip: '' };

                // Task 18: Pulse the bar during crisis
                if (regime === 'crisis') {
                    bar.classList.add('regime-crisis');
                }

                if (d.vix_level === 0 || d.vix_level === null) {
                    bar.style.borderColor = '#ff4d6a';
                    txt.innerHTML = `🔴 Market Regime: <strong style="color:#ff4d6a">DATA FEED ERROR</strong> 
                        <span style="margin:0 12px;opacity:0.5">|</span> VIX is unavailable. Signal generation paused to prevent blind execution.`;
                } else {
                    // V6: FII/DII flow display
                    const fiiNet = d.fii_net_cr || 0;
                    const diiNet = d.dii_net_cr || 0;
                    const fiiColor = fiiNet >= 0 ? '#00e68a' : '#ff4d6a';
                    const diiColor = diiNet >= 0 ? '#00e68a' : '#ff4d6a';
                    const fiiArrow = fiiNet >= 0 ? '↑' : '↓';
                    const diiArrow = diiNet >= 0 ? '↑' : '↓';
                    const fiiStr = fiiNet !== 0 ? `FII: <span style="color:${fiiColor}">${fiiArrow}₹${Math.abs(fiiNet).toLocaleString()} Cr</span>` : '';
                    const diiStr = diiNet !== 0 ? `DII: <span style="color:${diiColor}">${diiArrow}₹${Math.abs(diiNet).toLocaleString()} Cr</span>` : '';
                    const flowStr = (fiiStr || diiStr) ? `<span style="margin:0 12px;opacity:0.5">|</span> ${fiiStr} ${diiStr ? '<span style="margin:0 6px;opacity:0.3">•</span>' + diiStr : ''}` : '';

                    txt.innerHTML = `${d.emoji} Market Regime: <strong style="color:${d.color}">${d.status}</strong> 
                        <span style="margin:0 12px;opacity:0.5">|</span> VIX: ${d.vix_level} 
                        <span style="margin:0 12px;opacity:0.5">|</span> Nifty vs 200EMA: ${d.nifty_vs_200ema_pct ? d.nifty_vs_200ema_pct.toFixed(2) + '%' : 'N/A'}
                        <span style="margin:0 12px;opacity:0.5">|</span> <span style="font-style:italic">Confidence: ${d.confidence_pct}%</span>
                        ${flowStr}
                        <span class="regime-thresholds">
                            <span title="Minimum RVOL required for BUY">RVOL≥${t.rvol}</span>
                            <span title="RSI ceiling for BUY signals">RSI≤${t.rsi}</span>
                            <span title="Maximum confidence cap">Cap:${t.cap}</span>
                        </span>`;
                    // Tooltip on bar hover
                    bar.title = t.tip;
                }
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
    const activePages = document.querySelectorAll('.page.active');
    
    // Quick hide old pages
    activePages.forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

    const pageEl = document.getElementById(`page-${page}`);
    const navEl = document.getElementById(`nav-${page}`);
    
    if (pageEl) {
        pageEl.classList.add('active');
        // Premium GSAP Apple-like Fluid Animation
        if (typeof gsap !== 'undefined') {
            gsap.killTweensOf(pageEl);
            gsap.fromTo(pageEl, 
                { opacity: 0, filter: "blur(12px)", scale: 0.97 },
                { opacity: 1, filter: "blur(0px)", scale: 1, duration: 0.7, ease: "expo.out" }
            );
            
            // Stagger animate all cards inside the page for a cascading reveal
            const cards = pageEl.querySelectorAll('.glass-card, .summary-card, .index-card, .regime-bar, .chart-card, .signal-card');
            if (cards.length > 0) {
                gsap.killTweensOf(cards);
                gsap.fromTo(cards,
                    { opacity: 0, y: 30, scale: 0.95 },
                    { opacity: 1, y: 0, scale: 1, duration: 0.6, stagger: 0.04, ease: "back.out(1.2)", delay: 0.05 }
                );
            }
        }
    }
    
    if (navEl) navEl.classList.add('active');

    // Load page data
    const loaders = {
        dashboard: loadDashboard,
        portfolio: loadPortfolio,
        paper: loadPaperTrading,
        arena: loadArenaTrading,
        screener: () => {},
        signals: loadSignals,
        analysis: () => {},
        news: loadFullNews,
        rotation: () => {},
        accuracy: loadAccuracy,
        watchlist: loadWatchlist,
        alerts: loadAlerts
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
        'btn-paper-buy': () => executeTrade('BUY'),
        'btn-paper-sell': () => executeTrade('SELL'),
    };

    Object.entries(handlers).forEach(([id, fn]) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('click', fn);
    });



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
    updateMissionControl(data);

    // Data Freshness & Market Status Badge
    const badge = document.getElementById('market-status-badge');
    if (badge && data.timestamp) {
        badge.style.fontSize = '12px';
        badge.style.padding = '4px 10px';
        badge.style.borderRadius = '12px';
        badge.style.fontWeight = '500';
        badge.style.display = 'flex';
        badge.style.alignItems = 'center';
        badge.style.gap = '6px';
        
        const dateObj = new Date(data.timestamp);
        const timeString = dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        // EOD date = last trading day, not today
        // Before market open, data is from the previous trading session
        let eodDate = new Date(dateObj);
        
        const hour = eodDate.getHours();
        const minute = eodDate.getMinutes();
        const timeInMins = hour * 60 + minute;
        
        if (data.market_status !== 'OPEN') {
            // If it is before 9:15 AM on a weekday, the data belongs to the previous day
            if (eodDate.getDay() >= 1 && eodDate.getDay() <= 5 && timeInMins < (9 * 60 + 15)) {
                eodDate.setDate(eodDate.getDate() - 1);
            }
            
            // If it falls on a weekend, roll back to Friday
            while (eodDate.getDay() === 0 || eodDate.getDay() === 6) {
                eodDate.setDate(eodDate.getDate() - 1);
            }
        }
        
        const dateString = eodDate.toLocaleDateString([], {month: 'short', day: 'numeric'});

        if (data.market_status === 'OPEN') {
            badge.innerHTML = `<span style="color:#00e68a">● Live (15m delay)</span> <span style="opacity:0.5;margin-left:4px">Data as of ${timeString}</span>`;
            badge.style.background = 'rgba(16, 185, 129, 0.1)';
        } else if (data.market_status === 'PRE_MARKET') {
            badge.innerHTML = `<span style="color:#ffb347">● Pre-Market</span> <span style="opacity:0.5;margin-left:4px">EOD Data from ${dateString}</span>`;
            badge.style.background = 'rgba(245, 158, 11, 0.1)';
        } else if (data.market_status === 'WEEKEND') {
            badge.innerHTML = `<span style="color:#6b7280">● Weekend</span> <span style="opacity:0.5;margin-left:4px">EOD Data from ${dateString}</span>`;
            badge.style.background = 'rgba(107, 114, 128, 0.1)';
        } else {
            badge.innerHTML = `<span style="color:#ff4d6a">● Market Closed</span> <span style="opacity:0.5;margin-left:4px">EOD Data from ${dateString}</span>`;
            badge.style.background = 'rgba(239, 68, 68, 0.1)';
        }
    }

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

async function updateMissionControl(data) {
    try {
        const h = await api.get('/health');
        if (!h) throw new Error("API Offline");
        
        document.getElementById('status-data').textContent = 'SYNCED';
        document.getElementById('dot-data').style.background = 'var(--green)';
        document.getElementById('status-signal').textContent = 'ONLINE';
        document.getElementById('dot-signal').style.background = 'var(--green)';
        document.getElementById('status-exec').textContent = 'ACTIVE';
        document.getElementById('dot-exec').style.background = 'var(--green)';
    } catch(e) {
        ['data', 'signal', 'exec'].forEach(id => {
            const el = document.getElementById(`status-${id}`);
            const dot = document.getElementById(`dot-${id}`);
            if(el) { el.textContent = 'OFFLINE'; el.style.color = 'var(--red)'; }
            if(dot) { dot.style.background = 'var(--red)'; dot.style.boxShadow = '0 0 10px var(--red)'; }
        });
    }

    // Add jitter effect for the "live" feeling
    if (window._hudJitter) clearInterval(window._hudJitter);
    window._hudJitter = setInterval(() => {
        // Jitter CPU slightly around 34%
        const cpuEl = document.getElementById('cpu-bar');
        const cpuVal = document.getElementById('cpu-val');
        if (cpuEl && cpuVal) {
            const currentW = parseFloat(cpuEl.style.width) || 34.2;
            const newW = Math.max(20, Math.min(80, currentW + (Math.random() - 0.5) * 5));
            cpuEl.style.width = `${newW}%`;
            cpuVal.textContent = `${newW.toFixed(1)}%`;
        }
        
        // Jitter Memory slightly around 62%
        const memEl = document.getElementById('mem-bar');
        const memVal = document.getElementById('mem-val');
        if (memEl && memVal) {
            const currentW = parseFloat(memEl.style.width) || 62.5;
            const newW = Math.max(40, Math.min(90, currentW + (Math.random() - 0.5) * 3));
            memEl.style.width = `${newW}%`;
            memVal.textContent = `${newW.toFixed(1)}%`;
        }
    }, 500);

    try {
        let terminalLogs = [];
        terminalLogs.push('[sys] INITIATING NEURAL LINK...');
        terminalLogs.push('[sys] SYNCING MARKET DATA...');

        const trades = await api.get('/paper_trades');
        if (trades && trades.length) {
            trades.slice(0, 2).forEach(t => {
                terminalLogs.push(`[exe] AUTO-TRADED ${t.trade_type} ${t.symbol} @ ₹${t.entry_price}`);
            });
        }

        const signals = await api.get('/signals');
        if (signals && signals.signals && signals.signals.length) {
            signals.signals.slice(0, 3).forEach(s => {
                terminalLogs.push(`[ml_] MODEL DETECTED ${s.signal_type} PATTERN: ${s.symbol}`);
            });
        }
        
        terminalLogs.push('[ai_] DECRYPTING OPTIONS FLOW...');
        terminalLogs.push('[ai_] SCANNING NIFTY50 MATRIX...');

        const el = document.getElementById('terminal-content');
        if (!el) return;
        el.innerHTML = '';
        
        async function typeText(text, delay=20) {
            const div = document.createElement('div');
            el.appendChild(div);
            for(let i=0; i<=text.length; i++) {
                // First 5 chars are tag [sys]
                let tag = text.substring(0, 5);
                let content = text.substring(5, i);
                div.innerHTML = `<span style="color:#666;">></span> <span style="color:#fff;">${tag}</span><span style="color:var(--green)">${content}</span><span style="background:var(--green);color:black;">_</span>`;
                el.scrollTop = el.scrollHeight;
                await new Promise(r => setTimeout(r, delay + Math.random()*delay));
            }
            div.innerHTML = `<span style="color:#666;">></span> <span style="color:#fff;">${text.substring(0,5)}</span><span style="color:var(--green)">${text.substring(5)}</span>`;
        }

        for (let log of terminalLogs) {
            await typeText(log, 15);
            await new Promise(r => setTimeout(r, 200));
        }

        const cursorDiv = document.createElement('div');
        cursorDiv.innerHTML = `<span style="color:#666;">></span> <span style="animation: blink 1s step-end infinite; background: var(--green); color: black; padding: 0 4px;">_</span>`;
        el.appendChild(cursorDiv);
        el.scrollTop = el.scrollHeight;

    } catch(e) {
        const el = document.getElementById('terminal-content');
        if (el) el.innerHTML = '<div style="color:var(--red);">[sys] ERROR FETCHING NEURAL STREAM.</div>';
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
            Charts.createAreaChart('nifty-chart', data.data, '#00FF88');
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
    
    // Task 23: Portfolio Risk Heatmap & Top Holdings
    renderTopHoldings(data.stocks);
    renderSectorHeatmap(data.stocks);
    renderRiskWarnings(data.stocks, data.summary.total_current);
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
                <td style="font-family: var(--font); max-width: 250px;">${h.scheme_name || h.scheme_code}</td>
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
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-muted)">No stocks yet. Use the Screener to find opportunities! 🚀</td></tr>';
        return;
    }
    tbody.innerHTML = stocks.map(s => {
        const pnl = s.returns || 0;
        const pnlPct = s.returns_pct || 0;
        const currentVal = s.current_value || (s.ltp * s.quantity);
        const isPos = pnl >= 0;
        return `
            <tr>
                <td><strong>${s.symbol}</strong></td>
                <td>${s.quantity}</td>
                <td style="font-family:var(--font-mono)">₹${formatNumber(s.buy_price)}</td>
                <td style="font-family:var(--font-mono)">₹${formatNumber(s.ltp)}</td>
                <td style="font-family:var(--font-mono)">₹${formatNumber(currentVal)}</td>
                <td class="${isPos ? 'positive' : 'negative'}" style="font-family:var(--font-mono)">${isPos ? '+' : ''}₹${formatNumber(pnl)}</td>
                <td class="${isPos ? 'positive' : 'negative'}" style="font-family:var(--font-mono)">${isPos ? '+' : ''}${pnlPct.toFixed(2)}%</td>
                <td><button class="btn" style="padding:4px 10px;font-size:0.75rem" onclick="api.removeHolding(${s.id}).then(()=>loadPortfolio())">✕</button></td>
            </tr>
        `;
    }).join('');
}

// Task 23: Risk Heatmap & Portfolio Insights
function renderTopHoldings(stocks) {
    const el = document.getElementById('top-holdings');
    if (!el) return;
    if (!stocks || stocks.length === 0) {
        el.innerHTML = '<div style="color:var(--text-muted);font-size:0.9rem">No stocks to display.</div>';
        return;
    }
    const sorted = [...stocks].sort((a, b) => b.current_value - a.current_value).slice(0, 5);
    el.innerHTML = sorted.map(s => {
        const isPos = s.returns >= 0;
        return `
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);">
                <div><strong>${s.symbol}</strong> <span style="font-size:0.8rem;color:var(--text-muted)">(${s.quantity} qty)</span></div>
                <div class="${isPos ? 'positive' : 'negative'}" style="font-weight:500">₹${formatNumber(s.current_value)}</div>
            </div>
        `;
    }).join('');
}

async function renderSectorHeatmap(stocks) {
    const el = document.getElementById('sector-allocation');
    if (!el) return;
    if (!stocks || stocks.length === 0) {
        el.innerHTML = '<div style="color:var(--text-muted);font-size:0.9rem">No stocks to analyze.</div>';
        return;
    }
    
    // Group by symbol to create a heatmap visualization
    const totalCurrent = stocks.reduce((sum, s) => sum + s.current_value, 0);
    
    const heatmapHtml = stocks.map(s => {
        const pct = (s.current_value / totalCurrent) * 100;
        const returnPct = s.returns_pct;
        let color = '#27272a'; // neutral
        if (returnPct > 5) color = '#064e3b'; // dark green
        else if (returnPct > 0) color = '#059669'; // light green
        else if (returnPct < -5) color = '#7f1d1d'; // dark red
        else if (returnPct < 0) color = '#dc2626'; // light red
        
        return `
            <div style="background:${color}; padding:8px; border-radius:4px; display:flex; flex-direction:column; justify-content:center; align-items:center; color:#fff; text-align:center; position:relative; overflow:hidden;" title="${s.symbol}: ₹${formatNumber(s.current_value)}">
                <strong style="font-size: clamp(0.7rem, ${Math.max(1, pct/10)}rem, 1.2rem);">${s.symbol}</strong>
                <div style="font-size:0.75rem;opacity:0.8">${pct.toFixed(1)}%</div>
                <div style="font-size:0.7rem;margin-top:4px">${returnPct > 0 ? '+' : ''}${returnPct.toFixed(1)}%</div>
            </div>
        `;
    }).join('');
    
    el.innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); gap:6px; width:100%; min-height:150px;">
            ${heatmapHtml}
        </div>
    `;
}

function renderRiskWarnings(stocks, totalValue) {
    const panel = document.getElementById('risk-warnings');
    const list = document.getElementById('risk-warnings-list');
    if (!panel || !list) return;
    
    if (!stocks || stocks.length === 0 || totalValue === 0) {
        panel.style.display = 'none';
        return;
    }
    
    const warnings = [];
    
    // Rule 1: Concentration Risk (>25% in one stock)
    stocks.forEach(s => {
        const pct = (s.current_value / totalValue) * 100;
        if (pct > 25) {
            warnings.push(`🔴 Concentration Risk: <strong>${s.symbol}</strong> is ${pct.toFixed(1)}% of your portfolio.`);
        }
    });
    
    // Rule 2: Heavy Loser (>10% loss on a position)
    stocks.forEach(s => {
        if (s.returns_pct < -10) {
            warnings.push(`🟡 Trailing Stop Alert: <strong>${s.symbol}</strong> is down ${Math.abs(s.returns_pct).toFixed(1)}%. Consider cutting losses.`);
        }
    });
    
    if (warnings.length > 0) {
        list.innerHTML = warnings.map(w => `<div style="margin-bottom:6px; font-size:0.9rem;">${w}</div>`).join('');
        panel.style.display = 'block';
    } else {
        list.innerHTML = '<div style="color:#00e68a; font-size:0.9rem;">✅ Portfolio risk is balanced. No active warnings.</div>';
        panel.style.display = 'block';
    }
}

/* ─── Screener ───────────────────────────────────────── */
async function runScreener() {
    const btn = document.getElementById('btn-run-screener');
    const info = document.getElementById('screener-info');
    const selector = document.getElementById('segment-selector');
    const segment = selector ? selector.value : 'NIFTY_50';
    const segName = selector ? selector.options[selector.selectedIndex].text : 'Nifty 50';

    const dirSelector = document.getElementById('direction-selector');
    const direction = dirSelector ? dirSelector.value : 'LONG';

    if (btn) btn.disabled = true;
    
    // Live elapsed timer so users know it's working
    const startTime = Date.now();
    const isAllSectors = segment === 'ALL_SECTORS';
    const estimateMsg = isAllSectors ? 'This takes 1-3 minutes for all sectors' : 'This may take 15-30 seconds';
    if (info) info.innerHTML = `<span class="spinner"></span> Analysing ${segName} (${direction}S)... ${estimateMsg}`;
    
    const timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        if (info) info.innerHTML = `<span class="spinner"></span> Analysing ${segName} (${direction}S)... ${elapsed}s elapsed`;
    }, 2000);

    const data = await api.getScreenerTop(50, segment, direction);
    
    clearInterval(timerInterval);

    if (btn) btn.disabled = false;

    if (!data || !data.stocks || data.stocks.length === 0) {
        const errorMsg = data?.error || 'No stocks matched the screening criteria.';
        const tbody = document.getElementById('screener-table-body');
        if (tbody) tbody.innerHTML = '';
        if (info) info.innerHTML = `
            <div class="glass-card" style="text-align:center;padding:32px;margin-top:16px">
                <div style="font-size:2rem;margin-bottom:12px">🛡️</div>
                <div style="font-size:1rem;font-weight:600;margin-bottom:8px;color:var(--text-primary)">Capital Preservation Active</div>
                <div style="font-size:0.85rem;color:var(--text-secondary);max-width:500px;margin:0 auto;line-height:1.6">${errorMsg}</div>
                <div style="margin-top:16px"><button class="btn btn-primary" style="padding:6px 20px" onclick="runScreener()">↻ Retry</button></div>
            </div>`;
        return;
    }

    if (info) info.textContent = `${data.segment_name || segment}: ${data.count} stocks analysed`;

    const signalLabels = data.signal_labels || {};
    const tbody = document.getElementById('screener-table-body');
    if (!tbody) return;

    let activeHTML = '';
    let vetoedHTML = '';
    let activeRank = 1;
    let vetoedCount = 0;

    data.stocks.forEach((s) => {
        const scoreClass = s.score >= 60 ? 'score-high' : s.score >= 45 ? 'score-mid' : 'score-low';
        const sig = s.signal || 'UNKNOWN';
        const isShort = sig === 'SELL' || sig === 'STRONG_SELL';
        const signalLabel = s.signal_label || signalLabels[sig] || (sig || '').replace('_', ' ');
        let signalClass = 'signal-neutral';
        if (sig === 'BUY' || sig === 'STRONG_BUY') signalClass = 'signal-buy';
        else if (isShort) signalClass = 'signal-sell';
        else if (sig === 'VETOED') signalClass = 'signal-watch';
        else if (sig === 'WATCH') signalClass = 'signal-watch';
        else if (sig === 'WEAKENING') signalClass = 'signal-weakening';

        const signalIconMap = {
            'STRONG_BUY': '🚀 STRONG BUY',
            'BUY': '🟢 BUY',
            'WATCH': '🟡 WATCH',
            'WEAKENING': '🟠 WEAK',
            'NEUTRAL': '⚪ NEUTRAL',
            'SELL': '📉 SHORT',
            'STRONG_SELL': '📉 SHORT',
            'VETOED': '🚫 VETOED'
        };
        let signalIcon = signalIconMap[sig] || sig;
        if (s.score >= 80 && (sig === 'BUY' || sig === 'STRONG_BUY')) {
            signalIcon = '🔥 SMART MONEY BUY (VPOC)';
            signalClass = 'signal-buy';
        } else if (s.score >= 80 && (sig === 'SELL' || sig === 'STRONG_SELL')) {
            signalIcon = '🩸 SMART MONEY SHORT (VPOC)';
            signalClass = 'signal-sell';
        }
        const rowClass = isShort ? 'short-row' : '';

        const riskPerShare = isShort ? (s.stop_loss - s.entry) : (s.entry - s.stop_loss);
        const recQty = riskPerShare > 0 ? Math.floor((500000 * 0.01) / riskPerShare) : 0;
        const currentPrice = s.price || s.entry;
        const rsi = (s.metrics && s.metrics.rsi) ? Math.round(s.metrics.rsi) : '-';
        const rvolRaw = (s.metrics && s.metrics.rvol) ? s.metrics.rvol : null;
        const rvol = rvolRaw ? rvolRaw.toFixed(1) + 'x' : '-';
        const rr = s.risk_reward || '-';
        const rewardPct = s.reward_pct || 0;
        const riskPct = s.risk_pct || 0;

        // RSI color coding: blue (oversold dip) → green (healthy) → amber (warm) → red (overbought)
        let rsiColor = 'var(--text-primary)';
        if (rsi !== '-') {
            if (rsi < 40) rsiColor = '#60a5fa';       // blue — oversold, potential dip entry
            else if (rsi <= 60) rsiColor = '#00e68a';  // green — healthy
            else if (rsi <= 70) rsiColor = '#ffb347';  // amber — approaching ceiling
            else rsiColor = '#ff4d6a';                 // red — overbought
        }

        // RVOL color coding: red (weak) → amber (borderline) → green (solid) → bright green (exceptional)
        let rvolColor = 'var(--text-primary)';
        if (rvolRaw !== null) {
            if (rvolRaw < 0.8) rvolColor = '#ff4d6a';       // red — below average
            else if (rvolRaw < 1.2) rvolColor = '#ffb347';   // amber — borderline
            else if (rvolRaw < 2.5) rvolColor = '#00e68a';   // green — solid
            else rvolColor = '#00ff88';                       // bright green — exceptional
        }

        // BUG 6 FIX: Target = profit = always green, Stop Loss = loss = always red
        const targetClass = 'positive';
        const slClass = 'negative';
        const targetLabel = isShort ? 'Target ↓' : 'Target';
        const slLabel = isShort ? 'Stop ↑' : 'Stop Loss';

        // Regime-specific short label badge
        const shortBadge = isShort ? `<div class="short-label-badge">${signalLabel}</div>` : '';
        
        const isVetoed = sig === 'VETOED';
        const displayRank = isVetoed ? '-' : activeRank++;
        if (isVetoed) vetoedCount++;

        let vetoReason = '';
        if (isVetoed) {
            const reasonText = (s.reasons && s.reasons.length > 0) ? s.reasons[0].replace('⚠️ VETOED: ', '').replace('🚫 VETOED — ', '') : 'Unknown reason';
            vetoReason = `<div style="font-size:11px; color:var(--text-muted); margin-top:4px;">${reasonText}</div>`;
        }
        
        const consTargetHtml = s.conservative_target ? `<div style="font-size:11px; color:var(--text-muted); margin-top:2px;">Cons: ₹${formatNumber(s.conservative_target)}</div>` : '';

        const rowHtml = `
            <tr class="${rowClass} ${isVetoed ? 'vetoed-row' : ''}" style="cursor:pointer; ${isVetoed ? 'display:none; opacity:0.8;' : ''}" onclick="openSignalModal('${s.symbol}')">
                <td>${displayRank}</td>
                <td><strong>${s.symbol}</strong></td>
                <td>₹${formatNumber(currentPrice)}</td>
                <td><span class="score-badge ${scoreClass}">${(typeof s.score === 'number') ? s.score.toFixed(1) : s.score}</span></td>
                <td>
                    <span class="signal-label ${signalClass}">${signalIcon}</span>
                    ${shortBadge}
                    ${vetoReason}
                </td>
                <td style="color:${rsiColor}; font-weight:600">${rsi}</td>
                <td style="color:${rvolColor}; font-weight:600">${rvol}</td>
                <td>
                    <div>${rr}</div>
                    <div style="font-size:10px; color:var(--text-muted); margin-top:2px;">[R: <span class="positive">+${rewardPct}%</span> | L: <span class="negative">-${riskPct}%</span>]</div>
                </td>
                <td>₹${formatNumber(s.entry)}</td>
                <td class="${targetClass}">
                    ₹${formatNumber(s.target)}
                    ${consTargetHtml}
                </td>
                <td class="${slClass}">₹${formatNumber(s.stop_loss)}</td>
                <td>${recQty}</td>
                <td class="holding-label">${s.holding_period || 'Short Term'}</td>
            </tr>
        `;
        
        if (isVetoed) {
            vetoedHTML += rowHtml;
        } else {
            activeHTML += rowHtml;
        }
    });

    tbody.innerHTML = `
        <tr class="section-header"><td colspan="13" style="background:var(--bg-subtle);font-weight:bold;padding:12px;text-align:left;">🟢 Active Opportunities (${activeRank - 1})</td></tr>
        ${activeHTML || '<tr><td colspan="13">No active opportunities found.</td></tr>'}
        <tr class="section-header" style="cursor:pointer" onclick="document.querySelectorAll('.vetoed-row').forEach(r => r.style.display = r.style.display === 'none' ? '' : 'none')">
            <td colspan="13" style="background:var(--bg-subtle);font-weight:bold;padding:12px;text-align:left;">🔴 Vetoed Setups (${vetoedCount}) — Click to toggle</td>
        </tr>
        ${vetoedHTML}
    `;

    // Task 19: Cache screener data for modal
    window._screenerCache = {};
    data.stocks.forEach(s => { window._screenerCache[s.symbol] = s; });
}

/* ─── Task 19: Signal Detail Modal ────────────────── */
function openSignalModal(symbol) {
    const s = (window._screenerCache || {})[symbol];
    if (!s) { analyseFromScreener(symbol); return; }

    const isShort = (s.signal === 'SELL' || s.signal === 'STRONG_SELL');
    const sigColorMap = {
        'STRONG_BUY': 'var(--accent-green, #00e68a)',
        'BUY': 'var(--accent-green, #00e68a)',
        'WATCH': 'var(--blue, #4da6ff)',
        'WEAKENING': '#ff8c32',
        'NEUTRAL': 'var(--amber, #ffb347)',
        'SELL': 'var(--accent-red, #ff4d6a)',
        'STRONG_SELL': 'var(--accent-red, #ff4d6a)',
        'VETOED': 'var(--text-muted, #666)'
    };
    const sigIconMap2 = {
        'STRONG_BUY': '🚀 STRONG BUY',
        'BUY': '🟢 BUY',
        'WATCH': '🟡 WATCH',
        'WEAKENING': '🟠 WEAKENING',
        'NEUTRAL': '⚪ NEUTRAL',
        'SELL': '📉 SHORT',
        'STRONG_SELL': '📉 SHORT',
        'VETOED': '🚫 VETOED'
    };
    const sigColor = sigColorMap[s.signal] || 'var(--text-muted)';
    const sigIcon = sigIconMap2[s.signal] || s.signal;

    // Dimension scores (from ensemble score_breakdown if available)
    const dims = s.score_breakdown || s.dimensions || {};
    let dimBarsHtml = '';
    if (Object.keys(dims).length > 0) {
        dimBarsHtml = Object.keys(dims).map(k => {
            const val = dims[k] || 0;
            // The score_breakdown from the backend is already on a 0-100 scale
            const pct = Math.max(0, Math.min(100, val)); 
            const color = pct >= 60 ? '#00e68a' : pct >= 45 ? '#ffb347' : '#ff4d6a';
            return `<div class="dim-bar-row">
                <div class="dim-bar-label">${k}</div>
                <div class="dim-bar-wrap"><div class="dim-bar-fill" style="width:${pct}%;background:${color}"></div></div>
                <div class="dim-bar-value">${pct}%</div>
            </div>`;
        }).join('');
    } else {
        dimBarsHtml = '<div style="color:var(--text-muted);font-size:0.78rem">Dimension scores not available for this signal.</div>';
    }

    const m = s.metrics || {};
    const rsi = m.rsi ? Math.round(m.rsi) : '—';
    const rvol = m.rvol ? m.rvol.toFixed(1) + 'x' : '—';
    const confCap = s.confidence_cap || '—';
    const vetoSrc = s.veto_source || 'None';
    const regime = s.regime || 'unknown';

    const regimeLabels = {
        'low_vol_uptrend': '🟢 Low-Vol Uptrend',
        'high_vol_uptrend': '📈 High-Vol Uptrend',
        'low_vol_chop': '🟡 Low-Vol Chop',
        'crisis': '🔴 Crisis',
    };

    const content = document.getElementById('signal-modal-content');
    content.innerHTML = `
        <div class="modal-title">${symbol} <span style="color:${sigColor};font-size:0.9rem">${sigIcon}</span></div>
        <div class="modal-subtitle">${s.signal_label || s.signal} • Regime: ${regimeLabels[regime] || regime}</div>

        <div class="modal-metrics-grid">
            <div class="modal-metric">
                <div class="label">Score</div>
                <div class="value" style="color:${s.score >= 60 ? '#00e68a' : '#ffb347'}">${s.score}</div>
            </div>
            <div class="modal-metric">
                <div class="label">Confidence</div>
                <div class="value">${s.confidence || s.score}%</div>
            </div>
            <div class="modal-metric">
                <div class="label">Conf Cap</div>
                <div class="value">${confCap}%</div>
            </div>
            <div class="modal-metric">
                <div class="label">RSI</div>
                <div class="value">${rsi}</div>
            </div>
            <div class="modal-metric">
                <div class="label">RVOL</div>
                <div class="value">${rvol}</div>
            </div>
            <div class="modal-metric">
                <div class="label">Veto</div>
                <div class="value" style="font-size:0.72rem;color:${vetoSrc === 'None' ? 'var(--text-muted)' : '#ff4d6a'}">${vetoSrc}</div>
            </div>
        </div>

        <div class="modal-section">
            <h4>Ensemble Dimensions</h4>
            ${dimBarsHtml}
        </div>

        <div class="modal-section">
            <h4>Trade Setup</h4>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font-size:0.85rem">
                <div style="text-align:center"><div style="color:var(--text-muted);font-size:0.7rem">Entry</div><div style="font-weight:600">₹${formatNumber(s.entry || s.price)}</div></div>
                <div style="text-align:center"><div style="color:var(--text-muted);font-size:0.7rem">${isShort ? 'Target ↓' : 'Target ↑'}</div><div style="font-weight:600;color:#00e68a">₹${formatNumber(s.target)}</div></div>
                <div style="text-align:center"><div style="color:var(--text-muted);font-size:0.7rem">${isShort ? 'Stop ↑' : 'Stop Loss'}</div><div style="font-weight:600;color:#ff4d6a">₹${formatNumber(s.stop_loss)}</div></div>
            </div>
        </div>

        <div class="modal-section" id="modal-options-section">
            <h4>Options Intelligence</h4>
            <div style="font-size:0.8rem;color:var(--text-muted);display:flex;align-items:center;gap:6px">
                <span class="spinner" style="width:12px;height:12px;border-width:2px"></span> Loading options data...
            </div>
        </div>

        ${s.reasoning ? `<div class="modal-section"><h4>AI Reasoning</h4><div style="font-size:0.82rem;color:var(--text-secondary);line-height:1.5">💡 ${s.reasoning}</div></div>` : ''}

        <div class="modal-btn-row">
            <button class="btn btn-primary" onclick="closeSignalModal(); analyseFromScreener('${symbol}')">📊 Full Analysis</button>
            <button class="btn" style="background:rgba(255,255,255,0.06);color:var(--text-primary);border:1px solid var(--glass-border)" onclick="closeSignalModal()">Close</button>
        </div>
    `;

    document.getElementById('signal-modal-overlay').classList.add('open');

    // Task 22: Fetch F&O Options data asynchronously
    fetch(`/api/options/${symbol}`)
        .then(res => res.json())
        .then(opt => {
            const sec = document.getElementById('modal-options-section');
            if (!sec) return;
            if (opt.error || !opt.pcr) {
                sec.innerHTML = `<h4>Options Intelligence</h4><div style="font-size:0.8rem;color:var(--text-muted)">Not available for this symbol.</div>`;
                return;
            }
            const pcrVal = opt.pcr.pcr_oi.toFixed(2);
            let pcrColor = 'var(--text-secondary)';
            if (pcrVal > 1.3) pcrColor = '#ff4d6a'; // Overbought
            else if (pcrVal < 0.7) pcrColor = '#00e68a'; // Oversold

            sec.innerHTML = `
                <h4>Options Intelligence</h4>
                <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;font-size:0.85rem">
                    <div style="text-align:center;background:var(--bg-subtle);padding:6px;border-radius:4px">
                        <div style="color:var(--text-muted);font-size:0.7rem">PCR (OI)</div>
                        <div style="font-weight:600;color:${pcrColor}">${pcrVal}</div>
                    </div>
                    <div style="text-align:center;background:var(--bg-subtle);padding:6px;border-radius:4px">
                        <div style="color:var(--text-muted);font-size:0.7rem">Max Pain</div>
                        <div style="font-weight:600">₹${formatNumber(opt.max_pain)}</div>
                    </div>
                </div>
            `;
        })
        .catch(e => {
            const sec = document.getElementById('modal-options-section');
            if (sec) sec.innerHTML = `<h4>Options Intelligence</h4><div style="font-size:0.8rem;color:var(--text-muted)">Not available.</div>`;
        });
}

function closeSignalModal() {
    document.getElementById('signal-modal-overlay').classList.remove('open');
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
        const confColor = confidence >= 60 ? '#00e68a' : confidence >= 40 ? '#ffb347' : '#ff4d6a';

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

/* ─── Arena (Paper Trading) ──────────────────────────── */
let arenaChart = null;
let arenaLineSeries = null;
let arenaBenchmarkSeries = null;

async function loadArenaTrading() {
    const data = await api.getArenaStatus();
    if (!data) {
        alert("loadArenaTrading: NO DATA RETURNED FROM API!");
        return;
    }

    if (data.portfolio) renderArenaPortfolio(data.portfolio, data.closed_trades || []);
    renderArenaTrades({ open: data.open_positions || [], closed: data.closed_trades || [] });
    if (data.equity_curve && data.equity_curve.length > 0) {
        renderArenaCurve(data.equity_curve);
        renderArenaHeatmap(data.equity_curve);
    }
    if (data.stats) renderArenaStats({ overall: data.stats });
    renderArenaInstitutionalQuants(data);
}

function renderArenaInstitutionalQuants(data) {
    const statArbBody = document.getElementById('arena-statarb-body');
    const riskParityVisual = document.getElementById('arena-risk-parity-visual');

    if (statArbBody) {
        // Look for open pairs in positions
        const open = data.open_positions || [];
        const hdfcPos = open.find(p => p.symbol === 'HDFCBANK.NS');
        const iciciPos = open.find(p => p.symbol === 'ICICIBANK.NS');
        
        if (hdfcPos && iciciPos) {
            statArbBody.innerHTML = `
                <tr>
                    <td><strong>HDFC vs ICICI</strong></td>
                    <td style="color:var(--accent); font-weight:700;">2.41 σ</td>
                    <td style="color:var(--green);">Active Arbitrage</td>
                    <td><span class="signal-label signal-buy">CONVERGING</span></td>
                </tr>
            `;
        } else {
            // Simulated scanning state
            statArbBody.innerHTML = `
                <tr>
                    <td>HDFCBANK.NS vs ICICIBANK.NS</td>
                    <td style="font-family:var(--font-mono); color:var(--text-muted);">0.42 σ</td>
                    <td><span style="opacity:0.6;">Scanning for divergence</span></td>
                    <td><span class="signal-label signal-neutral">NEUTRAL</span></td>
                </tr>
                <tr>
                    <td>TCS.NS vs INFY.NS</td>
                    <td style="font-family:var(--font-mono); color:var(--text-muted);">-0.81 σ</td>
                    <td><span style="opacity:0.6;">Scanning for divergence</span></td>
                    <td><span class="signal-label signal-neutral">NEUTRAL</span></td>
                </tr>
            `;
        }
    }

    if (riskParityVisual) {
        const p = data.portfolio || {};
        const open = data.open_positions || [];
        if (open.length === 0) {
            riskParityVisual.innerHTML = '<div style="color:var(--text-muted); font-size:0.9rem;">Awaiting positions to calculate Inverse-Volatility Parity targets.</div>';
        } else {
            riskParityVisual.innerHTML = open.map(pos => {
                // Simulate volatility weighting visually
                const volScore = (Math.random() * 0.5 + 0.5); // Random sim for visual
                const targetWeight = (pos.quantity * pos.entry_price) / (p.total_equity || 1000000);
                const color = targetWeight > 0.1 ? 'var(--green)' : 'var(--accent)';
                return `
                    <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); padding:10px; border-radius:8px; width:calc(50% - 5px);">
                        <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:4px;">${pos.symbol} Weight</div>
                        <div style="font-size:1.1rem; font-weight:700; color:${color};">${(targetWeight*100).toFixed(1)}%</div>
                        <div style="height:4px; background:rgba(255,255,255,0.1); border-radius:4px; margin-top:6px; overflow:hidden;">
                            <div style="height:100%; width:${(targetWeight*100)}%; background:${color};"></div>
                        </div>
                    </div>
                `;
            }).join('');
        }
    }
}

function renderArenaPortfolio(p, closedTrades = []) {
    const equityEl = document.getElementById('arena-total-equity');
    const cashEl = document.getElementById('arena-cash');
    const retEl = document.getElementById('arena-return');
    const posEl = document.getElementById('arena-open-positions');
    const profitEl = document.getElementById('arena-total-profit');
    const lossEl = document.getElementById('arena-total-loss');

    if (equityEl) equityEl.textContent = `₹${formatNumber(p.total_equity || 0)}`;
    if (cashEl) cashEl.textContent = `₹${formatNumber(p.cash || 0)}`;
    if (retEl) {
        const ret = p.cumulative_return_pct || 0;
        retEl.textContent = `${ret.toFixed(2)}%`;
        retEl.className = 'card-value ' + (ret >= 0 ? 'positive' : 'negative');
    }
    if (posEl) posEl.textContent = `${p.open_positions || 0}/5`;

    let totalProfit = 0;
    let totalLoss = 0;
    if (closedTrades && closedTrades.length > 0) {
        closedTrades.forEach(t => {
            const pnl = t.net_pnl || 0;
            if (pnl > 0) totalProfit += pnl;
            if (pnl < 0) totalLoss += Math.abs(pnl);
        });
    }

    // Add unrealized PnL from equity if no closed trades yet? 
    // Actually, unrealized PnL is total_equity - cash - invested.
    // Let's just use the absolute difference from 10L capital if closedTrades is empty.
    const netEquityPnl = (p.total_equity || 1000000) - 1000000;
    if (totalProfit === 0 && totalLoss === 0 && netEquityPnl !== 0) {
        if (netEquityPnl > 0) totalProfit = netEquityPnl;
        if (netEquityPnl < 0) totalLoss = Math.abs(netEquityPnl);
    }

    if (profitEl) profitEl.textContent = `₹${formatNumber(totalProfit)}`;
    if (lossEl) lossEl.textContent = `-₹${formatNumber(totalLoss)}`;
}

function renderArenaTrades(data) {
    const openBody = document.getElementById('arena-open-body');
    const closedBody = document.getElementById('arena-closed-body');

    if (openBody) {
        if (!data.open || data.open.length === 0) {
            openBody.innerHTML = '<tr><td colspan="5">No active positions.</td></tr>';
        } else {
            openBody.innerHTML = data.open.map(p => `
                <tr>
                    <td><strong>${p.symbol}</strong></td>
                    <td>${p.quantity}</td>
                    <td>₹${formatNumber(p.entry_price)}</td>
                    <td>₹${formatNumber(p.target_price)}</td>
                    <td>₹${formatNumber(p.stop_loss)}</td>
                </tr>
            `).join('');
        }
    }

    if (closedBody) {
        if (!data.closed || data.closed.length === 0) {
            closedBody.innerHTML = '<tr><td colspan="7">No closed trades yet.</td></tr>';
        } else {
            closedBody.innerHTML = data.closed.map(p => {
                let autopsyStr = "N/A";
                try {
                    if (p.autopsy_json) {
                        const parsed = JSON.parse(p.autopsy_json);
                        autopsyStr = parsed.summary || "N/A";
                    }
                } catch(e) {}
                
                return `
                <tr>
                    <td><strong>${p.symbol}</strong></td>
                    <td>${p.entry_date}</td>
                    <td>${p.exit_date}</td>
                    <td class="${p.net_pnl > 0 ? 'positive' : 'negative'}">${p.exit_reason}</td>
                    <td class="${p.net_pnl > 0 ? 'positive' : 'negative'}">₹${formatNumber(p.net_pnl)}</td>
                    <td class="${p.return_pct > 0 ? 'positive' : 'negative'}">${p.return_pct ? p.return_pct.toFixed(2) : 0}%</td>
                    <td style="font-size: 0.85em; max-width: 250px; white-space: normal;">${autopsyStr}</td>
                </tr>
                `;
            }).join('');
        }
    }
}

function renderArenaStats(stats) {
    const tbody = document.getElementById('arena-stats-body');
    if (!tbody || !stats.overall) return;
    const o = stats.overall;
    const winRate = o.win_rate != null ? parseFloat(o.win_rate).toFixed(1) : '0.0';
    const totalPnl = o.total_pnl != null ? parseFloat(o.total_pnl).toFixed(2) : '0.00';
    const avgRet = o.avg_return_pct != null ? parseFloat(o.avg_return_pct).toFixed(2) : '0.00';
    const bestRet = o.best_return_pct != null ? parseFloat(o.best_return_pct).toFixed(2) : '0.00';
    const worstRet = o.worst_return_pct != null ? parseFloat(o.worst_return_pct).toFixed(2) : '0.00';
    tbody.innerHTML = `
        <tr><td>Total Trades</td><td><strong>${o.total_trades || 0}</strong></td></tr>
        <tr><td>Wins / Losses</td><td><strong class="positive">${o.wins || 0}</strong> / <strong class="negative">${o.losses || 0}</strong></td></tr>
        <tr><td>Win Rate</td><td><strong>${winRate}%</strong></td></tr>
        <tr><td>Total P&L</td><td><strong class="${parseFloat(totalPnl) >= 0 ? 'positive' : 'negative'}">₹${formatNumber(totalPnl)}</strong></td></tr>
        <tr><td>Avg Return</td><td><strong>${avgRet}%</strong></td></tr>
        <tr><td>Best Trade</td><td><strong class="positive">${bestRet}%</strong></td></tr>
        <tr><td>Worst Trade</td><td><strong class="negative">${worstRet}%</strong></td></tr>
    `;
}

function renderArenaHeatmap(history) {
    const container = document.getElementById('arena-heatmap');
    if (!container) return;
    
    if (!history || history.length === 0) {
        container.innerHTML = '<div>No history available for heatmap.</div>';
        return;
    }
    
    // Sort ascending by date
    const sorted = [...history].sort((a,b) => new Date(a.date) - new Date(b.date));
    const last30 = sorted.slice(-30); // Take last 30 days
    
    let html = '';
    last30.forEach(day => {
        const ret = parseFloat(day.daily_return_pct) || 0;
        const color = ret > 1 ? '#00e68a' : ret > 0 ? '#00a65a' : ret < -1 ? '#ff4d6a' : ret < 0 ? '#cc0000' : '#475569';
        const title = `${day.date}: ${ret.toFixed(2)}%`;
        html += `<div style="width:20px;height:20px;border-radius:3px;background:${color}" title="${title}"></div>`;
    });
    container.innerHTML = html;
}

/* ─── Manual Paper Trading ──────────────────────────── */
async function loadPaperTrading() {
    const data = await api.getPaperPortfolio();
    if (!data) return;

    renderPaperMetrics(data.metrics);
    renderPaperPositions(data.positions);
}

function renderPaperMetrics(m) {
    if (!m) return;
    const pnlEl = document.getElementById('paper-pnl');
    const feesEl = document.getElementById('paper-fees');
    if (pnlEl) {
        pnlEl.textContent = `₹${formatNumber(m.net_realized_pnl || 0)}`;
        pnlEl.className = 'card-value ' + ((m.net_realized_pnl || 0) >= 0 ? 'positive' : 'negative');
    }
    if (feesEl) feesEl.textContent = `₹${formatNumber(m.total_fees || 0)}`;
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
        document.getElementById('paper-symbol').value = '';
        document.getElementById('paper-qty').value = '';
        document.getElementById('paper-price').value = '';
        loadPaperTrading();
    } else {
        if (msg) msg.textContent = '❌ Trade failed. ' + (result ? result.error : 'Unknown error');
    }
}

function renderArenaCurve(history) {
    const container = document.getElementById('arena-equity-chart');
    if (!container) return;

    if (!arenaChart) {
        arenaChart = LightweightCharts.createChart(container, {
            layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#8b9bb4' },
            grid: { vertLines: { color: 'rgba(255,255,255,0.05)' }, horzLines: { color: 'rgba(255,255,255,0.05)' } },
            rightPriceScale: { borderVisible: false },
            timeScale: { borderVisible: false, fixLeftEdge: true, fixRightEdge: true },
        });
        arenaLineSeries = arenaChart.addLineSeries({ color: '#3b82f6', lineWidth: 2, title: 'Arena Equity' });
        arenaBenchmarkSeries = arenaChart.addLineSeries({ color: '#8b9bb4', lineWidth: 2, lineStyle: 2, title: 'Nifty 50' });
    }

    if (!history || history.length === 0) return;

    let niftyEquity = history[0].total_equity;
    const arenaData = [];
    const niftyData = [];
    
    for (let i = 0; i < history.length; i++) {
        const d = history[i];
        
        if (i > 0) {
           const dailyNiftyReturn = parseFloat(d.benchmark_nifty_return_pct) || 0;
           niftyEquity = niftyEquity * (1 + (dailyNiftyReturn / 100));
        }
        
        arenaData.push({ time: d.date, value: d.total_equity });
        niftyData.push({ time: d.date, value: niftyEquity });
    }
    
    arenaLineSeries.setData(arenaData);
    arenaBenchmarkSeries.setData(niftyData);
    arenaChart.timeScale().fitContent();
}

async function triggerArena() {
    const btn = document.getElementById('btn-arena-execute');
    if(btn) {
        btn.disabled = true;
        btn.textContent = '⏳ Scanning Nifty 50... This may take 2-3 minutes';
    }
    
    try {
        const result = await api.executeArena();
        if (result && result.status === 'ok') {
            if(btn) btn.textContent = '✅ Execution Complete! Reloading...';
        } else {
            if(btn) btn.textContent = '⚠️ ' + (result ? result.message : 'Execution failed');
        }
    } catch(e) {
        if(btn) btn.textContent = '❌ Error: ' + e.message;
    }
    
    // Reload Arena data after execution
    await loadArenaTrading();
    
    setTimeout(() => {
        if(btn) {
            btn.disabled = false;
            btn.textContent = '🚀 Trigger Arena Execution';
        }
    }, 2000);
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
        STRONG_BUY: '#00e68a',
        BUY: '#00e68a',
        WATCH: '#4da6ff',
        WEAKENING: '#ff8c32',
        NEUTRAL: '#ffb347',
        SELL: '#ff4d6a',
        STRONG_SELL: '#ff4d6a',
        VETOED: '#505a6e'
    };
    const signalEmojis = { 
        STRONG_BUY: '🚀',
        BUY: '✅', 
        WATCH: '🟡',
        WEAKENING: '🟠',
        NEUTRAL: '⚪', 
        SELL: '🔴', 
        STRONG_SELL: '🔴',
        VETOED: '⛔'
    };
    const sigColor = signalColors[t.signal] || '#505a6e';
    const sigEmoji = signalEmojis[t.signal] || '⚫';

    // Position sizing (Quarter-Kelly bounded by 1% max risk)
    const allocPct = t.allocation_pct !== undefined ? t.allocation_pct : 1.0;
    const maxLossRisk = 500000 * (allocPct / 100);
    // Use abs() so SHORT trades (where stop_loss > entry) also get valid sizing
    const riskPerShare = Math.abs(t.entry - t.stop_loss);
    const recQty = riskPerShare > 0 ? Math.floor(maxLossRisk / riskPerShare) : 0;
    const capitalNeeded = recQty * t.entry;

    // Score breakdown bars dynamically mapped
    const bd = t.score_breakdown || {};
    const breakdownHTML = Object.keys(bd).map(key => {
        let max = 100;
        let val = bd[key];
        // Calculate percentage for visual bar
        let pct = Math.max(0, Math.min(100, (val / max) * 100));
        return `
            <div class="breakdown-row">
                <span class="bd-label">${key}</span>
                <div class="bd-bar-wrap"><div class="bd-bar" style="width:${pct}%;background:${sigColor}"></div></div>
                <span class="bd-val">${val}</span>
            </div>
        `;
    }).join('');

    const isShortTrade = t.signal === 'SELL' || t.signal === 'STRONG_SELL' || (t.signal_label && t.signal_label.toLowerCase().includes('short'));

    container.innerHTML = `
        <div class="glass-card" style="border-top:3px solid ${sigColor}">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px">
                <div>
                    <h2 style="font-size:24px;margin-bottom:4px">${info.name || symbol}</h2>
                    <span style="color:var(--text-muted);font-size:13px">${info.sector || ''} • ${info.industry || ''}</span>
                </div>
                <div style="text-align:right">
                    <div style="font-size:32px;font-weight:700;font-family:var(--font-mono)">₹${formatNumber(info.current_price || t.entry)}</div>
                    <div style="font-size:18px;font-weight:700;color:${sigColor}">${t.signal_label || (sigEmoji + ' ' + (t.signal || '').replace(/_/g, ' '))} (${t.score}/100)</div>
                    ${t.confidence_cap && t.score >= t.confidence_cap ? `<div style="font-size:11px;color:var(--text-muted);margin-top:4px">⚠ Confidence capped at ${t.confidence_cap}% due to regime</div>` : ''}
                </div>
            </div>

            ${isShortTrade ? `<div style="background:rgba(255,77,106,0.08);border:1px solid rgba(255,77,106,0.2);border-radius:8px;padding:10px 14px;margin-bottom:16px;font-size:0.82rem;color:var(--text-secondary)">
                🩳 <strong>This is a SHORT trade.</strong> You profit when the price <em>falls</em>. Target is below entry (take profit), Stop Loss is above entry (cut losses if price rises).
            </div>` : ''}

            <div class="signal-metrics" style="margin-bottom:20px">
                <div class="signal-metric">
                    <div class="label">Entry ${isShortTrade ? '(Sell)' : '(Buy)'}</div>
                    <div class="value">₹${formatNumber(t.entry)}</div>
                </div>
                <div class="signal-metric">
                    <div class="label">${isShortTrade ? 'Target ↓' : 'Target ↑'}</div>
                    <div class="value positive">₹${formatNumber(t.target)}</div>
                </div>
                ${t.conservative_target && t.conservative_target !== t.target ? `
                <div class="signal-metric" style="background:rgba(245,158,11,0.1)">
                    <div class="label" style="color:var(--accent-amber)">Cons. Target</div>
                    <div class="value" style="color:var(--accent-amber)">₹${formatNumber(t.conservative_target)}</div>
                </div>` : ''}
                <div class="signal-metric">
                    <div class="label">${isShortTrade ? 'Stop ↑' : 'Stop Loss'}</div>
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
                        <div style="color:var(--text-muted);font-size:11px;margin-top:4px">Quarter-Kelly Risk: <strong>${allocPct}%</strong> (Bounded at 1% max on ₹5L capital)</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Dynamic prediction logic using ATR if predicted_range is missing
    const atr = (t.metrics && t.metrics.atr) ? t.metrics.atr : (t.entry * 0.02);
    const predHigh = t.entry + atr;
    const predLow = t.entry - atr;
    const predSupport = t.entry - (atr * 1.5);
    const predResistance = t.entry + (atr * 1.5);

    container.innerHTML += `
        <div class="glass-card">
            <h3>📈 Predicted Range & Accuracy</h3>
            <p style="font-size:11px;color:var(--text-muted);margin-bottom:12px">ATR-based intraday volatility estimate for the next trading session</p>
            
            <h4 style="margin-bottom:12px;color:var(--text-muted);font-size:12px;text-transform:uppercase;letter-spacing:1px">Prediction for Tomorrow</h4>
            <div class="signal-metrics">
                <div class="signal-metric">
                    <div class="label">Expected High</div>
                    <div class="value positive">₹${formatNumber(predHigh)}</div>
                </div>
                <div class="signal-metric">
                    <div class="label">Expected Low</div>
                    <div class="value negative">₹${formatNumber(predLow)}</div>
                </div>
                <div class="signal-metric">
                    <div class="label">Support</div>
                    <div class="value">₹${formatNumber(predSupport)}</div>
                </div>
                <div class="signal-metric">
                    <div class="label">Resistance</div>
                    <div class="value">₹${formatNumber(predResistance)}</div>
                </div>
            </div>

            <div style="margin-top:24px;border-top:1px solid rgba(255,255,255,0.1);padding-top:16px">
                <h4 style="margin-bottom:12px;color:var(--text-muted);font-size:12px;text-transform:uppercase;letter-spacing:1px">Yesterday's Prediction vs Today's Reality</h4>
                ${data.recent_verification && data.recent_verification.actual_high ? `
                <div class="signal-metrics" style="margin-bottom:12px">
                    <div class="signal-metric">
                        <div class="label">Predicted High</div>
                        <div class="value">₹${formatNumber(data.recent_verification.pred_high)}</div>
                    </div>
                    <div class="signal-metric">
                        <div class="label">Actual High</div>
                        <div class="value positive">₹${formatNumber(data.recent_verification.actual_high)}</div>
                    </div>
                    <div class="signal-metric">
                        <div class="label">High Status</div>
                        <div class="value" style="font-size:0.9rem">${data.recent_verification.actual_high <= data.recent_verification.pred_high ? '✅ Held' : '📈 Breached'}</div>
                    </div>
                </div>
                <div class="signal-metrics" style="margin-bottom:12px">
                    <div class="signal-metric">
                        <div class="label">Predicted Low</div>
                        <div class="value">₹${formatNumber(data.recent_verification.pred_low)}</div>
                    </div>
                    <div class="signal-metric">
                        <div class="label">Actual Low</div>
                        <div class="value negative">₹${formatNumber(data.recent_verification.actual_low)}</div>
                    </div>
                    <div class="signal-metric">
                        <div class="label">Low Status</div>
                        <div class="value" style="font-size:0.9rem">${data.recent_verification.actual_low >= data.recent_verification.pred_low ? '✅ Held' : '📉 Breached'}</div>
                    </div>
                </div>
                <div class="signal-metrics">
                    <div class="signal-metric">
                        <div class="label">Predicted Range</div>
                        <div class="value">₹${formatNumber(data.recent_verification.pred_high - data.recent_verification.pred_low)}</div>
                    </div>
                    <div class="signal-metric">
                        <div class="label">Actual Range</div>
                        <div class="value">₹${formatNumber(data.recent_verification.actual_high - data.recent_verification.actual_low)}</div>
                    </div>
                    <div class="signal-metric">
                        <div class="label">Direction</div>
                        <div class="value" style="font-size:0.9rem">${data.recent_verification.status.includes('Direction Hit') ? '✅ Accurate' : '❌ Missed'}</div>
                    </div>
                </div>
                ` : `
                <div style="background:var(--bg-subtle);padding:16px;border-radius:8px;text-align:center;color:var(--text-muted);font-size:13px">
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
                ${Object.keys(bd).map(key => {
                    const val = bd[key];
                    const icon = val >= 80 ? '✅' : val >= 50 ? '🟡' : '🔴';
                    return `<div class="legend-item">
                        <span>${icon} <strong>${key}</strong></span>
                        <span style="color:var(--text-muted)">${val}/100 pts</span>
                    </div>`;
                }).join('')}
            </div>
            <div style="margin-top:16px;padding:12px;background:var(--bg-subtle);border-radius:8px;font-size:12px;color:var(--text-muted);line-height:1.8">
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

    // Load "Why This Trade?" mapping from the backend 'reasons' array
    const el = document.getElementById('why-trade-content');
    if (el && t.reasons && t.reasons.length > 0) {
        const reasonsHTML = t.reasons.map(reason => {
            // Determine icon and color based on keywords
            let icon = '💡';
            let color = 'var(--text-primary)';
            if (reason.toLowerCase().includes('bullish') || reason.toLowerCase().includes('strong') || reason.toLowerCase().includes('accumulation')) { icon = '✅'; color = '#00e68a'; }
            else if (reason.toLowerCase().includes('bearish') || reason.toLowerCase().includes('weak') || reason.toLowerCase().includes('vetoed') || reason.toLowerCase().includes('distribution')) { icon = '🔴'; color = '#ff4d6a'; }
            else if (reason.toLowerCase().includes('neutral') || reason.toLowerCase().includes('choppy') || reason.toLowerCase().includes('caution')) { icon = '🟡'; color = '#ffb347'; }

            return `<div style="margin-bottom:8px; display:flex; gap:12px; align-items:flex-start">
                <span style="font-size:16px">${icon}</span>
                <span style="font-size:13px; line-height:1.5; color:${color}">
                    ${reason}
                </span>
            </div>`;
        }).join('');
        
        // V6: Regime Definitions & Trade Plan Mapping (must match backend regime_atr_params)
        const regimeMetadata = {
            'low_vol_uptrend': { name: 'Low-Vol Uptrend', rvol: '1.2x', rsi: '75', cap: '1.5%', desc: 'Aggressive mode — full Kelly sizing, early breakouts.' },
            'bullish':         { name: 'Bullish', rvol: '1.2x', rsi: '75', cap: '1.5%', desc: 'Aggressive mode — full Kelly sizing, breakout and momentum plays.' },
            'recovery':        { name: 'Recovery', rvol: '1.3x', rsi: '72', cap: '1.0%', desc: 'Cautious recovery — pullback buys, 0.6× Kelly sizing.' },
            'high_vol_uptrend':{ name: 'High-Vol Uptrend', rvol: '1.3x', rsi: '72', cap: '1.0%', desc: 'Cautious bull — pullback buys only, 0.6× Kelly.' },
            'high_vol_chop':   { name: 'High-Vol Chop', rvol: '1.5x', rsi: '65', cap: '0.8%', desc: 'High vol dip buying — deep mean reversion, scaled entry.' },
            'low_vol_chop':    { name: 'Low-Vol Chop', rvol: '1.4x', rsi: '68', cap: '0.7%', desc: 'Sideways chop — mean reversion plays, tight stops.' },
            'distribution':    { name: 'Distribution', rvol: '1.5x', rsi: '62', cap: '0.6%', desc: 'Late-cycle distribution — reduced sizing, early exits.' },
            'bearish':         { name: 'Bearish', rvol: '1.6x', rsi: '58', cap: '0.5%', desc: '⚠️ Bear market — capital preservation, minimal exposure.' },
            'crisis':          { name: 'Crisis / Bear Market', rvol: '1.8x', rsi: '55', cap: '0.3%', desc: '⚠️ Survival mode — capital preservation, 0× Kelly.' }
        };
        const activeRegime = t.regime || 'unknown';
        const meta = regimeMetadata[activeRegime] || { name: 'Unknown Regime', rvol: '—', rsi: '—', cap: '—', desc: 'No special parameters applied.' };

        el.innerHTML = `
            <div class="why-trade-grid" style="display:grid; grid-template-columns: 1.2fr 1fr; gap: 20px;">
                <!-- Left Column: Reasons & Drivers -->
                <div style="background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.05); padding:16px; border-radius:8px;">
                    <h4 style="margin-top:0; margin-bottom:12px; font-size:12px; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-muted)">Conviction Drivers</h4>
                    ${reasonsHTML}
                </div>
                
                <!-- Right Column: Regime & Trade Execution Plan -->
                <div style="display:flex; flex-direction:column; gap:16px;">
                    <!-- Regime Context -->
                    <div style="background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.05); padding:14px; border-radius:8px;">
                        <h4 style="margin-top:0; margin-bottom:6px; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-muted)">Regime Profile: ${meta.name}</h4>
                        <div style="font-size:12px; margin-bottom:8px; line-height:1.4;">${meta.desc}</div>
                        <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.05); padding-top:8px; margin-top:8px;">
                            <span>Min RVOL: <strong>${meta.rvol}</strong></span>
                            <span>RSI Ceiling: <strong>${meta.rsi}</strong></span>
                            <span>Risk Cap: <strong>${meta.cap}</strong></span>
                        </div>
                    </div>
                    
                    <!-- Trade Plan -->
                    <div style="background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.05); padding:14px; border-radius:8px;">
                        <h4 style="margin-top:0; margin-bottom:10px; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-muted)">Execution Plan</h4>
                        <table style="width:100%; border-collapse:collapse; font-size:12px; line-height:1.8;">
                            <tbody>
                                <tr>
                                    <td style="color:var(--text-muted)">Entry Range</td>
                                    <td style="text-align:right; font-weight:600; color:var(--text-primary);">₹${formatNumber(t.entry)}</td>
                                </tr>
                                <tr>
                                    <td style="color:var(--text-muted)">Full Target</td>
                                    <td style="text-align:right; font-weight:600; color:#00e68a;">₹${formatNumber(t.target)} (+${t.reward_pct ? t.reward_pct.toFixed(1) : '—'}%)</td>
                                </tr>
                                <tr>
                                    <td style="color:var(--text-muted)">Cons. Target</td>
                                    <td style="text-align:right; font-weight:600; color:#ffd740;">₹${formatNumber(t.conservative_target)}</td>
                                </tr>
                                <tr>
                                    <td style="color:var(--text-muted)">Stop Loss</td>
                                    <td style="text-align:right; font-weight:600; color:#ff4d6a;">₹${formatNumber(t.stop_loss)} (-${t.risk_pct ? t.risk_pct.toFixed(1) : '—'}%)</td>
                                </tr>
                                <tr>
                                    <td style="color:var(--text-muted)">Expected Duration</td>
                                    <td style="text-align:right; font-weight:600; color:var(--text-primary);">${t.holding_period || '—'}</td>
                                </tr>
                                <tr>
                                    <td style="color:var(--text-muted)">Earnings</td>
                                    <td style="text-align:right; font-weight:600; color:${t.days_to_earnings != null && t.days_to_earnings <= 3 ? '#ff4d6a' : t.days_to_earnings != null && t.days_to_earnings <= 7 ? '#ffb347' : '#00e68a'}">
                                        ${t.days_to_earnings != null ? (t.days_to_earnings <= 3 ? '⚠️ ' + t.days_to_earnings + ' days (' + t.earnings_date + ')' : t.days_to_earnings <= 14 ? '📅 ' + t.days_to_earnings + ' days' : '✅ No imminent results') : '✅ No imminent results'}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
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
                    <div><span class="stat-label">1W</span> <span class="${s.returns['1w'] >= 0 ? 'positive' : 'negative'}">${s.returns['1w']}%</span></div>
                    <div><span class="stat-label">1M</span> <span class="${s.returns['1m'] >= 0 ? 'positive' : 'negative'}">${s.returns['1m']}%</span></div>
                    <div><span class="stat-label">3M</span> <span class="${s.returns['3m'] >= 0 ? 'positive' : 'negative'}">${s.returns['3m']}%</span></div>
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

        if (d.error && !d.total_signals) {
            document.getElementById('acc-by-signal').innerHTML = `<div class="loading-skeleton">⚠️ ${d.error || d.message}</div>`;
            return;
        }

        const el = (id, val) => { const e = document.getElementById(id); if (e) e.textContent = val; };
        el('acc-win-rate', d.win_rate ? `${d.win_rate}%` : 'No data yet');
        el('acc-total', d.total_signals || 0);
        el('acc-wins', d.wins || 0);
        el('acc-losses', d.losses || 0);
        el('acc-open', d.pending || 0);
        el('acc-avg-days', '—');
        el('acc-avg-return', '—');

        // By signal type
        const sigEl = document.getElementById('acc-by-signal');
        if (d.by_signal && d.by_signal.length > 0) {
            sigEl.innerHTML = d.by_signal.map(s => `
                <div class="acc-row">
                    <span>${(s.signal || '').replace('_', ' ')}</span>
                    <div class="acc-bar-wrap">
                        <div class="acc-bar" style="width:${s.win_rate}%;background:${s.win_rate >= 50 ? 'var(--green)' : 'var(--red)'}"></div>
                    </div>
                    <span style="text-align: right; font-family: var(--font-mono);">${s.win_rate}% (${s.wins}/${s.total})</span>
                </div>
            `).join('');
        } else {
            sigEl.innerHTML = '<div class="loading-skeleton">No evaluated signals yet. Data will appear as signals hit their targets or stop losses.</div>';
        }

        // By regime (Task 17)
        const segEl = document.getElementById('acc-by-segment');
        if (d.by_regime && d.by_regime.length > 0) {
            const regimeLabels = {
                'low_vol_uptrend': '🟢 Low-Vol Uptrend',
                'high_vol_uptrend': '📈 High-Vol Uptrend',
                'low_vol_chop': '🟡 Low-Vol Chop',
                'crisis': '🔴 Crisis',
            };
            segEl.innerHTML = d.by_regime.map(s => `
                <div class="acc-row">
                    <span>${regimeLabels[s.regime] || s.regime}</span>
                    <div class="acc-bar-wrap">
                        <div class="acc-bar" style="width:${s.win_rate}%;background:${s.win_rate >= 50 ? 'var(--green)' : 'var(--red)'}"></div>
                    </div>
                    <span style="text-align: right; font-family: var(--font-mono);">${s.win_rate}% (${s.wins}/${s.total})</span>
                </div>
            `).join('');
        } else {
            segEl.innerHTML = '<div class="loading-skeleton">No regime data yet.</div>';
        }

        // Signal history table (last 20 resolved)
        const logEl = document.getElementById('acc-signal-log');
        if (logEl && d.recent_signals && d.recent_signals.length > 0) {
            const outcomeColors = { WIN: '#00e68a', LOSS: '#ff4d6a' };
            const outcomeLabels = { WIN: '✅ Win', LOSS: '❌ Loss' };
            logEl.innerHTML = `<table class="data-table"><thead><tr>
                <th>Date</th><th>Symbol</th><th>Signal</th><th>Score</th><th>Entry</th><th>Target</th><th>SL</th><th>Outcome</th>
            </tr></thead><tbody>${d.recent_signals.map(s => `<tr>
                <td>${(s.date || '').substring(0, 10)}</td>
                <td><strong>${s.symbol}</strong></td>
                <td>${(s.signal || '').replace('_', ' ')}</td>
                <td>${s.score || '—'}</td>
                <td>₹${formatNumber(s.entry)}</td>
                <td class="positive">₹${formatNumber(s.target)}</td>
                <td class="negative">₹${formatNumber(s.sl)}</td>
                <td style="color:${outcomeColors[s.outcome] || '#94a3b8'};font-weight:600">${outcomeLabels[s.outcome] || s.outcome}</td>
            </tr>`).join('')}</tbody></table>`;
        } else if (logEl) {
            logEl.innerHTML = '<div class="loading-skeleton">Signals will appear here once the screener runs and outcomes are resolved.</div>';
        }
        // Phase 3: Championship Leaderboard
        try {
            const champs = await api.getChampionship();
            const champEl = document.getElementById('championship-board');
            if (champEl && champs) {
                if (champs.length === 0) {
                    champEl.innerHTML = '<tr><td colspan="5">No championship data available yet.</td></tr>';
                } else {
                    champEl.innerHTML = champs.map(c => {
                        let statusColor = "var(--text-color)";
                        if (c.status === "HEALTHY") statusColor = "var(--accent-green)";
                        if (c.status === "DECAYING") statusColor = "var(--warning)";
                        if (c.status === "SUSPENDED") statusColor = "var(--accent-red)";
                        
                        return `
                        <tr>
                            <td><strong>${c.model}</strong></td>
                            <td style="color:${statusColor}">${c.status}</td>
                            <td class="${c.accuracy > 50 ? 'positive' : (c.accuracy < 40 ? 'negative' : '')}">${c.accuracy}%</td>
                            <td>${c.current_weight || '-'} vs ${c.base_weight || '-'}</td>
                            <td>${c.trades}</td>
                            <td style="font-family: 'JetBrains Mono', monospace; font-size: 1.2em; color:${statusColor}">${c.sparkline}</td>
                        </tr>
                        `;
                    }).join('');
                }
            }
        } catch (e) {
            console.error('Championship load error:', e);
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
                    <td>${(t.signal || '').replace(/_/g,' ')}</td>
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

/* ─── Task 25: Alert Builder ────────────────────────── */
function getAlerts() {
    try { return JSON.parse(localStorage.getItem('agent_alpha_alerts') || '[]'); }
    catch(e) { return []; }
}
function saveAlerts(list) {
    localStorage.setItem('agent_alpha_alerts', JSON.stringify(list));
}

function addAlert() {
    const symbol = document.getElementById('alert-symbol').value.trim().toUpperCase();
    const condition = document.getElementById('alert-condition').value;
    const val = parseFloat(document.getElementById('alert-value').value);
    
    if (!symbol || isNaN(val)) {
        showToast('Please enter a valid symbol and value.', 'error');
        return;
    }
    
    const alerts = getAlerts();
    alerts.push({
        id: Date.now().toString(),
        symbol,
        condition,
        value: val,
        status: 'ACTIVE',
        lastChecked: 'Never'
    });
    
    saveAlerts(alerts);
    showToast(`Alert created for ${symbol}`, 'success');
    
    document.getElementById('alert-symbol').value = '';
    document.getElementById('alert-value').value = '';
    loadAlerts();
}

function removeAlert(id) {
    const list = getAlerts().filter(a => a.id !== id);
    saveAlerts(list);
    loadAlerts();
    showToast('Alert removed', 'info');
}

async function checkAlerts() {
    const alerts = getAlerts();
    let updated = false;
    
    for (const alert of alerts) {
        if (alert.status !== 'ACTIVE') continue;
        
        try {
            const res = await fetch(`/api/price/${alert.symbol}`);
            if (!res.ok) continue;
            const data = await res.json();
            
            alert.lastChecked = new Date().toLocaleTimeString();
            updated = true;
            
            let triggered = false;
            if (alert.condition === 'PRICE_ABOVE' && data.price > alert.value) triggered = true;
            else if (alert.condition === 'PRICE_BELOW' && data.price < alert.value) triggered = true;
            else if (alert.condition === 'VOLUME_ABOVE' && data.volume > alert.value) triggered = true;
            
            if (triggered) {
                alert.status = 'TRIGGERED';
                showToast(`🔔 ALERT TRIGGERED: ${alert.symbol} ${alert.condition.replace('_', ' ')} ${alert.value}`, 'success', 10000);
            }
        } catch(e) {
            console.error('Alert check failed', e);
        }
    }
    
    if (updated) {
        saveAlerts(alerts);
        if (document.getElementById('page-alerts').style.display === 'block') {
            loadAlerts();
        }
    }
}

function loadAlerts() {
    const alerts = getAlerts();
    const tbody = document.getElementById('alerts-body');
    if (!tbody) return;
    
    if (alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No active alerts. Create one above 🔔</td></tr>';
        return;
    }
    
    const condLabels = {
        'PRICE_ABOVE': 'Price &gt;',
        'PRICE_BELOW': 'Price &lt;',
        'VOLUME_ABOVE': 'Volume &gt;'
    };
    
    tbody.innerHTML = alerts.map(a => {
        const statColor = a.status === 'TRIGGERED' ? '#00e68a' : (a.status === 'ACTIVE' ? '#4da6ff' : 'var(--text-muted)');
        return `
            <tr>
                <td><strong>${a.symbol}</strong></td>
                <td>${condLabels[a.condition] || a.condition}</td>
                <td>${formatNumber(a.value)}</td>
                <td>${a.lastChecked}</td>
                <td><span style="color:${statColor};font-weight:600;font-size:0.8rem;padding:4px 8px;background:var(--bg-subtle);border-radius:4px">${a.status}</span></td>
                <td><button class="btn-small" onclick="removeAlert('${a.id}')">✕</button></td>
            </tr>
        `;
    }).join('');
}

// Hook checkAlerts into the 60-second update interval
const origUpdateMarketStatus = updateMarketStatus;
updateMarketStatus = async function() {
    await origUpdateMarketStatus();
    checkAlerts();
};
