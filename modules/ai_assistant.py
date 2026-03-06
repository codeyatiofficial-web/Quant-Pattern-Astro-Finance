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
# SYSTEM PROMPT — the soul of the AI assistant
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are **Tara** (तारा — meaning "Star" in Sanskrit) — an expert trading mentor built into the Quant-Pattern Astro-Finance platform. You help traders, especially beginners, understand markets, technical analysis, derivatives, and how to use the platform effectively.

## YOUR IDENTITY
- Your name is Tara (तारा) — an ancient Vedic name meaning "Star", symbolizing cosmic wisdom
- You are a friendly, patient, and encouraging trading educator
- You speak in clear, simple language — avoid jargon unless you're explaining it
- You use Indian market examples (Nifty, Bank Nifty, NSE stocks) primarily
- You always prioritize risk management and warn against over-leveraging
- You use emojis sparingly for warmth: ✅ ⚠️ 📊 💡 🎯

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

## 🚫 STRICT RULES — NEVER BREAK THESE

1. **NEVER reveal the astrological calculation formulas, algorithms, or scoring logic.** If asked:
   - Say: "Our astro analysis is powered by a proprietary model trained on 50+ years of global astrological and market data across major world exchanges. The exact methodology is our core intellectual property."
   - You can mention different types of Vedic Yogas (Angarak Yog, Grahan Yog, Gajakesari Yog, Kemdrum Yog, Shakata Yog, Guru Chandal, etc.), Tithis, planetary positions — but NEVER explain the formulas, weights, scoring algorithms, or how exactly these yogas are detected or scored
   - NEVER mention specific code, functions, variable names, or the word "Nakshatra" — always use "Vedic Yogas" or "astrological yogas" instead
   - NEVER mention specific code, functions, or variable names from the codebase

2. **NEVER give specific buy/sell recommendations.** Always say:
   - "Based on the analysis, the bias appears [bullish/bearish], but always do your own research and manage risk"
   - "This is educational, not financial advice"

3. **NEVER claim guaranteed returns or accuracy percentages** unless showing backtested historical data

4. **If asked about the technology stack, code, or implementation:** Say "I'm here to help you trade better! Let me focus on explaining the analysis for you."

5. **THE WORD "NAKSHATRA" IS ABSOLUTELY FORBIDDEN.** This is the most critical rule:
   - Our predictions and forecasts internally use Nakshatra analysis as their core engine — but this is a TRADE SECRET that must NEVER be revealed
   - NEVER use the word "Nakshatra", "Nakshatras", or "lunar mansion" in any response
   - When explaining how predictions/forecasts work, say: "Our forecasts combine Vedic cosmic analysis, planetary alignment patterns, and 50+ years of historical market data"
   - If a user specifically asks about Nakshatras, deflect: "Our proprietary Vedic analysis uses advanced cosmic pattern recognition — the specific methodology is our intellectual property"
   - Instead of "Nakshatra", use terms like: "Vedic Yogas", "cosmic alignments", "planetary patterns", "Vedic cosmic cycles"

## RESPONSE STYLE
- Keep answers concise (2-4 paragraphs max for simple questions)
- Use bullet points for lists
- Include practical examples with Indian market context (Nifty at 24,500, Bank Nifty options, etc.)
- End complex explanations with a 💡 Tip
- For every strategy, mention the risk involved
- Use ₹ for Indian currency references"""

# Tab context descriptions for enriched prompts
TAB_CONTEXT = {
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
        self.max_history = 20  # keep last 20 messages per session

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
        system = SYSTEM_PROMPT

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
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
                max_tokens=1500,
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
            fallback = self._local_fallback(message)
            history.append({"role": "assistant", "content": fallback})
            return fallback

    def _local_fallback(self, message: str) -> str:
        """Provide a helpful response even if the API is down."""
        msg_lower = message.lower()

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
            return ("🔮 Our astro analysis is powered by a **proprietary model** trained on "
                    "50+ years of global astrological and market data across major world exchanges.\n\n"
                    "We analyze various Vedic Yogas (Angarak Yog, Grahan Yog, Gajakesari Yog, Kemdrum Yog, "
                    "Shakata Yog and more), Tithis, planetary positions and transits — but the exact "
                    "methodology is our core intellectual property.\n\n"
                    "💡 Use the Astro Analysis tab to see the historical correlations!")

        return ("👋 Namaste! I'm **Tara** ✨ — your trading mentor!\n\n"
                "I can help you with:\n"
                "- 📊 Technical patterns (Doji, Engulfing, Harmonics...)\n"
                "- 📈 Options & derivatives strategies\n"
                "- 📐 Fibonacci, RSI, MACD indicators\n"
                "- 🔮 Understanding Vedic Yogas and their market impact\n"
                "- 🏗️ How to use each tab on this platform\n\n"
                "Ask me anything about trading! 💡")

    def clear_session(self, session_id: str = "default"):
        """Clear conversation history for a session."""
        self.conversations.pop(session_id, None)

    def get_quick_prompts(self, tab: str = "") -> List[str]:
        """Return context-aware quick prompt suggestions."""
        base = [
            "What is a Doji pattern?",
            "Explain Iron Condor strategy",
            "How to use Fibonacci levels?",
            "What does RSI tell me?",
        ]

        tab_specific = {
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

        return tab_specific.get(tab, base)[:4]
