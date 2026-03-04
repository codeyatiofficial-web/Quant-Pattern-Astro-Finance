'use client';
import React, { useState, useEffect } from 'react';

const API = 'http://localhost:8000';

interface TodayInsight {
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

// US / Global market symbols — used to auto-detect the correct market flag
const US_SYMBOLS = new Set([
    // US Equities
    '^IXIC', '^GSPC', '^DJI', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META',
    // Commodities
    'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'PL=F', 'PA=F', 'ALI=F', 'ZC=F', 'ZW=F',
    // Cryptocurrency
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
    'ADA-USD', 'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'LINK-USD', 'MATIC-USD', 'LTC-USD',
]);

function TendencyBadge({ t }: { t: string }) {
    const cls = t === 'Bullish' ? 'badge-bullish' : t === 'Bearish' ? 'badge-bearish' : 'badge-neutral';
    const icon = t === 'Bullish' ? '▲' : t === 'Bearish' ? '▼' : '●';
    return <span className={`badge ${cls}`}>{icon} {t}</span>;
}

function MetricCard({ label, value, sub, color, icon }: {
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

export default function Dashboard({ onAnalysisDone }: { onAnalysisDone: (data: any) => void }) {
    const [insight, setInsight] = useState<TodayInsight | null>(null);
    const [loading, setLoading] = useState(true);
    const [analysing, setAnalysing] = useState(false);
    const [symbol, setSymbol] = useState('^NSEI');
    const [planet, setPlanet] = useState('Moon');
    const [startDate, setStartDate] = useState('2015-01-01');
    const [endDate] = useState(new Date().toISOString().slice(0, 10));
    const [status, setStatus] = useState('');

    const market = US_SYMBOLS.has(symbol) ? 'NASDAQ' : 'NSE';

    useEffect(() => {
        fetch(`${API}/api/insight/today`)
            .then(r => r.json())
            .then(d => { setInsight(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, []);

    const runAnalysis = async () => {
        setAnalysing(true);
        setStatus('Fetching market data & crunching Nakshatras…');
        try {
            const res = await fetch(`${API}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, planet, start_date: startDate, end_date: endDate, market }),
            });
            const data = await res.json();
            onAnalysisDone(data);
            setStatus('✅ Analysis complete! Switching to results…');
        } catch {
            setStatus('❌ Error fetching data. Is the backend running?');
        }
        setAnalysing(false);
    };

    const tendency = insight?.historical_tendency ?? 'Neutral';

    return (
        <div className="fade-in">
            {/* ── Page Header ── */}
            <div style={{ marginBottom: 24 }}>
                <h1 className="section-title">🌙 Astro-Finance Dashboard</h1>
                <p className="section-subtitle">
                    Correlating Moon's journey through 27 Vedic Nakshatras with global market movements
                </p>
            </div>

            {/* ── Today's Cosmic Snapshot ── */}
            {loading ? (
                <div className="panel" style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
                    <span className="spinner" />
                    <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading today's cosmic data…</span>
                </div>
            ) : insight ? (
                <>
                    {/* ── 4-card metrics row ── */}
                    <div className="grid-4" style={{ marginBottom: 18 }}>
                        <MetricCard
                            icon="🌙"
                            label="Current Nakshatra"
                            value={<span className="gradient-text" style={{ fontSize: 20, fontWeight: 800 }}>{insight.current_nakshatra}</span>}
                            sub={insight.nakshatra_sanskrit}
                        />
                        <MetricCard
                            icon="⭐"
                            label="Pada / Planet"
                            value={<span className="gradient-text" style={{ fontSize: 20, fontWeight: 800 }}>Pada {insight.pada}</span>}
                            sub={insight.ruling_planet}
                        />
                        <MetricCard
                            icon="📐"
                            label="Sidereal Longitude"
                            value={
                                typeof insight.moon_longitude === 'number'
                                    ? <span className="num" style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent-cyan)' }}>{insight.moon_longitude.toFixed(2)}°</span>
                                    : <span style={{ color: 'var(--text-muted)' }}>—</span>
                            }
                            sub="Moon sidereal position"
                        />
                        <MetricCard
                            icon="📈"
                            label="Historical Tendency"
                            value={<TendencyBadge t={tendency} />}
                            sub="Based on historical data"
                        />
                    </div>

                    {/* ── Secondary info row ── */}
                    {(insight.tithi_name || insight.yoga_name) && (
                        <div className="grid-3" style={{ marginBottom: 18 }}>
                            {insight.tithi_name && (
                                <MetricCard icon="🌒" label="Tithi" value={
                                    <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-gold)' }}>{insight.tithi_name}</span>
                                } sub={insight.paksha ?? ''} />
                            )}
                            {insight.yoga_name && (
                                <MetricCard icon="🔮" label="Nitya Yoga" value={
                                    <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-purple)' }}>{insight.yoga_name}</span>
                                } sub="Active yoga period" />
                            )}
                            <MetricCard icon="🌿" label="Ruling Planet" value={
                                <span style={{ fontSize: 18, fontWeight: 800, color: 'var(--accent-violet)' }}>{insight.ruling_planet}</span>
                            } sub="Nakshatra lord" />
                        </div>
                    )}

                    {/* ── Insight traits box ── */}
                    {insight.favorable_for && (
                        <div className="glass-card" style={{ padding: '18px 22px', marginBottom: 16 }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 24px' }}>
                                <div>
                                    <span style={{ color: 'var(--accent-green)', fontWeight: 700, fontSize: 12.5 }}>✅ Favorable for</span>
                                    <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {(insight.favorable_for || []).join(', ')}
                                    </p>
                                </div>
                                <div>
                                    <span style={{ color: 'var(--accent-red)', fontWeight: 700, fontSize: 12.5 }}>❌ Unfavorable for</span>
                                    <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {(insight.unfavorable_for || []).join(', ')}
                                    </p>
                                </div>
                                <div>
                                    <span style={{ color: 'var(--accent-gold)', fontWeight: 700, fontSize: 12.5 }}>🎯 Financial Traits</span>
                                    <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {(insight.financial_traits || []).join(', ')}
                                    </p>
                                </div>
                                <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                                    <div>
                                        <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: 12.5 }}>🔢 Lucky Numbers</span>
                                        <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
                                            {(insight.lucky_numbers || []).join(', ')}
                                        </p>
                                    </div>
                                    <div>
                                        <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: 12.5 }}>🎨 Lucky Colors</span>
                                        <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
                                            {(insight.lucky_colors || []).join(', ')}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ── Nakshatra transition ── */}
                    {insight.transition && (
                        <div className="alert-info" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
                            <span style={{ fontSize: 18 }}>🔄</span>
                            <span>
                                <strong>Nakshatra Transition Today:</strong>{' '}
                                <span style={{ color: 'var(--accent-red)' }}>{insight.transition.from_nakshatra}</span>
                                {' → '}
                                <span style={{ color: 'var(--accent-green)' }}>{insight.transition.to_nakshatra}</span>
                                {' at '}
                                <span className="num" style={{ color: 'var(--accent-gold)', fontWeight: 600 }}>{insight.transition.transition_time}</span>
                            </span>
                        </div>
                    )}
                </>
            ) : (
                <div className="alert-warn" style={{ marginBottom: 20 }}>⚠️ Could not load today's insight. Check backend connection.</div>
            )}

            {/* ── Analysis Form Panel ── */}
            <div className="glass-card" style={{ padding: 28 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
                    <span style={{ fontSize: 20 }}>📥</span>
                    <div>
                        <h2 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>Load Statistical Analysis</h2>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Choose a market, planet, and date range — then run the Nakshatra backtest</p>
                    </div>
                    {market === 'NASDAQ' && (
                        <span className="badge badge-info" style={{ marginLeft: 'auto' }}>🇺🇸 US / Global Market</span>
                    )}
                    {market === 'NSE' && (
                        <span className="badge badge-neutral" style={{ marginLeft: 'auto' }}>🇮🇳 NSE India</span>
                    )}
                </div>

                <div className="grid-4" style={{ marginBottom: 20 }}>
                    {/* Market Symbol */}
                    <div>
                        <label className="form-label">Market Symbol</label>
                        <select className="form-select" value={symbol} onChange={e => setSymbol(e.target.value)}>
                            <optgroup label="🇮🇳 India — NSE">
                                <option value="^NSEI">^NSEI (Nifty 50)</option>
                                <option value="^NSEBANK">^NSEBANK (Bank Nifty)</option>
                                <option value="^CNXIT">^CNXIT (Nifty IT)</option>
                                <option value="RELIANCE.NS">RELIANCE.NS (Reliance)</option>
                                <option value="TCS.NS">TCS.NS (TCS)</option>
                                <option value="HDFCBANK.NS">HDFCBANK.NS (HDFC Bank)</option>
                                <option value="INFY.NS">INFY.NS (Infosys)</option>
                            </optgroup>
                            <optgroup label="🇺🇸 USA — NASDAQ / NYSE">
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
                            <optgroup label="🛢️ Energy">
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
                        <label className="form-label">Start Date</label>
                        <input className="form-input" type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
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
                            : '🚀 Load & Analyze Data'
                        }
                    </button>
                    {status && (
                        <span style={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: status.startsWith('✅') ? 'var(--accent-green)'
                                : status.startsWith('❌') ? 'var(--accent-red)'
                                    : 'var(--accent-cyan)',
                            display: 'flex', alignItems: 'center', gap: 6,
                        }}>
                            {analysing && <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />}
                            {status}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
