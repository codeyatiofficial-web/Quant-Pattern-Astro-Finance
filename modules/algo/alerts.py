import requests
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# User provided Telegram configurations from latest system prompt
TELEGRAM_BOT_TOKEN = "8590460247:AAEoNxIst7RqAq6ivpP5pdVShHu-FE0Q6Qk"
TELEGRAM_CHAT_ID = "" # Needs to be configured

def send_telegram_message(text: str) -> bool:
    """Send a formatted message to a Telegram chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram Bot Token or Chat ID is missing. Cannot send alert.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

def format_premarket_report(global_bias: Dict[str, Any]) -> str:
    """Formats the Pre-Market report sent at 9:00 AM"""
    date_str = datetime.now().strftime("%Y-%m-%d %A")
    changes = global_bias.get('market_changes', {})
    
    # Helper for signing percents
    def p(val):
        return f"+{val}%" if val > 0 else f"{val}%"
        
    report = f"""<b>QUANT-PATTERN PRE-MARKET REPORT</b>
{date_str}

<b>GLOBAL MARKETS:</b>
  S&P 500:     {p(changes.get('S&P 500', 0))}
  NASDAQ:      {p(changes.get('NASDAQ', 0))}
  Nikkei:      {p(changes.get('Nikkei', 0))}
  Hang Seng:   {p(changes.get('Hang Seng', 0))}
  DAX:         {p(changes.get('DAX', 0))}

<b>COMMODITIES:</b>
  Crude Oil:   {p(changes.get('Crude Oil', 0))}
  Gold:        {p(changes.get('Gold', 0))}
  Dollar Index:{p(changes.get('DXY', 0))}

<b>CURRENCY:</b>
  USD/INR:     {changes.get('USDINR', 'N/A')}

<b>US VIX:</b>        {global_bias.get('vix_level', 'N/A')}

<b>GIFT NIFTY GAP:</b> {int(global_bias.get('gap_points', 0))} points ({global_bias.get('gap_label', '')})
<b>GLOBAL BIAS SCORE:</b> {global_bias.get('score', 0)} out of 30
<b>OVERALL BIAS:</b> {global_bias.get('bias_label', 'UNKNOWN')}

<b>TRADING PLAN FOR TODAY:</b>
"""
    # Logic for dynamic trading plan
    score = global_bias.get('score', 0)
    if score >= 15:
        report += "  Prefer BUY setups in morning session\n  Avoid SELL unless domestic signals very strong\n"
    elif score <= -15:
         report += "  Prefer SELL setups in morning session\n  Avoid BUY unless domestic signals very strong\n"
    else:
        report += "  Neutral global bias. Trade purely on algorithm signals.\n"
        
    return report

def format_trade_signal(signal: Dict[str, Any]) -> str:
    """Formats a live buy/sell signal triggered by the scorer."""
    return f"""🚨 <b>TRADE SIGNAL ALERT</b>
<b>Direction:</b> {signal.get('direction', 'UNKNOWN')}
<b>Score:</b> {signal.get('total_score', 0)} / 110
<b>Triggered Steps:</b> {signal.get('steps_triggered', '')}
<b>Global Bias at signal:</b> {signal.get('global_bias_label', '')}
<b>Entry Strike:</b> {signal.get('strike_name', 'N/A')} @ {signal.get('entry_premium', 'N/A')}
<b>Stop Loss:</b> {signal.get('sl', 'N/A')}
<b>Target 1:</b> {signal.get('target1', 'N/A')} (Half Qty)
<b>Target 2:</b> {signal.get('target2', 'N/A')} (Full Qty)
<b>Time:</b> {datetime.now().strftime('%H:%M:%S')}"""

def format_trade_exit(exit_data: Dict[str, Any]) -> str:
    """Formats the exit message when a position closes."""
    pnl = exit_data.get('pnl', 0)
    icon = '🟢' if pnl > 0 else '🔴'
    
    return f"""{icon} <b>TRADE EXIT</b>
<b>Entry:</b> {exit_data.get('entry_price', 0)}
<b>Exit:</b> {exit_data.get('exit_price', 0)}
<b>PnL:</b> {pnl} INR
<b>Reason:</b> {exit_data.get('reason', 'UNKNOWN')}
<b>Duration:</b> {exit_data.get('duration_minutes', 0)} mins"""

def send_warning(warning_text: str):
    """Sends immediate critical warnings."""
    text = f"⚠️ <b>ALGO WARNING</b>\n{warning_text}"
    send_telegram_message(text)
