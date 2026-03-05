'use client';
import React, { useState, useEffect } from 'react';
import { usePlanGate } from './UpgradeModal';
import { usePlan } from '../contexts/PlanContext';

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
    const icon = t === 'Bullish' ? '▲' : t === 'Bearish' ? '▼' : '●';
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
    const [insight, setInsight] = useState<TodayInsight | null>(null);
    const [loading, setLoading] = useState(true);
    const [analysing, setAnalysing] = useState(false);
    const [forecast, setForecast] = useState<any>(null);
    const [forecastLoading, setForecastLoading] = useState(false);
    const [forecastMarket, setForecastMarket] = useState('NSE');
    const [forecastDate, setForecastDate] = useState(() => new Date().toISOString().slice(0, 10));
    const [weekForecast, setWeekForecast] = useState<any>(null);
    const [weekLoading, setWeekLoading] = useState(true);
    const [symbol, setSymbol] = useState('^NSEI');
    const [planet, setPlanet] = useState('Moon');
    const [startDate, setStartDate] = useState(() => {
        const d = new Date();
        d.setFullYear(d.getFullYear() - 1);
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
        setStatus('Fetching market data & crunching Nakshatras…');
        try {
            const res = await fetch(`${API}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, planet, start_date: startDate, end_date: endDate, market }),
            });
            const data = await res.json();
            onAnalysisDone(data);
            setStatus('✅ Analysis complete! Switching to results…');
        } catch {
            setStatus('❌ Error fetching data. Is the backend running?');
        }
        setAnalysing(false);
    };

    const tendency = insight?.historical_tendency ?? 'Neutral';

    return (
        <div className="fade-in">
            {planModal}
            {/* ── Page Header ── */}
            <div style={{ marginBottom: 24 }}>
                <h1 className="section-title">🌙 Astro-Finance Dashboard</h1>
                <p className="section-subtitle">
                    Correlating Moon's journey through 27 Vedic Nakshatras with global market movements
                </p>
            </div>

            {/* ── ALL TIERS: 7-Day Comprehensive Forecast ── */}
            <div style={{
                background: 'linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(59,130,246,0.05) 100%)',
                border: '1px solid rgba(99,102,241,0.3)',
                borderRadius: 16,
                padding: '20px 24px',
                marginBottom: 24,
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                    <span style={{ fontSize: 20 }}>📅</span>
                    <div>
                        <div style={{ fontSize: 13, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: 0.5 }}>7-DAY MARKET INTELLIGENCE</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Composite: Astro · Planetary Yogas · Technicals · Options · FII/DII · Events · Weekday Seasonality</div>
                    </div>
                </div>

                {weekLoading ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)', padding: '8px 0' }}>
                        <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                        Crunching astro yogas, technicals, options & institutional data…
                    </div>
                ) : weekForecast.days && weekForecast.days.length > 0 ? (
                    <>
                        {/* Global Signals Bar */}
                        {weekForecast.global_signals && (
                            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
                                {weekForecast.global_signals.technical?.text !== 'N/A' && (
                                    <div style={{ padding: '4px 10px', borderRadius: 8, fontSize: 11, background: weekForecast.global_signals.technical?.direction === 'bullish' ? 'rgba(74,222,128,0.12)' : weekForecast.global_signals.technical?.direction === 'bearish' ? 'rgba(248,113,113,0.12)' : 'rgba(255,255,255,0.05)', color: weekForecast.global_signals.technical?.direction === 'bullish' ? '#4ade80' : weekForecast.global_signals.technical?.direction === 'bearish' ? '#f87171' : 'var(--text-muted)', border: '1px solid rgba(255,255,255,0.08)' }}>
                                        📈 {weekForecast.global_signals.technical.text}
                                    </div>
                                )}
                                {weekForecast.global_signals.options?.text !== 'N/A' && (
                                    <div style={{ padding: '4px 10px', borderRadius: 8, fontSize: 11, background: weekForecast.global_signals.options?.direction === 'bullish' ? 'rgba(74,222,128,0.12)' : weekForecast.global_signals.options?.direction === 'bearish' ? 'rgba(248,113,113,0.12)' : 'rgba(255,255,255,0.05)', color: weekForecast.global_signals.options?.direction === 'bullish' ? '#4ade80' : weekForecast.global_signals.options?.direction === 'bearish' ? '#f87171' : 'var(--text-muted)', border: '1px solid rgba(255,255,255,0.08)' }}>
                                        ⛓️ {weekForecast.global_signals.options.text}
                                    </div>
                                )}
                                {weekForecast.global_signals.institutional?.text !== 'N/A' && (
                                    <div style={{ padding: '4px 10px', borderRadius: 8, fontSize: 11, background: weekForecast.global_signals.institutional?.direction === 'bullish' ? 'rgba(74,222,128,0.12)' : weekForecast.global_signals.institutional?.direction === 'bearish' ? 'rgba(248,113,113,0.12)' : 'rgba(255,255,255,0.05)', color: weekForecast.global_signals.institutional?.direction === 'bullish' ? '#4ade80' : weekForecast.global_signals.institutional?.direction === 'bearish' ? '#f87171' : 'var(--text-muted)', border: '1px solid rgba(255,255,255,0.08)' }}>
                                        🏦 {weekForecast.global_signals.institutional.text}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Per-Day Cards */}
                        <div style={{ overflowX: 'auto' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${weekForecast.days.length}, minmax(155px, 1fr))`, gap: 8 }}>
                                {weekForecast.days.map((day: any, i: number) => {
                                    const isToday = i === 0;
                                    return (
                                        <div key={i} style={{
                                            background: day.verdict_color === '#4ade80' || day.verdict_color === '#86efac' ? 'rgba(74,222,128,0.08)' : day.verdict_color === '#f87171' || day.verdict_color === '#fca5a5' ? 'rgba(248,113,113,0.08)' : 'rgba(251,191,36,0.06)',
                                            border: `1px solid ${isToday ? day.verdict_color : 'rgba(255,255,255,0.08)'}`,
                                            borderRadius: 12,
                                            padding: '12px 12px 10px',
                                            position: 'relative',
                                        }}>
                                            {isToday && <div style={{ position: 'absolute', top: -8, left: '50%', transform: 'translateX(-50%)', background: 'var(--accent-cyan)', color: '#000', fontSize: 9, fontWeight: 800, padding: '1px 8px', borderRadius: 8, letterSpacing: 0.5 }}>TODAY</div>}

                                            {/* Date header */}
                                            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 6, textAlign: 'center' }}>
                                                {day.weekday?.slice(0, 3)} {new Date(day.date + 'T00:00:00').toLocaleDateString('en-US', { day: '2-digit', month: 'short' })}
                                            </div>

                                            {/* Verdict */}
                                            <div style={{ textAlign: 'center', marginBottom: 8 }}>
                                                <div style={{ fontSize: 16, fontWeight: 900, color: day.verdict_color }}>
                                                    {day.verdict === 'Strong Buy' ? '▲▲' : day.verdict === 'Bullish' ? '▲' : day.verdict === 'Strong Sell' ? '▼▼' : day.verdict === 'Bearish' ? '▼' : '●'}
                                                </div>
                                                <div style={{ fontSize: 10, fontWeight: 800, color: day.verdict_color, marginTop: 2 }}>{day.verdict}</div>
                                                <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>Score: {day.score}</div>
                                            </div>

                                            {/* Astro details */}
                                            <div style={{ fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.6, borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 6 }}>
                                                <div>🌙 {day.astro?.nakshatra}</div>
                                                <div>🌒 {day.astro?.tithi}</div>
                                                <div>🔮 {day.astro?.yoga}</div>
                                                <div style={{ color: day.weekday_bias?.bias === 'bullish' ? '#86efac' : day.weekday_bias?.bias === 'bearish' ? '#fca5a5' : 'var(--text-muted)' }}>
                                                    📊 {day.weekday_bias?.bias?.charAt(0).toUpperCase() + day.weekday_bias?.bias?.slice(1)} day
                                                </div>
                                            </div>

                                            {/* Active Yogas */}
                                            {day.planetary_yogas && day.planetary_yogas.length > 0 && (
                                                <div style={{ marginTop: 6, borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 6 }}>
                                                    {day.planetary_yogas.slice(0, 3).map((y: any, j: number) => (
                                                        <div key={j} style={{
                                                            fontSize: 9, padding: '2px 6px', marginBottom: 2,
                                                            borderRadius: 6,
                                                            background: y.impact === 'bullish' ? 'rgba(74,222,128,0.15)' : y.impact === 'bearish' ? 'rgba(248,113,113,0.15)' : 'rgba(251,191,36,0.1)',
                                                            color: y.impact === 'bullish' ? '#4ade80' : y.impact === 'bearish' ? '#f87171' : '#fbbf24',
                                                            display: 'flex', alignItems: 'center', gap: 4
                                                        }}>
                                                            <span>{y.icon}</span>
                                                            <span style={{ fontWeight: 700 }}>{y.name}</span>
                                                            <span style={{ marginLeft: 'auto', fontSize: 8, opacity: 0.7 }}>S:{y.severity}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Events */}
                                            {day.events && day.events.length > 0 && (
                                                <div style={{ marginTop: 4 }}>
                                                    {day.events.slice(0, 2).map((ev: any, j: number) => (
                                                        <div key={j} style={{ fontSize: 9, color: '#fbbf24', display: 'flex', alignItems: 'center', gap: 3 }}>
                                                            <span>📋</span> {ev.name?.slice(0, 25)}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </>
                ) : (
                    <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>No forecast data available.</div>
                )}

                {!isElite && (
                    <div style={{ marginTop: 14, padding: '10px 16px', background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 12 }}>
                        <span style={{ fontSize: 16 }}>⭐</span>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            <strong style={{ color: '#fbbf24' }}>Upgrade to Elite</strong> for the full <strong>1-Month Composite Forecast</strong> with date picker, FII/DII institutional flows, options chain analysis, and seasonality scoring.
                        </div>
                    </div>
                )}
            </div>

            {/* ── ELITE: 1-Month Composite Forecast ── */}
            {isElite && (
                <div style={{
                    background: 'linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(180,83,9,0.05) 100%)',
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
                        background: 'linear-gradient(135deg,#f59e0b,#b45309)',
                        color: '#fff', fontSize: 10, fontWeight: 800,
                        padding: '3px 10px', borderRadius: 20, letterSpacing: 1.2,
                    }}>⭐ ELITE</div>

                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 18 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <span style={{ fontSize: 22 }}>🔭</span>
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
                                style={{ padding: '4px 12px', fontSize: 12, height: 'auto', minWidth: 'auto', background: 'rgba(245,158,11,0.2)', border: '1px solid rgba(245,158,11,0.4)', color: '#fbbf24' }}
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
                                            background: `linear-gradient(90deg, ${forecast.verdict_color}88, ${forecast.verdict_color})`,
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
                                        <span style={{ fontSize: 16, flexShrink: 0 }}>{sig.icon}</span>
                                        <div>
                                            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 2 }}>{sig.category}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4 }}>{sig.text}</div>
                                        </div>
                                        <span style={{
                                            marginLeft: 'auto', flexShrink: 0, fontSize: 12,
                                            color: sig.direction === 'bullish' ? '#4ade80' : sig.direction === 'bearish' ? '#f87171' : sig.direction === 'historical' ? '#6b7280' : '#fbbf24',
                                        }}>{sig.direction === 'bullish' ? '▲' : sig.direction === 'bearish' ? '▼' : sig.direction === 'historical' ? '—' : '●'}</span>
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : null}
                </div>
            )}

            {/* ── Today's Cosmic Snapshot ── */}
            {loading ? (
                <div className="panel" style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
                    <span className="spinner" />
                    <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading today's cosmic data…</span>
                </div>
            ) : insight ? (
                <>
                    {/* ── 4-card metrics row ── */}
                    <div className="grid-4" style={{ marginBottom: 18 }}>
                        <MetricCard
                            icon="🌙"
                            label="Current Nakshatra"
                            value={<span className="gradient-text" style={{ fontSize: 20, fontWeight: 800 }}>{insight.current_nakshatra}</span>}
                            sub={insight.nakshatra_sanskrit}
                        />
                        <MetricCard
                            icon="⭐"
                            label="Pada / Planet"
                            value={<span className="gradient-text" style={{ fontSize: 20, fontWeight: 800 }}>Pada {insight.pada}</span>}
                            sub={insight.ruling_planet}
                        />
                        <MetricCard
                            icon="📐"
                            label="Sidereal Longitude"
                            value={
                                typeof insight.moon_longitude === 'number'
                                    ? <span className="num" style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent-cyan)' }}>{insight.moon_longitude.toFixed(2)}°</span>
                                    : <span style={{ color: 'var(--text-muted)' }}>—</span>
                            }
                            sub="Moon sidereal position"
                        />
                        <MetricCard
                            icon="📈"
                            label="Historical Tendency"
                            value={<TendencyBadge t={tendency} />}
                            sub="Based on historical data"
                        />
                    </div>

                    {/* ── Secondary info row ── */}
                    {(insight.tithi_name || insight.yoga_name) && (
                        <div className="grid-3" style={{ marginBottom: 18 }}>
                            {insight.tithi_name && (
                                <MetricCard icon="🌒" label="Tithi" value={
                                    <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-gold)' }}>{insight.tithi_name}</span>
                                } sub={insight.paksha ?? ''} />
                            )}
                            {insight.yoga_name && (
                                <MetricCard icon="🔮" label="Nitya Yoga" value={
                                    <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-purple)' }}>{insight.yoga_name}</span>
                                } sub="Active yoga period" />
                            )}
                            <MetricCard icon="🌿" label="Ruling Planet" value={
                                <span style={{ fontSize: 18, fontWeight: 800, color: 'var(--accent-violet)' }}>{insight.ruling_planet}</span>
                            } sub="Nakshatra lord" />
                        </div>
                    )}

                    {/* ── Insight traits box ── */}
                    {insight.favorable_for && (
                        <div className="glass-card" style={{ padding: '18px 22px', marginBottom: 16 }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 24px' }}>
                                <div>
                                    <span style={{ color: 'var(--accent-green)', fontWeight: 700, fontSize: 12.5 }}>✅ Favorable for</span>
                                    <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {(insight.favorable_for || []).join(', ')}
                                    </p>
                                </div>
                                <div>
                                    <span style={{ color: 'var(--accent-red)', fontWeight: 700, fontSize: 12.5 }}>❌ Unfavorable for</span>
                                    <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {(insight.unfavorable_for || []).join(', ')}
                                    </p>
                                </div>
                                <div>
                                    <span style={{ color: 'var(--accent-gold)', fontWeight: 700, fontSize: 12.5 }}>🎯 Financial Traits</span>
                                    <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {(insight.financial_traits || []).join(', ')}
                                    </p>
                                </div>
                                <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                                    <div>
                                        <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: 12.5 }}>🔢 Lucky Numbers</span>
                                        <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
                                            {(insight.lucky_numbers || []).join(', ')}
                                        </p>
                                    </div>
                                    <div>
                                        <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: 12.5 }}>🎨 Lucky Colors</span>
                                        <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
                                            {(insight.lucky_colors || []).join(', ')}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ── Nakshatra transition ── */}
                    {insight.transition && (
                        <div className="alert-info" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
                            <span style={{ fontSize: 18 }}>🔄</span>
                            <span>
                                <strong>Nakshatra Transition Today:</strong>{' '}
                                <span style={{ color: 'var(--accent-red)' }}>{insight.transition.from_nakshatra}</span>
                                {' → '}
                                <span style={{ color: 'var(--accent-green)' }}>{insight.transition.to_nakshatra}</span>
                                {' at '}
                                <span className="num" style={{ color: 'var(--accent-gold)', fontWeight: 600 }}>{insight.transition.transition_time}</span>
                            </span>
                        </div>
                    )}
                </>
            ) : (
                <div className="alert-warn" style={{ marginBottom: 20 }}>⚠️ Could not load today's insight. Check backend connection.</div>
            )}

            {/* ── Analysis Form Panel ── */}
            <div className="glass-card" style={{ padding: 28 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
                    <span style={{ fontSize: 20 }}>📥</span>
                    <div>
                        <h2 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>Load Statistical Analysis</h2>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Choose a market, planet, and date range — then run the Nakshatra backtest</p>
                    </div>
                    {market === 'NASDAQ' && (
                        <span className="badge badge-info" style={{ marginLeft: 'auto' }}>🇺🇸 US / Global Market</span>
                    )}
                    {market === 'NSE' && (
                        <span className="badge badge-neutral" style={{ marginLeft: 'auto' }}>🇮🇳 NSE India</span>
                    )}
                </div>

                <div className="grid-4" style={{ marginBottom: 20 }}>
                    {/* Market Symbol */}
                    <div>
                        <label className="form-label">Market Symbol</label>
                        <select className="form-select" value={symbol} onChange={e => setSymbol(e.target.value)}>
                            <optgroup label="🇮🇳 India — NSE">
                                <option value="^NSEI">^NSEI (Nifty 50)</option>
                                <option value="^NSEBANK">^NSEBANK (Bank Nifty)</option>
                                <option value="^CNXIT">^CNXIT (Nifty IT)</option>
                                <option value="RELIANCE.NS">RELIANCE.NS (Reliance)</option>
                                <option value="TCS.NS">TCS.NS (TCS)</option>
                                <option value="HDFCBANK.NS">HDFCBANK.NS (HDFC Bank)</option>
                                <option value="INFY.NS">INFY.NS (Infosys)</option>
                            </optgroup>
                            <optgroup label="🇺🇸 USA — NASDAQ / NYSE">
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
                            <optgroup label="🛢️ Energy">
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
                        <label className="form-label">Start Date <span style={{ fontSize: 10, color: '#f59e0b' }}>(Pro for &gt;1 Yr)</span></label>
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
                            : <>🚀 Load & Analyze Data <span style={{ fontSize: 10, padding: '2px 6px', background: 'rgba(255,255,255,0.2)', borderRadius: 4, marginLeft: 6 }}>PRO</span></>
                        }
                    </button>
                    {status && (
                        <span style={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: status.startsWith('✅') ? 'var(--accent-green)'
                                : status.startsWith('❌') ? 'var(--accent-red)'
                                    : 'var(--accent-cyan)',
                            display: 'flex', alignItems: 'center', gap: 6,
                        }}>
                            {analysing && <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />}
                            {status}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
