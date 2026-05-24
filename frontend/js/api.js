/**
 * Agent Alpha — API Client
 * Handles all backend communication
 */
const API_BASE = window.location.origin + '/api';

const api = {
    async get(endpoint) {
        try {
            // 10-minute timeout for long screener scans
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 600000);
            const res = await fetch(`${API_BASE}${endpoint}`, { signal: controller.signal });
            clearTimeout(timeoutId);
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error(`GET ${endpoint} failed:`, err);
            return null;
        }
    },

    async post(endpoint, data) {
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error(`POST ${endpoint} failed:`, err);
            return null;
        }
    },

    async del(endpoint) {
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE' });
            return await res.json();
        } catch (err) {
            console.error(`DELETE ${endpoint} failed:`, err);
            return null;
        }
    },

    // Convenience methods
    getMarketOverview: () => api.get('/market/overview'),
    getPortfolio: () => api.get('/portfolio'),
    getStockDetail: (symbol) => api.get(`/stock/${symbol}`),
    getStockChart: (symbol, period) => api.get(`/stock/${symbol}/chart?period=${period || '1y'}`),
    getIndexData: (symbol, period) => api.get(`/market/index/${encodeURIComponent(symbol)}?period=${period || '6mo'}`),
    getScreenerTop: (n, segment, direction) => api.get(`/screener/top?n=${n || 10}&segment=${segment || 'NIFTY_50'}&direction=${direction || 'LONG'}`),
    getSignals: () => api.get('/signals'),
    generateSignals: () => api.get('/signals/generate'),
    getMfDetail: (code) => api.get(`/mf/${code}`),
    addHolding: (data) => api.post('/portfolio/add', data),
    removeHolding: (id) => api.del(`/portfolio/${id}`),
    
    // Arena Engine
    getArenaStatus: () => api.get('/arena/status'),
    executeArena: () => api.post('/arena/execute', {}),

    // Accuracy & Championship
    getAccuracyStats: () => api.get('/accuracy/stats'),
    getChampionship: () => api.get('/championship'),
    sendTelegramAlert: () => api.post('/bot/alert', {}),

    // Backward compat aliases
    getPaperPortfolio: () => api.get('/arena/status'),
    getPaperTrades: () => api.get('/arena/status'),
    getPaperEquityCurve: () => api.get('/arena/status'),
    getPaperStats: () => api.get('/arena/status'),
    executePaperTrade: () => api.post('/arena/execute', {}),

    // Market Regime
    getRegime: () => api.get('/regime'),
};
