import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Clock } from 'lucide-react';

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
    const [error, setError] = useState<string | null>(null);

    const fetchMarketData = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/market/live');
            if (!response.ok) {
                throw new Error('Failed to fetch market data');
            }
            const data = await response.json();
            if (data.success && data.data) {
                setMarketData(data.data);
                setError(null);
            } else {
                throw new Error('Invalid data format');
            }
        } catch (err) {
            console.error('Error fetching market data:', err);
            // Keep existing data if fetch fails, but show error
            if (marketData.length === 0) {
                setError('Market data unavailable');
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMarketData();

        // Refresh every minute
        const intervalId = setInterval(fetchMarketData, 60000);

        return () => clearInterval(intervalId);
    }, []);

    if (loading && marketData.length === 0) {
        return (
            <div style={{
                width: '100%',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '16px',
                padding: '16px 0',
                marginBottom: '24px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-muted)', fontSize: '14px', gap: '8px' }}>
                    <Clock size={16} className="animate-spin" />
                    <span>Syncing live market feeds...</span>
                </div>
            </div>
        );
    }

    if (error && marketData.length === 0) {
        return null; // Don't show anything if we can't load data initially
    }

    return (
        <div
            style={{
                width: '100%',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '16px',
                padding: '14px 0',
                marginBottom: '24px',
                overflow: 'hidden',
                display: 'flex',
                position: 'relative',
                boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
                maskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)',
                WebkitMaskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)'
            }}
        >
            {/* Ticker Animation */}
            <div
                className="flex animate-marquee whitespace-nowrap hover:[animation-play-state:paused] w-max items-center"
                style={{
                    willChange: 'transform',
                    backfaceVisibility: 'hidden',
                    transform: 'translateZ(0)'
                }}
            >
                {/* Double the array to create a loop effect */}
                {[...marketData, ...marketData, ...marketData].map((item, index) => (
                    <div
                        key={`${item.symbol}-${index}`}
                        style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '0 32px', cursor: 'default' }}
                    >
                        <span style={{ fontWeight: 800, color: 'var(--text-muted)', fontSize: '13px', letterSpacing: '0.5px' }}>
                            {item.name}
                        </span>
                        <span style={{ fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums', fontWeight: 600, color: 'var(--text-primary)', fontSize: '15px' }}>
                            {item.priceStr}
                        </span>
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: '4px', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums', fontSize: '13px', fontWeight: 600,
                            padding: '4px 8px', borderRadius: '6px',
                            backgroundColor: item.isPositive ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                            color: item.isPositive ? '#4ade80' : '#f87171'
                        }}>
                            {item.isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                            <span>
                                {item.change > 0 ? '+' : ''}{item.change.toFixed(2)} ({item.change > 0 ? '+' : ''}{item.changePct.toFixed(2)}%)
                            </span>
                        </div>

                        {/* Visual separator */}
                        <div style={{ height: '16px', width: '1px', background: 'var(--border-subtle)', marginLeft: '32px' }} />
                    </div>
                ))}
            </div>

            <style dangerouslySetInnerHTML={{
                __html: `
                @keyframes marquee {
                    0% { transform: translate3d(0, 0, 0); }
                    100% { transform: translate3d(-33.33%, 0, 0); }
                }
                .animate-marquee {
                    animation: marquee 35s linear infinite;
                }
            `}} />
        </div>
    );
}
