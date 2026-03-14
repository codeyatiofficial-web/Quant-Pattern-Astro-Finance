'use client';
import React, { useState, useEffect } from 'react';
import { usePlanGate } from './UpgradeModal';
import { usePlan } from '../contexts/PlanContext';
import { MarketTicker } from './MarketTicker';
import NiftyTradingViewWidget from './NiftyTradingViewWidget';
import SignalConfluenceWidget from './SignalConfluenceWidget';
import NiftyHeatmapWidget from './NiftyHeatmapWidget';

const API = '';



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



export default function Dashboard({ onAnalysisDone }: { onAnalysisDone: (data: any) => void }) {
    const { guardYears, requirePlan, modal: planModal } = usePlanGate(1);
    const { tier } = usePlan();
    const isElite = tier === 'elite';
    const isFree = tier === 'free';

    const [analysing, setAnalysing] = useState(false);
    const [forecast, setForecast] = useState<any>(null);
    const [forecastLoading, setForecastLoading] = useState(false);
    const [forecastMarket, setForecastMarket] = useState('NSE');
    const [forecastDate, setForecastDate] = useState(() => new Date().toISOString().slice(0, 10));
    const [weekForecast, setWeekForecast] = useState<any>(null);
    const [weekLoading, setWeekLoading] = useState(true);    useEffect(() => {

        // Fetch 7-day comprehensive forecast for all users
        fetch(`${API}/api/forecast/weekly?market=NSE`)
            .then(r => r.json())
            .then(d => { setWeekForecast(d); setWeekLoading(false); })
            .catch(() => setWeekLoading(false));
    }, []);

    const fetchForecast = () => {
        setForecastLoading(true);
        fetch(`${API}/api/forecast/composite?date=${forecastDate}&market=${forecastMarket}`)
            .then(r => r.json())
            .then(d => { setForecast(d); setForecastLoading(false); })
            .catch(() => setForecastLoading(false));
    };

    return (
        <div>
            {planModal}

            <MarketTicker />



    {/* NIFTY 50 1-MIN CANDLE CHART (Kite API) */ }
    <NiftyTradingViewWidget />

    {/* TELEGRAM BOT CALL TO ACTION */ }
    <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 16,
        padding: '24px',
        marginBottom: 24,
        display: 'flex',
        flexDirection: 'row',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: 20,
    }}>
        <div style={{ flex: '1 1 300px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <h3 style={{ fontSize: 18, fontWeight: 800, color: '#3b82f6', margin: 0, letterSpacing: 0.5 }}>
                    LIVE MAGNITUDE ALERTS
                </h3>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: 12 }}>
                Get instant notifications on your mobile device whenever the system detects a strong positional trading opportunity.
            </p>
            <ul style={{ paddingLeft: 20, margin: 0, fontSize: 12, color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: 6 }}>
                <li>Scans 1-minute candles for deep short-interval signals</li>
                <li>Exact Entry, Target, and Stop-Loss Levels</li>
                <li>Calculated Risk-to-Reward Ratios</li>
            </ul>
        </div>
        
        <div style={{ 
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, 
            background: 'var(--bg-secondary)', padding: '16px 24px', borderRadius: 12,
            border: '1px solid var(--border-subtle)', flex: '0 1 auto'
        }}>
            <img 
                src="/assets/telegram_qr.png" 
                alt="Telegram Bot QR Code" 
                style={{ width: 120, height: 120, borderRadius: 8, objectFit: 'contain', background: '#fff', padding: 4 }} 
                onError={(e) => {
                    // Fallback to placeholder if image is missing
                    const target = e.target as HTMLImageElement;
                    target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120"><rect width="100%" height="100%" fill="%231e293b"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%2364748b" font-family="sans-serif" font-size="12">QR Missing</text></svg>';
                }}
            />
            <a 
                href="https://t.me/QUANTPATTERN_ALERT_BOT" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{
                    background: '#2563eb', color: '#fff', padding: '8px 16px', borderRadius: 6,
                    fontSize: 12, fontWeight: 700, textDecoration: 'none', display: 'inline-block',
                    transition: 'all 0.2s', textAlign: 'center'
                }}
            >
                Open in Telegram
            </a>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>@QUANTPATTERN_ALERT_BOT</span>
        </div>
    </div>

    {/* SIGNAL CONFLUENCE SCORING SYSTEM */ }
    <SignalConfluenceWidget />

    {/* ALGO TRADING PROMO */ }
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '28px', marginBottom: 24 }}>
        <div style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <h3 style={{ fontSize: 20, fontWeight: 900, color: 'var(--text-primary)', margin: 0, letterSpacing: 0.5 }}>ALGO TRADING</h3>
                <span style={{ fontSize: 10, fontWeight: 800, padding: '2px 8px', borderRadius: 6, background: 'rgba(74,222,128,0.15)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.3)', letterSpacing: 1 }}>LIVE</span>
            </div>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6, maxWidth: 700 }}>
                Let the system trade for you. Connect your broker via API key. Every trade executes automatically —
                <strong style={{ color: 'var(--text-primary)' }}> no screen watching, no emotional decisions.</strong>
            </p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 10, marginBottom: 20 }}>
            {[
                '80% accuracy on our live algo setups',
                '1–2 precision trades/day — quality over quantity',
                'Custom setup tailored to your strategy',
                'Equity · Commodity · Currency markets',
                'Pre-built strategies ready to deploy',
                'Minimal charges to link your account',
            ].map((text, i) => (
                <div key={i} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: '11px 15px', fontSize: 13, color: 'var(--text-primary)', fontWeight: 500 }}>
                    {text}
                </div>
            ))}
        </div>
        <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 12, padding: '20px 24px' }}>
            <div style={{ fontSize: 15, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 6 }}>No stress. No screen time. Just results.</div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>More details? Chat with us on WhatsApp — we will help you get started.</div>
            <a href="https://wa.me/919193112255" target="_blank" rel="noopener noreferrer"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 10, background: '#25D366', color: '#fff', padding: '11px 24px', borderRadius: 10, fontSize: 14, fontWeight: 700, textDecoration: 'none' }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
                Chat on WhatsApp
            </a>
        </div>
    </div>

    {/*  1-WEEK COMPREHENSIVE FORECAST (All users)  */ }
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
                        <div className="day-cards-grid" style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(displayedDays.length, 5)}, 1fr)`, gap: 10 }}>
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

    {/*  ELITE: 1-Month Composite Forecast  */ }
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





    {/* Nifty 50 Heatmap */}
    <NiftyHeatmapWidget />

    {/* Custom Strategy CTA for Pro Traders */}
    <div
        style={{
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
            <a href="https://wa.me/919193112255" target="_blank" rel="noopener noreferrer" style={{
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

