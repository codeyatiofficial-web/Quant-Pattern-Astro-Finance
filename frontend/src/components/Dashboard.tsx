'use client';
import React, { useState, useEffect } from 'react';
import { usePlanGate } from './UpgradeModal';
import { usePlan } from '../contexts/PlanContext';
import { MarketTicker } from './MarketTicker';
import IntradayForecastWidget from './IntradayForecastWidget';
import NiftyScannerWidget from './NiftyScannerWidget';
import NiftyTradingViewWidget from './NiftyTradingViewWidget';

const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

interface TodayInsight {
    current_nakshatra?: string;
    nakshatra_sanskrit?: string;
    pada?: number;
    ruling_planet?: string;
    moon_longitude?: number;
    planet_longitude?: number;
    historical_tendency?: string;
    favorable_for?: string[];
    unfavorable_for?: string[];
    financial_traits?: string[];
    lucky_colors?: string[];
    lucky_numbers?: number[];
    transition?: { from_nakshatra: string; to_nakshatra: string; transition_time: string };
    tithi_name?: string;
    paksha?: string;
    yoga_name?: string;
}

// US / Global market symbols — used to auto-detect the correct market flag
const US_SYMBOLS = new Set([
    // US Equities
    '^IXIC', '^GSPC', '^DJI', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META',
    // Commodities
    'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'PL=F', 'PA=F', 'ALI=F', 'ZC=F', 'ZW=F',
    // Cryptocurrency
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
    'ADA-USD', 'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'LINK-USD', 'MATIC-USD', 'LTC-USD',
]);

function TendencyBadge({ t }: { t: string }) {
    const cls = t === 'Bullish' ? 'badge-bullish' : t === 'Bearish' ? 'badge-bearish' : 'badge-neutral';
    const icon = t === 'Bullish' ? '' : t === 'Bearish' ? '' : '';
    return <span className={`badge ${cls}`}>{icon} {t}</span>;
}

function MetricCard({ label, value, sub, color, icon }: {
    label: string; value: React.ReactNode; sub?: string; color?: string; icon?: string;
}) {
    return (
        <div className="metric-box" style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                {icon && <span style={{ fontSize: 16 }}>{icon}</span>}
                <span style={{
                    fontSize: 10, fontWeight: 700, color: 'var(--text-muted)',
                    textTransform: 'uppercase', letterSpacing: '0.8px'
                }}>{label}</span>
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, color: color || 'var(--text-primary)', lineHeight: 1.2 }}>
                {value}
            </div>
            {sub && <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 5 }}>{sub}</div>}
        </div>
    );
}

export default function Dashboard({ onAnalysisDone }: { onAnalysisDone: (data: any) => void }) {
    const { guardYears, requirePlan, modal: planModal } = usePlanGate(1);
    const { tier } = usePlan();
    const isElite = tier === 'elite';
    const isFree = tier === 'free';
    const [insight, setInsight] = useState<TodayInsight | null>(null);
    const [loading, setLoading] = useState(true);
    const [analysing, setAnalysing] = useState(false);
    const [forecast, setForecast] = useState<any>(null);
    const [forecastLoading, setForecastLoading] = useState(false);
    const [forecastMarket, setForecastMarket] = useState('NSE');
    const [forecastDate, setForecastDate] = useState(() => new Date().toISOString().slice(0, 10));
    const [weekForecast, setWeekForecast] = useState<any>(null);
    const [weekLoading, setWeekLoading] = useState(true);
    const [volSignal, setVolSignal] = useState<any>(null);
    const [volLoading, setVolLoading] = useState(true);

    const [symbol, setSymbol] = useState('^NSEI');
    const [planet, setPlanet] = useState('Moon');
    const [startDate, setStartDate] = useState(() => {
        const d = new Date();
        d.setFullYear(d.getFullYear() - 15);
        return d.toISOString().slice(0, 10);
    });
    const [endDate] = useState(new Date().toISOString().slice(0, 10));
    const [status, setStatus] = useState('');

    const market = US_SYMBOLS.has(symbol) ? 'NASDAQ' : 'NSE';

    useEffect(() => {
        fetch(`${API}/api/insight/today`)
            .then(r => r.json())
            .then(d => { setInsight(d); setLoading(false); })
            .catch(() => setLoading(false));
        // Fetch 7-day comprehensive forecast for all users
        fetch(`${API}/api/forecast/weekly?market=NSE`)
            .then(r => r.json())
            .then(d => { setWeekForecast(d); setWeekLoading(false); })
            .catch(() => setWeekLoading(false));

        // Auto-fetch volatility signal for dashboard widget
        const fetchVolSignal = () => {
            fetch(`${API}/api/correlation/volatility-signals?market=NSE&_t=${Date.now()}`)
                .then(async r => {
                    if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`);
                    return r.json();
                })
                .then(d => {
                    if (d && d.signal) setVolSignal(d);
                    setVolLoading(false);
                })
                .catch(err => {
                    console.error("Volatility Signal Fetch Error:", err);
                    setVolLoading(false);
                });
        };
        fetchVolSignal(); // Initial fetch
        const volInterval = setInterval(fetchVolSignal, 60000); // Auto-refresh every 60 seconds

        return () => {
            clearInterval(volInterval);
        };
    }, []);

    const fetchForecast = () => {
        if (!isElite) return;
        setForecastLoading(true);
        fetch(`${API}/api/forecast/monthly?target_date=${forecastDate}&market=${forecastMarket}`)
            .then(r => r.json())
            .then(d => { setForecast(d); setForecastLoading(false); })
            .catch(() => setForecastLoading(false));
    };

    useEffect(() => {
        fetchForecast();
    }, [isElite]);

    const runAnalysis = async () => {
        if (!requirePlan(1)) return; // Requires PRO (tier 1) or higher

        setAnalysing(true);
        setStatus('Fetching market data & crunching AI signals…');
        try {
            const res = await fetch(`${API}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, planet, start_date: startDate, end_date: endDate, market }),
            });
            const data = await res.json();
            onAnalysisDone(data);
            setStatus(' Analysis complete! Switching to results…');
        } catch {
            setStatus(' Error fetching data. Is the backend running?');
        }
        setAnalysing(false);
    };

    const tendency = insight?.historical_tendency ?? 'Neutral';

    return (
        <div className="fade-in">
            {planModal}

            <MarketTicker />

            {/* ── VOLATILITY SIGNAL WIDGET (All Users) ── */}
            {(() => {
                const sigColor = volSignal?.signal === 'BUY' ? '#22c55e' : volSignal?.signal === 'SELL' ? '#ef4444' : '#3b82f6';
                return (
                    <div style={{
                        background: '#000', borderRadius: 14, padding: '18px 22px', marginBottom: 20,
                        color: sigColor, fontFamily: 'inherit', border: `1px solid ${sigColor}30`
                    }}>
                        {volLoading ? (
                            <div style={{ textAlign: 'center', padding: '14px 0', color: '#888' }}>
                                <span className="spinner" style={{ width: 20, height: 20, borderWidth: 2, borderColor: '#333', borderTopColor: '#888', display: 'inline-block', marginRight: 10 }} />
                                <span style={{ fontWeight: 700, fontSize: 14 }}>Scanning volatility history...</span>
                            </div>
                        ) : volSignal ? (
                            <div>
                                {/* Row 1: Signal + Confidence */}
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                                        <div style={{
                                            fontSize: 38, fontWeight: 900, letterSpacing: 2, lineHeight: 1
                                        }}>
                                            {volSignal.signal}
                                        </div>
                                        <div>
                                            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, opacity: 0.6 }}>Volatility Signal</div>
                                            <div style={{ fontSize: 13, fontWeight: 700, marginTop: 2 }}>
                                                Confidence: {volSignal.confidence}%
                                                <span style={{ margin: '0 6px', opacity: 0.3 }}>|</span>
                                                {volSignal.total_volatility_events.toLocaleString()} events analyzed
                                            </div>
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                        {['3m', '5m', '15m'].map(tf => (
                                            <span key={tf} style={{
                                                fontSize: 11, fontWeight: 800, padding: '4px 10px', borderRadius: 6,
                                                background: `${sigColor}15`, border: `1px solid ${sigColor}30`, letterSpacing: 0.5
                                            }}>
                                                {tf} Chart
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                {/* Row 2: Proprietary Source Badge */}
                                <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
                                    <span style={{
                                        fontSize: 10, fontWeight: 700, padding: '3px 10px', borderRadius: 6,
                                        background: '#1e293b', border: '1px solid #334155', color: '#94a3b8',
                                        display: 'flex', alignItems: 'center', gap: 6
                                    }}>
                                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#3b82f6', display: 'inline-block' }} />
                                        Analyzing historical patterns across global markets, volatility indices, and macroeconomic events
                                    </span>
                                </div>

                                {/* Row 3: Marketing Banner */}
                                <div style={{
                                    marginTop: 16, padding: '10px 16px', background: '#f59e0b', borderRadius: 8,
                                    fontSize: 12, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                    flexWrap: 'wrap', gap: 8, color: '#000', textTransform: 'uppercase', letterSpacing: 0.5
                                }}>
                                    <span>FREE ACCESS FOR A LIMITED TIME — THIS FEATURE WILL SOON MOVE TO PRO</span>
                                    <span style={{ opacity: 0.7, fontSize: 10, fontWeight: 700 }}>
                                        {volSignal.data_years ? `${volSignal.data_years}y data` : ''} | Threshold: {volSignal.threshold_pct}%
                                    </span>
                                </div>

                                <div style={{
                                    marginTop: 16, padding: '12px 16px', background: '#0f172a', borderRadius: 8, border: '1px solid #1e293b',
                                    fontSize: 11, color: '#94a3b8', lineHeight: 1.5, textAlign: 'center'
                                }}>
                                    <strong>Pro Tip:</strong> Both the Volatility Signal and Intraday Forecast track the <strong>Nifty 50 Index</strong>.
                                    Best practice: When <em>both</em> signals align perfectly (e.g. both are Positive), it presents a high-probability BUY setup.
                                    When both are Negative, a short-interval SELL setup.
                                </div>
                            </div>
                        ) : (
                            <div style={{ textAlign: 'center', fontSize: 12, fontWeight: 600, padding: '10px 0', color: '#666' }}>
                                Volatility signal unavailable -- backend may be loading
                            </div>
                        )}
                    </div>
                );
            })()}

            {/* LIVE 1-HOUR INTRADAY FORECAST (All Users) */}
            <IntradayForecastWidget />

            {/* NIFTY 50 1-MIN CANDLE CHART (Kite API) */}
            <NiftyTradingViewWidget />

            {/*  1-WEEK COMPREHENSIVE FORECAST (All users)  */}
            <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 16,
                padding: '20px 24px',
                marginBottom: 24,
            }}>
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 20 }}></span>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: 0.5 }}>
                            {isFree ? '1-DAY MARKET FORECAST' : '1-WEEK MARKET FORECAST'}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                            11 Signals: Cycles · Yogas · Lunar Phase · Transits · Technicals · Patterns · Options · FII/DII · News · Events · Weekday
                        </div>
                        {isFree && (
                            <div style={{ fontSize: 10, color: 'var(--text-secondary)', marginTop: 4, fontStyle: 'italic', maxWidth: '80%' }}>
                                Note: This forecast analyzes 11 distinct signal layers to gauge the current directional bias. Market conditions are dynamic, and this analysis reflects the present situation rather than a guaranteed long-term trend.
                            </div>
                        )}
                    </div>
                </div>

                {weekLoading ? (
                    <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        gap: 16, padding: '40px 20px', background: 'var(--bg-secondary)',
                        border: '1px dashed var(--border-subtle)', borderRadius: 12, margin: '10px 0'
                    }}>
                        <div style={{ position: 'relative', width: 48, height: 48 }}>
                            <div className="spinner" style={{ width: 48, height: 48, borderWidth: 3, borderColor: 'var(--border-subtle)', borderTopColor: 'var(--accent-indigo)' }} />
                            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontSize: 20 }}></div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6, letterSpacing: 0.5 }}>
                                INITIALIZING QUANTUM SCAN...
                            </div>
                            <div style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 450, lineHeight: 1.5 }}>
                                Fetching and analyzing huge amounts of data across <strong style={{ color: '#fff' }}>11 distinct market layers</strong>. This includes planetary cycles, live technical patterns, options chain data, and institutional flows.
                                <br /><span style={{ fontSize: 12, color: '#f59e0b', marginTop: 8, display: 'inline-block' }}>Please wait a moment...</span>
                            </div>
                        </div>
                    </div>
                ) : weekForecast?.days?.length > 0 ? (
                    <>
                        {/* Week Summary Bar */}
                        {weekForecast.week_summary && (() => {
                            const ws = weekForecast.week_summary;
                            return (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 16px', background: `${ws.verdict_color}12`, border: `1px solid ${ws.verdict_color}33`, borderRadius: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                                    <div style={{ fontSize: 18, fontWeight: 900, color: ws.verdict_color }}>{ws.verdict}</div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Avg Score: <strong style={{ color: 'white' }}>{ws.avg_score}</strong></div>
                                    <div style={{ display: 'flex', gap: 6 }}>
                                        <span style={{ fontSize: 10, background: 'rgba(74,222,128,0.15)', color: '#4ade80', padding: '2px 8px', borderRadius: 8, fontWeight: 700 }}> {ws.bull_days} Bull</span>
                                        <span style={{ fontSize: 10, background: 'var(--bg-secondary)', color: 'var(--text-primary)', padding: '2px 8px', borderRadius: 8, fontWeight: 700 }}>↔ {ws.neutral_days} Neutral</span>
                                        <span style={{ fontSize: 10, background: 'rgba(248,113,113,0.15)', color: '#f87171', padding: '2px 8px', borderRadius: 8, fontWeight: 700 }}> {ws.bear_days} Bear</span>
                                    </div>
                                    <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 'auto' }}>{ws.total_signals} signals analyzed</span>
                                </div>
                            );
                        })()}

                        {/* Global Signal Badges */}
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
                            {weekForecast.global_signals?.technical?.text && weekForecast.global_signals.technical.text !== 'N/A' && (
                                <span style={{ fontSize: 10, background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '3px 8px', color: 'var(--text-secondary)' }}> {weekForecast.global_signals.technical.text}</span>
                            )}
                            {weekForecast.global_signals?.options?.text && weekForecast.global_signals.options.text !== 'N/A' && (
                                <span style={{ fontSize: 10, background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '3px 8px', color: 'var(--text-secondary)' }}> {weekForecast.global_signals.options.text}</span>
                            )}
                            {weekForecast.global_signals?.institutional?.text && weekForecast.global_signals.institutional.text !== 'N/A' && (
                                <span style={{ fontSize: 10, background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.25)', borderRadius: 8, padding: '3px 8px', color: '#6ee7b7' }}> {weekForecast.global_signals.institutional.text}</span>
                            )}
                            {weekForecast.news_sentiment?.text && weekForecast.news_sentiment.text !== 'N/A' && (
                                <span style={{ fontSize: 10, background: 'rgba(245,158,11,0.12)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 8, padding: '3px 8px', color: '#fcd34d' }}> {weekForecast.news_sentiment.text}</span>
                            )}
                            {weekForecast.chart_patterns?.patterns?.length > 0 && (
                                <span style={{ fontSize: 10, background: 'rgba(236,72,153,0.12)', border: '1px solid rgba(236,72,153,0.25)', borderRadius: 8, padding: '3px 8px', color: '#f9a8d4' }}> {weekForecast.chart_patterns.bullish_count} {weekForecast.chart_patterns.bearish_count} patterns</span>
                            )}
                        </div>

                        {/* Per-Day Cards */}
                        {(() => {
                            const isMarketClosed = new Date().getHours() > 15 || (new Date().getHours() === 15 && new Date().getMinutes() >= 30);
                            const startIndex = isFree && isMarketClosed ? 1 : 0;
                            const endIndex = isFree ? startIndex + 1 : 5;
                            const displayedDays = weekForecast.days.slice(startIndex, endIndex);

                            return (
                                <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(displayedDays.length, 5)}, 1fr)`, gap: 10 }}>
                                    {displayedDays.map((day: any, idx: number) => {
                                        const isToday = startIndex === 0 && idx === 0;
                                        const isTomorrow = startIndex === 1 && idx === 0;

                                        return (
                                            <div key={day.date} style={{
                                                background: (isToday || isTomorrow) ? 'var(--bg-secondary)' : 'var(--bg-card)',
                                                border: `1px solid ${(isToday || isTomorrow) ? 'var(--border-active)' : 'var(--border-subtle)'}`,
                                                borderRadius: 12, padding: 14, position: 'relative',
                                            }}>
                                                {isToday && <div style={{ position: 'absolute', top: -8, left: '50%', transform: 'translateX(-50%)', background: 'var(--accent-indigo)', color: 'white', fontSize: 8, fontWeight: 800, padding: '2px 8px', borderRadius: 6, letterSpacing: 1 }}>TODAY</div>}
                                                {isTomorrow && <div style={{ position: 'absolute', top: -8, left: '50%', transform: 'translateX(-50%)', background: 'var(--accent-indigo)', color: 'white', fontSize: 8, fontWeight: 800, padding: '2px 8px', borderRadius: 6, letterSpacing: 1 }}>TOMORROW</div>}
                                                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 6 }}>{day.weekday} {day.date ? new Date(day.date + 'T00:00:00').toLocaleDateString('en-GB', { day: '2-digit', month: 'long' }) : ''}</div>

                                                {/* Verdict */}
                                                <div style={{ textAlign: 'center', marginBottom: 8 }}>
                                                    <div style={{ fontSize: 16 }}>{day.verdict_emoji}</div>
                                                    <div style={{ fontSize: 12, fontWeight: 800, color: day.verdict_color }}>{day.verdict}</div>
                                                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Score: {day.score}</div>
                                                </div>

                                                {/* Signal Breakdown Mini-Bar */}
                                                {day.signal_breakdown && (
                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginBottom: 6 }}>
                                                        {Object.entries(day.signal_breakdown as Record<string, number>).filter(([, v]) => v !== 0).map(([key, val]) => {
                                                            const v = val as number;
                                                            const label: Record<string, string> = { nakshatra: ' Cycle', yogas: ' Yoga', weekday: ' Day', tithi_paksha: ' Phase', gochar: ' Transit', events: ' Event', options: ' PCR', institutional: ' FII', technical: ' Tech', chart_patterns: ' Pattern', news: ' News' };
                                                            return (
                                                                <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9 }}>
                                                                    <span style={{ color: 'var(--text-muted)' }}>{label[key] || key}</span>
                                                                    <span style={{ color: v > 0 ? '#4ade80' : v < 0 ? '#f87171' : '#94a3b8', fontWeight: 700 }}>{v > 0 ? '+' : ''}{v}</span>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                )}

                                                {/* Yogas */}
                                                {day.planetary_yogas?.length > 0 && (
                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginTop: 4 }}>
                                                        {day.planetary_yogas.slice(0, 2).map((y: any, j: number) => (
                                                            <div key={j} style={{ fontSize: 8, padding: '2px 6px', borderRadius: 4, background: y.impact === 'bullish' ? 'rgba(74,222,128,0.15)' : y.impact === 'bearish' ? 'rgba(248,113,113,0.15)' : 'var(--bg-secondary)', color: y.impact === 'bullish' ? '#4ade80' : y.impact === 'bearish' ? '#f87171' : 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 3 }}>
                                                                <span style={{ fontWeight: 700 }}>{y.name}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}

                                                {/* Events */}
                                                {day.events?.length > 0 && (
                                                    <div style={{ marginTop: 3 }}>
                                                        {day.events.slice(0, 1).map((ev: any, j: number) => (
                                                            <div key={j} style={{ fontSize: 8, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 2 }}>
                                                                {ev.name?.slice(0, 20)}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            );
                        })()}

                        {/* Gochar / Transits row */}
                        {weekForecast.gochar_events?.length > 0 && (
                            <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 10 }}>
                                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}> Upcoming Planetary Transits</div>
                                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                    {weekForecast.gochar_events.slice(0, 5).map((g: any, i: number) => (
                                        <span key={i} style={{ fontSize: 9, padding: '2px 8px', borderRadius: 6, background: g.tendency === 'Bullish' ? 'rgba(74,222,128,0.12)' : g.tendency === 'Bearish' ? 'rgba(248,113,113,0.12)' : 'rgba(255,255,255,0.05)', color: g.tendency === 'Bullish' ? '#4ade80' : g.tendency === 'Bearish' ? '#f87171' : '#94a3b8' }}>
                                            {g.event}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {
                            !isElite && (
                                <div style={{
                                    marginTop: 16,
                                    background: 'rgba(245, 158, 11, 0.15)',
                                    border: '1px solid rgba(245, 158, 11, 0.4)',
                                    borderRadius: 12,
                                    padding: '20px 24px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    flexWrap: 'wrap',
                                    gap: 16,
                                    position: 'relative',
                                    overflow: 'hidden'
                                }}>
                                    <div style={{ position: 'absolute', right: -20, top: -20, opacity: 0.1, transform: 'rotate(15deg)' }}>
                                        <svg width="120" height="120" viewBox="0 0 24 24" fill="currentColor" style={{ color: '#f59e0b' }}><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" /></svg>
                                    </div>
                                    <div style={{ flex: 1, zIndex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                                            <span style={{ color: '#f59e0b', fontWeight: 900, fontSize: 16, letterSpacing: 0.5 }}>ELITE EXCLUSIVE</span>
                                            <span className="pulse-dot" style={{ background: '#f59e0b', boxShadow: '0 0 0 2px rgba(245, 158, 11, 0.25)' }}></span>
                                        </div>
                                        <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500, lineHeight: 1.5, maxWidth: 500 }}>
                                            Unlock the full <strong>1-Month Composite Forecast</strong> to look ahead into the future. Includes FII/DII institutional flows, options chain analysis, custom date picker, and seasonality scoring.
                                        </div>
                                    </div>
                                    <button className="btn-upgrade-pro" style={{ zIndex: 1, padding: '10px 20px', fontSize: 14 }} onClick={() => requirePlan(2)}>
                                        Unlock Elite Forecast ✨
                                    </button>
                                </div>
                            )
                        }
                    </>
                ) : (
                    <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>No forecast data available.</div>
                )}
            </div>

            {/*  ELITE: 1-Month Composite Forecast  */}
            {
                isElite && (

                    <div style={{
                        background: 'rgba(245, 158, 11, 0.08)',
                        border: '1px solid rgba(245,158,11,0.35)',
                        borderRadius: 16,
                        padding: '24px 28px',
                        marginBottom: 28,
                        position: 'relative',
                        overflow: 'hidden',
                    }}>
                        {/* Elite badge */}
                        <div style={{
                            position: 'absolute', top: 16, right: 20,
                            background: '#f59e0b',
                            color: '#fff', fontSize: 10, fontWeight: 800,
                            padding: '3px 10px', borderRadius: 20, letterSpacing: 1.2,
                        }}> ELITE</div>

                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 18 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                <span style={{ fontSize: 22 }}></span>
                                <div>
                                    <div style={{ fontSize: 13, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: 0.5 }}>1-MONTH MARKET FORECAST</div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Composite: Astro · Technical · Institutional · Options · Macro · Seasonality</div>
                                </div>
                            </div>

                            {/* Forecast Controls */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'rgba(0,0,0,0.15)', padding: '6px 12px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.05)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <label style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>MARKET</label>
                                    <select
                                        className="form-input"
                                        value={forecastMarket}
                                        onChange={(e) => setForecastMarket(e.target.value)}
                                        style={{ padding: '4px 8px', fontSize: 12, height: 'auto', minWidth: 80 }}
                                    >
                                        <option value="NSE">NSE (India)</option>
                                        <option value="NASDAQ">NASDAQ (US)</option>
                                    </select>
                                </div>
                                <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)' }} />
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <label style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>T-ZERO DATE</label>
                                    <input
                                        type="date"
                                        className="form-input"
                                        value={forecastDate}
                                        onChange={(e) => setForecastDate(e.target.value)}
                                        style={{ padding: '4px 8px', fontSize: 12, height: 'auto', maxWidth: 130 }}
                                    />
                                </div>
                                <button
                                    onClick={fetchForecast}
                                    className="btn-primary"
                                    style={{ padding: '4px 12px', fontSize: 12, height: 'auto', minWidth: 'auto', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                                >
                                    Recalculate
                                </button>
                            </div>
                        </div>

                        {forecastLoading ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)', padding: '12px 0' }}>
                                <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
                                Crunching astro, technicals, options & news signals…
                            </div>
                        ) : forecast ? (
                            <>
                                {/* Top row: verdict + confidence */}
                                <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap', marginBottom: 20 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <span style={{ fontSize: 36 }}>{forecast.verdict_emoji}</span>
                                        <div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                <div style={{ fontSize: 26, fontWeight: 900, color: forecast.verdict_color, lineHeight: 1 }}>
                                                    {forecast.verdict}
                                                </div>
                                                {forecast.is_historical && (
                                                    <span style={{ fontSize: 10, background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: 12, color: 'var(--text-muted)' }}>HISTORICAL</span>
                                                )}
                                            </div>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
                                                <span style={{ color: 'var(--text-secondary)' }}>T-Zero: <strong>{forecast.anchor_date}</strong></span>
                                                <span>→</span>
                                                <span style={{ color: 'var(--accent-cyan)' }}>Target: <strong>{forecast.target_date}</strong></span>
                                            </div>
                                        </div>
                                    </div>
                                    {/* Confidence meter */}
                                    <div style={{ flex: 1, minWidth: 180 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                                            <span>Confidence</span>
                                            <span style={{ fontWeight: 700, color: forecast.verdict_color }}>{forecast.confidence}%</span>
                                        </div>
                                        <div style={{ height: 8, background: 'rgba(255,255,255,0.08)', borderRadius: 8, overflow: 'hidden' }}>
                                            <div style={{
                                                height: '100%', width: `${forecast.confidence}%`,
                                                background: forecast.verdict_color,
                                                borderRadius: 8, transition: 'width 0.8s ease',
                                            }} />
                                        </div>
                                    </div>
                                </div>

                                {/* Summary */}
                                <div style={{
                                    background: 'rgba(255,255,255,0.04)', borderRadius: 10,
                                    padding: '12px 16px', marginBottom: 20,
                                    fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6,
                                    borderLeft: `3px solid ${forecast.verdict_color}`,
                                }}>{forecast.summary}</div>

                                {/* Signal breakdown */}
                                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 }}>
                                    Signal Breakdown
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 8 }}>
                                    {(forecast.signals || []).map((sig: any, i: number) => (
                                        <div key={i} style={{
                                            display: 'flex', alignItems: 'flex-start', gap: 10,
                                            background: sig.direction === 'bullish' ? 'rgba(74,222,128,0.07)'
                                                : sig.direction === 'bearish' ? 'rgba(248,113,113,0.07)'
                                                    : sig.direction === 'historical' ? 'rgba(0,0,0,0.2)'
                                                        : 'rgba(255,255,255,0.04)',
                                            border: `1px solid ${sig.direction === 'bullish' ? 'rgba(74,222,128,0.2)'
                                                : sig.direction === 'bearish' ? 'rgba(248,113,113,0.2)'
                                                    : sig.direction === 'historical' ? 'rgba(255,255,255,0.05)'
                                                        : 'rgba(255,255,255,0.1)'}`,
                                            borderRadius: 8, padding: '8px 12px',
                                            opacity: sig.direction === 'historical' ? 0.6 : 1
                                        }}>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 2 }}>{sig.category}</div>
                                                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4 }}>{sig.text}</div>
                                            </div>
                                            <span style={{
                                                marginLeft: 'auto', flexShrink: 0, fontSize: 12,
                                                color: sig.direction === 'bullish' ? '#4ade80' : sig.direction === 'bearish' ? '#f87171' : sig.direction === 'historical' ? '#6b7280' : 'var(--text-primary)',
                                            }}>{sig.direction === 'bullish' ? '' : sig.direction === 'bearish' ? '' : sig.direction === 'historical' ? '—' : ''}</span>
                                        </div>
                                    ))}
                                </div>
                            </>
                        ) : null}

                        {isFree && (
                            <div style={{
                                marginTop: 20, padding: '16px 20px', background: '#1e293b', border: '1px solid #334155', borderRadius: 10,
                                textAlign: 'center'
                            }}>
                                <div style={{ color: '#f8fafc', fontSize: 15, fontWeight: 800, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                                    Want to see the full week ahead?
                                </div>
                                <div style={{ color: '#94a3b8', fontSize: 13, marginBottom: 12 }}>
                                    Upgrade to Pro to unlock the complete 7-day comprehensive market forecast and plan your week with precision.
                                </div>
                                <button className="btn-primary" onClick={() => window.location.href = '/pricing'}>
                                    UPGRADE TO PRO FOR 1-WEEK FORECAST
                                </button>
                            </div>
                        )}
                    </div>
                )
            }

            {/* Nifty 50 Scanner Widget */}
            <NiftyScannerWidget />

            {/*  Today's Cosmic Snapshot  */}
            {
                loading ? (
                    <div className="panel" style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
                        <span className="spinner" />
                        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading today's cosmic data…</span>
                    </div>
                ) : insight ? (
                    <>
                        {/*  4-card metrics row  */}
                        <div className="grid-4" style={{ marginBottom: 18 }}>
                            <MetricCard
                                icon=""
                                label="Current Cycle"
                                value={<span className="gradient-text" style={{ fontSize: 20, fontWeight: 800 }}>{insight.current_nakshatra}</span>}
                                sub={insight.nakshatra_sanskrit}
                            />
                            <MetricCard
                                icon=""
                                label="Cycle Position"
                                value={<span className="gradient-text" style={{ fontSize: 20, fontWeight: 800 }}>Phase {insight.pada}</span>}
                                sub={insight.ruling_planet}
                            />
                            <MetricCard
                                icon=""
                                label="Sidereal Longitude"
                                value={
                                    typeof insight.moon_longitude === 'number'
                                        ? <span className="num" style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent-cyan)' }}>{insight.moon_longitude.toFixed(2)}°</span>
                                        : <span style={{ color: 'var(--text-muted)' }}>—</span>
                                }
                                sub="Moon sidereal position"
                            />
                            <MetricCard
                                icon=""
                                label="Historical Tendency"
                                value={<TendencyBadge t={tendency} />}
                                sub="Based on historical data"
                            />
                        </div>

                        {/*  Secondary info row  */}
                        {(insight.tithi_name || insight.yoga_name) && (
                            <div className="grid-3" style={{ marginBottom: 18 }}>
                                {insight.tithi_name && (
                                    <MetricCard icon="" label="Lunar Phase" value={
                                        <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-gold)' }}>{insight.tithi_name}</span>
                                    } sub={insight.paksha ?? ''} />
                                )}
                                {insight.yoga_name && (
                                    <MetricCard icon="" label="Signal Pattern" value={
                                        <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-purple)' }}>{insight.yoga_name}</span>
                                    } sub="Active pattern period" />
                                )}
                                <MetricCard icon="" label="Signal Driver" value={
                                    <span style={{ fontSize: 18, fontWeight: 800, color: 'var(--accent-violet)' }}>{insight.ruling_planet}</span>
                                } sub="Pattern driver" />
                            </div>
                        )}

                        {/*  Insight traits box  */}
                        {insight.favorable_for && (
                            <div className="glass-card" style={{ padding: '18px 22px', marginBottom: 16 }}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 24px' }}>
                                    <div>
                                        <span style={{ color: 'var(--accent-green)', fontWeight: 700, fontSize: 12.5 }}> Favorable for</span>
                                        <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                            {(insight.favorable_for || []).join(', ')}
                                        </p>
                                    </div>
                                    <div>
                                        <span style={{ color: 'var(--accent-red)', fontWeight: 700, fontSize: 12.5 }}> Unfavorable for</span>
                                        <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                            {(insight.unfavorable_for || []).join(', ')}
                                        </p>
                                    </div>
                                    <div>
                                        <span style={{ color: 'var(--accent-gold)', fontWeight: 700, fontSize: 12.5 }}> Financial Traits</span>
                                        <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                            {(insight.financial_traits || []).join(', ')}
                                        </p>
                                    </div>
                                    <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                                        <div>
                                            <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: 12.5 }}> Lucky Numbers</span>
                                            <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
                                                {(insight.lucky_numbers || []).join(', ')}
                                            </p>
                                        </div>
                                        <div>
                                            <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: 12.5 }}> Lucky Colors</span>
                                            <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
                                                {(insight.lucky_colors || []).join(', ')}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/*  Cycle transition  */}
                        {insight.transition && (
                            <div className="alert-info" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
                                <span style={{ fontSize: 18 }}></span>
                                <span>
                                    <strong>Cycle Transition Today:</strong>{' '}
                                    <span style={{ color: 'var(--accent-red)' }}>{insight.transition.from_nakshatra}</span>
                                    {' → '}
                                    <span style={{ color: 'var(--accent-green)' }}>{insight.transition.to_nakshatra}</span>
                                    {' at '}
                                    <span className="num" style={{ color: 'var(--accent-gold)', fontWeight: 600 }}>
                                        {new Date(insight.transition.transition_time).toLocaleString('en-IN', {
                                            day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true
                                        })} (Mumbai Time)
                                    </span>
                                </span>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="alert-warn" style={{ marginBottom: 20 }}> Could not load today's insight. Check backend connection.</div>
                )
            }

            {/*  Analysis Form Panel  */}
            <div className="glass-card" style={{ padding: 28 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
                    <span style={{ fontSize: 20 }}></span>
                    <div>
                        <h2 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>Load Statistical Analysis</h2>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Choose a market, planet, and date range — then run the composite signal backtest</p>
                    </div>
                    {market === 'NASDAQ' && (
                        <span className="badge badge-info" style={{ marginLeft: 'auto' }}> US / Global Market</span>
                    )}
                    {market === 'NSE' && (
                        <span className="badge badge-neutral" style={{ marginLeft: 'auto' }}> NSE India</span>
                    )}
                </div>

                <div className="grid-4" style={{ marginBottom: 20 }}>
                    {/* Market Symbol */}
                    <div>
                        <label className="form-label">Market Symbol</label>
                        <select className="form-select" value={symbol} onChange={e => setSymbol(e.target.value)}>
                            <optgroup label=" India — NSE">
                                <option value="^NSEI">^NSEI (Nifty 50)</option>
                                <option value="^NSEBANK">^NSEBANK (Bank Nifty)</option>
                                <option value="^CNXIT">^CNXIT (Nifty IT)</option>
                                <option value="RELIANCE.NS">RELIANCE.NS (Reliance)</option>
                                <option value="TCS.NS">TCS.NS (TCS)</option>
                                <option value="HDFCBANK.NS">HDFCBANK.NS (HDFC Bank)</option>
                                <option value="INFY.NS">INFY.NS (Infosys)</option>
                            </optgroup>
                            <optgroup label=" USA — NASDAQ / NYSE">
                                <option value="^IXIC">^IXIC (NASDAQ Composite)</option>
                                <option value="^GSPC">^GSPC (S&amp;P 500)</option>
                                <option value="^DJI">^DJI (Dow Jones)</option>
                                <option value="AAPL">AAPL (Apple)</option>
                                <option value="MSFT">MSFT (Microsoft)</option>
                                <option value="NVDA">NVDA (NVIDIA)</option>
                                <option value="TSLA">TSLA (Tesla)</option>
                                <option value="AMZN">AMZN (Amazon)</option>
                                <option value="GOOGL">GOOGL (Alphabet)</option>
                                <option value="META">META (Meta)</option>
                            </optgroup>
                            <optgroup label="🪙 Precious Metals &amp; Commodities">
                                <option value="GC=F">GC=F (Gold Futures)</option>
                                <option value="SI=F">SI=F (Silver Futures)</option>
                                <option value="PL=F">PL=F (Platinum Futures)</option>
                                <option value="PA=F">PA=F (Palladium Futures)</option>
                                <option value="HG=F">HG=F (Copper Futures)</option>
                                <option value="ALI=F">ALI=F (Aluminium Futures)</option>
                            </optgroup>
                            <optgroup label=" Energy">
                                <option value="CL=F">CL=F (Crude Oil WTI)</option>
                                <option value="BZ=F">BZ=F (Brent Crude Oil)</option>
                                <option value="NG=F">NG=F (Natural Gas)</option>
                                <option value="ZC=F">ZC=F (Corn Futures)</option>
                                <option value="ZW=F">ZW=F (Wheat Futures)</option>
                            </optgroup>
                            <optgroup label="₿ Cryptocurrency">
                                <option value="BTC-USD">BTC-USD (Bitcoin)</option>
                                <option value="ETH-USD">ETH-USD (Ethereum)</option>
                                <option value="BNB-USD">BNB-USD (BNB)</option>
                                <option value="SOL-USD">SOL-USD (Solana)</option>
                                <option value="XRP-USD">XRP-USD (XRP)</option>
                                <option value="ADA-USD">ADA-USD (Cardano)</option>
                                <option value="DOGE-USD">DOGE-USD (Dogecoin)</option>
                                <option value="AVAX-USD">AVAX-USD (Avalanche)</option>
                                <option value="DOT-USD">DOT-USD (Polkadot)</option>
                                <option value="LINK-USD">LINK-USD (Chainlink)</option>
                                <option value="MATIC-USD">MATIC-USD (Polygon)</option>
                                <option value="LTC-USD">LTC-USD (Litecoin)</option>
                            </optgroup>
                        </select>
                    </div>

                    {/* Planet */}
                    <div>
                        <label className="form-label">Planet / Body</label>
                        <select className="form-select" value={planet} onChange={e => setPlanet(e.target.value)}>
                            {['Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu'].map(p => (
                                <option key={p} value={p}>{p}</option>
                            ))}
                        </select>
                    </div>

                    {/* Start Date */}
                    <div>
                        <label className="form-label">Start Date <span style={{ fontSize: 9, background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', padding: '2px 6px', borderRadius: 4, marginLeft: 6, fontWeight: 700, letterSpacing: 0.5 }}>FREE LIMIT: 1 YR</span></label>
                        <input className="form-input" type="date" value={startDate}
                            max={endDate}
                            onChange={e => {
                                const start = new Date(e.target.value);
                                const end = new Date(endDate);
                                const diffYears = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24 * 365);
                                if (guardYears(diffYears)) setStartDate(e.target.value);
                            }}
                        />
                    </div>

                    {/* End Date */}
                    <div>
                        <label className="form-label">End Date</label>
                        <input className="form-input" type="date" value={endDate} readOnly style={{ opacity: 0.65, cursor: 'not-allowed' }} />
                    </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
                    <button className="btn-primary" onClick={runAnalysis} disabled={analysing} style={{ minWidth: 220 }}>
                        {analysing
                            ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Analyzing…</>
                            : <> Load & Analyze Data <span style={{ fontSize: 10, padding: '2px 6px', background: 'rgba(255,255,255,0.2)', borderRadius: 4, marginLeft: 6 }}>PRO</span></>
                        }
                    </button>
                    {status && (
                        <span style={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: status.startsWith('') ? 'var(--accent-green)'
                                : status.startsWith('') ? 'var(--accent-red)'
                                    : 'var(--accent-cyan)',
                            display: 'flex', alignItems: 'center', gap: 6,
                        }}>
                            {analysing && <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />}
                            {status}
                        </span>
                    )}
                </div>
            </div>

            {/* Custom Strategy CTA for Pro Traders */}
            <div style={{
                marginTop: 32, padding: '24px', background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16,
                textAlign: 'center'
            }}>
                <div style={{ fontSize: 16, fontWeight: 800, color: '#f8fafc', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Pro Trader with a Custom Strategy?
                </div>
                <div style={{ fontSize: 14, color: '#94a3b8', maxWidth: 600, margin: '0 auto', lineHeight: 1.6 }}>
                    We offer bespoke integrations and custom AI modeling for institutional and professional traders. Contact us to get our engine customized exactly to your proprietary rules and requirements.
                </div>
                <div style={{ marginTop: 16, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
                    <a href="mailto:quant0pattern@gmail.com" style={{
                        display: 'inline-block', padding: '10px 20px', background: '#3b82f6', color: '#fff',
                        fontWeight: 700, borderRadius: 8, fontSize: 13, textDecoration: 'none', textTransform: 'uppercase', letterSpacing: 0.5
                    }}>
                        CONTACT US VIA EMAIL
                    </a>
                    <a href="https://wa.me/9193112255" target="_blank" rel="noopener noreferrer" style={{
                        display: 'inline-block', padding: '10px 20px', background: '#22c55e', color: '#fff',
                        fontWeight: 700, borderRadius: 8, fontSize: 13, textDecoration: 'none', textTransform: 'uppercase', letterSpacing: 0.5
                    }}>
                        CHAT ON WHATSAPP
                    </a>
                </div>
            </div>
        </div >
    );
}
