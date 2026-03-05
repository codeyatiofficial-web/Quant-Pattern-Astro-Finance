'use client';
import React, { useState, useEffect } from 'react';
import { usePlanGate } from './UpgradeModal';

const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

type SubTab = 'upcoming' | 'backtest' | 'pulse' | 'news';

// Color mapping for categories
const CAT_COLOR: Record<string, string> = {
    'RBI Policy': '#ef4444',
    'Union Budget': '#8b5cf6',
    'US Fed': '#3b82f6',
    'US Bonds': '#f59e0b',
    'US CPI': '#f97316',
    'US Jobs': '#06b6d4',
    'Elections': '#10b981',
    'US Elections': '#6366f1',
    'Oil/Commodity': '#84cc16',
    'GST': '#ec4899',
    'India CPI': '#f43f5e',
    'FII Flows': '#14b8a6',
    'Earnings Season': '#a855f7',
    'Global Shock': '#dc2626',
    'IPO/Corporate': '#7c3aed',
    'Currency': '#f59e0b',
};

function categoryColor(cat: string) {
    return CAT_COLOR[cat] || '#94a3b8';
}

function ReturnPill({ v, small }: { v: number | null; small?: boolean }) {
    if (v == null) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
    const color = v > 0 ? '#10b981' : v < 0 ? '#ef4444' : '#94a3b8';
    const bg = v > 0 ? 'rgba(16,185,129,0.12)' : v < 0 ? 'rgba(239,68,68,0.12)' : 'rgba(148,163,184,0.1)';
    return (
        <span style={{
            background: bg, color, fontWeight: 700, borderRadius: 6,
            padding: small ? '2px 6px' : '3px 8px', fontSize: small ? 11 : 12,
            display: 'inline-block',
        }}>
            {v > 0 ? '+' : ''}{v.toFixed(2)}%
        </span>
    );
}

function EventBadge({ bias }: { bias: string }) {
    const cls = bias === 'Bullish' ? 'badge-bullish' : bias === 'Bearish' ? 'badge-bearish' : 'badge-neutral';
    return <span className={`badge ${cls}`}>{bias}</span>;
}

interface CategoryObj { sub_event: string; category: string; count: number; emoji: string; color: string; desc: string }
interface BacktestResult { sub_event: string; symbol: string; emoji: string; desc: string; stats: any; events: any[]; next_occurrence?: any }

export default function EconomicEvents() {
    const { guardYears, modal: planModal, tier } = usePlanGate(1);
    const [sub, setSub] = useState<SubTab>('upcoming');
    const [events, setEvents] = useState<any[]>([]);
    const [evLoading, setEvLoading] = useState(false);
    const [categories, setCategories] = useState<CategoryObj[]>([]);
    const [selectedCat, setSelectedCat] = useState('');
    const [btSymbol, setBtSymbol] = useState('^NSEI');
    const [windowDays, setWindowDays] = useState(5);
    const [btResult, setBtResult] = useState<BacktestResult | null>(null);
    const [btLoading, setBtLoading] = useState(false);
    const [btError, setBtError] = useState('');
    const [pulse, setPulse] = useState<any>(null);
    const [pulseLoading, setPulseLoading] = useState(false);
    const [news, setNews] = useState<any>(null);
    const [newsLoading, setNewsLoading] = useState(false);
    const [catFilter, setCatFilter] = useState('All');

    // Load categories on mount
    useEffect(() => {
        fetch(`${API}/api/events/categories`)
            .then(r => r.json())
            .then(d => {
                const cats: CategoryObj[] = d.categories || [];
                setCategories(cats);
                if (cats.length > 0) setSelectedCat(cats[0].sub_event);
            }).catch(() => { });
    }, []);

    useEffect(() => {
        if (sub === 'upcoming' && events.length === 0) fetchEvents();
        if (sub === 'pulse' && !pulse) fetchPulse();
        if (sub === 'news' && !news) fetchNews();
    }, [sub]);

    const fetchEvents = async () => {
        setEvLoading(true);
        try {
            const r = await fetch(`${API}/api/events/upcoming?days=30`);
            const d = await r.json();
            setEvents(d.events || []);
        } catch { }
        setEvLoading(false);
    };

    const fetchPulse = async () => {
        setPulseLoading(true);
        try {
            const r = await fetch(`${API}/api/events/live-pulse`);
            setPulse(await r.json());
        } catch { }
        setPulseLoading(false);
    };

    const fetchNews = async () => {
        setNewsLoading(true);
        try {
            const r = await fetch(`${API}/api/sentiment/live`);
            setNews(await r.json());
        } catch { }
        setNewsLoading(false);
    };

    const runBacktest = async () => {
        if (!guardYears(5)) return;
        if (!selectedCat) { setBtError('Please select an event category.'); return; }
        setBtLoading(true); setBtResult(null); setBtError('');
        try {
            const r = await fetch(`${API}/api/events/backtest`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sub_event: selectedCat, symbol: btSymbol, window_days: windowDays }),
            });
            const data = await r.json();
            if (!r.ok) setBtError(data.detail || 'Backtest failed');
            else if (data.error) setBtError(data.error);
            else setBtResult(data);
        } catch { setBtError('Network error — is backend running?'); }
        setBtLoading(false);
    };

    const SUBTABS = [
        { key: 'upcoming', label: '📅 Upcoming Events' },
        { key: 'backtest', label: '🔁 Event Backtest' },
        { key: 'pulse', label: '🌐 Live Pulse' },
        { key: 'news', label: '📰 Market News' },
    ] as const;

    const SYMBOLS = ['^NSEI', '^NSEBANK', '^CNXIT', 'RELIANCE.NS', 'HDFCBANK.NS', 'TCS.NS'];
    const parentCats = ['All', ...Array.from(new Set(categories.map(c => c.category)))];
    const filteredCats = catFilter === 'All' ? categories : categories.filter(c => c.category === catFilter);

    return (
        <div>
            {planModal}
            <h1 className="section-title">📅 Economic Events</h1>
            <p className="section-subtitle">400+ historical events from 2000 · Backtest market reactions · Live pulse & news</p>

            <div className="tab-list" style={{ marginBottom: 24 }}>
                {SUBTABS.map(s => (
                    <button key={s.key} className={`tab-btn ${sub === s.key ? 'active' : ''}`} onClick={() => setSub(s.key)}>{s.label}</button>
                ))}
            </div>

            {/* ── UPCOMING EVENTS ─────────────────────────────── */}
            {sub === 'upcoming' && (
                <div>
                    <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
                        <button className="btn-primary" onClick={fetchEvents} disabled={evLoading}>
                            {evLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Loading…</> : '🔄 Refresh (Next 30 Days)'}
                        </button>
                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{events.length} events found</span>
                    </div>

                    {events.length === 0 && !evLoading ? (
                        <div className="alert-info">No upcoming events in the next 30 days. Check back closer to key dates.</div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            {events.map((ev: any, i: number) => {
                                const col = categoryColor(ev.category || '');
                                const urgencyBg = ev.urgency === 'imminent' ? 'rgba(239,68,68,0.06)' : ev.urgency === 'soon' ? 'rgba(245,158,11,0.06)' : 'transparent';
                                return (
                                    <div key={i} style={{
                                        background: urgencyBg, border: `1px solid rgba(255,255,255,0.07)`,
                                        borderLeft: `4px solid ${col}`, borderRadius: 12, padding: '14px 18px',
                                        display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16,
                                        transition: 'all 0.2s ease',
                                    }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                                                <span style={{ fontSize: 18 }}>{ev.emoji || '📅'}</span>
                                                <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 14 }}>{ev.description || ev.name}</span>
                                                {ev.urgency === 'imminent' && <span className="badge badge-bearish">⚡ Imminent</span>}
                                                {ev.urgency === 'soon' && <span className="badge badge-moderate">Soon</span>}
                                            </div>
                                            <div style={{ display: 'flex', gap: 14, fontSize: 11, color: 'var(--text-muted)', flexWrap: 'wrap' }}>
                                                <span>📆 {ev.date}</span>
                                                <span style={{ color: col, fontWeight: 600 }}>● {ev.sub_event || ev.category}</span>
                                                {ev.historical_bias && <span>Historical: <strong style={{ color: 'var(--text-secondary)' }}>{ev.historical_bias}</strong></span>}
                                            </div>
                                        </div>
                                        <div style={{ textAlign: 'right', minWidth: 60 }}>
                                            <div style={{ fontSize: 22, fontWeight: 800, color: col }}>{ev.days_away}</div>
                                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>days away</div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}

            {/* ── EVENT BACKTEST ───────────────────────────────── */}
            {sub === 'backtest' && (
                <div>
                    <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ fontWeight: 700, marginBottom: 6, fontSize: 16 }}>
                            📊 Event Category Backtest
                            <span style={{ fontSize: 10, color: '#f59e0b', verticalAlign: 'middle', marginLeft: 8, padding: '2px 6px', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: 4 }}>PRO</span>
                        </h3>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 20 }}>
                            400+ historical events from 2000 · RBI · Fed · Budget · Elections · Bonds · Oil · CPI · FII · Earnings · Global Shocks
                        </p>

                        {/* Category Group Filter */}
                        <div style={{ marginBottom: 16 }}>
                            <label className="form-label">Filter by Category Group</label>
                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                                {parentCats.map(c => (
                                    <button key={c} onClick={() => { setCatFilter(c); }}
                                        style={{
                                            padding: '5px 14px', borderRadius: 20, fontSize: 12, fontWeight: 500,
                                            border: `1px solid ${catFilter === c ? (CAT_COLOR[c] || '#8b5cf6') : 'rgba(255,255,255,0.1)'}`,
                                            background: catFilter === c ? `rgba(139,92,246,0.2)` : 'transparent',
                                            color: catFilter === c ? 'white' : 'var(--text-secondary)',
                                            cursor: 'pointer', transition: 'all 0.2s',
                                        }}>
                                        {c}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Event picker grid */}
                        <div style={{ marginBottom: 20 }}>
                            <label className="form-label">Select Event Sub-Type ({filteredCats.length} types, {filteredCats.reduce((s, c) => s + c.count, 0)} occurrences)</label>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8, marginTop: 8, maxHeight: 260, overflowY: 'auto', paddingRight: 4 }}>
                                {filteredCats.map(cat => (
                                    <button key={cat.sub_event}
                                        onClick={() => setSelectedCat(cat.sub_event)}
                                        style={{
                                            padding: '10px 14px', borderRadius: 10, textAlign: 'left', cursor: 'pointer',
                                            border: `1px solid ${selectedCat === cat.sub_event ? (categoryColor(cat.category)) : 'rgba(255,255,255,0.07)'}`,
                                            background: selectedCat === cat.sub_event ? `${categoryColor(cat.category)}20` : 'rgba(255,255,255,0.03)',
                                            transition: 'all 0.2s',
                                        }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                            <span style={{ fontSize: 16 }}>{cat.emoji}</span>
                                            <span style={{ fontSize: 12, fontWeight: 600, color: selectedCat === cat.sub_event ? 'white' : 'var(--text-primary)' }}>{cat.sub_event}</span>
                                        </div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span style={{ fontSize: 10, color: categoryColor(cat.category), fontWeight: 500 }}>{cat.category}</span>
                                            <span style={{ fontSize: 10, color: 'var(--text-muted)', background: 'rgba(255,255,255,0.08)', padding: '1px 6px', borderRadius: 10 }}>{cat.count}</span>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Controls row */}
                        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 20 }}>
                            <div style={{ minWidth: 180 }}>
                                <label className="form-label">Symbol</label>
                                <select className="form-select" value={btSymbol} onChange={e => setBtSymbol(e.target.value)}>
                                    {SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
                                </select>
                            </div>
                            <div style={{ minWidth: 160 }}>
                                <label className="form-label">Forward Window</label>
                                <select className="form-select" value={windowDays} onChange={e => setWindowDays(Number(e.target.value))}>
                                    {[1, 2, 3, 5, 7, 10].map(d => <option key={d} value={d}>T+{d}</option>)}
                                </select>
                            </div>
                            <button className="btn-primary" onClick={runBacktest} disabled={btLoading || !selectedCat} style={{ alignSelf: 'flex-end', minWidth: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                                {btLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2 }} />Running…</> : <>▶ Backtest "{selectedCat}" {tier === 'free' && '🔒'}</>}
                            </button>
                        </div>
                        {btError && <div className="alert-error">❌ {btError}</div>}
                    </div>

                    {/* ── Backtest Results ── */}
                    {btResult && (
                        <div>
                            {/* Header */}
                            <div className="glass-card" style={{ padding: 24, marginBottom: 16 }}>
                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
                                    <div style={{ fontSize: 40 }}>{btResult.emoji}</div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontWeight: 700, fontSize: 20, color: 'var(--text-primary)', marginBottom: 4 }}>{btResult.sub_event}</div>
                                        <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 10 }}>{btResult.desc}</div>
                                        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                                            <EventBadge bias={btResult.stats?.bias || 'Neutral'} />
                                            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                                {btResult.stats?.total_events} occurrences · {btResult.symbol}
                                            </span>
                                        </div>
                                    </div>
                                    {btResult.next_occurrence && (
                                        <div style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.3)', borderRadius: 10, padding: '10px 14px', textAlign: 'right', minWidth: 160 }}>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>NEXT OCCURRENCE</div>
                                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{btResult.next_occurrence.date}</div>
                                            <div style={{ fontSize: 11, color: 'var(--accent-violet)' }}>in {btResult.next_occurrence.days_away} days</div>
                                        </div>
                                    )}
                                </div>

                                {/* Stats grid */}
                                <div className="grid-4">
                                    {[
                                        { label: 'Total Events', value: btResult.stats?.total_events, color: '' },
                                        { label: 'Win Rate (Same Day ↑)', value: btResult.stats?.win_rate != null ? btResult.stats.win_rate.toFixed(1) + '%' : '—', color: (btResult.stats?.win_rate || 0) >= 50 ? '#10b981' : '#ef4444' },
                                        { label: 'Avg Same-Day Return', value: btResult.stats?.avg_same_day != null ? ((btResult.stats.avg_same_day > 0 ? '+' : '') + btResult.stats.avg_same_day.toFixed(3) + '%') : '—', color: (btResult.stats?.avg_same_day || 0) > 0 ? '#10b981' : '#ef4444' },
                                        { label: 'Max Gain / Max Loss', value: `+${btResult.stats?.max_gain?.toFixed(2)}% / ${btResult.stats?.max_loss?.toFixed(2)}%`, color: '#94a3b8' },
                                    ].map(m => (
                                        <div key={m.label} className="metric-box">
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>{m.label}</div>
                                            <div style={{ fontSize: 22, fontWeight: 700, color: m.color || 'var(--text-primary)' }}>{m.value ?? '—'}</div>
                                        </div>
                                    ))}
                                </div>

                                {/* T+1 / T+3 / T+5 averages */}
                                <div style={{ marginTop: 16, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                                    {[
                                        { label: 'Avg T+1', v: btResult.stats?.avg_t1_return },
                                        { label: 'Avg T+3', v: btResult.stats?.avg_t3_return },
                                        { label: 'Avg T+5', v: btResult.stats?.avg_t5_return },
                                    ].map(m => (
                                        <div key={m.label} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
                                            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{m.label}</span>
                                            <ReturnPill v={m.v} />
                                        </div>
                                    ))}
                                    <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
                                        <span style={{ fontSize: 12, color: 'var(--accent-green)' }}>📈 Up Days:</span>
                                        <span style={{ fontWeight: 700, color: '#10b981' }}>{btResult.stats?.up_count}</span>
                                        <span style={{ fontSize: 12, color: 'var(--accent-red)', marginLeft: 10 }}>📉 Down Days:</span>
                                        <span style={{ fontWeight: 700, color: '#ef4444' }}>{btResult.stats?.down_count}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Occurrences table */}
                            {btResult.events && btResult.events.length > 0 && (
                                <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
                                    <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ fontWeight: 700, fontSize: 15 }}>📋 Historical Occurrences ({btResult.events.length})</span>
                                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Data from 2000 · Yahoo Finance</span>
                                    </div>
                                    <div style={{ overflowX: 'auto', maxHeight: 500, overflowY: 'auto' }}>
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Date</th>
                                                    <th>Event</th>
                                                    <th>Expected</th>
                                                    <th>Same Day</th>
                                                    <th>T+1</th>
                                                    <th>T+3</th>
                                                    <th>T+5</th>
                                                    <th>Direction</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {btResult.events.map((e: any, i: number) => (
                                                    <tr key={i}>
                                                        <td style={{ color: 'var(--accent-gold)', fontWeight: 500 }}>{e.date}</td>
                                                        <td style={{ color: 'var(--text-primary)', maxWidth: 250, fontSize: 12 }}>{e.description}</td>
                                                        <td><EventBadge bias={e.expected_bias || 'Neutral'} /></td>
                                                        <td><ReturnPill v={e.same_day_return} small /></td>
                                                        <td><ReturnPill v={e.t1_return} small /></td>
                                                        <td><ReturnPill v={e.t3_return} small /></td>
                                                        <td><ReturnPill v={e.t5_return} small /></td>
                                                        <td>
                                                            <span style={{ color: e.direction === 'Up' ? '#10b981' : e.direction === 'Down' ? '#ef4444' : '#94a3b8', fontWeight: 600, fontSize: 12 }}>
                                                                {e.direction === 'Up' ? '▲' : e.direction === 'Down' ? '▼' : '→'} {e.direction}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* ── LIVE PULSE ───────────────────────────────────── */}
            {sub === 'pulse' && (
                <div>
                    <button className="btn-primary" onClick={fetchPulse} disabled={pulseLoading} style={{ marginBottom: 20 }}>
                        {pulseLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Loading…</> : '🔄 Refresh Live Pulse'}
                    </button>
                    {pulse && (
                        <div>
                            <div className="grid-2" style={{ marginBottom: 20 }}>
                                {/* Kite Live Quote */}
                                <div className="glass-card" style={{ padding: 24, borderColor: pulse.kite_connected ? 'rgba(16,185,129,0.2)' : 'rgba(255,255,255,0.06)' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                                        <div className="pulse-dot" style={{ background: pulse.kite_connected ? '#10b981' : '#ef4444' }} />
                                        <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>NIFTY 50 — Kite Live</span>
                                        <span className={`badge ${pulse.kite_connected ? 'badge-bullish' : 'badge-bearish'}`}>
                                            {pulse.kite_connected ? 'Connected' : 'Not Connected'}
                                        </span>
                                    </div>
                                    {pulse.live_quote ? (
                                        <div>
                                            <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'monospace', marginBottom: 6 }}>
                                                ₹{pulse.live_quote.last_price?.toLocaleString('en-IN')}
                                            </div>
                                            <div style={{ fontSize: 16, fontWeight: 600, color: (pulse.live_quote.change ?? 0) >= 0 ? '#10b981' : '#ef4444' }}>
                                                {(pulse.live_quote.change ?? 0) >= 0 ? '▲' : '▼'} {pulse.live_quote.change?.toFixed(2)} pts
                                            </div>
                                        </div>
                                    ) : (
                                        <div style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.7 }}>
                                            {pulse.kite_connected ? 'Quote unavailable — try refreshing.' : '→ Connect your Kite API for live Nifty quotes.\n Go to Dashboard → configure Kite credentials.'}
                                        </div>
                                    )}
                                </div>
                                {/* Upcoming events in next 7 days */}
                                <div className="glass-card" style={{ padding: 24 }}>
                                    <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 14 }}>⚡ Events — Next 7 Days</div>
                                    {(pulse.upcoming_events || []).length === 0 ? (
                                        <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>No major events in the next 7 days.</div>
                                    ) : (
                                        (pulse.upcoming_events || []).slice(0, 6).map((e: any, i: number) => (
                                            <div key={i} style={{
                                                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                                padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: 13,
                                            }}>
                                                <div>
                                                    <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{e.emoji || '📅'} {e.description || e.name}</div>
                                                    <div style={{ fontSize: 11, color: categoryColor(e.category), marginTop: 2 }}>{e.sub_event || e.category}</div>
                                                </div>
                                                <div style={{ textAlign: 'right', fontSize: 12 }}>
                                                    <div style={{ color: 'var(--text-muted)' }}>{e.date}</div>
                                                    <div style={{ color: e.days_away <= 2 ? '#ef4444' : e.days_away <= 5 ? '#f59e0b' : '#94a3b8', fontWeight: 600 }}>
                                                        {e.days_away === 0 ? 'Today' : `${e.days_away}d`}
                                                    </div>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ── MARKET NEWS ──────────────────────────────────── */}
            {sub === 'news' && (
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
                        <button className="btn-primary" onClick={fetchNews} disabled={newsLoading}>
                            {newsLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Fetching…</> : '🔄 Refresh Headlines'}
                        </button>
                        {news?.aggregate && (
                            <div className="glass-card" style={{ padding: '8px 16px', display: 'inline-flex', alignItems: 'center', gap: 14 }}>
                                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Overall Sentiment:</span>
                                <span style={{ fontWeight: 700, color: news.aggregate.overall_label === 'Bullish' ? '#10b981' : news.aggregate.overall_label === 'Bearish' ? '#ef4444' : '#94a3b8', fontSize: 13 }}>
                                    {news.aggregate.overall_label === 'Bullish' ? '▲' : news.aggregate.overall_label === 'Bearish' ? '▼' : '→'} {news.aggregate.overall_label}
                                </span>
                                <span style={{ fontSize: 12, color: '#10b981' }}>▲ {news.aggregate.bullish_count}</span>
                                <span style={{ fontSize: 12, color: '#ef4444' }}>▼ {news.aggregate.bearish_count}</span>
                                <span style={{ fontSize: 12, color: '#94a3b8' }}>→ {news.aggregate.neutral_count}</span>
                            </div>
                        )}
                    </div>
                    {news?.headlines?.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {news.headlines.map((h: any, i: number) => {
                                const polarity = h.polarity ?? 0;
                                const sentColor = polarity > 0.1 ? '#10b981' : polarity < -0.1 ? '#ef4444' : '#94a3b8';
                                const sentLabel = polarity > 0.1 ? '▲ Bullish' : polarity < -0.1 ? '▼ Bearish' : '→ Neutral';
                                const barWidth = Math.min(Math.abs(polarity) * 200, 100);
                                return (
                                    <div key={i} style={{
                                        background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.06)',
                                        borderRadius: 10, padding: '12px 16px', transition: 'all 0.2s',
                                        borderLeft: `3px solid ${sentColor}40`,
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5, marginBottom: 6 }}>
                                                    {h.link ? <a href={h.link} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'none' }}>{h.title}</a> : h.title}
                                                </div>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 11, color: 'var(--text-muted)' }}>
                                                    <span style={{ fontWeight: 600 }}>{h.source}</span>
                                                    {h.published && <span>{h.published?.slice(0, 16)}</span>}
                                                    <div style={{ flex: 1, height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 2, maxWidth: 80 }}>
                                                        <div style={{ width: `${barWidth}%`, height: '100%', background: sentColor, borderRadius: 2 }} />
                                                    </div>
                                                </div>
                                            </div>
                                            <span style={{ color: sentColor, fontWeight: 600, fontSize: 12, whiteSpace: 'nowrap', minWidth: 80, textAlign: 'right' }}>
                                                {sentLabel}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        !newsLoading && <div className="alert-info">📰 Click Refresh Headlines to load live market news from Economic Times, MoneyControl &amp; LiveMint.</div>
                    )}
                </div>
            )}
        </div>
    );
}
