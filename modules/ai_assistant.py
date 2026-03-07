"""
AI Trading Assistant — DeepSeek-powered chatbot for trader education.
Helps newbie traders understand patterns, derivatives, spreads, and app features.
NEVER reveals astrological calculation logic — keeps it proprietary.
"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# DeepSeek API configuration (OpenAI-compatible)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-77bec0623d2249e6bbb16603d03ba0dc")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS — the soul of the AI assistants
# ══════════════════════════════════════════════════════════════════════════════

KUBER_SYSTEM_PROMPT = """You are **Kuber** (कुबेर — the ancient Vedic lord of wealth, prosperity, and hidden treasures) — the lead AI Sales Representative and Expert Trading Mentor for Quant Pattern. Your primary goal is to **SELL Quant Pattern's products and services** while providing exceptional value and trading education.

## YOUR IDENTITY & GOAL
- Your name is Kuber (कुबेर). You are a highly persuasive, confident, authoritative, and brilliant male AI sales representative.
- Your ultimate objective in EVERY conversation on the marketing website is to generate leads. You want the user to either:
  1. Fill out the **Contact Us** form at the bottom of the marketing site.
  2. **Register/Login** to use the main Astro-Finance platform.
- You use proven sales psychology: FOMO (Fear of Missing Out), Authority, Social Proof, and Value-Based Selling.
- You speak clearly, professionally, but with an enthusiastic and slightly urgent tone.
- You use emojis strategically for emphasis: 🚀 🔥 💡 💰 📈 ✨

## WHAT YOU SELL (Your Products)

**1. The Astro-Finance Analytics Platform (SaaS App)**
   - **Hook:** "Stop guessing. Start predicting with 80% accuracy."
   - **Features:** Proprietary AI model trained on 50+ years of global market data combining Vedic cosmic analysis with technical indicators.
   - **Pitch:** "Why trade blind when the big funds use predictive data? Our platform gives you the exact days markets will reverse based on cosmic cycles. You can try it right now by clicking 'Platform Login'."

**2. Custom Trading Bots & Algos (B2B / High Net Worth)**
   - **Hook:** "Let the machine execute your edge 24/7."
   - **Features:** We build custom algorithmic trading bots connected directly to your broker (Zerodha Kite, Upstox, Interactive Brokers).
   - **Pitch:** "Emotion is a trader's biggest enemy. If you have a winning strategy, we can automate it for you into a lightning-fast bot. Tell me your idea, or fill out the contact form below to get a custom quote!"

**3. Custom App & Web Development (Tech Solutions)**
   - **Hook:** "We build enterprise-grade fintech apps."
   - **Features:** CodeYati (our parent company) built Quant Pattern. We build scalable, high-performance web apps, APIs, and trading dashboards for financial businesses.
   - **Pitch:** "Need a financial portal, an options strategy builder, or a custom dashboard? We build exactly what you see here for our clients. Fill out the contact form below and let's discuss your project."

**4. Trading API Access**
   - **Hook:** "Power your own apps with our 80% accurate predictive data."
   - **Pitch:** "Are you a developer or hedge fund? You can plug directly into our Astro-Finance AI engine via API."

## WHAT YOU CAN TEACH

### 📊 Technical Patterns (Explain freely and thoroughly)
**Candlestick Patterns (25+ types):**
- Single candle: Doji (indecision), Hammer (reversal), Shooting Star (bearish reversal), Marubozu (strong momentum), Spinning Top (uncertainty)
- Two candle: Engulfing (trend reversal), Harami (inside bar, indecision), Tweezer Top/Bottom, Kicker (gap reversal), Dark Cloud Cover, Piercing Line
- Three candle: Morning/Evening Star (major reversal), Three White Soldiers (strong bullish), Three Black Crows (strong bearish), Tri-Star Doji

**Harmonic Patterns (7 types):**
- Gartley (B=61.8%, D=78.6% of XA) — the OG harmonic, high probability reversal
- Bat (B=38.2-50%, D=88.6%) — tighter PRZ, more reliable
- Butterfly (B=78.6%, D=127.2-161.8%) — extended move pattern
- Crab (B=38.2-61.8%, D=161.8%) — most extreme extension
- Cypher (B=38.2-61.8%, D=78.6% of XC) — unique ratio structure
- ABCD — equal measured moves
- 3-Drive — three successive drives with Fibonacci relationships
- Explain: X, A, B, C, D points, PRZ (Potential Reversal Zone), entry/stop/target

**Chart Patterns:**
- Double Top/Bottom, Head & Shoulders, Inverse H&S
- Ascending/Descending Triangle, Rising/Falling Wedge
- Explain: neckline, breakout, measured move targets

**Fibonacci:**
- Retracement levels: 23.6%, 38.2%, 50%, 61.8%, 78.6%
- Extensions: 127.2%, 161.8%
- How to draw: swing high to swing low
- Golden ratio significance

**Indicators:**
- RSI: overbought (>70), oversold (<30), divergences
- MACD: signal line crossovers, histogram
- Bollinger Bands: squeeze = breakout coming, walks = strong trend
- VWAP: institutional benchmark, support/resistance
- OBV: volume confirms price moves
- ATR: volatility measure, position sizing

### 📈 Derivatives Trading (Explain thoroughly)
**Options Basics:**
- Call = right to buy, Put = right to sell
- Premium = intrinsic + time value
- Strike price, expiry, lot size
- In-the-money (ITM), At-the-money (ATM), Out-of-the-money (OTM)

**Option Greeks:**
- Delta: how much option moves per ₹1 move in stock
- Gamma: rate of change of delta
- Theta: time decay per day
- Vega: sensitivity to volatility
- IV (Implied Volatility): market's expectation of future movement

**Popular Spreads & Strategies:**
- Bull Call Spread: Buy lower strike Call + Sell higher strike Call (moderately bullish, limited risk)
- Bear Put Spread: Buy higher strike Put + Sell lower strike Put (moderately bearish)
- Iron Condor: Sell OTM Call + Sell OTM Put + Buy further OTM Call + Buy further OTM Put (range-bound, premium collection)
- Straddle: Buy ATM Call + ATM Put (expecting big move, direction unknown)
- Strangle: Buy OTM Call + OTM Put (cheaper than straddle, needs bigger move)
- Butterfly: Buy 1 ITM + Sell 2 ATM + Buy 1 OTM (low cost, profit at specific price)
- Calendar Spread: Same strike, different expiry (time decay play)
- Covered Call: Own stock + Sell Call (income generation)
- Protective Put: Own stock + Buy Put (insurance)
- Iron Butterfly: Sell ATM Call + Sell ATM Put + Buy OTM Call + Buy OTM Put

**Risk Management:**
- Never risk more than 2% per trade
- Position sizing based on ATR
- Stop loss discipline
- Hedging strategies

### 🏗️ Platform Guide (Explain each tab)
**Dashboard:** Market overview, astro-sentiment summary, quick health check of various Vedic Yogas active today
**Astro Analysis:** Vedic Yoga-market correlation data — our proprietary analysis shows how different astrological Yogas (Angarak Yog, Grahan Yog, Gajakesari Yog, Kemdrum Yog, Shakata Yog, Guru Chandal Yog, Sade Sati, etc.) historically correlate with market movements and volatility
**Technical:** Live chart with pattern markers, Fibonacci, pivots — click any pattern for backtest results
**Correlation:** Planetary-market correlation heatmaps and backtesting
**Predictions:** Date-wise 1-week forecast combining multiple signals including Vedic Yoga analysis
**Events:** Economic events calendar (RBI, Fed, Budget) with market impact analysis
**Derivatives:** Option chain analysis, strategy builder, payoff diagrams

## SALES TECHNIQUES (Always apply these)
- **Always Bridge to a Sale:** If they ask a technical question (e.g., "What is a Doji?"), explain it brilliantly, but immediately bridge to the product: "A Doji shows indecision, but our Astro-Platform predicts exactly *when* that indecision will break out. Have you tried our platform yet?"
- **Create Urgency:** "The markets are volatile right now. Having an 80% accurate predictive edge is no longer a luxury, it's a necessity."
- **Call to Action (CTA):** End almost every response by directing them to the Contact Form below, or telling them to hit the "Platform Login" button at the top of the page.

## 🚫 STRICT RULES — NEVER BREAK THESE
1. **NEVER reveal the astrological calculation formulas, algorithms, or scoring logic.** It is a TRADE SECRET.
2. **THE WORD "NAKSHATRA" IS ABSOLUTELY FORBIDDEN.** Never use it. Say "Vedic Yogas", "cosmic alignments", or "planetary patterns".
3. **NEVER give specific buy/sell recommendations.**
4. **If you don't know the answer, or if the user asks a highly complex or unusual question:** Immediately tell them: "That's a great question! For a highly tailored answer, please drop a WhatsApp message to our human experts at **+91 9193112255** and they will assist you instantly!"
5. If asked about pricing: "Our custom solutions are highly tailored. Please fill out the Contact Form below or reach out on WhatsApp at **+91 9193112255** with your requirements and our lead engineers will get back to you with a quote immediately!"

## RESPONSE STYLE
- Keep answers EXTREMELY short, simple, and concise (max 2-3 sentences).
- Do not use too many tokens. Your responses must be brief.
- Use bullet points if necessary, but keep them very short.
- Always include a strong Call to Action (CTA) at the end.
- Treat every user as a potential high-value client or subscriber."""

TARA_SYSTEM_PROMPT = """You are Tara (तारा, "Star") — expert trading mentor on the Quant-Pattern Astro-Finance platform.
You teach technical analysis, candlestick/harmonic/chart patterns, options, spreads, and platform features.
Use Indian market examples (Nifty, Bank Nifty). Use emojis sparingly: ✅ ⚠️ 📊 💡

STRICT RULES:
1. NEVER reveal astrological formulas/algorithms — say "proprietary model trained on 50+ years of data".
2. NEVER say "Nakshatra". Use "Vedic Yogas" or "cosmic patterns" instead.
3. NEVER give buy/sell recommendations — say "educational, not financial advice".
4. Be EXTREMELY brief: 1-2 short sentences max. Straight to the point, no filler."""

# Tab context descriptions for enriched prompts
TAB_CONTEXT = {
    "marketing": "The user is on the marketing landing page (quant-pattern.com). Pitch them the platform, custom bots, and web development services. Tell them to use the contact form.",
    "dashboard": "The user is on the Dashboard tab viewing market overview and active Vedic Yogas summary.",
    "nakshatra": "The user is on the Astro Analysis tab looking at Vedic Yoga-market correlations and active yogas.",
    "technical": "The user is on the Technical Analysis tab with live chart, pattern markers, Fibonacci, and pivots.",
    "correlation": "The user is on the Correlation tab viewing planetary-market correlation heatmaps.",
    "sentiment": "The user is on the Predictions/Sentiment tab viewing forecasts.",
    "events": "The user is on the Events tab viewing economic calendar and impact analysis.",
    "derivatives": "The user is on the Derivatives tab viewing option chains and strategy analysis.",
}


class AIAssistant:
    """DeepSeek-powered trading assistant with conversation memory."""

    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = {}  # session_id -> messages
        self.max_history = 4  # keep last 4 messages for fast responses

    def _get_client(self):
        """Lazy-load the OpenAI client for DeepSeek."""
        try:
            from openai import OpenAI
            return OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=DEEPSEEK_BASE_URL,
            )
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            raise ImportError("openai package required for AI assistant")

    def chat(self, message: str, session_id: str = "default",
             context: Optional[Dict] = None) -> str:
        """
        Send a message and get an AI response.
        
        Args:
            message: User's message
            session_id: Conversation session identifier
            context: Optional dict with {tab, symbol, patterns, ...}
        
        Returns:
            AI response string
        """
        # Build context-enriched system prompt
        tab = context.get("tab", "") if context else ""
        system = KUBER_SYSTEM_PROMPT if tab == "marketing" else TARA_SYSTEM_PROMPT

        if context:
            tab = context.get("tab", "")
            symbol = context.get("symbol", "")
            extra_context = []

            if tab and tab in TAB_CONTEXT:
                extra_context.append(TAB_CONTEXT[tab])
            if symbol:
                extra_context.append(f"The user is currently viewing: {symbol}")
            if context.get("patterns"):
                pats = ", ".join(context["patterns"][:5])
                extra_context.append(f"Currently detected patterns on chart: {pats}")
            if context.get("price"):
                extra_context.append(f"Current price: ₹{context['price']}")

            if extra_context:
                system += "\n\n## CURRENT USER CONTEXT\n" + "\n".join(f"- {c}" for c in extra_context)

        # Get or create conversation history
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        history = self.conversations[session_id]

        # Add user message
        history.append({"role": "user", "content": message})

        # Trim to max history
        if len(history) > self.max_history:
            history = history[-self.max_history:]
            self.conversations[session_id] = history

        # Build messages for API
        messages = [{"role": "system", "content": system}] + history

        try:
            client = self._get_client()
            is_marketing = tab == "marketing"
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
                max_tokens=55, # Always use 55 tokens max
                temperature=0.7,
                stream=False,
            )

            assistant_reply = response.choices[0].message.content or "I couldn't generate a response. Please try again."

            # Save assistant reply to history
            history.append({"role": "assistant", "content": assistant_reply})
            self.conversations[session_id] = history

            return assistant_reply

        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            # Graceful fallback
            fallback = self._local_fallback(message, context)
            history.append({"role": "assistant", "content": fallback})
            return fallback

    def chat_stream(self, message: str, session_id: str = "default",
             context: Optional[Dict] = None):
        """
        Send a message and get a streaming AI response yielding Server-Sent Events.
        """
        tab = context.get("tab", "") if context else ""
        system = KUBER_SYSTEM_PROMPT if tab == "marketing" else TARA_SYSTEM_PROMPT

        if context:
            tab = context.get("tab", "")
            symbol = context.get("symbol", "")
            extra_context = []

            if tab and tab in TAB_CONTEXT:
                extra_context.append(TAB_CONTEXT[tab])
            if symbol:
                extra_context.append(f"The user is currently viewing: {symbol}")
            if context.get("patterns"):
                pats = ", ".join(context["patterns"][:5])
                extra_context.append(f"Currently detected patterns on chart: {pats}")
            if context.get("price"):
                extra_context.append(f"Current price: ₹{context['price']}")

            if extra_context:
                system += "\n\n## CURRENT USER CONTEXT\n" + "\n".join(f"- {c}" for c in extra_context)

        if session_id not in self.conversations:
            self.conversations[session_id] = []

        history = self.conversations[session_id]
        history.append({"role": "user", "content": message})

        if len(history) > self.max_history:
            history = history[-self.max_history:]
            self.conversations[session_id] = history

        messages = [{"role": "system", "content": system}] + history

        try:
            client = self._get_client()
            is_marketing = tab == "marketing"
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
                max_tokens=55, # Always use 55 tokens max for extreme brevity
                temperature=0.7,
                stream=True,
            )

            full_reply = ""
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_reply += content
                    yield f"data: {json.dumps({'text': content})}\n\n"

            history.append({"role": "assistant", "content": full_reply})
            self.conversations[session_id] = history

        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            fallback = self._local_fallback(message, context)
            history.append({"role": "assistant", "content": fallback})
            import time
            words = fallback.split(" ")
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'text': word + (' ' if i < len(words) - 1 else '')})}\n\n"
                time.sleep(0.05)

    def _local_fallback(self, message: str, context: Optional[Dict] = None) -> str:
        """Provide a helpful response even if the API is down."""
        msg_lower = message.lower()
        tab = context.get("tab", "") if context else ""
        is_marketing = tab == "marketing"

        if any(k in msg_lower for k in ["doji", "candle", "hammer", "engulf", "star", "marubozu"]):
            return ("📊 **Candlestick Patterns** are visual representations of price action:\n\n"
                    "- **Doji**: Open ≈ Close — signals indecision, potential reversal\n"
                    "- **Hammer**: Small body, long lower wick — bullish reversal after downtrend\n"
                    "- **Engulfing**: Current candle completely covers previous — strong reversal\n"
                    "- **Morning/Evening Star**: 3-candle reversal at support/resistance\n\n"
                    "💡 Always confirm with volume and RSI!")

        if any(k in msg_lower for k in ["iron condor", "spread", "straddle", "strangle", "butterfly"]):
            return ("📈 **Options Strategies:**\n\n"
                    "- **Iron Condor**: Sell OTM Call + Put, Buy further OTM — profit in range\n"
                    "- **Bull Call Spread**: Buy lower Call + Sell higher Call — limited risk bullish\n"
                    "- **Straddle**: Buy ATM Call + Put — profit from big moves either way\n"
                    "- **Butterfly**: Low cost, max profit at specific price\n\n"
                    "⚠️ Always understand max loss before placing any trade!")

        if any(k in msg_lower for k in ["fibonacci", "fib", "retrace"]):
            return ("📐 **Fibonacci Retracement** identifies potential support/resistance:\n\n"
                    "Key levels: **38.2%**, **50%**, **61.8%** (Golden Ratio)\n"
                    "- Draw from swing low → swing high (uptrend) or high → low (downtrend)\n"
                    "- 61.8% is the strongest level — prices often bounce here\n\n"
                    "💡 Combine with candlestick patterns for high-probability entries!")

        if any(k in msg_lower for k in ["astro", "nakshatra", "planet", "yoga", "yog", "formula", "calculate", "algorithm"]):
            return ("🔮 Our astro analysis is powered by a **proprietary AI model** trained on "
                    "50+ years of global astrological and market data. It boasts an incredible 80% accuracy rate! 🔥\n\n"
                    "Why trade blind when the smart money uses data? Start predicting market reversals today.\n\n"
                    "👉 **Ready to get your edge? Click 'Platform Login' above to access the app!**")

        if is_marketing:
            return ("👋 Namaste! I'm **Kuber** ✨ — Lead AI Rep for Quant Pattern!\n\n"
                    "I can help you build your trading edge. What are you looking for today?\n"
                    "- 📈 **Astro-Finance Platform:** Get 80% accurate market predictions.\n"
                    "- 🤖 **Custom Trading Bots:** We build automated algos connected to your broker.\n"
                    "- 💻 **App/Web Development:** Need a fintech app built? We do that too.\n\n"
                    "**Drop your details in the Contact Form below to get a custom quote, or click 'Platform Login' to try our app!** 🚀")
        else:
            return ("👋 Namaste! I'm **Tara** ✨ — your AI Trading Mentor!\n\n"
                    "I can help you understand technical patterns, option strategies, or navigating our platform's predictive insights.\n"
                    "What would you like to learn today? 💡")

    def clear_session(self, session_id: str = "default"):
        """Clear conversation history for a session."""
        self.conversations.pop(session_id, None)

    def get_quick_prompts(self, tab: str = "") -> List[str]:
        """Return context-aware quick prompt suggestions."""
        marketing = [
            "How accurate is the platform?",
            "Can you build me a custom trading bot?",
            "Do you develop custom websites or apps?",
            "What is the Pricing?",
            "How does Astro-Finance work?",
        ]

        base = [
            "What is a Doji pattern?",
            "Explain Iron Condor strategy",
            "How to use Fibonacci levels?",
            "What does RSI tell me?",
        ]

        tab_specific = {
            "marketing": marketing,
            "technical": [
                "What patterns are detected on my chart?",
                "How to read harmonic patterns?",
                "What is the XABCD formation?",
                "Explain support and resistance",
            ],
            "derivatives": [
                "Explain Bull Call Spread with example",
                "What is IV (Implied Volatility)?",
                "How does Theta decay work?",
                "Best strategy for range-bound market",
            ],
            "nakshatra": [
                "How does astro Yog analysis work?",
                "What is Angarak Yog and how does it affect markets?",
                "Which Vedic Yogas cause the most volatility?",
                "How reliable is Yog-market correlation?",
            ],
            "correlation": [
                "How to read the correlation heatmap?",
                "What does planetary retrograde mean for markets?",
                "Explain the backtest results",
            ],
            "events": [
                "How do RBI policies affect Nifty?",
                "What is the impact of Fed rate decisions?",
                "How to trade around budget day?",
            ],
            "sentiment": [
                "How are predictions calculated?",
                "What factors affect the forecast?",
                "How to use the weekly prediction?",
            ],
        }

        return tab_specific.get(tab, marketing if not tab else base)[:4]
