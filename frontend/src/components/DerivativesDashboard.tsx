'use client';
import { useState, useEffect, useCallback } from 'react';
import { usePlanGate } from './UpgradeModal';

const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

//  Tiny helper components 
function Spinner() {
    return <div className="flex justify-center py-10"><div className="spinner w-8 h-8 border-4" /></div>;
}
function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
    return <div className={`glass-card p-5 group transition-all duration-300 ${className}`}>{children}</div>;
}
function Badge({ text, color }: { text: string; color: string }) {
    const colors: Record<string, string> = {
        green: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
        red: 'bg-red-500/15 text-red-400 border-red-500/25',
        yellow: 'bg-amber-500/15 text-amber-400 border-amber-500/25',
        blue: 'bg-blue-500/15 text-blue-400 border-blue-500/25',
        purple: 'bg-purple-500/15 text-purple-400 border-purple-500/25',
    };
    return <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${colors[color] || colors.blue}`}>{text}</span>;
}

//  Sub-sections rendered by tab 
type Tab = 'overview' | 'chain' | 'strategy' | 'backtest' | 'alerts';

export default function DerivativesDashboard() {
    const [tab, setTab] = useState<Tab>('overview');
    const [snapshot, setSnapshot] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchSnapshot = useCallback(async () => {
        setLoading(true); setError('');
        try {
            const res = await fetch(`${API}/api/derivatives/snapshot`);
            if (!res.ok) throw new Error(await res.text());
            setSnapshot(await res.json());
        } catch (e: any) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { fetchSnapshot(); }, [fetchSnapshot]);

    const tabs: { key: Tab; label: string }[] = [
        { key: 'overview', label: ' Overview' },
        { key: 'chain', label: ' Options Chain' },
        { key: 'strategy', label: ' Strategy Wizard' },
        { key: 'backtest', label: ' Backtesting' },
        { key: 'alerts', label: ' Alerts' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-[var(--text-primary)]">
                        Derivatives & Options Strategy
                    </h1>
                    <div className="flex items-center gap-2 mt-1">
                        <p className="text-sm text-[var(--text-muted)]">NSE India — Options Chain · Strategy Recommender · Backtesting</p>
                        {snapshot && (
                            snapshot.kite_connected ? (
                                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25"> Kite Live</span>
                            ) : (
                                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/25"> Synthetic</span>
                            )
                        )}
                    </div>
                </div>
                <button onClick={fetchSnapshot} disabled={loading}
                    style={{ background: 'var(--text-primary)', color: 'var(--bg-primary)' }}
                    className="px-4 py-2 text-sm font-semibold rounded-lg hover:shadow-lg hover:opacity-90 transition-all disabled:opacity-50">
                    {loading ? 'Loading…' : '↻ Refresh Data'}
                </button>
            </div>

            {/* Tab bar */}
            <div className="flex gap-1 bg-[var(--bg-card)] p-1 rounded-xl border border-[var(--border-subtle)] overflow-x-auto">
                {tabs.map(t => (
                    <button key={t.key} onClick={() => setTab(t.key)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${tab === t.key
                            ? 'bg-[var(--bg-secondary)] text-[var(--text-primary)] font-bold shadow-sm border border-[var(--border-active)]'
                            : 'text-gray-400 hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]'}`}>
                        {t.label}
                    </button>
                ))}
            </div>

            {error && <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">{error}</div>}
            {loading && <Spinner />}

            {!loading && snapshot && (
                <>
                    {tab === 'overview' && <OverviewTab snapshot={snapshot} />}
                    {tab === 'chain' && <ChainTab chain={snapshot.options_chain} spot={snapshot.spot} />}
                    {tab === 'strategy' && <StrategyTab snapshot={snapshot} />}
                    {tab === 'backtest' && <BacktestTab />}
                    {tab === 'alerts' && <AlertsTab />}
                </>
            )}
        </div>
    );
}

/* 
   OVERVIEW TAB
    */
function OverviewTab({ snapshot }: { snapshot: any }) {
    const { spot, pcr, max_pain, vix, forecast, fii_dii_30d, days_to_expiry } = snapshot;
    const fc = forecast;
    const fiiRecent = fii_dii_30d?.slice(-5) || [];

    return (
        <div className="space-y-6">
            {/* KPI row */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <KPI label="NIFTY Spot" value={`₹${spot?.toLocaleString()}`} sub="" color="blue" />
                <KPI label="PCR" value={pcr?.toFixed(2)} sub={pcr > 1.2 ? 'Bearish' : pcr < 0.8 ? 'Bullish' : 'Neutral'} color={pcr > 1.2 ? 'red' : pcr < 0.8 ? 'green' : 'yellow'} />
                <KPI label="Max Pain" value={`₹${max_pain?.toLocaleString()}`} sub={`${((max_pain - spot) / spot * 100).toFixed(1)}% from spot`} color="purple" />
                <KPI label="India VIX" value={vix?.current?.toFixed(1)} sub={vix?.interpretation?.split('—')[0]} color={vix?.current > 20 ? 'red' : 'green'} />
                <KPI label="Expiry" value={`${days_to_expiry}d`} sub="Days to expiry" color="blue" />
                <KPI label="Forecast" value={fc?.forecast} sub={`${fc?.confidence}% confidence`} color={fc?.forecast === 'BULLISH' ? 'green' : fc?.forecast === 'BEARISH' ? 'red' : 'yellow'} />
            </div>

            {/* Forecast signals */}
            <Card>
                <h3 className="text-lg font-bold text-[var(--text-primary)] mb-3"> Trend Forecast — 1 Month Ahead</h3>
                <div className="flex items-center gap-3 mb-4">
                    <Badge text={fc?.forecast} color={fc?.forecast === 'BULLISH' ? 'green' : fc?.forecast === 'BEARISH' ? 'red' : 'yellow'} />
                    <span className="text-sm text-[var(--text-muted)]">Score: {fc?.score} · Confidence: {fc?.confidence}%</span>
                </div>
                <div className="space-y-2">
                    {fc?.signals?.map((s: any, i: number) => (
                        <div key={i} className={`flex items-start gap-2 text-sm p-2 rounded-lg ${s.type === 'bullish' ? 'bg-emerald-500/5' : s.type === 'bearish' ? 'bg-red-500/5' : 'bg-gray-500/5'}`}>
                            <span>{s.type === 'bullish' ? '🟢' : s.type === 'bearish' ? '' : '🟡'}</span>
                            <span className="text-[var(--text-secondary)]">{s.signal}</span>
                        </div>
                    ))}
                </div>
            </Card>

            {/* FII/DII table */}
            <Card>
                <h3 className="text-lg font-bold text-[var(--text-primary)] mb-3"> FII / DII Flow (Last 5 Days)</h3>
                <div className="overflow-x-auto rounded-xl border border-[var(--border-subtle)] shadow-[var(--shadow-card)]">
                    <table className="w-full text-sm font-quant text-right">
                        <thead className="bg-[var(--bg-table-head)] border-b border-[var(--border-subtle)] text-[11px] uppercase tracking-wider text-[var(--text-muted)] font-inter font-bold">
                            <tr>
                                <th className="py-2 text-left">Date</th><th className="text-right">FII Buy</th><th className="text-right">FII Sell</th>
                                <th className="text-right">FII Net</th><th className="text-right">DII Buy</th><th className="text-right">DII Sell</th><th className="text-right">DII Net</th>
                            </tr></thead>
                        <tbody>
                            {fiiRecent.map((d: any, i: number) => (
                                <tr key={i} className="border-b border-[var(--border-subtle)]/50 hover:bg-[var(--bg-card-hover)]">
                                    <td className="py-2 text-[var(--text-secondary)]">{d.date}</td>
                                    <td className="text-right text-emerald-400">₹{d.fii_buy?.toFixed(0)}</td>
                                    <td className="text-right text-red-400">₹{d.fii_sell?.toFixed(0)}</td>
                                    <td className={`text-right font-semibold ${d.fii_net > 0 ? 'text-emerald-400' : 'text-red-400'}`}>₹{d.fii_net?.toFixed(0)}</td>
                                    <td className="text-right text-emerald-400">₹{d.dii_buy?.toFixed(0)}</td>
                                    <td className="text-right text-red-400">₹{d.dii_sell?.toFixed(0)}</td>
                                    <td className={`text-right font-semibold ${d.dii_net > 0 ? 'text-emerald-400' : 'text-red-400'}`}>₹{d.dii_net?.toFixed(0)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </Card>
        </div>
    );
}

function KPI({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
    const bgColors: Record<string, string> = {
        green: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
        red: 'bg-red-500/10 border-red-500/20 text-red-400',
        yellow: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
        blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
        purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
    };
    return (
        <div className={`border rounded-xl p-4 text-center ${bgColors[color] || bgColors.blue} flex flex-col justify-center`}>
            <p className="text-[10px] font-inter text-[var(--text-muted)] mb-1 uppercase tracking-widest font-bold">{label}</p>
            <p className="text-xl font-bold font-quant opacity-90 text-[var(--text-primary)]">{value}</p>
            {sub && <p className="text-[10px] font-inter text-[var(--text-muted)] mt-1">{sub}</p>}
        </div>
    );
}

/* 
   OPTIONS CHAIN TAB
    */
function ChainTab({ chain, spot }: { chain: any[]; spot: number }) {
    const [showGreeks, setShowGreeks] = useState(false);
    if (!chain?.length) return <p className="text-center text-gray-400 py-8">No chain data</p>;
    const atm = chain.reduce((prev: any, curr: any) => Math.abs(curr.strike - spot) < Math.abs(prev.strike - spot) ? curr : prev);

    return (
        <Card>
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-[var(--text-primary)]"> Options Chain Heatmap</h3>
                <label className="flex items-center gap-2 text-sm text-[var(--text-muted)] cursor-pointer">
                    <input type="checkbox" checked={showGreeks} onChange={e => setShowGreeks(e.target.checked)} className="accent-orange-500" />
                    Show Greeks
                </label>
            </div>
            <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                <table className="w-full text-xs">
                    <thead className="sticky top-0 bg-[var(--bg-card)] z-10">
                        <tr className="text-[var(--text-muted)] border-b border-[var(--border-subtle)]">
                            <th className="py-2 text-right text-emerald-400">CE OI</th>
                            <th className="text-right text-emerald-400">CE Chg</th>
                            <th className="text-right text-emerald-400">CE IV</th>
                            <th className="text-right text-emerald-400">CE Price</th>
                            {showGreeks && <><th className="text-right text-emerald-400">Δ</th><th className="text-right text-emerald-400">Θ</th></>}
                            <th className="text-center font-bold text-orange-400">STRIKE</th>
                            <th className="text-right text-red-400">PE Price</th>
                            <th className="text-right text-red-400">PE IV</th>
                            <th className="text-right text-red-400">PE Chg</th>
                            <th className="text-right text-red-400">PE OI</th>
                            {showGreeks && <><th className="text-right text-red-400">Δ</th><th className="text-right text-red-400">Θ</th></>}
                        </tr>
                    </thead>
                    <tbody>
                        {chain.map((row: any) => {
                            const isATM = row.strike === atm.strike;
                            const maxOI = Math.max(...chain.map((r: any) => Math.max(r.CE.oi, r.PE.oi)));
                            const ceHeat = Math.min(1, row.CE.oi / maxOI);
                            const peHeat = Math.min(1, row.PE.oi / maxOI);
                            return (
                                <tr key={row.strike} className={`border-b border-[var(--border-subtle)]/30 ${isATM ? 'bg-orange-500/10 font-semibold' : 'hover:bg-[var(--bg-card-hover)]'}`}>
                                    <td className="py-1.5 text-right" style={{ backgroundColor: `rgba(16,185,129,${ceHeat * 0.2})` }}>{row.CE.oi.toLocaleString()}</td>
                                    <td className={`text-right ${row.CE.change_oi > 0 ? 'text-emerald-400' : 'text-red-400'}`}>{row.CE.change_oi > 0 ? '+' : ''}{row.CE.change_oi.toLocaleString()}</td>
                                    <td className="text-right text-[var(--text-secondary)]">{row.CE.iv}%</td>
                                    <td className="text-right text-emerald-400 font-medium">{row.CE.price}</td>
                                    {showGreeks && <><td className="text-right text-[var(--text-muted)]">{row.CE.delta}</td><td className="text-right text-[var(--text-muted)]">{row.CE.theta}</td></>}
                                    <td className={`text-center font-bold ${isATM ? 'text-orange-400' : 'text-[var(--text-primary)]'}`}>{row.strike.toLocaleString()} {isATM && ''}</td>
                                    <td className="text-right text-red-400 font-medium">{row.PE.price}</td>
                                    <td className="text-right text-[var(--text-secondary)]">{row.PE.iv}%</td>
                                    <td className={`text-right ${row.PE.change_oi > 0 ? 'text-emerald-400' : 'text-red-400'}`}>{row.PE.change_oi > 0 ? '+' : ''}{row.PE.change_oi.toLocaleString()}</td>
                                    <td className="py-1.5 text-right" style={{ backgroundColor: `rgba(239,68,68,${peHeat * 0.2})` }}>{row.PE.oi.toLocaleString()}</td>
                                    {showGreeks && <><td className="text-right text-[var(--text-muted)]">{row.PE.delta}</td><td className="text-right text-[var(--text-muted)]">{row.PE.theta}</td></>}
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </Card>
    );
}

/* 
   STRATEGY WIZARD TAB
    */
function StrategyTab({ snapshot }: { snapshot: any }) {
    const [risk, setRisk] = useState('moderate');
    const [marketView, setMarketView] = useState('ALL'); // ALL, BULLISH, BEARISH, NEUTRAL
    const [recs, setRecs] = useState<any>({ BULLISH: [], BEARISH: [], NEUTRAL: [] });
    const [loadingRec, setLoadingRec] = useState(false);
    const [selectedPayoff, setSelectedPayoff] = useState<any>(null);

    const fetchRecs = async () => {
        setLoadingRec(true);
        try {
            const fc = snapshot.forecast;
            const avgIV = snapshot.options_chain?.reduce((s: number, r: any) => s + r.CE.iv, 0) / (snapshot.options_chain?.length || 1);
            const res = await fetch(`${API}/api/derivatives/recommend`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ forecast: fc.forecast, confidence: fc.confidence, avg_iv: avgIV, pcr: snapshot.pcr, risk_appetite: risk, fii_net: fc.avg_fii_net_10d || 0 }),
            });
            const data = await res.json();
            setRecs(data.recommendations || { BULLISH: [], BEARISH: [], NEUTRAL: [] });
            setMarketView(fc.forecast); // Default to actual forecast
        } catch (e) { console.error(e); }
        finally { setLoadingRec(false); }
    };

    const fetchPayoff = async (key: string) => {
        try {
            const res = await fetch(`${API}/api/derivatives/payoff`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ strategy_key: key }),
            });
            setSelectedPayoff(await res.json());
        } catch (e) { console.error(e); }
    };

    useEffect(() => { fetchRecs(); }, [risk]);

    const catColors: Record<string, string> = { BULLISH: 'green', BEARISH: 'red', NEUTRAL: 'yellow', HEDGING: 'purple' };

    // Flatten recs for rendering if ALL is selected, otherwise get specific category
    let displayedRecs: any[] = [];
    if (marketView === 'ALL') {
        displayedRecs = [...(recs.BULLISH || []), ...(recs.BEARISH || []), ...(recs.NEUTRAL || [])];
    } else {
        displayedRecs = recs[marketView] || [];
    }

    return (
        <div className="space-y-6">
            <Card>
                <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 mb-4">
                    <h3 className="text-lg font-bold text-[var(--text-primary)]"> Strategy Selector Wizard</h3>
                    <div className="flex gap-2">
                        {['BULLISH', 'BEARISH', 'NEUTRAL', 'ALL'].map(view => (
                            <button key={view} onClick={() => setMarketView(view)}
                                className={`px-3 py-1 text-xs font-bold rounded min-w-[70px] transition-all border
                                ${marketView === view
                                        ? view === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500'
                                            : view === 'BEARISH' ? 'bg-red-500/20 text-red-400 border-red-500'
                                                : view === 'NEUTRAL' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500'
                                                    : 'bg-[var(--text-primary)] text-[var(--bg-primary)] border-[var(--text-primary)]'
                                        : 'bg-transparent text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-[var(--text-muted)]'
                                    }`}>
                                {view}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="flex flex-wrap gap-3 mb-4">
                    <span className="text-sm text-[var(--text-muted)]">Risk Appetite:</span>
                    {['conservative', 'moderate', 'aggressive'].map(r => (
                        <button key={r} onClick={() => setRisk(r)}
                            className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all capitalize ${risk === r
                                ? 'bg-orange-500/20 text-orange-400 border-orange-500/40' : 'text-[var(--text-secondary)] border-[var(--border-subtle)] hover:bg-[var(--bg-card-hover)]'}`}>
                            {r}
                        </button>
                    ))}
                </div>
                <div className="flex flex-wrap gap-2 mb-2 text-xs text-[var(--text-muted)] p-2 rounded bg-[var(--bg-primary)]/50 border border-[var(--border-subtle)]">
                    <span>Forecast: <Badge text={snapshot.forecast.forecast} color={catColors[snapshot.forecast.forecast] || 'blue'} /></span>
                    <span className="border-l border-[var(--border-subtle)] pl-2">PCR: {snapshot.pcr?.toFixed(2)}</span>
                    <span className="border-l border-[var(--border-subtle)] pl-2">VIX: {snapshot.vix?.current?.toFixed(1)}</span>
                </div>
            </Card>

            {loadingRec ? <Spinner /> : displayedRecs.length === 0 ? (
                <div className="text-center p-8 text-[var(--text-muted)] border border-dashed border-[var(--border-subtle)] rounded-lg">
                    No strategies found for this combination. Try adjusting risk appetite.
                </div>
            ) : (
                <div className="grid gap-4">
                    {displayedRecs.map((rec: any, i: number) => (
                        <Card key={i} className="hover:border-[var(--border-focus)] transition-all bg-[var(--bg-card)] relative overflow-hidden">

                            {/* Accent line based on category */}
                            <div className={`absolute left-0 top-0 bottom-0 w-1 ${rec.category === 'BULLISH' ? 'bg-emerald-500' :
                                rec.category === 'BEARISH' ? 'bg-red-500' :
                                    'bg-yellow-500'
                                }`} />

                            <div className="flex flex-col md:flex-row items-start justify-between gap-6 pl-3">
                                <div className="flex-1 w-full text-left">
                                    <div className="flex flex-wrap items-center gap-2 mb-2">
                                        <h4 className="text-base font-bold text-[var(--text-primary)]">{rec.name}</h4>
                                        <Badge text={rec.category} color={catColors[rec.category] || 'blue'} />
                                    </div>

                                    {/* Real Trade Execution Block */}
                                    <div className="mb-3 p-3 bg-[var(--bg-secondary)]/40 rounded-lg border border-[var(--border-active)]/20 shadow-inner">
                                        <p className="font-quant text-sm text-[var(--text-primary)] mb-1">
                                            {rec.trade_description || rec.description}
                                        </p>
                                        <div className="flex gap-4 text-[13px] mt-2 font-quant">
                                            <span className="text-emerald-500 font-bold">Max Profit: {typeof rec.max_profit === 'number' ? `₹${rec.max_profit.toLocaleString()}` : rec.max_profit}</span>
                                            <span className="text-red-500 font-bold">Max Risk: {typeof rec.max_loss === 'number' ? `₹${rec.max_loss.toLocaleString()}` : rec.max_loss}</span>
                                        </div>
                                    </div>

                                    {/* 35-yr Expert Insight */}
                                    {rec.expert_insight && (
                                        <div className="mb-3 p-2 pl-3 border-l-2 border-indigo-500 bg-indigo-500/5 text-sm">
                                            <span className="font-bold text-indigo-400 text-xs uppercase tracking-wider block mb-1"> Expert Insight</span>
                                            <span className="text-[var(--text-secondary)] italic leading-relaxed">{rec.expert_insight}</span>
                                        </div>
                                    )}

                                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--text-muted)] mt-2">
                                        <span> {rec.best_when}</span>
                                        <span> IV: {rec.iv_preference}</span>
                                    </div>
                                    {rec.reasons?.length > 0 && (
                                        <div className="mt-2 space-y-1">
                                            {rec.reasons.map((r: string, j: number) => (
                                                <div key={j} className="text-[11px] text-[var(--text-muted)] flex items-start gap-1">
                                                    <span className="text-orange-400 mt-0.5">•</span> <span>{r}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                <button onClick={() => {
                                    if (selectedPayoff?.strategy_key === rec.key) {
                                        setSelectedPayoff(null); // toggle off
                                    } else {
                                        fetchPayoff(rec.key);
                                    }
                                }}
                                    className="w-full md:w-auto px-4 py-2 bg-[var(--bg-primary)] text-[var(--text-primary)] hover:text-[var(--text-focus)] text-xs font-bold rounded border border-[var(--border-subtle)] hover:border-[var(--text-focus)] transition-all whitespace-nowrap">
                                    {selectedPayoff?.strategy_key === rec.key ? 'Hide Payoff ' : 'View Payoff & Greeks '}
                                </button>
                            </div>

                            {/* Inline Payoff Detail */}
                            {selectedPayoff && selectedPayoff.strategy_key === rec.key && (
                                <div className="mt-6 pt-6 border-t border-[var(--border-subtle)] animate-in slide-in-from-top-4 fade-in duration-300">
                                    <h3 className="text-lg font-bold text-[var(--text-primary)] mb-3"> Payoff Profile</h3>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 font-quant">
                                        <div className="text-center p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20"><p className="text-[10px] font-inter uppercase tracking-widest text-[var(--text-muted)] font-bold">Max Profit</p><p className="text-lg font-bold text-emerald-400">₹{typeof selectedPayoff.max_profit === 'number' ? selectedPayoff.max_profit.toLocaleString() : selectedPayoff.max_profit}</p></div>
                                        <div className="text-center p-3 bg-red-500/10 rounded-lg border border-red-500/20"><p className="text-[10px] font-inter uppercase tracking-widest text-[var(--text-muted)] font-bold">Max Loss</p><p className="text-lg font-bold text-red-400">₹{typeof selectedPayoff.max_loss === 'number' ? selectedPayoff.max_loss.toLocaleString() : selectedPayoff.max_loss}</p></div>
                                        <div className="text-center p-3 bg-blue-500/10 rounded-lg border border-blue-500/20"><p className="text-[10px] font-inter uppercase tracking-widest text-[var(--text-muted)] font-bold">Breakeven</p><p className="text-lg font-bold text-blue-500">₹{selectedPayoff.breakeven?.toLocaleString() ?? '-'}</p></div>
                                        <div className="text-center p-3 bg-purple-500/10 rounded-lg border border-purple-500/20"><p className="text-[10px] font-inter uppercase tracking-widest text-[var(--text-muted)] font-bold">Capital Req.</p><p className="text-lg font-bold text-purple-400">₹{selectedPayoff.capital_required?.toLocaleString() ?? '-'}</p></div>
                                    </div>
                                    <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2 mt-6">Execution Legs:</h4>
                                    <div className="space-y-2 mb-6">
                                        {selectedPayoff.legs?.map((l: any, i: number) => (
                                            <div key={i} className={`flex items-center gap-4 font-quant text-sm p-3 rounded-lg border ${l.action === 'BUY' ? 'bg-emerald-500/5 border-emerald-500/15' : 'bg-red-500/5 border-red-500/15'}`}>
                                                <Badge text={l.action} color={l.action === 'BUY' ? 'green' : 'red'} />
                                                <span className="text-[var(--text-primary)] font-semibold">{l.type} {l.strike}</span>
                                                <span className="ml-auto text-[var(--text-muted)]">@ ₹{l.premium?.toFixed(2)}</span>
                                            </div>
                                        ))}
                                    </div>
                                    <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Payoff Curve:</h4>
                                    <div className="overflow-x-auto"><div className="flex items-end gap-px h-32">
                                        {selectedPayoff.payoff_curve?.map((p: any, i: number) => {
                                            const maxAbs = Math.max(...selectedPayoff.payoff_curve.map((x: any) => Math.abs(x.pnl)), 1);
                                            const h = Math.abs(p.pnl) / maxAbs * 100;
                                            return <div key={i} title={`₹${p.price}: ₹${p.pnl}`} className={`flex-1 min-w-[3px] rounded-t ${p.pnl >= 0 ? 'bg-emerald-500' : 'bg-red-500'}`} style={{ height: `${Math.max(2, h)}%`, alignSelf: p.pnl >= 0 ? 'flex-end' : 'flex-start', marginTop: p.pnl < 0 ? 'auto' : undefined }} />;
                                        })}
                                    </div></div>
                                </div>
                            )}
                        </Card>
                    ))}
                </div>
            )}


        </div>
    );
}

/* 
   BACKTESTING TAB
    */
function BacktestTab() {
    const [strategy, setStrategy] = useState('bull_call_spread');
    const [years, setYears] = useState(1);
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [allResults, setAllResults] = useState<any[]>([]);

    const { guardYears, modal: planModal } = usePlanGate(1);

    const runBacktest = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/derivatives/backtest`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ strategy_key: strategy, years, holding_days: 20 }),
            });
            setResult(await res.json());
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const runAll = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/derivatives/backtest-all?years=${years}`);
            const data = await res.json();
            setAllResults(data.results || []);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const strategies = ['bull_call_spread', 'bear_put_spread', 'iron_condor', 'long_call', 'long_put', 'short_straddle', 'long_straddle', 'protective_put'];

    return (
        <div className="space-y-6">
            <Card>
                <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4"> Strategy Backtester</h3>
                <div className="flex flex-wrap gap-4 items-end">
                    <div>
                        <label className="block text-xs text-[var(--text-muted)] mb-1">Strategy</label>
                        <select value={strategy} onChange={e => setStrategy(e.target.value)}
                            className="bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)]">
                            {strategies.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ').toUpperCase()}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs text-[var(--text-muted)] mb-1">Years</label>
                        <select value={years} onChange={e => {
                            const v = Number(e.target.value);
                            if (guardYears(v)) setYears(v);
                        }}
                            className="bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)]">
                            <option value={1}>1 Year  Free</option>
                            <option value={2}> 2 Years — Pro</option>
                            <option value={3}> 3 Years — Pro</option>
                            <option value={5}> 5 Years — Pro</option>
                            <option value={10}> 10 Years — Elite</option>
                            <option value={15}> 15 Years — Elite</option>
                            <option value={99}> Max Available — Elite</option>
                        </select>
                    </div>
                    <button onClick={runBacktest} disabled={loading} className="px-4 py-2 bg-[var(--accent-indigo)] text-white text-sm font-semibold rounded-lg disabled:opacity-50">
                        {loading ? 'Running…' : 'Run Backtest'}
                    </button>
                    <button onClick={runAll} disabled={loading} className="px-4 py-2 bg-[var(--bg-card-hover)] text-[var(--text-primary)] text-sm font-semibold rounded-lg border border-[var(--border-subtle)] disabled:opacity-50">
                        Compare All
                    </button>
                </div>
            </Card>
            {planModal}

            {loading && <Spinner />}

            {result && !loading && (
                <Card>
                    <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4">Results: {result.strategy_key?.replace(/_/g, ' ').toUpperCase()}</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <KPI label="Win Rate" value={`${result.win_rate}%`} sub={`${result.wins}W / ${result.losses}L`} color={result.win_rate > 55 ? 'green' : 'red'} />
                        <KPI label="Sharpe Ratio" value={result.sharpe_ratio?.toFixed(2)} sub={result.sharpe_ratio > 1 ? 'Good' : 'Below avg'} color={result.sharpe_ratio > 1 ? 'green' : 'yellow'} />
                        <KPI label="Max Drawdown" value={`${result.max_drawdown_pct}%`} sub="" color="red" />
                        <KPI label="ROI" value={`${result.roi_pct}%`} sub={`vs Buy&Hold ${result.buy_hold_roi_pct}%`} color={result.roi_pct > 0 ? 'green' : 'red'} />
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <KPI label="Total P&L" value={`₹${result.total_pnl?.toLocaleString()}`} sub="" color={result.total_pnl > 0 ? 'green' : 'red'} />
                        <KPI label="Avg P&L/Trade" value={`₹${result.avg_pnl_per_trade?.toLocaleString()}`} sub="" color={result.avg_pnl_per_trade > 0 ? 'green' : 'red'} />
                        <KPI label="Avg Win" value={`₹${result.avg_win?.toLocaleString()}`} sub="" color="green" />
                        <KPI label="Avg Loss" value={`₹${result.avg_loss?.toLocaleString()}`} sub="" color="red" />
                    </div>
                    {/* Recent trades */}
                    <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Recent Trades (Last 15)</h4>
                    <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                            <thead><tr className="text-[var(--text-muted)] border-b border-[var(--border-subtle)]">
                                <th className="py-2 text-left">Entry</th><th className="text-left">Exit</th><th className="text-right">Entry ₹</th>
                                <th className="text-right">Exit ₹</th><th className="text-right">P&L</th><th className="text-right">Move%</th><th className="text-center">Result</th>
                            </tr></thead>
                            <tbody>
                                {result.recent_trades?.map((t: any, i: number) => (
                                    <tr key={i} className="border-b border-[var(--border-subtle)]/30 hover:bg-[var(--bg-card-hover)]">
                                        <td className="py-1.5 text-[var(--text-secondary)]">{t.entry_date}</td>
                                        <td className="text-[var(--text-secondary)]">{t.exit_date}</td>
                                        <td className="text-right">{t.entry_price?.toFixed(0)}</td>
                                        <td className="text-right">{t.exit_price?.toFixed(0)}</td>
                                        <td className={`text-right font-semibold ${t.pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>₹{t.pnl?.toFixed(0)}</td>
                                        <td className={`text-right ${t.spot_move_pct > 0 ? 'text-emerald-400' : 'text-red-400'}`}>{t.spot_move_pct?.toFixed(1)}%</td>
                                        <td className="text-center">{t.win ? '' : ''}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>
            )}

            {/* Compare All Results */}
            {allResults.length > 0 && !loading && (
                <Card>
                    <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4"> Strategy Comparison (Ranked by Sharpe)</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead><tr className="text-[var(--text-muted)] border-b border-[var(--border-subtle)]">
                                <th className="py-2 text-left">Strategy</th><th className="text-right">Win%</th><th className="text-right">Sharpe</th>
                                <th className="text-right">ROI%</th><th className="text-right">Max DD%</th><th className="text-right">Total P&L</th><th className="text-right">Trades</th>
                            </tr></thead>
                            <tbody>
                                {allResults.map((r: any, i: number) => (
                                    <tr key={i} className={`border-b border-[var(--border-subtle)]/30 hover:bg-[var(--bg-card-hover)] ${i === 0 ? 'bg-emerald-500/5' : ''}`}>
                                        <td className="py-2 font-medium text-[var(--text-primary)]">{i === 0 && ' '}{r.strategy_key?.replace(/_/g, ' ')}</td>
                                        <td className={`text-right ${r.win_rate > 55 ? 'text-emerald-400' : 'text-red-400'}`}>{r.win_rate}%</td>
                                        <td className={`text-right font-semibold ${r.sharpe_ratio > 1 ? 'text-emerald-400' : 'text-amber-400'}`}>{r.sharpe_ratio}</td>
                                        <td className={`text-right ${r.roi_pct > 0 ? 'text-emerald-400' : 'text-red-400'}`}>{r.roi_pct}%</td>
                                        <td className="text-right text-red-400">{r.max_drawdown_pct}%</td>
                                        <td className={`text-right ${r.total_pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>₹{r.total_pnl?.toLocaleString()}</td>
                                        <td className="text-right text-[var(--text-muted)]">{r.total_trades}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>
            )}
        </div>
    );
}

/* 
   ALERTS TAB
    */
function AlertsTab() {
    const [alerts, setAlerts] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const fetch_alerts = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/derivatives/alerts`);
            setAlerts(await res.json());
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetch_alerts(); }, []);

    const typeColors: Record<string, string> = {
        warning: 'border-l-red-500 bg-red-500/5',
        bullish: 'border-l-emerald-500 bg-emerald-500/5',
        extreme: 'border-l-amber-500 bg-amber-500/5',
        info: 'border-l-blue-500 bg-blue-500/5',
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-[var(--text-primary)]"> Real-Time Derivatives Alerts</h3>
                <button onClick={fetch_alerts} disabled={loading}
                    className="px-3 py-1.5 text-xs font-semibold bg-[var(--bg-card-hover)] text-[var(--text-primary)] rounded-lg border border-[var(--border-subtle)]">
                    {loading ? 'Checking…' : '↻ Refresh'}
                </button>
            </div>

            {loading && <Spinner />}

            {alerts?.snapshot_summary && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <KPI label="Spot" value={`₹${alerts.snapshot_summary.spot?.toLocaleString()}`} sub="" color="blue" />
                    <KPI label="PCR" value={alerts.snapshot_summary.pcr?.toFixed(2)} sub="" color="purple" />
                    <KPI label="Max Pain" value={`₹${alerts.snapshot_summary.max_pain?.toLocaleString()}`} sub="" color="blue" />
                    <KPI label="VIX" value={alerts.snapshot_summary.vix?.toFixed(1)} sub="" color={alerts.snapshot_summary.vix > 20 ? 'red' : 'green'} />
                    <KPI label="Forecast" value={alerts.snapshot_summary.forecast} sub="" color={alerts.snapshot_summary.forecast === 'BULLISH' ? 'green' : alerts.snapshot_summary.forecast === 'BEARISH' ? 'red' : 'yellow'} />
                </div>
            )}

            <div className="space-y-3">
                {alerts?.alerts?.map((a: any, i: number) => (
                    <div key={i} className={`border-l-4 rounded-lg p-4 ${typeColors[a.type] || typeColors.info}`}>
                        <div className="flex items-center gap-2 mb-1">
                            <Badge text={a.category} color="blue" />
                        </div>
                        <p className="text-sm font-medium text-[var(--text-primary)]">{a.message}</p>
                        <p className="text-xs text-[var(--text-muted)] mt-1"> {a.action}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
