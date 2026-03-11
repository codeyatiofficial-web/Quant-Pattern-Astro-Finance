'use client';
import React, { useState, useEffect } from 'react';
import {
    Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

export default function IntradayForecastWidget() {
    const [sp500Result, setSp500Result] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        let isMounted = true;
        const fetchIntraday = async () => {
            try {
                const res = await fetch(`${API}/api/correlation/sp500-intraday?market=NSE`);
                const data = await res.json();
                if (!res.ok || data.error) throw new Error(data.error || 'Error');
                if (isMounted) setSp500Result(data);
            } catch (err) {
                if (isMounted) setError('Could not load short-term correlation data.');
            }
            if (isMounted) setLoading(false);
        };

        fetchIntraday();

        // Auto-refresh the 1-hour intraday prediction every 60 seconds
        const interval = setInterval(fetchIntraday, 60000);

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, []);

    if (loading) {
        return (
            <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 16,
                padding: '20px 24px', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 12
            }}>
                <span className="spinner" style={{ width: 24, height: 24, borderWidth: 2 }} />
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Calculating real-time 1-hour forecast...</span>
            </div>
        );
    }

    if (error || !sp500Result) return null;

    const sig5 = sp500Result.timeframes['5m']?.combined_signal || 0;
    const sig15 = sp500Result.timeframes['15m']?.combined_signal || 0;

    // Create smoothly interpolated signals up to 15m
    const sig3 = sig5 * 0.6;
    const sig6 = sig5 * 1.2;
    const sig9 = (sig5 + sig15) * 0.45;
    const sig12 = (sig5 + sig15) * 0.75;
    const sig15_final = sig15;

    const path = [
        0,
        sig3 * 10,
        (sig3 + sig6) * 10,
        (sig3 + sig6 + sig9) * 10,
        (sig3 + sig6 + sig9 + sig12) * 10,
        (sig3 + sig6 + sig9 + sig12 + sig15_final) * 10
    ];

    const overallForecast = path[5] > 0.5 ? 'Strong Bullish' : path[5] > 0 ? 'Bullish' : path[5] < -0.5 ? 'Strong Bearish' : path[5] < 0 ? 'Bearish' : 'Neutral';
    const pathColor = path[5] > 0 ? '#10b981' : path[5] < 0 ? '#ef4444' : '#f59e0b';
    const pathGradientFill = path[5] > 0 ? 'rgba(16, 185, 129, 0.1)' : path[5] < 0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)';

    const forecastData = {
        labels: ['Now', '+3m', '+6m', '+9m', '+12m', '+15m'],
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
            x: { display: true, ticks: { color: 'rgba(255,255,255,0.6)', font: { size: 10 } }, grid: { display: false } },
            y: { display: false, grid: { display: false } }
        },
        interaction: { intersect: false, mode: 'index' as const },
    };

    return (
        <div style={{
            background: 'var(--bg-card)', border: `1px solid ${pathColor}40`, borderRadius: 16,
            padding: '20px 24px', marginBottom: 24, position: 'relative', overflow: 'hidden'
        }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <span style={{ fontSize: 18 }}></span>
                        <h3 style={{ fontSize: 15, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: 0.5, margin: 0, textTransform: 'uppercase' }}>
                            Live 15-Minute Intraday Forecast
                        </h3>
                    </div>
                    <p style={{ fontSize: 11, color: 'var(--text-muted)', margin: 0 }}>
                        Real-time trajectory projection based on immediately overlapping global signals
                    </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <span className={`badge ${path[5] > 0 ? 'badge-bullish' : path[5] < 0 ? 'badge-bearish' : 'badge-neutral'}`} style={{ fontSize: 13, padding: '5px 12px' }}>
                        {path[5] > 0 ? '▲' : path[5] < 0 ? '▼' : '●'} {overallForecast}
                    </span>
                </div>
            </div>

            <div style={{ height: 220, width: '100%', position: 'relative', background: 'rgba(0,0,0,0.1)', borderRadius: 12, padding: 8 }}>
                <Line data={forecastData} options={forecastOptions as any} />
            </div>

            <div style={{ fontSize: 10, color: 'var(--text-muted)', textAlign: 'center', marginTop: 12 }}>
                This is a live forward-looking projection correlating Nifty against 5 Global Futures.
                <span style={{ opacity: 0.6 }}> (15m max projection window)</span>
            </div>
        </div>
    );
}
