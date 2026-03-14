'use client';

import React, { useState, useEffect } from 'react';

const API = '';

function ScoreBar({ score, max, color }: { score: number; max: number; color: string }) {
    const pct = max === 0 ? 0 : Math.max(0, Math.min(100, (Math.abs(score) / max) * 100));
    return (
        <div style={{ height: 6, borderRadius: 4, background: 'var(--border-subtle)', overflow: 'hidden', marginTop: 8 }}>
            <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 4, transition: 'width 0.5s ease' }} />
        </div>
    );
}

export default function NiftyAlgoWidget() {
    const [algoData, setAlgoData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [toggling, setToggling] = useState(false);

    const fetchStatus = async () => {
        try {
            const res = await fetch(`${API}/api/algo/status`);
            if (res.ok) {
                const json = await res.json();
                setAlgoData(json.data);
            }
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const toggleAlgo = async () => {
        if (!algoData) return;
        setToggling(true);
        try {
            const res = await fetch(`${API}/api/algo/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !algoData.is_active }),
            });
            if (res.ok) {
                const json = await res.json();
                setAlgoData((prev: any) => ({ ...prev, is_active: json.is_active }));
            }
        } catch (e) { console.error(e); }
        finally { setToggling(false); }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const bias = algoData?.global_bias ?? 0;
    const biasLabel = bias >= 15 ? 'STRONG BULLISH' : bias >= 5 ? 'MILD BULLISH' : bias <= -15 ? 'STRONG BEARISH' : bias <= -5 ? 'MILD BEARISH' : 'NEUTRAL';
    const biasColor = bias > 0 ? '#22c55e' : bias < 0 ? '#ef4444' : '#f59e0b';
    const signal = algoData?.latest_signal;

    const stages = [
        { label: 'TREND ALIGNMENT', key: 'step1_score', desc: 'Supertrend 15m + 1h, EMA 20/50', max: 25 },
        { label: 'MOMENTUM + VOLUME', key: 'step2_score', desc: 'RSI 14, MACD, Volume ratio', max: 25 },
        { label: 'OPTIONS CHAIN', key: 'step3_score', desc: 'PCR, OI concentration, premium', max: 25 },
        { label: 'KEY LEVELS + TIME', key: 'step4_score', desc: 'Support/Resistance, time window', max: 25 },
    ];

    const dirColor = signal?.direction === 'BUY' ? '#22c55e' : signal?.direction === 'SELL' ? '#ef4444' : '#94a3b8';
    const totalScore = signal?.total_score ?? 0;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Header */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
                    <div>
                        <h2 style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', margin: 0, letterSpacing: 0.5 }}>ALGO TRADING</h2>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>Automated execution engine — Nifty 50 Options</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontSize: 12, fontWeight: 700, padding: '4px 12px', borderRadius: 6, background: algoData?.is_active ? 'rgba(34,197,94,0.12)' : 'rgba(148,163,184,0.1)', color: algoData?.is_active ? '#22c55e' : '#94a3b8', border: `1px solid ${algoData?.is_active ? 'rgba(34,197,94,0.25)' : 'rgba(148,163,184,0.2)'}` }}>
                            {loading ? 'Loading...' : algoData?.is_active ? 'RUNNING' : 'PAUSED'}
                        </span>
                        <button onClick={toggleAlgo} disabled={toggling || loading}
                            style={{ padding: '7px 16px', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: toggling || loading ? 'not-allowed' : 'pointer', background: algoData?.is_active ? 'rgba(239,68,68,0.12)' : 'rgba(34,197,94,0.12)', color: algoData?.is_active ? '#ef4444' : '#22c55e', border: `1px solid ${algoData?.is_active ? 'rgba(239,68,68,0.25)' : 'rgba(34,197,94,0.25)'}` }}>
                            {toggling ? 'Updating...' : algoData?.is_active ? 'Pause Algo' : 'Start Algo'}
                        </button>
                        <button onClick={fetchStatus}
                            style={{ padding: '7px 13px', borderRadius: 8, fontSize: 12, cursor: 'pointer', background: 'var(--bg-secondary)', color: 'var(--text-muted)', border: '1px solid var(--border-subtle)' }}>
                            Refresh
                        </button>
                    </div>
                </div>

                {/* Global Bias — out of 30 */}
                <div style={{ background: 'var(--bg-secondary)', borderRadius: 12, padding: '16px 20px', border: `1px solid ${biasColor}33`, marginBottom: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8 }}>GLOBAL MARKET BIAS</div>
                        <div style={{ fontSize: 13, fontWeight: 800, color: biasColor }}>{bias > 0 ? '+' : ''}{bias} / 30</div>
                    </div>
                    <div style={{ fontSize: 18, fontWeight: 900, color: biasColor, marginBottom: 6 }}>{biasLabel}</div>
                    <ScoreBar score={bias} max={30} color={biasColor} />
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                        US Markets + Asian Markets + European Markets + Commodities + VIX
                    </div>
                </div>

                {/* 4 Stages */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 16 }}>
                    {stages.map((stage, i) => {
                        const s = signal?.[stage.key] ?? 0;
                        const stageColor = s >= 20 ? '#22c55e' : s >= 12 ? '#f59e0b' : s > 0 ? '#94a3b8' : '#ef4444';
                        return (
                            <div key={stage.key} style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '14px 16px', border: '1px solid var(--border-subtle)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                                    <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.6 }}>STAGE {i + 1}</div>
                                    <div style={{ fontSize: 13, fontWeight: 800, color: stageColor }}>{s} / 25</div>
                                </div>
                                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>{stage.label}</div>
                                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{stage.desc}</div>
                                <ScoreBar score={s} max={25} color={stageColor} />
                            </div>
                        );
                    })}
                </div>

                {/* Total Score */}
                {signal && (
                    <div style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '14px 20px', border: `1px solid ${dirColor}33`, marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                        <div>
                            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: 0.8, marginBottom: 2 }}>TOTAL SCORE</div>
                            <div style={{ fontSize: 22, fontWeight: 900, color: dirColor }}>{totalScore} <span style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 400 }}>/ 110</span></div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: 16, fontWeight: 800, color: dirColor }}>{signal.direction}</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{signal.signal_strength}</div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Size: {signal.trade_size} &nbsp;|&nbsp; {signal.action}</div>
                        </div>
                    </div>
                )}

                {/* Pre-market Report */}
                <div style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '14px 16px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8, letterSpacing: 0.8 }}>PRE-MARKET REPORT</div>
                    <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                        {loading ? 'Loading...' : (algoData?.pre_market_report ?? 'Not generated yet.')}
                    </div>
                </div>
            </div>
        </div>
    );
}
