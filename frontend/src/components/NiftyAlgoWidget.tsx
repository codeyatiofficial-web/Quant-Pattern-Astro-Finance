'use client';

import React from 'react';

export default function NiftyAlgoWidget() {
    const whatsappUrl = 'https://wa.me/message/QUANTPATTERN';

    const features = [
        { icon: '🎯', text: '80% accuracy on our live algo setups' },
        { icon: '⚡', text: '1–2 precision trades/day — quality over quantity' },
        { icon: '🔧', text: 'Custom setup tailored to your strategy' },
        { icon: '📊', text: 'Equity · Commodity · Currency markets' },
        { icon: '🤖', text: 'Pre-built strategies ready to deploy' },
        { icon: '💰', text: 'Minimal charges to link your account' },
    ];

    return (
        <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 16,
            padding: '32px 28px',
            marginBottom: 24,
        }}>
            {/* Header */}
            <div style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                    <span style={{ fontSize: 24 }}>🤖</span>
                    <h2 style={{ fontSize: 22, fontWeight: 900, color: 'var(--text-primary)', margin: 0, letterSpacing: 0.5 }}>
                        ALGO TRADING
                    </h2>
                    <span style={{
                        fontSize: 10, fontWeight: 800, padding: '2px 8px', borderRadius: 6,
                        background: 'rgba(74,222,128,0.15)', color: '#4ade80',
                        border: '1px solid rgba(74,222,128,0.3)', letterSpacing: 1
                    }}>LIVE</span>
                </div>
                <p style={{ fontSize: 15, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6, maxWidth: 700 }}>
                    Let the system trade for you. Connect your broker via API key. Every trade executes automatically —
                    <strong style={{ color: 'var(--text-primary)' }}> no screen watching, no emotional decisions.</strong>
                </p>
            </div>

            {/* Features Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                gap: 12,
                marginBottom: 24,
            }}>
                {features.map((f, i) => (
                    <div key={i} style={{
                        display: 'flex', alignItems: 'center', gap: 10,
                        background: 'var(--bg-secondary)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 10, padding: '12px 16px',
                    }}>
                        <span style={{ fontSize: 18 }}>{f.icon}</span>
                        <span style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500 }}>{f.text}</span>
                    </div>
                ))}
            </div>

            {/* Bottom strip */}
            <div style={{
                background: 'rgba(37,211,102,0.07)',
                border: '1px solid rgba(37,211,102,0.25)',
                borderRadius: 12, padding: '20px 24px',
            }}>
                {/* Tagline */}
                <div style={{
                    fontSize: 16, fontWeight: 800, color: 'var(--text-primary)',
                    marginBottom: 6, letterSpacing: 0.3,
                }}>
                    🚀 No stress. No screen time. Just results.
                </div>

                {/* CTA text — prominent */}
                <div style={{
                    fontSize: 14, color: '#4ade80', fontWeight: 600, marginBottom: 16,
                }}>
                    💬 More details? Chat with us on WhatsApp — we'll help you get started!
                </div>

                {/* WhatsApp button — full-width on mobile, auto on desktop */}
                <a
                    href={whatsappUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                        display: 'inline-flex', alignItems: 'center', gap: 10,
                        background: '#25D366', color: '#fff',
                        padding: '12px 28px', borderRadius: 10,
                        fontSize: 15, fontWeight: 800, textDecoration: 'none',
                        boxShadow: '0 4px 14px rgba(37,211,102,0.35)',
                        transition: 'opacity 0.2s, transform 0.15s',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.opacity = '0.9'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
                    onMouseLeave={e => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.transform = 'translateY(0)'; }}
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                    </svg>
                    Chat on WhatsApp
                </a>
            </div>
        </div>
    );
}
