'use client';

import React, { useState, useEffect } from 'react';
import Navigation, { Page } from '@/components/Navigation';
import Dashboard from '@/components/Dashboard';
import NakshatraAnalysis from '@/components/NakshatraAnalysis';
import TechnicalAnalysis from '@/components/TechnicalAnalysis';
import AstroCorrelation from '@/components/AstroCorrelation';
import SentimentVix from '@/components/SentimentVix';
import EconomicEvents from '@/components/EconomicEvents';
import DerivativesDashboard from '@/components/DerivativesDashboard';
import AIChatbot from '@/components/AIChatbot';
import Settings from '@/components/Settings';
import NiftyAlgoWidget from '@/components/NiftyAlgoWidget';
import { usePlan } from '@/contexts/PlanContext';

// Pages that require Pro or Elite
const PRO_PAGES: Page[] = ['correlation', 'sentiment'];
// Pages that require Elite
const ELITE_PAGES: Page[] = ['nakshatra', 'algo', 'settings'];

export default function AstroFinanceApp() {
  const [page, setPage] = useState<Page>('dashboard');
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [isProcessingAuth, setIsProcessingAuth] = useState(false);
  const [currentSymbol, setCurrentSymbol] = useState('^NSEI');
  const { tier } = usePlan();
  const isFree = tier === 'free';

  // Guard: redirect free/pro users away from gated pages
  const handleNavigate = (target: Page) => {
    if (ELITE_PAGES.includes(target) && tier !== 'elite') {
      setPage('dashboard');
      return;
    }
    if (PRO_PAGES.includes(target) && tier === 'free') {
      setPage('dashboard');
      return;
    }
    setPage(target);
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const requestToken = params.get('request_token');

    if (requestToken) {
      setIsProcessingAuth(true);
      fetch((typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '') + '/api/kite/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_token: requestToken }),
      })
        .then(res => res.json())
        .then(() => {
          window.history.replaceState({}, document.title, window.location.pathname);
          setIsProcessingAuth(false);
          window.location.reload();
        })
        .catch(err => {
          console.error("Kite auth failed", err);
          setIsProcessingAuth(false);
        });
    }
  }, []);

  // Redirect if user lands on a page they can't access
  useEffect(() => {
    if (ELITE_PAGES.includes(page) && tier !== 'elite') {
      setPage('dashboard');
    } else if (PRO_PAGES.includes(page) && tier === 'free') {
      setPage('dashboard');
    }
  }, [tier, page]);

  return (
    <>
      <Navigation activePage={page} onNavigate={handleNavigate} />

      <main className="pt-[68px] sm:pt-[130px] pb-[80px] sm:pb-12 px-3 sm:px-4 max-w-[1400px] mx-auto min-h-screen">
        {isProcessingAuth && (
          <div className="flex flex-col items-center justify-center p-10 bg-[var(--bg-card)] rounded-xl border border-[var(--border-subtle)] mb-8 shadow-lg">
            <div className="spinner mb-4 w-8 h-8 border-4"></div>
            <h2 className="text-xl font-bold text-blue-500">Authenticating with Kite...</h2>
            <p className="text-gray-400 text-sm mt-2">Connecting up your live data feeds. Please wait.</p>
          </div>
        )}

        {page === 'dashboard' && (
          <Dashboard
            onAnalysisDone={(data) => {
              setAnalysisData(data);
              if (!isFree) setPage('nakshatra');
            }}
          />
        )}
        {page === 'nakshatra' && tier === 'elite' && <NakshatraAnalysis data={analysisData} />}
        {page === 'technical' && <TechnicalAnalysis active={true} onSymbolChange={setCurrentSymbol} />}
        {page === 'correlation' && !isFree && <AstroCorrelation />}
        {page === 'sentiment' && !isFree && <SentimentVix />}
        {page === 'events' && <EconomicEvents />}
        {page === 'algo' && (
          <div className="w-full max-w-5xl mx-auto">
            <NiftyAlgoWidget />
          </div>
        )}
        {page === 'settings' && <Settings />}
      </main>

      {/* AI Trading Assistant — accessible from all pages with live market context */}
      <AIChatbot currentTab={page} currentSymbol={currentSymbol} />
    </>
  );
}
