'use client';

import React, { useEffect, useState } from 'react';
import Navigation from '@/components/Navigation';

const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

export default function AdminDashboard() {
    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API}/api/admin/users/export`);
            const data = await res.json();
            if (data.success) {
                setUsers(data.users);
            } else {
                setError('Failed to fetch users');
            }
        } catch (err) {
            setError('Network error');
        } finally {
            setLoading(false);
        }
    };

    const downloadCSV = () => {
        if (users.length === 0) return;

        const headers = ['ID', 'Email Address', 'Signup Date'];
        const rows = users.map(u => [
            u.id,
            u.email,
            new Date(u.signup_date).toLocaleString()
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(e => e.join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `quant_pattern_users_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <main className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-purple-500/30 selection:text-white">
            <div className="gradient-bg" />
            <Navigation activePage={'technical' as any} onNavigate={() => { }} />

            <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-8" style={{ marginTop: '80px' }}>
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
                             Admin Dashboard
                        </h1>
                        <p className="text-slate-400 mt-2">Manage captured prospect emails and user registrations.</p>
                    </div>

                    <button
                        onClick={downloadCSV}
                        disabled={users.length === 0}
                        className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:hover:bg-emerald-600 text-white font-medium rounded-lg transition-colors shadow-lg shadow-emerald-900/20"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        Export to CSV ({users.length})
                    </button>
                </div>

                <div className="glass-card overflow-hidden border border-slate-700/50 rounded-xl bg-slate-900/40">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-slate-800 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
                                    <th className="px-6 py-4 font-semibold">User ID</th>
                                    <th className="px-6 py-4 font-semibold">Email Address</th>
                                    <th className="px-6 py-4 font-semibold text-right">Signup Date</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60">
                                {loading ? (
                                    <tr>
                                        <td colSpan={3} className="px-6 py-12 text-center text-slate-400">
                                            <div className="inline-block animate-spin w-6 h-6 border-2 border-slate-500 border-t-white rounded-full mb-3" />
                                            <div>Loading users...</div>
                                        </td>
                                    </tr>
                                ) : error ? (
                                    <tr>
                                        <td colSpan={3} className="px-6 py-8 text-center text-red-400 bg-red-500/5">
                                            {error}
                                        </td>
                                    </tr>
                                ) : users.length === 0 ? (
                                    <tr>
                                        <td colSpan={3} className="px-6 py-12 text-center text-slate-400">
                                            No users have signed up yet.
                                        </td>
                                    </tr>
                                ) : (
                                    users.map((user) => (
                                        <tr key={user.id} className="hover:bg-slate-800/30 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-500">
                                                #{user.id.toString().padStart(4, '0')}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-200 font-medium">
                                                {user.email}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400 text-right">
                                                {new Date(user.signup_date).toLocaleString(undefined, {
                                                    year: 'numeric',
                                                    month: 'short',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </main>
    );
}
