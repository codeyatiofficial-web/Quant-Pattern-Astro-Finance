'use client';
import React, { useState, useEffect } from 'react';

const API = 'http://localhost:8000';

type Sub = 'live' | 'backtest' | 'forecast' | 'alignment';

function SentimentDot({ score }: { score: number }) {
    const color = score > 0.05 ? 'var(--accent-green)' : score < -0.05 ? 'var(--accent-red)' : 'var(--text-muted)';
    const label = score > 0.05 ? 'Bullish' : score < -0.05 ? 'Bearish' : 'Neutral';
    const icon = score > 0.05 ? '▲' : score < -0.05 ? '▼' : '●';
    return <span style={{ color, fontWeight: 700, fontSize: 12 }}>{icon} {label} ({score.toFixed(3)})</span>;
}

function BiasChip({ bias, confidence }: { bias: string; confidence?: number }) {
    const color = bias === 'Bullish' ? 'var(--accent-green)' : bias === 'Bearish' ? 'var(--accent-red)' : 'var(--text-muted)';
    const bg = bias === 'Bullish' ? 'rgba(52,211,153,0.13)' : bias === 'Bearish' ? 'rgba(248,113,113,0.13)' : 'rgba(100,116,139,0.10)';
    const icon = bias === 'Bullish' ? '▲' : bias === 'Bearish' ? '▼' : '●';
    return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 6, background: bg, color, fontWeight: 700, fontSize: 12.5 }}>
            {icon} {bias}{confidence != null ? ` · ${confidence}%` : ''}
        </span>
    );
}

// NSE symbols for backtest
const NSE_SYMBOLS = ['^NSEI', '^NSEBANK', '^CNXIT', 'RELIANCE.NS', 'TCS.NS', 'INFY.NS'];
const GLOBAL_SYMBOLS = ['^IXIC', '^GSPC', 'GC=F', 'CL=F', 'BTC-USD', 'ETH-USD'];

export default function SentimentVix() {
    const [sub, setSub] = useState<Sub>('live');
    const [liveData, setLiveData] = useState<any>(null);
    const [liveLoading, setLiveLoading] = useState(false);
    const [forecastData, setForecastData] = useState<any>(null);
    const [forecastLoading, setForecastLoading] = useState(false);
    const [fcSymbol, setFcSymbol] = useState('^NSEI');
    const [btData, setBtData] = useState<any>(null);
    const [btLoading, setBtLoading] = useState(false);
    const [btSymbol, setBtSymbol] = useState('^NSEI');
    const [btPeriod, setBtPeriod] = useState('5y');
    const [alignData, setAlignData] = useState<any>(null);
    const [alignLoading, setAlignLoading] = useState(false);

    const fetchLive = async () => {
        setLiveLoading(true);
        try { const r = await fetch(`${API}/api/sentiment/live`); setLiveData(await r.json()); } catch { }
        setLiveLoading(false);
    };

    const fetchForecast = async (sym = fcSymbol) => {
        setForecastLoading(true);
        try {
            const market = GLOBAL_SYMBOLS.includes(sym) ? 'NASDAQ' : 'NSE';
            const r = await fetch(`${API}/api/sentiment/forecast?symbol=${encodeURIComponent(sym)}&market=${market}`);
            setForecastData(await r.json());
        } catch { }
        setForecastLoading(false);
    };

    const fetchBacktest = async () => {
        setBtLoading(true);
        try {
            const r = await fetch(`${API}/api/sentiment/backtest`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol: btSymbol, period: btPeriod }),
            });
            setBtData(await r.json());
        } catch { }
        setBtLoading(false);
    };

    const fetchAlignment = async () => {
        setAlignLoading(true);
        try { const r = await fetch(`${API}/api/sentiment/astro-alignment`); setAlignData(await r.json()); } catch { }
        setAlignLoading(false);
    };

    useEffect(() => {
        if (sub === 'live' && !liveData) fetchLive();
        if (sub === 'forecast' && !forecastData) fetchForecast();
        if (sub === 'alignment' && !alignData) fetchAlignment();
    }, [sub]);

    const SUBTABS = [
        { key: 'live', label: '📰 Live Sentiment' },
        { key: 'backtest', label: '🔁 Sentiment Backtest' },
        { key: 'forecast', label: '🔮 1-Month Forecast' },
        { key: 'alignment', label: '🌌 Astro Alignment' },
    ] as const;

    // Group forecast days by week
    const weeks = forecastData?.daily_forecasts
        ? forecastData.daily_forecasts.reduce((acc: Record<number, any[]>, d: any) => {
            const w = d.week ?? 1;
            if (!acc[w]) acc[w] = [];
            acc[w].push(d);
            return acc;
        }, {} as Record<number, any[]>)
        : {};

    return (
        <div className="fade-in">
            <h1 className="section-title">💬 Sentiment &amp; Market Pulse</h1>
            <p className="section-subtitle">News sentiment scoring, 1-month forecasting, and astro-news alignment</p>

            <div className="tab-list" style={{ marginBottom: 20 }}>
                {SUBTABS.map(s => (
                    <button key={s.key} className={`tab-btn ${sub === s.key ? 'active' : ''}`} onClick={() => setSub(s.key as Sub)}>{s.label}</button>
                ))}
            </div>

            {/* ── LIVE SENTIMENT ── */}
            {sub === 'live' && (
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                        <button className="btn-primary" onClick={fetchLive} disabled={liveLoading}>
                            {liveLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2 }} /> Fetching…</> : '🔄 Refresh Headlines'}
                        </button>
                        {liveData?.overall_score !== undefined && (
                            <div className="glass-card" style={{ padding: '8px 16px', display: 'inline-flex', alignItems: 'center', gap: 16 }}>
                                <div>
                                    <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: 2 }}>Overall Sentiment</div>
                                    <SentimentDot score={liveData.overall_score} />
                                </div>
                                {liveData.counts && (
                                    <div style={{ display: 'flex', gap: 10, fontSize: 12 }}>
                                        <span style={{ color: 'var(--accent-green)', fontWeight: 700 }}>▲ {liveData.counts.bullish ?? 0}</span>
                                        <span style={{ color: 'var(--accent-red)', fontWeight: 700 }}>▼ {liveData.counts.bearish ?? 0}</span>
                                        <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>→ {liveData.counts.neutral ?? 0}</span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                    {liveData?.headlines?.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {liveData.headlines.map((h: any, i: number) => {
                                const s = h.score ?? 0;
                                const left = s > 0.1 ? 'var(--accent-green)' : s < -0.1 ? 'var(--accent-red)' : 'var(--border-subtle)';
                                return (
                                    <div key={i} style={{
                                        background: 'var(--bg-card)',
                                        border: '1px solid var(--border-subtle)',
                                        borderLeft: `3px solid ${left}`,
                                        borderRadius: 10,
                                        padding: '11px 16px',
                                        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 14,
                                        transition: 'all 0.15s ease',
                                    }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: 13.5, color: 'var(--text-primary)', lineHeight: 1.5, fontWeight: 500 }}>{h.title}</div>
                                            <div style={{ marginTop: 5, display: 'flex', gap: 12, fontSize: 11, color: 'var(--text-muted)' }}>
                                                <span style={{ fontWeight: 600 }}>{h.source}</span>
                                                {h.published && <span>{h.published}</span>}
                                            </div>
                                        </div>
                                        <SentimentDot score={s} />
                                    </div>
                                );
                            })}
                        </div>
                    ) : (!liveLoading && <div className="alert-info">No live headlines loaded yet. Click Refresh.</div>)}
                </div>
            )}

            {/* ── SENTIMENT BACKTEST ── */}
            {sub === 'backtest' && (
                <div>
                    <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ fontWeight: 700, marginBottom: 16, fontSize: 15 }}>Historical Sentiment Backtest</h3>
                        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 16, alignItems: 'flex-end' }}>
                            <div>
                                <label className="form-label">Symbol</label>
                                <select className="form-select" value={btSymbol} onChange={e => setBtSymbol(e.target.value)} style={{ width: 200 }}>
                                    <optgroup label="🇮🇳 India — NSE">
                                        {NSE_SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
                                    </optgroup>
                                    <optgroup label="🌍 Global / US">
                                        {GLOBAL_SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
                                    </optgroup>
                                </select>
                            </div>
                            <div>
                                <label className="form-label">Period</label>
                                <select className="form-select" value={btPeriod} onChange={e => setBtPeriod(e.target.value)} style={{ width: 130 }}>
                                    {['1y', '2y', '3y', '5y', '10y'].map(p => <option key={p} value={p}>{p}</option>)}
                                </select>
                            </div>
                            <button className="btn-primary" onClick={fetchBacktest} disabled={btLoading}>
                                {btLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2 }} /> Running…</> : '▶ Run Backtest'}
                            </button>
                        </div>
                    </div>
                    {btData?.stats && (
                        <div className="grid-3" style={{ gap: 16, marginBottom: 20 }}>
                            {(['bullish', 'bearish', 'neutral'] as const).map(k => {
                                const s = btData.stats[k];
                                if (!s) return null;
                                return (
                                    <div key={k} className="glass-card" style={{ padding: 22 }}>
                                        <BiasChip bias={k.charAt(0).toUpperCase() + k.slice(1)} />
                                        <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
                                            {[
                                                { label: 'Signal Days', value: s.count },
                                                { label: 'Win Rate', value: s.win_rate != null ? s.win_rate.toFixed(1) + '%' : '—' },
                                                { label: 'Avg Next Day', value: s.avg_next_day != null ? (s.avg_next_day > 0 ? '+' : '') + s.avg_next_day.toFixed(3) + '%' : '—' },
                                                { label: 'Avg Next Week', value: s.avg_next_week != null ? (s.avg_next_week > 0 ? '+' : '') + s.avg_next_week.toFixed(3) + '%' : '—' },
                                            ].map(r => (
                                                <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5 }}>
                                                    <span style={{ color: 'var(--text-muted)' }}>{r.label}</span>
                                                    <span className="num" style={{ fontWeight: 700 }}>{r.value}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                    {btData?.overall_accuracy != null && (
                        <div className="glass-card" style={{ padding: 20, display: 'flex', alignItems: 'center', gap: 20 }}>
                            <div>
                                <div className="form-label">Overall Signal Accuracy</div>
                                <div className="gradient-text" style={{ fontSize: 28, fontWeight: 800 }}>{btData.overall_accuracy}%</div>
                            </div>
                            {btData.total_trading_days && (
                                <div style={{ borderLeft: '1px solid var(--border-subtle)', paddingLeft: 20 }}>
                                    <div className="form-label">Trading Days Analysed</div>
                                    <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>{btData.total_trading_days?.toLocaleString()}</div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* ── 1-MONTH FORECAST ── */}
            {sub === 'forecast' && (
                <div>
                    {/* Controls */}
                    <div className="glass-card" style={{ padding: 20, marginBottom: 18 }}>
                        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                            <div>
                                <label className="form-label">Symbol</label>
                                <select className="form-select" value={fcSymbol} onChange={e => setFcSymbol(e.target.value)} style={{ width: 220 }}>
                                    <optgroup label="🇮🇳 India — NSE">
                                        {NSE_SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
                                    </optgroup>
                                    <optgroup label="🌍 Global / US / Crypto">
                                        {GLOBAL_SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
                                    </optgroup>
                                </select>
                            </div>
                            <button className="btn-primary" onClick={() => fetchForecast(fcSymbol)} disabled={forecastLoading}>
                                {forecastLoading
                                    ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2 }} /> Generating…</>
                                    : '🔮 Generate 1-Month Forecast'}
                            </button>
                        </div>
                    </div>

                    {/* Outlook summary bar */}
                    {forecastData?.outlook && !forecastData.error && (
                        <div className="glass-card" style={{ padding: '16px 22px', marginBottom: 18, display: 'flex', flexWrap: 'wrap', gap: 20, alignItems: 'center' }}>
                            <div>
                                <div className="form-label">1-Month Outlook — {forecastData.symbol}</div>
                                <BiasChip bias={forecastData.outlook.overall_bias} />
                            </div>
                            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                                {[
                                    { label: '▲ Bullish days', value: forecastData.outlook.bullish_days, color: 'var(--accent-green)' },
                                    { label: '▼ Bearish days', value: forecastData.outlook.bearish_days, color: 'var(--accent-red)' },
                                    { label: '● Neutral days', value: forecastData.outlook.neutral_days, color: 'var(--text-muted)' },
                                    { label: 'Avg Confidence', value: `${forecastData.outlook.avg_confidence?.toFixed(1)}%`, color: 'var(--accent-indigo)' },
                                    { label: 'Vol Regime', value: forecastData.outlook.vol_regime, color: 'var(--accent-gold)' },
                                ].map(m => (
                                    <div key={m.label}>
                                        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.5px', textTransform: 'uppercase', marginBottom: 3 }}>{m.label}</div>
                                        <div className="num" style={{ fontSize: 16, fontWeight: 800, color: m.color }}>{m.value}</div>
                                    </div>
                                ))}
                                {forecastData.outlook.current_price && (
                                    <div>
                                        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.5px', textTransform: 'uppercase', marginBottom: 3 }}>Current Price</div>
                                        <div className="num" style={{ fontSize: 16, fontWeight: 800 }}>{forecastData.outlook.current_price?.toLocaleString()}</div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Calendar-style week-by-week grid */}
                    {Object.keys(weeks).length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            {(Object.entries(weeks) as [string, any[]][]).map(([weekNum, days]) => (
                                <div key={weekNum}>
                                    <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.7px', marginBottom: 8 }}>
                                        📅 Week {weekNum} &nbsp;
                                        <span style={{ fontWeight: 400 }}>
                                            {days[0]?.date} → {days[days.length - 1]?.date}
                                        </span>
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
                                        {days.map((d: any, i: number) => {
                                            const bias = (d.bias || '').toLowerCase();
                                            const borderColor = bias === 'bullish' ? 'var(--accent-green)' : bias === 'bearish' ? 'var(--accent-red)' : 'var(--border-subtle)';
                                            const biasColor = bias === 'bullish' ? 'var(--accent-green)' : bias === 'bearish' ? 'var(--accent-red)' : 'var(--text-muted)';
                                            const biasIcon = bias === 'bullish' ? '▲' : bias === 'bearish' ? '▼' : '●';
                                            return (
                                                <div key={i} style={{
                                                    background: 'var(--bg-card)',
                                                    border: `1px solid ${borderColor}`,
                                                    borderTop: `3px solid ${borderColor}`,
                                                    borderRadius: 12,
                                                    padding: '12px 14px',
                                                }}>
                                                    <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 2 }}>{d.date}</div>
                                                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>{d.day_name}</div>
                                                    <div style={{ fontSize: 16, fontWeight: 800, color: biasColor, marginBottom: 6 }}>{biasIcon} {d.bias}</div>
                                                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Conf: <span className="num" style={{ fontWeight: 700 }}>{d.confidence}%</span></div>
                                                    {d.nakshatra && (
                                                        <div style={{ marginTop: 6, fontSize: 10, color: 'var(--accent-violet)', fontWeight: 600 }}>
                                                            🌙 {d.nakshatra}
                                                        </div>
                                                    )}
                                                    {d.ruling_planet && (
                                                        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{d.ruling_planet}</div>
                                                    )}
                                                    {d.events && d.events.length > 0 && (
                                                        <div style={{ marginTop: 6/*, overflow: 'hidden'*/ }}>
                                                            {d.events.slice(0, 1).map((ev: string, ei: number) => (
                                                                <div key={ei} style={{ fontSize: 9, color: 'var(--accent-gold)', lineHeight: 1.3, fontWeight: 600 }}>{ev}</div>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Upcoming economic events list */}
                    {forecastData?.upcoming_events?.length > 0 && (
                        <div style={{ marginTop: 24 }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.7px', marginBottom: 10 }}>
                                📆 Upcoming Key Events This Month
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {forecastData.upcoming_events.slice(0, 12).map((ev: any, i: number) => (
                                    <div key={i} style={{
                                        display: 'flex', alignItems: 'center', gap: 14,
                                        background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                                        borderRadius: 10, padding: '10px 16px',
                                    }}>
                                        <span style={{ fontSize: 18 }}>{ev.emoji ?? '📅'}</span>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{ev.description}</div>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{ev.category} · {ev.date}</div>
                                        </div>
                                        <span className="num" style={{ fontSize: 12, color: 'var(--accent-gold)', fontWeight: 700 }}>T+{ev.days_away}d</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {forecastData?.error && <div className="alert-warn">⚠️ {forecastData.error}</div>}
                </div>
            )}

            {/* ── ASTRO ALIGNMENT ── */}
            {sub === 'alignment' && (
                <div>
                    <button className="btn-primary" onClick={fetchAlignment} disabled={alignLoading} style={{ marginBottom: 16 }}>
                        {alignLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2 }} /> Analyzing…</> : '🌌 Analyze Astro-News Alignment'}
                    </button>
                    {alignData && (
                        <div className="grid-2">
                            <div className="glass-card" style={{ padding: 24 }}>
                                <h3 style={{ fontWeight: 700, marginBottom: 14, fontSize: 15 }}>Active Astro States</h3>
                                {alignData.active_astro_states?.retrograde_planets?.length > 0 && (
                                    <div style={{ marginBottom: 12 }}>
                                        <div className="form-label" style={{ marginBottom: 6 }}>Retrograde Planets</div>
                                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                            {alignData.active_astro_states.retrograde_planets.map((p: string) => (
                                                <span key={p} className="badge badge-bearish">{p} ℞</span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {alignData.active_astro_states?.yogas?.length > 0 && (
                                    <div>
                                        <div className="form-label" style={{ marginBottom: 6 }}>Active Yogas</div>
                                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                            {alignData.active_astro_states.yogas.map((y: string) => (
                                                <span key={y} className="badge badge-neutral">{y.replace(/_/g, ' ')}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {!alignData.active_astro_states?.retrograde_planets?.length && !alignData.active_astro_states?.yogas?.length && (
                                    <div className="alert-info">✅ No major adverse astro states active today.</div>
                                )}
                            </div>
                            <div className="glass-card" style={{ padding: 24 }}>
                                <h3 style={{ fontWeight: 700, marginBottom: 14, fontSize: 15 }}>News–Astro Alignment Score</h3>
                                {alignData.alignment_score !== undefined && (
                                    <div style={{ marginBottom: 14 }}>
                                        <div className="form-label">Score</div>
                                        <div className="num" style={{
                                            fontSize: 30, fontWeight: 800,
                                            color: alignData.alignment_score > 0 ? 'var(--accent-green)' : 'var(--accent-red)'
                                        }}>
                                            {alignData.alignment_score > 0 ? '+' : ''}{alignData.alignment_score?.toFixed(3)}
                                        </div>
                                    </div>
                                )}
                                {alignData.interpretation && <div className="insight-box" style={{ fontSize: 13, lineHeight: 1.7 }}>{alignData.interpretation}</div>}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
