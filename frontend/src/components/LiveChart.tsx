'use client';
import React, { useRef, useEffect, useState } from 'react';
import {
    createChart, ColorType, CrosshairMode,
    CandlestickSeries, LineSeries, HistogramSeries,
} from 'lightweight-charts';
import type { IChartApi, Time } from 'lightweight-charts';

const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

// ── Interval / period config ─────────────────────────────────────────────────
const INTERVALS = [
    { key: '15m', label: '15m', period: '5d' },
    { key: '1h', label: '1H', period: '1mo' },
    { key: '1d', label: '1D', period: '6mo' },
    { key: '1wk', label: '1W', period: '2y' },
    { key: '1mo', label: '1M', period: '5y' },
];

const OVERLAY_CONFIG: Record<string, { color: string; label: string; width: number }> = {
    sma20: { color: '#f59e0b', label: 'SMA 20', width: 1 },
    sma50: { color: '#3b82f6', label: 'SMA 50', width: 1 },
    ema9: { color: '#10b981', label: 'EMA 9', width: 1 },
    ema21: { color: '#8b5cf6', label: 'EMA 21', width: 1 },
    bb_upper: { color: '#6366f1', label: 'BB Upper', width: 1 },
    bb_lower: { color: '#6366f1', label: 'BB Lower', width: 1 },
};

interface LiveChartProps {
    symbol: string;
    patterns?: any[];
}

export default function LiveChart({ symbol, patterns }: LiveChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const rsiContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const rsiChartRef = useRef<IChartApi | null>(null);
    const [activeInterval, setActiveInterval] = useState('1d');
    const [chartData, setChartData] = useState<any>(null);
    const [chartLoading, setChartLoading] = useState(true);
    const [overlays, setOverlays] = useState<Record<string, boolean>>({
        sma20: true, sma50: true, ema9: false, ema21: false, bb_upper: false, bb_lower: false,
    });

    // Fetch chart data
    useEffect(() => {
        setChartLoading(true);
        const intv = INTERVALS.find(i => i.key === activeInterval);
        const period = intv?.period || '6mo';
        fetch(`${API}/api/chart/ohlcv?symbol=${encodeURIComponent(symbol)}&interval=${activeInterval}&period=${period}`)
            .then(r => r.json())
            .then(d => { setChartData(d); setChartLoading(false); })
            .catch(() => setChartLoading(false));
    }, [symbol, activeInterval]);

    // Render chart
    useEffect(() => {
        if (!chartData || !chartContainerRef.current) return;

        // Clean up previous charts
        if (chartRef.current) { chartRef.current.remove(); chartRef.current = null; }
        if (rsiChartRef.current) { rsiChartRef.current.remove(); rsiChartRef.current = null; }

        const container = chartContainerRef.current;

        // ── Main chart ────────────────────────────────────────────────────────
        const chart = createChart(container, {
            width: container.clientWidth,
            height: 420,
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: '#94a3b8',
                fontSize: 11,
            },
            grid: {
                vertLines: { color: 'rgba(255,255,255,0.03)' },
                horzLines: { color: 'rgba(255,255,255,0.03)' },
            },
            crosshair: { mode: CrosshairMode.Normal },
            rightPriceScale: {
                borderColor: 'rgba(255,255,255,0.1)',
                scaleMargins: { top: 0.05, bottom: 0.25 },
            },
            timeScale: {
                borderColor: 'rgba(255,255,255,0.1)',
                timeVisible: activeInterval !== '1d' && activeInterval !== '1wk' && activeInterval !== '1mo',
            },
        });
        chartRef.current = chart;

        // Candlestick series
        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: '#4ade80',
            downColor: '#f87171',
            borderUpColor: '#4ade80',
            borderDownColor: '#f87171',
            wickUpColor: '#4ade8088',
            wickDownColor: '#f8717188',
        });
        candleSeries.setData(chartData.candles);

        // Volume series
        if (chartData.volume?.length) {
            const volumeSeries = chart.addSeries(HistogramSeries, {
                priceFormat: { type: 'volume' },
                priceScaleId: 'volume',
            });
            chart.priceScale('volume').applyOptions({
                scaleMargins: { top: 0.8, bottom: 0.01 },
            });
            volumeSeries.setData(chartData.volume);
        }

        // Overlay lines
        if (chartData.overlays) {
            Object.entries(chartData.overlays).forEach(([key, data]) => {
                if (!overlays[key] || !(data as any[]).length) return;
                const cfg = OVERLAY_CONFIG[key];
                if (!cfg) return;
                const series = chart.addSeries(LineSeries, {
                    color: cfg.color,
                    lineWidth: cfg.width as any,
                    priceLineVisible: false,
                    lastValueVisible: false,
                    crosshairMarkerVisible: false,
                });
                series.setData(data as any[]);
            });
        }

        // Pattern markers
        if (patterns && patterns.length > 0) {
            const markers = patterns
                .filter((p: any) => p.date)
                .map((p: any) => ({
                    time: Math.floor(new Date(p.date).getTime() / 1000) as Time,
                    position: p.bias === 'Bearish' ? 'aboveBar' as const : 'belowBar' as const,
                    color: p.bias === 'Bearish' ? '#f87171' : '#4ade80',
                    shape: p.bias === 'Bearish' ? 'arrowDown' as const : 'arrowUp' as const,
                    text: p.name?.slice(0, 15) || 'Pattern',
                }));
            if (markers.length) {
                candleSeries.setMarkers(markers);
            }
        }

        // ── RSI sub-chart ─────────────────────────────────────────────────────
        if (rsiContainerRef.current && chartData.indicators?.rsi?.length) {
            const rsiChart = createChart(rsiContainerRef.current, {
                width: container.clientWidth,
                height: 100,
                layout: {
                    background: { type: ColorType.Solid, color: 'transparent' },
                    textColor: '#94a3b8',
                    fontSize: 10,
                },
                grid: {
                    vertLines: { color: 'rgba(255,255,255,0.02)' },
                    horzLines: { color: 'rgba(255,255,255,0.02)' },
                },
                rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)' },
                timeScale: { visible: false },
            });
            rsiChartRef.current = rsiChart;

            const rsiSeries = rsiChart.addSeries(LineSeries, {
                color: '#8b5cf6',
                lineWidth: 1,
                priceLineVisible: false,
            });
            rsiSeries.setData(chartData.indicators.rsi);

            // Overbought/oversold lines
            const rsiTimes = chartData.indicators.rsi.map((d: any) => d.time);
            if (rsiTimes.length >= 2) {
                const obLine = rsiChart.addSeries(LineSeries, {
                    color: '#f8717144',
                    lineWidth: 1,
                    lineStyle: 2,
                    priceLineVisible: false,
                    lastValueVisible: false,
                    crosshairMarkerVisible: false,
                });
                obLine.setData([
                    { time: rsiTimes[0] as Time, value: 70 },
                    { time: rsiTimes[rsiTimes.length - 1] as Time, value: 70 },
                ]);
                const osLine = rsiChart.addSeries(LineSeries, {
                    color: '#4ade8044',
                    lineWidth: 1,
                    lineStyle: 2,
                    priceLineVisible: false,
                    lastValueVisible: false,
                    crosshairMarkerVisible: false,
                });
                osLine.setData([
                    { time: rsiTimes[0] as Time, value: 30 },
                    { time: rsiTimes[rsiTimes.length - 1] as Time, value: 30 },
                ]);
            }

            // Sync time scales
            chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
                if (range) rsiChart.timeScale().setVisibleLogicalRange(range);
            });
            rsiChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
                if (range) chart.timeScale().setVisibleLogicalRange(range);
            });
        }

        // Resize handler
        const handleResize = () => {
            if (chartRef.current && container) {
                chartRef.current.applyOptions({ width: container.clientWidth });
            }
            if (rsiChartRef.current && container) {
                rsiChartRef.current.applyOptions({ width: container.clientWidth });
            }
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (chartRef.current) { chartRef.current.remove(); chartRef.current = null; }
            if (rsiChartRef.current) { rsiChartRef.current.remove(); rsiChartRef.current = null; }
        };
    }, [chartData, overlays, patterns]);

    return (
        <div style={{
            background: 'rgba(0,0,0,0.15)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 14,
            padding: '16px 16px 12px',
            marginBottom: 20,
        }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10, marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 16, fontWeight: 900, color: 'var(--text-primary)' }}>{symbol}</span>
                    {chartData?.price && (
                        <>
                            <span style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)' }}>
                                {chartData.price.last.toLocaleString()}
                            </span>
                            <span style={{
                                fontSize: 13, fontWeight: 700,
                                color: chartData.price.change >= 0 ? '#4ade80' : '#f87171',
                            }}>
                                {chartData.price.change >= 0 ? '+' : ''}{chartData.price.change.toFixed(2)} ({chartData.price.change_pct.toFixed(2)}%)
                            </span>
                        </>
                    )}
                </div>

                {/* Interval selector */}
                <div style={{ display: 'flex', gap: 4 }}>
                    {INTERVALS.map(int => (
                        <button key={int.key} onClick={() => setActiveInterval(int.key)} style={{
                            padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                            cursor: 'pointer',
                            border: activeInterval === int.key ? '1px solid rgba(139,92,246,0.5)' : '1px solid rgba(255,255,255,0.08)',
                            background: activeInterval === int.key ? 'rgba(139,92,246,0.2)' : 'transparent',
                            color: activeInterval === int.key ? '#c4b5fd' : '#64748b',
                        }}>
                            {int.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Overlay toggles */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                {Object.entries(OVERLAY_CONFIG).map(([key, cfg]) => (
                    <button key={key} onClick={() => setOverlays(prev => ({ ...prev, [key]: !prev[key] }))} style={{
                        padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                        cursor: 'pointer',
                        border: `1px solid ${overlays[key] ? cfg.color : 'rgba(255,255,255,0.08)'}`,
                        background: overlays[key] ? `${cfg.color}22` : 'transparent',
                        color: overlays[key] ? cfg.color : '#475569',
                    }}>
                        {cfg.label}
                    </button>
                ))}
            </div>

            {/* Chart */}
            {chartLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)', height: 420 }}>
                    <span className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
                    Loading chart data…
                </div>
            ) : (
                <>
                    <div ref={chartContainerRef} style={{ borderRadius: 8, overflow: 'hidden' }} />
                    {/* RSI sub-chart */}
                    <div style={{ marginTop: 2, position: 'relative' }}>
                        <div style={{ position: 'absolute', top: 4, left: 8, fontSize: 9, fontWeight: 700, color: '#8b5cf6', zIndex: 1, pointerEvents: 'none' }}>RSI (14)</div>
                        <div ref={rsiContainerRef} style={{ borderRadius: 8, overflow: 'hidden' }} />
                    </div>

                    {/* Price info bar */}
                    {chartData?.price && (
                        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8, padding: '6px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                                52W High: <span style={{ color: '#4ade80', fontWeight: 700 }}>{chartData.price.high_52w?.toLocaleString()}</span>
                            </div>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                                52W Low: <span style={{ color: '#f87171', fontWeight: 700 }}>{chartData.price.low_52w?.toLocaleString()}</span>
                            </div>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                                Candles: <span style={{ fontWeight: 700, color: '#94a3b8' }}>{chartData.total_candles}</span>
                            </div>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                                Interval: <span style={{ fontWeight: 700, color: '#c4b5fd' }}>{chartData.interval}</span>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
