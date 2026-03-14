import React, { useEffect, useState } from 'react';

interface MarketData {
    name: string;
    symbol: string;
    price: number;
    priceStr: string;
    change: number;
    changePct: number;
    isPositive: boolean;
}

export function MarketTicker() {
    const [marketData, setMarketData] = useState<MarketData[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchMarketData = async () => {
        try {
            const r = await fetch('/api/market/live');
            if (!r.ok) throw new Error('Failed');
            const d = await r.json();
            if (d.success && d.data) setMarketData(d.data);
        } catch (e) {
            console.error('Ticker fetch error:', e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMarketData();
        const id = setInterval(fetchMarketData, 60000);
        return () => clearInterval(id);
    }, []);

    if (loading && marketData.length === 0) {
        return (
            <div className="ticker-wrap" style={{ justifyContent: 'center' }}>
                <span style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: 1 }}>SYNCING MARKET FEEDS…</span>
            </div>
        );
    }

    if (marketData.length === 0) return null;

    // Double items for seamless infinite loop
    const items = [...marketData, ...marketData];

    return (
        <div className="ticker-wrap">
            <span className="ticker-badge">LIVE</span>
            <div className="ticker-track">
                <div className="ticker-scroll">
                    {items.map((item, i) => (
                        <span key={i} className="ticker-item">
                            <span className="ticker-name">{item.name}</span>
                            <span className="ticker-price">{item.priceStr}</span>
                            <span className={`ticker-chg ${item.isPositive ? 'up' : 'down'}`}>
                                {item.isPositive ? '▲' : '▼'}{Math.abs(item.changePct).toFixed(2)}%
                            </span>
                            <span className="ticker-dot">•</span>
                        </span>
                    ))}
                </div>
            </div>
        </div>
    );
}
