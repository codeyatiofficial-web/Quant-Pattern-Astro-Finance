"""
News Sentiment Engine for Astro-Finance.
Scrapes financial news RSS feeds and scores headlines using TextBlob polarity.
Compares human market sentiment against active astro-cycle states.
"""

import feedparser
import logging
import ssl
import pandas as pd
from datetime import datetime, timedelta
from textblob import TextBlob

# Workaround for SSL certificate issues on some machines
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

logger = logging.getLogger(__name__)

# Public RSS feeds for Indian financial markets
RSS_FEEDS = {
    "MoneyControl": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "LiveMint": "https://www.livemint.com/rss/markets",
}

# Financial keywords to boost relevance filtering
MARKET_KEYWORDS = [
    "nifty", "sensex", "market", "stock", "share", "rally", "crash", "bull",
    "bear", "rbi", "inflation", "gdp", "fii", "dii", "ipo", "earnings",
    "profit", "loss", "growth", "recession", "rate", "banking", "trade",
    "investment", "funds", "mutual", "equity", "index", "volatility",
]


class NewsSentimentEngine:
    """Fetches and scores financial news headlines for sentiment analysis."""

    def _score_headline(self, text: str) -> dict:
        """Score a single headline using TextBlob polarity (-1 to +1)."""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        if polarity > 0.1:
            label = "Bullish"
        elif polarity < -0.1:
            label = "Bearish"
        else:
            label = "Neutral"

        return {
            "polarity": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
            "label": label,
        }

    def _is_market_relevant(self, text: str) -> bool:
        """Check if a headline is relevant to financial markets."""
        lower = text.lower()
        return any(kw in lower for kw in MARKET_KEYWORDS)

    def get_live_sentiment(self) -> dict:
        """
        Fetch today's live news headlines from RSS feeds and score them.
        Returns a dict with individual headlines and aggregate scores.
        """
        all_headlines = []

        for source_name, feed_url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:20]:  # Cap at 20 per source
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "")
                    published = entry.get("published", "")

                    if not title:
                        continue

                    score = self._score_headline(title)
                    all_headlines.append({
                        "source": source_name,
                        "title": title,
                        "link": link,
                        "published": published,
                        **score,
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch RSS from {source_name}: {e}")

        if not all_headlines:
            return {
                "headlines": [],
                "aggregate": {
                    "avg_polarity": 0.0,
                    "total_headlines": 0,
                    "bullish_count": 0,
                    "bearish_count": 0,
                    "neutral_count": 0,
                    "overall_label": "No Data",
                },
            }

        # Filter for market-relevant headlines
        relevant = [h for h in all_headlines if self._is_market_relevant(h["title"])]
        # If too few relevant, fall back to all
        headlines_to_score = relevant if len(relevant) >= 5 else all_headlines

        polarities = [h["polarity"] for h in headlines_to_score]
        avg_pol = sum(polarities) / len(polarities) if polarities else 0.0

        bullish_count = sum(1 for h in headlines_to_score if h["label"] == "Bullish")
        bearish_count = sum(1 for h in headlines_to_score if h["label"] == "Bearish")
        neutral_count = sum(1 for h in headlines_to_score if h["label"] == "Neutral")

        if avg_pol > 0.05:
            overall = "Bullish"
        elif avg_pol < -0.05:
            overall = "Bearish"
        else:
            overall = "Neutral"

        return {
            "headlines": headlines_to_score[:30],  # Cap response size
            "aggregate": {
                "avg_polarity": round(avg_pol, 4),
                "total_headlines": len(headlines_to_score),
                "bullish_count": bullish_count,
                "bearish_count": bearish_count,
                "neutral_count": neutral_count,
                "overall_label": overall,
            },
        }

    def get_astro_alignment(self, active_astro_states: dict) -> dict:
        """
        Compare current news sentiment against active astrological states.
        active_astro_states: dict of planet -> state (e.g. {"Mercury": "Retrograde", "yogas": ["Vish_Yoga"]})
        Returns alignment analysis.
        """
        sentiment = self.get_live_sentiment()
        agg = sentiment["aggregate"]

        # Determine astro expectation based on known patterns
        bearish_signals = []
        bullish_signals = []

        active_yogas = active_astro_states.get("yogas", [])
        retro_planets = active_astro_states.get("retrograde_planets", [])

        # Known bearish astro patterns
        bearish_yogas = ["Vish_Yoga", "Angarak_Yoga", "Kaal_Sarp_Dosh", "Solar_Eclipse", "Lunar_Eclipse", "Yama_Yoga"]
        bullish_yogas = ["Gajakesari_Yoga", "Budh_Aditya_Yoga", "Shasha_Yoga"]

        for y in active_yogas:
            if y in bearish_yogas:
                bearish_signals.append(f"{y.replace('_', ' ')} (active)")
            elif y in bullish_yogas:
                bullish_signals.append(f"{y.replace('_', ' ')} (active)")

        for p in retro_planets:
            bearish_signals.append(f"{p} Retrograde")

        astro_direction = "Neutral"
        if len(bearish_signals) > len(bullish_signals):
            astro_direction = "Bearish"
        elif len(bullish_signals) > len(bearish_signals):
            astro_direction = "Bullish"

        sentiment_direction = agg["overall_label"]

        if sentiment_direction == astro_direction:
            alignment = "ALIGNED"
            alignment_detail = f"Both news sentiment and astro cycles point {astro_direction.lower()}."
        elif sentiment_direction == "Neutral" or astro_direction == "Neutral":
            alignment = "PARTIAL"
            alignment_detail = f"Sentiment is {sentiment_direction.lower()}, astro cycles are {astro_direction.lower()}. No strong conflict."
        else:
            alignment = "DIVERGENT"
            alignment_detail = f"Sentiment is {sentiment_direction.lower()} but astro cycles suggest {astro_direction.lower()}. Potential reversal signal."

        return {
            "sentiment": agg,
            "astro_direction": astro_direction,
            "bearish_signals": bearish_signals,
            "bullish_signals": bullish_signals,
            "alignment": alignment,
            "alignment_detail": alignment_detail,
        }
