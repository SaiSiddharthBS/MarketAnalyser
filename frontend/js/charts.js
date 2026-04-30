/**
 * Agent Alpha — Chart Module
 * TradingView Lightweight Charts integration
 */
const Charts = {
    instances: {},

    createAreaChart(containerId, data, color = '#3b82f6') {
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
                vertLines: { color: 'rgba(255,255,255,0.03)' },
                horzLines: { color: 'rgba(255,255,255,0.03)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: { color: 'rgba(255,255,255,0.1)', width: 1, style: 2 },
                horzLine: { color: 'rgba(255,255,255,0.1)', width: 1, style: 2 },
            },
            rightPriceScale: {
                borderColor: 'rgba(255,255,255,0.05)',
            },
            timeScale: {
                borderColor: 'rgba(255,255,255,0.05)',
                timeVisible: false,
            },
            handleScroll: { mouseWheel: true, pressedMouseMove: true },
            handleScale: { mouseWheel: true, pinch: true },
        });

        const series = chart.addAreaSeries({
            topColor: color + '40',
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

        // Responsive resize
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
                vertLines: { color: 'rgba(255,255,255,0.03)' },
                horzLines: { color: 'rgba(255,255,255,0.03)' },
            },
            crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
            rightPriceScale: { borderColor: 'rgba(255,255,255,0.05)' },
            timeScale: { borderColor: 'rgba(255,255,255,0.05)' },
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
