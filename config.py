"""
Streamlit configuration and theme settings for Astro-Finance.
"""

# App Title and Branding
APP_TITLE = "🌙 Astro-Finance: Nakshatra Market Analysis"
APP_ICON = "🌙"
APP_SUBTITLE = "Vedic Astrology × NSE Stock Market Correlation"

# Page config
PAGE_CONFIG = {
    "page_title": "Astro-Finance | Nakshatra Analysis",
    "page_icon": "🌙",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Date range defaults
DEFAULT_START_DATE = "2015-01-01"

# Color palette for Nakshatras (mapped to ruling planets)
PLANET_COLORS = {
    "Ketu (South Node)": "#FF6B6B",
    "Venus (Shukra)": "#FF69B4",
    "Sun (Surya)": "#FFD700",
    "Moon (Chandra)": "#C0C0C0",
    "Mars (Mangal)": "#DC143C",
    "Rahu (North Node)": "#4169E1",
    "Jupiter (Guru)": "#FFA500",
    "Saturn (Shani)": "#2F4F4F",
    "Mercury (Budh)": "#32CD32",
}

# Element colors
ELEMENT_COLORS = {
    "Fire": "#FF4500",
    "Earth": "#8B4513",
    "Air": "#87CEEB",
    "Water": "#1E90FF",
    "Ether": "#9370DB",
}

# Gana colors
GANA_COLORS = {
    "Deva (Divine)": "#FFD700",
    "Manushya (Human)": "#32CD32",
    "Rakshasa (Demon)": "#DC143C",
}

# Direction colors
DIRECTION_COLORS = {
    "Bullish": "#00C853",
    "Bearish": "#FF1744",
    "Flat": "#9E9E9E",
}
