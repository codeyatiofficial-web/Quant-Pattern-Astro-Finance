import React, { useState, useEffect } from 'react';
import { Save, CheckCircle, AlertCircle, Key, Link as LinkIcon } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function Settings() {
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState<{type: 'success' | 'error' | null, msg: string}>({type: null, msg: ''});

  const [brokerConfig, setBrokerConfig] = useState({
    broker_name: 'zerodha',
    api_key: '',
    api_secret: '',
    is_active: false,
    trade_multiplier: 1.0,
    has_access_token: false
  });

  useEffect(() => {
    // Basic auth check for local development dummy token, or real token from localstorage
    const token = localStorage.getItem('algo_session_token');
    if (token) {
      setSessionToken(token);
      fetchBrokerStatus(token);
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchBrokerStatus = async (token: string) => {
    try {
      const res = await fetch(`${API}/api/user/broker/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });
      const data = await res.json();
      if (res.ok && data) {
        setBrokerConfig(prev => ({
          ...prev,
          broker_name: data.broker_name || 'zerodha',
          api_key: data.api_key || '',
          api_secret: data.api_secret ? '********' : '',
          is_active: !!data.is_active,
          trade_multiplier: data.trade_multiplier || 1.0,
          has_access_token: !!data.has_access_token
        }));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    if (!sessionToken) {
      setSaveStatus({ type: 'error', msg: 'You must be logged in to save broker settings.' });
      return;
    }

    setSaveStatus({ type: null, msg: '' });
    try {
      const res = await fetch(`${API}/api/user/broker/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: sessionToken,
          broker_name: brokerConfig.broker_name,
          api_key: brokerConfig.api_key,
          api_secret: brokerConfig.api_secret === '********' ? '' : brokerConfig.api_secret
        })
      });
      const data = await res.json();
      if (res.ok) {
        setSaveStatus({ type: 'success', msg: 'Broker configuration saved securely.' });
      } else {
        setSaveStatus({ type: 'error', msg: data.detail || 'Failed to save config.' });
      }
    } catch (err) {
      setSaveStatus({ type: 'error', msg: 'Network error while saving.' });
    }
  };

  const handleToggleActive = async (newVal: boolean) => {
    if (!sessionToken) return;
    setBrokerConfig(prev => ({ ...prev, is_active: newVal }));
    try {
      await fetch(`${API}/api/user/broker/preference`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: sessionToken,
          is_active: newVal,
          trade_multiplier: brokerConfig.trade_multiplier
        })
      });
    } catch (err) {
      console.error('Failed to toggle active state', err);
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Key className="text-blue-500" />
          Trading Settings
        </h1>
        <p className="text-gray-400 mt-2">
          Connect your broker API, manage keys, and configure automated execution logic securely.
        </p>
      </div>

      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] p-6 rounded-2xl shadow-xl">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2 border-b border-[var(--border-subtle)] pb-3">
          <LinkIcon size={20} className="text-emerald-400" />
          Broker Integration
        </h2>

        {!sessionToken ? (
          <div className="p-4 bg-orange-500/10 border border-orange-500/20 text-orange-400 rounded-xl mb-4 text-sm flex items-center gap-2">
            <AlertCircle size={18} />
            Please login or create an account to save API keys across sessions securely.
          </div>
        ) : null}

        <div className="space-y-5 mt-5">
          <div>
            <label className="block text-sm text-gray-400 font-medium mb-1">Select Broker</label>
            <select
              value={brokerConfig.broker_name}
              onChange={e => setBrokerConfig({...brokerConfig, broker_name: e.target.value})}
              className="w-full bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="zerodha">Zerodha Kite</option>
              <option value="fyers">Fyers</option>
              <option value="upstox">Upstox</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 font-medium mb-1">API Key / Client ID</label>
            <input
              type="text"
              value={brokerConfig.api_key}
              onChange={e => setBrokerConfig({...brokerConfig, api_key: e.target.value})}
              placeholder="e.g. xyz123key"
              className="w-full bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 font-medium mb-1">API Secret / Secret Key</label>
            <input
              type="password"
              value={brokerConfig.api_secret}
              onChange={e => setBrokerConfig({...brokerConfig, api_secret: e.target.value})}
              placeholder={brokerConfig.api_secret === '********' ? '******** (Encrypted)' : 'Your secure API Secret'}
              className="w-full bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex items-center justify-between py-2">
             <button
                onClick={handleSaveConfig}
                disabled={isLoading || !sessionToken}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 px-6 py-3 rounded-xl text-white font-medium text-sm transition-colors disabled:opacity-50"
             >
                <Save size={16} /> Save Broker Configuration
             </button>

             {saveStatus.msg && (
                <div className={`text-sm flex items-center gap-2 ${saveStatus.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`}>
                  {saveStatus.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                  {saveStatus.msg}
                </div>
             )}
          </div>
        </div>
      </div>

      <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] p-6 rounded-2xl shadow-xl">
        <h2 className="text-xl font-bold mb-4 border-b border-[var(--border-subtle)] pb-3">Automated Execution</h2>
        
        <div className="flex flex-col sm:flex-row gap-6 items-start sm:items-center">
          <div className="flex-1">
             <h3 className="font-semibold text-lg text-white">Algorithm Trading Engine</h3>
             <p className="text-gray-400 text-sm mt-1">Enable to allow the server to place live trades on your connected broker account.</p>
          </div>
          
          <button 
             onClick={() => handleToggleActive(!brokerConfig.is_active)}
             disabled={!sessionToken}
             className={`px-8 py-3 rounded-full font-bold text-sm tracking-wide transition-all shadow-lg border disabled:opacity-50 ${
                brokerConfig.is_active 
                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50 hover:bg-emerald-500/30' 
                : 'bg-gray-800 text-gray-400 border-gray-700 hover:bg-gray-700'
             }`}
          >
             {brokerConfig.is_active ? 'ACTIVE (TRADING)' : 'DISABLED'}
          </button>
        </div>

        {brokerConfig.has_access_token && brokerConfig.is_active && (
           <div className="mt-4 p-4 border border-emerald-500/20 bg-emerald-500/5 rounded-xl flex items-start gap-4">
              <div className="p-2 bg-emerald-500/20 rounded-full text-emerald-400">
                <CheckCircle size={20} />
              </div>
              <div>
                <h4 className="font-semibold text-emerald-400">System Ready</h4>
                <p className="text-sm text-emerald-400/80 mt-1">
                   Your broker connection is authorized and the engine is listening for signals. Trades will be executed automatically.
                </p>
              </div>
           </div>
        )}
      </div>

    </div>
  );
}
