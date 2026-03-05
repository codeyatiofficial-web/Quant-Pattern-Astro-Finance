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

export default function AstroFinanceApp() {
  const [page, setPage] = useState<Page>('dashboard');
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [isProcessingAuth, setIsProcessingAuth] = useState(false);

  useEffect(() => {
    // Check if returning from Kite Auth
    const params = new URLSearchParams(window.location.search);
    const requestToken = params.get('request_token');

    if (requestToken) {
      setIsProcessingAuth(true);
      fetch((typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '') + '/api/kite/callback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ request_token: requestToken }),
      })
        .then(res => res.json())
        .then(data => {
          // Remove token from URL for clean state
          window.history.replaceState({}, document.title, window.location.pathname);
          setIsProcessingAuth(false);
          // Force reload to update navigation state
          window.location.reload();
        })
        .catch(err => {
          console.error("Kite auth failed", err);
          setIsProcessingAuth(false);
        });
    }
  }, []);

  return (
    <>
      <Navigation activePage={page} onNavigate={setPage} />

      <main className="pt-32 pb-10 px-4 max-w-[1400px] mx-auto min-h-screen">
        {isProcessingAuth && (
          <div className="flex flex-col items-center justify-center p-10 bg-[var(--bg-card)] rounded-xl border border-[var(--border-subtle)] mb-8 shadow-lg">
            <div className="spinner mb-4 w-8 h-8 border-4"></div>
            <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">Authenticating with Kite...</h2>
            <p className="text-gray-400 text-sm mt-2">Connecting up your live data feeds. Please wait.</p>
          </div>
        )}

        {page === 'dashboard' && (
          <Dashboard
            onAnalysisDone={(data) => {
              setAnalysisData(data);
              setPage('nakshatra');
            }}
          />
        )}
        {page === 'nakshatra' && <NakshatraAnalysis data={analysisData} />}
        {page === 'technical' && <TechnicalAnalysis />}
        {page === 'correlation' && <AstroCorrelation />}
        {page === 'sentiment' && <SentimentVix />}
        {page === 'events' && <EconomicEvents />}
        {page === 'derivatives' && <DerivativesDashboard />}
      </main>
    </>
  );
}
