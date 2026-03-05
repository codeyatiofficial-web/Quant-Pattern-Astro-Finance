import { useState, useEffect } from "react";
import { Home, LineChart, PieChart, BarChart2, Calendar, FileText, Menu, X, Link as LinkIcon, CheckCircle2, TrendingUp } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { PlanStatusBadge } from './UpgradeModal';
const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

function Logo() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" className="w-[160px] sm:w-[190px] h-auto max-h-[50px]">
      <defs>
        <linearGradient id="qGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4ea8c7" />
          <stop offset="100%" stopColor="#3b82f6" />
        </linearGradient>
      </defs>
      <g transform="translate(10, 15)">
        <path d="M 60 20 A 70 70 0 1 0 140 120" fill="none" stroke="url(#qGrad)" strokeWidth="12" strokeLinecap="round" />
        <rect x="45" y="80" width="12" height="35" fill="#3b82f6" rx="3" />
        <rect x="70" y="50" width="12" height="65" fill="#4ea8c7" rx="3" />
        <rect x="95" y="65" width="12" height="50" fill="#34d399" rx="3" />
        <path d="M 25 120 L 135 15" fill="none" stroke="#6ee7b7" strokeWidth="14" strokeLinecap="round" />
        <polygon points="115,15 145,5 135,35" fill="#6ee7b7" />
        <circle cx="15" cy="90" r="7" fill="#6ee7b7" />
        <circle cx="45" cy="35" r="7" fill="#4ea8c7" />
        <circle cx="115" cy="150" r="7" fill="#3b82f6" />
        <path d="M 15 90 L 45 35" fill="none" stroke="#4ea8c7" strokeWidth="2" opacity="0.5" />
      </g>
      <text x="185" y="115" fontFamily="Inter, sans-serif" fontWeight="800" fontSize="76" style={{ fill: 'var(--text-primary)' }} letterSpacing="-1">
        quant-pattern
      </text>
      <text x="188" y="160" fontFamily="Inter, sans-serif" fontWeight="600" fontSize="23" style={{ fill: 'var(--text-muted)' }} letterSpacing="4.5">
        PRECISION IN PATTERNS | DATA-DRIVEN TRADING
      </text>
    </svg>
  );
}

export type Page = 'dashboard' | 'nakshatra' | 'technical' | 'correlation' | 'sentiment' | 'events' | 'derivatives';

const links: { key: Page; label: string; fullName: string; icon: any }[] = [
  { key: 'dashboard', label: 'Dashboard', fullName: 'Dashboard', icon: Home },
  { key: 'nakshatra', label: 'Astro Analysis', fullName: 'Astro Analysis', icon: BarChart2 },
  { key: 'technical', label: 'Technical', fullName: 'Technical Analysis', icon: LineChart },
  { key: 'correlation', label: 'Correlation', fullName: 'Astro-Correlation', icon: PieChart },
  { key: 'sentiment', label: 'Predictions', fullName: 'Daily Predictions', icon: Calendar },
  { key: 'events', label: 'Events', fullName: 'Economic Events', icon: FileText },
  { key: 'derivatives', label: 'Derivatives', fullName: 'Derivatives', icon: TrendingUp },
];

interface NavigationProps {
  activePage: Page;
  onNavigate: (page: Page) => void;
}

export default function Navigation({ activePage, onNavigate }: NavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [kiteConnected, setKiteConnected] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(`${API}/api/kite/status`)
      .then(res => res.json())
      .then(data => setKiteConnected(data.authenticated))
      .catch(err => console.error("Kite status check failed:", err));
  }, []);

  const handleKiteLogin = () => {
    // Navigate directly - the backend will redirect to Kite login page,
    // and Kite will redirect back to /api/kite/callback after successful login.
    window.location.href = `${window.location.origin}/api/kite/redirect`;
  };

  return (
    <nav style={{
      position: 'fixed', width: '100%', zIndex: 50, top: 0, left: 0,
      background: 'var(--bg-card)', borderBottom: '1px solid var(--border-active)',
      backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)', transition: 'background 0.3s, border-color 0.3s',
      boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)',
    }}>
      <div style={{ maxWidth: 1600, margin: '0 auto', padding: '0 16px' }}>
        {/* Row 1: Logo + Kite/Theme + Mobile hamburger */}
        <div style={{ height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <button onClick={() => onNavigate('dashboard')} style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: 0 }}>
            <Logo />
          </button>

          {/* Desktop: Kite + Theme — use inline media query via CSS class */}
          <div className="nav-desktop-actions">
            <PlanStatusBadge />
            {kiteConnected === true ? (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 6, padding: '4px 12px',
                background: 'rgba(16,185,129,0.1)', color: '#10b981', fontSize: 12, fontWeight: 600,
                borderRadius: 20, border: '1px solid rgba(16,185,129,0.2)',
              }}>
                <CheckCircle2 size={14} /> Kite Live
              </div>
            ) : kiteConnected === false ? (
              <button onClick={handleKiteLogin} style={{
                display: 'flex', alignItems: 'center', gap: 6, padding: '4px 12px',
                background: 'var(--accent-indigo)', color: 'white', fontSize: 12, fontWeight: 600,
                borderRadius: 20, border: 'none', cursor: 'pointer',
              }}>
                <LinkIcon size={14} /> Connect Kite
              </button>
            ) : null}
            <ThemeToggle />
          </div>

          {/* Mobile hamburger + theme */}
          <div className="nav-mobile-actions">
            {kiteConnected === false && (
              <button onClick={handleKiteLogin} style={{
                padding: '4px 10px', background: 'var(--accent-indigo)', color: 'white',
                fontSize: 11, fontWeight: 600, borderRadius: 8, border: 'none', cursor: 'pointer',
              }}>
                Connect
              </button>
            )}
            <ThemeToggle />
            <button onClick={() => setMobileMenuOpen(x => !x)} style={{
              background: 'none', border: 'none', cursor: 'pointer', padding: 8, color: '#9ca3af',
            }}>
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Row 2: Desktop tab bar */}
        <div className="nav-desktop-tabs">
          <div style={{
            display: 'inline-flex', gap: 6, alignItems: 'center',
            background: 'var(--bg-card)', padding: '6px 8px', borderRadius: 14,
            border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-card)',
          }}>
            {links.map((link) => {
              const Icon = link.icon;
              const active = activePage === link.key;
              return (
                <button key={link.key} onClick={() => onNavigate(link.key)} style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '8px 20px', borderRadius: 10, fontSize: 14, fontWeight: active ? 700 : 500,
                  whiteSpace: 'nowrap', cursor: 'pointer', border: 'none', transition: 'all 0.3s ease',
                  background: active ? 'linear-gradient(135deg, rgba(99,102,241,0.2) 0%, rgba(139,92,246,0.1) 100%)' : 'transparent',
                  color: active ? 'var(--text-primary)' : 'var(--text-muted)',
                  boxShadow: active ? 'inset 0 -2px 0 var(--accent-indigo)' : 'none',
                }}>
                  <Icon size={14} />
                  <span>{link.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileMenuOpen && (
        <div className="nav-mobile-dropdown" style={{
          position: 'absolute', top: 56, left: 0, width: '100%',
          background: 'var(--bg-primary)', borderBottom: '1px solid var(--border-subtle)',
          boxShadow: '0 12px 30px rgba(0,0,0,0.3)', padding: 16,
          display: 'flex', flexDirection: 'column', gap: 8, zIndex: 50,
        }}>
          {links.map((link) => {
            const Icon = link.icon;
            const active = activePage === link.key;
            return (
              <button key={link.key}
                onClick={() => { onNavigate(link.key); setMobileMenuOpen(false); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '12px 16px', borderRadius: 12, border: 'none',
                  cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s',
                  background: active ? 'rgba(99,102,241,0.12)' : 'transparent',
                  color: active ? 'var(--accent-indigo)' : '#9ca3af',
                  fontWeight: active ? 700 : 500, fontSize: 14,
                }}>
                <Icon size={18} />
                <span>{link.fullName}</span>
              </button>
            );
          })}
        </div>
      )}
    </nav>
  );
}
