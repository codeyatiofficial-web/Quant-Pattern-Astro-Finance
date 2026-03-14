'use client';

import React, { useState, useEffect } from 'react';

interface AlgoState {
    global_bias: number;
    pre_market_report: string;
    latest_signal: any;
    is_active: boolean;
}

export default function NiftyAlgoWidget() {
    const [algoState, setAlgoState] = useState<AlgoState | null>(null);
    const [loading, setLoading] = useState(true);

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/algo/status`);
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.success) {
                        setAlgoState(data.data);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch algo status", error);
            } finally {
                setLoading(false);
            }
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, 15000); // 15 sec refresh
        return () => clearInterval(interval);
    }, [API_BASE]);

    const handleToggle = async (checked: boolean) => {
        try {
            // Optimistic update
            setAlgoState(prev => prev ? { ...prev, is_active: checked } : null);
            
            await fetch(`${API_BASE}/api/algo/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: checked })
            });
        } catch (error) {
            console.error("Failed to toggle algo execution", error);
            // Revert
            setAlgoState(prev => prev ? { ...prev, is_active: !checked } : null);
        }
    };

    if (loading && !algoState) {
        return (
            <div className="glass-card" style={{ padding: 24, textAlign: 'center' }}>
                <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--text-primary)' }}>Loading Nifty Options Algo...</div>
            </div>
        );
    }

    const isActive = algoState?.is_active || false;
    const globalBias = algoState?.global_bias || 0;
    
    // Fallback if latest_signal is missing
    const signal = algoState?.latest_signal || {
        direction: "WAIT",
        total_score: 0,
        signal_strength: "NO SIGNAL",
        step1_score: 0,
        step2_score: 0,
        step3_score: 0,
        step4_score: 0
    };

    return (
        <div className="glass-card" style={{ padding: 24, display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 14 }}>
                <div>
                    <h2 style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
                        Nifty Options Algo
                    </h2>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0 }}>Autonomous 4-Step Validation System</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: isActive ? '#4ade80' : 'var(--text-muted)' }}>
                        {isActive ? 'LIVE EXECUTION ON' : 'EXECUTION PAUSED'}
                    </span>
                    <button 
                        onClick={() => handleToggle(!isActive)}
                        style={{
                            padding: '6px 16px', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer', transition: 'all 0.2s',
                            background: isActive ? 'rgba(239, 68, 68, 0.15)' : 'rgba(74, 222, 128, 0.15)',
                            color: isActive ? '#f87171' : '#4ade80',
                            border: `1px solid ${isActive ? 'rgba(239, 68, 68, 0.3)' : 'rgba(74, 222, 128, 0.3)'}`
                        }}
                    >
                        {isActive ? 'TURN OFF' : 'TURN ON'}
                    </button>
                </div>
            </div>

            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
                
                {/* 1. Global Bias Section */}
                <div style={{ background: 'rgba(0,0,0,0.15)', borderRadius: 12, padding: 16, border: '1px solid rgba(255,255,255,0.05)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8 }}>Pre-Market Global Bias</span>
                        <span style={{ 
                            padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 700,
                            background: globalBias > 0 ? 'rgba(74,222,128,0.15)' : globalBias < 0 ? 'rgba(248,113,113,0.15)' : 'rgba(245,158,11,0.15)',
                            color: globalBias > 0 ? '#4ade80' : globalBias < 0 ? '#f87171' : '#f59e0b',
                            border: `1px solid ${globalBias > 0 ? 'rgba(74,222,128,0.3)' : globalBias < 0 ? 'rgba(248,113,113,0.3)' : 'rgba(245,158,11,0.3)'}`
                        }}>
                            Score: {globalBias} / 30
                        </span>
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                        {algoState?.pre_market_report || "No pre-market report generated today yet."}
                    </p>
                </div>

                <div style={{ height: 1, width: '100%', background: 'rgba(255,255,255,0.05)' }} />

                {/* 2. Live 4-Step Validation */}
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8 }}>Live Signal Analysis</span>
                        <span style={{ 
                            fontSize: 16, fontWeight: 800, 
                            color: signal.direction === 'BUY' ? '#4ade80' : signal.direction === 'SELL' ? '#f87171' : 'var(--text-primary)'
                        }}>
                            {signal.total_score}/110 ({signal.direction})
                        </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12 }}>
                        {[
                            { label: 'Step 1: Trend', score: signal.step1_score },
                            { label: 'Step 2: Momentum', score: signal.step2_score },
                            { label: 'Step 3: Options', score: signal.step3_score },
                            { label: 'Step 4: Levels', score: signal.step4_score }
                        ].map(step => (
                            <div key={step.label} style={{ background: 'rgba(0,0,0,0.15)', borderRadius: 10, padding: 12, border: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                                <span style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 6 }}>{step.label}</span>
                                <span style={{ 
                                    fontSize: 14, fontWeight: 700, 
                                    color: step.score > 15 ? '#4ade80' : step.score > 0 ? '#f59e0b' : 'var(--text-muted)' 
                                }}>
                                    {step.score} / 25
                                </span>
                            </div>
                        ))}
                    </div>

                    <div style={{ marginTop: 16, background: 'rgba(0,0,0,0.2)', padding: 16, borderRadius: 12, border: '1px solid rgba(255,255,255,0.05)', textAlign: 'center' }}>
                        <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>STATUS</div>
                        <div style={{ 
                            fontSize: 16, fontWeight: 800, letterSpacing: 0.5,
                            color: signal.signal_strength.includes('STRONG') ? '#f59e0b' : 'var(--text-primary)' 
                        }}>
                            {signal.signal_strength}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
