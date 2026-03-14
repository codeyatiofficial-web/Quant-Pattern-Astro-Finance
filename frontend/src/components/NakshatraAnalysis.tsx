'use client';
import React, { useState } from 'react';
import { usePlanGate } from './UpgradeModal';
import CosmicSnapshotWidget from './CosmicSnapshotWidget';

const API = '';

const US_SYMBOLS = new Set([
    '^IXIC', '^GSPC', '^DJI', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META',
    'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'PL=F', 'PA=F', 'ALI=F', 'ZC=F', 'ZW=F',
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
    'ADA-USD', 'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'LINK-USD', 'MATIC-USD', 'LTC-USD',
]);

/*  Tiny helpers  */
function ReturnPill({ v }: { v: number | null }) {
    if (v == null) return <span className="num" style={{ color: 'var(--text-muted)' }}>—</span>;
    const cls = v > 0 ? 'bull' : v < 0 ? 'bear' : 'flat';
    const arrow = v > 0 ? '' : v < 0 ? '' : '';
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
    const icon = t === 'Bullish' ? '' : t === 'Bearish' ? '' : '';
    return <span className={`badge ${cls}`}>{icon} {t}</span>;
}

function RankBadge({ i }: { i: number }) {
    if (i > 2) return <span className="rank-badge" style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: 11 }}>{i + 1}</span>;
    const cls = i === 0 ? 'rank-1' : i === 1 ? 'rank-2' : 'rank-3';
    const label = i === 0 ? '1' : i === 1 ? '2' : '3';
    return <span className={`rank-badge ${cls}`}>{label}</span>;
}

function NumCell({ v, decimals = 4, suffix = '%' }: { v: number | null; decimals?: number; suffix?: string }) {
    if (v == null) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
    return <span className="num" style={{ color: 'var(--text-secondary)' }}>{v.toFixed(decimals)}{suffix}</span>;
}

type SubTab = 'all' | 'rise' | 'no_rise' | 'tithi' | 'stats' | 'planets';

const SUBTABS: { key: SubTab; label: string; emoji: string }[] = [
    { key: 'all', label: 'All Days', emoji: '' },
    { key: 'rise', label: 'Intraday Cycle', emoji: '' },
    { key: 'no_rise', label: 'Off-Cycle', emoji: '' },
    { key: 'tithi', label: 'By Lunar Phase', emoji: '' },
    { key: 'stats', label: 'Statistical Tests', emoji: '' },
    { key: 'planets', label: 'Signal Driver', emoji: '' },
];

export default function NakshatraAnalysis({ data, onAnalysisDone }: { data: any, onAnalysisDone?: (data: any) => void }) {
    const [sub, setSub] = useState<SubTab>('all');
    const { guardYears, requirePlan, modal: planModal } = usePlanGate(1);
    const [analysing, setAnalysing] = useState(false);
    const [symbol, setSymbol] = useState('^NSEI');
    const [planet, setPlanet] = useState('Moon');
    const [startDate, setStartDate] = useState(() => {
        const d = new Date();
        d.setFullYear(d.getFullYear() - 15);
        return d.toISOString().slice(0, 10);
    });
    const [endDate] = useState(new Date().toISOString().slice(0, 10));
    const [status, setStatus] = useState('');

    const market = US_SYMBOLS.has(symbol) ? 'NASDAQ' : 'NSE';

    const runAnalysis = async () => {
        if (!requirePlan(1)) return; // Requires PRO (tier 1) or higher

        setAnalysing(true);
        setStatus('Fetching market data & crunching AI signals…');
        try {
            const res = await fetch(`${API}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, planet, start_date: startDate, end_date: endDate, market }),
            });
            const newData = await res.json();
            if (onAnalysisDone) onAnalysisDone(newData);
            setStatus(' Analysis complete! Switching to results…');
        } catch {
            setStatus(' Error fetching data. Is the backend running?');
        }
        setAnalysing(false);
    };
    const renderNoData = () => {
        if (!data || Object.keys(data).length === 0) {
            return (
                <div style={{ padding: '40px 0' }}>
                    <CosmicSnapshotWidget />
                    <h1 className="section-title"> Cycle Pattern Analysis</h1>
                    <p className="section-subtitle">Run the composite signal backtest to see results.</p>
                </div>
            );
        }
        return null;
    };

    if (!data || Object.keys(data).length === 0) {
        return (
            <div className="fade-in">
                {planModal}
                {/*  Analysis Form Panel  */}
                <div className="glass-card" style={{ padding: 28, marginBottom: 24 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
                        <span style={{ fontSize: 20 }}></span>
                        <div>
                            <h2 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>Load Statistical Analysis</h2>
                            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Choose a market, planet, and date range — then run the composite signal backtest</p>
                        </div>
                        {market === 'NASDAQ' && (
                            <span className="badge badge-info" style={{ marginLeft: 'auto' }}> US / Global Market</span>
                        )}
                        {market === 'NSE' && (
                            <span className="badge badge-neutral" style={{ marginLeft: 'auto' }}> NSE India</span>
                        )}
                    </div>

                    <div className="grid-4" style={{ marginBottom: 20 }}>
                        {/* Market Symbol */}
                        <div>
                            <label className="form-label">Market Symbol</label>
                            <select className="form-select" value={symbol} onChange={e => setSymbol(e.target.value)}>
                                <optgroup label=" India — NSE">
                                    <option value="^NSEI">^NSEI (Nifty 50)</option>
                                    <option value="^NSEBANK">^NSEBANK (Bank Nifty)</option>
                                    <option value="^CNXIT">^CNXIT (Nifty IT)</option>
                                    <option value="RELIANCE.NS">RELIANCE.NS (Reliance)</option>
                                    <option value="TCS.NS">TCS.NS (TCS)</option>
                                    <option value="HDFCBANK.NS">HDFCBANK.NS (HDFC Bank)</option>
                                    <option value="INFY.NS">INFY.NS (Infosys)</option>
                                </optgroup>
                                <optgroup label=" USA — NASDAQ / NYSE">
                                    <option value="^IXIC">^IXIC (NASDAQ Composite)</option>
                                    <option value="^GSPC">^GSPC (S&amp;P 500)</option>
                                    <option value="^DJI">^DJI (Dow Jones)</option>
                                    <option value="AAPL">AAPL (Apple)</option>
                                    <option value="MSFT">MSFT (Microsoft)</option>
                                    <option value="NVDA">NVDA (NVIDIA)</option>
                                    <option value="TSLA">TSLA (Tesla)</option>
                                    <option value="AMZN">AMZN (Amazon)</option>
                                    <option value="GOOGL">GOOGL (Alphabet)</option>
                                    <option value="META">META (Meta)</option>
                                </optgroup>
                                <optgroup label="🪙 Precious Metals &amp; Commodities">
                                    <option value="GC=F">GC=F (Gold Futures)</option>
                                    <option value="SI=F">SI=F (Silver Futures)</option>
                                    <option value="PL=F">PL=F (Platinum Futures)</option>
                                    <option value="PA=F">PA=F (Palladium Futures)</option>
                                    <option value="HG=F">HG=F (Copper Futures)</option>
                                    <option value="ALI=F">ALI=F (Aluminium Futures)</option>
                                </optgroup>
                                <optgroup label=" Energy">
                                    <option value="CL=F">CL=F (Crude Oil WTI)</option>
                                    <option value="BZ=F">BZ=F (Brent Crude Oil)</option>
                                    <option value="NG=F">NG=F (Natural Gas)</option>
                                    <option value="ZC=F">ZC=F (Corn Futures)</option>
                                    <option value="ZW=F">ZW=F (Wheat Futures)</option>
                                </optgroup>
                                <optgroup label="₿ Cryptocurrency">
                                    <option value="BTC-USD">BTC-USD (Bitcoin)</option>
                                    <option value="ETH-USD">ETH-USD (Ethereum)</option>
                                    <option value="BNB-USD">BNB-USD (BNB)</option>
                                    <option value="SOL-USD">SOL-USD (Solana)</option>
                                    <option value="XRP-USD">XRP-USD (XRP)</option>
                                    <option value="ADA-USD">ADA-USD (Cardano)</option>
                                    <option value="DOGE-USD">DOGE-USD (Dogecoin)</option>
                                    <option value="AVAX-USD">AVAX-USD (Avalanche)</option>
                                    <option value="DOT-USD">DOT-USD (Polkadot)</option>
                                    <option value="LINK-USD">LINK-USD (Chainlink)</option>
                                    <option value="MATIC-USD">MATIC-USD (Polygon)</option>
                                    <option value="LTC-USD">LTC-USD (Litecoin)</option>
                                </optgroup>
                            </select>
                        </div>

                        {/* Planet */}
                        <div>
                            <label className="form-label">Planet / Body</label>
                            <select className="form-select" value={planet} onChange={e => setPlanet(e.target.value)}>
                                {['Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu'].map(p => (
                                    <option key={p} value={p}>{p}</option>
                                ))}
                            </select>
                        </div>

                        {/* Start Date */}
                        <div>
                            <label className="form-label">Start Date <span style={{ fontSize: 9, background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', padding: '2px 6px', borderRadius: 4, marginLeft: 6, fontWeight: 700, letterSpacing: 0.5 }}>FREE LIMIT: 1 YR</span></label>
                            <input className="form-input" type="date" value={startDate}
                                max={endDate}
                                onChange={e => {
                                    const start = new Date(e.target.value);
                                    const end = new Date(endDate);
                                    const diffYears = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24 * 365);
                                    if (guardYears(diffYears)) setStartDate(e.target.value);
                                }}
                            />
                        </div>

                        {/* End Date */}
                        <div>
                            <label className="form-label">End Date</label>
                            <input className="form-input" type="date" value={endDate} readOnly style={{ opacity: 0.65, cursor: 'not-allowed' }} />
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
                        <button className="btn-primary" onClick={runAnalysis} disabled={analysing} style={{ minWidth: 220 }}>
                            {analysing
                                ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Analyzing…</>
                                : <> Load & Analyze Data <span style={{ fontSize: 10, padding: '2px 6px', background: 'rgba(255,255,255,0.2)', borderRadius: 4, marginLeft: 6 }}>PRO</span></>
                            }
                        </button>
                        {status && (
                            <span style={{
                                fontSize: 13,
                                fontWeight: 600,
                                color: status.startsWith('') ? 'var(--accent-green)'
                                    : status.startsWith('') ? 'var(--accent-red)'
                                        : 'var(--accent-cyan)',
                                display: 'flex', alignItems: 'center', gap: 6,
                            }}>
                                {analysing && <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />}
                                {status}
                            </span>
                        )}
                    </div>
                </div>
                {renderNoData()}
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
            {planModal}

            {/*  Analysis Form Panel  */}
            <div className="glass-card" style={{ padding: 28, marginBottom: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
                    <span style={{ fontSize: 20 }}></span>
                    <div>
                        <h2 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>Load Statistical Analysis</h2>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Choose a market, planet, and date range — then run the composite signal backtest</p>
                    </div>
                    {market === 'NASDAQ' && (
                        <span className="badge badge-info" style={{ marginLeft: 'auto' }}> US / Global Market</span>
                    )}
                    {market === 'NSE' && (
                        <span className="badge badge-neutral" style={{ marginLeft: 'auto' }}> NSE India</span>
                    )}
                </div>

                <div className="grid-4" style={{ marginBottom: 20 }}>
                    {/* Market Symbol */}
                    <div>
                        <label className="form-label">Market Symbol</label>
                        <select className="form-select" value={symbol} onChange={e => setSymbol(e.target.value)}>
                            <optgroup label=" India — NSE">
                                <option value="^NSEI">^NSEI (Nifty 50)</option>
                                <option value="^NSEBANK">^NSEBANK (Bank Nifty)</option>
                                <option value="^CNXIT">^CNXIT (Nifty IT)</option>
                                <option value="RELIANCE.NS">RELIANCE.NS (Reliance)</option>
                                <option value="TCS.NS">TCS.NS (TCS)</option>
                                <option value="HDFCBANK.NS">HDFCBANK.NS (HDFC Bank)</option>
                                <option value="INFY.NS">INFY.NS (Infosys)</option>
                            </optgroup>
                            <optgroup label=" USA — NASDAQ / NYSE">
                                <option value="^IXIC">^IXIC (NASDAQ Composite)</option>
                                <option value="^GSPC">^GSPC (S&amp;P 500)</option>
                                <option value="^DJI">^DJI (Dow Jones)</option>
                                <option value="AAPL">AAPL (Apple)</option>
                                <option value="MSFT">MSFT (Microsoft)</option>
                                <option value="NVDA">NVDA (NVIDIA)</option>
                                <option value="TSLA">TSLA (Tesla)</option>
                                <option value="AMZN">AMZN (Amazon)</option>
                                <option value="GOOGL">GOOGL (Alphabet)</option>
                                <option value="META">META (Meta)</option>
                            </optgroup>
                            <optgroup label="🪙 Precious Metals &amp; Commodities">
                                <option value="GC=F">GC=F (Gold Futures)</option>
                                <option value="SI=F">SI=F (Silver Futures)</option>
                                <option value="PL=F">PL=F (Platinum Futures)</option>
                                <option value="PA=F">PA=F (Palladium Futures)</option>
                                <option value="HG=F">HG=F (Copper Futures)</option>
                                <option value="ALI=F">ALI=F (Aluminium Futures)</option>
                            </optgroup>
                            <optgroup label=" Energy">
                                <option value="CL=F">CL=F (Crude Oil WTI)</option>
                                <option value="BZ=F">BZ=F (Brent Crude Oil)</option>
                                <option value="NG=F">NG=F (Natural Gas)</option>
                                <option value="ZC=F">ZC=F (Corn Futures)</option>
                                <option value="ZW=F">ZW=F (Wheat Futures)</option>
                            </optgroup>
                            <optgroup label="₿ Cryptocurrency">
                                <option value="BTC-USD">BTC-USD (Bitcoin)</option>
                                <option value="ETH-USD">ETH-USD (Ethereum)</option>
                                <option value="BNB-USD">BNB-USD (BNB)</option>
                                <option value="SOL-USD">SOL-USD (Solana)</option>
                                <option value="XRP-USD">XRP-USD (XRP)</option>
                                <option value="ADA-USD">ADA-USD (Cardano)</option>
                                <option value="DOGE-USD">DOGE-USD (Dogecoin)</option>
                                <option value="AVAX-USD">AVAX-USD (Avalanche)</option>
                                <option value="DOT-USD">DOT-USD (Polkadot)</option>
                                <option value="LINK-USD">LINK-USD (Chainlink)</option>
                                <option value="MATIC-USD">MATIC-USD (Polygon)</option>
                                <option value="LTC-USD">LTC-USD (Litecoin)</option>
                            </optgroup>
                        </select>
                    </div>

                    {/* Planet */}
                    <div>
                        <label className="form-label">Planet / Body</label>
                        <select className="form-select" value={planet} onChange={e => setPlanet(e.target.value)}>
                            {['Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu'].map(p => (
                                <option key={p} value={p}>{p}</option>
                            ))}
                        </select>
                    </div>

                    {/* Start Date */}
                    <div>
                        <label className="form-label">Start Date <span style={{ fontSize: 9, background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', padding: '2px 6px', borderRadius: 4, marginLeft: 6, fontWeight: 700, letterSpacing: 0.5 }}>FREE LIMIT: 1 YR</span></label>
                        <input className="form-input" type="date" value={startDate}
                            max={endDate}
                            onChange={e => {
                                const start = new Date(e.target.value);
                                const end = new Date(endDate);
                                const diffYears = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24 * 365);
                                if (guardYears(diffYears)) setStartDate(e.target.value);
                            }}
                        />
                    </div>

                    {/* End Date */}
                    <div>
                        <label className="form-label">End Date</label>
                        <input className="form-input" type="date" value={endDate} readOnly style={{ opacity: 0.65, cursor: 'not-allowed' }} />
                    </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
                    <button className="btn-primary" onClick={runAnalysis} disabled={analysing} style={{ minWidth: 220 }}>
                        {analysing
                            ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Analyzing…</>
                            : <> Load & Analyze Data <span style={{ fontSize: 10, padding: '2px 6px', background: 'rgba(255,255,255,0.2)', borderRadius: 4, marginLeft: 6 }}>PRO</span></>
                        }
                    </button>
                    {status && (
                        <span style={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: status.startsWith('') ? 'var(--accent-green)'
                                : status.startsWith('') ? 'var(--accent-red)'
                                    : 'var(--accent-cyan)',
                            display: 'flex', alignItems: 'center', gap: 6,
                        }}>
                            {analysing && <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />}
                            {status}
                        </span>
                    )}
                </div>
            </div>

            {/*  Header  */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 20 }}>
                <div>
                    <h1 className="section-title"> Cycle Pattern Analysis</h1>
                    <p className="section-subtitle">
                        <span className="pulse-dot" style={{ marginRight: 7 }} />
                        {data.observations?.toLocaleString()} trading days analysed
                    </p>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <span className="stat-tag"> ANOVA: <strong style={{ marginLeft: 3 }}>{data.anova?.result ?? '—'}</strong></span>
                    <span className="stat-tag">χ² Test: <strong style={{ marginLeft: 3 }}>{data.chi2?.result ?? '—'}</strong></span>
                </div>
            </div>

            {/*  Sub-tabs  */}
            <div className="tab-list" style={{ marginBottom: 20 }}>
                {SUBTABS.map(s => (
                    <button key={s.key} className={`tab-btn ${sub === s.key ? 'active' : ''}`} onClick={() => setSub(s.key)}>
                        {s.emoji} {s.label}
                    </button>
                ))}
            </div>

            {/*  Cycle Pattern / Phase tables  */}
            {(isNak || isTithi) && (
                <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div style={{ overflowX: 'auto', maxHeight: 620, overflowY: 'auto' }}>
                        {isNak ? (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th style={{ width: 32 }}>#</th>
                                        <th>Cycle Pattern</th>
                                        <th>Cycle Driver</th>
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
                                        <th>Phase</th>
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

            {/*  Statistical Tests  */}
            {sub === 'stats' && (
                <div className="grid-2" style={{ gap: 20 }}>
                    {[
                        {
                            title: ' ANOVA Test',
                            sub: 'Are mean returns significantly different across cycle patterns?',
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
                            title: ' Chi-Square Test',
                            sub: 'Is market direction independent of cycle pattern?',
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

            {/*  Planet / Element  */}
            {sub === 'planets' && (
                <div className="grid-2" style={{ gap: 20 }}>
                    {[
                        { title: ' Signal Driver Returns', rows: data.planet_analysis || [], nameKey: 'ruling_planet' },
                        { title: ' Element Returns', rows: data.element_analysis || [], nameKey: 'element' },
                    ].map((section, si) => (
                        <div key={si} className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
                            <div style={{ padding: '18px 22px', borderBottom: '1px solid var(--border-subtle)' }}>
                                <h3 style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>{section.title}</h3>
                            </div>
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>{si === 0 ? 'Driver' : 'Element'}</th>
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
