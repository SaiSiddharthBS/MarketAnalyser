/**
 * Agent Alpha v3.0 — Chart Module (Light Theme)
 * TradingView Lightweight Charts — Institutional look
 */
const Charts = {
    instances: {},

    createAreaChart(containerId, data, color = '#6366f1') {
        const container = document.getElementById(containerId);
        if (!container || !data || !data.length) return null;

        container.innerHTML = '';

        const chart = LightweightCharts.createChart(container, {
            layout: {
                background: { type: 'solid', color: 'transparent' },
                textColor: '#94a3b8',
                fontSize: 11,
                fontFamily: "'Inter', sans-serif",
            },
            grid: {
                vertLines: { color: '#f1f5f9' },
                horzLines: { color: '#f1f5f9' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: { color: '#cbd5e1', width: 1, style: 2 },
                horzLine: { color: '#cbd5e1', width: 1, style: 2 },
            },
            rightPriceScale: {
                borderColor: '#e2e8f0',
            },
            timeScale: {
                borderColor: '#e2e8f0',
                timeVisible: false,
            },
            handleScroll: { mouseWheel: true, pressedMouseMove: true },
            handleScale: { mouseWheel: true, pinch: true },
        });

        const series = chart.addAreaSeries({
            topColor: color + '30',
            bottomColor: color + '05',
            lineColor: color,
            lineWidth: 2,
        });

        const chartData = data
            .filter(d => d.Date || d.date)
            .map(d => ({
                time: (d.Date || d.date).substring(0, 10),
                value: d.Close || d.close || d.nav || 0,
            }))
            .sort((a, b) => a.time.localeCompare(b.time));

        if (chartData.length > 0) {
            series.setData(chartData);
            chart.timeScale().fitContent();
        }

        this.instances[containerId] = chart;

        const ro = new ResizeObserver(() => {
            chart.applyOptions({
                width: container.clientWidth,
                height: container.clientHeight,
            });
        });
        ro.observe(container);

        return chart;
    },

    createCandlestickChart(containerId, data) {
        const container = document.getElementById(containerId);
        if (!container || !data || !data.length) return null;

        container.innerHTML = '';

        const chart = LightweightCharts.createChart(container, {
            layout: {
                background: { type: 'solid', color: 'transparent' },
                textColor: '#94a3b8',
                fontSize: 11,
                fontFamily: "'Inter', sans-serif",
            },
            grid: {
                vertLines: { color: '#f1f5f9' },
                horzLines: { color: '#f1f5f9' },
            },
            crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
            rightPriceScale: { borderColor: '#e2e8f0' },
            timeScale: { borderColor: '#e2e8f0' },
        });

        const series = chart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderUpColor: '#10b981',
            borderDownColor: '#ef4444',
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });

        const chartData = data
            .filter(d => d.Date || d.date)
            .map(d => ({
                time: (d.Date || d.date).substring(0, 10),
                open: d.Open || d.open,
                high: d.High || d.high,
                low: d.Low || d.low,
                close: d.Close || d.close,
            }))
            .sort((a, b) => a.time.localeCompare(b.time));

        if (chartData.length > 0) {
            series.setData(chartData);
            chart.timeScale().fitContent();
        }

        this.instances[containerId] = chart;

        const ro = new ResizeObserver(() => {
            chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
        });
        ro.observe(container);

        return chart;
    },

    destroy(containerId) {
        if (this.instances[containerId]) {
            this.instances[containerId].remove();
            delete this.instances[containerId];
        }
    }
};
