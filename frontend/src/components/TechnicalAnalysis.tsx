import React, { useState, useEffect } from 'react';
import { usePlanGate } from './UpgradeModal';
import LiveChart from './LiveChart';
import { AuthModal } from './AuthModal';

const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

// ── Color helpers ─────────────────────────────────────────────────────────────
const pct_color = (v: number | null) =>
    v == null ? 'var(--text-muted)' : v >= 55 ? 'var(--accent-green)' : v >= 45 ? 'var(--accent-gold)' : 'var(--accent-red)';
const ret_color = (v: number | null) =>
    v == null ? 'var(--text-muted)' : v > 0 ? 'var(--accent-green)' : 'var(--accent-red)';

function Badge({ v }: { v: string }) {
    const map: Record<string, string> = {
        Bullish: '#10b981', Bearish: '#ef4444', Neutral: '#94a3b8',
        Win: '#10b981', Loss: '#ef4444', Triggered: '#8b5cf6', Forming: '#f59e0b', Completing: '#f97316',
    };
    const c = Object.entries(map).find(([k]) => v?.includes(k))?.[1] ?? '#94a3b8';
    return (
        <span style={{ background: c + '22', color: c, border: `1px solid ${c}44`, padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600 }}>
            {v}
        </span>
    );
}

function IndicatorPill({ label, value, good, bad }: { label: string; value: any; good?: boolean; bad?: boolean }) {
    const color = good ? 'var(--accent-green)' : bad ? 'var(--accent-red)' : '#94a3b8';
    return (
        <div style={{ background: `${color}11`, border: `1px solid ${color}33`, borderRadius: 8, padding: '6px 10px', minWidth: 90 }}>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 2 }}>{label}</div>
            <div style={{ fontSize: 12, fontWeight: 700, color }}>{value ?? '—'}</div>
        </div>
    );
}

// ── Pattern card ─────────────────────────────────────────────────────────────
function PatternCard({ pat }: { pat: any }) {
    const [open, setOpen] = useState(false);
    const wr = pat.win_rate;
    const isHarmonic = pat.source === 'Harmonic';
    const isCandle = pat.source === 'Candlestick';

    return (
        <div style={{ background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: 16, marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 14, fontWeight: 700 }}>
                            {isHarmonic ? '〽️' : isCandle ? '🕯' : '📊'} {pat.pattern_name || pat.name}
                        </span>
                        <Badge v={pat.bias || 'Neutral'} />
                        <Badge v={pat.status || 'Monitoring'} />
                        <span style={{ fontSize: 10, color: '#94a3b8', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: 6 }}>{pat.source}</span>
                    </div>
                    {pat.completion_pct != null && (
                        <div style={{ marginTop: 8 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', marginBottom: 3 }}>
                                <span>Completion</span><span>{pat.completion_pct}%</span>
                            </div>
                            <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: 4, height: 5, overflow: 'hidden' }}>
                                <div style={{ width: `${pat.completion_pct}%`, background: pat.completion_pct >= 75 ? '#10b981' : '#f59e0b', height: '100%', transition: 'width 0.4s' }} />
                            </div>
                        </div>
                    )}
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                    <IndicatorPill label="Win Rate" value={wr != null ? `${wr}%` : '—'} good={wr >= 55} bad={wr < 45 && wr != null} />
                    <IndicatorPill label="Avg Return" value={pat.avg_return != null ? `${pat.avg_return > 0 ? '+' : ''}${pat.avg_return?.toFixed(2)}%` : '—'}
                        good={pat.avg_return > 0} bad={pat.avg_return < 0} />
                    <IndicatorPill label="Trades" value={`${(pat.wins ?? 0) + (pat.losses ?? 0)}`} />
                </div>
            </div>

            {/* PRZ / Target / Stop */}
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 14 }}>
                {pat.prz && <div style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.25)', borderRadius: 8, padding: '6px 12px' }}>
                    <div style={{ fontSize: 9, color: '#a78bfa', fontWeight: 700 }}>PRZ / Entry</div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#c4b5fd' }}>{pat.prz}</div>
                </div>}
                {pat.target && <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 8, padding: '6px 12px' }}>
                    <div style={{ fontSize: 9, color: '#6ee7b7', fontWeight: 700 }}>Target</div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#6ee7b7' }}>{pat.target}</div>
                </div>}
                {pat.stop && <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, padding: '6px 12px' }}>
                    <div style={{ fontSize: 9, color: '#fca5a5', fontWeight: 700 }}>Stop Loss</div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#fca5a5' }}>{pat.stop}</div>
                </div>}
            </div>

            {/* Volume confirmation & indicators */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                {pat.vol_label && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>📊 Vol: <strong style={{ color: 'white' }}>{pat.vol_label}</strong></span>}
                {pat.rsi != null && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>RSI: <strong style={{ color: pat.rsi > 70 ? 'var(--accent-red)' : pat.rsi < 30 ? 'var(--accent-green)' : 'white' }}>{pat.rsi}</strong></span>}
                {pat.macd_bull != null && <span style={{ fontSize: 10, color: pat.macd_bull ? 'var(--accent-green)' : 'var(--accent-red)' }}>{pat.macd_bull ? '📈 MACD Bull' : '📉 MACD Bear'}</span>}
                {pat.obv_rising != null && <span style={{ fontSize: 10, color: pat.obv_rising ? 'var(--accent-green)' : 'var(--accent-red)' }}>{pat.obv_rising ? '📊 OBV Rising' : '📊 OBV Falling'}</span>}
                {pat.price_above_vwap != null && <span style={{ fontSize: 10, color: pat.price_above_vwap ? 'var(--accent-green)' : 'var(--accent-red)' }}>{pat.price_above_vwap ? '✅ Above VWAP' : '❌ Below VWAP'}</span>}
                {pat.sharpe_like != null && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Sharpe: <strong style={{ color: 'white' }}>{pat.sharpe_like}</strong></span>}
                {pat.max_drawdown != null && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Max DD: <strong style={{ color: 'var(--accent-red)' }}>{pat.max_drawdown?.toFixed(1)}%</strong></span>}
            </div>

            {/* Harmonic ratios */}
            {pat.ratios && (
                <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                    {Object.entries(pat.ratios).map(([k, v]: [string, any]) => (
                        <span key={k} style={{ fontSize: 10, background: 'rgba(139,92,246,0.1)', borderRadius: 6, padding: '2px 6px', color: '#a78bfa' }}>{k}: {v}</span>
                    ))}
                </div>
            )}

            {/* Recent trades toggle */}
            {pat.trades?.length > 0 && (
                <div style={{ marginTop: 10 }}>
                    <button onClick={() => setOpen(!open)} style={{ background: 'none', border: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)', borderRadius: 6, padding: '3px 10px', fontSize: 11, cursor: 'pointer' }}>
                        {open ? '▲ Hide' : '▼ Show'} Backtest Trades ({pat.trades.length})
                    </button>
                    {open && (
                        <div style={{ overflowX: 'auto', marginTop: 8 }}>
                            <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ color: 'var(--text-muted)', textAlign: 'left' }}>
                                        <th style={{ padding: '4px 8px' }}>Date</th>
                                        <th style={{ padding: '4px 8px' }}>Result</th>
                                        <th style={{ padding: '4px 8px' }}>Return</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {pat.trades.map((t: any, i: number) => (
                                        <tr key={i} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                                            <td style={{ padding: '4px 8px', color: '#94a3b8' }}>{t.date}</td>
                                            <td style={{ padding: '4px 8px' }}><Badge v={t.result} /></td>
                                            <td style={{ padding: '4px 8px', fontWeight: 600, color: t.return?.startsWith('+') ? 'var(--accent-green)' : 'var(--accent-red)' }}>{t.return}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ─── Fibonacci Panel ──────────────────────────────────────────────────────────
function FibPanel({ fib }: { fib: any }) {
    if (!fib || !fib.fib_levels) return null;
    const levels = Object.entries(fib.fib_levels);
    const pivots = fib.pivots;

    return (
        <div className="glass-card" style={{ padding: 20, marginBottom: 16 }}>
            <h4 style={{ fontWeight: 700, marginBottom: 14, fontSize: 14 }}>📐 Fibonacci Levels</h4>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                <span style={{ fontSize: 11, color: '#94a3b8' }}>Swing High: <strong style={{ color: '#f59e0b' }}>{fib.swing_high?.toLocaleString('en-IN')}</strong></span>
                <span style={{ fontSize: 11, color: '#94a3b8', marginLeft: 8 }}>Swing Low: <strong style={{ color: '#a78bfa' }}>{fib.swing_low?.toLocaleString('en-IN')}</strong></span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 6, marginBottom: 14 }}>
                {levels.slice(0, 24).map(([k, v]: any) => (
                    <div key={k} style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 6, padding: '4px 8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: 10, color: k.startsWith('Ext') ? '#f59e0b' : '#94a3b8' }}>{k.replace('Ret_', '').replace('Ext_', '🅴 ')}</span>
                        <span style={{ fontSize: 11, fontWeight: 600, color: 'white' }}>{Number(v)?.toLocaleString('en-IN')}</span>
                    </div>
                ))}
            </div>
            {pivots && (
                <div>
                    <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 700, marginBottom: 6 }}>Floor Trader Pivots</div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {[['R2', '#ef4444'], ['R1', '#f97316'], ['P', '#10b981'], ['S1', '#6366f1'], ['S2', '#8b5cf6']].map(([k, c]) => (
                            <div key={k} style={{ background: `${c}15`, border: `1px solid ${c}33`, borderRadius: 8, padding: '6px 10px' }}>
                                <div style={{ fontSize: 9, color: c as string, fontWeight: 700 }}>{k}</div>
                                <div style={{ fontSize: 12, fontWeight: 700, color: 'white' }}>{pivots[k]?.toLocaleString('en-IN')}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── Week Prediction Panel ────────────────────────────────────────────────────
function WeekPrediction({ pred, tier, guardPeriod }: { pred: any, tier: string, guardPeriod: (p: string) => void }) {
    if (!pred || pred.error || !pred.days) return null;
    const colors: Record<string, string> = { Bullish: '#10b981', Bearish: '#ef4444', Neutral: '#94a3b8' };
    const biasColor = colors[pred.bias] ?? '#94a3b8';

    const displayDays = tier === 'elite' ? pred.days.slice(0, 10) : tier === 'pro' ? pred.days.slice(0, 5) : pred.days.slice(0, 1);
    const title = tier === 'elite' ? '2-Week Technical Prediction' : tier === 'pro' ? '1-Week Technical Prediction' : '1-Day Technical Prediction';

    return (
        <>
            <div className="glass-card" style={{ padding: 20, marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
                    <h4 style={{ fontWeight: 700, fontSize: 14 }}>🔮 {title}</h4>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <Badge v={pred.bias} />
                        <span style={{ fontSize: 11, color: '#94a3b8' }}>Current: <strong style={{ color: 'white' }}>{pred.current_price?.toLocaleString()}</strong></span>
                        <span style={{ fontSize: 11, color: '#94a3b8' }}>RSI: <strong style={{ color: pred.rsi > 70 ? '#ef4444' : pred.rsi < 30 ? '#10b981' : 'white' }}>{pred.rsi}</strong></span>
                        <span style={{ fontSize: 11, color: '#94a3b8' }}>ATR: <strong style={{ color: 'white' }}>{pred.atr?.toLocaleString('en-IN')}</strong></span>
                    </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: 8 }}>
                    {displayDays.map((d: any, i: number) => (
                        <div key={i} style={{ background: `${biasColor}08`, border: `1px solid ${biasColor}22`, borderRadius: 10, padding: 12, textAlign: 'center' }}>
                            <div style={{ fontSize: 10, color: '#94a3b8', fontWeight: 700, marginBottom: 6 }}>{d.day}</div>
                            <div style={{ fontSize: 13, fontWeight: 700, color: biasColor, marginBottom: 4 }}>
                                {d.projected?.toLocaleString('en-IN')}
                            </div>
                            <div style={{ fontSize: 9, color: '#10b981' }}>H: {d.upper_band?.toLocaleString('en-IN')}</div>
                            <div style={{ fontSize: 9, color: '#ef4444' }}>L: {d.lower_band?.toLocaleString('en-IN')}</div>
                        </div>
                    ))}
                </div>
                <div style={{ marginTop: 10, fontSize: 10, color: 'var(--text-muted)', textAlign: 'center' }}>
                    Based on linear momentum, ATR bands, and RSI weighted drift. Not financial advice.
                </div>
            </div>
            {/* Upsell Banner */}
            {tier !== 'elite' && (
                <div style={{ marginBottom: 18, padding: 20, background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Unlock Extended Predictions</div>
                    {tier === 'free' && (
                        <div className="group transition-all duration-300" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: 8, cursor: 'pointer' }} onClick={() => guardPeriod('15y')} >
                            <div>
                                <div style={{ fontSize: 13, fontWeight: 700, color: '#f59e0b', marginBottom: 2 }}>🚀 Pro Plan</div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Get full 1-Week AI Technical Predictions (5-Days)</div>
                            </div>
                            <button className="btn-primary" style={{ padding: '6px 14px', fontSize: 12, background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', border: 'none' }}>Upgrade to Pro</button>
                        </div>
                    )}
                    <div className="group transition-all duration-300" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'rgba(168, 85, 247, 0.05)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: 8, cursor: 'pointer' }} onClick={() => guardPeriod('30y')} >
                        <div>
                            <div style={{ fontSize: 13, fontWeight: 700, color: '#a855f7', marginBottom: 2 }}>💎 Elite Plan</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Get max 2-Week AI Technical Predictions (10-Days)</div>
                        </div>
                        <button className="btn-primary" style={{ padding: '6px 14px', fontSize: 12, background: 'linear-gradient(135deg, #a855f7 0%, #7e22ce 100%)', border: 'none' }}>Upgrade to Elite</button>
                    </div>
                </div>
            )}
        </>
    );
}

// ─── Timeframe Tab ────────────────────────────────────────────────────────────
function TimeframePane({ label, data, isNSE }: { label: string; data: any; isNSE: boolean }) {
    if (!data) return null;

    const ind = data.indicators;
    const pats = data.patterns ?? [];

    return (
        <div>
            {/* Data transparency badge */}
            {(data.total_candles || data.data_range) && (
                <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap', alignItems: 'center' }}>
                    {data.total_candles && (
                        <span style={{ fontSize: 11, background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8, padding: '3px 10px', color: '#a5b4fc', fontWeight: 600 }}>
                            📊 {data.total_candles.toLocaleString()} candles analyzed
                        </span>
                    )}
                    {data.data_range && (
                        <span style={{ fontSize: 11, background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 8, padding: '3px 10px', color: '#fcd34d' }}>
                            📅 {data.data_range}
                        </span>
                    )}
                </div>
            )}

            {/* Indicator strip */}
            {ind && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
                    <IndicatorPill label="Price" value={`${isNSE ? '₹' : ''}${ind.current_price?.toLocaleString()}`} />
                    <IndicatorPill label="RSI" value={`${ind.rsi} ${ind.rsi_signal === 'Overbought' ? '🔴' : ind.rsi_signal === 'Oversold' ? '🟢' : '⚪'}`}
                        good={ind.rsi_signal === 'Oversold'} bad={ind.rsi_signal === 'Overbought'} />
                    <IndicatorPill label="MACD" value={ind.macd_bull ? '📈 Bullish' : '📉 Bearish'}
                        good={ind.macd_bull === true} bad={ind.macd_bull === false} />
                    <IndicatorPill label="Boll%" value={`${ind.boll_position?.toFixed(0)}%`}
                        good={ind.boll_position < 30} bad={ind.boll_position > 70} />
                    <IndicatorPill label="Vol Ratio" value={`${ind.vol_ratio}x`}
                        good={ind.vol_ratio >= 1.3} bad={ind.vol_ratio < 0.7} />
                    <IndicatorPill label="ATR" value={ind.atr?.toLocaleString('en-IN')} />
                    <IndicatorPill label="OBV" value={ind.obv_rising ? '↑ Rising' : '↓ Falling'}
                        good={ind.obv_rising === true} bad={ind.obv_rising === false} />
                    {ind.price_above_vwap != null && <IndicatorPill label="VWAP" value={ind.price_above_vwap ? '✅ Above' : '❌ Below'}
                        good={ind.price_above_vwap === true} bad={ind.price_above_vwap === false} />}
                </div>
            )}

            {data.error && (
                <div style={{ color: 'var(--accent-red)', fontSize: 12, padding: '8px 12px', background: 'rgba(239,68,68,0.08)', borderRadius: 8, marginBottom: 10 }}>
                    ⚠️ {data.error}
                </div>
            )}

            {pats.length > 0 ? (
                pats.map((p: any, i: number) => <PatternCard key={i} pat={p} />)
            ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: 12, padding: '12px 0' }}>
                    No strong patterns detected in {label} timeframe.
                </div>
            )}
        </div>
    );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function TechnicalAnalysis({ active }: { active: boolean }) {
    const [symbol, setSymbol] = useState('^NSEI');
    const [market, setMarket] = useState('NSE');
    const [period, setPeriod] = useState('1y');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('');
    const [liveFallbackUsed, setLiveFallbackUsed] = useState(false);

    // Auth State
    const [showAuth, setShowAuth] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    const { guardPeriod, modal: planModal, tier } = usePlanGate(1);

    // Check auth on load
    useEffect(() => {
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('auth_token');
            setIsAuthenticated(!!token);
        }
    }, [showAuth]);

    // Symbol → market auto-detection
    const US_GLOBAL = new Set([
        '^IXIC', '^GSPC', '^DJI', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META',
        'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'PL=F', 'PA=F', 'ALI=F', 'ZC=F', 'ZW=F',
        'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD',
        'AVAX-USD', 'DOT-USD', 'LINK-USD', 'MATIC-USD', 'LTC-USD',
    ]);
    const derivedMarket = US_GLOBAL.has(symbol) ? 'NASDAQ' : market;
    const PERIODS = ['1y', '2y', '5y', '10y', '20y', 'max'];

    const runScan = async () => {
        if (!isAuthenticated) {
            setShowAuth(true);
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null); setActiveTab(''); setLiveFallbackUsed(false);
        try {
            const res = await fetch(`${API}/api/analyze/technical`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, market: derivedMarket, historical_period: period }),
            });
            const data = await res.json();
            if (!res.ok || !data.success) { setError(data.detail || 'Scan failed'); }
            else {
                setResult(data);
                if (data.live_fallback_used) {
                    setLiveFallbackUsed(true);
                    if (data.symbol !== symbol) {
                        setSymbol(data.symbol);
                        if (data.symbol === 'CL=F') setMarket('Global');
                    }
                }
                const first = Object.keys(data.scans || {})[0];
                if (first) setActiveTab(first);
            }
        } catch { setError('Network error – is backend running?'); }
        setLoading(false);
    };

    const scans: Record<string, any> = result?.scans ?? {};
    const tfLabels = Object.keys(scans);

    const TF_COLORS: Record<string, string> = {
        '1m': '#8b5cf6', '5m': '#6366f1', '15m': '#3b82f6',
        '1h': '#10b981', 'Daily': '#f59e0b', 'Weekly': '#f97316',
    };

    return (
        <div>
            {planModal}
            <h1 className="section-title">🔬 Technical Analysis</h1>
            <p className="section-subtitle">
                Harmonics (Gartley/Bat/Butterfly/Crab/Cypher/ABCD) · 25+ Candlestick Patterns · Fibonacci · VWAP · OBV · MACD · RSI · ATR · 1-Week Forecast
            </p>

            {/* Config Card */}
            <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 16 }}>
                    <div style={{ minWidth: 200 }}>
                        <label className="form-label">Symbol</label>
                        <select className="form-select" value={symbol} onChange={e => setSymbol(e.target.value)}>
                            <optgroup label="🇮🇳 India — NSE">
                                <option value="^NSEI">^NSEI (Nifty 50)</option>
                                <option value="^NSEBANK">^NSEBANK (Bank Nifty)</option>
                                <option value="^CNXIT">^CNXIT (Nifty IT)</option>
                                <option value="^CNXAUTO">^CNXAUTO (Nifty Auto)</option>
                                <option value="^CNXFMCG">^CNXFMCG (Nifty FMCG)</option>
                                <option value="^CNXPHARMA">^CNXPHARMA (Nifty Pharma)</option>
                                <option value="^CNXMETAL">^CNXMETAL (Nifty Metal)</option>
                                <option value="RELIANCE.NS">RELIANCE.NS</option>
                                <option value="TCS.NS">TCS.NS</option>
                                <option value="HDFCBANK.NS">HDFCBANK.NS</option>
                                <option value="INFY.NS">INFY.NS</option>
                                <option value="ICICIBANK.NS">ICICIBANK.NS</option>
                                <option value="SBIN.NS">SBIN.NS</option>
                                <option value="WIPRO.NS">WIPRO.NS</option>
                                <option value="ADANIENT.NS">ADANIENT.NS</option>
                                <option value="BAJFINANCE.NS">BAJFINANCE.NS</option>
                                <option value="AXISBANK.NS">AXISBANK.NS</option>
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
                            <optgroup label="🪙 Precious Metals">
                                <option value="GC=F">GC=F (Gold)</option>
                                <option value="SI=F">SI=F (Silver)</option>
                                <option value="PL=F">PL=F (Platinum)</option>
                                <option value="PA=F">PA=F (Palladium)</option>
                                <option value="HG=F">HG=F (Copper)</option>
                                <option value="ALI=F">ALI=F (Aluminium)</option>
                            </optgroup>
                            <optgroup label="🛢️ Energy &amp; Commodities">
                                <option value="CL=F">CL=F (Crude Oil WTI)</option>
                                <option value="BZ=F">BZ=F (Brent Crude)</option>
                                <option value="NG=F">NG=F (Natural Gas)</option>
                                <option value="ZC=F">ZC=F (Corn)</option>
                                <option value="ZW=F">ZW=F (Wheat)</option>
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
                    <div style={{ minWidth: 130 }}>
                        <label className="form-label">Market</label>
                        <select className="form-select" value={derivedMarket} disabled style={{ opacity: 0.7 }}>
                            <option value="NSE">NSE 🇮🇳</option>
                            <option value="NASDAQ">NASDAQ 🌍</option>
                        </select>
                    </div>
                    <div style={{ minWidth: 130 }}>
                        <label className="form-label">Backtest Period <span style={{ fontSize: 10, color: '#f59e0b' }}>(Pro)</span></label>
                        <select className="form-select" value={period} onChange={e => { if (guardPeriod(e.target.value)) setPeriod(e.target.value); }}>
                            {PERIODS.map(p => <option key={p} value={p}>{p} {p !== '1y' && '🔒'}</option>)}
                        </select>
                    </div>
                    <button className="btn-primary" onClick={runScan} disabled={loading} style={{ minWidth: 220, alignSelf: 'flex-end' }}>
                        {loading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Scanning All Timeframes…</> : '🔬 Run Full Technical Scan'}
                    </button>
                </div>

                {/* What's included */}
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {['〽️ Harmonic (7 types)', '🕯 Candlestick (25+)', '📊 Chart Patterns',
                        '📐 Fibonacci + Pivots', '📈 MACD + RSI', '📊 OBV + VWAP',
                        '⚡ Volume Confirm', '🔮 1-Week Forecast'].map(t => (
                            <span key={t} style={{ fontSize: 10, background: 'rgba(139,92,246,0.12)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 14, padding: '3px 10px', color: '#c4b5fd' }}>{t}</span>
                        ))}
                </div>

                {error && <div className="alert-error" style={{ marginTop: 14 }}>❌ {error}</div>}
            </div>

            {liveFallbackUsed && (
                <div style={{
                    background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)',
                    padding: '12px 16px', borderRadius: 8, marginBottom: 16, color: '#fcd34d',
                    display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, fontWeight: 600
                }}>
                    <span>⚠️ NSE Offline</span>
                    <span style={{ color: '#fff', fontWeight: 400 }}>| Temporarily switched to Crude Oil (CL=F) for live market testing and pattern analysis.</span>
                </div>
            )}

            {showAuth && (
                <AuthModal
                    onClose={() => setShowAuth(false)}
                    onSuccess={() => {
                        setShowAuth(false);
                        runScan();
                    }}
                />
            )}

            {/* ── Live Chart ─────────────────────────────────────────────── */}
            <LiveChart
                symbol={symbol}
                patterns={result ? Object.values(result.scans || {}).flatMap((s: any) => (s.patterns || []).map((p: any) => ({
                    name: p.name,
                    date: p.last_occurrences?.[0]?.date,
                    bias: p.bias,
                })).filter((p: any) => p.date)) : []}
            />

            {result && (
                <div>
                    {/* ── 1-Week Prediction ────────────────────────────────────── */}
                    <WeekPrediction pred={result.week_prediction} tier={tier} guardPeriod={guardPeriod} />

                    {/* ── Fibonacci Levels ─────────────────────────────────────── */}
                    <FibPanel fib={result.fibonacci} />

                    {/* ── Astro Triggers ───────────────────────────────────────── */}
                    {result.astro_confluence?.length > 0 && (
                        <div className="glass-card" style={{ padding: 20, marginBottom: 16 }}>
                            <h4 style={{ fontWeight: 700, marginBottom: 12, fontSize: 14 }}>⚡ Upcoming AI Signal Triggers (7 Days)</h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {result.astro_confluence.map((t: any, i: number) => (
                                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: '8px 12px' }}>
                                        <div>
                                            <span style={{ fontWeight: 600, fontSize: 13 }}>{t.event}</span>
                                        </div>
                                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                            <span style={{ fontSize: 12, color: '#f59e0b' }}>{t.date}</span>
                                            {t.bias && <Badge v={t.bias} />}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ── Multi-Timeframe Tabs ─────────────────────────────────── */}
                    {tfLabels.length > 0 && (
                        <div className="glass-card" style={{ padding: 24 }}>
                            <h3 style={{ fontWeight: 700, marginBottom: 16, fontSize: 15 }}>
                                📊 Multi-Timeframe Pattern Scan — {result.symbol}
                            </h3>

                            {/* Timeframe selector */}
                            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
                                {tfLabels.map(tf => {
                                    const hasPatterns = (scans[tf]?.patterns?.length ?? 0) > 0;
                                    const candleCount = scans[tf]?.total_candles;
                                    const col = TF_COLORS[tf] ?? '#6366f1';
                                    const active = activeTab === tf;
                                    return (
                                        <button key={tf} onClick={() => setActiveTab(tf)} style={{
                                            padding: '8px 16px', borderRadius: 10, fontWeight: 700, fontSize: 12, cursor: 'pointer',
                                            border: `1px solid ${active ? col : 'rgba(255,255,255,0.1)'}`,
                                            background: active ? `${col}22` : 'rgba(255,255,255,0.02)',
                                            color: active ? 'white' : '#94a3b8', position: 'relative',
                                        }}>
                                            {tf}
                                            {candleCount && <span style={{ fontSize: 9, marginLeft: 4, opacity: 0.7 }}>({candleCount.toLocaleString()})</span>}
                                            {hasPatterns && <span style={{ position: 'absolute', top: -4, right: -4, width: 8, height: 8, background: col, borderRadius: '50%' }} />}
                                        </button>
                                    );
                                })}
                            </div>

                            {/* Active timeframe content */}
                            {activeTab && scans[activeTab] && (
                                <TimeframePane label={activeTab} data={scans[activeTab]} isNSE={derivedMarket === 'NSE'} />
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
