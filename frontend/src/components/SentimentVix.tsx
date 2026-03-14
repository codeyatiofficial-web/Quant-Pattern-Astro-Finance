'use client';
import React, { useState, useEffect } from 'react';
import { usePlanGate } from './UpgradeModal';

const API = '';

type Sub = 'live' | 'backtest' | 'forecast' | 'alignment';

function SentimentDot({ score }: { score: number }) {
    const color = score > 0.05 ? 'var(--accent-green)' : score < -0.05 ? 'var(--accent-red)' : 'var(--text-muted)';
    const label = score > 0.05 ? 'Bullish' : score < -0.05 ? 'Bearish' : 'Neutral';
    const icon = score > 0.05 ? '' : score < -0.05 ? '' : '';
    return <span style={{ color, fontWeight: 700, fontSize: 12 }}>{icon} {label} ({score.toFixed(3)})</span>;
}

function BiasChip({ bias, confidence }: { bias: string; confidence?: number }) {
    const color = bias === 'Bullish' ? 'var(--accent-green)' : bias === 'Bearish' ? 'var(--accent-red)' : 'var(--text-muted)';
    const bg = bias === 'Bullish' ? 'rgba(52,211,153,0.13)' : bias === 'Bearish' ? 'rgba(248,113,113,0.13)' : 'rgba(100,116,139,0.10)';
    const icon = bias === 'Bullish' ? '' : bias === 'Bearish' ? '' : '';
    return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 6, background: bg, color, fontWeight: 700, fontSize: 12.5 }}>
            {icon} {bias}{confidence != null ? ` · ${confidence}%` : ''}
        </span>
    );
}

//  Symbol Catalogue with Full Display Names 
const SYMBOL_GROUPS = [
    {
        label: ' NSE Indices',
        market: 'NSE',
        symbols: [
            { v: '^NSEI', l: '^NSEI — Nifty 50' },
            { v: '^NSEBANK', l: '^NSEBANK — Bank Nifty' },
            { v: '^CNXIT', l: '^CNXIT — Nifty IT' },
            { v: '^CNXAUTO', l: '^CNXAUTO — Nifty Auto' },
            { v: '^CNXFMCG', l: '^CNXFMCG — Nifty FMCG' },
            { v: '^CNXPHARMA', l: '^CNXPHARMA — Nifty Pharma' },
            { v: '^CNXMETAL', l: '^CNXMETAL — Nifty Metal' },
            { v: '^CNXREALTY', l: '^CNXREALTY — Nifty Realty' },
            { v: '^CNXENERGY', l: '^CNXENERGY — Nifty Energy' },
            { v: '^CNXINFRA', l: '^CNXINFRA — Nifty Infrastructure' },
            { v: '^CNXCONSUM', l: '^CNXCONSUM — Nifty Consumer Durables' },
            { v: '^CNXMEDIA', l: '^CNXMEDIA — Nifty Media' },
            { v: '^CNXPSU', l: '^CNXPSU — Nifty PSU Bank' },
            { v: '^INDIAVIX', l: '^INDIAVIX — India VIX (Fear Index)' },
            { v: '^NSMIDCP50', l: '^NSMIDCP50 — Nifty Midcap 50' },
        ],
    },
    {
        label: ' Nifty 50 Blue Chips',
        market: 'NSE',
        symbols: [
            { v: 'RELIANCE.NS', l: 'RELIANCE.NS — Reliance Industries' },
            { v: 'TCS.NS', l: 'TCS.NS — Tata Consultancy Services' },
            { v: 'HDFCBANK.NS', l: 'HDFCBANK.NS — HDFC Bank' },
            { v: 'INFY.NS', l: 'INFY.NS — Infosys' },
            { v: 'ICICIBANK.NS', l: 'ICICIBANK.NS — ICICI Bank' },
            { v: 'HINDUNILVR.NS', l: 'HINDUNILVR.NS — Hindustan Unilever' },
            { v: 'SBIN.NS', l: 'SBIN.NS — State Bank of India' },
            { v: 'BHARTIARTL.NS', l: 'BHARTIARTL.NS — Bharti Airtel' },
            { v: 'ITC.NS', l: 'ITC.NS — ITC Ltd' },
            { v: 'KOTAKBANK.NS', l: 'KOTAKBANK.NS — Kotak Mahindra Bank' },
            { v: 'LT.NS', l: 'LT.NS — Larsen & Toubro' },
            { v: 'BAJFINANCE.NS', l: 'BAJFINANCE.NS — Bajaj Finance' },
            { v: 'ASIANPAINT.NS', l: 'ASIANPAINT.NS — Asian Paints' },
            { v: 'AXISBANK.NS', l: 'AXISBANK.NS — Axis Bank' },
            { v: 'MARUTI.NS', l: 'MARUTI.NS — Maruti Suzuki' },
            { v: 'TITAN.NS', l: 'TITAN.NS — Titan Company' },
            { v: 'SUNPHARMA.NS', l: 'SUNPHARMA.NS — Sun Pharmaceutical' },
            { v: 'WIPRO.NS', l: 'WIPRO.NS — Wipro' },
            { v: 'HCLTECH.NS', l: 'HCLTECH.NS — HCL Technologies' },
            { v: 'TATAMOTORS.NS', l: 'TATAMOTORS.NS — Tata Motors' },
            { v: 'TATASTEEL.NS', l: 'TATASTEEL.NS — Tata Steel' },
            { v: 'ADANIENT.NS', l: 'ADANIENT.NS — Adani Enterprises' },
            { v: 'NTPC.NS', l: 'NTPC.NS — NTPC Ltd' },
            { v: 'ONGC.NS', l: 'ONGC.NS — Oil & Natural Gas Corp' },
            { v: 'COALINDIA.NS', l: 'COALINDIA.NS — Coal India' },
            { v: 'POWERGRID.NS', l: 'POWERGRID.NS — Power Grid Corp' },
            { v: 'JSWSTEEL.NS', l: 'JSWSTEEL.NS — JSW Steel' },
            { v: 'DRREDDY.NS', l: 'DRREDDY.NS — Dr Reddy Laboratories' },
            { v: 'CIPLA.NS', l: 'CIPLA.NS — Cipla' },
            { v: 'ULTRACEMCO.NS', l: 'ULTRACEMCO.NS — UltraTech Cement' },
            { v: 'BAJAJFINSV.NS', l: 'BAJAJFINSV.NS — Bajaj Finserv' },
            { v: 'APOLLOHOSP.NS', l: 'APOLLOHOSP.NS — Apollo Hospitals' },
        ],
    },
    {
        label: 'Precious Metals',
        market: 'NASDAQ',
        symbols: [
            { v: 'GC=F', l: 'GC=F — Gold Futures (COMEX)' },
            { v: 'SI=F', l: 'SI=F — Silver Futures (COMEX)' },
            { v: 'PL=F', l: 'PL=F — Platinum Futures' },
            { v: 'PA=F', l: 'PA=F — Palladium Futures' },
            { v: 'HG=F', l: 'HG=F — Copper Futures (COMEX)' },
            { v: 'ALI=F', l: 'ALI=F — Aluminium Futures' },
        ],
    },
    {
        label: ' Energy & Commodities',
        market: 'NASDAQ',
        symbols: [
            { v: 'CL=F', l: 'CL=F — Crude Oil WTI Futures' },
            { v: 'BZ=F', l: 'BZ=F — Brent Crude Oil Futures' },
            { v: 'NG=F', l: 'NG=F — Natural Gas Futures (Henry Hub)' },
            { v: 'RB=F', l: 'RB=F — RBOB Gasoline Futures' },
            { v: 'HO=F', l: 'HO=F — Heating Oil Futures' },
            { v: 'ZC=F', l: 'ZC=F — Corn Futures (CBOT)' },
            { v: 'ZW=F', l: 'ZW=F — Wheat Futures (CBOT)' },
            { v: 'ZS=F', l: 'ZS=F — Soybean Futures (CBOT)' },
            { v: 'CC=F', l: 'CC=F — Cocoa Futures' },
            { v: 'KC=F', l: 'KC=F — Coffee Futures (Arabica)' },
        ],
    },
    {
        label: ' Forex (Currency Pairs)',
        market: 'NASDAQ',
        symbols: [
            { v: 'USDINR=X', l: 'USDINR — US Dollar / Indian Rupee' },
            { v: 'EURINR=X', l: 'EURINR — Euro / Indian Rupee' },
            { v: 'GBPINR=X', l: 'GBPINR — British Pound / Indian Rupee' },
            { v: 'EURUSD=X', l: 'EURUSD — Euro / US Dollar' },
            { v: 'GBPUSD=X', l: 'GBPUSD — British Pound / US Dollar' },
            { v: 'USDJPY=X', l: 'USDJPY — US Dollar / Japanese Yen' },
            { v: 'AUDUSD=X', l: 'AUDUSD — Australian Dollar / US Dollar' },
            { v: 'DX-Y.NYB', l: 'DXY — US Dollar Index (DXY)' },
        ],
    },
    {
        label: ' US & Global Indices',
        market: 'NASDAQ',
        symbols: [
            { v: '^IXIC', l: '^IXIC — NASDAQ Composite' },
            { v: '^GSPC', l: '^GSPC — S&P 500' },
            { v: '^DJI', l: '^DJI — Dow Jones Industrial Average' },
            { v: '^RUT', l: '^RUT — Russell 2000 (Small Cap)' },
            { v: '^VIX', l: '^VIX — CBOE Volatility Index' },
            { v: '^FTSE', l: '^FTSE — FTSE 100 (London)' },
            { v: '^N225', l: '^N225 — Nikkei 225 (Japan)' },
            { v: '^HSI', l: '^HSI — Hang Seng Index (Hong Kong)' },
            { v: 'AAPL', l: 'AAPL — Apple Inc.' },
            { v: 'MSFT', l: 'MSFT — Microsoft Corporation' },
            { v: 'NVDA', l: 'NVDA — NVIDIA Corporation' },
            { v: 'TSLA', l: 'TSLA — Tesla Inc.' },
        ],
    },
    {
        label: '₿ Cryptocurrency',
        market: 'NASDAQ',
        symbols: [
            { v: 'BTC-USD', l: 'BTC-USD — Bitcoin (BTC)' },
            { v: 'ETH-USD', l: 'ETH-USD — Ethereum (ETH)' },
            { v: 'BNB-USD', l: 'BNB-USD — Binance Coin (BNB)' },
            { v: 'SOL-USD', l: 'SOL-USD — Solana (SOL)' },
            { v: 'XRP-USD', l: 'XRP-USD — XRP (Ripple)' },
            { v: 'ADA-USD', l: 'ADA-USD — Cardano (ADA)' },
            { v: 'DOGE-USD', l: 'DOGE-USD — Dogecoin (DOGE)' },
            { v: 'AVAX-USD', l: 'AVAX-USD — Avalanche (AVAX)' },
            { v: 'LTC-USD', l: 'LTC-USD — Litecoin (LTC)' },
        ],
    },
];

// Flat lookup: symbol -> market
const SYMBOL_MARKET_MAP: Record<string, string> = {};
SYMBOL_GROUPS.forEach(g => g.symbols.forEach(s => { SYMBOL_MARKET_MAP[s.v] = g.market; }));

// Kept for backtest dropdowns that reference the old arrays
const NSE_SYMBOLS = ['^NSEI', '^NSEBANK', '^CNXIT', '^CNXMETAL', '^CNXENERGY', '^CNXPHARMA', '^CNXAUTO', '^CNXFMCG', 'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS'];
const GLOBAL_SYMBOLS = ['^IXIC', '^GSPC', '^DJI', 'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'PL=F', 'PA=F', 'USDINR=X', 'EURUSD=X', 'BTC-USD', 'ETH-USD', 'SOL-USD'];

export default function SentimentVix() {
    const [sub, setSub] = useState<Sub>('live');
    const [liveData, setLiveData] = useState<any>(null);
    const [liveLoading, setLiveLoading] = useState(false);
    const [forecastData, setForecastData] = useState<any>(null);
    const [forecastLoading, setForecastLoading] = useState(false);
    const [fcSymbol, setFcSymbol] = useState('^NSEI');
    const [btData, setBtData] = useState<any>(null);
    const [btLoading, setBtLoading] = useState(false);
    const [btSymbol, setBtSymbol] = useState('^NSEI');
    const [btPeriod, setBtPeriod] = useState('1y');
    const [alignData, setAlignData] = useState<any>(null);
    const [alignLoading, setAlignLoading] = useState(false);
    const [alignSymbol, setAlignSymbol] = useState('^NSEI');
    const [alignPeriod, setAlignPeriod] = useState('1y');
    const [alignEvent, setAlignEvent] = useState('High Speed');
    const [alignPlanet, setAlignPlanet] = useState('Mercury');

    const { guardPeriod, modal: planModal, tier } = usePlanGate(1);


    const fetchLive = async () => {
        setLiveLoading(true);
        try { const r = await fetch(`${API}/api/sentiment/live`); setLiveData(await r.json()); } catch { }
        setLiveLoading(false);
    };

    const fetchForecast = async (sym = fcSymbol) => {
        setForecastLoading(true);
        setForecastData(null);
        try {
            const market = SYMBOL_MARKET_MAP[sym] ?? (GLOBAL_SYMBOLS.includes(sym) ? 'NASDAQ' : 'NSE');
            const r = await fetch(`${API}/api/sentiment/forecast?symbol=${encodeURIComponent(sym)}&market=${market}`);
            const data = await r.json();
            if (data && !data.error) {
                setForecastData(data);
            } else {
                setForecastData({ error: data?.error || 'No data available for this symbol.' });
            }
        } catch {
            setForecastData({ error: 'Network error. Is the backend running?' });
        }
        setForecastLoading(false);
    };


    const fetchBacktest = async () => {
        setBtLoading(true);
        try {
            const r = await fetch(`${API}/api/sentiment/backtest`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol: btSymbol, period: btPeriod }),
            });
            setBtData(await r.json());
        } catch { }
        setBtLoading(false);
    };

    const fetchAlignment = async () => {
        setAlignLoading(true);
        try {
            const y = alignPeriod === 'max' ? 25 : parseInt(alignPeriod.replace('y', '')) || 1;
            const r = await fetch(`${API}/api/sentiment/astro-backtest`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: alignSymbol,
                    period: alignPeriod,
                    event_type: alignEvent,
                    planet: alignPlanet,
                    market: GLOBAL_SYMBOLS.includes(alignSymbol) ? 'NASDAQ' : 'NSE',
                    years: y
                }),
            });
            setAlignData(await r.json());
        } catch { }
        setAlignLoading(false);
    };

    useEffect(() => {
        if (sub === 'live' && !liveData) fetchLive();
        if (sub === 'forecast' && !forecastData) fetchForecast();
        if (sub === 'alignment' && !alignData) fetchAlignment();
    }, [sub]);

    const SUBTABS = [
        { key: 'live', label: ' Live Sentiment' },
        { key: 'backtest', label: ' Sentiment Backtest' },
        { key: 'forecast', label: tier === 'elite' ? ' 1-Month Forecast' : tier === 'free' ? ' 1-Day Forecast' : ' 15-Day Forecast' },
        { key: 'alignment', label: ' Astro Alignment' },
    ] as const;

    // Limit forecast based on tier
    const allowedDaysCount = tier === 'elite' ? 60 : tier === 'free' ? 1 : 15;
    const limitedForecasts = forecastData?.daily_forecasts?.slice(0, allowedDaysCount) || [];

    // Recalculate outlook for pro tier limits
    let displayOutlook = forecastData?.outlook;
    if (displayOutlook && tier !== 'elite' && limitedForecasts.length > 0) {
        const bullish_days = limitedForecasts.filter((d: any) => d.bias === 'Bullish').length;
        const bearish_days = limitedForecasts.filter((d: any) => d.bias === 'Bearish').length;
        const neutral_days = limitedForecasts.filter((d: any) => d.bias === 'Neutral').length;
        const avg_confidence = limitedForecasts.reduce((acc: number, d: any) => acc + d.confidence, 0) / limitedForecasts.length;
        const overall_bias = bullish_days > bearish_days ? 'Bullish' : bearish_days > bullish_days ? 'Bearish' : 'Neutral';
        displayOutlook = { ...displayOutlook, bullish_days, bearish_days, neutral_days, avg_confidence, overall_bias };
    }

    // Group forecast days by week
    const weeks = limitedForecasts.reduce((acc: Record<number, any[]>, d: any) => {
        const w = d.week ?? 1;
        if (!acc[w]) acc[w] = [];
        acc[w].push(d);
        return acc;
    }, {} as Record<number, any[]>);

    return (
        <>
            <div className="fade-in">
                <h1 className="section-title"> Sentiment &amp; Market Pulse</h1>
                <p className="section-subtitle">News sentiment scoring, 1-month forecasting, and astro-news alignment</p>

                <div className="tab-list" style={{ marginBottom: 20 }}>
                    {SUBTABS.map(s => (
                        <button key={s.key} className={`tab-btn ${sub === s.key ? 'active' : ''}`} onClick={() => setSub(s.key as Sub)}>{s.label}</button>
                    ))}
                </div>

                {/*  LIVE SENTIMENT  */}
                {sub === 'live' && (
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                            <button className="btn-primary" onClick={fetchLive} disabled={liveLoading}>
                                {liveLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2 }} /> Fetching…</> : ' Refresh Headlines'}
                            </button>
                            {liveData?.overall_score !== undefined && (
                                <div className="glass-card group transition-all duration-300 hover:-translate-y-1 hover:shadow-[var(--shadow-glow)]" style={{ padding: '8px 16px', display: 'inline-flex', alignItems: 'center', gap: 16 }}>
                                    <div>
                                        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: 2 }}>Overall Sentiment</div>
                                        <SentimentDot score={liveData.overall_score} />
                                    </div>
                                    {liveData.counts && (
                                        <div className="font-quant" style={{ display: 'flex', gap: 10, fontSize: 13 }}>
                                            <span style={{ color: 'var(--accent-green)', fontWeight: 700 }}> {liveData.counts.bullish ?? 0}</span>
                                            <span style={{ color: 'var(--accent-red)', fontWeight: 700 }}> {liveData.counts.bearish ?? 0}</span>
                                            <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>→ {liveData.counts.neutral ?? 0}</span>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                        {liveData?.headlines?.length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {liveData.headlines.map((h: any, i: number) => {
                                    const s = h.score ?? 0;
                                    const left = s > 0.1 ? 'var(--accent-green)' : s < -0.1 ? 'var(--accent-red)' : 'var(--border-subtle)';
                                    return (
                                        <div key={i} className="group transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg" style={{
                                            background: 'var(--bg-card)',
                                            border: '1px solid var(--border-subtle)',
                                            borderLeft: `3px solid ${left}`,
                                            borderRadius: 10,
                                            padding: '11px 16px',
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 14,
                                        }}>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontSize: 13.5, color: 'var(--text-primary)', lineHeight: 1.5, fontWeight: 500 }}>{h.title}</div>
                                                <div style={{ marginTop: 5, display: 'flex', gap: 12, fontSize: 11, color: 'var(--text-muted)' }}>
                                                    <span style={{ fontWeight: 600 }}>{h.source}</span>
                                                    {h.published && <span className="font-quant">{h.published}</span>}
                                                </div>
                                            </div>
                                            <SentimentDot score={s} />
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (!liveLoading && <div className="alert-info">No live headlines loaded yet. Click Refresh.</div>)}
                    </div>
                )}

                {/*  SENTIMENT BACKTEST  */}
                {sub === 'backtest' && (
                    <div>
                        <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                            <h3 style={{ fontWeight: 700, marginBottom: 16, fontSize: 15 }}>Historical Sentiment Backtest</h3>
                            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 16, alignItems: 'flex-end' }}>
                                <div>
                                    <label className="form-label">Symbol</label>
                                    <select className="form-select" value={btSymbol} onChange={e => setBtSymbol(e.target.value)} style={{ width: 200 }}>
                                        <optgroup label=" India — NSE">
                                            {NSE_SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
                                        </optgroup>
                                        <optgroup label=" Global / US">
                                            {GLOBAL_SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
                                        </optgroup>
                                    </select>
                                </div>
                                <div>
                                    <label className="form-label">Period</label>
                                    <select className="form-select" value={btPeriod} onChange={e => {
                                        const p = e.target.value;
                                        if (guardPeriod(p)) setBtPeriod(p);
                                    }} style={{ width: 200 }}>
                                        <option value="1y">1 year  Free</option>
                                        <option value="2y"> 2 years — Pro</option>
                                        <option value="3y"> 3 years — Pro</option>
                                        <option value="5y"> 5 years — Pro</option>
                                        <option value="10y"> 10 years — Elite</option>
                                        <option value="max"> Max Available — Elite</option>
                                    </select>
                                </div>
                                <button className="btn-primary" onClick={fetchBacktest} disabled={btLoading}>
                                    {btLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2 }} /> Running…</> : ' Run Backtest'}
                                </button>
                            </div>
                        </div>
                        {btData?.stats && (
                            <div className="grid-3" style={{ gap: 16, marginBottom: 20 }}>
                                {(['bullish', 'bearish', 'neutral'] as const).map(k => {
                                    const s = btData.stats[k];
                                    if (!s) return null;
                                    return (
                                        <div key={k} className="glass-card group transition-all duration-300 hover:-translate-y-1 hover:shadow-[var(--shadow-glow)]" style={{ padding: 22 }}>
                                            <BiasChip bias={k.charAt(0).toUpperCase() + k.slice(1)} />
                                            <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                {[
                                                    { label: 'Signal Days', value: s.count },
                                                    { label: 'Win Rate', value: s.win_rate != null ? s.win_rate.toFixed(1) + '%' : '—' },
                                                    { label: 'Avg Next Day', value: s.avg_next_day != null ? (s.avg_next_day > 0 ? '+' : '') + s.avg_next_day.toFixed(3) + '%' : '—' },
                                                    { label: 'Avg Next Week', value: s.avg_next_week != null ? (s.avg_next_week > 0 ? '+' : '') + s.avg_next_week.toFixed(3) + '%' : '—' },
                                                ].map(r => (
                                                    <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5 }}>
                                                        <span style={{ color: 'var(--text-muted)' }}>{r.label}</span>
                                                        <span className="font-quant" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{r.value}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                        {btData?.overall_accuracy != null && (
                            <div className="glass-card group transition-all duration-300 hover:shadow-[var(--shadow-glow)]" style={{ padding: 20, display: 'flex', alignItems: 'center', gap: 20 }}>
                                <div>
                                    <div className="form-label">Overall Signal Accuracy</div>
                                    <div className="gradient-text font-quant drop-shadow-md" style={{ fontSize: 32, fontWeight: 800 }}>{btData.overall_accuracy}%</div>
                                </div>
                                {btData.total_trading_days && (
                                    <div style={{ borderLeft: '1px solid var(--border-subtle)', paddingLeft: 20 }}>
                                        <div className="form-label">Trading Days Analysed</div>
                                        <div className="font-quant" style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>{btData.total_trading_days?.toLocaleString()}</div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/*  FORECAST  */}
                {sub === 'forecast' && (
                    <div>
                        {/* Controls */}
                        <div className="glass-card" style={{ padding: 20, marginBottom: 18 }}>
                            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                                <div>
                                    <label className="form-label">Symbol</label>
                                    <select className="form-select" value={fcSymbol} onChange={e => { setFcSymbol(e.target.value); setForecastData(null); }} style={{ width: 300 }}>
                                        {SYMBOL_GROUPS.map(g => (
                                            <optgroup key={g.label} label={g.label}>
                                                {g.symbols.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
                                            </optgroup>
                                        ))}
                                    </select>
                                </div>
                                <button className="btn-primary" onClick={() => fetchForecast(fcSymbol)} disabled={forecastLoading}>
                                    {forecastLoading
                                        ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2 }} /> Generating…</>
                                        : ` Generate ${tier === 'elite' ? '1-Month' : tier === 'free' ? '1-Day' : '15-Day'} Forecast`}
                                </button>
                            </div>
                            {forecastData?.error && (
                                <div className="alert-error" style={{ marginTop: 14 }}> {forecastData.error}</div>
                            )}
                        </div>

                        {/* Upsell Banner */}
                        {forecastData && !forecastData.error && tier !== 'elite' && (
                            <div style={{ marginBottom: 18, padding: 20, background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
                                <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Unlock Extended Forecasts</div>
                                {tier === 'free' && (
                                    <div className="group transition-all duration-300" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: 8, cursor: 'pointer' }} onClick={() => guardPeriod('15y')} >
                                        <div>
                                            <div style={{ fontSize: 13, fontWeight: 700, color: '#f59e0b', marginBottom: 2 }}> Pro Plan</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Get full 15-Day AI Predictive Forecasts and Market Outlook</div>
                                        </div>
                                        <button className="btn-primary" style={{ padding: '6px 14px', fontSize: 12, background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', border: 'none' }}>Upgrade to Pro</button>
                                    </div>
                                )}
                                <div className="group transition-all duration-300" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'rgba(168, 85, 247, 0.05)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: 8, cursor: 'pointer' }} onClick={() => guardPeriod('30y')} >
                                    <div>
                                        <div style={{ fontSize: 13, fontWeight: 700, color: '#a855f7', marginBottom: 2 }}> Elite Plan</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Get max 30-Day AI Predictive Forecasts and Elite Analytics</div>
                                    </div>
                                    <button className="btn-primary" style={{ padding: '6px 14px', fontSize: 12, background: 'linear-gradient(135deg, #a855f7 0%, #7e22ce 100%)', border: 'none' }}>Upgrade to Elite</button>
                                </div>
                            </div>
                        )}

                        {/* Outlook summary bar */}
                        {displayOutlook && !forecastData.error && (
                            <div className="glass-card" style={{ padding: '16px 22px', marginBottom: 18, display: 'flex', flexWrap: 'wrap', gap: 20, alignItems: 'center' }}>
                                <div>
                                    <div className="form-label">{tier === 'elite' ? '1-Month' : tier === 'free' ? '1-Day' : '15-Day'} Outlook — {forecastData.symbol}</div>
                                    <BiasChip bias={displayOutlook.overall_bias} />
                                </div>
                                <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                                    {[
                                        { label: ' Bullish days', value: displayOutlook.bullish_days, color: 'var(--accent-green)' },
                                        { label: ' Bearish days', value: displayOutlook.bearish_days, color: 'var(--accent-red)' },
                                        { label: ' Neutral days', value: displayOutlook.neutral_days, color: 'var(--text-muted)' },
                                        { label: 'Avg Confidence', value: `${displayOutlook.avg_confidence?.toFixed(1)}%`, color: 'var(--accent-indigo)' },
                                        { label: 'Vol Regime', value: displayOutlook.vol_regime, color: 'var(--accent-gold)' },
                                    ].map(m => (
                                        <div key={m.label}>
                                            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.5px', textTransform: 'uppercase', marginBottom: 3 }}>{m.label}</div>
                                            <div className="num" style={{ fontSize: 16, fontWeight: 800, color: m.color }}>{m.value}</div>
                                        </div>
                                    ))}
                                    {displayOutlook.current_price && (
                                        <div>
                                            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.5px', textTransform: 'uppercase', marginBottom: 3 }}>Current Price</div>
                                            <div className="num" style={{ fontSize: 16, fontWeight: 800 }}>{displayOutlook.current_price?.toLocaleString()}</div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Calendar-style week-by-week grid */}
                        {Object.keys(weeks).length > 0 && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                {(Object.entries(weeks) as [string, any[]][]).map(([weekNum, days]) => (
                                    <div key={weekNum}>
                                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.7px', marginBottom: 8 }}>
                                            Week {weekNum} &nbsp;
                                            <span style={{ fontWeight: 400 }}>
                                                {days[0]?.date} → {days[days.length - 1]?.date}
                                            </span>
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
                                            {days.map((d: any, i: number) => {
                                                const bias = (d.bias || '').toLowerCase();
                                                const borderColor = bias === 'bullish' ? 'var(--accent-green)' : bias === 'bearish' ? 'var(--accent-red)' : 'var(--border-subtle)';
                                                const biasColor = bias === 'bullish' ? 'var(--accent-green)' : bias === 'bearish' ? 'var(--accent-red)' : 'var(--text-muted)';
                                                const biasIcon = bias === 'bullish' ? '' : bias === 'bearish' ? '' : '';
                                                return (
                                                    <div key={i} className="group transition-all duration-300 hover:-translate-y-1 hover:shadow-lg" style={{
                                                        background: 'var(--bg-card)',
                                                        border: `1px solid ${borderColor}`,
                                                        borderTop: `3px solid ${borderColor}`,
                                                        borderRadius: 12,
                                                        padding: '12px 14px',
                                                    }}>
                                                        <div className="font-quant" style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 2 }}>{d.date}</div>
                                                        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>{d.day_name}</div>
                                                        <div style={{ fontSize: 16, fontWeight: 800, color: biasColor, marginBottom: 6 }}>{biasIcon} {d.bias}</div>
                                                        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Conf: <span className="font-quant" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{d.confidence}%</span></div>
                                                        {d.nakshatra && (
                                                            <div style={{ marginTop: 6, fontSize: 10, color: 'var(--accent-violet)', fontWeight: 600 }}>
                                                                {d.nakshatra}
                                                            </div>
                                                        )}
                                                        {d.ruling_planet && (
                                                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{d.ruling_planet}</div>
                                                        )}
                                                        {d.events && d.events.length > 0 && (
                                                            <div style={{ marginTop: 6/*, overflow: 'hidden'*/ }}>
                                                                {d.events.slice(0, 1).map((ev: string, ei: number) => (
                                                                    <div key={ei} style={{ fontSize: 9, color: 'var(--accent-gold)', lineHeight: 1.3, fontWeight: 600 }}>{ev}</div>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Upcoming economic events list */}
                        {forecastData?.upcoming_events?.length > 0 && (
                            <div style={{ marginTop: 24 }}>
                                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.7px', marginBottom: 10 }}>
                                    Upcoming Key Events This Month
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                    {forecastData.upcoming_events.slice(0, 12).map((ev: any, i: number) => (
                                        <div key={i} style={{
                                            display: 'flex', alignItems: 'center', gap: 14,
                                            background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                                            borderRadius: 10, padding: '10px 16px',
                                        }}>
                                            <span style={{ fontSize: 18 }}>{ev.emoji ?? ''}</span>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{ev.description}</div>
                                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{ev.category} · {ev.date}</div>
                                            </div>
                                            <span className="num" style={{ fontSize: 12, color: 'var(--accent-gold)', fontWeight: 700 }}>T+{ev.days_away}d</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {forecastData?.error && <div className="alert-warn"> {forecastData.error}</div>}

                    </div>
                )}

                {/*  ASTRO ALIGNMENT  */}
                {sub === 'alignment' && (
                    <div>
                        <div className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
                            <h3 style={{ fontWeight: 700, marginBottom: 16, fontSize: 15 }}>Astro-Sentiment Matrix</h3>
                            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>Find out if planetary events improve or invert standard news sentiment accuracy.</p>

                            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 16, alignItems: 'flex-end' }}>
                                <div>
                                    <label className="form-label">Symbol</label>
                                    <select className="form-select" value={alignSymbol} onChange={e => setAlignSymbol(e.target.value)} style={{ width: 180 }}>
                                        <optgroup label=" India — NSE">{NSE_SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}</optgroup>
                                        <optgroup label=" Global / US">{GLOBAL_SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}</optgroup>
                                    </select>
                                </div>
                                <div>
                                    <label className="form-label">Period <span style={{ fontSize: 10, color: '#f59e0b' }}>(Pro)</span></label>
                                    <select className="form-select" value={alignPeriod} onChange={e => { if (guardPeriod(e.target.value)) setAlignPeriod(e.target.value); }} style={{ width: 110 }}>
                                        {['1y', '3y', '5y', '10y', '15y', 'max'].map(p => <option key={p} value={p}>{p} {p !== '1y' && ''}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="form-label">Planet</label>
                                    <select className="form-select" value={alignPlanet} onChange={e => setAlignPlanet(e.target.value)} style={{ width: 130 }}>
                                        {['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu'].map(p => <option key={p} value={p}>{p}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="form-label">Astro Event</label>
                                    <select className="form-select" value={alignEvent} onChange={e => setAlignEvent(e.target.value)} style={{ width: 200 }}>
                                        <optgroup label="Motion & States">
                                            {['Retrograde', 'Direct', 'High Speed', 'Exalted', 'Debilitated', 'Own House'].map(e => <option key={e} value={e}>{e}</option>)}
                                        </optgroup>
                                        <optgroup label="Major Yogas">
                                            {[
                                                'Gajakesari_Yoga', 'Guru_Chandal_Yoga', 'Vish_Yoga', 'Angarak_Yoga',
                                                'Budh_Aditya_Yoga', 'Shasha_Yoga', 'Amavasya_Defect', 'Purnima_Yoga',
                                                'Solar_Eclipse', 'Lunar_Eclipse', 'Kaal_Sarp_Dosh'
                                            ].map(e => <option key={e} value={e}>{e.replace(/_/g, ' ')}</option>)}
                                        </optgroup>
                                    </select>
                                </div>
                                <button className="btn-primary" onClick={fetchAlignment} disabled={alignLoading}>
                                    {alignLoading ? <><span className="spinner" style={{ width: 15, height: 15, borderWidth: 2 }} /> Computing Matrix…</> : ' Correlate'}
                                </button>
                            </div>
                        </div>

                        {alignData?.matrix && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                                {/* OVERALL LIFT */}
                                <div className="glass-card group transition-all duration-300 hover:shadow-[var(--shadow-glow)]" style={{ padding: 24, display: 'flex', gap: 40, alignItems: 'center' }}>
                                    <div>
                                        <div className="form-label">Astro Impact Lift</div>
                                        <div className="gradient-text font-quant drop-shadow-md" style={{ fontSize: 34, fontWeight: 800 }}>
                                            {alignData.lift > 0 ? '+' : ''}{alignData.lift ?? 0}%
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: 30, borderLeft: '1px solid var(--border-subtle)', paddingLeft: 40 }}>
                                        <div>
                                            <div className="form-label">Baseline Win Rate</div>
                                            <div className="font-quant" style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>{alignData.baseline_winrate ?? 0}%</div>
                                        </div>
                                        <div>
                                            <div className="form-label">Win Rate when {alignData.event_type.replace(/_/g, ' ')} active</div>
                                            <div className="font-quant" style={{ fontSize: 22, fontWeight: 700, color: 'var(--accent-gold)' }}>{alignData.astro_winrate ?? 0}%</div>
                                        </div>
                                        <div>
                                            <div className="form-label">Astro Active Days</div>
                                            <div className="font-quant" style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>{alignData.astro_active_days} <span className="font-inter" style={{ fontSize: 13, color: 'var(--text-muted)' }}>/ {alignData.total_trading_days}</span></div>
                                        </div>
                                    </div>
                                </div>

                                {/* SENTIMENT MATRIX */}
                                <div className="grid-3" style={{ gap: 16 }}>
                                    {alignData.matrix.map((row: any) => (
                                        <div key={row.sentiment} className="glass-card" style={{ padding: 20 }}>
                                            <div style={{ marginBottom: 16 }}>
                                                <BiasChip bias={row.sentiment} />
                                            </div>

                                            <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
                                                <thead>
                                                    <tr style={{ color: 'var(--text-muted)', textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
                                                        <th style={{ paddingBottom: 8, fontWeight: 600 }}>Condition</th>
                                                        <th style={{ paddingBottom: 8, fontWeight: 600 }}>Win Rate</th>
                                                        <th style={{ paddingBottom: 8, fontWeight: 600 }}>Avg Ret</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr>
                                                        <td style={{ paddingTop: 12, color: 'var(--text-primary)', fontWeight: 500 }}>All Days</td>
                                                        <td style={{ paddingTop: 12, fontWeight: 700 }} className="num">{row.combined.win_rate ?? '—'}%</td>
                                                        <td style={{ paddingTop: 12 }} className="num">{row.combined.avg_return != null ? `${row.combined.avg_return > 0 ? '+' : ''}${row.combined.avg_return.toFixed(2)}%` : '—'}</td>
                                                    </tr>
                                                    <tr>
                                                        <td style={{ paddingTop: 8, color: 'var(--accent-gold)', fontWeight: 600 }}>+ Astro Event</td>
                                                        <td style={{ paddingTop: 8, color: 'var(--accent-gold)', fontWeight: 800 }} className="num">{row.with_astro.win_rate ?? '—'}%</td>
                                                        <td style={{ paddingTop: 8, color: 'var(--accent-gold)' }} className="num">{row.with_astro.avg_return != null ? `${row.with_astro.avg_return > 0 ? '+' : ''}${row.with_astro.avg_return.toFixed(2)}%` : '—'}</td>
                                                    </tr>
                                                    <tr>
                                                        <td style={{ paddingTop: 8, color: 'var(--text-muted)' }}>No Astro</td>
                                                        <td style={{ paddingTop: 8 }} className="num">{row.without_astro.win_rate ?? '—'}%</td>
                                                        <td style={{ paddingTop: 8 }} className="num">{row.without_astro.avg_return != null ? `${row.without_astro.avg_return > 0 ? '+' : ''}${row.without_astro.avg_return.toFixed(2)}%` : '—'}</td>
                                                    </tr>
                                                </tbody>
                                            </table>

                                            <div style={{ marginTop: 14, fontSize: 11, color: 'var(--text-muted)' }}>
                                                {row.with_astro.count} signals with astro vs {row.without_astro.count} without
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
            {planModal}
        </>
    );
}
