'use client';
import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { usePlanGate } from './UpgradeModal';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const API = '';

function ReturnCell({ v }: { v: number | null }) {
    if (v == null) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
    const color = v > 0 ? 'var(--accent-green)' : v < 0 ? 'var(--accent-red)' : 'var(--text-muted)';
    return <span style={{ color, fontWeight: 600 }}>{v > 0 ? '+' : ''}{v.toFixed(3)}%</span>;
}

//  Comprehensive signal type groups 
const EVENT_GROUPS = [
    {
        group: ' Cycle Motion',
        desc: 'Planetary speed & direction states',
        color: '#6366f1',
        events: [
            { value: 'Retrograde', label: '↩ Retrograde Cycle', note: 'Planet moving backward' },
            { value: 'Direct', label: '→ Direct Cycle', note: 'Planet moving forward' },
            { value: 'High Speed', label: ' High Velocity', note: 'Top 20% orbital velocity' },
            { value: 'Exalted', label: ' Peak Strength', note: 'Planet at maximum strength' },
            { value: 'Debilitated', label: ' Low Strength', note: 'Planet at minimum strength' },
            { value: 'Own House', label: ' Home Position', note: 'Planet in home sign' },
        ],
    },
    {
        group: ' Stress Signals',
        desc: 'Challenging planetary combinations',
        color: '#ef4444',
        events: [
            { value: 'Angarak_Yoga', label: ' Stress Signal A1', note: 'Mars + Rahu combination' },
            { value: 'Guru_Chandal_Yoga', label: ' Stress Signal A2', note: 'Jupiter + Rahu combination' },
            { value: 'Vish_Yoga', label: ' Stress Signal A3', note: 'Moon + Saturn combination' },
            { value: 'Yama_Yoga', label: ' Stress Signal A4', note: 'Mars + Saturn combination' },
            { value: 'Surya_Shani_Yoga', label: ' Stress Signal A5', note: 'Sun + Saturn combination' },
            { value: 'Surya_Mangal_Yoga', label: ' Stress Signal A6', note: 'Sun + Mars combination' },
            { value: 'Chandra_Mangal_Yoga', label: ' Stress Signal A7', note: 'Moon + Mars combination' },
            { value: 'Chandra_Shani_Yoga', label: ' Stress Signal A8', note: 'Moon + Saturn combination' },
            { value: 'Chandal_Venus', label: ' Stress Signal A9', note: 'Venus + Rahu combination' },
            { value: 'Shani_Rahu', label: ' Stress Signal A10', note: 'Saturn + Rahu combination' },
            { value: 'Shani_Ketu', label: ' Stress Signal A11', note: 'Saturn + Ketu combination' },
        ],
    },
    {
        group: ' Momentum Signals',
        desc: 'Favorable compound combinations',
        color: '#10b981',
        events: [
            { value: 'Budh_Aditya_Yoga', label: ' Momentum Signal B1', note: 'Mercury + Sun combination' },
            { value: 'Gajakesari_Yoga', label: ' Momentum Signal B2', note: 'Moon + Jupiter (same sign)' },
            { value: 'Gajakesari_Kendra', label: ' Momentum Signal B3', note: 'Jupiter in Kendra to Moon' },
            { value: 'Shukra_Guru_Yoga', label: ' Momentum Signal B4', note: 'Venus + Jupiter combination' },
            { value: 'Guru_Mangal_Yoga', label: ' Momentum Signal B5', note: 'Jupiter + Mars combination' },
            { value: 'Bhrigu_Mangal_Yoga', label: ' Momentum Signal B6', note: 'Venus + Mars combination' },
            { value: 'Clash_Of_Gurus', label: ' Momentum Signal B7', note: 'Jupiter + Venus (same sign)' },
            { value: 'Budh_Shani_Yoga', label: ' Momentum Signal B8', note: 'Mercury + Saturn combination' },
            { value: 'Guru_Ketu', label: ' Momentum Signal B9', note: 'Jupiter + Ketu combination' },
        ],
    },
    {
        group: ' Strength Signals',
        desc: 'High-strength planetary placements',
        color: '#f59e0b',
        events: [
            { value: 'Shasha_Yoga', label: ' Strength Signal C1', note: 'Saturn at peak power' },
            { value: 'Malavya_Yoga', label: ' Strength Signal C2', note: 'Venus at peak power' },
            { value: 'Ruchaka_Yoga', label: ' Strength Signal C3', note: 'Mars at peak power' },
            { value: 'Hamsa_Yoga', label: ' Strength Signal C4', note: 'Jupiter at peak power' },
            { value: 'Bhadra_Yoga', label: ' Strength Signal C5', note: 'Mercury at peak power' },
            { value: 'Neech_Bhang_Raj_Yoga', label: ' Strength Signal C6', note: 'Weakness reversal pattern' },
        ],
    },
    {
        group: ' Volatility Events',
        desc: 'High-volatility astronomical formations',
        color: '#dc2626',
        events: [
            { value: 'Solar_Eclipse', label: ' Volatility Event D1', note: 'Solar eclipse formation' },
            { value: 'Lunar_Eclipse', label: ' Volatility Event D2', note: 'Lunar eclipse formation' },
            { value: 'Grahan_Yoga', label: ' Volatility Event D3', note: 'Near-node planetary alignment' },
            { value: 'Kaal_Sarp_Dosh', label: ' Volatility Event D4', note: 'All planets hemmed by nodes' },
            { value: 'Sarp_Dosh', label: ' Volatility Event D5', note: '2+ malefics in same sign' },
            { value: 'Rahu_Ketu_Axis_Sun', label: ' Volatility Event D6', note: 'Sun on nodal axis' },
            { value: 'Rahu_Ketu_Axis_Moon', label: ' Volatility Event D7', note: 'Moon on nodal axis' },
            { value: 'Rahu_Ketu_Axis_Mars', label: ' Volatility Event D8', note: 'Mars on nodal axis' },
        ],
    },
    {
        group: ' Phase Events',
        desc: 'Lunar cycle formations',
        color: '#8b5cf6',
        events: [
            { value: 'Amavasya_Defect', label: ' Phase Event E1', note: 'New Moon formation' },
            { value: 'Purnima_Yoga', label: ' Phase Event E2', note: 'Full Moon formation' },
            { value: 'Paksha_Sandi', label: ' Phase Event E3', note: 'Waxing/waning boundary' },
            { value: 'Paap_Kartari_Moon', label: ' Phase Event E4', note: 'Moon hemmed by malefics' },
        ],
    },
    {
        group: ' Suppression Signals',
        desc: 'Planets weakened by proximity to Sun',
        color: '#f97316',
        events: [
            { value: 'Mercury_Combust', label: ' Suppression F1', note: 'Mercury suppressed' },
            { value: 'Venus_Combust', label: ' Suppression F2', note: 'Venus suppressed' },
            { value: 'Mars_Combust', label: ' Suppression F3', note: 'Mars suppressed' },
            { value: 'Jupiter_Combust', label: ' Suppression F4', note: 'Jupiter suppressed' },
            { value: 'Saturn_Combust', label: ' Suppression F5', note: 'Saturn suppressed' },
            { value: 'Multiple_Retrograde', label: '↩↩ Suppression F6', note: '3+ planets retrograde simultaneously' },
        ],
    },
];

// Planet motion events that need a specific planet (NOT yoga events)
const PLANET_MOTION_EVENTS = ['Retrograde', 'Direct', 'High Speed', 'Exalted', 'Debilitated', 'Own House'];
// Flatten all yoga events for lookup (exclude planet motion events that need a specific planet)
const ALL_YOGA_EVENTS = EVENT_GROUPS.flatMap(g => g.events.map(e => e.value)).filter(v => !PLANET_MOTION_EVENTS.includes(v));

export default function AstroCorrelation() {
    const { resolvedTheme } = useTheme();
    const isDark = resolvedTheme === 'dark';
    const chartTick   = isDark ? 'rgba(255,255,255,0.45)' : '#6b7280';
    const chartGrid   = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.07)';
    const chartLegend = isDark ? 'rgba(255,255,255,0.65)' : '#4b5563';
    const [symbol, setSymbol] = useState('^NSEI');
    const [planet, setPlanet] = useState('Mercury');
    const [eventType, setEventType] = useState('Retrograde');
    const [years, setYears] = useState(1);
    const [forwardDays, setForwardDays] = useState(0);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');
    const [groupFilter, setGroupFilter] = useState('All');

    const [vixPlanet, setVixPlanet] = useState('Mercury');
    const [vixEvent, setVixEvent] = useState('Retrograde');
    const [vixYears, setVixYears] = useState(1);
    const [vixLoading, setVixLoading] = useState(false);
    const [vixResult, setVixResult] = useState<any>(null);
    const [vixError, setVixError] = useState('');

    const [futuresMarket, setFuturesMarket] = useState('NSE');
    const [futuresLoading, setFuturesLoading] = useState(false);
    const [futuresResult, setFuturesResult] = useState<any>(null);
    const [futuresError, setFuturesError] = useState('');

    const [sp500Loading, setSp500Loading] = useState(false);
    const [sp500Result, setSp500Result] = useState<any>(null);
    const [sp500Error, setSp500Error] = useState('');

    const [macroLoading, setMacroLoading] = useState(false);
    const [macroResult, setMacroResult] = useState<any>(null);
    const [macroError, setMacroError] = useState('');


    const [sub, setSub] = useState<'backtest' | 'vix' | 'futures' | 'macro' | 'futures-backtest'>('backtest');

    const [fbTarget, setFbTarget] = useState('^NSEI');
    const [fbPredictor, setFbPredictor] = useState('ES=F');
    const [fbCondition, setFbCondition] = useState('Positive Return');
    const [fbYears, setFbYears] = useState(15);
    const [fbForwardDays, setFbForwardDays] = useState(0);

    const [fbLoading, setFbLoading] = useState(false);
    const [fbResult, setFbResult] = useState<any>(null);
    const [fbError, setFbError] = useState('');

    const runFuturesBacktest = async () => {
        setFbLoading(true); setFbError(''); setFbResult(null);
        try {
            const res = await fetch(`${API}/api/correlation/futures-backtest`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_symbol: fbTarget, predictor_symbol: fbPredictor, condition: fbCondition, years: fbYears, forward_days: fbForwardDays }),
            });
            const data = await res.json();
            if (!res.ok || data.error) setFbError(data.error || data.detail || 'Error');
            else setFbResult(data);
        } catch { setFbError('Network error'); }
        setFbLoading(false);
    }; const { guardYears, modal: planModal } = usePlanGate(1);


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

    const runFuturesPrediction = async () => {
        setFuturesLoading(true); setFuturesError(''); setFuturesResult(null);
        try {
            const res = await fetch(`${API}/api/correlation/live-prediction?market=${futuresMarket}`);
            const data = await res.json();
            if (!res.ok || data.error) setFuturesError(data.error || data.detail || 'Error');
            else setFuturesResult(data);
        } catch { setFuturesError('Network error'); }
        setFuturesLoading(false);
    };

    const TF_LABELS: Record<string, string> = { '5m': '5 Min', '15m': '15 Min', '30m': '30 Min', '1h': '1 Hour' };
    const TF_COLORS: Record<string, string> = { '5m': '#6366f1', '15m': '#10b981', '30m': '#f59e0b', '1h': '#ef4444' };

    const runSP500Correlation = async () => {
        setSp500Loading(true); setSp500Error(''); setSp500Result(null);
        try {
            const res = await fetch(`${API}/api/correlation/sp500-intraday?market=${futuresMarket}`);
            const data = await res.json();
            if (!res.ok || data.error) setSp500Error(data.error || data.detail || 'Error');
            else setSp500Result(data);
        } catch { setSp500Error('Network error – is backend running?'); }
        setSp500Loading(false);
    };

    const runMacroCorrelation = async () => {
        setMacroLoading(true); setMacroError(''); setMacroResult(null);
        // Automatically fetch intraday data if empty so the user can compare macro vs intraday
        if (!sp500Result) {
            runSP500Correlation();
        }
        try {
            const res = await fetch(`${API}/api/correlation/futures-macro?market=${futuresMarket}`);
            const data = await res.json();
            if (!res.ok || data.error) setMacroError(data.error || data.detail || 'Error');
            else setMacroResult(data);
        } catch { setMacroError('Network error – is backend running?'); }
        setMacroLoading(false);
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
                    <button onClick={() => setGroupFilter('All')} style={{ padding: '5px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600, border: `1px solid ${groupFilter === 'All' ? '#8b5cf6' : 'var(--border-active)'}`, background: groupFilter === 'All' ? 'rgba(139,92,246,0.2)' : 'transparent', color: groupFilter === 'All' ? '#8b5cf6' : 'var(--text-muted)', cursor: 'pointer' }}>All</button>
                    {EVENT_GROUPS.map(g => (
                        <button key={g.group} onClick={() => setGroupFilter(g.group)} style={{ padding: '5px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600, border: `1px solid ${groupFilter === g.group ? g.color : 'var(--border-active)'}`, background: groupFilter === g.group ? `${g.color}20` : 'transparent', color: groupFilter === g.group ? g.color : 'var(--text-muted)', cursor: 'pointer' }}>
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
                                        border: `1px solid ${activeEvent === ev.value ? g.color : 'var(--border-subtle)'}`,
                                        background: activeEvent === ev.value ? `${g.color}20` : 'var(--bg-secondary)',
                                        transition: 'all 0.15s',
                                    }}>
                                    <div style={{ fontSize: 12, fontWeight: 600, color: activeEvent === ev.value ? g.color : 'var(--text-primary)', marginBottom: 2 }}>{ev.label}</div>
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
            {planModal}
            <h1 className="section-title"> Signal Correlation Engine</h1>
            <p className="section-subtitle">
                Backtesting 44 proprietary signal patterns · Cycle & Volatility reactions across markets
            </p>

            <div className="tab-list" style={{ marginBottom: 20 }}>
                <button className={`tab-btn ${sub === 'backtest' ? 'active' : ''}`} onClick={() => setSub('backtest')}> Market Backtest</button>
                <button className={`tab-btn ${sub === 'vix' ? 'active' : ''}`} onClick={() => setSub('vix')}> VIX Backtest</button>
                <button className={`tab-btn ${sub === 'futures' ? 'active' : ''}`} onClick={() => setSub('futures')}> Nifty Backtesting with 5 Global Indicators</button>
                <button className={`tab-btn ${sub === 'macro' ? 'active' : ''}`} onClick={() => setSub('macro')}> 25-Year Macro</button>
            </div>

            {sub === 'backtest' && (
                <div>
                    <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ fontWeight: 700, marginBottom: 4, fontSize: 16 }}>Configure Signal Pattern Backtest</h3>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 20 }}>
                            Select any signal pattern below · {ALL_YOGA_EVENTS.length} signal types across 7 categories
                        </p>

                        {/* Symbol, Planet (if applicable), Lookback, Forward */}
                        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 20, alignItems: 'flex-end' }}>
                            <div style={{ minWidth: 150 }}>
                                <label className="form-label">Symbol</label>
                                <select className="form-select" value={symbol} onChange={e => setSymbol(e.target.value)}>
                                    <optgroup label=" NSE Indices">
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
                                    <optgroup label=" Nifty 50 Stocks">
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
                                    <optgroup label=" USA — NASDAQ / NYSE">
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
                                    <optgroup label=" Energy &amp; Commodities">
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
                                    <div style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 8, padding: '9px 14px', fontSize: 13, color: '#a78bfa' }}> Multiple (Yoga)</div>
                                </div>
                            )}
                            <div style={{ minWidth: 180 }}>
                                <label className="form-label">Historical Period <span style={{ fontSize: 9, background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', padding: '2px 6px', borderRadius: 4, marginLeft: 6, fontWeight: 700, letterSpacing: 0.5 }}>FREE LIMIT: 1 YR</span></label>
                                <select className="form-select" value={years} onChange={e => { if (guardYears(Number(e.target.value))) setYears(Number(e.target.value)); }}>
                                    {[1, 2, 3, 5, 10, 15, 20].map(y => <option key={y} value={y}>{y} {y > 1 ? 'Year(s) ' : 'Year'}</option>)}
                                </select>
                            </div>
                            <div style={{ minWidth: 150 }}>
                                <label className="form-label">Forward Days (lag)</label>
                                <select className="form-select" value={forwardDays} onChange={e => setForwardDays(Number(e.target.value))}>
                                    {[0, 1, 2, 3, 5, 7, 10, 14].map(d => <option key={d} value={d}>{d === 0 ? 'Same day' : `T+${d}`}</option>)}
                                </select>
                            </div>
                        </div>

                        {/* Current selection indicator */}
                        {chosenEvent && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, padding: '10px 14px', background: `${chosenGroup?.color || '#6366f1'}15`, border: `1px solid ${chosenGroup?.color || '#6366f1'}30`, borderRadius: 10 }}>
                                <span style={{ fontSize: 18 }}>{chosenEvent.label.split(' ')[0]}</span>
                                <div>
                                    <div style={{ fontSize: 13, fontWeight: 600, color: chosenGroup?.color || 'var(--text-primary)' }}>Selected: {chosenEvent.label}</div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{chosenEvent.note}</div>
                                </div>
                            </div>
                        )}

                        {/* Event Picker */}
                        <EventPicker activeEvent={eventType} onPick={setEventType} />

                        <button className="btn-primary" onClick={runBacktest} disabled={loading} style={{ minWidth: 220 }}>
                            {loading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Running…</> : ` Run Backtest: ${chosenEvent?.label || eventType}`}
                        </button>
                        {error && <div className="alert-error" style={{ marginTop: 14 }}> {error}</div>}
                    </div>

                    {result && result.stats && (
                        <div className="glass-card" style={{ padding: 24 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                                <div>
                                    <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
                                        {chosenEvent?.label || eventType} — {result.symbol}
                                    </div>
                                    <span className={`badge ${result.stats.is_significant ? 'badge-bullish' : 'badge-neutral'}`} style={{ fontSize: 13, padding: '6px 14px' }}>
                                        {result.stats.is_significant ? ' Statistically Significant' : ' Not Significant'}
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
                        <h3 style={{ fontWeight: 700, marginBottom: 4, fontSize: 16 }}>VIX Signal Backtest (India VIX)</h3>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 20 }}>
                            Does a specific signal pattern or cycle state cause India VIX to spike or drop?
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
                                    <div style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 8, padding: '9px 14px', fontSize: 13, color: '#a78bfa' }}> Multiple</div>
                                </div>
                            )}
                            <div style={{ minWidth: 180 }}>
                                <label className="form-label">Lookback Period</label>
                                <select className="form-select" value={vixYears} onChange={e => {
                                    const v = Number(e.target.value);
                                    if (guardYears(v)) setVixYears(v);
                                }}>
                                    <option value={1}>1 year  Free</option>
                                    <option value={3}> 3 years — Pro</option>
                                    <option value={5}> 5 years — Pro</option>
                                    <option value={7}> 7 years — Pro</option>
                                    <option value={10}> 10 years — Pro</option>
                                    <option value={15}> 15 years — Elite</option>
                                    <option value={20}> 20 years — Elite</option>
                                    <option value={30}> 30 years — Elite</option>
                                    <option value={99}> Max Available — Elite</option>
                                </select>
                            </div>
                        </div>

                        {chosenVixEvent && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, padding: '10px 14px', background: `${chosenVixGroup?.color || '#6366f1'}15`, border: `1px solid ${chosenVixGroup?.color || '#6366f1'}30`, borderRadius: 10 }}>
                                <span style={{ fontSize: 18 }}>{chosenVixEvent.label.split(' ')[0]}</span>
                                <div>
                                    <div style={{ fontSize: 13, fontWeight: 600, color: chosenVixGroup?.color || 'var(--text-primary)' }}>Selected: {chosenVixEvent.label}</div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{chosenVixEvent.note}</div>
                                </div>
                            </div>
                        )}

                        <EventPicker activeEvent={vixEvent} onPick={setVixEvent} />

                        <button className="btn-primary" onClick={runVixBacktest} disabled={vixLoading}>
                            {vixLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Running…</> : ` Run VIX Backtest`}
                        </button>
                        {vixError && <div className="alert-error" style={{ marginTop: 14 }}> {vixError}</div>}
                    </div>

                    {vixResult && vixResult.stats && (
                        <div className="glass-card" style={{ padding: 24 }}>
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{chosenVixEvent?.label} — India VIX</div>
                                <span className={`badge ${vixResult.stats.is_significant ? 'badge-bullish' : 'badge-neutral'}`} style={{ fontSize: 13, padding: '6px 14px' }}>
                                    {vixResult.stats.is_significant ? ' Significant VIX Impact' : ' No Significant Impact'}
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

            {sub === 'futures-backtest' && (
                <div>
                    <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ fontWeight: 700, marginBottom: 4, fontSize: 16 }}>Nifty 50 Global Indicators Backtest</h3>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 20 }}>
                            Determine how Nifty 50 historically performs when specific conditions are met by global baseline assets.
                        </p>

                        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 20, alignItems: 'flex-end' }}>
                            <div style={{ minWidth: 150 }}>
                                <label className="form-label">Target Asset</label>
                                <select className="form-select" value={fbTarget} onChange={e => setFbTarget(e.target.value)}>
                                    <option value="^NSEI">^NSEI — Nifty 50</option>
                                    <option value="^NSEBANK">^NSEBANK — Bank Nifty</option>
                                    <option value="^CNXIT">^CNXIT — Nifty IT</option>
                                </select>
                            </div>

                            <div style={{ minWidth: 150 }}>
                                <label className="form-label">Global Indicator</label>
                                <select className="form-select" value={fbPredictor} onChange={e => setFbPredictor(e.target.value)}>
                                    <option value="ES=F">ES=F — S&P 500 Futures</option>
                                    <option value="NQ=F">NQ=F — Nasdaq Futures</option>
                                    <option value="GC=F">GC=F — Gold</option>
                                    <option value="CL=F">CL=F — Crude Oil</option>
                                    <option value="DX-Y.NYB">DX-Y.NYB — US Dollar Index</option>
                                </select>
                            </div>

                            <div style={{ minWidth: 150 }}>
                                <label className="form-label">Condition</label>
                                <select className="form-select" value={fbCondition} onChange={e => setFbCondition(e.target.value)}>
                                    <option value="Positive Return">Closes Positive</option>
                                    <option value="Negative Return">Closes Negative</option>
                                    <option value="Return > 1%">Daily Return &gt; 1%</option>
                                    <option value="Return < -1%">Daily Return &lt; -1%</option>
                                    <option value="Return > 2%">Daily Return &gt; 2%</option>
                                    <option value="Return < -2%">Daily Return &lt; -2%</option>
                                </select>
                            </div>

                            <div style={{ minWidth: 120 }}>
                                <label className="form-label">Forward Days</label>
                                <select className="form-select" value={fbForwardDays} onChange={e => setFbForwardDays(Number(e.target.value))}>
                                    <option value={0}>0 (Same Day)</option>
                                    <option value={1}>1 Day (T+1)</option>
                                    <option value={2}>2 Days (T+2)</option>
                                    <option value={3}>3 Days (T+3)</option>
                                    <option value={5}>5 Days (T+5)</option>
                                    <option value={10}>10 Days (T+10)</option>
                                </select>
                            </div>

                            <div style={{ minWidth: 120 }}>
                                <label className="form-label">Historical Period <span style={{ fontSize: 9, background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', padding: '2px 6px', borderRadius: 4, marginLeft: 6, fontWeight: 700, letterSpacing: 0.5 }}>FREE LIMIT: 1 YR</span></label>
                                <select className="form-select" value={fbYears} onChange={e => guardYears(Number(e.target.value)) ? setFbYears(Number(e.target.value)) : null}>
                                    <option value={1}>1 Year (Free)</option>
                                    <option value={5}>5 Years (Pro)</option>
                                    <option value={10}>10 Years (Pro)</option>
                                    <option value={15}>15 Years (Pro)</option>
                                    <option value={99}>Max Available (Pro)</option>
                                </select>
                            </div>

                        </div>

                        <button className="btn btn-primary" onClick={runFuturesBacktest} disabled={fbLoading} style={{ width: '100%' }}>
                            {fbLoading ? <span className="spinner"></span> : 'Run Global Indicator Backtest'}
                        </button>
                        {fbError && <div className="alert-error" style={{ marginTop: 14 }}> {fbError}</div>}
                    </div>

                    {fbResult && fbResult.stats && (
                        <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{fbResult.predictor} {fbResult.condition} Effect on {fbResult.target}</div>
                                <span className={`badge ${fbResult.stats.is_significant ? 'badge-bullish' : 'badge-neutral'}`} style={{ fontSize: 13, padding: '6px 14px' }}>
                                    {fbResult.stats.is_significant ? ' ✨ Statistically Significant' : ' No Statistical Edge Found'}
                                </span>
                            </div>

                            <div className="grid-2" style={{ marginBottom: 20 }}>
                                <div style={{ background: 'var(--card-bg-elevated)', border: '1px solid var(--border)', borderRadius: 10, padding: 16 }}>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>Condition Triggered</div>
                                    <div style={{ marginBottom: 8 }}>Win Rate: <span style={{ fontWeight: 'bold', color: fbResult.stats.event_win_rate > 50 ? 'var(--success)' : 'var(--danger)' }}>{fbResult.stats.event_win_rate?.toFixed(1) || 'N/A'}%</span></div>
                                    <div style={{ marginBottom: 8 }}>Avg Target Return: <ReturnCell v={fbResult.stats.event_mean_return} /></div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{fbResult.stats.event_days} tracking days</div>
                                </div>
                                <div style={{ background: 'var(--card-bg-elevated)', border: '1px solid var(--border)', borderRadius: 10, padding: 16 }}>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>Normal Baseline (Condition Not Met)</div>
                                    <div style={{ marginBottom: 8 }}>Win Rate: <span style={{ fontWeight: 'bold' }}>{fbResult.stats.normal_win_rate?.toFixed(1) || 'N/A'}%</span></div>
                                    <div style={{ marginBottom: 8 }}>Avg Target Return: <ReturnCell v={fbResult.stats.normal_mean_return} /></div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{fbResult.stats.normal_days} tracking days</div>
                                </div>
                            </div>

                            {fbResult.stats.interpretation && (
                                <div className="insight-box">{fbResult.stats.interpretation}</div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {sub === 'futures' && (
                <div>
                    <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ fontWeight: 700, marginBottom: 4, fontSize: 16 }}>Live Market Prediction Engine</h3>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 20 }}>
                            Predict target direction by correlating historical returns against core global assets (Nasdaq, S&P 500, Oil, Gold, USD/INR).
                        </p>

                        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 20, alignItems: 'flex-end' }}>
                            <div style={{ minWidth: 150 }}>
                                <label className="form-label">Target Market</label>
                                <select className="form-select" value={futuresMarket} onChange={e => setFuturesMarket(e.target.value)}>
                                    <option value="NSE">Nifty 50 (^NSEI)</option>
                                    <option value="NASDAQ">Nasdaq (^IXIC)</option>
                                </select>
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                            <button className="btn-primary" onClick={runFuturesPrediction} disabled={futuresLoading}>
                                {futuresLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Running…</> : ` Run Live Prediction`}
                            </button>
                            <button className="btn-primary" onClick={runSP500Correlation} disabled={sp500Loading} style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
                                {sp500Loading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Analyzing…</> : `📊 Nifty Direction Indicator`}
                            </button>
                        </div>
                        {futuresError && <div className="alert-error" style={{ marginTop: 14 }}> {futuresError}</div>}
                        {sp500Error && <div className="alert-error" style={{ marginTop: 14 }}> {sp500Error}</div>}
                    </div>

                    {futuresResult && (
                        <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                                <div>
                                    <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
                                        Hourly Output: {futuresResult.target.symbol}
                                    </div>
                                    <span className={`badge ${futuresResult.prediction === 'Bullish' ? 'badge-bullish' : futuresResult.prediction === 'Bearish' ? 'badge-bearish' : 'badge-neutral'}`} style={{ fontSize: 13, padding: '6px 14px' }}>
                                        Direction: {futuresResult.prediction} ({futuresResult.confidence}% confidence)
                                    </span>
                                </div>
                                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Score: <strong style={{ color: 'var(--text-primary)', fontSize: 16 }}>{futuresResult.score}</strong></span>
                            </div>

                            <div className="grid-2" style={{ marginBottom: 16 }}>
                                <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: 16 }}>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>Correlated Global Assets List</div>
                                    <div style={{ display: 'grid', gap: 8 }}>
                                        {Object.entries(futuresResult.correlations || {}).map(([key, val]) => (
                                            <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                                                <span>{key.replace('_', '/')}</span>
                                                <span style={{ color: (val as number) > 0 ? 'var(--accent-green)' : (val as number) < 0 ? 'var(--accent-red)' : 'var(--text-muted)' }}>
                                                    {(val as number) > 0 ? '+' : ''}{val as React.ReactNode} (r)
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: 16 }}>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>Current Ticker Prices</div>
                                    <div style={{ display: 'grid', gap: 8 }}>
                                        {Object.entries(futuresResult.current_values || {}).map(([key, price]) => (
                                            <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, fontWeight: 600 }}>
                                                <span>{key.replace('_', '/')}</span>
                                                <span>{price as React.ReactNode}</span>
                                            </div>
                                        ))}
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, fontWeight: 700, borderTop: '1px solid var(--border-subtle)', paddingTop: 8, marginTop: 4 }}>
                                            <span>{futuresResult.target.symbol} Target</span>
                                            <span style={{ color: 'var(--accent-blue)' }}>{futuresResult.target.current_price}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="insight-box" style={{ marginTop: 16 }}>
                                {futuresResult.prediction === 'Bullish' ? 'The collective regression from global indices points upwards. Risk-on environment likely.' : futuresResult.prediction === 'Bearish' ? 'The collective regression indicates downward pressure on the target index. Consider protective hedges.' : 'System is showing mixed signals. No clear directional edge from global correlations right now.'}
                            </div>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)', textAlign: 'right', marginTop: 10 }}>Updated Context @ {new Date(futuresResult.timestamp).toLocaleTimeString()}</div>
                        </div>
                    )}

                    {/* ═══════════════════════════════════════════════════════════ */}
                    {/* GLOBAL FUTURES INTRADAY CORRELATION CHARTS                 */}
                    {/* ═══════════════════════════════════════════════════════════ */}
                    {sp500Result && sp500Result.timeframes && (() => {
                        const ASSET_COLORS: Record<string, string> = { SP500: '#6366f1', Dollar: '#f59e0b', Oil: '#ef4444', Gold: '#10b981', Nasdaq: '#3b82f6' };
                        const ASSET_LABELS: Record<string, string> = sp500Result.reference_assets || { SP500: 'S&P 500', Dollar: 'Dollar', Oil: 'Oil', Gold: 'Gold', Nasdaq: 'Nasdaq' };
                        return (
                            <div style={{ marginTop: 4 }}>
                                <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
                                        <span style={{ fontSize: 22 }}>📊</span>
                                        <div>
                                            <h3 style={{ fontWeight: 700, fontSize: 18, margin: 0 }}>Global Futures → Nifty Prediction</h3>
                                            <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '4px 0 0' }}>
                                                Rolling 20-bar Pearson correlation of {sp500Result.target} vs 5 global futures · Combined prediction per timeframe
                                            </p>
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 10 }}>
                                        {Object.entries(ASSET_COLORS).map(([key, color]) => (
                                            <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--text-muted)' }}>
                                                <div style={{ width: 10, height: 3, borderRadius: 2, background: color }} />
                                                {ASSET_LABELS[key] || key}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Prediction summary cards */}
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 20 }}>
                                    {(['5m', '15m', '30m', '1h'] as const).map(tf => {
                                        const tfData = sp500Result.timeframes[tf];
                                        if (!tfData) return null;
                                        return (
                                            <div key={tf} style={{ background: 'var(--bg-secondary)', border: `1px solid ${TF_COLORS[tf]}30`, borderRadius: 12, padding: 18, position: 'relative', overflow: 'hidden' }}>
                                                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: TF_COLORS[tf] }} />
                                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>{TF_LABELS[tf]} Prediction</div>
                                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                                                    <span className={`badge ${tfData.prediction === 'Bullish' ? 'badge-bullish' : tfData.prediction === 'Bearish' ? 'badge-bearish' : 'badge-neutral'}`} style={{ fontSize: 12, padding: '5px 12px' }}>
                                                        {tfData.prediction === 'Bullish' ? '▲' : tfData.prediction === 'Bearish' ? '▼' : '●'} {tfData.prediction}
                                                    </span>
                                                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{tfData.confidence}%</span>
                                                </div>
                                                <div style={{ display: 'grid', gap: 4 }}>
                                                    {tfData.assets && Object.entries(tfData.assets).map(([aKey, aData]: [string, any]) => (
                                                        <div key={aKey} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                                            <span style={{ color: ASSET_COLORS[aKey] || 'var(--text-muted)', fontWeight: 600 }}>{aKey}</span>
                                                            <span style={{ color: aData.current_corr != null ? (aData.current_corr > 0 ? '#10b981' : '#ef4444') : 'var(--text-muted)', fontWeight: 600 }}>
                                                                {aData.current_corr != null ? (aData.current_corr > 0 ? '+' : '') + aData.current_corr.toFixed(3) : '—'}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>

                                {/* Forward-Looking Multi-Timeframe Forecast */}
                                {(() => {
                                    const sig5 = sp500Result.timeframes['5m']?.combined_signal || 0;
                                    const sig15 = sp500Result.timeframes['15m']?.combined_signal || 0;
                                    const sig30 = sp500Result.timeframes['30m']?.combined_signal || 0;
                                    const sig60 = sp500Result.timeframes['1h']?.combined_signal || 0;
                                    const sig10 = (sig5 + sig15) / 2; // Interpolated 10m

                                    const path = [
                                        0,
                                        sig5 * 10,
                                        (sig5 + sig10) * 10,
                                        (sig5 + sig10 + sig15) * 10,
                                        (sig5 + sig10 + sig15 + sig30) * 10,
                                        (sig5 + sig10 + sig15 + sig30 + sig60) * 10
                                    ];

                                    const overallForecast = path[5] > 0.5 ? 'Strong Bullish' : path[5] > 0 ? 'Bullish' : path[5] < -0.5 ? 'Strong Bearish' : path[5] < 0 ? 'Bearish' : 'Neutral';
                                    const pathColor = path[5] > 0 ? '#10b981' : path[5] < 0 ? '#ef4444' : '#f59e0b';
                                    const pathGradientFill = path[5] > 0 ? 'rgba(16, 185, 129, 0.1)' : path[5] < 0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)';

                                    const forecastData = {
                                        labels: ['Now', '+5m', '+10m', '+15m', '+30m', '+1h'],
                                        datasets: [{
                                            label: 'Predicted Nifty Trajectory',
                                            data: path,
                                            borderColor: pathColor,
                                            backgroundColor: pathGradientFill,
                                            borderWidth: 3,
                                            pointRadius: 4,
                                            pointBackgroundColor: pathColor,
                                            tension: 0.4,
                                            fill: true,
                                        }]
                                    };

                                    const forecastOptions = {
                                        responsive: true, maintainAspectRatio: false,
                                        plugins: {
                                            legend: { display: false },
                                            tooltip: { backgroundColor: 'rgba(15,15,25,0.95)', titleColor: '#fff', bodyColor: pathColor, borderColor: pathColor, borderWidth: 1 }
                                        },
                                        scales: {
                                            x: { display: true, ticks: { color: chartTick, font: { size: 11 } }, grid: { display: false } },
                                            y: { display: false, grid: { display: false } }
                                        },
                                        interaction: { intersect: false, mode: 'index' as const },
                                    };

                                    return (
                                        <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                                                <div>
                                                    <h3 style={{ fontWeight: 700, fontSize: 18, margin: 0 }}>AI Intraday Forecast Pattern</h3>
                                                    <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '4px 0 0' }}>Target trajectory based on overlapping 5m, 10m, 15m, 30m, and 1h indicators</p>
                                                </div>
                                                <div style={{ textAlign: 'right' }}>
                                                    <span className={`badge ${path[5] > 0 ? 'badge-bullish' : path[5] < 0 ? 'badge-bearish' : 'badge-neutral'}`} style={{ fontSize: 14, padding: '6px 14px' }}>
                                                        {path[5] > 0 ? '▲' : path[5] < 0 ? '▼' : '●'} {overallForecast}
                                                    </span>
                                                </div>
                                            </div>
                                            <div style={{ height: 260, padding: 8, background: 'var(--bg-secondary)', borderRadius: 12, border: `1px solid ${pathColor}40` }}>
                                                <Line data={forecastData} options={forecastOptions} />
                                            </div>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 12 }}>
                                                This path represents cumulative momentum from all 5 global futures overlaid on Nifty.
                                                <br />
                                                <span style={{ opacity: 0.7 }}>Back data used: 5 Days (for 5m), 15 Days (for 15m), 30 Days (for 30m), and 60 Days (for 1h) with a 20-bar rolling correlation.</span>
                                            </div>
                                        </div>
                                    );
                                })()}

                                <h3 style={{ fontWeight: 600, fontSize: 15, marginBottom: 12, marginTop: 10, color: 'var(--text-primary)' }}>Individual Timeframe Correlation Charts</h3>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: 16 }}>
                                    {(['5m', '15m', '30m', '1h'] as const).map(tf => {
                                        const tfData = sp500Result.timeframes[tf];
                                        if (!tfData || !tfData.assets) return null;
                                        const assetEntries = Object.entries(tfData.assets).filter(([, a]: [string, any]) => a.data && a.data.length > 0);
                                        if (assetEntries.length === 0) return null;

                                        const longestAsset = assetEntries.reduce((a, b) => ((a[1] as any).data.length > (b[1] as any).data.length ? a : b));
                                        const labels = (longestAsset[1] as any).data.map((d: any) => {
                                            const dt = new Date(d.time);
                                            return tf === '1h' ? dt.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) + ' ' + dt.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
                                                : dt.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
                                        });

                                        const indexDatasets = assetEntries.map(([aKey, aData]: [string, any]) => ({
                                            label: ASSET_LABELS[aKey] || aKey,
                                            data: aData.data.map((d: any) => d.correlation),
                                            borderColor: ASSET_COLORS[aKey] || '#94a3b8',
                                            backgroundColor: 'transparent',
                                            borderWidth: 1.5,
                                            pointRadius: 0,
                                            pointHoverRadius: 3,
                                            tension: 0.3,
                                        }));

                                        const chartData = { labels, datasets: indexDatasets };
                                        const chartOptions = {
                                            responsive: true, maintainAspectRatio: false,
                                            plugins: {
                                                legend: { display: true, position: 'top' as const, labels: { color: chartLegend, font: { size: 10 }, boxWidth: 12, padding: 10 } },
                                                tooltip: {
                                                    backgroundColor: 'rgba(15,15,25,0.95)', titleColor: '#fff', bodyColor: '#a0a0b0', borderColor: TF_COLORS[tf], borderWidth: 1,
                                                    callbacks: { label: (ctx: any) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(4)}` }
                                                }
                                            },
                                            scales: {
                                                x: { display: true, ticks: { color: chartTick, font: { size: 9 }, maxTicksLimit: 8, maxRotation: 0 }, grid: { color: chartGrid } },
                                                y: { min: -1, max: 1, ticks: { color: chartTick, font: { size: 10 }, stepSize: 0.5 }, grid: { color: chartGrid } }
                                            },
                                            interaction: { intersect: false, mode: 'index' as const },
                                        };

                                        return (
                                            <div key={tf} className="glass-card" style={{ padding: 18 }}>
                                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                        <div style={{ width: 10, height: 10, borderRadius: '50%', background: TF_COLORS[tf] }} />
                                                        <span style={{ fontSize: 14, fontWeight: 700 }}>{TF_LABELS[tf]} Correlation Chart</span>
                                                    </div>
                                                    <span className={`badge ${tfData.prediction === 'Bullish' ? 'badge-bullish' : tfData.prediction === 'Bearish' ? 'badge-bearish' : 'badge-neutral'}`} style={{ fontSize: 11 }}>
                                                        Nifty → {tfData.prediction}
                                                    </span>
                                                </div>
                                                <div style={{ height: 250 }}>
                                                    <Line data={chartData} options={chartOptions} />
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>

                                <div className="insight-box" style={{ marginTop: 16 }}>
                                    {(() => {
                                        const tfs = sp500Result.timeframes;
                                        const bullish = Object.values(tfs).filter((t: any) => t.prediction === 'Bullish').length;
                                        const bearish = Object.values(tfs).filter((t: any) => t.prediction === 'Bearish').length;
                                        if (bullish > bearish) return `${bullish} of 4 timeframes predict Bullish for Nifty based on global futures correlation. Positive momentum is dominant across multiple intervals.`;
                                        if (bearish > bullish) return `${bearish} of 4 timeframes predict Bearish for Nifty based on global futures correlation. Downside pressure detected across multiple intervals.`;
                                        return 'Timeframes are evenly split between Bullish and Bearish. No clear directional consensus from global futures correlation signals.';
                                    })()}
                                </div>
                                <div style={{ fontSize: 10, color: 'var(--text-muted)', textAlign: 'right', marginTop: 8 }}>Last updated @ {new Date(sp500Result.timestamp).toLocaleTimeString()}</div>
                            </div>
                        );
                    })()}
                </div>
            )}

            {sub === 'macro' && (
                <div>
                    <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ fontWeight: 700, marginBottom: 4, fontSize: 16 }}>25-Year Global Futures Macro Correlation</h3>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 20 }}>
                            Analyze the long-term Pearson correlation (60-day rolling window) between Nifty and 5 key global futures over a 25-year period.
                        </p>

                        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                            <button className="btn-primary" onClick={runMacroCorrelation} disabled={macroLoading} style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}>
                                {macroLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2, marginRight: 8 }} />Analyzing 25 Years…</> : `🌍 Run 25-Year Macro Correlation`}
                            </button>
                        </div>
                        {macroError && <div className="alert-error" style={{ marginTop: 14 }}> {macroError}</div>}
                    </div>

                    {macroResult && macroResult.timeframes && macroResult.timeframes['1d'] && (() => {
                        const tfData = macroResult.timeframes['1d'];
                        if (!tfData || !tfData.assets) return null;

                        const ASSET_COLORS: Record<string, string> = { SP500: '#6366f1', Dollar: '#f59e0b', Oil: '#ef4444', Gold: '#10b981', Nasdaq: '#3b82f6' };
                        const ASSET_LABELS: Record<string, string> = macroResult.reference_assets || { SP500: 'S&P 500', Dollar: 'Dollar', Oil: 'Oil', Gold: 'Gold', Nasdaq: 'Nasdaq' };

                        const assetEntries = Object.entries(tfData.assets).filter(([, a]: [string, any]) => a.data && a.data.length > 0);
                        if (assetEntries.length === 0) return null;

                        // Find consensus
                        const bullishCount = assetEntries.filter(([, a]: [string, any]) => (a.current_corr ?? 0) > 0.2).length;
                        const bearishCount = assetEntries.filter(([, a]: [string, any]) => (a.current_corr ?? 0) < -0.2).length;
                        const macroPrediction = bullishCount > bearishCount ? 'Bullish' : bearishCount > bullishCount ? 'Bearish' : 'Neutral';

                        const longestAsset = assetEntries.reduce((a, b) => ((a[1] as any).data.length > (b[1] as any).data.length ? a : b));
                        const labels = (longestAsset[1] as any).data.map((d: any) => new Date(d.time).toLocaleDateString('en-IN', { year: 'numeric', month: 'short' }));

                        const indexDatasets = assetEntries.map(([aKey, aData]: [string, any]) => ({
                            label: ASSET_LABELS[aKey] || aKey,
                            data: aData.data.map((d: any) => d.correlation),
                            borderColor: ASSET_COLORS[aKey] || '#94a3b8',
                            backgroundColor: 'transparent',
                            borderWidth: 1.5,
                            pointRadius: 0,
                            pointHoverRadius: 4,
                            tension: 0.3,
                        }));

                        const chartData = { labels, datasets: indexDatasets };
                        const chartOptions = {
                            responsive: true, maintainAspectRatio: false,
                            plugins: {
                                legend: { display: true, position: 'top' as const, labels: { color: chartLegend, font: { size: 11 }, padding: 16 } },
                                tooltip: {
                                    backgroundColor: 'rgba(15,15,25,0.95)', titleColor: '#fff', bodyColor: '#a0a0b0', borderColor: '#10b981', borderWidth: 1,
                                    callbacks: { label: (ctx: any) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(4)}` }
                                }
                            },
                            scales: {
                                x: { display: true, ticks: { color: chartTick, font: { size: 10 }, maxTicksLimit: 12, maxRotation: 45 }, grid: { color: chartGrid } },
                                y: { min: -1, max: 1, ticks: { color: chartTick, font: { size: 10 }, stepSize: 0.5 }, grid: { color: chartGrid } }
                            },
                            interaction: { intersect: false, mode: 'index' as const },
                        };

                        return (
                            <div style={{ marginTop: 4 }}>
                                <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                            <span style={{ fontSize: 22 }}>📈</span>
                                            <div>
                                                <h3 style={{ fontWeight: 700, fontSize: 18, margin: 0 }}>25-Year Macro History</h3>
                                                <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '4px 0 0' }}>Daily correlation trends of Nifty vs Global Assets since ~2000</p>
                                            </div>
                                        </div>
                                        <div style={{ textAlign: 'right' }}>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>25-Year Outlook</div>
                                            <span className={`badge ${macroPrediction === 'Bullish' ? 'badge-bullish' : macroPrediction === 'Bearish' ? 'badge-bearish' : 'badge-neutral'}`} style={{ fontSize: 13, padding: '6px 14px' }}>
                                                {macroPrediction === 'Bullish' ? '▲' : macroPrediction === 'Bearish' ? '▼' : '●'} {macroPrediction}
                                            </span>
                                        </div>
                                    </div>

                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10, marginBottom: 20 }}>
                                        {assetEntries.map(([aKey, aData]: [string, any]) => (
                                            <div key={aKey} style={{ background: 'var(--bg-secondary)', padding: '10px 14px', borderRadius: 8, border: `1px solid var(--border-subtle)`, borderLeft: `3px solid ${ASSET_COLORS[aKey]}` }}>
                                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{aKey} Correl</div>
                                                <div style={{ fontSize: 14, fontWeight: 700, color: aData.current_corr != null ? (aData.current_corr > 0 ? '#10b981' : '#ef4444') : 'var(--text-muted)' }}>
                                                    {aData.current_corr != null ? (aData.current_corr > 0 ? '+' : '') + aData.current_corr.toFixed(3) : '—'}
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    <div style={{ height: 450, padding: 8, background: 'var(--bg-secondary)', borderRadius: 12 }}>
                                        <Line data={chartData} options={chartOptions} />
                                    </div>
                                </div>

                                {/* Intraday Forecast for Comparison */}
                                {sp500Result && (() => {
                                    const sig5 = sp500Result.timeframes['5m']?.combined_signal || 0;
                                    const sig15 = sp500Result.timeframes['15m']?.combined_signal || 0;
                                    const sig30 = sp500Result.timeframes['30m']?.combined_signal || 0;
                                    const sig60 = sp500Result.timeframes['1h']?.combined_signal || 0;
                                    const sig10 = (sig5 + sig15) / 2;

                                    const path = [
                                        0,
                                        sig5 * 10,
                                        (sig5 + sig10) * 10,
                                        (sig5 + sig10 + sig15) * 10,
                                        (sig5 + sig10 + sig15 + sig30) * 10,
                                        (sig5 + sig10 + sig15 + sig30 + sig60) * 10
                                    ];

                                    const overallForecast = path[5] > 0.5 ? 'Strong Bullish' : path[5] > 0 ? 'Bullish' : path[5] < -0.5 ? 'Strong Bearish' : path[5] < 0 ? 'Bearish' : 'Neutral';
                                    const pathColor = path[5] > 0 ? '#10b981' : path[5] < 0 ? '#ef4444' : '#f59e0b';
                                    const pathGradientFill = path[5] > 0 ? 'rgba(16, 185, 129, 0.1)' : path[5] < 0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)';

                                    const forecastData = {
                                        labels: ['Now', '+5m', '+10m', '+15m', '+30m', '+1h'],
                                        datasets: [{
                                            label: 'Predicted Nifty Trajectory',
                                            data: path,
                                            borderColor: pathColor,
                                            backgroundColor: pathGradientFill,
                                            borderWidth: 3,
                                            pointRadius: 4,
                                            pointBackgroundColor: pathColor,
                                            tension: 0.4,
                                            fill: true,
                                        }]
                                    };

                                    const forecastOptions = {
                                        responsive: true, maintainAspectRatio: false,
                                        plugins: {
                                            legend: { display: false },
                                            tooltip: { backgroundColor: 'rgba(15,15,25,0.95)', titleColor: '#fff', bodyColor: pathColor, borderColor: pathColor, borderWidth: 1 }
                                        },
                                        scales: {
                                            x: { display: true, ticks: { color: chartTick, font: { size: 11 } }, grid: { display: false } },
                                            y: { display: false, grid: { display: false } }
                                        },
                                        interaction: { intersect: false, mode: 'index' as const },
                                    };

                                    return (
                                        <div className="glass-card" style={{ padding: 24, marginTop: 24 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                                                <div>
                                                    <h3 style={{ fontWeight: 700, fontSize: 18, margin: 0 }}>Short-Term AI Intraday Forecast Pattern</h3>
                                                    <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '4px 0 0' }}>Compare immediate 1-hour Nifty trajectory against the 25-Year Macro outlook</p>
                                                </div>
                                                <div style={{ textAlign: 'right' }}>
                                                    <span className={`badge ${path[5] > 0 ? 'badge-bullish' : path[5] < 0 ? 'badge-bearish' : 'badge-neutral'}`} style={{ fontSize: 14, padding: '6px 14px' }}>
                                                        {path[5] > 0 ? '▲' : path[5] < 0 ? '▼' : '●'} {overallForecast}
                                                    </span>
                                                </div>
                                            </div>
                                            <div style={{ height: 260, padding: 8, background: 'var(--bg-secondary)', borderRadius: 12, border: `1px solid ${pathColor}40` }}>
                                                <Line data={forecastData} options={forecastOptions as any} />
                                            </div>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 12 }}>
                                                This path represents the immediate short-term momentum from the 5 global futures overlaid on Nifty.
                                                <br />
                                                <span style={{ opacity: 0.7 }}>Short-term Back data used: 5 Days (for 5m), 15 Days (for 15m), 30 Days (for 30m), and 60 Days (for 1h) with a 20-bar rolling correlation.</span>
                                            </div>
                                        </div>
                                    );
                                })()}
                            </div>
                        );
                    })()}


                </div>
            )}
        </div>
    );
}
