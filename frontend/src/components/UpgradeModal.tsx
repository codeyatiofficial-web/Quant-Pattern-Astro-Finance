'use client';
import React, { useState, useEffect, useCallback } from 'react';
import { usePlan, PlanTier } from '../contexts/PlanContext';

//  WhatsApp config 
const WA_NUMBER = '919193112255';
const WA_MESSAGE = encodeURIComponent(
    'Hi! I want to subscribe to Quant-Pattern Premium to unlock extended historical analysis. Please share payment details.'
);
const WA_URL = `https://wa.me/${WA_NUMBER}?text=${WA_MESSAGE}`;

//  Plans 
const PLANS = [
    {
        name: 'Free',
        price: '₹0',
        period: '/forever',
        color: '#64748b',
        tier: 'free' as PlanTier,
        features: ['7-Day AI Signal Forecast', 'Technical & Derivatives Analysis', 'Economic Events Calendar', 'Live Market Prices'],
        cta: 'Current Plan',
        disabled: true,
    },
    {
        name: 'Pro',
        price: '₹9,999',
        period: '/year',
        color: '#6366f1',
        tier: 'pro' as PlanTier,
        features: ['Up to 15 Years Historical Data', 'All Free Features', 'Cycle Pattern Analysis', 'Signal Correlation Engine', 'Daily Predictions', 'Derivatives Strategy Tool', 'Priority Support'],
        cta: 'Upgrade to Pro',
        disabled: false,
        badge: 'Popular',
    },
    {
        name: 'Elite',
        price: '₹19,999',
        period: '/year',
        color: 'var(--text-primary)',
        tier: 'elite' as PlanTier,
        features: ['Max 30+ Years Historical Data', 'All Pro Features', 'Full Signal Backtesting', '1-Month AI Forecast', 'Custom Alerts', 'Dedicated WhatsApp Support'],
        cta: 'Upgrade to Elite',
        disabled: false,
        badge: 'Best Value',
    },
];

//  Plan Status Banner (shown in app corner when plan is active) 
export function PlanStatusBadge() {
    const { tier, expiresAt, deactivate } = usePlan();
    if (tier === 'free') return null;

    const expiryText = expiresAt
        ? `Valid till ${new Date(expiresAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}`
        : 'Lifetime Access';

    return (
        <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: tier === 'elite' ? 'var(--bg-secondary)' : 'linear-gradient(135deg,#6366f133,#4f46e533)',
            border: `1px solid ${tier === 'elite' ? 'var(--border-active)' : '#6366f155'}`,
            borderRadius: 30, padding: '5px 14px', fontSize: 12, fontWeight: 700,
            color: tier === 'elite' ? 'var(--text-primary)' : '#a5b4fc',
        }}>
            {tier === 'elite' ? ' Elite' : ' Pro'}
            <span style={{ fontSize: 10, opacity: 0.8, fontWeight: 500, borderLeft: '1px solid rgba(255,255,255,0.2)', paddingLeft: 8 }}>
                {expiryText}
            </span>
            <button onClick={deactivate} title="Deactivate plan" style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'inherit', opacity: 0.5, fontSize: 14, padding: 0, marginLeft: 4
            }}>×</button>
        </div>
    );
}

//  Upgrade Modal 
export function UpgradeModal({ onClose }: { onClose: () => void }) {
    const { tier, expiresAt, activateCode } = usePlan();
    const [code, setCode] = useState('');
    const [msg, setMsg] = useState('');
    const [ok, setOk] = useState(false);
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
        document.addEventListener('keydown', handler);
        return () => document.removeEventListener('keydown', handler);
    }, [onClose]);

    const handleActivate = () => {
        if (!code.trim()) { setMsg('Please enter your access code.'); return; }
        setBusy(true);
        setTimeout(() => {                          // tiny delay for UX feedback
            const result = activateCode(code.trim());
            setMsg(result.message);
            setOk(result.success);
            setBusy(false);
            if (result.success) {
                setTimeout(() => onClose(), 2200); // auto-close after success
            }
        }, 400);
    };

    const expiryText = expiresAt
        ? `Valid till ${new Date(expiresAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}`
        : 'Lifetime Access';

    return (
        <div
            onClick={e => { if (e.target === e.currentTarget) onClose(); }}
            style={{
                position: 'fixed', inset: 0, zIndex: 9999,
                background: 'rgba(0,0,0,0.78)', backdropFilter: 'blur(10px)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                padding: '20px',
            }}
        >
            <div style={{
                background: 'linear-gradient(145deg, #0f172a 0%, #1e1b4b 100%)',
                border: '1px solid rgba(99,102,241,0.3)',
                borderRadius: 22, width: '100%', maxWidth: 820,
                boxShadow: '0 30px 90px rgba(99,102,241,0.22)',
                overflow: 'hidden', position: 'relative',
            }}>
                {/* Close */}
                <button onClick={onClose} style={{
                    position: 'absolute', top: 16, right: 16, width: 34, height: 34,
                    borderRadius: '50%', border: '1px solid rgba(255,255,255,0.1)',
                    background: 'rgba(255,255,255,0.05)', color: '#94a3b8',
                    fontSize: 18, cursor: 'pointer', display: 'flex',
                    alignItems: 'center', justifyContent: 'center', zIndex: 1,
                }}>×</button>

                {/* Header */}
                <div style={{ padding: '32px 32px 18px', textAlign: 'center' }}>
                    <div style={{ fontSize: 40, marginBottom: 8 }}></div>
                    <h2 style={{ fontSize: 24, fontWeight: 800, color: 'white', marginBottom: 6 }}>
                        Unlock Extended Analysis
                    </h2>
                    <p style={{ color: '#94a3b8', fontSize: 14, maxWidth: 500, margin: '0 auto' }}>
                        Your <strong style={{ color: '#a78bfa' }}>Free plan</strong> includes 1 year of data.
                        Upgrade to analyse up to 30 years for statistically reliable insights.
                    </p>
                </div>

                {/* Plan Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, padding: '0 24px 20px' }}>
                    {PLANS.map(plan => {
                        const isActive = tier === plan.tier;
                        return (
                            <div key={plan.name} style={{
                                border: `1px solid ${isActive ? plan.color : plan.color + '40'}`,
                                borderRadius: 16, padding: '22px 16px',
                                background: isActive ? `${plan.color}14` : `${plan.color}08`,
                                position: 'relative',
                                boxShadow: isActive ? `0 0 20px ${plan.color}30` : 'none',
                            }}>
                                {plan.badge && !isActive && (
                                    <div style={{
                                        position: 'absolute', top: -11, left: '50%', transform: 'translateX(-50%)',
                                        background: plan.color, color: 'white', fontSize: 10, fontWeight: 700,
                                        padding: '3px 12px', borderRadius: 20, letterSpacing: '0.5px', textTransform: 'uppercase',
                                    }}>{plan.badge}</div>
                                )}
                                {isActive && (
                                    <div style={{
                                        position: 'absolute', top: -11, left: '50%', transform: 'translateX(-50%)',
                                        background: plan.color, color: 'white', fontSize: 10, fontWeight: 700,
                                        padding: '3px 12px', borderRadius: 20, letterSpacing: '0.5px',
                                    }}> ACTIVE</div>
                                )}
                                <div style={{ color: plan.color, fontSize: 13, fontWeight: 700, marginBottom: 6 }}>{plan.name}</div>
                                <div style={{ marginBottom: 14 }}>
                                    <span style={{ fontSize: 26, fontWeight: 800, color: 'white' }}>{plan.price}</span>
                                    <span style={{ fontSize: 11, color: '#64748b', marginLeft: 4 }}>{plan.period}</span>
                                </div>
                                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 16px', fontSize: 11, color: '#94a3b8', lineHeight: 1.9 }}>
                                    {plan.features.map(f => (
                                        <li key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                                            <span style={{ color: plan.color }}></span> {f}
                                        </li>
                                    ))}
                                </ul>
                                {!plan.disabled && !isActive && (
                                    <a href={WA_URL} target="_blank" rel="noopener noreferrer" style={{
                                        display: 'block', textAlign: 'center', padding: '9px 12px',
                                        borderRadius: 10, fontSize: 12, fontWeight: 700, textDecoration: 'none',
                                        background: `linear-gradient(135deg, ${plan.color}, ${plan.color}bb)`,
                                        color: 'white',
                                    }}> Buy via WhatsApp</a>
                                )}
                                {isActive && (
                                    <div style={{ textAlign: 'center', fontSize: 12, color: plan.color, fontWeight: 700, padding: '4px 0 0' }}>
                                        Plan Active
                                        <div style={{ fontSize: 10, opacity: 0.8, marginTop: 4, fontWeight: 500 }}>{expiryText}</div>
                                    </div>
                                )}
                                {plan.disabled && !isActive && (
                                    <div style={{ textAlign: 'center', fontSize: 12, color: '#475569', padding: '9px 0' }}>
                                        Current Plan
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/*  Access Code Box  */}
                <div style={{
                    margin: '0 24px 24px',
                    background: 'rgba(99,102,241,0.06)',
                    border: '1px solid rgba(99,102,241,0.2)',
                    borderRadius: 16, padding: '20px 22px',
                }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'white', marginBottom: 4 }}>
                        Have an Access Code?
                    </div>
                    <div style={{ fontSize: 12, color: '#64748b', marginBottom: 14 }}>
                        Enter the code sent to you on WhatsApp after payment. Format: <code style={{ color: '#a78bfa' }}>QPRO-2025-XXXX</code> or <code style={{ color: 'var(--text-primary)' }}>QELT-2025-XXXX</code>
                    </div>
                    <div style={{ display: 'flex', gap: 10 }}>
                        <input
                            type="text"
                            value={code}
                            onChange={e => { setCode(e.target.value.toUpperCase()); setMsg(''); }}
                            onKeyDown={e => { if (e.key === 'Enter') handleActivate(); }}
                            placeholder="e.g. QPRO-2025-STAR"
                            style={{
                                flex: 1, padding: '11px 16px', borderRadius: 10, fontSize: 13,
                                background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(99,102,241,0.3)',
                                color: 'white', outline: 'none', fontFamily: 'monospace',
                                letterSpacing: '1px',
                            }}
                        />
                        <button
                            onClick={handleActivate}
                            disabled={busy}
                            style={{
                                padding: '11px 24px', borderRadius: 10, fontSize: 13, fontWeight: 700,
                                background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                                color: 'white', border: 'none', cursor: busy ? 'wait' : 'pointer',
                                opacity: busy ? 0.7 : 1, whiteSpace: 'nowrap',
                            }}
                        >
                            {busy ? ' Checking…' : ' Activate'}
                        </button>
                    </div>
                    {msg && (
                        <div style={{
                            marginTop: 12, padding: '10px 14px', borderRadius: 10, fontSize: 13,
                            background: ok ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                            border: `1px solid ${ok ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
                            color: ok ? '#34d399' : '#f87171',
                        }}>
                            {msg}
                        </div>
                    )}
                </div>

                {/* WhatsApp footer */}
                <div style={{
                    padding: '14px 24px 24px',
                    borderTop: '1px solid rgba(255,255,255,0.05)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, flexWrap: 'wrap',
                }}>
                    <span style={{ fontSize: 12, color: '#64748b' }}>Questions? Chat with us directly</span>
                    <a href={WA_URL} target="_blank" rel="noopener noreferrer" style={{
                        display: 'inline-flex', alignItems: 'center', gap: 8,
                        background: 'linear-gradient(135deg, #25D366, #128C7E)',
                        color: 'white', textDecoration: 'none', padding: '10px 22px',
                        borderRadius: 30, fontWeight: 700, fontSize: 13,
                        boxShadow: '0 4px 15px rgba(37,211,102,0.25)',
                    }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                        </svg>
                        WhatsApp — +91 91931 22255
                    </a>
                </div>
            </div>
        </div>
    );
}

//  Hook used in all analysis components 
export function usePlanGate(FREE_LIMIT_YEARS = 1) {
    const { canAccess, tier } = usePlan();
    const [showModal, setShowModal] = useState(false);

    /** Returns true if allowed, false if blocked (shows upgrade modal) */
    const guardYears = useCallback((selectedYears: number): boolean => {
        if (canAccess(selectedYears)) return true;
        setShowModal(true);
        return false;
    }, [canAccess]);

    /** For period strings like '1y', '5y', '10y', 'max' */
    const guardPeriod = useCallback((period: string): boolean => {
        const freeSet = new Set(['1y', '1Y', '1']);
        if (freeSet.has(period)) return true;
        // map period string to approximate years
        const yearMap: Record<string, number> = {
            '2y': 2, '3y': 3, '5y': 5, '10y': 10, '15y': 15, 'max': 99,
        };
        const years = yearMap[period.toLowerCase()] ?? 99;
        if (canAccess(years)) return true;
        setShowModal(true);
        return false;
    }, [canAccess]);

    /** Explicit plan override check. Returns true if user has tier >= requiredTierLevel */
    const requirePlan = useCallback((requiredTierLevel: number): boolean => {
        const tiers: Record<PlanTier, number> = { 'free': 0, 'pro': 1, 'elite': 2 };
        if (tiers[tier] >= requiredTierLevel) return true;

        setShowModal(true);
        return false;
    }, [tier]);

    const modal = showModal ? <UpgradeModal onClose={() => setShowModal(false)} /> : null;

    return { guardYears, guardPeriod, requirePlan, modal, tier };
}
