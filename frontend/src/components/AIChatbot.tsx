'use client';
import React, { useState, useRef, useEffect, useCallback } from 'react';

const API = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
}

interface AIChatbotProps {
    currentTab?: string;
    currentSymbol?: string;
    currentPrice?: number;
    detectedPatterns?: string[];
}

//  Simple markdown renderer 
function renderMarkdown(text: string) {
    return text.split('\n').map((line, i) => {
        // Headers
        if (line.startsWith('### ')) return <h4 key={i} style={{ fontSize: 13, fontWeight: 800, color: '#93c5fd', margin: '8px 0 4px' }}>{line.slice(4)}</h4>;
        if (line.startsWith('## ')) return <h3 key={i} style={{ fontSize: 14, fontWeight: 800, color: '#e2e8f0', margin: '8px 0 4px' }}>{line.slice(3)}</h3>;

        // Bullet points
        if (line.startsWith('- **')) {
            const parts = line.slice(2).split('**');
            return (
                <div key={i} style={{ fontSize: 12, lineHeight: 1.6, paddingLeft: 8, marginBottom: 2 }}>
                    • <strong style={{ color: '#e2e8f0' }}>{parts[1]}</strong>{parts[2] || ''}
                </div>
            );
        }
        if (line.startsWith('- ')) return <div key={i} style={{ fontSize: 12, lineHeight: 1.6, paddingLeft: 8 }}>• {line.slice(2)}</div>;

        // Bold text inline
        let processed: React.ReactNode = line;
        if (line.includes('**')) {
            const parts = line.split('**');
            processed = parts.map((part, j) =>
                j % 2 === 1 ? <strong key={j} style={{ color: '#e2e8f0' }}>{part}</strong> : part
            );
        }

        // Empty line
        if (!line.trim()) return <div key={i} style={{ height: 8 }} />;

        return <div key={i} style={{ fontSize: 12, lineHeight: 1.6 }}>{processed}</div>;
    });
}

export default function AIChatbot({ currentTab, currentSymbol, currentPrice, detectedPatterns }: AIChatbotProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [quickPrompts, setQuickPrompts] = useState<string[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const sessionId = useRef(`session_${Date.now()}`);

    // Scroll to bottom when new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Focus input when opened
    useEffect(() => {
        if (isOpen) inputRef.current?.focus();
    }, [isOpen]);

    // Fetch quick prompts based on tab
    useEffect(() => {
        fetch(`${API}/api/ai/prompts?tab=${currentTab || ''}`)
            .then(r => r.json())
            .then(d => setQuickPrompts(d.prompts || []))
            .catch(() => setQuickPrompts([
                "What is a Doji pattern?",
                "Explain Iron Condor",
                "How to use Fibonacci?",
                "What does RSI tell me?",
            ]));
    }, [currentTab]);

    const sendMessage = useCallback(async (text: string) => {
        if (!text.trim() || loading) return;

        const userMsg: Message = { role: 'user', content: text.trim(), timestamp: Date.now() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await fetch(`${API}/api/ai/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text.trim(),
                    session_id: sessionId.current,
                    context: {
                        tab: currentTab || '',
                        symbol: currentSymbol || '',
                        price: currentPrice || 0,
                        patterns: detectedPatterns || [],
                    },
                    stream: true,
                }),
            });

            if (!res.body) throw new Error("No response body");

            setLoading(false); // Stop typing indicator as stream starts

            // Add empty assistant message that we will populate
            setMessages(prev => [...prev, { role: 'assistant', content: '', timestamp: Date.now() }]);

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedContent = '';
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || ''; // Keep last incomplete part

                for (const part of parts) {
                    if (part.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(part.slice(6));
                            if (data.text) {
                                accumulatedContent += data.text;
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    newMessages[newMessages.length - 1] = {
                                        ...newMessages[newMessages.length - 1],
                                        content: accumulatedContent
                                    };
                                    return newMessages;
                                });
                            }
                        } catch (e) {
                            // Ignore parse errors for incomplete chunks
                        }
                    }
                }
            }
        } catch {
            setLoading(false);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: ' Connection issue. Please try again!',
                timestamp: Date.now(),
            }]);
        }
    }, [loading, currentTab, currentSymbol, currentPrice, detectedPatterns]);

    const clearChat = () => {
        setMessages([]);
        fetch(`${API}/api/ai/clear?session_id=${sessionId.current}`, { method: 'DELETE' }).catch(() => { });
    };

    return (
        <>
            {/*  Floating Chat Bubble  */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    position: 'fixed', bottom: 24, right: 24, zIndex: 9990,
                    width: 56, height: 56, borderRadius: '50%',
                    background: isOpen ? 'rgba(59,130,246,0.3)' : 'linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #3b82f6 100%)',
                    border: '2px solid rgba(59,130,246,0.4)',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    boxShadow: isOpen ? 'none' : '0 4px 24px rgba(59,130,246,0.4), 0 0 40px rgba(37,99,235,0.2)',
                    transition: 'all 0.3s ease',
                }}
            >
                <span style={{ fontSize: 24 }}>{isOpen ? '' : ''}</span>
                {!isOpen && (
                    <img src="/tara-avatar.png" alt="Tara" style={{
                        width: 48, height: 48, borderRadius: '50%', objectFit: 'cover',
                        position: 'absolute', top: 2, left: 2,
                    }} />
                )}
            </button>

            {/* Notification dot when closed */}
            {!isOpen && messages.length === 0 && (
                <div style={{
                    position: 'fixed', bottom: 70, right: 20, zIndex: 9991,
                    background: 'rgba(0,0,0,0.85)', border: '1px solid rgba(59,130,246,0.3)',
                    borderRadius: 12, padding: '8px 14px', maxWidth: 200,
                    animation: 'fadeInUp 0.5s ease',
                }}>
                    <div style={{ fontSize: 11, color: '#93c5fd', fontWeight: 700 }}> Tara — AI Trading Mentor</div>
                    <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>Ask me about patterns, strategies & AI signals!</div>
                </div>
            )}

            {/*  Chat Window  */}
            {isOpen && (
                <div style={{
                    position: 'fixed', bottom: 90, right: 24, zIndex: 9991,
                    width: 400, maxWidth: 'calc(100vw - 32px)',
                    height: 520, maxHeight: 'calc(100vh - 120px)',
                    background: '#0f1225', border: '1px solid rgba(59,130,246,0.25)',
                    borderRadius: 20, display: 'flex', flexDirection: 'column',
                    boxShadow: '0 8px 40px rgba(0,0,0,0.6), 0 0 60px rgba(59,130,246,0.1)',
                    overflow: 'hidden',
                }}>
                    {/* Header */}
                    <div style={{
                        padding: '14px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        borderBottom: '1px solid rgba(255,255,255,0.06)',
                        background: 'linear-gradient(135deg, rgba(59,130,246,0.1), rgba(37,99,235,0.05))',
                    }}>
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <img src="/tara-avatar.png" alt="Tara" style={{
                                    width: 32, height: 32, borderRadius: '50%', objectFit: 'cover',
                                    border: '2px solid rgba(59,130,246,0.3)',
                                }} />
                                <div>
                                    <div style={{ fontSize: 14, fontWeight: 800, color: '#e2e8f0' }}>
                                        Tara
                                    </div>
                                    <div style={{ fontSize: 10, color: '#64748b', marginTop: 1 }}>
                                        तारा • Vedic Trading Mentor
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                            {currentTab && (
                                <span style={{
                                    fontSize: 9, padding: '2px 8px', borderRadius: 6,
                                    background: 'rgba(59,130,246,0.15)', color: '#93c5fd',
                                    border: '1px solid rgba(59,130,246,0.2)', fontWeight: 700,
                                    textTransform: 'uppercase' as const, letterSpacing: 0.5,
                                }}>
                                    {currentTab}
                                </span>
                            )}
                            <button onClick={clearChat} style={{
                                fontSize: 10, padding: '3px 8px', borderRadius: 6,
                                background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                                color: '#64748b', cursor: 'pointer', fontWeight: 600,
                            }}>
                                Clear
                            </button>
                        </div>
                    </div>

                    {/* Messages area */}
                    <div style={{
                        flex: 1, overflowY: 'auto', padding: '12px 14px',
                        display: 'flex', flexDirection: 'column', gap: 10,
                    }}>
                        {/* Welcome message */}
                        {messages.length === 0 && (
                            <div style={{ textAlign: 'center', padding: '30px 10px' }}>
                                <img src="/tara-avatar.png" alt="Tara" style={{
                                    width: 80, height: 80, borderRadius: '50%', objectFit: 'cover',
                                    border: '3px solid rgba(59,130,246,0.3)',
                                    boxShadow: '0 0 20px rgba(59,130,246,0.2)',
                                    marginBottom: 12,
                                }} />
                                <div style={{ fontSize: 15, fontWeight: 800, color: '#e2e8f0', marginBottom: 4 }}>
                                    Namaste! I&apos;m Tara
                                </div>
                                <div style={{ fontSize: 11, color: '#64748b', marginBottom: 16, lineHeight: 1.6 }}>
                                    Your AI Trading Mentor • तारा<br />
                                    Ask me about patterns, derivatives strategies,<br />
                                    signal patterns, or any trading concept!
                                </div>

                                {/* Quick prompts */}
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                    {quickPrompts.map((p, i) => (
                                        <button key={i} onClick={() => sendMessage(p)} style={{
                                            padding: '8px 14px', borderRadius: 10, fontSize: 11, fontWeight: 600,
                                            cursor: 'pointer', textAlign: 'left',
                                            background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.15)',
                                            color: '#93c5fd', transition: 'all 0.2s',
                                        }}
                                            onMouseEnter={e => { (e.target as HTMLElement).style.background = 'rgba(59,130,246,0.2)'; }}
                                            onMouseLeave={e => { (e.target as HTMLElement).style.background = 'rgba(59,130,246,0.08)'; }}
                                        >
                                            {p}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Message bubbles */}
                        {messages.map((msg, i) => (
                            <div key={i} style={{
                                display: 'flex',
                                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                            }}>
                                <div style={{
                                    maxWidth: '85%', padding: '10px 14px', borderRadius: 14,
                                    background: msg.role === 'user'
                                        ? 'linear-gradient(135deg, rgba(59,130,246,0.3), rgba(37,99,235,0.2))'
                                        : 'rgba(255,255,255,0.04)',
                                    border: msg.role === 'user'
                                        ? '1px solid rgba(59,130,246,0.3)'
                                        : '1px solid rgba(255,255,255,0.06)',
                                    borderBottomRightRadius: msg.role === 'user' ? 4 : 14,
                                    borderBottomLeftRadius: msg.role === 'assistant' ? 4 : 14,
                                    color: msg.role === 'user' ? '#e2e8f0' : '#94a3b8',
                                }}>
                                    {msg.role === 'assistant' ? renderMarkdown(msg.content) : (
                                        <div style={{ fontSize: 12, lineHeight: 1.6 }}>{msg.content}</div>
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* Typing indicator */}
                        {loading && (
                            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                                <div style={{
                                    padding: '12px 18px', borderRadius: 14, borderBottomLeftRadius: 4,
                                    background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
                                }}>
                                    <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                                        {[0, 1, 2].map(j => (
                                            <div key={j} style={{
                                                width: 6, height: 6, borderRadius: '50%',
                                                background: '#3b82f6',
                                                animation: `bounce 1.2s infinite ${j * 0.2}s`,
                                            }} />
                                        ))}
                                        <span style={{ fontSize: 10, color: '#64748b', marginLeft: 6 }}>Tara is thinking...</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input area */}
                    <div style={{
                        padding: '10px 14px', borderTop: '1px solid rgba(255,255,255,0.06)',
                        background: 'rgba(255,255,255,0.02)',
                    }}>
                        <form
                            onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
                            style={{ display: 'flex', gap: 8 }}
                        >
                            <input
                                ref={inputRef}
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                placeholder="Ask Tara about patterns, strategies..."
                                disabled={loading}
                                style={{
                                    flex: 1, padding: '10px 14px', borderRadius: 12, fontSize: 12,
                                    border: '1px solid rgba(59,130,246,0.2)',
                                    background: 'rgba(255,255,255,0.04)', color: '#e2e8f0',
                                    outline: 'none',
                                }}
                                onFocus={e => e.target.style.borderColor = 'rgba(59,130,246,0.5)'}
                                onBlur={e => e.target.style.borderColor = 'rgba(59,130,246,0.2)'}
                            />
                            <button
                                type="submit"
                                disabled={loading || !input.trim()}
                                style={{
                                    padding: '10px 16px', borderRadius: 12, fontSize: 14,
                                    border: 'none', cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                                    background: loading || !input.trim()
                                        ? 'rgba(59,130,246,0.15)'
                                        : 'linear-gradient(135deg, #3b82f6, #2563eb)',
                                    color: '#fff', fontWeight: 700,
                                    opacity: loading || !input.trim() ? 0.5 : 1,
                                    transition: 'all 0.2s',
                                }}
                            >

                            </button>
                        </form>
                        <div style={{ fontSize: 9, color: '#475569', textAlign: 'center', marginTop: 6 }}>
                            Powered by Tara  • Not financial advice
                        </div>
                    </div>
                </div>
            )}

            {/*  Animations  */}
            <style jsx global>{`
                @keyframes bounce {
                    0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
                    40% { transform: translateY(-6px); opacity: 1; }
                }
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </>
    );
}

