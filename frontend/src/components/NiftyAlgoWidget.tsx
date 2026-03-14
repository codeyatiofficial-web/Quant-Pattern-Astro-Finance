'use client';

import React, { useState, useEffect, useRef } from 'react';

const API = '';
const REFRESH_SEC = 60;

function Bar({ value, max, color }: { value: number; max: number; color: string }) {
    const pct = max > 0 ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;
    return (
        <div style={{ height: 5, borderRadius: 3, background: 'rgba(255,255,255,0.06)', overflow: 'hidden', marginTop: 7 }}>
            <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.6s ease' }} />
        </div>
    );
}

function Chip({ label, color, bg }: { label: string; color: string; bg: string }) {
    return (
        <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 5, background: bg, color, letterSpacing: 0.5, whiteSpace: 'nowrap' }}>
            {label}
        </span>
    );
}

// ─── ALGO 2: CORRELATION ENGINE ────────────────────────────────────────────
function Algo2CorrelationEngine() {
    const [cd, setCd] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [toggling, setToggling] = useState(false);
    const [isActive, setIsActive] = useState(false);
    const [countdown, setCountdown] = useState(60);

    const fetchStatus2 = async () => {
        try {
            const r = await fetch('/api/algo/status');
            if (r.ok) { const j = await r.json(); setIsActive(j.data?.is_active_algo2 ?? false); }
        } catch (e) { console.error(e); }
    };

    const fetch2 = async () => {
        setLoading(true);
        try {
            const r = await fetch('/api/correlation/live-prediction');
            if (r.ok) { const j = await r.json(); setCd(j); }
        } catch (e) { console.error(e); }
        finally { setLoading(false); setCountdown(60); }
    };

    const toggleAlgo2 = async () => {
        setToggling(true);
        try {
            const r = await fetch('/api/algo2/toggle', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !isActive }),
            });
            if (r.ok) { const j = await r.json(); setIsActive(j.is_active); }
        } catch (e) { console.error(e); }
        finally { setToggling(false); }
    };

    useEffect(() => {
        fetchStatus2();
        fetch2();
        const ri = setInterval(fetch2, 60000);
        const ti = setInterval(() => setCountdown(c => c > 0 ? c - 1 : 0), 1000);
        return () => { clearInterval(ri); clearInterval(ti); };
    }, []);

    const dir2    = cd?.direction ?? 'NEUTRAL';
    const d2Color = dir2 === 'BULLISH' || dir2 === 'BUY' ? '#22c55e' : dir2 === 'BEARISH' || dir2 === 'SELL' ? '#ef4444' : '#94a3b8';
    const conf    = cd?.confidence ?? 0;
    const confLabel = conf >= 70 ? 'HIGH' : conf >= 45 ? 'MEDIUM' : 'LOW';
    const confColor = conf >= 70 ? '#22c55e' : conf >= 45 ? '#f59e0b' : '#94a3b8';
    const magPts  = cd?.magnitude_points ?? 0;
    const magConf = cd?.magnitude_confidence ?? '—';
    const rrRatio = cd?.risk_reward ?? 0;
    const entry   = cd?.current_nifty ?? 0;
    const target  = cd?.target_price ?? 0;
    const sl      = cd?.stop_loss ?? 0;
    const corrs   = cd?.correlations ?? {};
    const currVals = cd?.current_values ?? {};

    const corrAssets = [
        { name: 'Nasdaq',  key: 'Nasdaq',   color: '#6366f1' },
        { name: 'S&P 500', key: 'SP500',    color: '#06b6d4' },
        { name: 'USD/INR', key: 'USD_INR',  color: '#f59e0b' },
        { name: 'Oil',     key: 'Oil',      color: '#ef4444' },
        { name: 'Gold',    key: 'Gold',     color: '#fbbf24' },
    ];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>

            {/* Divider */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 1 }}>ALGO 2</span>
                <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
            </div>

            {/* Header */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '18px 24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
                    <div>
                        <h3 style={{ fontSize: 15, fontWeight: 800, color: 'var(--text-primary)', margin: 0, letterSpacing: 0.4 }}>CORRELATION ENGINE</h3>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Rolling 90-day correlation · Nasdaq · SP500 · USD/INR · Oil · Gold → Nifty 50 projection</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontSize: 11, fontWeight: 700, padding: '4px 11px', borderRadius: 5, background: isActive ? 'rgba(34,197,94,0.12)' : 'rgba(148,163,184,0.08)', color: isActive ? '#22c55e' : '#94a3b8', border: `1px solid ${isActive ? 'rgba(34,197,94,0.25)' : 'rgba(148,163,184,0.15)'}` }}>
                            {isActive ? 'LIVE' : 'PAUSED'}
                        </span>
                        <button onClick={toggleAlgo2} disabled={toggling}
                            style={{ padding: '6px 14px', borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: toggling ? 'not-allowed' : 'pointer', background: isActive ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)', color: isActive ? '#ef4444' : '#22c55e', border: `1px solid ${isActive ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)'}` }}>
                            {toggling ? '...' : isActive ? 'Pause Algo 2' : 'Start Algo 2'}
                        </button>
                        <button onClick={fetch2} style={{ padding: '5px 12px', borderRadius: 7, fontSize: 12, cursor: 'pointer', background: 'var(--bg-secondary)', color: 'var(--text-muted)', border: '1px solid var(--border-subtle)' }}>Refresh</button>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{countdown}s</span>
                    </div>
                </div>
            </div>

            {loading ? (
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                    Computing correlations...
                </div>
            ) : (
                <>
                    {/* Direction + magnitude */}
                    <div style={{ background: 'var(--bg-card)', border: `1px solid ${d2Color}40`, borderRadius: 16, padding: '20px 24px' }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 18, flexWrap: 'wrap', gap: 12 }}>
                            <div>
                                <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 0.8, marginBottom: 5 }}>CORRELATION SIGNAL</div>
                                <div style={{ fontSize: 32, fontWeight: 900, color: d2Color, letterSpacing: 1, lineHeight: 1 }}>{dir2}</div>
                                <div style={{ fontSize: 11, color: confColor, marginTop: 5, fontWeight: 700 }}>{confLabel} CONFIDENCE ({conf.toFixed(0)}%)</div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>MAGNITUDE FORECAST</div>
                                <div style={{ fontSize: 26, fontWeight: 900, color: d2Color, lineHeight: 1 }}>{magPts} <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 400 }}>pts</span></div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>Band: {magConf} &nbsp;|&nbsp; R:R 1:{rrRatio}</div>
                            </div>
                        </div>

                        {/* Entry / Target / SL / RR */}
                        {entry > 0 && dir2 !== 'NEUTRAL' && (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: 10, marginBottom: 14 }}>
                                {[
                                    { label: 'ENTRY',       val: entry.toFixed(1),  color: 'var(--text-primary)' },
                                    { label: 'TARGET',      val: target.toFixed(1), color: '#22c55e' },
                                    { label: 'STOP LOSS',   val: sl.toFixed(1),     color: '#ef4444' },
                                    { label: 'R / R',       val: `1 : ${rrRatio}`,  color: '#f59e0b' },
                                ].map(item => (
                                    <div key={item.label} style={{ background: 'var(--bg-secondary)', borderRadius: 9, padding: '11px 12px', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                                        <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 0.4, marginBottom: 4 }}>{item.label}</div>
                                        <div style={{ fontSize: 15, fontWeight: 800, color: item.color }}>{item.val}</div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Confidence bar */}
                        <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '10px 14px', border: '1px solid var(--border-subtle)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 10, color: 'var(--text-muted)' }}>
                                <span>SIGNAL CONFIDENCE</span>
                                <span style={{ color: confColor, fontWeight: 700 }}>{conf.toFixed(0)}%</span>
                            </div>
                            <Bar value={conf} max={100} color={confColor} />
                        </div>
                    </div>

                    {/* Per-asset correlation table */}
                    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '20px 24px' }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8, marginBottom: 12 }}>ASSET CORRELATIONS (90-DAY ROLLING)</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            {corrAssets.map(asset => {
                                const c = corrs[asset.key] ?? 0;
                                const v = currVals[asset.name] ?? currVals[asset.key] ?? 0;
                                const cAbs = Math.abs(c);
                                const cColor = cAbs > 0.6 ? '#22c55e' : cAbs > 0.3 ? '#f59e0b' : '#94a3b8';
                                return (
                                    <div key={asset.key} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <div style={{ width: 76, fontSize: 11, fontWeight: 700, color: asset.color }}>{asset.name}</div>
                                        <div style={{ flex: 1, height: 5, borderRadius: 3, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                                            <div style={{ height: '100%', width: `${Math.min(100, cAbs * 100)}%`, background: cColor, borderRadius: 3, transition: 'width 0.5s ease' }} />
                                        </div>
                                        <div style={{ width: 44, fontSize: 12, fontWeight: 700, color: cColor, textAlign: 'right' }}>{c > 0 ? '+' : ''}{c.toFixed(2)}</div>
                                        <div style={{ width: 72, fontSize: 11, color: 'var(--text-muted)', textAlign: 'right' }}>{v > 0 ? Number(v).toLocaleString() : '—'}</div>
                                    </div>
                                );
                            })}
                        </div>
                        <div style={{ marginTop: 10, fontSize: 10, color: 'var(--text-muted)' }}>
                            Score = Σ (today return × 90-day correlation coefficient) &nbsp;|&nbsp; Range: −1 inverse to +1 direct
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

// ─── ALGO 3: NIFTY OPTIONS ENGINE ─────────────────────────────────────────────
function Algo3OptionsEngine() {
    const [sig3, setSig3]         = useState<any>(null);
    const [loading, setLoading]   = useState(true);
    const [toggling, setToggling] = useState(false);
    const [isActive, setIsActive] = useState(false);
    const [countdown, setCountdown] = useState(60);

    const fetchStatus3 = async () => {
        try {
            const r = await fetch('/api/algo/status');
            if (r.ok) { const j = await r.json(); setIsActive(j.data?.is_active_algo3 ?? false); }
        } catch (e) { console.error(e); }
    };

    const fetch3 = async () => {
        setLoading(true);
        try {
            const r = await fetch('/api/algo3/live-signal');
            if (r.ok) { const j = await r.json(); setSig3(j.data); }
        } catch (e) { console.error(e); }
        finally { setLoading(false); setCountdown(60); }
    };

    const toggle3 = async () => {
        setToggling(true);
        try {
            const r = await fetch('/api/algo3/toggle', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !isActive }),
            });
            if (r.ok) { const j = await r.json(); setIsActive(j.is_active); }
        } catch (e) { console.error(e); }
        finally { setToggling(false); }
    };

    useEffect(() => {
        fetchStatus3();
        fetch3();
        const ri = setInterval(fetch3, 60000);
        const ti = setInterval(() => setCountdown(c => c > 0 ? c - 1 : 0), 1000);
        return () => { clearInterval(ri); clearInterval(ti); };
    }, []);

    // Derived colours
    const dir3      = sig3?.direction ?? 'WAIT';
    const dirColor3 = dir3 === 'BUY' ? '#4ade80' : dir3 === 'SELL' ? '#f87171' : '#94a3b8';
    const total3    = sig3?.total_score ?? 0;
    const confColor3 = sig3?.confidence === 'HIGH' ? '#4ade80' : sig3?.confidence === 'MEDIUM' ? '#fb923c' : '#94a3b8';
    const globalScore3 = sig3?.global_bias_score ?? 0;
    const biasColor3   = globalScore3 > 0 ? '#4ade80' : globalScore3 < 0 ? '#f87171' : '#94a3b8';

    const steps3 = [
        { label: 'TREND ALIGNMENT',    sub: 'Supertrend 15m+1h · EMA20>50', key: 'step1_score', max: 25, color: '#6366f1' },
        { label: 'MOMENTUM + VOLUME',  sub: 'RSI14 · MACD(12,26,9) · Vol ratio', key: 'step2_score', max: 25, color: '#06b6d4' },
        { label: 'OPTIONS CHAIN',      sub: 'PCR · MaxPain · ATM OI · IV rank', key: 'step3_score', max: 25, color: '#f59e0b' },
        { label: 'LEVELS + TIME',      sub: 'Trade windows · Key level proximity', key: 'step4_score', max: 25, color: '#a78bfa' },
    ];

    const safetyChecks: Array<{name: string; ok: boolean; reason: string}> = sig3?.safety_checks ?? [];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>

            {/* Divider */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 1 }}>ALGO 3</span>
                <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
            </div>

            {/* Header */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '18px 24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
                    <div>
                        <h3 style={{ fontSize: 15, fontWeight: 800, color: 'var(--text-primary)', margin: 0, letterSpacing: 0.4 }}>NIFTY OPTIONS ENGINE</h3>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                            4-Step validation · 110 pts · Real MaxPain · PCR · IV Rank · ATM CE/PE
                        </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontSize: 11, fontWeight: 700, padding: '4px 11px', borderRadius: 5, background: isActive ? 'rgba(74,222,128,0.10)' : 'rgba(148,163,184,0.08)', color: isActive ? '#4ade80' : '#94a3b8', border: `1px solid ${isActive ? 'rgba(74,222,128,0.22)' : 'rgba(148,163,184,0.15)'}` }}>
                            {isActive ? 'LIVE' : 'PAUSED'}
                        </span>
                        <button onClick={toggle3} disabled={toggling}
                            style={{ padding: '6px 14px', borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: toggling ? 'not-allowed' : 'pointer', background: isActive ? 'rgba(248,113,113,0.10)' : 'rgba(74,222,128,0.10)', color: isActive ? '#f87171' : '#4ade80', border: `1px solid ${isActive ? 'rgba(248,113,113,0.20)' : 'rgba(74,222,128,0.20)'}` }}>
                            {toggling ? '...' : isActive ? 'Pause Algo 3' : 'Start Algo 3'}
                        </button>
                        <button onClick={fetch3}
                            style={{ padding: '5px 12px', borderRadius: 7, fontSize: 12, cursor: 'pointer', background: 'var(--bg-secondary)', color: 'var(--text-muted)', border: '1px solid var(--border-subtle)' }}>
                            Refresh
                        </button>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{countdown}s</span>
                    </div>
                </div>
            </div>

            {loading ? (
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                    Running 4-step analysis...
                </div>
            ) : (
                <>
                    {/* Signal Card */}
                    <div style={{ background: 'var(--bg-card)', border: `1px solid ${dirColor3}40`, borderRadius: 16, padding: '22px 24px' }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 14, marginBottom: 18 }}>
                            <div>
                                <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 0.8, marginBottom: 5 }}>ALGO 3 SIGNAL</div>
                                <div style={{ fontSize: 34, fontWeight: 900, color: dirColor3, letterSpacing: 1, lineHeight: 1 }}>{dir3}</div>
                                <div style={{ fontSize: 11, color: confColor3, marginTop: 5, fontWeight: 700 }}>
                                    {sig3?.signal_strength ?? 'NO SIGNAL'} — {sig3?.confidence ?? 'LOW'} CONFIDENCE
                                </div>
                                {sig3?.in_trade_window && (
                                    <div style={{ fontSize: 10, color: '#4ade80', marginTop: 4, fontWeight: 600 }}>IN VALID TRADE WINDOW</div>
                                )}
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: 30, fontWeight: 900, color: 'var(--text-primary)', lineHeight: 1 }}>
                                    {total3}
                                    <span style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 400 }}>/110</span>
                                </div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>Total Score</div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                                    Global Bonus: <strong style={{ color: biasColor3 }}>+{sig3?.global_bonus ?? 0}</strong>
                                </div>
                            </div>
                        </div>

                        {/* Total score bar */}
                        <Bar value={total3} max={110} color={dirColor3} />
                        <div style={{ display: 'flex', gap: 16, marginTop: 7, fontSize: 10 }}>
                            <span style={{ color: '#94a3b8' }}>0–54 WAIT</span>
                            <span style={{ color: '#fb923c' }}>55–69 WEAK</span>
                            <span style={{ color: '#06b6d4' }}>70–84 GOOD</span>
                            <span style={{ color: '#4ade80' }}>85–110 STRONG</span>
                        </div>
                    </div>

                    {/* Trade Details — Entry / SL / T1 / T2 */}
                    {dir3 !== 'WAIT' && (sig3?.entry_premium ?? 0) > 0 && (
                        <div style={{ background: 'var(--bg-card)', border: `1px solid ${dirColor3}35`, borderRadius: 16, padding: '20px 24px' }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8, marginBottom: 14 }}>TRADE SETUP</div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10, marginBottom: 14 }}>
                                {[
                                    { label: `ATM ${sig3?.option_type ?? ''} STRIKE`, val: sig3?.atm_strike?.toFixed(0) ?? '—', color: 'var(--text-primary)' },
                                    { label: 'ENTRY PREMIUM',  val: `${sig3?.entry_premium ?? '—'}`,  color: 'var(--text-primary)' },
                                    { label: 'SL (40% DROP)',  val: `${sig3?.sl_premium ?? '—'}`,      color: '#f87171' },
                                    { label: 'TARGET 1 (2x)', val: `${sig3?.t1_premium ?? '—'}`,      color: '#4ade80' },
                                    { label: 'TARGET 2 (3x)', val: `${sig3?.t2_premium ?? '—'}`,      color: '#4ade80' },
                                    { label: 'LOT SIZE',      val: `${sig3?.lot_size ?? 50} units`,   color: 'var(--text-muted)' },
                                ].map(item => (
                                    <div key={item.label} style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '12px 14px', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                                        <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 0.4, marginBottom: 4 }}>{item.label}</div>
                                        <div style={{ fontSize: 15, fontWeight: 800, color: item.color }}>{item.val}</div>
                                    </div>
                                ))}
                            </div>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                                Force-exit at 3:10 PM · Max 2 lots · ATM strike rounded to nearest 50
                            </div>
                        </div>
                    )}

                    {/* Step Breakdown */}
                    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '20px 24px' }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8, marginBottom: 14 }}>4-STEP SCORE BREAKDOWN</div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
                            {steps3.map(step => {
                                const sc = sig3?.[step.key] ?? 0;
                                const scColor = sc >= step.max * 0.7 ? '#4ade80' : sc >= step.max * 0.4 ? '#fb923c' : '#94a3b8';
                                return (
                                    <div key={step.key} style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '14px 16px', border: '1px solid var(--border-subtle)' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <div style={{ fontSize: 11, fontWeight: 700, color: step.color, letterSpacing: 0.4 }}>{step.label}</div>
                                            <div style={{ fontSize: 14, fontWeight: 800, color: scColor }}>{sc}/{step.max}</div>
                                        </div>
                                        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>{step.sub}</div>
                                        <Bar value={sc} max={step.max} color={step.color} />
                                    </div>
                                );
                            })}
                        </div>

                        {/* Options chain meta */}
                        {(sig3?.pcr ?? 0) > 0 && (
                            <div style={{ marginTop: 12, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                                {[
                                    { label: 'PCR',       val: (sig3?.pcr ?? 0).toFixed(2) },
                                    { label: 'MAX PAIN',  val: sig3?.max_pain?.toFixed(0) ?? '—' },
                                    { label: 'IV RANK',   val: `${sig3?.iv_rank?.toFixed(0) ?? 50}%` },
                                    { label: 'CALL WALL', val: sig3?.call_wall?.toFixed(0) ?? '—' },
                                    { label: 'PUT WALL',  val: sig3?.put_wall?.toFixed(0) ?? '—' },
                                    { label: 'RSI',       val: sig3?.rsi?.toFixed(1) ?? '—' },
                                ].map(item => (
                                    <div key={item.label} style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '8px 14px', border: '1px solid var(--border-subtle)', flex: '1 0 80px', textAlign: 'center' }}>
                                        <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 0.4 }}>{item.label}</div>
                                        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>{item.val}</div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Global Bias */}
                    <div style={{ background: 'var(--bg-card)', border: `1px solid ${biasColor3}30`, borderRadius: 16, padding: '18px 24px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8 }}>GLOBAL MARKET BIAS</div>
                            <div style={{ fontSize: 14, fontWeight: 800, color: biasColor3 }}>{globalScore3 >= 0 ? '+' : ''}{globalScore3}/30</div>
                        </div>
                        <div style={{ fontSize: 13, fontWeight: 800, color: biasColor3, marginBottom: 6 }}>
                            {globalScore3 >= 15 ? 'STRONG BULLISH' : globalScore3 >= 5 ? 'MILD BULLISH' : globalScore3 <= -15 ? 'STRONG BEARISH' : globalScore3 <= -5 ? 'MILD BEARISH' : 'NEUTRAL'}
                        </div>
                        <Bar value={Math.abs(globalScore3)} max={30} color={biasColor3} />
                        {sig3?.gift_nifty_gap && (
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
                                Gift Nifty: {sig3.gift_nifty_gap}
                            </div>
                        )}
                    </div>

                    {/* Safety System */}
                    {safetyChecks.length > 0 && (
                        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '20px 24px' }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8, marginBottom: 12 }}>
                                SAFETY SYSTEM — {sig3?.safety_clear ? 'ALL CLEAR' : 'BLOCKED'}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {safetyChecks.map((check: {name: string; ok: boolean; reason: string}, i: number) => (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                        <div style={{ width: 7, height: 7, borderRadius: '50%', background: check.ok ? '#4ade80' : '#f87171', flexShrink: 0 }} />
                                        <div style={{ fontSize: 12, fontWeight: 600, color: check.ok ? 'var(--text-primary)' : '#f87171', flex: 1 }}>{check.name}</div>
                                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{check.reason}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Pre-Market Report */}
                    {sig3?.pre_market_report && (
                        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '20px 24px' }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 10, letterSpacing: 0.8 }}>
                                ALGO 3 PRE-MARKET REPORT
                            </div>
                            <div style={{ fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.85, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                                {sig3.pre_market_report}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

export default function NiftyAlgoWidget() {
    const [status, setStatus] = useState<any>(null);
    const [sig, setSig] = useState<any>(null);
    const [statusLoading, setStatusLoading] = useState(true);
    const [sigLoading, setSigLoading] = useState(true);
    const [toggling, setToggling] = useState(false);
    const [countdown, setCountdown] = useState(REFRESH_SEC);
    const timerRef = useRef<any>(null);

    const fetchStatus = async () => {
        try {
            const r = await fetch(`${API}/api/algo/status`);
            if (r.ok) { const j = await r.json(); setStatus(j.data); }
        } catch (e) { console.error(e); }
        finally { setStatusLoading(false); }
    };

    const fetchSignal = async () => {
        setSigLoading(true);
        try {
            const r = await fetch(`${API}/api/algo/live-signal`);
            if (r.ok) { const j = await r.json(); setSig(j.data); }
        } catch (e) { console.error(e); }
        finally { setSigLoading(false); setCountdown(REFRESH_SEC); }
    };

    const toggleAlgo = async () => {
        if (!status) return;
        setToggling(true);
        try {
            const r = await fetch(`${API}/api/algo/toggle`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !status.is_active }),
            });
            if (r.ok) { const j = await r.json(); setStatus((p: any) => ({ ...p, is_active: j.is_active })); }
        } catch (e) { console.error(e); }
        finally { setToggling(false); }
    };

    useEffect(() => {
        fetchStatus();
        fetchSignal();
        const si = setInterval(fetchStatus, 30000);
        const li = setInterval(fetchSignal, REFRESH_SEC * 1000);
        timerRef.current = setInterval(() => setCountdown(c => (c > 0 ? c - 1 : 0)), 1000);
        return () => { clearInterval(si); clearInterval(li); clearInterval(timerRef.current); };
    }, []);

    // ── derived colours ──────────────────────────────────────────────────────────
    const dir = sig?.direction ?? 'WAIT';
    const dirColor = dir === 'BUY' ? '#22c55e' : dir === 'SELL' ? '#ef4444' : '#94a3b8';
    const dirBg    = dir === 'BUY' ? 'rgba(34,197,94,0.12)' : dir === 'SELL' ? 'rgba(239,68,68,0.12)' : 'rgba(148,163,184,0.08)';
    const total    = sig?.total_score ?? 0;
    const confColor = sig?.confidence === 'HIGH' ? '#22c55e' : sig?.confidence === 'MEDIUM' ? '#f59e0b' : '#94a3b8';
    const globalScore = status?.global_bias ?? sig?.global_bias_score ?? 0;
    const biasColor   = globalScore > 0 ? '#22c55e' : globalScore < 0 ? '#ef4444' : '#f59e0b';

    const components = [
        { label: 'CORRELATION',   sub: 'Nasdaq · SP500 · USD/INR · Oil · Gold',  key: 'comp1_correlation',  max: 30, color: '#6366f1' },
        { label: 'GLOBAL BIAS',   sub: 'US · Asia · Europe · Commodities · VIX', key: 'comp2_global_bias',  max: 25, color: '#f59e0b' },
        { label: 'TECHNICAL',     sub: 'RSI 14 · MACD 12/26/9 · VWAP',          key: 'comp3_technical',    max: 25, color: '#06b6d4' },
        { label: 'PRICE LEVEL',   sub: 'ATR(14) · Round levels · Time window',   key: 'comp4_price_level',  max: 20, color: '#a78bfa' },
    ];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* ── HEADER ──────────────────────────────────────────────────────────── */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '20px 24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                    <div>
                        <h2 style={{ fontSize: 17, fontWeight: 800, color: 'var(--text-primary)', margin: 0, letterSpacing: 0.4 }}>
                            ALGO TRADING ENGINE
                        </h2>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>
                            4-Component composite scoring — Nifty 50 Options
                        </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontSize: 11, fontWeight: 700, padding: '4px 11px', borderRadius: 5, background: status?.is_active ? 'rgba(34,197,94,0.12)' : 'rgba(148,163,184,0.08)', color: status?.is_active ? '#22c55e' : '#94a3b8', border: `1px solid ${status?.is_active ? 'rgba(34,197,94,0.25)' : 'rgba(148,163,184,0.15)'}` }}>
                            {statusLoading ? '...' : status?.is_active ? 'LIVE' : 'PAUSED'}
                        </span>
                        <button onClick={toggleAlgo} disabled={toggling || statusLoading}
                            style={{ padding: '6px 14px', borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: 'pointer', background: status?.is_active ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)', color: status?.is_active ? '#ef4444' : '#22c55e', border: `1px solid ${status?.is_active ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)'}` }}>
                            {toggling ? '...' : status?.is_active ? 'Pause' : 'Start Algo'}
                        </button>
                        <button onClick={fetchSignal}
                            style={{ padding: '6px 12px', borderRadius: 7, fontSize: 12, cursor: 'pointer', background: 'var(--bg-secondary)', color: 'var(--text-muted)', border: '1px solid var(--border-subtle)' }}>
                            Refresh
                        </button>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)', minWidth: 52 }}>
                            {countdown}s
                        </span>
                    </div>
                </div>
            </div>

            {/* ── LIVE SIGNAL CARD ─────────────────────────────────────────────────── */}
            <div style={{ background: 'var(--bg-card)', border: `1px solid ${dirColor}40`, borderRadius: 16, padding: '24px' }}>
                {sigLoading ? (
                    <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '28px 0' }}>
                        Analyzing market conditions...
                    </div>
                ) : (
                    <>
                        {/* Direction + score */}
                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 14 }}>
                            <div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', letterSpacing: 0.8, marginBottom: 6 }}>ACTIVE SIGNAL</div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
                                    <span style={{ fontSize: 36, fontWeight: 900, color: dirColor, letterSpacing: 1, lineHeight: 1 }}>{dir}</span>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                                        <Chip label={sig?.signal_strength ?? 'WAIT'} color={dirColor} bg={dirBg} />
                                        <Chip label={`${sig?.confidence ?? 'LOW'} CONFIDENCE`} color={confColor} bg={`${confColor}18`} />
                                    </div>
                                </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: 30, fontWeight: 900, color: 'var(--text-primary)', lineHeight: 1 }}>
                                    {total}
                                    <span style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 400 }}>/100</span>
                                </div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>Composite Score</div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                                    ATR(14): <strong style={{ color: 'var(--text-primary)' }}>{sig?.atr ?? '—'} pts</strong>
                                </div>
                            </div>
                        </div>

                        {/* Entry / Target / SL / R:R */}
                        {dir !== 'WAIT' && (sig?.entry_price ?? 0) > 0 && (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: 10, marginBottom: 16 }}>
                                {[
                                    { label: 'ENTRY',        val: sig.entry_price?.toFixed(1),  color: 'var(--text-primary)' },
                                    { label: 'TARGET',       val: sig.target_price?.toFixed(1), color: '#22c55e' },
                                    { label: 'STOP LOSS',    val: sig.stop_loss?.toFixed(1),    color: '#ef4444' },
                                    { label: 'RISK / REWARD', val: `1 : ${sig.rr_ratio}`,       color: '#f59e0b' },
                                ].map(item => (
                                    <div key={item.label} style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '12px 14px', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                                        <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 0.5, marginBottom: 4 }}>{item.label}</div>
                                        <div style={{ fontSize: 16, fontWeight: 800, color: item.color }}>{item.val}</div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Market context pills */}
                        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                            {[
                                { label: 'RSI (14)',      val: sig?.rsi ?? '—' },
                                { label: 'MACD HIST',     val: sig?.macd_direction ?? '—' },
                                { label: 'GLOBAL BIAS',   val: `${globalScore > 0 ? '+' : ''}${globalScore} / 30` },
                                { label: 'CORR SCORE',    val: sig?.corr_score_raw ?? '—' },
                                { label: 'ACTION',        val: sig?.action ?? '—' },
                            ].map(item => (
                                <div key={item.label} style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '8px 14px', border: '1px solid var(--border-subtle)', flex: '1 0 90px', textAlign: 'center' }}>
                                    <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 0.4 }}>{item.label}</div>
                                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>{String(item.val)}</div>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* ── SCORE BREAKDOWN ─────────────────────────────────────────────────── */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '20px 24px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8, marginBottom: 14 }}>SCORE BREAKDOWN</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
                    {components.map(comp => {
                        const sc = sig?.[comp.key] ?? 0;
                        const scColor = sc >= comp.max * 0.7 ? '#22c55e' : sc >= comp.max * 0.4 ? '#f59e0b' : '#94a3b8';
                        return (
                            <div key={comp.key} style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '14px 16px', border: '1px solid var(--border-subtle)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div style={{ fontSize: 11, fontWeight: 700, color: comp.color, letterSpacing: 0.4 }}>{comp.label}</div>
                                    <div style={{ fontSize: 14, fontWeight: 800, color: scColor }}>{sc} / {comp.max}</div>
                                </div>
                                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>{comp.sub}</div>
                                <Bar value={sc} max={comp.max} color={comp.color} />
                            </div>
                        );
                    })}
                </div>

                {/* Total composite bar */}
                <div style={{ marginTop: 14, background: 'var(--bg-secondary)', borderRadius: 10, padding: '12px 16px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.6 }}>TOTAL COMPOSITE</span>
                        <span style={{ fontSize: 14, fontWeight: 900, color: dirColor }}>{total} / 100</span>
                    </div>
                    <Bar value={total} max={100} color={dirColor} />
                    <div style={{ display: 'flex', gap: 20, marginTop: 8, fontSize: 10 }}>
                        <span style={{ color: '#94a3b8' }}>0–39  WAIT</span>
                        <span style={{ color: '#f59e0b' }}>40–54  WEAK</span>
                        <span style={{ color: '#06b6d4' }}>55–74  MODERATE</span>
                        <span style={{ color: '#22c55e' }}>75–100  STRONG</span>
                    </div>
                </div>
            </div>

            {/* ── GLOBAL BIAS BAR ─────────────────────────────────────────────────── */}
            <div style={{ background: 'var(--bg-card)', border: `1px solid ${biasColor}30`, borderRadius: 16, padding: '18px 24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8 }}>GLOBAL MARKET BIAS (±30)</div>
                    <div style={{ fontSize: 14, fontWeight: 800, color: biasColor }}>{globalScore > 0 ? '+' : ''}{globalScore} / 30</div>
                </div>
                <div style={{ fontSize: 14, fontWeight: 800, color: biasColor, marginBottom: 6 }}>
                    {globalScore >= 15 ? 'STRONG BULLISH' : globalScore >= 5 ? 'MILD BULLISH' : globalScore <= -15 ? 'STRONG BEARISH' : globalScore <= -5 ? 'MILD BEARISH' : 'NEUTRAL'}
                </div>
                <Bar value={Math.abs(globalScore)} max={30} color={biasColor} />
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                    US Markets (10) · Asian Markets (8) · European (6) · Commodities/FX (6) · VIX (0/±4)
                </div>
            </div>

            {/* ── PRE-MARKET REPORT ───────────────────────────────────────────────── */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '20px 24px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 10, letterSpacing: 0.8 }}>
                    PRE-MARKET GLOBAL REPORT
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                    {statusLoading ? 'Loading...' : (status?.pre_market_report ?? 'Pre-market report updates daily at 7:00 AM IST.')}
                </div>
            </div>

            {/* ── ALGO 2 ──────────────────────────────────────────────────────────── */}
            <Algo2CorrelationEngine />

            {/* ── ALGO 3 ──────────────────────────────────────────────────────────── */}
            <Algo3OptionsEngine />

        </div>
    );
}


