'use client';
import React, { useState } from 'react';

const API = 'http://localhost:8000';

function ReturnCell({ v }: { v: number | null }) {
    if (v == null) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
    const color = v > 0 ? 'var(--accent-green)' : v < 0 ? 'var(--accent-red)' : 'var(--text-muted)';
    return <span style={{ color, fontWeight: 600 }}>{v > 0 ? '+' : ''}{v.toFixed(3)}%</span>;
}

// ── Comprehensive event type groups ─────────────────────────────────────────────
const EVENT_GROUPS = [
    {
        group: '⚙️ Planet Motion',
        desc: 'Planetary speed & direction states',
        color: '#6366f1',
        events: [
            { value: 'Retrograde', label: '↩ Retrograde', note: 'Planet moving backward' },
            { value: 'Direct', label: '→ Direct', note: 'Planet moving forward' },
            { value: 'High Speed', label: '⚡ High Speed', note: 'Top 20% orbital velocity' },
            { value: 'Exalted', label: '⬆️ Exalted', note: 'Planet in exaltation sign' },
            { value: 'Debilitated', label: '⬇️ Debilitated', note: 'Planet in debilitation sign' },
            { value: 'Own House', label: '🏠 Own House', note: 'Planet in own sign' },
        ],
    },
    {
        group: '🔥 Malefic Conjunction Yogas',
        desc: 'Challenging planetary combinations',
        color: '#ef4444',
        events: [
            { value: 'Angarak_Yoga', label: '🔥 Angarak Yoga', note: 'Mars + Rahu' },
            { value: 'Guru_Chandal_Yoga', label: '☠️ Guru Chandal', note: 'Jupiter + Rahu' },
            { value: 'Vish_Yoga', label: '☠️ Vish Yoga', note: 'Moon + Saturn' },
            { value: 'Yama_Yoga', label: '⚔️ Yama Yoga', note: 'Mars + Saturn' },
            { value: 'Surya_Shani_Yoga', label: '☀️🪐 Surya-Shani', note: 'Sun + Saturn' },
            { value: 'Surya_Mangal_Yoga', label: '☀️♂️ Surya-Mangal', note: 'Sun + Mars' },
            { value: 'Chandra_Mangal_Yoga', label: '🌙♂️ Chandra-Mangal', note: 'Moon + Mars' },
            { value: 'Chandra_Shani_Yoga', label: '🌙🪐 Chandra-Shani', note: 'Moon + Saturn' },
            { value: 'Chandal_Venus', label: '♀️🐍 Chandal Venus', note: 'Venus + Rahu' },
            { value: 'Shani_Rahu', label: '🪐🐍 Shani-Rahu', note: 'Saturn + Rahu (Shrapit)' },
            { value: 'Shani_Ketu', label: '🪐🔱 Shani-Ketu', note: 'Saturn + Ketu' },
        ],
    },
    {
        group: '✨ Benefic Conjunction Yogas',
        desc: 'Favorable planetary combinations',
        color: '#10b981',
        events: [
            { value: 'Budh_Aditya_Yoga', label: '☿☀️ Budh-Aditya', note: 'Mercury + Sun' },
            { value: 'Gajakesari_Yoga', label: '🐘 Gajakesari', note: 'Moon + Jupiter (same sign)' },
            { value: 'Gajakesari_Kendra', label: '🐘🔲 Gajakesari Kendra', note: 'Jupiter in Kendra to Moon' },
            { value: 'Shukra_Guru_Yoga', label: '♀️♃ Shukra-Guru', note: 'Venus + Jupiter' },
            { value: 'Guru_Mangal_Yoga', label: '♃♂️ Guru-Mangal', note: 'Jupiter + Mars' },
            { value: 'Bhrigu_Mangal_Yoga', label: '♀️♂️ Bhrigu-Mangal', note: 'Venus + Mars' },
            { value: 'Clash_Of_Gurus', label: '⚖️ Clash of Gurus', note: 'Jupiter + Venus (same sign)' },
            { value: 'Budh_Shani_Yoga', label: '☿🪐 Budh-Shani', note: 'Mercury + Saturn' },
            { value: 'Guru_Ketu', label: '♃🔱 Guru-Ketu', note: 'Jupiter + Ketu' },
        ],
    },
    {
        group: '👑 Pancha Mahapurusha Yogas',
        desc: 'Five great person yogas by planet in power',
        color: '#f59e0b',
        events: [
            { value: 'Shasha_Yoga', label: '🪐 Shasha Yoga', note: 'Saturn in Libra/Cap/Aqua' },
            { value: 'Malavya_Yoga', label: '♀️ Malavya Yoga', note: 'Venus in Taurus/Libra/Pisces' },
            { value: 'Ruchaka_Yoga', label: '♂️ Ruchaka Yoga', note: 'Mars in Aries/Scorpio/Cap' },
            { value: 'Hamsa_Yoga', label: '♃ Hamsa Yoga', note: 'Jupiter in Cancer/Sag/Pisces' },
            { value: 'Bhadra_Yoga', label: '☿ Bhadra Yoga', note: 'Mercury in Gemini/Virgo' },
            { value: 'Neech_Bhang_Raj_Yoga', label: '♻️ Neech Bhang Raj', note: 'Debilitated planet saved' },
        ],
    },
    {
        group: '🌑 Eclipse & Node Yogas',
        desc: 'Solar/Lunar eclipses and Rahu-Ketu formations',
        color: '#dc2626',
        events: [
            { value: 'Solar_Eclipse', label: '🌑 Solar Eclipse', note: 'New Moon + Rahu/Ketu <18°' },
            { value: 'Lunar_Eclipse', label: '🌕 Lunar Eclipse', note: 'Full Moon + Rahu/Ketu <18°' },
            { value: 'Grahan_Yoga', label: '🌗 Grahan Yoga', note: 'Any planet within 9° of nodes' },
            { value: 'Kaal_Sarp_Dosh', label: '🐍 Kaal Sarp Dosh', note: 'All 7 planets hemmed by nodes' },
            { value: 'Sarp_Dosh', label: '🐍 Sarp Dosh', note: '2+ malefics in same sign' },
            { value: 'Rahu_Ketu_Axis_Sun', label: '☀️🐍 Sun on Node Axis', note: 'Sun within 10° of Rahu/Ketu' },
            { value: 'Rahu_Ketu_Axis_Moon', label: '🌙🐍 Moon on Node Axis', note: 'Moon within 10° of Rahu/Ketu' },
            { value: 'Rahu_Ketu_Axis_Mars', label: '♂️🐍 Mars on Node Axis', note: 'Mars within 10° of Rahu/Ketu' },
        ],
    },
    {
        group: '🌙 Moon Phase Yogas',
        desc: 'Lunar cycle formations',
        color: '#8b5cf6',
        events: [
            { value: 'Amavasya_Defect', label: '🌑 Amavasya', note: 'New Moon (Sun+Moon <12°)' },
            { value: 'Purnima_Yoga', label: '🌕 Purnima', note: 'Full Moon (Sun-Moon ~180°)' },
            { value: 'Paksha_Sandi', label: '🌓 Paksha Sandi', note: 'Moon at waxing/waning boundary' },
            { value: 'Paap_Kartari_Moon', label: '🌙⚔️ Paap Kartari Moon', note: 'Moon hemmed by malefics' },
        ],
    },
    {
        group: '🔥 Combustion Yogas',
        desc: 'Planets hidden/weakened by proximity to Sun',
        color: '#f97316',
        events: [
            { value: 'Mercury_Combust', label: '☿🔥 Mercury Combust', note: 'Mercury within 14° of Sun' },
            { value: 'Venus_Combust', label: '♀️🔥 Venus Combust', note: 'Venus within 10° of Sun' },
            { value: 'Mars_Combust', label: '♂️🔥 Mars Combust', note: 'Mars within 17° of Sun' },
            { value: 'Jupiter_Combust', label: '♃🔥 Jupiter Combust', note: 'Jupiter within 11° of Sun' },
            { value: 'Saturn_Combust', label: '🪐🔥 Saturn Combust', note: 'Saturn within 15° of Sun' },
            { value: 'Multiple_Retrograde', label: '↩↩ Multiple Retrograde', note: '3+ planets retrograde simultaneously' },
        ],
    },
];

// Planet motion events that need a specific planet (NOT yoga events)
const PLANET_MOTION_EVENTS = ['Retrograde', 'Direct', 'High Speed', 'Exalted', 'Debilitated', 'Own House'];
// Flatten all yoga events for lookup (exclude planet motion events that need a specific planet)
const ALL_YOGA_EVENTS = EVENT_GROUPS.flatMap(g => g.events.map(e => e.value)).filter(v => !PLANET_MOTION_EVENTS.includes(v));

export default function AstroCorrelation() {
    const [symbol, setSymbol] = useState('^NSEI');
    const [planet, setPlanet] = useState('Mercury');
    const [eventType, setEventType] = useState('Retrograde');
    const [years, setYears] = useState(10);
    const [forwardDays, setForwardDays] = useState(0);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');
    const [groupFilter, setGroupFilter] = useState('All');

    const [vixPlanet, setVixPlanet] = useState('Mercury');
    const [vixEvent, setVixEvent] = useState('Retrograde');
    const [vixYears, setVixYears] = useState(10);
    const [vixLoading, setVixLoading] = useState(false);
    const [vixResult, setVixResult] = useState<any>(null);
    const [vixError, setVixError] = useState('');

    const [sub, setSub] = useState<'backtest' | 'vix'>('backtest');

    const US_GLOBAL = new Set([
        '^IXIC', '^GSPC', '^DJI', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META',
        'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'PL=F', 'PA=F', 'ALI=F', 'ZC=F', 'ZW=F',
        'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD',
        'AVAX-USD', 'DOT-USD', 'LINK-USD', 'MATIC-USD', 'LTC-USD',
    ]);
    const derivedMarket = US_GLOBAL.has(symbol) ? 'NASDAQ' : 'NSE';
    const PLANETS = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Sun', 'Moon', 'Rahu', 'Ketu'];

    const isYogaEvent = ALL_YOGA_EVENTS.includes(eventType);
    // For yoga events planet is "Multiple" (handled by backend), for motion events planet matters
    const planetRequired = !isYogaEvent;

    const runBacktest = async () => {
        setLoading(true); setError(''); setResult(null);
        try {
            const res = await fetch(`${API}/api/correlation/event-backtest`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, planet: planetRequired ? planet : 'Multiple', event_type: eventType, years, forward_days: forwardDays, market: derivedMarket }),
            });
            const data = await res.json();
            if (!res.ok || data.error) setError(data.error || data.detail || 'Error');
            else setResult(data);
        } catch { setError('Network error – is backend running?'); }
        setLoading(false);
    };

    const runVixBacktest = async () => {
        setVixLoading(true); setVixError(''); setVixResult(null);
        try {
            const isYv = ALL_YOGA_EVENTS.includes(vixEvent);
            const res = await fetch(`${API}/api/vix/event-backtest`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ planet: isYv ? 'Multiple' : vixPlanet, event_type: vixEvent, years: vixYears, forward_days: 0 }),
            });
            const data = await res.json();
            if (!res.ok || data.error) setVixError(data.error || data.detail || 'Error');
            else setVixResult(data);
        } catch { setVixError('Network error'); }
        setVixLoading(false);
    };

    // Currently chosen group info
    const chosenGroup = EVENT_GROUPS.find(g => g.events.some(e => e.value === eventType));
    const chosenEvent = EVENT_GROUPS.flatMap(g => g.events).find(e => e.value === eventType);
    const chosenVixGroup = EVENT_GROUPS.find(g => g.events.some(e => e.value === vixEvent));
    const chosenVixEvent = EVENT_GROUPS.flatMap(g => g.events).find(e => e.value === vixEvent);

    const filteredGroups = groupFilter === 'All' ? EVENT_GROUPS : EVENT_GROUPS.filter(g => g.group === groupFilter);

    function EventPicker({ activeEvent, onPick }: { activeEvent: string; onPick: (v: string) => void }) {
        return (
            <div style={{ marginBottom: 20 }}>
                {/* Group filter tabs */}
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
                    <button onClick={() => setGroupFilter('All')} style={{ padding: '5px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600, border: `1px solid ${groupFilter === 'All' ? '#8b5cf6' : 'rgba(255,255,255,0.1)'}`, background: groupFilter === 'All' ? 'rgba(139,92,246,0.2)' : 'transparent', color: groupFilter === 'All' ? 'white' : 'var(--text-muted)', cursor: 'pointer' }}>All</button>
                    {EVENT_GROUPS.map(g => (
                        <button key={g.group} onClick={() => setGroupFilter(g.group)} style={{ padding: '5px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600, border: `1px solid ${groupFilter === g.group ? g.color : 'rgba(255,255,255,0.1)'}`, background: groupFilter === g.group ? `${g.color}20` : 'transparent', color: groupFilter === g.group ? 'white' : 'var(--text-muted)', cursor: 'pointer' }}>
                            {g.group.split(' ').slice(0, 2).join(' ')}
                        </button>
                    ))}
                </div>
                {/* Event grid */}
                {filteredGroups.map(g => (
                    <div key={g.group} style={{ marginBottom: 16 }}>
                        <div style={{ fontSize: 12, fontWeight: 700, color: g.color, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                            {g.group}
                            <span style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 400 }}>{g.desc}</span>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 6 }}>
                            {g.events.map(ev => (
                                <button key={ev.value} onClick={() => onPick(ev.value)}
                                    style={{
                                        padding: '8px 12px', borderRadius: 8, textAlign: 'left', cursor: 'pointer',
                                        border: `1px solid ${activeEvent === ev.value ? g.color : 'rgba(255,255,255,0.06)'}`,
                                        background: activeEvent === ev.value ? `${g.color}20` : 'rgba(255,255,255,0.02)',
                                        transition: 'all 0.15s',
                                    }}>
                                    <div style={{ fontSize: 12, fontWeight: 600, color: activeEvent === ev.value ? 'white' : 'var(--text-primary)', marginBottom: 2 }}>{ev.label}</div>
                                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{ev.note}</div>
                                </button>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    return (
        <div>
            <h1 className="section-title">🌌 Astro-Correlation Engine</h1>
            <p className="section-subtitle">
                Backtesting all 9 planets · 44 Yoga types · Solar & Lunar Eclipses · Market & VIX reactions
            </p>

            <div className="tab-list" style={{ marginBottom: 20 }}>
                <button className={`tab-btn ${sub === 'backtest' ? 'active' : ''}`} onClick={() => setSub('backtest')}>📊 Market Backtest</button>
                <button className={`tab-btn ${sub === 'vix' ? 'active' : ''}`} onClick={() => setSub('vix')}>🌡️ VIX Backtest</button>
            </div>

            {sub === 'backtest' && (
                <div>
                    <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ fontWeight: 700, marginBottom: 4, fontSize: 16 }}>Configure Planetary + Yoga Backtest</h3>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 20 }}>
                            Select any yoga / planetary state below · {ALL_YOGA_EVENTS.length} yoga types across 7 categories
                        </p>

                        {/* Symbol, Planet (if applicable), Lookback, Forward */}
                        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 20, alignItems: 'flex-end' }}>
                            <div style={{ minWidth: 150 }}>
                                <label className="form-label">Symbol</label>
                                <select className="form-select" value={symbol} onChange={e => setSymbol(e.target.value)}>
                                    <optgroup label="🇮🇳 NSE Indices">
                                        <option value="^NSEI">^NSEI — Nifty 50</option>
                                        <option value="^NSEBANK">^NSEBANK — Bank Nifty</option>
                                        <option value="^CNXIT">^CNXIT — Nifty IT</option>
                                        <option value="^CNXAUTO">^CNXAUTO — Nifty Auto</option>
                                        <option value="^CNXFMCG">^CNXFMCG — Nifty FMCG</option>
                                        <option value="^CNXPHARMA">^CNXPHARMA — Nifty Pharma</option>
                                        <option value="^CNXMETAL">^CNXMETAL — Nifty Metal</option>
                                        <option value="^CNXREALTY">^CNXREALTY — Nifty Realty</option>
                                        <option value="^CNXENERGY">^CNXENERGY — Nifty Energy</option>
                                        <option value="^INDIAVIX">^INDIAVIX — India VIX</option>
                                    </optgroup>
                                    <optgroup label="🇮🇳 Nifty 50 Stocks">
                                        <option value="RELIANCE.NS">RELIANCE.NS</option>
                                        <option value="TCS.NS">TCS.NS</option>
                                        <option value="HDFCBANK.NS">HDFCBANK.NS</option>
                                        <option value="INFY.NS">INFY.NS</option>
                                        <option value="ICICIBANK.NS">ICICIBANK.NS</option>
                                        <option value="HINDUNILVR.NS">HINDUNILVR.NS</option>
                                        <option value="SBIN.NS">SBIN.NS</option>
                                        <option value="BHARTIARTL.NS">BHARTIARTL.NS</option>
                                        <option value="ITC.NS">ITC.NS</option>
                                        <option value="KOTAKBANK.NS">KOTAKBANK.NS</option>
                                        <option value="LT.NS">LT.NS</option>
                                        <option value="AXISBANK.NS">AXISBANK.NS</option>
                                        <option value="BAJFINANCE.NS">BAJFINANCE.NS</option>
                                        <option value="ASIANPAINT.NS">ASIANPAINT.NS</option>
                                        <option value="MARUTI.NS">MARUTI.NS</option>
                                        <option value="TITAN.NS">TITAN.NS</option>
                                        <option value="SUNPHARMA.NS">SUNPHARMA.NS</option>
                                        <option value="WIPRO.NS">WIPRO.NS</option>
                                        <option value="HCLTECH.NS">HCLTECH.NS</option>
                                        <option value="ULTRACEMCO.NS">ULTRACEMCO.NS</option>
                                        <option value="ADANIENT.NS">ADANIENT.NS</option>
                                        <option value="ADANIPORTS.NS">ADANIPORTS.NS</option>
                                        <option value="TATAMOTORS.NS">TATAMOTORS.NS</option>
                                        <option value="TATASTEEL.NS">TATASTEEL.NS</option>
                                        <option value="JSWSTEEL.NS">JSWSTEEL.NS</option>
                                        <option value="NTPC.NS">NTPC.NS</option>
                                        <option value="POWERGRID.NS">POWERGRID.NS</option>
                                        <option value="ONGC.NS">ONGC.NS</option>
                                        <option value="COALINDIA.NS">COALINDIA.NS</option>
                                        <option value="GRASIM.NS">GRASIM.NS</option>
                                        <option value="TECHM.NS">TECHM.NS</option>
                                        <option value="CIPLA.NS">CIPLA.NS</option>
                                        <option value="HEROMOTOCO.NS">HEROMOTOCO.NS</option>
                                        <option value="DRREDDY.NS">DRREDDY.NS</option>
                                        <option value="BPCL.NS">BPCL.NS</option>
                                        <option value="EICHERMOT.NS">EICHERMOT.NS</option>
                                        <option value="DIVISLAB.NS">DIVISLAB.NS</option>
                                        <option value="SBILIFE.NS">SBILIFE.NS</option>
                                        <option value="HDFCLIFE.NS">HDFCLIFE.NS</option>
                                        <option value="APOLLOHOSP.NS">APOLLOHOSP.NS</option>
                                        <option value="TRENT.NS">TRENT.NS</option>
                                        <option value="BAJAJFINSV.NS">BAJAJFINSV.NS</option>
                                        <option value="INDUSINDBK.NS">INDUSINDBK.NS</option>
                                    </optgroup>
                                    <optgroup label="🇺🇸 USA — NASDAQ / NYSE">
                                        <option value="^IXIC">^IXIC — NASDAQ Composite</option>
                                        <option value="^GSPC">^GSPC — S&amp;P 500</option>
                                        <option value="^DJI">^DJI — Dow Jones</option>
                                        <option value="AAPL">AAPL — Apple</option>
                                        <option value="MSFT">MSFT — Microsoft</option>
                                        <option value="NVDA">NVDA — NVIDIA</option>
                                        <option value="TSLA">TSLA — Tesla</option>
                                        <option value="AMZN">AMZN — Amazon</option>
                                        <option value="GOOGL">GOOGL — Alphabet</option>
                                        <option value="META">META — Meta</option>
                                    </optgroup>
                                    <optgroup label="🪙 Precious Metals">
                                        <option value="GC=F">GC=F — Gold</option>
                                        <option value="SI=F">SI=F — Silver</option>
                                        <option value="PL=F">PL=F — Platinum</option>
                                        <option value="PA=F">PA=F — Palladium</option>
                                        <option value="HG=F">HG=F — Copper</option>
                                        <option value="ALI=F">ALI=F — Aluminium</option>
                                    </optgroup>
                                    <optgroup label="🛢️ Energy &amp; Commodities">
                                        <option value="CL=F">CL=F — Crude Oil WTI</option>
                                        <option value="BZ=F">BZ=F — Brent Crude</option>
                                        <option value="NG=F">NG=F — Natural Gas</option>
                                        <option value="ZC=F">ZC=F — Corn</option>
                                        <option value="ZW=F">ZW=F — Wheat</option>
                                    </optgroup>
                                    <optgroup label="₿ Cryptocurrency">
                                        <option value="BTC-USD">BTC-USD — Bitcoin</option>
                                        <option value="ETH-USD">ETH-USD — Ethereum</option>
                                        <option value="BNB-USD">BNB-USD — BNB</option>
                                        <option value="SOL-USD">SOL-USD — Solana</option>
                                        <option value="XRP-USD">XRP-USD — XRP</option>
                                        <option value="ADA-USD">ADA-USD — Cardano</option>
                                        <option value="DOGE-USD">DOGE-USD — Dogecoin</option>
                                        <option value="AVAX-USD">AVAX-USD — Avalanche</option>
                                        <option value="DOT-USD">DOT-USD — Polkadot</option>
                                        <option value="LINK-USD">LINK-USD — Chainlink</option>
                                        <option value="MATIC-USD">MATIC-USD — Polygon</option>
                                        <option value="LTC-USD">LTC-USD — Litecoin</option>
                                    </optgroup>
                                </select>
                            </div>
                            {planetRequired && (
                                <div style={{ minWidth: 150 }}>
                                    <label className="form-label">Planet</label>
                                    <select className="form-select" value={planet} onChange={e => setPlanet(e.target.value)}>
                                        {PLANETS.map(p => <option key={p} value={p}>{p}</option>)}
                                    </select>
                                </div>
                            )}
                            {!planetRequired && (
                                <div style={{ minWidth: 150 }}>
                                    <label className="form-label">Planet</label>
                                    <div style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 8, padding: '9px 14px', fontSize: 13, color: '#a78bfa' }}>🔮 Multiple (Yoga)</div>
                                </div>
                            )}
                            <div style={{ minWidth: 150 }}>
                                <label className="form-label">Lookback</label>
                                <select className="form-select" value={years} onChange={e => setYears(Number(e.target.value))}>
                                    {[3, 5, 7, 10, 15, 20].map(y => <option key={y} value={y}>{y} years</option>)}
                                </select>
                            </div>
                            <div style={{ minWidth: 150 }}>
                                <label className="form-label">Forward Days (lag)</label>
                                <select className="form-select" value={forwardDays} onChange={e => setForwardDays(Number(e.target.value))}>
                                    {[0, 1, 2, 3, 5, 7].map(d => <option key={d} value={d}>{d === 0 ? 'Same day' : `T+${d}`}</option>)}
                                </select>
                            </div>
                        </div>

                        {/* Current selection indicator */}
                        {chosenEvent && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, padding: '10px 14px', background: `${chosenGroup?.color || '#6366f1'}15`, border: `1px solid ${chosenGroup?.color || '#6366f1'}30`, borderRadius: 10 }}>
                                <span style={{ fontSize: 18 }}>{chosenEvent.label.split(' ')[0]}</span>
                                <div>
                                    <div style={{ fontSize: 13, fontWeight: 600, color: 'white' }}>Selected: {chosenEvent.label}</div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{chosenEvent.note}</div>
                                </div>
                            </div>
                        )}

                        {/* Event Picker */}
                        <EventPicker activeEvent={eventType} onPick={setEventType} />

                        <button className="btn-primary" onClick={runBacktest} disabled={loading} style={{ minWidth: 220 }}>
                            {loading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Running…</> : `▶ Run Backtest: ${chosenEvent?.label || eventType}`}
                        </button>
                        {error && <div className="alert-error" style={{ marginTop: 14 }}>❌ {error}</div>}
                    </div>

                    {result && result.stats && (
                        <div className="glass-card" style={{ padding: 24 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                                <div>
                                    <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
                                        {chosenEvent?.label || eventType} — {result.symbol}
                                    </div>
                                    <span className={`badge ${result.stats.is_significant ? 'badge-bullish' : 'badge-neutral'}`} style={{ fontSize: 13, padding: '6px 14px' }}>
                                        {result.stats.is_significant ? '✅ Statistically Significant' : '⚪ Not Significant'}
                                    </span>
                                </div>
                                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>p-value: <strong style={{ color: 'var(--text-primary)', fontSize: 16 }}>{result.stats.p_value?.toFixed(4)}</strong></span>
                            </div>
                            <div className="grid-2" style={{ marginBottom: 16 }}>
                                <div style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)', borderRadius: 10, padding: 16 }}>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>During {chosenEvent?.label || eventType}</div>
                                    <div style={{ marginBottom: 8 }}>Avg Return: <ReturnCell v={result.stats.event_mean_return} /></div>
                                    <div style={{ marginBottom: 8 }}>Win Rate: <span style={{ color: 'var(--accent-green)', fontWeight: 600 }}>{result.stats.event_win_rate?.toFixed(1)}%</span></div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{result.stats.event_days} trading days</div>
                                </div>
                                <div style={{ background: 'rgba(148,163,184,0.04)', border: '1px solid rgba(148,163,184,0.15)', borderRadius: 10, padding: 16 }}>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>Normal Days (control)</div>
                                    <div style={{ marginBottom: 8 }}>Avg Return: <ReturnCell v={result.stats.normal_mean_return} /></div>
                                    <div style={{ marginBottom: 8 }}>Win Rate: <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{result.stats.normal_win_rate?.toFixed(1)}%</span></div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{result.stats.normal_days} trading days</div>
                                </div>
                            </div>
                            {result.stats.interpretation && (
                                <div className="insight-box">{result.stats.interpretation}</div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {sub === 'vix' && (
                <div>
                    <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ fontWeight: 700, marginBottom: 4, fontSize: 16 }}>VIX Planetary Backtest (India VIX)</h3>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 20 }}>
                            Does a specific yoga or planetary state cause India VIX to spike or drop?
                        </p>

                        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 20, alignItems: 'flex-end' }}>
                            {!ALL_YOGA_EVENTS.includes(vixEvent) && (
                                <div style={{ minWidth: 150 }}>
                                    <label className="form-label">Planet</label>
                                    <select className="form-select" value={vixPlanet} onChange={e => setVixPlanet(e.target.value)}>
                                        {PLANETS.map(p => <option key={p} value={p}>{p}</option>)}
                                    </select>
                                </div>
                            )}
                            {ALL_YOGA_EVENTS.includes(vixEvent) && (
                                <div style={{ minWidth: 150 }}>
                                    <label className="form-label">Planet</label>
                                    <div style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 8, padding: '9px 14px', fontSize: 13, color: '#a78bfa' }}>🔮 Multiple</div>
                                </div>
                            )}
                            <div style={{ minWidth: 150 }}>
                                <label className="form-label">Lookback</label>
                                <select className="form-select" value={vixYears} onChange={e => setVixYears(Number(e.target.value))}>
                                    {[3, 5, 7, 10, 15].map(y => <option key={y} value={y}>{y} years</option>)}
                                </select>
                            </div>
                        </div>

                        {chosenVixEvent && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, padding: '10px 14px', background: `${chosenVixGroup?.color || '#6366f1'}15`, border: `1px solid ${chosenVixGroup?.color || '#6366f1'}30`, borderRadius: 10 }}>
                                <span style={{ fontSize: 18 }}>{chosenVixEvent.label.split(' ')[0]}</span>
                                <div>
                                    <div style={{ fontSize: 13, fontWeight: 600, color: 'white' }}>Selected: {chosenVixEvent.label}</div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{chosenVixEvent.note}</div>
                                </div>
                            </div>
                        )}

                        <EventPicker activeEvent={vixEvent} onPick={setVixEvent} />

                        <button className="btn-primary" onClick={runVixBacktest} disabled={vixLoading}>
                            {vixLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Running…</> : `▶ Run VIX Backtest`}
                        </button>
                        {vixError && <div className="alert-error" style={{ marginTop: 14 }}>❌ {vixError}</div>}
                    </div>

                    {vixResult && vixResult.stats && (
                        <div className="glass-card" style={{ padding: 24 }}>
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{chosenVixEvent?.label} — India VIX</div>
                                <span className={`badge ${vixResult.stats.is_significant ? 'badge-bullish' : 'badge-neutral'}`} style={{ fontSize: 13, padding: '6px 14px' }}>
                                    {vixResult.stats.is_significant ? '✅ Significant VIX Impact' : '⚪ No Significant Impact'}
                                </span>
                            </div>
                            <div className="grid-2">
                                <div style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)', borderRadius: 10, padding: 16 }}>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>VIX during {chosenVixEvent?.label}</div>
                                    <div style={{ marginBottom: 8 }}>Avg VIX Change: <ReturnCell v={vixResult.stats.event_mean_return} /></div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{vixResult.stats.event_days} days sampled</div>
                                </div>
                                <div style={{ background: 'rgba(148,163,184,0.04)', border: '1px solid rgba(148,163,184,0.15)', borderRadius: 10, padding: 16 }}>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>Normal VIX (baseline)</div>
                                    <div style={{ marginBottom: 8 }}>Avg VIX Change: <ReturnCell v={vixResult.stats.normal_mean_return} /></div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{vixResult.stats.normal_days} days sampled</div>
                                </div>
                            </div>
                            {vixResult.stats.interpretation && (
                                <div className="insight-box" style={{ marginTop: 16 }}>{vixResult.stats.interpretation}</div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
