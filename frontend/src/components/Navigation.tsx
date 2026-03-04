import { useState, useEffect } from "react";
import Image from 'next/image';
import { Home, LineChart, PieChart, BarChart2, Calendar, FileText, Menu, X, Link as LinkIcon, CheckCircle2 } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';

const API = 'http://localhost:8000';

function Logo() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" className="w-[180px] sm:w-[220px] h-auto max-h-[45px]">
      <defs>
        <linearGradient id="qGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4ea8c7" />
          <stop offset="100%" stopColor="#3b82f6" />
        </linearGradient>
      </defs>

      {/* Logo Mark */}
      <g transform="translate(10, 15)">
        {/* Outer Arc */}
        <path d="M 60 20 A 70 70 0 1 0 140 120" fill="none" stroke="url(#qGrad)" strokeWidth="12" strokeLinecap="round" />

        {/* Candlesticks */}
        <rect x="45" y="80" width="12" height="35" fill="#3b82f6" rx="3" />
        <rect x="70" y="50" width="12" height="65" fill="#4ea8c7" rx="3" />
        <rect x="95" y="65" width="12" height="50" fill="#34d399" rx="3" />

        {/* Upward Trend Arrow */}
        <path d="M 25 120 L 135 15" fill="none" stroke="#6ee7b7" strokeWidth="14" strokeLinecap="round" />
        <polygon points="115,15 145,5 135,35" fill="#6ee7b7" />

        {/* Connection Nodes */}
        <circle cx="15" cy="90" r="7" fill="#6ee7b7" />
        <circle cx="45" cy="35" r="7" fill="#4ea8c7" />
        <circle cx="115" cy="150" r="7" fill="#3b82f6" />
        <path d="M 15 90 L 45 35" fill="none" stroke="#4ea8c7" strokeWidth="2" opacity="0.5" />
      </g>

      {/* Text Group */}
      <text x="185" y="115" fontFamily="Inter, sans-serif" fontWeight="800" fontSize="76" style={{ fill: 'var(--text-primary)' }} letterSpacing="-1">
        quant-pattern
      </text>

      <text x="188" y="160" fontFamily="Inter, sans-serif" fontWeight="600" fontSize="23" style={{ fill: 'var(--text-muted)' }} letterSpacing="4.5">
        PRECISION IN PATTERNS | DATA-DRIVEN TRADING
      </text>
    </svg>
  );
}

export type Page = 'dashboard' | 'nakshatra' | 'technical' | 'correlation' | 'sentiment' | 'events';

const links: { key: Page; name: string; icon: any }[] = [
  { key: 'dashboard', name: 'Dashboard', icon: Home },
  { key: 'nakshatra', name: 'Nakshatra Scan', icon: BarChart2 },
  { key: 'technical', name: 'Technical Analysis', icon: LineChart },
  { key: 'correlation', name: 'Astro-Correlation', icon: PieChart },
  { key: 'sentiment', name: 'Daily Predictions', icon: Calendar },
  { key: 'events', name: 'Economic Events', icon: FileText },
];

interface NavigationProps {
  activePage: Page;
  onNavigate: (page: Page) => void;
}

export default function Navigation({ activePage, onNavigate }: NavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [kiteConnected, setKiteConnected] = useState<boolean | null>(null);

  useEffect(() => {
    // Check Kite Auth Status
    fetch(`${API}/api/kite/status`)
      .then(res => res.json())
      .then(data => setKiteConnected(data.authenticated))
      .catch(err => console.error("Kite status check failed:", err));
  }, []);

  const handleKiteLogin = async () => {
    try {
      const res = await fetch(`${API}/api/kite/login`);
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error("Failed to get Kite login URL", err);
    }
  };

  return (
    <nav className="fixed w-full z-50 top-0 left-0 bg-[var(--bg-primary)]/80 backdrop-blur-md border-[var(--border-subtle)] border-b transition-colors duration-300">
      <div className="max-w-[1400px] mx-auto px-4 h-16 flex items-center justify-between">
        <button onClick={() => onNavigate('dashboard')} className="flex items-center gap-3">
          <div className="relative w-[180px] sm:w-[220px] h-[40px] flex items-center justify-center transition-all duration-300">
            <Logo />
          </div>
        </button>
        <div className="hidden lg:flex items-center gap-6">
          <div className="flex gap-1 items-center bg-[var(--bg-card)] p-1 rounded-xl border border-[var(--border-subtle)] shadow-sm mr-2 transition-colors duration-300">
            {links.map((link) => {
              const Icon = link.icon;
              const active = activePage === link.key;
              return (
                <button
                  key={link.key}
                  onClick={() => onNavigate(link.key)}
                  className={`
                    flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer
                    ${active
                      ? 'bg-[var(--accent-indigo)]/20 text-[var(--accent-indigo)] font-semibold shadow-sm backdrop-blur-md'
                      : 'text-gray-400 hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]'
                    }
                  `}
                >
                  <Icon size={16} />
                  <span>{link.name}</span>
                </button>
              );
            })}
          </div>
          <div className="flex items-center gap-3">
            {kiteConnected === true ? (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 text-green-500 text-xs font-semibold rounded-full border border-green-500/20">
                <CheckCircle2 size={14} />
                Kite Live
              </div>
            ) : kiteConnected === false ? (
              <button
                onClick={handleKiteLogin}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--accent-indigo)] hover:bg-opacity-80 text-white text-xs font-semibold rounded-full transition-all shadow-md"
              >
                <LinkIcon size={14} />
                Connect Kite
              </button>
            ) : null}
            <ThemeToggle />
          </div>
        </div>
        <div className="lg:hidden flex items-center gap-4">
          {kiteConnected === false && (
            <button
              onClick={handleKiteLogin}
              className="px-2 py-1 bg-[var(--accent-indigo)] text-white text-xs font-medium rounded-lg"
            >
              Connect
            </button>
          )}
          <ThemeToggle />
          <button onClick={() => setMobileMenuOpen(x => !x)} className="p-2 text-gray-500 hover:text-[var(--text-primary)]">
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>
      {mobileMenuOpen && (
        <div className="lg:hidden absolute top-16 left-0 w-full bg-[var(--bg-primary)] border-b border-[var(--border-subtle)] shadow-xl p-4 flex flex-col gap-2 backdrop-blur-lg">
          {links.map((link) => {
            const Icon = link.icon;
            const active = activePage === link.key;
            return (
              <button
                key={link.key}
                onClick={() => { onNavigate(link.key); setMobileMenuOpen(false); }}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left ${active
                  ? 'bg-gradient-to-r from-[var(--accent-indigo)]/20 to-transparent text-[var(--accent-indigo)] font-bold'
                  : 'text-gray-500 hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)]'
                  }`}
              >
                <Icon size={18} />
                <span>{link.name}</span>
              </button>
            );
          })}
        </div>
      )}
    </nav>
  );
}
