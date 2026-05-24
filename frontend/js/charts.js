/**
 * Agent Alpha v4.0 — Chart Module (Obsidian Terminal Dark Theme)
 * TradingView Lightweight Charts — Institutional dark mode
 */
const Charts = {
    instances: {},

    createAreaChart(containerId, data, color = '#00FF88') {
        const container = document.getElementById(containerId);
        if (!container || !data || !data.length) return null;

        container.innerHTML = '';

        const chart = LightweightCharts.createChart(container, {
            width: container.clientWidth,
            height: container.clientHeight || 280,
            layout: {
                background: { type: 'solid', color: 'transparent' },
                textColor: '#8b95a8',
                fontSize: 11,
                fontFamily: "'Inter', sans-serif",
            },
            grid: {
                vertLines: { color: 'rgba(0, 255, 136, 0.03)' },
                horzLines: { color: 'rgba(0, 255, 136, 0.03)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: { color: 'rgba(255,255,255,0.15)', width: 1, style: 2 },
                horzLine: { color: 'rgba(255,255,255,0.15)', width: 1, style: 2 },
            },
            rightPriceScale: {
                borderColor: 'rgba(255,255,255,0.08)',
            },
            timeScale: {
                borderColor: 'rgba(255,255,255,0.08)',
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
            const w = container.clientWidth;
            const h = container.clientHeight || 280;
            if (w > 0 && h > 0) {
                chart.applyOptions({ width: w, height: h });
            }
        });
        ro.observe(container);

        return chart;
    },

    createCandlestickChart(containerId, data) {
        const container = document.getElementById(containerId);
        if (!container || !data || !data.length) return null;

        container.innerHTML = '';

        const chart = LightweightCharts.createChart(container, {
            width: container.clientWidth,
            height: container.clientHeight || 280,
            layout: {
                background: { type: 'solid', color: 'transparent' },
                textColor: '#8b95a8',
                fontSize: 11,
                fontFamily: "'Inter', sans-serif",
            },
            grid: {
                vertLines: { color: 'rgba(0, 255, 136, 0.03)' },
                horzLines: { color: 'rgba(0, 255, 136, 0.03)' },
            },
            crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
            rightPriceScale: { borderColor: 'rgba(255,255,255,0.08)' },
            timeScale: { borderColor: 'rgba(255,255,255,0.08)' },
        });

        const series = chart.addCandlestickSeries({
            upColor: '#00FF88',
            downColor: '#ff3366',
            borderUpColor: '#00FF88',
            borderDownColor: '#ff3366',
            wickUpColor: '#00FF88',
            wickDownColor: '#ff3366',
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
            const w = container.clientWidth;
            const h = container.clientHeight || 280;
            if (w > 0 && h > 0) {
                chart.applyOptions({ width: w, height: h });
            }
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
