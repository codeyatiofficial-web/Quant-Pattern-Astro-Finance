import React, { useState } from 'react';

interface AuthModalProps {
    onClose: () => void;
    onSuccess: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ onClose, onSuccess }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const endpoint = isLogin ? '/api/auth/login' : '/api/auth/signup';

        try {
            const res = await fetch(`http://localhost:8000${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            const data = await res.json();
            if (data.success) {
                localStorage.setItem('auth_token', data.token);
                localStorage.setItem('user_email', data.email);
                onSuccess();
            } else {
                setError(data.detail || 'Authentication failed');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            <div className="relative w-full max-w-md bg-slate-900 border border-slate-700/50 rounded-2xl shadow-2xl overflow-hidden p-1 animate-in fade-in zoom-in duration-200">
                <div className="bg-slate-900/50 p-6 sm:p-8 rounded-xl relative z-10">

                    <div className="mb-6 text-center">
                        <h2 className="text-2xl font-bold text-white tracking-tight">
                            {isLogin ? 'Welcome Back' : 'Create Account'}
                        </h2>
                        <p className="text-sm text-slate-400 mt-2">
                            {isLogin
                                ? 'Sign in to run advanced technical scans.'
                                : 'Sign up for free to access premium trading tools.'}
                        </p>
                    </div>

                    {error && (
                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm text-center">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
                                Email Address
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
                                placeholder="you@email.com"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
                                Password
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
                                placeholder="••••••••"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-lg px-4 py-3 shadow-lg shadow-blue-900/20 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-2"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center">
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Processing...
                                </span>
                            ) : (
                                isLogin ? 'Sign In' : 'Sign Up Free'
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-sm text-slate-400">
                        {isLogin ? "Don't have an account? " : "Already have an account? "}
                        <button
                            onClick={() => { setIsLogin(!isLogin); setError(''); }}
                            className="text-blue-400 hover:text-blue-300 font-medium tracking-wide transition-colors"
                        >
                            {isLogin ? 'Sign up' : 'Sign in'}
                        </button>
                    </div>

                </div>
            </div>
        </div>
    );
};
