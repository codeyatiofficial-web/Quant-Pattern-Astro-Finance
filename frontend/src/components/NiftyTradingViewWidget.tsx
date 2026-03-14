import React, { useEffect, useState, useRef, memo } from 'react';

const API = '';

interface Candle {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

interface CandleData {
    success: boolean;
    symbol: string;
    interval: string;
    count: number;
    candles: Candle[];
    last_price: number;
    change: number;
    change_pct: number;
}

function NiftyCandleChart() {
    const [data, setData] = useState<CandleData | null>(null);
    const [signalData, setSignalData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedInterval, setSelectedInterval] = useState('minute');
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const fetchSignal = async () => {
        try {
            const res = await fetch(`${API}/api/correlation/live-prediction`);
            if (res.ok) {
                const json = await res.json();
                setSignalData(json);
            }
        } catch (e) {
            console.error("Failed to load magnitude signal", e);
        }
    };

    const fetchCandles = async (intv: string) => {
        try {
            const res = await fetch(`${API}/api/nifty50/candles?count=30&interval=${intv}`);
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: 'Failed to fetch' }));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }
            const json: CandleData = await res.json();
            setData(json);
            setError(null);
        } catch (e: any) {
            setError(e.message || 'Failed to load candle data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        setLoading(true);
        fetchCandles(selectedInterval);
        fetchSignal();
        
        // Adaptive refresh: faster for short intervals, slower for long ones
        const refreshMs: Record<string, number> = {
            'minute': 1000, '3minute': 3000, '5minute': 5000,
            '15minute': 10000, '30minute': 15000, '60minute': 30000,
        };
        const timer = setInterval(() => fetchCandles(selectedInterval), refreshMs[selectedInterval] || 5000);
        const signalTimer = setInterval(fetchSignal, 60000); // 1 minute signal refresh
        
        return () => {
            clearInterval(timer);
            clearInterval(signalTimer);
        };
    }, [selectedInterval]);

    // Draw candlestick chart on canvas
    useEffect(() => {
        if (!data || !data.candles.length || !canvasRef.current || !containerRef.current) return;

        const canvas = canvasRef.current;
        const container = containerRef.current;
        const dpr = window.devicePixelRatio || 1;

        const rect = container.getBoundingClientRect();
        const W = rect.width;
        const H = rect.height;

        canvas.width = W * dpr;
        canvas.height = H * dpr;
        canvas.style.width = `${W}px`;
        canvas.style.height = `${H}px`;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        ctx.scale(dpr, dpr);

        // Clear
        ctx.clearRect(0, 0, W, H);

        const candles = data.candles;
        const padding = { top: 20, bottom: 40, left: 10, right: 60 };
        const chartW = W - padding.left - padding.right;
        const chartH = H - padding.top - padding.bottom;

        // Price range
        let allHighs = candles.map(c => c.high);
        let allLows = candles.map(c => c.low);
        
        // Ensure bounds include the overlays
        if (signalData && signalData.direction !== 'NEUTRAL' && signalData.target_price) {
            allHighs.push(signalData.target_price);
            allLows.push(signalData.target_price);
            if (signalData.target_range_high) allHighs.push(signalData.target_range_high);
            if (signalData.target_range_low) allLows.push(signalData.target_range_low);
            if (signalData.stop_loss) {
                allHighs.push(signalData.stop_loss);
                allLows.push(signalData.stop_loss);
            }
            if (signalData.current_nifty) {
                allHighs.push(signalData.current_nifty);
                allLows.push(signalData.current_nifty);
            }
        }
        
        const maxPrice = Math.max(...allHighs);
        const minPrice = Math.min(...allLows);
        const priceRange = maxPrice - minPrice || 1;
        const priceMargin = priceRange * 0.08;
        const adjMin = minPrice - priceMargin;
        const adjMax = maxPrice + priceMargin;
        const adjRange = adjMax - adjMin;

        const toY = (price: number) => padding.top + chartH * (1 - (price - adjMin) / adjRange);
        const candleWidth = Math.max(4, (chartW / candles.length) * 0.65);
        const gap = chartW / candles.length;

        // Grid lines
        ctx.strokeStyle = 'rgba(30, 41, 59, 0.8)';
        ctx.lineWidth = 0.5;
        const gridLines = 5;
        for (let i = 0; i <= gridLines; i++) {
            const price = adjMin + (adjRange / gridLines) * i;
            const y = toY(price);
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(W - padding.right, y);
            ctx.stroke();

            // Price labels on right
            ctx.fillStyle = '#64748b';
            ctx.font = '10px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(price.toFixed(1), W - padding.right + 6, y + 3);
        }

        // Draw candles
        candles.forEach((c, i) => {
            const x = padding.left + gap * i + gap / 2;
            const isBullish = c.close >= c.open;
            const bodyColor = isBullish ? '#22c55e' : '#ef4444';
            const wickColor = isBullish ? '#4ade80' : '#f87171';

            // Wick (high-low line)
            ctx.strokeStyle = wickColor;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(x, toY(c.high));
            ctx.lineTo(x, toY(c.low));
            ctx.stroke();

            // Body
            const bodyTop = toY(Math.max(c.open, c.close));
            const bodyBottom = toY(Math.min(c.open, c.close));
            const bodyH = Math.max(1, bodyBottom - bodyTop);

            ctx.fillStyle = bodyColor;
            ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyH);
        });

        // Time labels on bottom
        ctx.fillStyle = '#64748b';
        ctx.font = '9px monospace';
        ctx.textAlign = 'center';
        const labelEvery = Math.max(1, Math.floor(candles.length / 6));
        candles.forEach((c, i) => {
            if (i % labelEvery === 0 || i === candles.length - 1) {
                const x = padding.left + gap * i + gap / 2;
                ctx.fillText(c.time, x, H - padding.bottom + 16);
            }
        });

        // Current price line
        const lastPrice = candles[candles.length - 1].close;
        const lastY = toY(lastPrice);
        ctx.setLineDash([4, 3]);
        ctx.strokeStyle = data.change >= 0 ? 'rgba(74,222,128,0.6)' : 'rgba(248,113,113,0.6)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding.left, lastY);
        ctx.lineTo(W - padding.right, lastY);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // --- DRAW MAGNITUDE SIGNAL OVERLAYS ---
        if (signalData && signalData.direction !== 'NEUTRAL' && signalData.target_price) {
            const isBuy = signalData.direction === 'BUY' || signalData.prediction === 'Bullish' || signalData.prediction === 'BULLISH';
            const targetColor = isBuy ? 'rgba(34, 197, 94, 0.9)' : 'rgba(239, 68, 68, 0.9)';
            const bandColor = isBuy ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)';
            const stopColor = 'rgba(249, 115, 22, 0.9)'; // Orange for SL

            const currentX = padding.left + gap * (candles.length - 1) + gap / 2;

            // 1) Target Band
            if (signalData.target_range_high && signalData.target_range_low) {
                const bandTop = toY(Math.max(signalData.target_range_high, signalData.target_range_low));
                const bandBottom = toY(Math.min(signalData.target_range_high, signalData.target_range_low));
                ctx.fillStyle = bandColor;
                ctx.fillRect(padding.left, bandTop, chartW, bandBottom - bandTop);
            }

            // 2) Target Line
            const tY = toY(signalData.target_price);
            ctx.setLineDash([5, 5]);
            ctx.strokeStyle = targetColor;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(padding.left, tY);
            ctx.lineTo(W - padding.right, tY);
            ctx.stroke();
            ctx.setLineDash([]);
            
            ctx.fillStyle = targetColor;
            ctx.font = '10px monospace';
            ctx.fillText('🎯 TARGET', W - padding.right - 55, tY - 4);

            // 3) Stop Loss Line
            if (signalData.stop_loss) {
                const slY = toY(signalData.stop_loss);
                ctx.strokeStyle = stopColor;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(padding.left, slY);
                ctx.lineTo(W - padding.right, slY);
                ctx.stroke();
                
                ctx.fillStyle = stopColor;
                ctx.font = '10px monospace';
                ctx.fillText('🛑 SL', W - padding.right - 35, slY + 12);
            }

            // 4) Entry Line (current_nifty — where the signal was triggered)
            const entryPrice = signalData.current_nifty || signalData.target?.current_price;
            if (entryPrice) {
                const entryY = toY(entryPrice);
                ctx.setLineDash([3, 4]);
                ctx.strokeStyle = 'rgba(148, 163, 184, 0.7)'; // Slate/white dashed
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(padding.left, entryY);
                ctx.lineTo(W - padding.right, entryY);
                ctx.stroke();
                ctx.setLineDash([]);

                ctx.fillStyle = 'rgba(148, 163, 184, 0.9)';
                ctx.font = '10px monospace';
                ctx.fillText('⚡ ENTRY', W - padding.right - 52, entryY - 4);
            }

            // 5) Signal Arrow above/below current candle
            ctx.font = '18px Arial';
            if (isBuy) {
                ctx.fillText('⬆️', currentX - 9, toY(candles[candles.length - 1].low) + 20);
            } else {
                ctx.fillText('⬇️', currentX - 9, toY(candles[candles.length - 1].high) - 10);
            }
        }

    }, [data, signalData]);

    const isPositive = data ? data.change >= 0 : true;

    const intervals = [
        { label: '1m', value: 'minute' },
        { label: '3m', value: '3minute' },
        { label: '5m', value: '5minute' },
        { label: '15m', value: '15minute' },
        { label: '30m', value: '30minute' },
        { label: '1h', value: '60minute' },
    ];

    return (
        <div style={{
            background: '#0f172a', border: '1px solid #1e293b', borderRadius: 14,
            padding: '16px 16px 12px', marginBottom: 24, overflow: 'hidden'
        }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                        <h3 style={{ fontSize: 13, fontWeight: 800, color: '#f8fafc', letterSpacing: 0.5, margin: 0, textTransform: 'uppercase' }}>
                            NIFTY 50 — {intervals.find(i => i.value === selectedInterval)?.label} Chart
                        </h3>
                        
                        {/* Interval Selector */}
                        <div style={{ display: 'flex', background: '#1e293b', padding: 2, borderRadius: 6, gap: 2 }}>
                            {intervals.map((intv) => (
                                <button
                                    key={intv.value}
                                    onClick={() => setSelectedInterval(intv.value)}
                                    style={{
                                        background: selectedInterval === intv.value ? '#3b82f6' : 'transparent',
                                        color: selectedInterval === intv.value ? '#ffffff' : '#94a3b8',
                                        border: 'none',
                                        borderRadius: 4,
                                        padding: '2px 8px',
                                        fontSize: 10,
                                        fontWeight: 700,
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease',
                                    }}
                                >
                                    {intv.label}
                                </button>
                            ))}
                        </div>
                    </div>
                    <p style={{ fontSize: 10, color: '#64748b', margin: 0, marginTop: 4 }}>
                        Last 30 candles via Kite API | Live updates
                    </p>
                </div>
                {data && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontFamily: 'monospace', fontSize: 18, fontWeight: 800, color: '#f8fafc' }}>
                            {data.last_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </span>
                        <span style={{
                            fontFamily: 'monospace', fontSize: 12, fontWeight: 700,
                            padding: '3px 8px', borderRadius: 6,
                            background: isPositive ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
                            color: isPositive ? '#4ade80' : '#f87171',
                        }}>
                            {isPositive ? '+' : ''}{data.change.toFixed(2)} ({isPositive ? '+' : ''}{data.change_pct.toFixed(2)}%)
                        </span>
                    </div>
                )}
            </div>

            {/* Chart area */}
            <div ref={containerRef} style={{ width: '100%', height: 280, position: 'relative' }}>
                {loading ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b', fontSize: 13 }}>
                        <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2, marginRight: 8 }} />
                        Loading Nifty 50 candles from Kite API...
                    </div>
                ) : error ? (
                    <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        height: '100%', color: '#94a3b8', fontSize: 12, textAlign: 'center', gap: 8, padding: 20
                    }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: '#f87171' }}>Chart Unavailable</div>
                        <div>{error}</div>
                        <button
                            onClick={() => { setLoading(true); setError(null); fetchCandles(selectedInterval); }}
                            style={{
                                marginTop: 4, padding: '6px 16px', fontSize: 11, fontWeight: 700,
                                background: '#1e293b', border: '1px solid #334155', borderRadius: 6,
                                color: '#f8fafc', cursor: 'pointer'
                            }}
                        >
                            Retry
                        </button>
                    </div>
                ) : (
                    <>
                        <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
                        
                        {/* Signal Info Floating Box */}
                        {signalData && signalData.direction !== 'NEUTRAL' && signalData.target_price && (
                            <div style={{
                                position: 'absolute', top: 12, left: 16, zIndex: 10,
                                background: 'rgba(15, 23, 42, 0.85)',
                                border: `1px solid ${signalData.direction === 'BUY' || signalData.prediction === 'Bullish' ? '#22c55e' : '#ef4444'}`,
                                borderRadius: 8, padding: '10px 14px',
                                backdropFilter: 'blur(4px)',
                                boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                                display: 'flex', flexDirection: 'column', gap: 6,
                                minWidth: 160
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: 11, fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase' }}>
                                        ACTIVE SIGNAL
                                    </span>
                                    <span style={{ 
                                        fontSize: 11, fontWeight: 800, 
                                        color: signalData.direction === 'BUY' || signalData.prediction === 'Bullish' ? '#4ade80' : '#f87171' 
                                    }}>
                                        {signalData.direction || signalData.prediction.toUpperCase()}
                                    </span>
                                </div>
                                <div style={{ height: 1, background: '#334155', margin: '2px 0' }} />

                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                    <span style={{ color: '#cbd5e1' }}>Entry</span>
                                    <span style={{ color: '#e2e8f0', fontWeight: 700 }}>
                                        {signalData.current_nifty ? signalData.current_nifty.toFixed(1) : signalData.target?.current_price?.toFixed(1) ?? '—'}
                                    </span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                    <span style={{ color: '#cbd5e1' }}>Target</span>
                                    <span style={{ color: '#f8fafc', fontWeight: 700 }}>{signalData.target_price.toFixed(1)}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                    <span style={{ color: '#cbd5e1' }}>Stop Loss</span>
                                    <span style={{ color: '#fb923c', fontWeight: 700 }}>{signalData.stop_loss.toFixed(1)}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                    <span style={{ color: '#cbd5e1' }}>Magnitude</span>
                                    <span style={{ color: '#fcd34d', fontWeight: 700 }}>{signalData.magnitude_points} pts</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                    <span style={{ color: '#cbd5e1' }}>Confidence</span>
                                    <span style={{ color: '#38bdf8', fontWeight: 700 }}>{signalData.confidence}% ({signalData.magnitude_confidence})</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginTop: 4 }}>
                                    <span style={{ color: '#64748b' }}>Risk/Reward</span>
                                    <span style={{ color: '#94a3b8' }}>1:{signalData.risk_reward}</span>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Footer */}
            <div style={{ marginTop: 8, fontSize: 9, color: '#475569', textAlign: 'center' }}>
                Data source: Kite Connect API | Exchange: NSE | Live updates
            </div>
        </div>
    );
}

export default memo(NiftyCandleChart);
