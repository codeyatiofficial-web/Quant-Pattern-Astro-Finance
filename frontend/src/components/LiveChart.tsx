'use client';
import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
    createChart, ColorType, CrosshairMode,
    CandlestickSeries, LineSeries, HistogramSeries,
} from 'lightweight-charts';
import type { IChartApi, Time } from 'lightweight-charts';

const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

// ── Interval / period config ─────────────────────────────────────────────────
const INTERVALS = [
    { key: '1m', label: '1m', period: '1d' },
    { key: '3m', label: '3m', period: '1d' },
    { key: '5m', label: '5m', period: '5d' },
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

// ── Backtest popup component ─────────────────────────────────────────────────
function BacktestPopup({ pattern, onClose }: { pattern: any; onClose: () => void }) {
    const bt = pattern?.backtest;
    if (!bt) return null;
    const total = (bt.wins || 0) + (bt.losses || 0);
    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)', zIndex: 9999,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        }} onClick={onClose}>
            <div onClick={e => e.stopPropagation()} style={{
                background: '#1a1f35', border: '1px solid rgba(139,92,246,0.3)',
                borderRadius: 16, padding: 24, maxWidth: 520, width: '95%',
                maxHeight: '80vh', overflowY: 'auto', color: '#e2e8f0',
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <h3 style={{ margin: 0, fontSize: 16, fontWeight: 800 }}>
                        <span style={{ color: pattern.bias === 'Bullish' ? '#4ade80' : pattern.bias === 'Bearish' ? '#f87171' : '#94a3b8' }}>
                            {pattern.bias === 'Bullish' ? '▲' : pattern.bias === 'Bearish' ? '▼' : '●'}
                        </span>{' '}
                        {pattern.name}
                    </h3>
                    <button onClick={onClose} style={{
                        background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 8, padding: '4px 10px', color: '#94a3b8', cursor: 'pointer', fontSize: 13,
                    }}>✕</button>
                </div>

                {/* Stats grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 16 }}>
                    <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: 12, textAlign: 'center' }}>
                        <div style={{ fontSize: 22, fontWeight: 900, color: bt.win_rate >= 60 ? '#4ade80' : bt.win_rate >= 40 ? '#fbbf24' : '#f87171' }}>
                            {bt.win_rate}%
                        </div>
                        <div style={{ fontSize: 9, color: '#64748b', fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: 1 }}>Win Rate</div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: 12, textAlign: 'center' }}>
                        <div style={{ fontSize: 22, fontWeight: 900, color: '#c4b5fd' }}>{total}</div>
                        <div style={{ fontSize: 9, color: '#64748b', fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: 1 }}>Total Trades</div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: 12, textAlign: 'center' }}>
                        <div style={{ fontSize: 22, fontWeight: 900, color: (bt.avg_return || 0) >= 0 ? '#4ade80' : '#f87171' }}>
                            {(bt.avg_return || 0) >= 0 ? '+' : ''}{(bt.avg_return || 0).toFixed(2)}%
                        </div>
                        <div style={{ fontSize: 9, color: '#64748b', fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: 1 }}>Avg Return</div>
                    </div>
                </div>

                {/* Extra stats */}
                <div style={{ display: 'flex', gap: 12, marginBottom: 16, fontSize: 11 }}>
                    <div style={{ flex: 1, background: 'rgba(255,255,255,0.02)', borderRadius: 8, padding: 10 }}>
                        <span style={{ color: '#64748b' }}>Sharpe:</span>{' '}
                        <span style={{ fontWeight: 700, color: '#e2e8f0' }}>{bt.sharpe_like || 0}</span>
                    </div>
                    <div style={{ flex: 1, background: 'rgba(255,255,255,0.02)', borderRadius: 8, padding: 10 }}>
                        <span style={{ color: '#64748b' }}>Max DD:</span>{' '}
                        <span style={{ fontWeight: 700, color: '#f87171' }}>{bt.max_drawdown || 0}%</span>
                    </div>
                    {pattern.target && (
                        <div style={{ flex: 1, background: 'rgba(255,255,255,0.02)', borderRadius: 8, padding: 10 }}>
                            <span style={{ color: '#64748b' }}>Target:</span>{' '}
                            <span style={{ fontWeight: 700, color: '#4ade80' }}>₹{parseFloat(pattern.target).toLocaleString()}</span>
                        </div>
                    )}
                </div>

                {/* Trade history */}
                {bt.trades && bt.trades.length > 0 && (
                    <>
                        <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', marginBottom: 8, textTransform: 'uppercase' as const, letterSpacing: 1 }}>
                            Last {bt.trades.length} Occurrences
                        </div>
                        <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                            {bt.trades.map((t: any, idx: number) => (
                                <div key={idx} style={{
                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                    padding: '6px 10px', borderRadius: 6,
                                    background: idx % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent',
                                    fontSize: 11,
                                }}>
                                    <span style={{ color: '#64748b', fontFamily: 'monospace' }}>{t.date}</span>
                                    <span style={{
                                        fontWeight: 700, fontSize: 10, padding: '2px 8px', borderRadius: 4,
                                        background: t.result === 'Win' ? 'rgba(74,222,128,0.12)' : 'rgba(248,113,113,0.12)',
                                        color: t.result === 'Win' ? '#4ade80' : '#f87171',
                                    }}>
                                        {t.result === 'Win' ? '✅' : '❌'} {t.return}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
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

    // ── Pattern detection state ──────────────────────────────────────────────
    const [patternData, setPatternData] = useState<any>(null);
    const [patternLoading, setPatternLoading] = useState(false);
    const [showPatterns, setShowPatterns] = useState(true);
    const [showFib, setShowFib] = useState(false);
    const [showPivots, setShowPivots] = useState(false);
    const [selectedPattern, setSelectedPattern] = useState<any>(null);

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

    // Fetch patterns when chart data is loaded
    useEffect(() => {
        if (!chartData) return;
        setPatternLoading(true);
        const intv = INTERVALS.find(i => i.key === activeInterval);
        const period = intv?.period || '6mo';
        fetch(`${API}/api/chart/patterns?symbol=${encodeURIComponent(symbol)}&interval=${activeInterval}&period=${period}`)
            .then(r => r.json())
            .then(d => { setPatternData(d); setPatternLoading(false); })
            .catch(() => setPatternLoading(false));
    }, [chartData, symbol, activeInterval]);

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

        // ── Pattern markers on chart ─────────────────────────────────────────
        if (showPatterns) {
            let markers: any[] = [];

            // 1. Current active patterns
            if (patternData?.patterns?.length) {
                const activeMarkers = patternData.patterns
                    .filter((p: any) => p.time)
                    .map((p: any) => ({
                        time: p.time as Time,
                        position: p.bias === 'Bearish' ? 'aboveBar' as const : 'belowBar' as const,
                        color: p.bias === 'Bearish' ? '#f87171' : p.bias === 'Bullish' ? '#4ade80' : '#fbbf24',
                        shape: p.bias === 'Bearish' ? 'arrowDown' as const : 'arrowUp' as const,
                        text: p.name?.replace('Bullish ', '↑').replace('Bearish ', '↓').slice(0, 18) || 'Pattern',
                    }));
                markers = [...markers, ...activeMarkers];
            }

            // 2. Historical occurrences of selected pattern
            if (selectedPattern?.backtest?.trades?.length) {
                const histMarkers = selectedPattern.backtest.trades
                    .filter((t: any) => t.time)
                    .map((t: any) => ({
                        time: t.time as Time,
                        position: selectedPattern.bias === 'Bearish' ? 'aboveBar' as const : 'belowBar' as const,
                        color: t.result === 'Win' ? '#4ade80' : '#f87171',
                        shape: selectedPattern.bias === 'Bearish' ? 'arrowDown' as const : 'arrowUp' as const,
                        text: `${t.result === 'Win' ? '✅' : '❌'} ${t.return}`
                    }));
                markers = [...markers, ...histMarkers];
            }

            if (markers.length) {
                // Remove duplicates by time and sort
                const uniqueMarkers = Array.from(new Map(markers.map(m => [m.time, m])).values());
                uniqueMarkers.sort((a, b) => (a.time as number) - (b.time as number));

                try {
                    // @ts-ignore — setMarkers exists at runtime in v5
                    candleSeries.setMarkers(uniqueMarkers);
                } catch {
                    // silently skip if not supported
                }
            }
        }

        // ── Fibonacci horizontal lines ───────────────────────────────────────
        if (showFib && patternData?.fibonacci?.fib_levels) {
            const candles = chartData.candles;
            if (candles.length >= 2) {
                const t1 = candles[0].time as Time;
                const t2 = candles[candles.length - 1].time as Time;
                const fibColors: Record<string, string> = {
                    'Ret_23.6%': '#fbbf2440', 'Ret_38.2%': '#f59e0b60', 'Ret_50%': '#3b82f680',
                    'Ret_61.8%': '#8b5cf680', 'Ret_78.6%': '#ec489960', 'Ret_100%': '#ef444460',
                };

                Object.entries(patternData.fibonacci.fib_levels).forEach(([name, price]) => {
                    if (typeof price !== 'number' || name.startsWith('Ext_')) return;
                    const color = fibColors[name] || '#60a5fa40';
                    const fibLine = chart.addSeries(LineSeries, {
                        color: color,
                        lineWidth: 1,
                        lineStyle: 2,
                        priceLineVisible: false,
                        lastValueVisible: true,
                        crosshairMarkerVisible: false,
                        title: name.replace('Ret_', 'Fib '),
                    });
                    fibLine.setData([{ time: t1, value: price as number }, { time: t2, value: price as number }]);
                });
            }
        }

        // ── Pivot lines ──────────────────────────────────────────────────────
        if (showPivots && patternData?.fibonacci?.pivots) {
            const candles = chartData.candles;
            if (candles.length >= 2) {
                const t1 = candles[0].time as Time;
                const t2 = candles[candles.length - 1].time as Time;
                const pivotColors: Record<string, string> = {
                    P: '#fbbf24', R1: '#f87171', R2: '#ef4444', S1: '#4ade80', S2: '#22c55e',
                };
                Object.entries(patternData.fibonacci.pivots).forEach(([name, price]) => {
                    if (typeof price !== 'number') return;
                    const pivotLine = chart.addSeries(LineSeries, {
                        color: pivotColors[name] || '#64748b',
                        lineWidth: 1,
                        lineStyle: 3,
                        priceLineVisible: false,
                        lastValueVisible: true,
                        crosshairMarkerVisible: false,
                        title: name,
                    });
                    pivotLine.setData([{ time: t1, value: price as number }, { time: t2, value: price as number }]);
                });
            }
        }

        // ── Harmonic XABCD lines ─────────────────────────────────────────────
        if (showPatterns && patternData?.harmonic?.xabcd_points?.length >= 4) {
            const xabcdLine = chart.addSeries(LineSeries, {
                color: patternData.harmonic.name?.includes('Bullish') ? '#4ade80' : '#f87171',
                lineWidth: 2,
                lineStyle: 0,
                priceLineVisible: false,
                lastValueVisible: false,
                crosshairMarkerVisible: false,
                title: patternData.harmonic.name || 'Harmonic',
            });
            const xabcdData = patternData.harmonic.xabcd_points
                .filter((pt: any) => pt.time > 0)
                .map((pt: any) => ({ time: pt.time as Time, value: pt.price }));
            if (xabcdData.length >= 3) {
                xabcdLine.setData(xabcdData);
            }
        }

        // ── RSI sub-chart ─────────────────────────────────────────────────────
        if (rsiContainerRef.current && chartData.indicators?.rsi?.length) {
            const rsiChart = createChart(rsiContainerRef.current, {
                width: container.clientWidth,
                height: 140,
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
                    color: '#f8717144', lineWidth: 1, lineStyle: 2,
                    priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
                });
                obLine.setData([
                    { time: rsiTimes[0] as Time, value: 70 },
                    { time: rsiTimes[rsiTimes.length - 1] as Time, value: 70 },
                ]);
                const osLine = rsiChart.addSeries(LineSeries, {
                    color: '#4ade8044', lineWidth: 1, lineStyle: 2,
                    priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
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

        // Fit all candles into the visible chart area
        chart.timeScale().fitContent();

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
    }, [chartData, overlays, patternData, showPatterns, showFib, showPivots, selectedPattern]);

    // ── Helper: unique patterns for the panel ────────────────────────────────
    const uniquePatterns = React.useMemo(() => {
        if (!patternData) return [];
        const items: any[] = [];
        // Candlestick patterns (unique names)
        const seenNames = new Set<string>();
        for (const p of (patternData.patterns || [])) {
            if (!seenNames.has(p.name)) {
                seenNames.add(p.name);
                items.push(p);
            }
        }
        return items;
    }, [patternData]);

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

            {/* Overlay + Pattern toggles */}
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
                <span style={{ width: 1, background: 'rgba(255,255,255,0.08)', margin: '0 4px' }} />
                <button onClick={() => setShowPatterns(p => !p)} style={{
                    padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600, cursor: 'pointer',
                    border: `1px solid ${showPatterns ? '#ec4899' : 'rgba(255,255,255,0.08)'}`,
                    background: showPatterns ? 'rgba(236,72,153,0.15)' : 'transparent',
                    color: showPatterns ? '#ec4899' : '#475569',
                }}>
                    🔍 Patterns
                </button>
                <button onClick={() => setShowFib(f => !f)} style={{
                    padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600, cursor: 'pointer',
                    border: `1px solid ${showFib ? '#f59e0b' : 'rgba(255,255,255,0.08)'}`,
                    background: showFib ? 'rgba(245,158,11,0.15)' : 'transparent',
                    color: showFib ? '#f59e0b' : '#475569',
                }}>
                    📐 Fibonacci
                </button>
                <button onClick={() => setShowPivots(p => !p)} style={{
                    padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600, cursor: 'pointer',
                    border: `1px solid ${showPivots ? '#06b6d4' : 'rgba(255,255,255,0.08)'}`,
                    background: showPivots ? 'rgba(6,182,212,0.15)' : 'transparent',
                    color: showPivots ? '#06b6d4' : '#475569',
                }}>
                    📊 Pivots
                </button>
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

                    {/* Info bar with data source */}
                    {chartData?.price && (
                        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8, padding: '6px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: 8, alignItems: 'center' }}>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                                52W H: <span style={{ color: '#4ade80', fontWeight: 700 }}>{chartData.price.high_52w?.toLocaleString()}</span>
                            </div>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                                52W L: <span style={{ color: '#f87171', fontWeight: 700 }}>{chartData.price.low_52w?.toLocaleString()}</span>
                            </div>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                                Candles: <span style={{ fontWeight: 700, color: '#94a3b8' }}>{chartData.total_candles}</span>
                            </div>
                            <div style={{
                                fontSize: 9, fontWeight: 800, padding: '2px 8px', borderRadius: 6,
                                background: chartData.data_source === 'kite' ? 'rgba(74,222,128,0.15)' : 'rgba(255,255,255,0.05)',
                                color: chartData.data_source === 'kite' ? '#4ade80' : '#64748b',
                                border: `1px solid ${chartData.data_source === 'kite' ? 'rgba(74,222,128,0.3)' : 'rgba(255,255,255,0.08)'}`,
                                letterSpacing: 0.5, textTransform: 'uppercase' as const,
                            }}>
                                {chartData.data_source === 'kite' ? '⚡ KITE API' : '📊 yfinance'}
                            </div>
                            {patternLoading && (
                                <span style={{ fontSize: 10, color: '#c4b5fd' }}>🔄 Scanning patterns…</span>
                            )}
                        </div>
                    )}

                    {/* ═══ PATTERN PANEL ═══ */}
                    {showPatterns && patternData && (
                        <div style={{
                            marginTop: 12, background: 'rgba(255,255,255,0.02)', borderRadius: 12,
                            border: '1px solid rgba(255,255,255,0.05)', padding: 12,
                        }}>
                            {/* Harmonic pattern card */}
                            {patternData.harmonic?.name && !['No Swing', 'Consolidation'].includes(patternData.harmonic.name) && (
                                <div style={{ marginBottom: 12 }}>
                                    <div style={{ fontSize: 10, fontWeight: 800, color: '#8b5cf6', textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 6 }}>
                                        🔷 HARMONIC PATTERN
                                    </div>
                                    <div onClick={() => setSelectedPattern({ ...patternData.harmonic, type: 'harmonic' })}
                                        style={{
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            padding: '8px 12px', borderRadius: 8, cursor: 'pointer',
                                            background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.2)',
                                        }}>
                                        <div>
                                            <div style={{ fontSize: 13, fontWeight: 800, color: patternData.harmonic.name?.includes('Bull') ? '#4ade80' : '#f87171' }}>
                                                {patternData.harmonic.name}
                                            </div>
                                            <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>
                                                PRZ: ₹{patternData.harmonic.prz} → Target: ₹{patternData.harmonic.target} | Stop: ₹{patternData.harmonic.stop}
                                            </div>
                                        </div>
                                        <div style={{ textAlign: 'right' }}>
                                            <div style={{ fontSize: 11, fontWeight: 800, color: '#c4b5fd' }}>
                                                {patternData.harmonic.completion_pct}%
                                            </div>
                                            <div style={{ fontSize: 9, color: '#64748b' }}>{patternData.harmonic.status}</div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Chart pattern card */}
                            {patternData.chart_pattern?.name && !['Consolidation', 'Ranging'].includes(patternData.chart_pattern.name) && (
                                <div style={{ marginBottom: 12 }}>
                                    <div style={{ fontSize: 10, fontWeight: 800, color: '#06b6d4', textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 6 }}>
                                        📐 CHART PATTERN
                                    </div>
                                    <div onClick={() => setSelectedPattern({ ...patternData.chart_pattern, type: 'chart' })}
                                        style={{
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            padding: '8px 12px', borderRadius: 8, cursor: 'pointer',
                                            background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.2)',
                                        }}>
                                        <div>
                                            <div style={{ fontSize: 13, fontWeight: 800, color: '#e2e8f0' }}>
                                                {patternData.chart_pattern.name}
                                            </div>
                                            <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>
                                                PRZ: ₹{patternData.chart_pattern.prz} → Target: ₹{patternData.chart_pattern.target}
                                            </div>
                                        </div>
                                        <div style={{ textAlign: 'right' }}>
                                            <div style={{ fontSize: 11, fontWeight: 800, color: '#06b6d4' }}>
                                                {patternData.chart_pattern.completion_pct}%
                                            </div>
                                            <div style={{ fontSize: 9, color: '#64748b' }}>{patternData.chart_pattern.status}</div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Fibonacci summary */}
                            {showFib && patternData.fibonacci?.fib_levels && (
                                <div style={{ marginBottom: 12 }}>
                                    <div style={{ fontSize: 10, fontWeight: 800, color: '#f59e0b', textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 6 }}>
                                        📐 FIBONACCI LEVELS
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 4 }}>
                                        {Object.entries(patternData.fibonacci.fib_levels)
                                            .filter(([k]) => k.startsWith('Ret_'))
                                            .map(([name, price]) => (
                                                <div key={name} style={{
                                                    fontSize: 10, padding: '4px 8px', borderRadius: 6,
                                                    background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.1)',
                                                    display: 'flex', justifyContent: 'space-between',
                                                }}>
                                                    <span style={{ color: '#f59e0b', fontWeight: 700 }}>{(name as string).replace('Ret_', '')}</span>
                                                    <span style={{ color: '#e2e8f0', fontWeight: 600 }}>₹{(price as number).toLocaleString()}</span>
                                                </div>
                                            ))}
                                    </div>
                                </div>
                            )}

                            {/* Candlestick pattern list */}
                            {uniquePatterns.length > 0 && (
                                <div>
                                    <div style={{ fontSize: 10, fontWeight: 800, color: '#ec4899', textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 6 }}>
                                        🕯️ CANDLESTICK PATTERNS ({uniquePatterns.length} detected)
                                    </div>
                                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                        {uniquePatterns.slice(0, 12).map((p: any, i: number) => (
                                            <button key={i} onClick={() => setSelectedPattern(p)} style={{
                                                padding: '4px 10px', borderRadius: 8, fontSize: 10, fontWeight: 700,
                                                cursor: 'pointer', border: 'none',
                                                background: p.bias === 'Bullish' ? 'rgba(74,222,128,0.12)' : p.bias === 'Bearish' ? 'rgba(248,113,113,0.12)' : 'rgba(255,255,255,0.05)',
                                                color: p.bias === 'Bullish' ? '#4ade80' : p.bias === 'Bearish' ? '#f87171' : '#94a3b8',
                                            }}>
                                                {p.bias === 'Bullish' ? '▲' : p.bias === 'Bearish' ? '▼' : '●'} {p.name.replace('Bullish ', '').replace('Bearish ', '')}
                                                {p.backtest ? ` (${p.backtest.win_rate}%)` : ''}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}

            {/* Backtest popup */}
            {selectedPattern && (
                <BacktestPopup pattern={selectedPattern} onClose={() => setSelectedPattern(null)} />
            )}
        </div>
    );
}
