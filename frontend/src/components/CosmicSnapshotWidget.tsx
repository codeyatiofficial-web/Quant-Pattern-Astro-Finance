'use client';
import React, { useState, useEffect } from 'react';

const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

export interface TodayInsight {
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

export function TendencyBadge({ t }: { t: string }) {
    const cls = t === 'Bullish' ? 'badge-bullish' : t === 'Bearish' ? 'badge-bearish' : 'badge-neutral';
    const icon = t === 'Bullish' ? '' : t === 'Bearish' ? '' : '';
    return <span className={`badge ${cls}`}>{icon} {t}</span>;
}

export function MetricCard({ label, value, sub, color, icon }: {
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

export default function CosmicSnapshotWidget() {
    const [insight, setInsight] = useState<TodayInsight | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API}/api/insight/today`)
            .then(r => r.json())
            .then(d => { setInsight(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div className="panel" style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
                <span className="spinner" />
                <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading today's cosmic data…</span>
            </div>
        );
    }

    if (!insight) {
        return (
            <div className="alert-warn" style={{ marginBottom: 20 }}> Could not load today's insight. Check backend connection.</div>
        );
    }

    return (
        <div style={{ marginBottom: 32 }}>
            <h2 style={{ fontSize: 16, fontWeight: 800, marginBottom: 16, color: 'var(--text-primary)' }}>Today's Cosmic Snapshot</h2>
            {/*  4-card metrics row  */}
            <div className="grid-4" style={{ marginBottom: 18 }}>
                <MetricCard
                    icon=""
                    label="Current Cycle"
                    value={<span className="gradient-text" style={{ fontSize: 20, fontWeight: 800 }}>{insight.current_nakshatra}</span>}
                    sub={insight.nakshatra_sanskrit}
                />
                <MetricCard
                    icon=""
                    label="Cycle Position"
                    value={<span className="gradient-text" style={{ fontSize: 20, fontWeight: 800 }}>Phase {insight.pada}</span>}
                    sub={insight.ruling_planet}
                />
                <MetricCard
                    icon=""
                    label="Sidereal Longitude"
                    value={
                        typeof insight.moon_longitude === 'number'
                            ? <span className="num" style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent-cyan)' }}>{insight.moon_longitude.toFixed(2)}°</span>
                            : <span style={{ color: 'var(--text-muted)' }}>—</span>
                    }
                    sub="Moon sidereal position"
                />
                <MetricCard
                    icon=""
                    label="Historical Tendency"
                    value={<TendencyBadge t={insight.historical_tendency || 'Neutral'} />}
                    sub="Based on historical data"
                />
            </div>

            {/*  Secondary info row  */}
            {(insight.tithi_name || insight.yoga_name) && (
                <div className="grid-3" style={{ marginBottom: 18 }}>
                    {insight.tithi_name && (
                        <MetricCard icon="" label="Lunar Phase" value={
                            <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-gold)' }}>{insight.tithi_name}</span>
                        } sub={insight.paksha ?? ''} />
                    )}
                    {insight.yoga_name && (
                        <MetricCard icon="" label="Signal Pattern" value={
                            <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-purple)' }}>{insight.yoga_name}</span>
                        } sub="Active pattern period" />
                    )}
                    <MetricCard icon="" label="Signal Driver" value={
                        <span style={{ fontSize: 18, fontWeight: 800, color: 'var(--accent-violet)' }}>{insight.ruling_planet}</span>
                    } sub="Pattern driver" />
                </div>
            )}

            {/*  Insight traits box  */}
            {insight.favorable_for && (
                <div className="glass-card" style={{ padding: '18px 22px', marginBottom: 16 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 24px' }}>
                        <div>
                            <span style={{ color: 'var(--accent-green)', fontWeight: 700, fontSize: 12.5 }}> Favorable for</span>
                            <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                {(insight.favorable_for || []).join(', ')}
                            </p>
                        </div>
                        <div>
                            <span style={{ color: 'var(--accent-red)', fontWeight: 700, fontSize: 12.5 }}> Unfavorable for</span>
                            <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                {(insight.unfavorable_for || []).join(', ')}
                            </p>
                        </div>
                        <div>
                            <span style={{ color: 'var(--accent-gold)', fontWeight: 700, fontSize: 12.5 }}> Financial Traits</span>
                            <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                {(insight.financial_traits || []).join(', ')}
                            </p>
                        </div>
                        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                            <div>
                                <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: 12.5 }}> Lucky Numbers</span>
                                <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
                                    {(insight.lucky_numbers || []).join(', ')}
                                </p>
                            </div>
                            <div>
                                <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: 12.5 }}> Lucky Colors</span>
                                <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
                                    {(insight.lucky_colors || []).join(', ')}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/*  Cycle transition  */}
            {insight.transition && (
                <div className="alert-info" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 18 }}></span>
                    <span>
                        <strong>Cycle Transition Today:</strong>{' '}
                        <span style={{ color: 'var(--accent-red)' }}>{insight.transition.from_nakshatra}</span>
                        {' → '}
                        <span style={{ color: 'var(--accent-green)' }}>{insight.transition.to_nakshatra}</span>
                        {' at '}
                        <span className="num" style={{ color: 'var(--accent-gold)', fontWeight: 600 }}>
                            {new Date(insight.transition.transition_time).toLocaleString('en-IN', {
                                day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true
                            })} (Mumbai Time)
                        </span>
                    </span>
                </div>
            )}
        </div>
    );
}
