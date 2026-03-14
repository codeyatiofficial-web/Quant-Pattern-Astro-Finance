import { useState, useEffect } from "react";
import { Home, LineChart, PieChart, BarChart2, Calendar, FileText, Menu, X, Link as LinkIcon, CheckCircle2, TrendingUp, Lock, Cpu } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { PlanStatusBadge } from './UpgradeModal';
import { usePlan } from '../contexts/PlanContext';

const API = '';

function Logo() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" className="w-[200px] sm:w-[240px] h-auto max-h-[64px] transition-all">
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
        Quant-Pattern
      </text>
      <text x="188" y="160" fontFamily="Inter, sans-serif" fontWeight="600" fontSize="23" style={{ fill: 'var(--text-muted)' }} letterSpacing="4.5">
        PRECISION IN PATTERNS | DATA-DRIVEN TRADING
      </text>
    </svg>
  );
}

export type Page = 'dashboard' | 'nakshatra' | 'technical' | 'correlation' | 'sentiment' | 'events' | 'derivatives' | 'algo' | 'settings';

const ALL_LINKS: { key: Page; label: string; fullName: string; icon: any; proOnly?: boolean; eliteOnly?: boolean }[] = [
  { key: 'dashboard', label: 'Dashboard', fullName: 'Dashboard', icon: Home },
  { key: 'nakshatra', label: 'Cycle Analysis', fullName: 'Cycle Analysis', icon: BarChart2, eliteOnly: true },
  { key: 'technical', label: 'Technical', fullName: 'Technical Analysis', icon: LineChart },
  { key: 'derivatives', label: 'Derivatives', fullName: 'Derivatives', icon: TrendingUp },
  { key: 'sentiment', label: 'Predictions', fullName: 'Daily Predictions', icon: Calendar, proOnly: true },
  { key: 'events', label: 'Events', fullName: 'Economic Events', icon: FileText },
  { key: 'correlation', label: 'Signal Correlation', fullName: 'Signal Correlation', icon: PieChart, proOnly: true },
  { key: 'algo', label: 'Algo trading', fullName: 'Algo trading', icon: Cpu, eliteOnly: true },
  { key: 'settings', label: 'Settings', fullName: 'Settings', icon: Menu, eliteOnly: true }, // or another icon like Settings if imported
];

interface NavigationProps {
  activePage: Page;
  onNavigate: (page: Page) => void;
}

export default function Navigation({ activePage, onNavigate }: NavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [kiteConnected, setKiteConnected] = useState<boolean | null>(null);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [tokenInput, setTokenInput] = useState('');
  const [tokenStatus, setTokenStatus] = useState<string | null>(null);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const { tier } = usePlan();
  const isFree = tier === 'free';
  const isElite = tier === 'elite';

  const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost';

  useEffect(() => {
    fetch(`${API}/api/kite/status`)
      .then(res => res.json())
      .then(data => setKiteConnected(data.authenticated))
      .catch(err => console.error("Kite status check failed:", err));
  }, []);

  const handleKiteLogin = () => {
    const backendUrl = API || window.location.origin;
    window.location.href = `${backendUrl}/api/kite/redirect`;
  };

  const handlePasteToken = async () => {
    if (!tokenInput.trim()) return;
    setTokenStatus('Connecting...');
    try {
      const res = await fetch(`${API}/api/kite/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ access_token: tokenInput.trim() }),
      });
      const data = await res.json();
      if (data.success) {
        setTokenStatus(' ' + data.message);
        setKiteConnected(true);
        setTimeout(() => { setShowTokenModal(false); setTokenStatus(null); setTokenInput(''); }, 1500);
      } else {
        setTokenStatus(' ' + (data.message || 'Token invalid or expired'));
      }
    } catch (e) {
      setTokenStatus(' Network error — is backend running on port 8000?');
    }
  };

  const handleOpenKiteLogin = () => {
    const backendUrl = API || window.location.origin;
    window.open(`${backendUrl}/api/kite/redirect`, '_blank');
  };

  const handleNavClick = (link: typeof ALL_LINKS[0]) => {
    if (link.eliteOnly && !isElite) {
      setShowUpgrade(true);
      return;
    }
    if (link.proOnly && isFree) {
      setShowUpgrade(true);
      return;
    }
    onNavigate(link.key);
  };

  // Dynamically import UpgradeModal only when needed to avoid circular deps
  const [UpgradeModal, setUpgradeModalComp] = useState<any>(null);
  useEffect(() => {
    if (showUpgrade && !UpgradeModal) {
      import('./UpgradeModal').then(m => setUpgradeModalComp(() => m.UpgradeModal));
    }
  }, [showUpgrade]);

  return (
    <>
      {showUpgrade && UpgradeModal && <UpgradeModal onClose={() => setShowUpgrade(false)} />}
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

            {/* Desktop: Kite + Theme */}
            <div className="nav-desktop-actions">
              <PlanStatusBadge />
              {isFree && (
                <button onClick={() => setShowUpgrade(true)} className="btn-upgrade-pro">
                  ✨ Upgrade to Pro
                </button>
              )}
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
              {isFree && (
                <button onClick={() => setShowUpgrade(true)} className="btn-upgrade-pro" style={{ padding: '4px 10px', fontSize: 11, animation: 'none' }}>
                  ✨ Upgrade
                </button>
              )}
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

          <div className="nav-desktop-tabs" style={{ paddingBottom: 12 }}>
            <div style={{
              display: 'flex', gap: 6, alignItems: 'center', justifyContent: 'space-between',
              background: 'var(--bg-card)', padding: '8px 8px', borderRadius: 16,
              border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-card)',
              width: '100%', overflowX: 'auto', scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch'
            }}>
              {ALL_LINKS.map((link) => {
                const Icon = link.icon;
                const active = activePage === link.key;
                const locked = (link.eliteOnly && !isElite) || (link.proOnly && isFree);
                return (
                  <button key={link.key} onClick={() => handleNavClick(link)} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                    padding: '10px 16px', borderRadius: 12, fontSize: 13.5, fontWeight: active ? 700 : 500,
                    whiteSpace: 'nowrap', cursor: 'pointer', border: 'none', transition: 'all 0.3s ease',
                    flex: '1 1 auto', minWidth: 'min-content',
                    background: active ? 'var(--bg-secondary)' : 'transparent',
                    color: locked ? 'var(--text-muted)' : active ? 'var(--text-primary)' : 'var(--text-muted)',
                    boxShadow: active ? 'inset 0 -2px 0 var(--accent-indigo)' : 'none',
                    opacity: locked ? 0.65 : 1,
                  }}>
                    <Icon size={13} />
                    <span>{link.label}</span>
                    {locked && <Lock size={9} style={{ marginLeft: 2, opacity: 0.7 }} />}
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
            {ALL_LINKS.map((link) => {
              const Icon = link.icon;
              const active = activePage === link.key;
              const locked = (link.eliteOnly && !isElite) || (link.proOnly && isFree);
              return (
                <button key={link.key}
                  onClick={() => { handleNavClick(link); setMobileMenuOpen(false); }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '12px 16px', borderRadius: 12, border: 'none',
                    cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s',
                    background: active ? 'rgba(99,102,241,0.12)' : 'transparent',
                    color: locked ? '#6b7280' : active ? 'var(--accent-indigo)' : '#9ca3af',
                    fontWeight: active ? 700 : 500, fontSize: 14,
                    opacity: locked ? 0.7 : 1,
                  }}>
                  <Icon size={18} />
                  <span>{link.fullName}</span>
                  {locked && <Lock size={12} style={{ marginLeft: 'auto', opacity: 0.6 }} />}
                </button>
              );
            })}
          </div>
        )}
      </nav>
    </>
  );
}
