'use client';

import React, { useState, useEffect } from 'react';

const API = '';

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
    const biasLabel = bias > 0 ? 'BULLISH' : bias < 0 ? 'BEARISH' : 'NEUTRAL';
    const biasColor = bias > 0 ? '#22c55e' : bias < 0 ? '#ef4444' : '#f59e0b';
    const signal = algoData?.latest_signal;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Status Panel */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16, padding: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                    <div>
                        <h2 style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', margin: 0, letterSpacing: 0.5 }}>ALGO TRADING</h2>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>Automated execution engine — Nifty 50 Options</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 6, background: algoData?.is_active ? 'rgba(34,197,94,0.12)' : 'rgba(148,163,184,0.1)', color: algoData?.is_active ? '#22c55e' : '#94a3b8', border: `1px solid ${algoData?.is_active ? 'rgba(34,197,94,0.25)' : 'rgba(148,163,184,0.2)'}` }}>
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

                {/* KPI Row */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 20 }}>
                    <div style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '14px 16px', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: 0.6 }}>GLOBAL BIAS</div>
                        <div style={{ fontSize: 20, fontWeight: 900, color: biasColor }}>{biasLabel}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Score: {bias}</div>
                    </div>
                    <div style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '14px 16px', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: 0.6 }}>EXECUTION</div>
                        <div style={{ fontSize: 15, fontWeight: 700, color: algoData?.is_active ? '#22c55e' : '#94a3b8' }}>
                            {loading ? '—' : algoData?.is_active ? 'Live Orders Active' : 'Orders Paused'}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Nifty 50 Options</div>
                    </div>
                    <div style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '14px 16px', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: 0.6 }}>LATEST SIGNAL</div>
                        <div style={{ fontSize: 15, fontWeight: 700, color: signal?.direction === 'BUY' ? '#22c55e' : signal?.direction === 'SELL' ? '#ef4444' : '#94a3b8' }}>
                            {signal ? signal.direction : 'No signal yet'}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                            {signal?.timestamp ? new Date(signal.timestamp).toLocaleTimeString() : '—'}
                        </div>
                    </div>
                </div>

                {/* Pre-market report */}
                <div style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: '14px 16px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8, letterSpacing: 0.8 }}>PRE-MARKET REPORT</div>
                    <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                        {loading ? 'Loading...' : (algoData?.pre_market_report ?? 'Not generated yet.')}
                    </div>
                </div>
            </div>

            {/* Latest Signal Detail */}
            {signal && (
                <div style={{ background: 'var(--bg-card)', border: `1px solid ${signal.direction === 'BUY' ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`, borderRadius: 16, padding: '20px 24px' }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 14, letterSpacing: 0.8 }}>LATEST SIGNAL DETAIL</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
                        {Object.entries(signal).map(([k, v]: any) => (
                            <div key={k} style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '10px 14px', border: '1px solid var(--border-subtle)' }}>
                                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 3, textTransform: 'uppercase', letterSpacing: 0.6 }}>{k.replace(/_/g, ' ')}</div>
                                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{String(v)}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
