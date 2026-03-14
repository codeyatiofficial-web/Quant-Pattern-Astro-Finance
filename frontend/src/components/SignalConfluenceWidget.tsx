'use client';
import React, { useState, useEffect } from 'react';
import { usePlan } from '../contexts/PlanContext';

const SIGNAL_METRICS = [
    { id: 'pcr', name: 'PCR', bull: '> 1.2', bear: '< 0.8' },
    { id: 'fii', name: 'FII Futures', bull: 'Net Long', bear: 'Net Short' },
    { id: 'oi', name: 'OI Analysis', bull: 'PE unwinding', bear: 'CE unwinding' },
    { id: 'vwap', name: 'Price vs VWAP', bull: 'Above', bear: 'Below' },
    { id: 'rsi', name: 'RSI (1hr)', bull: '50-65', bear: '35-50' },
    { id: 'vix', name: 'VIX', bull: 'Falling', bear: 'Rising' },
    { id: 'sgx', name: 'SGX/Gift Nifty', bull: 'Gap up', bear: 'Gap down' },
    { id: 'supertrend', name: 'Supertrend (15m)', bull: 'Buy', bear: 'Sell' },
    { id: 'maxpain', name: 'Max Pain', bull: 'Below MP', bear: 'Above MP' },
    { id: 'breadth', name: 'Breadth A/D', bull: '> 35/15', bear: '< 15/35' },
];
export default function SignalConfluenceWidget() {
    const tf = '15m'; // using a fixed timeframe
    const [loading, setLoading] = useState(false);
    
    // For demo purposes, we generate a mock state based on TF
    // In production, fetch from backend.
    const [signals, setSignals] = useState<any>({});
    const [score, setScore] = useState(0);

    useEffect(() => {
        setLoading(true);
        const url = `${typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : ''}/api/correlation/confluence?tf=${tf}&market=NSE`;
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data && data.signals) {
                    setSignals(data.signals);
                    setScore(data.score ?? 0);
                }
                setLoading(false);
            })
            .catch(err => {
                console.error("Confluence fetch error:", err);
                setLoading(false);
            });
    }, [tf]);
    
    const { tier } = usePlan();
    const isLocked = false; // Made available for all users

    let recommendation = '';
    let recColor = '';
    if (score >= 7) {
        recommendation = 'STRONG BUY';
        recColor = '#22c55e'; // Green
    } else if (score <= 3) {
        recommendation = 'STRONG SELL';
        recColor = '#ef4444'; // Red
    } else {
        recommendation = 'NEUTRAL / NO TRADE';
        recColor = '#f59e0b'; // Amber
    }

    return (
        <div className="glass-card" style={{ marginBottom: 24, padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 14 }}>
                <div>
                    <h2 style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
                        NIFTY 50 Signal Confluence
                    </h2>
                </div>
            </div>

            <div style={{ position: 'relative' }}>
                {/* Paywall Overlay */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24, transition: 'all 0.3s' }}>
                    {/* Score Section */}
                    <div style={{ background: 'rgba(0,0,0,0.15)', borderRadius: 12, padding: 20, border: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', position: 'relative' }}>
                        <div style={{ position: 'relative', width: 140, height: 140, marginBottom: 16 }}>
                            <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                                <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                                <circle cx="50" cy="50" r="40" fill="none" stroke={recColor} strokeWidth="8" strokeDasharray="251.2" strokeDashoffset={251.2 - (score / 10) * 251.2} style={{ transition: 'stroke-dashoffset 1s ease-out' }} />
                            </svg>
                            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                                <span style={{ fontSize: 36, fontWeight: 900, color: '#fff', lineHeight: 1 }}>{score}</span>
                                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>/ 10</span>
                            </div>
                        </div>
                        
                        <div style={{ fontSize: 18, fontWeight: 800, color: recColor, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                            {loading ? 'Analyzing...' : recommendation}
                        </div>
                        <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                            {loading ? 'Computing metrics...' : 'Based on real-time multi-timeframe confluence.'}
                        </p>
                    </div>

                    {/* Table Section */}
                    <div style={{ overflowX: 'auto', background: 'rgba(0,0,0,0.15)', borderRadius: 12, padding: '16px 20px', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <table className="data-table" style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                    <th style={{ textAlign: 'left', paddingBottom: 10, color: 'var(--text-muted)' }}>Signal</th>
                                    <th style={{ textAlign: 'center', paddingBottom: 10, color: '#4ade80' }}>Bullish +1</th>
                                    <th style={{ textAlign: 'center', paddingBottom: 10, color: '#f87171' }}>Bearish +1</th>
                                    <th style={{ textAlign: 'center', paddingBottom: 10, color: 'var(--text-muted)' }}>State</th>
                                </tr>
                            </thead>
                            <tbody style={{ opacity: loading ? 0.3 : 1, transition: 'opacity 0.2s', borderTop: 'none' }}>
                                {SIGNAL_METRICS.map((m, idx) => {
                                    const st = signals[m.id];
                                    return (
                                        <tr key={m.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                                            <td style={{ padding: '8px 0', fontWeight: 600, color: 'var(--text-primary)' }}>
                                                {m.name}
                                            </td>
                                            <td style={{ padding: '8px 0', textAlign: 'center', color: st === 1 ? '#4ade80' : 'var(--text-muted)', fontWeight: st === 1 ? 700 : 400 }}>{m.bull}</td>
                                            <td style={{ padding: '8px 0', textAlign: 'center', color: st === -1 ? '#f87171' : 'var(--text-muted)', fontWeight: st === -1 ? 700 : 400 }}>{m.bear}</td>
                                            <td style={{ padding: '8px 0', textAlign: 'center' }}>
                                                {st === 1 && <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: '#4ade80', boxShadow: '0 0 8px #4ade80' }} />}
                                                {st === -1 && <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: '#f87171', boxShadow: '0 0 8px #f87171' }} />}
                                                {st === 0 && <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: 'rgba(255,255,255,0.1)' }} />}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div style={{ marginTop: 24, padding: '12px 16px', background: 'rgba(0,0,0,0.2)', borderRadius: 10, border: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: 24, fontSize: 12, color: 'var(--text-muted)', justifyContent: 'center', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ width: 10, height: 10, borderRadius: '50%', background: '#22c55e' }}></span><span style={{ color: '#fff', fontWeight: 700 }}>Score ≥ 7</span> → Strong Buy Signal</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b' }}></span><span style={{ color: '#fff', fontWeight: 700 }}>Score 4-6</span> → Neutral / No Trade</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }}></span><span style={{ color: '#fff', fontWeight: 700 }}>Score ≤ 3</span> → Strong Sell Signal</div>
            </div>
        </div>
    );
}

