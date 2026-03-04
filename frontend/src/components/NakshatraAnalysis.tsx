'use client';
import React, { useState } from 'react';

/* ── Tiny helpers ── */
function ReturnPill({ v }: { v: number | null }) {
    if (v == null) return <span className="num" style={{ color: 'var(--text-muted)' }}>—</span>;
    const cls = v > 0 ? 'bull' : v < 0 ? 'bear' : 'flat';
    const arrow = v > 0 ? '▲' : v < 0 ? '▼' : '●';
    return (
        <span className={`return-pill ${cls}`}>
            {arrow} {v > 0 ? '+' : ''}{v.toFixed(4)}%
        </span>
    );
}

function WinBar({ v }: { v: number | null }) {
    if (v == null) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
    const color = v >= 55 ? 'var(--accent-green)' : v >= 48 ? 'var(--accent-gold)' : 'var(--accent-red)';
    return (
        <div className="win-bar-wrap">
            <div className="win-bar-bg">
                <div className="win-bar-fill" style={{ width: `${Math.min(v, 100)}%`, background: color }} />
            </div>
            <span className="num" style={{ color, fontWeight: 700, fontSize: 12, minWidth: 38, textAlign: 'right' }}>
                {v.toFixed(1)}%
            </span>
        </div>
    );
}

function TendencyBadge({ t }: { t: string }) {
    const cls = t === 'Bullish' ? 'badge-bullish' : t === 'Bearish' ? 'badge-bearish' : 'badge-neutral';
    const icon = t === 'Bullish' ? '▲' : t === 'Bearish' ? '▼' : '●';
    return <span className={`badge ${cls}`}>{icon} {t}</span>;
}

function RankBadge({ i }: { i: number }) {
    if (i > 2) return <span className="rank-badge" style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: 11 }}>{i + 1}</span>;
    const cls = i === 0 ? 'rank-1' : i === 1 ? 'rank-2' : 'rank-3';
    const label = i === 0 ? '🥇' : i === 1 ? '🥈' : '🥉';
    return <span className={`rank-badge ${cls}`}>{label}</span>;
}

function NumCell({ v, decimals = 4, suffix = '%' }: { v: number | null; decimals?: number; suffix?: string }) {
    if (v == null) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
    return <span className="num" style={{ color: 'var(--text-secondary)' }}>{v.toFixed(decimals)}{suffix}</span>;
}

type SubTab = 'all' | 'rise' | 'no_rise' | 'tithi' | 'stats' | 'planets';

const SUBTABS: { key: SubTab; label: string; emoji: string }[] = [
    { key: 'all', label: 'All Days', emoji: '🌕' },
    { key: 'rise', label: 'Moon Rises (Market)', emoji: '🌅' },
    { key: 'no_rise', label: 'Moon Not Visible', emoji: '🌑' },
    { key: 'tithi', label: 'By Tithi', emoji: '📅' },
    { key: 'stats', label: 'Statistical Tests', emoji: '🔬' },
    { key: 'planets', label: 'Planet / Element', emoji: '🪐' },
];

export default function NakshatraAnalysis({ data }: { data: any }) {
    const [sub, setSub] = useState<SubTab>('all');

    if (!data) {
        return (
            <div style={{ padding: '40px 0' }}>
                <h1 className="section-title">📊 Nakshatra Performance Analysis</h1>
                <p className="section-subtitle">Load data from the Dashboard to run analysis.</p>
                <div className="alert-warn" style={{ maxWidth: 500 }}>
                    ⚠️ Please run analysis from the <strong>Dashboard</strong> tab first.
                </div>
            </div>
        );
    }

    const rows: any[] = sub === 'rise' ? (data.summary_market_rise || [])
        : sub === 'no_rise' ? (data.summary_outside_rise || [])
            : sub === 'tithi' ? (data.tithi_summary || [])
                : (data.summary || []);

    const isNak = !['tithi', 'stats', 'planets'].includes(sub);
    const isTithi = sub === 'tithi';

    return (
        <div className="fade-in">
            {/* ── Header ── */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 20 }}>
                <div>
                    <h1 className="section-title">📊 Nakshatra Performance Analysis</h1>
                    <p className="section-subtitle">
                        <span className="pulse-dot" style={{ marginRight: 7 }} />
                        {data.observations?.toLocaleString()} trading days analysed
                    </p>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <span className="stat-tag">🔬 ANOVA: <strong style={{ marginLeft: 3 }}>{data.anova?.result ?? '—'}</strong></span>
                    <span className="stat-tag">χ² Test: <strong style={{ marginLeft: 3 }}>{data.chi2?.result ?? '—'}</strong></span>
                </div>
            </div>

            {/* ── Sub-tabs ── */}
            <div className="tab-list" style={{ marginBottom: 20 }}>
                {SUBTABS.map(s => (
                    <button key={s.key} className={`tab-btn ${sub === s.key ? 'active' : ''}`} onClick={() => setSub(s.key)}>
                        {s.emoji} {s.label}
                    </button>
                ))}
            </div>

            {/* ── Nakshatra / Tithi tables ── */}
            {(isNak || isTithi) && (
                <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div style={{ overflowX: 'auto', maxHeight: 620, overflowY: 'auto' }}>
                        {isNak ? (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th style={{ width: 32 }}>#</th>
                                        <th>Nakshatra</th>
                                        <th>Ruling Planet</th>
                                        <th>Days</th>
                                        <th>Mean Return</th>
                                        <th>Median</th>
                                        <th>Win Rate</th>
                                        <th>Volatility</th>
                                        <th>Cum. Return</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows.length === 0 ? (
                                        <tr><td colSpan={9} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No data available</td></tr>
                                    ) : rows.map((row: any, i: number) => (
                                        <tr key={i}>
                                            <td style={{ paddingLeft: 12 }}><RankBadge i={i} /></td>
                                            <td>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                                    <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: 13.5 }}>{row.nakshatra_name}</span>
                                                    {row.nakshatra_sanskrit && <span style={{ fontSize: 10.5, color: 'var(--text-muted)', letterSpacing: '0.3px' }}>{row.nakshatra_sanskrit}</span>}
                                                </div>
                                            </td>
                                            <td>
                                                <span style={{ color: 'var(--accent-violet)', fontWeight: 600, fontSize: 12.5 }}>{row.ruling_planet}</span>
                                            </td>
                                            <td><span className="num" style={{ color: 'var(--text-secondary)' }}>{row.trading_days}</span></td>
                                            <td><ReturnPill v={row.mean_return} /></td>
                                            <td><ReturnPill v={row.median_return} /></td>
                                            <td><WinBar v={row.win_rate} /></td>
                                            <td><NumCell v={row.std_dev} /></td>
                                            <td><ReturnPill v={row.cumulative_return} /></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th style={{ width: 32 }}>#</th>
                                        <th>Tithi</th>
                                        <th>Paksha</th>
                                        <th>Days</th>
                                        <th>Mean Return</th>
                                        <th>Win Rate</th>
                                        <th>Volatility</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows.length === 0 ? (
                                        <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No data available</td></tr>
                                    ) : rows.map((row: any, i: number) => (
                                        <tr key={i}>
                                            <td style={{ paddingLeft: 12 }}><RankBadge i={i} /></td>
                                            <td style={{ fontWeight: 700, fontSize: 13.5 }}>{row.tithi_name}</td>
                                            <td>
                                                <span className="badge badge-info" style={{ fontSize: 11 }}>{row.paksha ?? '—'}</span>
                                            </td>
                                            <td><span className="num">{row.trading_days}</span></td>
                                            <td><ReturnPill v={row.mean_return} /></td>
                                            <td><WinBar v={row.win_rate} /></td>
                                            <td><NumCell v={row.std_dev} /></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            )}

            {/* ── Statistical Tests ── */}
            {sub === 'stats' && (
                <div className="grid-2" style={{ gap: 20 }}>
                    {[
                        {
                            title: '🔬 ANOVA Test',
                            sub: 'Are mean returns significantly different across Nakshatras?',
                            result: data.anova?.result,
                            fields: [
                                { label: 'F-Statistic', value: data.anova?.f_statistic?.toFixed(4) },
                                { label: 'p-value', value: data.anova?.p_value?.toFixed(6) },
                                { label: 'Groups', value: data.anova?.num_groups },
                                { label: 'Observations', value: data.anova?.total_observations?.toLocaleString() },
                            ],
                            interpretation: data.anova?.interpretation,
                        },
                        {
                            title: '📐 Chi-Square Test',
                            sub: 'Is market direction independent of Nakshatra?',
                            result: data.chi2?.result,
                            fields: [
                                { label: 'χ² Statistic', value: data.chi2?.chi_square_statistic?.toFixed(4) },
                                { label: 'p-value', value: data.chi2?.p_value?.toFixed(6) },
                                { label: 'Degrees of Freedom', value: data.chi2?.degrees_of_freedom },
                            ],
                            interpretation: data.chi2?.interpretation,
                        },
                    ].map((card, ci) => (
                        <div key={ci} className="glass-card" style={{ padding: 26 }}>
                            <h3 style={{ fontWeight: 700, fontSize: 15, marginBottom: 6, color: 'var(--text-primary)' }}>{card.title}</h3>
                            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16, lineHeight: 1.5 }}>{card.sub}</p>
                            <div style={{ marginBottom: 18 }}>
                                <TendencyBadge t={card.result === 'Significant' ? 'Bullish' : 'Neutral'} />
                                <span style={{ marginLeft: 8, fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600 }}>{card.result}</span>
                            </div>
                            <div className="insight-box" style={{ marginBottom: 14 }}>
                                {card.fields.map((f, fi) => (
                                    <div key={fi} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: fi < card.fields.length - 1 ? '1px solid var(--border-subtle)' : 'none' }}>
                                        <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{f.label}</span>
                                        <span className="num" style={{ fontWeight: 600 }}>{f.value ?? '—'}</span>
                                    </div>
                                ))}
                            </div>
                            <p style={{ fontSize: 11.5, color: 'var(--text-secondary)', lineHeight: 1.65 }}>{card.interpretation}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* ── Planet / Element ── */}
            {sub === 'planets' && (
                <div className="grid-2" style={{ gap: 20 }}>
                    {[
                        { title: '🪐 Ruling Planet Returns', rows: data.planet_analysis || [], nameKey: 'ruling_planet' },
                        { title: '🔥 Element Returns', rows: data.element_analysis || [], nameKey: 'element' },
                    ].map((section, si) => (
                        <div key={si} className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
                            <div style={{ padding: '18px 22px', borderBottom: '1px solid var(--border-subtle)' }}>
                                <h3 style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>{section.title}</h3>
                            </div>
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>{si === 0 ? 'Planet' : 'Element'}</th>
                                        <th>Days</th>
                                        <th>Mean Return</th>
                                        <th>Win Rate</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {section.rows.map((r: any, i: number) => (
                                        <tr key={i}>
                                            <td style={{ paddingLeft: 12 }}><RankBadge i={i} /></td>
                                            <td style={{ fontWeight: 700, color: 'var(--accent-violet)' }}>{r[section.nameKey]}</td>
                                            <td><span className="num">{r.trading_days}</span></td>
                                            <td><ReturnPill v={r.mean_return} /></td>
                                            <td><WinBar v={r.win_rate} /></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
