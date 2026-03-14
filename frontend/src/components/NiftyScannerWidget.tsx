'use client';
import React, { useState, useEffect } from 'react';

const API = '';

export default function NiftyScannerWidget() {
    const [scanData, setScanData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        let isMounted = true;
        const fetchScan = async () => {
            try {
                const res = await fetch(`${API}/api/nifty50-scan?_t=${Date.now()}`);
                const data = await res.json();
                if (!res.ok || data.error) throw new Error(data.error || 'Error');
                if (isMounted) {
                    setScanData(data);
                    setError('');
                }
            } catch (err) {
                if (isMounted) setError('Could not load Nifty 50 scan data.');
            }
            if (isMounted) setLoading(false);
        };

        fetchScan();
        const interval = setInterval(fetchScan, 120000); // refresh every 2 minutes

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, []);

    if (loading) {
        return (
            <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16,
                padding: '20px 24px', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 12
            }}>
                <span className="spinner" style={{ width: 24, height: 24, borderWidth: 2 }} />
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Scanning 50 constituents for technical patterns...</span>
            </div>
        );
    }

    if (error || !scanData) return null;

    const { top_buy, top_sell } = scanData;

    return (
        <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16,
            padding: '20px 24px', marginBottom: 24
        }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
                <div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: '#f8fafc', letterSpacing: 0.5, textTransform: 'uppercase' }}>
                        NIFTY 50 LIVE SCANNER
                    </div>
                    <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>
                        Real-time technical analysis (RSI, MACD, SMA) across all index constituents.
                    </div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>

                {/* TOP BUY CARD */}
                {top_buy && (
                    <div style={{
                        background: '#064e3b15', border: '1px solid #10b98130', borderRadius: 12, padding: '16px'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                            <div>
                                <div style={{ fontSize: 10, fontWeight: 800, color: '#10b981', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
                                    Strongest Buy Signal
                                </div>
                                <div style={{ fontSize: 24, fontWeight: 900, color: '#f8fafc', letterSpacing: 0.5 }}>
                                    {top_buy.symbol}
                                </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: 16, fontWeight: 700, color: '#f8fafc' }}>
                                    ₹{top_buy.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </div>
                                <div style={{ fontSize: 12, fontWeight: 700, color: top_buy.change_pct >= 0 ? '#10b981' : '#f43f5e' }}>
                                    {top_buy.change_pct >= 0 ? '+' : ''}{top_buy.change_pct.toFixed(2)}%
                                </div>
                            </div>
                        </div>

                        {/* Metrics */}
                        <div style={{ display: 'flex', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
                            <div style={{ background: '#00000040', padding: '6px 10px', borderRadius: 6, fontSize: 11 }}>
                                <span style={{ color: '#94a3b8' }}>RSI:</span> <span style={{ color: top_buy.rsi < 40 ? '#10b981' : '#f8fafc', fontWeight: 600 }}>{top_buy.rsi.toFixed(1)}</span>
                            </div>
                            <div style={{ background: '#00000040', padding: '6px 10px', borderRadius: 6, fontSize: 11 }}>
                                <span style={{ color: '#94a3b8' }}>Tech Score:</span> <span style={{ color: '#10b981', fontWeight: 600 }}>+{top_buy.score}</span>
                            </div>
                        </div>

                        {/* Reasons */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {top_buy.reasons.map((r: string, idx: number) => (
                                <div key={idx} style={{ fontSize: 12, color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <span style={{ color: '#10b981' }}>✓</span> {r}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* TOP SELL CARD */}
                {top_sell && (
                    <div style={{
                        background: '#7f1d1d15', border: '1px solid #f43f5e30', borderRadius: 12, padding: '16px'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                            <div>
                                <div style={{ fontSize: 10, fontWeight: 800, color: '#f43f5e', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
                                    Strongest Sell Signal
                                </div>
                                <div style={{ fontSize: 24, fontWeight: 900, color: '#f8fafc', letterSpacing: 0.5 }}>
                                    {top_sell.symbol}
                                </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: 16, fontWeight: 700, color: '#f8fafc' }}>
                                    ₹{top_sell.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </div>
                                <div style={{ fontSize: 12, fontWeight: 700, color: top_sell.change_pct >= 0 ? '#10b981' : '#f43f5e' }}>
                                    {top_sell.change_pct >= 0 ? '+' : ''}{top_sell.change_pct.toFixed(2)}%
                                </div>
                            </div>
                        </div>

                        {/* Metrics */}
                        <div style={{ display: 'flex', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
                            <div style={{ background: '#00000040', padding: '6px 10px', borderRadius: 6, fontSize: 11 }}>
                                <span style={{ color: '#94a3b8' }}>RSI:</span> <span style={{ color: top_sell.rsi > 60 ? '#f43f5e' : '#f8fafc', fontWeight: 600 }}>{top_sell.rsi.toFixed(1)}</span>
                            </div>
                            <div style={{ background: '#00000040', padding: '6px 10px', borderRadius: 6, fontSize: 11 }}>
                                <span style={{ color: '#94a3b8' }}>Tech Score:</span> <span style={{ color: '#f43f5e', fontWeight: 600 }}>{top_sell.score}</span>
                            </div>
                        </div>

                        {/* Reasons */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {top_sell.reasons.map((r: string, idx: number) => (
                                <div key={idx} style={{ fontSize: 12, color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <span style={{ color: '#f43f5e' }}>✗</span> {r}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
