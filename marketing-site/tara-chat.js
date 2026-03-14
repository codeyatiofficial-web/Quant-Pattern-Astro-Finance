/* 
   Kuber Chatbot — Vanilla JS widget for marketing site
   Connects to Quant Pattern AI API
    */

(function () {
  'use strict';

  // API base — use production URL
  const API = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://app.quant-pattern.com';

  const sessionId = 'mkt_' + Date.now();
  let isOpen = false;
  let messages = [];
  let loading = false;
  let quickPrompts = [];

  //  Inject CSS 
  const style = document.createElement('style');
  style.textContent = `
    .tara-bubble {
      position: fixed; bottom: 24px; right: 24px; z-index: 9990;
      width: 60px; height: 60px; border-radius: 50%;
      background: linear-gradient(135deg, #1f1f1f 0%, #111 50%, #000 100%);
      border: 2px solid rgba(246, 211, 101, 0.4);
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.6), 0 0 40px rgba(246, 211, 101, 0.15);
      transition: all 0.3s ease;
      overflow: hidden;
    }
    .tara-bubble:hover { transform: scale(1.08); box-shadow: 0 6px 32px rgba(246, 211, 101, 0.3); }
    .tara-bubble.open { background: rgba(0, 0, 0, 0.8); box-shadow: none; border-color: rgba(255,255,255,0.1); }
    .tara-bubble img { width: 52px; height: 52px; border-radius: 50%; object-fit: cover; }
    .tara-bubble .close-x { font-size: 22px; color: #fff; font-weight: 700; }

    .tara-tooltip {
      position: fixed; bottom: 90px; right: 20px; z-index: 9991;
      background: rgba(10, 10, 12, 0.95); border: 1px solid rgba(246, 211, 101, 0.3);
      border-radius: 14px; padding: 10px 16px; max-width: 210px;
      animation: taraFadeIn 0.5s ease;
      backdrop-filter: blur(12px);
    }
    .tara-tooltip-title { font-size: 12px; color: #f6d365; font-weight: 700; }
    .tara-tooltip-sub { font-size: 10px; color: #94a3b8; margin-top: 3px; }

    [data-theme="light"] .tara-tooltip {
      background: rgba(255,255,255,0.95); border-color: rgba(246, 211, 101, 0.4);
    }
    [data-theme="light"] .tara-tooltip-title { color: #d97706; }
    [data-theme="light"] .tara-tooltip-sub { color: #64748b; }

    .tara-chat {
      position: fixed; bottom: 92px; right: 24px; z-index: 9991;
      width: 400px; max-width: calc(100vw - 32px);
      height: 520px; max-height: calc(100vh - 120px);
      background: #050505; border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px; display: none; flex-direction: column;
      box-shadow: 0 8px 40px rgba(0,0,0,0.8), 0 0 60px rgba(246, 211, 101, 0.05);
      overflow: hidden; animation: taraSlideUp 0.3s ease;
    }
    .tara-chat.open { display: flex; }

    [data-theme="light"] .tara-chat {
      background: #ffffff; border-color: rgba(139,92,246,0.15);
      box-shadow: 0 8px 40px rgba(102,126,234,0.15);
    }

    .tara-header {
      padding: 14px 16px; display: flex; justify-content: space-between; align-items: center;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      background: linear-gradient(135deg, rgba(20,20,20,0.9), rgba(10,10,10,1));
    }
    [data-theme="light"] .tara-header { border-bottom-color: rgba(0,0,0,0.1); }
    .tara-header-left { display: flex; align-items: center; gap: 10px; }
    .tara-header img { width: 34px; height: 34px; border-radius: 50%; object-fit: cover; border: 2px solid rgba(246, 211, 101, 0.5); }
    .tara-header-name { font-size: 14px; font-weight: 800; color: #e2e8f0; }
    .tara-header-sub { font-size: 10px; color: #64748b; margin-top: 1px; }
    [data-theme="light"] .tara-header-name { color: #1e1b4b; }
    .tara-clear { font-size: 10px; padding: 4px 10px; border-radius: 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #64748b; cursor: pointer; font-weight: 600; }
    [data-theme="light"] .tara-clear { background: rgba(139,92,246,0.05); border-color: rgba(139,92,246,0.15); }

    .tara-messages {
      flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 10px;
    }

    .tara-welcome { text-align: center; padding: 24px 10px; }
    .tara-welcome img { width: 72px; height: 72px; border-radius: 50%; object-fit: cover; border: 3px solid rgba(246, 211, 101, 0.4); box-shadow: 0 0 30px rgba(246, 211, 101, 0.1); margin: 0 auto 12px; }
    .tara-welcome-title { font-size: 15px; font-weight: 800; color: #f6d365; margin-bottom: 4px; }
    .tara-welcome-sub { font-size: 11px; color: #94a3b8; line-height: 1.6; margin-bottom: 16px; }
    [data-theme="light"] .tara-welcome-title { color: #111; }
    [data-theme="light"] .tara-welcome-sub { color: #475569; }

    .tara-prompt-btn {
      display: block; width: 100%; padding: 9px 14px; border-radius: 10px; font-size: 11px; font-weight: 600;
      cursor: pointer; text-align: left; margin-bottom: 6px;
      background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
      color: #e2e8f0; transition: all 0.2s;
    }
    .tara-prompt-btn:hover { background: rgba(246, 211, 101, 0.1); border-color: rgba(246, 211, 101, 0.3); color: #f6d365; }
    [data-theme="light"] .tara-prompt-btn { background: rgba(0,0,0,0.03); color: #111; border-color: rgba(0,0,0,0.1); }

    .tara-msg { display: flex; }
    .tara-msg.user { justify-content: flex-end; }
    .tara-msg.assistant { justify-content: flex-start; }
    .tara-msg-bubble {
      max-width: 85%; padding: 10px 14px; border-radius: 14px; font-size: 12px; line-height: 1.6;
    }
    .tara-msg.user .tara-msg-bubble {
      background: linear-gradient(135deg, #222, #111);
      border: 1px solid rgba(246, 211, 101, 0.3); border-bottom-right-radius: 4px; color: #f8fafc;
    }
    .tara-msg.assistant .tara-msg-bubble {
      background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
      border-bottom-left-radius: 4px; color: #cbd5e1;
    }
    [data-theme="light"] .tara-msg.user .tara-msg-bubble {
      background: linear-gradient(135deg, #111, #000);
      color: #fff; border-color: #000;
    }
    [data-theme="light"] .tara-msg.assistant .tara-msg-bubble {
      background: rgba(0,0,0,0.04); border-color: rgba(0,0,0,0.1); color: #333;
    }

    .tara-typing { display: flex; gap: 4px; align-items: center; padding: 12px 18px; }
    .tara-typing-dot { width: 6px; height: 6px; border-radius: 50%; background: #f6d365; animation: taraBounce 1.2s infinite; }
    .tara-typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .tara-typing-dot:nth-child(3) { animation-delay: 0.4s; }
    .tara-typing-text { font-size: 10px; color: #64748b; margin-left: 6px; }

    .tara-input-area {
      padding: 10px 14px; border-top: 1px solid rgba(255,255,255,0.1); background: rgba(10,10,10,0.9);
    }
    [data-theme="light"] .tara-input-area { border-top-color: rgba(0,0,0,0.1); background: rgba(250,250,250,1); }
    .tara-input-form { display: flex; gap: 8px; }
    .tara-input {
      flex: 1; padding: 10px 14px; border-radius: 12px; font-size: 12px;
      border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.05);
      color: #e2e8f0; outline: none; font-family: 'Inter', sans-serif;
    }
    .tara-input:focus { border-color: #f6d365; }
    [data-theme="light"] .tara-input { background: rgba(0,0,0,0.05); color: #111; border-color: rgba(0,0,0,0.2); }
    .tara-send {
      padding: 10px 16px; border-radius: 12px; font-size: 14px; border: none;
      background: #f6d365; color: #111; font-weight: 800;
      cursor: pointer; transition: all 0.2s;
    }
    .tara-send:disabled { opacity: 0.4; cursor: not-allowed; }
    .tara-footer-note { font-size: 9px; color: #475569; text-align: center; margin-top: 6px; }

    @keyframes taraFadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes taraSlideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes taraBounce { 0%, 80%, 100% { transform: translateY(0); opacity: 0.4; } 40% { transform: translateY(-6px); opacity: 1; } }

    @media (max-width: 480px) {
      .tara-chat { width: calc(100vw - 16px); right: 8px; bottom: 88px; height: calc(100vh - 120px); }
    }
  `;
  document.head.appendChild(style);

  //  Build DOM 
  function build() {
    // Bubble
    const bubble = document.createElement('button');
    bubble.className = 'tara-bubble';
    bubble.id = 'taraBubble';
    bubble.innerHTML = `<img src="images/kuber-avatar.png" alt="Kuber" />`;
    bubble.onclick = toggle;
    document.body.appendChild(bubble);

    // Tooltip removed

    // Chat window
    const chat = document.createElement('div');
    chat.className = 'tara-chat';
    chat.id = 'taraChat';
    chat.innerHTML = `
      <div class="tara-header">
        <div class="tara-header-left">
          <img src="images/kuber-avatar.png" alt="Kuber" />
          <div>
            <div class="tara-header-name">Kuber </div>
            <div class="tara-header-sub">कुबेर • AI Sales & Growth Rep</div>
          </div>
        </div>
        <button class="tara-clear" id="taraClear">Clear</button>
      </div>
      <div class="tara-messages" id="taraMessages"></div>
      <div class="tara-input-area">
        <form class="tara-input-form" id="taraForm">
          <input class="tara-input" id="taraInput" placeholder="Ask Kuber about patterns, strategies..." autocomplete="off" />
          <button class="tara-send" type="submit" id="taraSend">↑</button>
        </form>
        <div class="tara-footer-note">Powered by Kuber  • Not financial advice</div>
      </div>
    `;
    document.body.appendChild(chat);

    // Events
    document.getElementById('taraClear').onclick = clearChat;
    document.getElementById('taraForm').onsubmit = (e) => {
      e.preventDefault();
      const input = document.getElementById('taraInput');
      sendMessage(input.value);
      input.value = '';
    };

    // Render welcome
    renderMessages();
  }

  function toggle() {
    isOpen = !isOpen;
    const bubble = document.getElementById('taraBubble');
    const chat = document.getElementById('taraChat');
    const tooltip = document.getElementById('taraTooltip');

    if (isOpen) {
      bubble.classList.add('open');
      bubble.innerHTML = `<span class="close-x">X</span>`;
      chat.classList.add('open');
      if (tooltip) tooltip.style.display = 'none';
      document.getElementById('taraInput').focus();
    } else {
      bubble.classList.remove('open');
      bubble.innerHTML = `<img src="images/kuber-avatar.png" alt="Kuber" />`;
      chat.classList.remove('open');
      if (messages.length === 0 && tooltip) tooltip.style.display = 'block';
    }
    bubble.onclick = toggle;
  }

  function renderMessages() {
    const container = document.getElementById('taraMessages');
    if (!container) return;

    if (messages.length === 0) {
      container.innerHTML = `
        <div class="tara-welcome">
          <img src="images/kuber-avatar.png" alt="Kuber" />
          <div class="tara-welcome-title">Namaste! I'm Kuber </div>
          <div class="tara-welcome-sub">
            Your AI Sales & Growth Rep • कुबेर<br />
            Ask me how we can boost your<br />
            trading with our platform & services!
          </div>
          <div id="taraPrompts"></div>
        </div>
      `;
      const promptsDiv = document.getElementById('taraPrompts');
      quickPrompts.forEach(p => {
        const btn = document.createElement('button');
        btn.className = 'tara-prompt-btn';
        btn.textContent = p;
        btn.onclick = () => sendMessage(p);
        promptsDiv.appendChild(btn);
      });
      return;
    }

    let html = '';
    messages.forEach(msg => {
      const content = msg.role === 'assistant' ? renderMarkdown(msg.content) : escapeHtml(msg.content);
      html += `<div class="tara-msg ${msg.role}"><div class="tara-msg-bubble">${content}</div></div>`;
    });

    if (loading) {
      html += `
        <div class="tara-msg assistant">
          <div class="tara-msg-bubble">
            <div class="tara-typing">
              <div class="tara-typing-dot"></div>
              <div class="tara-typing-dot"></div>
              <div class="tara-typing-dot"></div>
              <span class="tara-typing-text">Kuber is thinking...</span>
            </div>
          </div>
        </div>
      `;
    }

    container.innerHTML = html;
    container.scrollTop = container.scrollHeight;
  }

  async function sendMessage(text) {
    if (!text || !text.trim() || loading) return;

    messages.push({ role: 'user', content: text.trim() });
    loading = true;
    renderMessages();

    try {
      const res = await fetch(`${API}/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text.trim(),
          session_id: sessionId,
          context: { tab: 'marketing', symbol: '', price: 0, patterns: [] },
          stream: true
        })
      });

      if (!res.body) throw new Error("No response body");

      loading = false;
      messages.push({ role: 'assistant', content: '' });
      renderMessages();

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (part.startsWith('data: ')) {
            try {
              const data = JSON.parse(part.slice(6));
              if (data.text) {
                accumulatedContent += data.text;
                messages[messages.length - 1].content = accumulatedContent;
                renderMessages();
              }
            } catch (e) {
              // Ignore partial JSON
            }
          }
        }
      }
    } catch {
      loading = false;
      messages.push({ role: 'assistant', content: 'Connection issue. Please try again!' });
      renderMessages();
    }
  }

  function clearChat() {
    messages = [];
    fetch(`${API}/api/ai/clear?session_id=${sessionId}`, { method: 'DELETE' }).catch(() => { });
    renderMessages();
    const tooltip = document.getElementById('taraTooltip');
    if (tooltip) tooltip.style.display = 'block';
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderMarkdown(text) {
    return text.split('\n').map(line => {
      if (line.startsWith('### ')) return `<h4 style="font-size:13px;font-weight:800;color:#c4b5fd;margin:8px 0 4px">${line.slice(4)}</h4>`;
      if (line.startsWith('## ')) return `<h3 style="font-size:14px;font-weight:800;margin:8px 0 4px">${line.slice(3)}</h3>`;

      if (line.startsWith('- **')) {
        const parts = line.slice(2).split('**');
        return `<div style="font-size:12px;line-height:1.6;padding-left:8px;margin-bottom:2px">• <strong>${parts[1] || ''}</strong>${parts[2] || ''}</div>`;
      }
      if (line.startsWith('- ')) return `<div style="font-size:12px;line-height:1.6;padding-left:8px">• ${line.slice(2)}</div>`;

      // Bold
      let processed = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

      if (!line.trim()) return '<div style="height:8px"></div>';
      return `<div style="font-size:12px;line-height:1.6">${processed}</div>`;
    }).join('');
  }

  //  Init 
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
