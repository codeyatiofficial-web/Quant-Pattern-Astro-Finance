import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', '.env'))

# To use this, the user needs to set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in their .env file
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message: str):
    """
    Sends a message to the configured Telegram chat.
    If tokens are missing, it just logs it to the console.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning(f"Telegram NOT CONFIG: {message}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram message sent successfully.")
            return True
        else:
            logger.error(f"Failed to send Telegram message: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram API Exception: {e}")
        return False

def send_magnitude_signal(signal_data):
    """
    Formats and sends the magnitude prediction signal via Telegram.
    """
    direction_icon = "✅ BUY" if signal_data['direction'] == "BUY" else ("❌ SELL" if signal_data['direction'] == "SELL" else "➖ NEUTRAL")
    
    # Format supporting/conflicting signals
    global_text = ""
    for s in signal_data.get('supporting_signals', []):
        global_text += f"\n  {s:<9} ✅ SUPPORTS"
    for c in signal_data.get('conflicting_signals', []):
        global_text += f"\n  {c:<9} ⚠️ CONFLICTS"
        
    if not global_text:
        global_text = "\n  No clear global signals"

    time_str = datetime.now().strftime("%I:%M %p")
    
    msg = f"""━━━━━━━━━━━━━━━━━━━━━━━
<b>QUANT-PATTERN SIGNAL</b>
━━━━━━━━━━━━━━━━━━━━━━━
Direction:   {direction_icon}
Confidence:  {signal_data['confidence']} out of 100
Time:        {time_str}

Nifty Now:   {signal_data['current_nifty']}
Target:      {signal_data['target_price']}  ({'+' if signal_data['direction']=='BUY' else '-'}{signal_data['magnitude_points']} pts)
Target Range:{signal_data['target_range_low']} to {signal_data['target_range_high']}
Stop Loss:   {signal_data['stop_loss']}  ({'-' if signal_data['direction']=='BUY' else '+'}{int(signal_data['magnitude_points']/2)} pts)
Risk Reward: 1 : {signal_data['risk_reward']}

Magnitude Confidence: {signal_data['magnitude_confidence']}
Historical Accuracy:  {signal_data['historical_accuracy']}%

Global Signals:{global_text}

<i>Signal valid for next 15 minutes only</i>"""

    return send_telegram_message(msg)
