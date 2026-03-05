'use client';
/**
 * PlanContext — Subscription Access Code System
 *
 * HOW IT WORKS FOR THE OWNER (YOU):
 * ─────────────────────────────────
 * Underneath are 50 unique codes for Pro and Elite.
 * When a customer pays, send them ONE unused code.
 * The app will store it and timestamp it. It auto-expires in exactly 1 year.
 *
 * MASTER CODES:
 *   Use 'QMASTER-PRO-LIFE' or 'QMASTER-ELITE-LIFE' for your own lifetime access.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

// ─── MASTER CODES (Lifetime access, no expiration) ───────────────────────────
const MASTER_PRO = 'QMASTER-PRO-LIFE';
const MASTER_ELITE = 'QMASTER-ELITE-LIFE';

// ─── 50 PRO CODES (Unlocks 15 Years) ──────────────────────────────────────────
const PRO_CODES: string[] = [
    'QPRO-2025-A1', 'QPRO-2025-A2', 'QPRO-2025-A3', 'QPRO-2025-A4', 'QPRO-2025-A5',
    'QPRO-2025-B1', 'QPRO-2025-B2', 'QPRO-2025-B3', 'QPRO-2025-B4', 'QPRO-2025-B5',
    'QPRO-2025-C1', 'QPRO-2025-C2', 'QPRO-2025-C3', 'QPRO-2025-C4', 'QPRO-2025-C5',
    'QPRO-2025-D1', 'QPRO-2025-D2', 'QPRO-2025-D3', 'QPRO-2025-D4', 'QPRO-2025-D5',
    'QPRO-2025-E1', 'QPRO-2025-E2', 'QPRO-2025-E3', 'QPRO-2025-E4', 'QPRO-2025-E5',
    'QPRO-2025-F1', 'QPRO-2025-F2', 'QPRO-2025-F3', 'QPRO-2025-F4', 'QPRO-2025-F5',
    'QPRO-2025-G1', 'QPRO-2025-G2', 'QPRO-2025-G3', 'QPRO-2025-G4', 'QPRO-2025-G5',
    'QPRO-2025-H1', 'QPRO-2025-H2', 'QPRO-2025-H3', 'QPRO-2025-H4', 'QPRO-2025-H5',
    'QPRO-2025-I1', 'QPRO-2025-I2', 'QPRO-2025-I3', 'QPRO-2025-I4', 'QPRO-2025-I5',
    'QPRO-2025-J1', 'QPRO-2025-J2', 'QPRO-2025-J3', 'QPRO-2025-J4', 'QPRO-2025-J5',
];

// ─── 50 ELITE CODES (Unlocks 30+ Years) ───────────────────────────────────────
const ELITE_CODES: string[] = [
    'QELT-2025-X1', 'QELT-2025-X2', 'QELT-2025-X3', 'QELT-2025-X4', 'QELT-2025-X5',
    'QELT-2025-X6', 'QELT-2025-X7', 'QELT-2025-X8', 'QELT-2025-X9', 'QELT-2025-X10',
    'QELT-2025-Y1', 'QELT-2025-Y2', 'QELT-2025-Y3', 'QELT-2025-Y4', 'QELT-2025-Y5',
    'QELT-2025-Y6', 'QELT-2025-Y7', 'QELT-2025-Y8', 'QELT-2025-Y9', 'QELT-2025-Y10',
    'QELT-2025-Z1', 'QELT-2025-Z2', 'QELT-2025-Z3', 'QELT-2025-Z4', 'QELT-2025-Z5',
    'QELT-2025-Z6', 'QELT-2025-Z7', 'QELT-2025-Z8', 'QELT-2025-Z9', 'QELT-2025-Z10',
    'QELT-2025-W1', 'QELT-2025-W2', 'QELT-2025-W3', 'QELT-2025-W4', 'QELT-2025-W5',
    'QELT-2025-W6', 'QELT-2025-W7', 'QELT-2025-W8', 'QELT-2025-W9', 'QELT-2025-W10',
    'QELT-2025-V1', 'QELT-2025-V2', 'QELT-2025-V3', 'QELT-2025-V4', 'QELT-2025-V5',
    'QELT-2025-V6', 'QELT-2025-V7', 'QELT-2025-V8', 'QELT-2025-V9', 'QELT-2025-V10',
];

// ─────────────────────────────────────────────────────────────────────────────

export type PlanTier = 'free' | 'pro' | 'elite';

const STORAGE_KEY = 'qp_plan_access';
const ONE_YEAR_MS = 365 * 24 * 60 * 60 * 1000;

interface SavedPlan {
    code: string;
    activatedAt: number; // Unix timestamp
}

export interface PlanContextValue {
    tier: PlanTier;
    activatedCode: string | null;
    expiresAt: number | null;
    activateCode: (code: string) => { success: boolean; tier: PlanTier; message: string };
    deactivate: () => void;
    canAccess: (requiredYears: number) => boolean;
}

const PlanContext = createContext<PlanContextValue | null>(null);

function detectTier(code: string): PlanTier | null {
    const upper = code.trim().toUpperCase();
    if (upper === MASTER_ELITE || ELITE_CODES.includes(upper)) return 'elite';
    if (upper === MASTER_PRO || PRO_CODES.includes(upper)) return 'pro';
    return null;
}

function isMasterCode(code: string): boolean {
    const upper = code.trim().toUpperCase();
    return upper === MASTER_ELITE || upper === MASTER_PRO;
}

export function PlanProvider({ children }: { children: React.ReactNode }) {
    const [tier, setTier] = useState<PlanTier>('free');
    const [activatedCode, setActivatedCode] = useState<string | null>(null);
    const [expiresAt, setExpiresAt] = useState<number | null>(null);

    // Restore and validate from localStorage
    useEffect(() => {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return;

            const saved: SavedPlan = JSON.parse(raw);
            const detected = detectTier(saved.code);

            if (!detected) {
                localStorage.removeItem(STORAGE_KEY);
                return;
            }

            // Check expiration (Master codes never expire)
            if (!isMasterCode(saved.code)) {
                const now = Date.now();
                const expirationDate = saved.activatedAt + ONE_YEAR_MS;

                if (now > expirationDate) {
                    // Expired
                    localStorage.removeItem(STORAGE_KEY);
                    console.warn('Plan code expired.');
                    return;
                }
                setExpiresAt(expirationDate);
            }

            setTier(detected);
            setActivatedCode(saved.code);

        } catch {
            localStorage.removeItem(STORAGE_KEY); // clean up bad data
        }
    }, []);

    const activateCode = useCallback((code: string): { success: boolean; tier: PlanTier; message: string } => {
        const detected = detectTier(code);
        if (!detected) {
            return { success: false, tier: 'free', message: '❌ Invalid code.' };
        }

        const now = Date.now();
        const upperCode = code.trim().toUpperCase();

        const payload: SavedPlan = {
            code: upperCode,
            activatedAt: now,
        };

        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(payload)); } catch { }

        setTier(detected);
        setActivatedCode(upperCode);

        if (isMasterCode(upperCode)) {
            setExpiresAt(null);
            return {
                success: true, tier: detected,
                message: '👑 Lifetime Master Code activated!',
            };
        } else {
            setExpiresAt(now + ONE_YEAR_MS);
            return {
                success: true, tier: detected,
                message: detected === 'elite'
                    ? '🏆 Elite plan activated for 1 Year! All premium features unlocked.'
                    : '🚀 Pro plan activated for 1 Year! Up to 15-year historical data unlocked.',
            };
        }
    }, []);

    const deactivate = useCallback(() => {
        try { localStorage.removeItem(STORAGE_KEY); } catch { }
        setTier('free');
        setActivatedCode(null);
        setExpiresAt(null);
    }, []);

    /** Returns true if user's plan can access analysis for this many years */
    const canAccess = useCallback((requiredYears: number): boolean => {
        if (requiredYears <= 1) return true;          // free
        if (requiredYears <= 15) return tier !== 'free'; // pro or elite
        return tier === 'elite';                         // elite only (16–99yr)
    }, [tier]);

    return (
        <PlanContext.Provider value={{ tier, activatedCode, expiresAt, activateCode, deactivate, canAccess }}>
            {children}
        </PlanContext.Provider>
    );
}

export function usePlan(): PlanContextValue {
    const ctx = useContext(PlanContext);
    if (!ctx) throw new Error('usePlan must be used inside <PlanProvider>');
    return ctx;
}
