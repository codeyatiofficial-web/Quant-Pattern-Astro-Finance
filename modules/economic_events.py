"""
Economic Events Engine for Astro-Finance.
Provides a comprehensive historical database of major economic events that affect Indian
markets (RBI, Fed, Budget, Elections, US Bonds, CPI, Oil, GST, Earnings, Global Shocks),
backtesting of market reactions, and upcoming event alerts with forecast integration.
"""

import logging
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from modules.market_data import MarketDataFetcher

def _safe_round(val, decimals=3):
    """Round a value safely, converting NaN/Inf to None for JSON."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, decimals)
    except (TypeError, ValueError):
        return None

logger = logging.getLogger(__name__)

# ============================================================
# HISTORICAL EVENTS DATABASE — COMPREHENSIVE
# Each event has: date, category, sub_event, description, expected_bias
# ============================================================

HISTORICAL_EVENTS = [
    # ===== RBI RATE CUTS =====
    {"date": "2015-01-15", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI surprise rate cut by 25bps to 7.75%", "expected_bias": "Bullish"},
    {"date": "2015-03-04", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate 25bps to 7.5%", "expected_bias": "Bullish"},
    {"date": "2015-06-02", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate 25bps to 7.25%", "expected_bias": "Bullish"},
    {"date": "2015-09-29", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI surprise 50bps cut to 6.75%", "expected_bias": "Bullish"},
    {"date": "2016-04-05", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate to 6.5%", "expected_bias": "Bullish"},
    {"date": "2017-08-02", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate to 6.0%", "expected_bias": "Bullish"},
    {"date": "2019-02-07", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate 25bps to 6.25%", "expected_bias": "Bullish"},
    {"date": "2019-04-04", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate to 6.0%", "expected_bias": "Bullish"},
    {"date": "2019-06-06", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate to 5.75%", "expected_bias": "Bullish"},
    {"date": "2019-08-07", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate 35bps to 5.40%", "expected_bias": "Bullish"},
    {"date": "2019-10-04", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate to 5.15%", "expected_bias": "Bullish"},
    {"date": "2020-03-27", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "Emergency COVID rate cut 75bps to 4.40%", "expected_bias": "Bullish"},
    {"date": "2020-05-22", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate 40bps to 4.0%", "expected_bias": "Bullish"},
    {"date": "2023-04-06", "category": "RBI Policy", "sub_event": "Rate Hold", "description": "RBI surprise pause at 6.50%", "expected_bias": "Bullish"},
    {"date": "2025-02-07", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate 25bps to 6.25%", "expected_bias": "Bullish"},

    # ===== RBI RATE HIKES =====
    {"date": "2018-06-06", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo rate 25bps to 6.25%", "expected_bias": "Bearish"},
    {"date": "2018-08-01", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo rate 25bps to 6.50%", "expected_bias": "Bearish"},
    {"date": "2022-05-04", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "Emergency rate hike 40bps to 4.40%", "expected_bias": "Bearish"},
    {"date": "2022-06-08", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo rate 50bps to 4.90%", "expected_bias": "Bearish"},
    {"date": "2022-08-05", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo rate 50bps to 5.40%", "expected_bias": "Bearish"},
    {"date": "2022-09-30", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo rate 50bps to 5.90%", "expected_bias": "Bearish"},
    {"date": "2022-12-07", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo rate 35bps to 6.25%", "expected_bias": "Bearish"},
    {"date": "2023-02-08", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo rate 25bps to 6.50%", "expected_bias": "Bearish"},

    # ===== UNION BUDGET =====
    {"date": "2015-02-28", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2015-16", "expected_bias": "Neutral"},
    {"date": "2016-02-29", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2016-17", "expected_bias": "Neutral"},
    {"date": "2017-02-01", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2017-18 (Rail+General merged)", "expected_bias": "Neutral"},
    {"date": "2018-02-01", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2018-19 (LTCG introduced)", "expected_bias": "Bearish"},
    {"date": "2019-02-01", "category": "Union Budget", "sub_event": "Budget Day", "description": "Interim Budget 2019-20", "expected_bias": "Neutral"},
    {"date": "2019-07-05", "category": "Union Budget", "sub_event": "Budget Day", "description": "Full Budget 2019-20 (Surcharge hike)", "expected_bias": "Bearish"},
    {"date": "2020-02-01", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2020-21", "expected_bias": "Neutral"},
    {"date": "2021-02-01", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2021-22 (Infra push)", "expected_bias": "Bullish"},
    {"date": "2022-02-01", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2022-23", "expected_bias": "Neutral"},
    {"date": "2023-02-01", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2023-24", "expected_bias": "Neutral"},
    {"date": "2024-02-01", "category": "Union Budget", "sub_event": "Budget Day", "description": "Interim Budget 2024-25", "expected_bias": "Neutral"},
    {"date": "2024-07-23", "category": "Union Budget", "sub_event": "Budget Day", "description": "Full Budget 2024-25 (LTCG changes)", "expected_bias": "Bearish"},
    {"date": "2025-02-01", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2025-26", "expected_bias": "Neutral"},

    # ===== US FED FOMC =====
    {"date": "2022-03-16", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 25bps (first post-COVID hike)", "expected_bias": "Bearish"},
    {"date": "2022-05-04", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 50bps", "expected_bias": "Bearish"},
    {"date": "2022-06-15", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 75bps (jumbo)", "expected_bias": "Bearish"},
    {"date": "2022-07-27", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 75bps", "expected_bias": "Bearish"},
    {"date": "2022-09-21", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 75bps", "expected_bias": "Bearish"},
    {"date": "2022-11-02", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 75bps", "expected_bias": "Bearish"},
    {"date": "2022-12-14", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 50bps", "expected_bias": "Bearish"},
    {"date": "2023-02-01", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 25bps", "expected_bias": "Bearish"},
    {"date": "2023-03-22", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 25bps", "expected_bias": "Bearish"},
    {"date": "2024-09-18", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts 50bps (pivot)", "expected_bias": "Bullish"},
    {"date": "2024-11-07", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts 25bps", "expected_bias": "Bullish"},
    {"date": "2024-12-18", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts 25bps", "expected_bias": "Bullish"},

    # ===== US TREASURY / BOND YIELD EVENTS =====
    {"date": "2018-02-05", "category": "US Bonds", "sub_event": "Bond Yield Spike", "description": "US 10Y yield crosses 2.85% — global equity selloff", "expected_bias": "Bearish"},
    {"date": "2018-10-03", "category": "US Bonds", "sub_event": "Bond Yield Spike", "description": "US 10Y yield surges past 3.2% — EM selloff", "expected_bias": "Bearish"},
    {"date": "2019-08-14", "category": "US Bonds", "sub_event": "Yield Curve Inversion", "description": "2Y-10Y yield curve inverts — recession signal", "expected_bias": "Bearish"},
    {"date": "2022-04-11", "category": "US Bonds", "sub_event": "Bond Yield Spike", "description": "US 10Y yield crosses 2.8% — tightening fears", "expected_bias": "Bearish"},
    {"date": "2022-10-21", "category": "US Bonds", "sub_event": "Bond Yield Spike", "description": "US 10Y yield crosses 4.3% — global bond rout", "expected_bias": "Bearish"},
    {"date": "2023-10-19", "category": "US Bonds", "sub_event": "Bond Yield Spike", "description": "US 10Y yield crosses 5% — highest since 2007", "expected_bias": "Bearish"},
    {"date": "2024-01-02", "category": "US Bonds", "sub_event": "Bond Yield Drop", "description": "US 10Y yield drops below 3.9% — rate cut hopes", "expected_bias": "Bullish"},
    {"date": "2024-09-16", "category": "US Bonds", "sub_event": "Bond Yield Drop", "description": "US 10Y plunges on Fed pivot anticipation", "expected_bias": "Bullish"},

    # ===== US CPI / INFLATION DATA =====
    {"date": "2021-06-10", "category": "US CPI", "sub_event": "CPI Surprise High", "description": "US CPI at 5.0% YoY — 13-year high", "expected_bias": "Bearish"},
    {"date": "2021-11-10", "category": "US CPI", "sub_event": "CPI Surprise High", "description": "US CPI at 6.2% YoY — 30-year high", "expected_bias": "Bearish"},
    {"date": "2022-01-12", "category": "US CPI", "sub_event": "CPI Surprise High", "description": "US CPI at 7.0% YoY — 40-year high", "expected_bias": "Bearish"},
    {"date": "2022-06-10", "category": "US CPI", "sub_event": "CPI Surprise High", "description": "US CPI at 8.6% YoY — peak inflation", "expected_bias": "Bearish"},
    {"date": "2022-07-13", "category": "US CPI", "sub_event": "CPI Surprise High", "description": "US CPI at 9.1% YoY — cycle peak", "expected_bias": "Bearish"},
    {"date": "2022-11-10", "category": "US CPI", "sub_event": "CPI Below Estimate", "description": "US CPI at 7.7% — below 8% expected, rally trigger", "expected_bias": "Bullish"},
    {"date": "2023-07-12", "category": "US CPI", "sub_event": "CPI Below Estimate", "description": "US CPI drops to 3.0% — disinflation confirmed", "expected_bias": "Bullish"},
    {"date": "2024-05-15", "category": "US CPI", "sub_event": "CPI Below Estimate", "description": "US CPI at 3.4% — rate cut hopes rise", "expected_bias": "Bullish"},

    # ===== US JOBS / NON-FARM PAYROLLS =====
    {"date": "2022-01-07", "category": "US Jobs", "sub_event": "NFP Strong", "description": "US adds 199K jobs — Fed hawkish signal", "expected_bias": "Bearish"},
    {"date": "2022-07-08", "category": "US Jobs", "sub_event": "NFP Strong", "description": "US adds 528K jobs — rate hike fears", "expected_bias": "Bearish"},
    {"date": "2023-01-06", "category": "US Jobs", "sub_event": "NFP Strong", "description": "US adds 223K jobs — soft landing hopes", "expected_bias": "Neutral"},
    {"date": "2023-08-04", "category": "US Jobs", "sub_event": "NFP Weak", "description": "US adds 187K — below estimate, rate pause hope", "expected_bias": "Bullish"},
    {"date": "2024-08-02", "category": "US Jobs", "sub_event": "NFP Weak", "description": "US adds 114K — recession fears spike", "expected_bias": "Bearish"},
    {"date": "2024-09-06", "category": "US Jobs", "sub_event": "NFP Weak", "description": "US adds 142K — Fed pivot catalyst", "expected_bias": "Bullish"},

    # ===== INDIA ELECTIONS =====
    {"date": "2014-05-16", "category": "Elections", "sub_event": "General Election Result", "description": "BJP wins majority (Modi wave)", "expected_bias": "Bullish"},
    {"date": "2019-05-23", "category": "Elections", "sub_event": "General Election Result", "description": "BJP wins second term with bigger majority", "expected_bias": "Bullish"},
    {"date": "2024-06-04", "category": "Elections", "sub_event": "General Election Result", "description": "NDA wins but BJP loses single-party majority", "expected_bias": "Bearish"},
    {"date": "2017-03-11", "category": "Elections", "sub_event": "State Election Result", "description": "BJP sweeps UP with 312 seats", "expected_bias": "Bullish"},
    {"date": "2018-12-11", "category": "Elections", "sub_event": "State Election Result", "description": "Congress wins MP, Rajasthan, Chhattisgarh", "expected_bias": "Bearish"},
    {"date": "2022-03-10", "category": "Elections", "sub_event": "State Election Result", "description": "BJP wins UP, Punjab goes AAP", "expected_bias": "Bullish"},
    {"date": "2023-12-03", "category": "Elections", "sub_event": "State Election Result", "description": "BJP sweeps MP, Rajasthan, Chhattisgarh", "expected_bias": "Bullish"},

    # ===== US ELECTIONS =====
    {"date": "2016-11-09", "category": "US Elections", "sub_event": "US Presidential Result", "description": "Trump wins 2016 — markets initially drop then rally", "expected_bias": "Neutral"},
    {"date": "2020-11-07", "category": "US Elections", "sub_event": "US Presidential Result", "description": "Biden wins 2020 — stimulus hopes", "expected_bias": "Bullish"},
    {"date": "2024-11-06", "category": "US Elections", "sub_event": "US Presidential Result", "description": "Trump wins 2024 — tariff fears + dollar rally", "expected_bias": "Bearish"},

    # ===== OIL PRICE SHOCKS =====
    {"date": "2016-01-20", "category": "Oil/Commodity", "sub_event": "Oil Price Crash", "description": "Crude oil hits $26/barrel — multi-year low", "expected_bias": "Bullish"},
    {"date": "2018-10-03", "category": "Oil/Commodity", "sub_event": "Oil Price Spike", "description": "Crude oil crosses $86/barrel — INR weakens", "expected_bias": "Bearish"},
    {"date": "2020-04-20", "category": "Oil/Commodity", "sub_event": "Oil Price Crash", "description": "WTI crude goes NEGATIVE (-$37/barrel)", "expected_bias": "Bearish"},
    {"date": "2022-03-07", "category": "Oil/Commodity", "sub_event": "Oil Price Spike", "description": "Crude oil crosses $130/barrel — Ukraine war", "expected_bias": "Bearish"},
    {"date": "2022-06-08", "category": "Oil/Commodity", "sub_event": "Oil Price Spike", "description": "Crude at $122 — inflation fears peak", "expected_bias": "Bearish"},
    {"date": "2023-06-05", "category": "Oil/Commodity", "sub_event": "Oil Price Drop", "description": "Crude drops below $70 — demand worries", "expected_bias": "Bullish"},
    {"date": "2024-09-10", "category": "Oil/Commodity", "sub_event": "Oil Price Drop", "description": "Crude drops below $68 — global slowdown", "expected_bias": "Bullish"},

    # ===== GST COUNCIL DECISIONS =====
    {"date": "2017-07-01", "category": "GST", "sub_event": "GST Launch", "description": "GST rollout across India — historic tax reform", "expected_bias": "Neutral"},
    {"date": "2017-11-10", "category": "GST", "sub_event": "GST Rate Cut", "description": "GST Council cuts rates on 178 items", "expected_bias": "Bullish"},
    {"date": "2018-07-21", "category": "GST", "sub_event": "GST Rate Cut", "description": "GST cut on 100+ items — consumer boost", "expected_bias": "Bullish"},
    {"date": "2019-09-20", "category": "GST", "sub_event": "GST Rate Cut", "description": "Corporate tax slashed to 22% — mega reform", "expected_bias": "Bullish"},
    {"date": "2022-06-29", "category": "GST", "sub_event": "GST Rate Hike", "description": "GST on pre-packed foods, hospital rooms", "expected_bias": "Bearish"},

    # ===== INDIA CPI / INFLATION =====
    {"date": "2020-01-13", "category": "India CPI", "sub_event": "India CPI High", "description": "India CPI at 7.35% — above RBI tolerance", "expected_bias": "Bearish"},
    {"date": "2021-11-12", "category": "India CPI", "sub_event": "India CPI High", "description": "India CPI at 4.48% — food prices drive up", "expected_bias": "Neutral"},
    {"date": "2022-04-12", "category": "India CPI", "sub_event": "India CPI High", "description": "India CPI at 6.95% — breaches RBI 6% ceiling", "expected_bias": "Bearish"},
    {"date": "2022-06-13", "category": "India CPI", "sub_event": "India CPI High", "description": "India CPI at 7.01% — emergency hike trigger", "expected_bias": "Bearish"},
    {"date": "2023-06-12", "category": "India CPI", "sub_event": "India CPI Low", "description": "India CPI drops to 4.25% — within RBI band", "expected_bias": "Bullish"},
    {"date": "2024-09-12", "category": "India CPI", "sub_event": "India CPI Low", "description": "India CPI at 3.65% — rate cut speculation", "expected_bias": "Bullish"},

    # ===== FII / DII FLOWS =====
    {"date": "2018-10-01", "category": "FII Flows", "sub_event": "FII Massive Sell", "description": "FIIs sell ₹24,000cr in Oct 2018 — IL&FS crisis", "expected_bias": "Bearish"},
    {"date": "2020-03-16", "category": "FII Flows", "sub_event": "FII Massive Sell", "description": "FIIs sell ₹1.1L cr in March 2020 — COVID", "expected_bias": "Bearish"},
    {"date": "2021-10-01", "category": "FII Flows", "sub_event": "FII Massive Sell", "description": "FIIs turn net sellers for first time in FY22", "expected_bias": "Bearish"},
    {"date": "2022-01-03", "category": "FII Flows", "sub_event": "FII Massive Sell", "description": "FIIs sell ₹33,300cr in Jan 2022", "expected_bias": "Bearish"},
    {"date": "2024-10-01", "category": "FII Flows", "sub_event": "FII Massive Sell", "description": "FIIs sell ₹94,000cr in Oct 2024 — record month", "expected_bias": "Bearish"},
    {"date": "2020-11-01", "category": "FII Flows", "sub_event": "FII Massive Buy", "description": "FIIs invest ₹60,000cr in Nov 2020 — vaccine rally", "expected_bias": "Bullish"},
    {"date": "2023-07-01", "category": "FII Flows", "sub_event": "FII Massive Buy", "description": "FIIs invest ₹46,000cr in Jul 2023", "expected_bias": "Bullish"},

    # ===== QUARTERLY EARNINGS SEASON =====
    {"date": "2020-07-13", "category": "Earnings Season", "sub_event": "IT Earnings Beat", "description": "TCS Q1 FY21 beats estimates — WFH tailwind", "expected_bias": "Bullish"},
    {"date": "2021-01-08", "category": "Earnings Season", "sub_event": "IT Earnings Beat", "description": "TCS/Infy Q3 FY21 beat — IT rally", "expected_bias": "Bullish"},
    {"date": "2022-04-13", "category": "Earnings Season", "sub_event": "IT Earnings Miss", "description": "Infosys cuts FY23 guidance — IT selloff", "expected_bias": "Bearish"},
    {"date": "2022-10-13", "category": "Earnings Season", "sub_event": "IT Earnings Miss", "description": "HCL Tech weak Q2 outlook — attrition concerns", "expected_bias": "Bearish"},
    {"date": "2023-07-20", "category": "Earnings Season", "sub_event": "Bank Earnings Beat", "description": "HDFC Bank Q1 FY24 beats after merger", "expected_bias": "Bullish"},
    {"date": "2024-01-17", "category": "Earnings Season", "sub_event": "Bank Earnings Beat", "description": "HDFC Bank Q3 FY24 strong — banking sector rally", "expected_bias": "Bullish"},
    {"date": "2024-10-16", "category": "Earnings Season", "sub_event": "Bank Earnings Miss", "description": "HDFC Bank Q2 FY25 miss — deposit growth concern", "expected_bias": "Bearish"},

    # ===== GLOBAL SHOCKS =====
    {"date": "2015-08-24", "category": "Global Shock", "sub_event": "China Crash", "description": "China Black Monday — Shanghai crashes 8.5%", "expected_bias": "Bearish"},
    {"date": "2016-06-24", "category": "Global Shock", "sub_event": "Brexit", "description": "UK votes for Brexit — global risk-off", "expected_bias": "Bearish"},
    {"date": "2016-11-08", "category": "Global Shock", "sub_event": "Demonetization", "description": "India demonetizes 500 & 1000 rupee notes", "expected_bias": "Bearish"},
    {"date": "2018-09-21", "category": "Global Shock", "sub_event": "IL&FS Crisis", "description": "IL&FS defaults — Indian NBFC crisis begins", "expected_bias": "Bearish"},
    {"date": "2020-03-12", "category": "Global Shock", "sub_event": "COVID Crash", "description": "WHO declares COVID-19 pandemic", "expected_bias": "Bearish"},
    {"date": "2020-03-23", "category": "Global Shock", "sub_event": "COVID Bottom", "description": "Nifty hits COVID low ~7511", "expected_bias": "Bullish"},
    {"date": "2022-02-24", "category": "Global Shock", "sub_event": "Russia-Ukraine War", "description": "Russia invades Ukraine", "expected_bias": "Bearish"},
    {"date": "2023-03-10", "category": "Global Shock", "sub_event": "SVB Bank Failure", "description": "Silicon Valley Bank collapses — banking fears", "expected_bias": "Bearish"},
    {"date": "2023-10-07", "category": "Global Shock", "sub_event": "Israel-Hamas War", "description": "Hamas attacks Israel — oil/geopolitical risk", "expected_bias": "Bearish"},
    {"date": "2024-08-05", "category": "Global Shock", "sub_event": "Japan Carry Trade Unwind", "description": "Nikkei crashes 12% — carry trade unwind, global selloff", "expected_bias": "Bearish"},
    {"date": "2025-02-01", "category": "Global Shock", "sub_event": "US Tariff Shock", "description": "Trump imposes tariffs on Canada, Mexico, China", "expected_bias": "Bearish"},

    # ===== CORPORATE ACTIONS / IPO =====
    {"date": "2021-11-10", "category": "IPO/Corporate", "sub_event": "Major IPO", "description": "Nykaa IPO lists at 79% premium", "expected_bias": "Bullish"},
    {"date": "2021-11-18", "category": "IPO/Corporate", "sub_event": "Major IPO", "description": "Paytm IPO lists at 27% discount — worst debut", "expected_bias": "Bearish"},
    {"date": "2022-05-25", "category": "IPO/Corporate", "sub_event": "Major IPO", "description": "LIC IPO — India's largest at ₹21,000cr", "expected_bias": "Neutral"},
    {"date": "2023-09-27", "category": "IPO/Corporate", "sub_event": "Adani Crisis", "description": "Hindenburg vs Adani — ₹10L cr market cap wiped", "expected_bias": "Bearish"},

    # ===== CURRENCY SHOCKS (INR) =====
    {"date": "2018-10-05", "category": "Currency", "sub_event": "INR Crash", "description": "Rupee hits 74/$ — oil + FII outflow", "expected_bias": "Bearish"},
    {"date": "2022-07-19", "category": "Currency", "sub_event": "INR Crash", "description": "Rupee breaches 80/$ for first time", "expected_bias": "Bearish"},
    {"date": "2023-10-20", "category": "Currency", "sub_event": "INR Crash", "description": "Rupee hits 83.3/$ — all-time low", "expected_bias": "Bearish"},
    {"date": "2024-11-22", "category": "Currency", "sub_event": "INR Crash", "description": "Rupee breaches 84.4/$ — Trump tariff fears", "expected_bias": "Bearish"},

    # ===== EXPANDED HISTORICAL DATA (2000-2025) =====
    {"date": "2001-03-01", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate post dot-com bust", "expected_bias": "Bullish"},
    {"date": "2001-10-22", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate post 9/11 slowdown", "expected_bias": "Bullish"},
    {"date": "2002-03-01", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts bank rate to 6.5%", "expected_bias": "Bullish"},
    {"date": "2003-03-03", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts bank rate to 6.25%", "expected_bias": "Bullish"},
    {"date": "2003-04-29", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts bank rate to 6.0%", "expected_bias": "Bullish"},
    {"date": "2004-10-26", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI reverse repo at 4.75%", "expected_bias": "Bullish"},
    {"date": "2009-01-05", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo 100bps to 5.5% — GFC response", "expected_bias": "Bullish"},
    {"date": "2009-03-04", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo 50bps to 5.0% — GFC easing", "expected_bias": "Bullish"},
    {"date": "2009-04-21", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo 25bps to 4.75% — record low", "expected_bias": "Bullish"},
    {"date": "2012-04-17", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate 50bps to 8.0%", "expected_bias": "Bullish"},
    {"date": "2013-05-03", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI cuts repo rate 25bps to 7.25%", "expected_bias": "Bullish"},
    {"date": "2014-01-28", "category": "RBI Policy", "sub_event": "Rate Cut", "description": "RBI keeps rate at 8.0% — surprise hold", "expected_bias": "Neutral"},
    {"date": "2004-10-27", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes reverse repo 25bps — tightening begins", "expected_bias": "Bearish"},
    {"date": "2005-04-28", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes reverse repo 25bps to 5.0%", "expected_bias": "Bearish"},
    {"date": "2005-10-25", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes reverse repo to 5.25%", "expected_bias": "Bearish"},
    {"date": "2006-01-24", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo rate 25bps to 6.5%", "expected_bias": "Bearish"},
    {"date": "2006-06-09", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo 25bps to 6.75%", "expected_bias": "Bearish"},
    {"date": "2006-07-25", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo 25bps to 7.0%", "expected_bias": "Bearish"},
    {"date": "2007-01-31", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo to 7.5%", "expected_bias": "Bearish"},
    {"date": "2007-03-30", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo to 7.75%", "expected_bias": "Bearish"},
    {"date": "2008-06-11", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo 25bps to 8.0% — inflation fight", "expected_bias": "Bearish"},
    {"date": "2008-06-25", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI emergency 50bps hike to 8.5%", "expected_bias": "Bearish"},
    {"date": "2008-07-29", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo 50bps to 9.0% — peak rate", "expected_bias": "Bearish"},
    {"date": "2010-03-19", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo 25bps to 5.0% — exit from GFC easing", "expected_bias": "Bearish"},
    {"date": "2010-07-27", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo 25bps to 5.75%", "expected_bias": "Bearish"},
    {"date": "2011-01-25", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes repo 25bps to 6.5%", "expected_bias": "Bearish"},
    {"date": "2011-03-17", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI surprise inter-meeting hike to 6.75%", "expected_bias": "Bearish"},
    {"date": "2011-05-03", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes 50bps to 7.25%", "expected_bias": "Bearish"},
    {"date": "2011-07-26", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes 50bps to 8.0%", "expected_bias": "Bearish"},
    {"date": "2011-10-25", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes 25bps to 8.5% — peak of cycle", "expected_bias": "Bearish"},
    {"date": "2013-09-20", "category": "RBI Policy", "sub_event": "Rate Hike", "description": "RBI hikes 25bps to 7.5% — Rajan's first move", "expected_bias": "Bearish"},
    {"date": "2000-02-29", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2000-01 (IT tax reform)", "expected_bias": "Neutral"},
    {"date": "2001-02-28", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2001-02", "expected_bias": "Neutral"},
    {"date": "2002-02-28", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2002-03", "expected_bias": "Neutral"},
    {"date": "2003-02-28", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2003-04", "expected_bias": "Neutral"},
    {"date": "2004-02-03", "category": "Union Budget", "sub_event": "Budget Day", "description": "Interim Budget 2004-05", "expected_bias": "Neutral"},
    {"date": "2004-07-08", "category": "Union Budget", "sub_event": "Budget Day", "description": "Full Budget 2004-05 (UPA-I)", "expected_bias": "Bearish"},
    {"date": "2005-02-28", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2005-06", "expected_bias": "Neutral"},
    {"date": "2006-02-28", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2006-07 (FBT introduced)", "expected_bias": "Bearish"},
    {"date": "2007-02-28", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2007-08", "expected_bias": "Neutral"},
    {"date": "2008-02-29", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2008-09 (Farm loan waiver)", "expected_bias": "Bullish"},
    {"date": "2009-02-16", "category": "Union Budget", "sub_event": "Budget Day", "description": "Interim Budget 2009-10", "expected_bias": "Neutral"},
    {"date": "2009-07-06", "category": "Union Budget", "sub_event": "Budget Day", "description": "Full Budget 2009-10 (UPA-II)", "expected_bias": "Bearish"},
    {"date": "2010-02-26", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2010-11", "expected_bias": "Neutral"},
    {"date": "2011-02-28", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2011-12", "expected_bias": "Neutral"},
    {"date": "2012-03-16", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2012-13 (GAAR shock)", "expected_bias": "Bearish"},
    {"date": "2013-02-28", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2013-14", "expected_bias": "Neutral"},
    {"date": "2014-02-17", "category": "Union Budget", "sub_event": "Budget Day", "description": "Interim Budget 2014-15", "expected_bias": "Neutral"},
    {"date": "2014-07-10", "category": "Union Budget", "sub_event": "Budget Day", "description": "Full Budget 2014-15 (Modi's first)", "expected_bias": "Bullish"},
    {"date": "2001-01-03", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed emergency 50bps cut to 6.0% — dot-com bust", "expected_bias": "Bullish"},
    {"date": "2001-03-20", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts 50bps to 5.0%", "expected_bias": "Bullish"},
    {"date": "2001-09-17", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed emergency cut post-9/11 to 3.0%", "expected_bias": "Bullish"},
    {"date": "2001-12-11", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts to 1.75%", "expected_bias": "Bullish"},
    {"date": "2003-06-25", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts to 1.0% — record low", "expected_bias": "Bullish"},
    {"date": "2004-06-30", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 25bps to 1.25% — tightening begins", "expected_bias": "Bearish"},
    {"date": "2005-02-02", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 2.5%", "expected_bias": "Bearish"},
    {"date": "2005-06-30", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 3.25%", "expected_bias": "Bearish"},
    {"date": "2005-12-13", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 4.25%", "expected_bias": "Bearish"},
    {"date": "2006-06-29", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 5.25% — cycle peak", "expected_bias": "Bearish"},
    {"date": "2007-09-18", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts 50bps to 4.75% — subprime response", "expected_bias": "Bullish"},
    {"date": "2008-01-22", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed emergency 75bps cut — market in freefall", "expected_bias": "Bullish"},
    {"date": "2008-03-18", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts 75bps to 2.25% — Bear Stearns week", "expected_bias": "Bullish"},
    {"date": "2008-10-08", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Coordinated global cut post-Lehman", "expected_bias": "Bullish"},
    {"date": "2008-12-16", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts to 0-0.25% — zero bound", "expected_bias": "Bullish"},
    {"date": "2015-12-16", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 25bps — first in 9 years", "expected_bias": "Bearish"},
    {"date": "2016-12-14", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 25bps to 0.75%", "expected_bias": "Bearish"},
    {"date": "2017-03-15", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 1.0%", "expected_bias": "Bearish"},
    {"date": "2017-06-14", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 1.25%", "expected_bias": "Bearish"},
    {"date": "2017-12-13", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 1.5%", "expected_bias": "Bearish"},
    {"date": "2018-03-21", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 1.75% — Powell's first", "expected_bias": "Bearish"},
    {"date": "2018-06-13", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 2.0%", "expected_bias": "Bearish"},
    {"date": "2018-09-26", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 2.25%", "expected_bias": "Bearish"},
    {"date": "2018-12-19", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes to 2.5% — Dec 2018 crash trigger", "expected_bias": "Bearish"},
    {"date": "2019-07-31", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts 25bps — insurance cut", "expected_bias": "Bullish"},
    {"date": "2019-09-18", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts 25bps to 2.0%", "expected_bias": "Bullish"},
    {"date": "2019-10-30", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed cuts 25bps to 1.75%", "expected_bias": "Bullish"},
    {"date": "2020-03-03", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed emergency 50bps cut — COVID first response", "expected_bias": "Bullish"},
    {"date": "2020-03-15", "category": "US Fed", "sub_event": "Fed Rate Cut", "description": "Fed emergency cut to 0% + QE — COVID nuclear option", "expected_bias": "Bullish"},
    {"date": "2023-05-03", "category": "US Fed", "sub_event": "Fed Rate Hike", "description": "Fed hikes 25bps to 5.25% — final hike of cycle", "expected_bias": "Bearish"},
    {"date": "2004-05-13", "category": "Elections", "sub_event": "General Election Result", "description": "UPA wins — BJP loses despite India Shining (market crashed 10%+)", "expected_bias": "Bearish"},
    {"date": "2009-05-18", "category": "Elections", "sub_event": "General Election Result", "description": "UPA-II wins clear majority — Nifty upper circuit", "expected_bias": "Bullish"},
    {"date": "2015-02-10", "category": "Elections", "sub_event": "State Election Result", "description": "AAP sweeps Delhi with 67/70 seats", "expected_bias": "Bearish"},
    {"date": "2016-05-19", "category": "Elections", "sub_event": "State Election Result", "description": "TMC wins West Bengal, DMK wins Tamil Nadu", "expected_bias": "Neutral"},
    {"date": "2021-05-02", "category": "Elections", "sub_event": "State Election Result", "description": "TMC wins Bengal, BJP wins Assam", "expected_bias": "Neutral"},
    {"date": "2000-12-13", "category": "US Elections", "sub_event": "US Presidential Result", "description": "Bush wins after Florida recount — settled by Supreme Court", "expected_bias": "Neutral"},
    {"date": "2008-11-04", "category": "US Elections", "sub_event": "US Presidential Result", "description": "Obama wins 2008 — historic, during GFC", "expected_bias": "Neutral"},
    {"date": "2012-11-06", "category": "US Elections", "sub_event": "US Presidential Result", "description": "Obama re-elected — continuity trade", "expected_bias": "Neutral"},
    {"date": "2001-09-11", "category": "Global Shock", "sub_event": "Terror Attack", "description": "9/11 terror attacks — global markets crash", "expected_bias": "Bearish"},
    {"date": "2008-09-15", "category": "Global Shock", "sub_event": "Lehman Collapse", "description": "Lehman Brothers files bankruptcy — GFC begins", "expected_bias": "Bearish"},
    {"date": "2008-10-10", "category": "Global Shock", "sub_event": "GFC Bottom", "description": "Nifty hits GFC low ~2600 — capitulation", "expected_bias": "Bullish"},
    {"date": "2010-05-06", "category": "Global Shock", "sub_event": "Flash Crash", "description": "US Flash Crash — Dow drops 1000pts in minutes", "expected_bias": "Bearish"},
    {"date": "2011-08-05", "category": "Global Shock", "sub_event": "US Downgrade", "description": "S&P downgrades US credit rating from AAA", "expected_bias": "Bearish"},
    {"date": "2013-05-22", "category": "Global Shock", "sub_event": "Taper Tantrum", "description": "Bernanke hints at QE taper — EM selloff", "expected_bias": "Bearish"},
    {"date": "2015-08-11", "category": "Global Shock", "sub_event": "China Devaluation", "description": "China devalues yuan — global risk-off", "expected_bias": "Bearish"},
    {"date": "2018-12-24", "category": "Global Shock", "sub_event": "Dec 2018 Crash", "description": "Christmas Eve crash — Fed hike fears + trade war", "expected_bias": "Bearish"},
    {"date": "2025-04-02", "category": "Global Shock", "sub_event": "Trump Liberation Day", "description": "Trump announces sweeping global tariffs — Liberation Day", "expected_bias": "Bearish"},
    {"date": "2008-11-26", "category": "Global Shock", "sub_event": "Terror Attack", "description": "26/11 Mumbai terror attacks", "expected_bias": "Bearish"},
    {"date": "2019-02-14", "category": "Global Shock", "sub_event": "Terror Attack", "description": "Pulwama terror attack — India-Pak tensions", "expected_bias": "Bearish"},
    {"date": "2019-09-14", "category": "Global Shock", "sub_event": "Oil Supply Shock", "description": "Saudi Aramco drone attack — oil spikes 15%", "expected_bias": "Bearish"},
    {"date": "2006-06-28", "category": "US Bonds", "sub_event": "Yield Curve Inversion", "description": "2Y-10Y inverts ahead of 2008 crisis", "expected_bias": "Bearish"},
    {"date": "2007-06-12", "category": "US Bonds", "sub_event": "Bond Yield Spike", "description": "US 10Y crosses 5.3% — pre-GFC peak", "expected_bias": "Bearish"},
    {"date": "2013-06-24", "category": "US Bonds", "sub_event": "Bond Yield Spike", "description": "US 10Y spikes to 2.6% — taper tantrum bond rout", "expected_bias": "Bearish"},
    {"date": "2016-07-06", "category": "US Bonds", "sub_event": "Bond Yield Drop", "description": "US 10Y hits 1.36% — all-time low, Brexit flight", "expected_bias": "Bullish"},
    {"date": "2020-03-09", "category": "US Bonds", "sub_event": "Bond Yield Drop", "description": "US 10Y crashes below 0.5% — COVID panic", "expected_bias": "Bullish"},
    {"date": "2021-03-18", "category": "US Bonds", "sub_event": "Bond Yield Spike", "description": "US 10Y crosses 1.7% — reflation trade", "expected_bias": "Bearish"},
    {"date": "2008-07-03", "category": "Oil/Commodity", "sub_event": "Oil Price Spike", "description": "Crude oil hits $147/barrel — all-time record", "expected_bias": "Bearish"},
    {"date": "2008-12-19", "category": "Oil/Commodity", "sub_event": "Oil Price Crash", "description": "Crude crashes to $32 from $147 — GFC demand collapse", "expected_bias": "Bullish"},
    {"date": "2014-11-27", "category": "Oil/Commodity", "sub_event": "Oil Price Crash", "description": "OPEC refuses to cut — oil crashes below $70", "expected_bias": "Bullish"},
    {"date": "2015-01-13", "category": "Oil/Commodity", "sub_event": "Oil Price Crash", "description": "Crude hits $45 — lowest since 2009", "expected_bias": "Bullish"},
    {"date": "2019-09-16", "category": "Oil/Commodity", "sub_event": "Oil Price Spike", "description": "Oil gaps up 15% — Saudi Aramco attack", "expected_bias": "Bearish"},
    {"date": "2020-11-09", "category": "Oil/Commodity", "sub_event": "Oil Price Spike", "description": "Crude rallies 10% on COVID vaccine news", "expected_bias": "Bullish"},
    {"date": "2013-11-12", "category": "India CPI", "sub_event": "India CPI High", "description": "India CPI at 11.24% — peak under Rajan", "expected_bias": "Bearish"},
    {"date": "2014-06-12", "category": "India CPI", "sub_event": "India CPI High", "description": "India CPI at 7.31% — food inflation", "expected_bias": "Bearish"},
    {"date": "2017-06-12", "category": "India CPI", "sub_event": "India CPI Low", "description": "India CPI drops to 1.54% — record low", "expected_bias": "Bullish"},
    {"date": "2019-10-14", "category": "India CPI", "sub_event": "India CPI High", "description": "India CPI at 4.62% — food prices surge", "expected_bias": "Bearish"},
    {"date": "2021-05-12", "category": "India CPI", "sub_event": "India CPI High", "description": "India CPI at 6.30% — COVID supply disruption", "expected_bias": "Bearish"},
    {"date": "2023-09-12", "category": "India CPI", "sub_event": "India CPI High", "description": "India CPI spikes to 6.83% — tomato crisis", "expected_bias": "Bearish"},
    {"date": "2008-07-16", "category": "US CPI", "sub_event": "CPI Surprise High", "description": "US CPI at 5.6% YoY — oil-driven inflation peak", "expected_bias": "Bearish"},
    {"date": "2009-07-15", "category": "US CPI", "sub_event": "CPI Below Estimate", "description": "US CPI at -2.1% YoY — deflation scare", "expected_bias": "Bullish"},
    {"date": "2020-04-10", "category": "US CPI", "sub_event": "CPI Below Estimate", "description": "US CPI crashes — COVID demand destruction", "expected_bias": "Neutral"},
    {"date": "2023-01-12", "category": "US CPI", "sub_event": "CPI Below Estimate", "description": "US CPI at 6.5% — downtrend confirmed", "expected_bias": "Bullish"},
    {"date": "2024-01-11", "category": "US CPI", "sub_event": "CPI Below Estimate", "description": "US CPI at 3.4% — soft landing narrative", "expected_bias": "Bullish"},
    {"date": "2008-01-01", "category": "FII Flows", "sub_event": "FII Massive Sell", "description": "FIIs sell ₹52,000cr in 2008 — worst year ever at that time", "expected_bias": "Bearish"},
    {"date": "2013-06-01", "category": "FII Flows", "sub_event": "FII Massive Sell", "description": "FIIs sell ₹44,000cr post taper tantrum — INR crashes", "expected_bias": "Bearish"},
    {"date": "2014-01-01", "category": "FII Flows", "sub_event": "FII Massive Buy", "description": "FIIs invest ₹97,000cr in 2014 — Modi rally", "expected_bias": "Bullish"},
    {"date": "2017-01-01", "category": "FII Flows", "sub_event": "FII Massive Buy", "description": "FIIs invest ₹48,000cr in H1 2017", "expected_bias": "Bullish"},
    {"date": "2019-01-01", "category": "FII Flows", "sub_event": "FII Massive Buy", "description": "FIIs invest ₹1.01L cr in 2019 — election year", "expected_bias": "Bullish"},
    {"date": "2008-10-17", "category": "Earnings Season", "sub_event": "IT Earnings Beat", "description": "Infosys Q2 FY09 beats despite GFC — resilience", "expected_bias": "Bullish"},
    {"date": "2016-01-12", "category": "Earnings Season", "sub_event": "IT Earnings Miss", "description": "TCS Q3 FY16 misses — growth concerns", "expected_bias": "Bearish"},
    {"date": "2018-01-12", "category": "Earnings Season", "sub_event": "IT Earnings Beat", "description": "TCS Q3 FY18 beats — digital revenue surges", "expected_bias": "Bullish"},
    {"date": "2019-01-11", "category": "Earnings Season", "sub_event": "IT Earnings Beat", "description": "TCS Q3 FY19 strong — deal pipeline robust", "expected_bias": "Bullish"},
    {"date": "2020-01-10", "category": "Earnings Season", "sub_event": "Bank Earnings Beat", "description": "HDFC Bank Q3 FY20 in-line — steady as always", "expected_bias": "Bullish"},
    {"date": "2021-04-17", "category": "Earnings Season", "sub_event": "Bank Earnings Beat", "description": "HDFC Bank Q4 FY21 beats — credit growth revival", "expected_bias": "Bullish"},
    {"date": "2023-04-14", "category": "Earnings Season", "sub_event": "IT Earnings Miss", "description": "TCS Q4 FY23 — weak guidance, deal slowdown", "expected_bias": "Bearish"},
    {"date": "2023-10-12", "category": "Earnings Season", "sub_event": "IT Earnings Miss", "description": "Infosys Q2 FY24 cuts guidance — AI disruption fears", "expected_bias": "Bearish"},
    {"date": "2008-10-28", "category": "Currency", "sub_event": "INR Crash", "description": "Rupee hits 50/$ for first time — GFC impact", "expected_bias": "Bearish"},
    {"date": "2011-12-15", "category": "Currency", "sub_event": "INR Crash", "description": "Rupee breaches 54/$ — euro crisis contagion", "expected_bias": "Bearish"},
    {"date": "2013-08-28", "category": "Currency", "sub_event": "INR Crash", "description": "Rupee crashes to 68.85/$ — taper tantrum + CAD crisis", "expected_bias": "Bearish"},
    {"date": "2016-11-24", "category": "Currency", "sub_event": "INR Crash", "description": "Rupee hits 68.7/$ — demonetization + Trump effect", "expected_bias": "Bearish"},
    {"date": "2020-04-22", "category": "Currency", "sub_event": "INR Crash", "description": "Rupee breaches 76.9/$ — COVID capital flight", "expected_bias": "Bearish"},
    {"date": "2004-05-17", "category": "IPO/Corporate", "sub_event": "Market Crash", "description": "Nifty crashes 17% — UPA win + FII panic (Black Monday)", "expected_bias": "Bearish"},
    {"date": "2008-01-21", "category": "IPO/Corporate", "sub_event": "Market Crash", "description": "Nifty crashes 10%+ — Global GFC panic Monday", "expected_bias": "Bearish"},
    {"date": "2009-03-09", "category": "IPO/Corporate", "sub_event": "Market Bottom", "description": "Global markets bottom — start of decade-long bull run", "expected_bias": "Bullish"},
    {"date": "2024-09-26", "category": "IPO/Corporate", "sub_event": "Market Peak", "description": "Nifty hits all-time high 26277 — before correction", "expected_bias": "Bearish"},
    {"date": "2008-09-05", "category": "US Jobs", "sub_event": "NFP Weak", "description": "US loses 84K jobs — recession confirmed", "expected_bias": "Bearish"},
    {"date": "2009-03-06", "category": "US Jobs", "sub_event": "NFP Weak", "description": "US loses 651K jobs — GFC employment peak decline", "expected_bias": "Bearish"},
    {"date": "2020-05-08", "category": "US Jobs", "sub_event": "NFP Weak", "description": "US loses 20.5M jobs in April — biggest drop in history", "expected_bias": "Bearish"},
    {"date": "2021-07-02", "category": "US Jobs", "sub_event": "NFP Strong", "description": "US adds 850K jobs — recovery accelerates", "expected_bias": "Neutral"},
    {"date": "2022-10-07", "category": "US Jobs", "sub_event": "NFP Strong", "description": "US adds 263K jobs — hot labor market, hawkish Fed", "expected_bias": "Bearish"},
]

# ============================================================
# UPCOMING EVENTS CALENDAR (2025-2026)
# Comprehensive recurring events
# ============================================================

UPCOMING_EVENTS_CALENDAR = [
    # RBI Policy Dates 2025 (Bi-monthly MPC)
    {"date": "2025-04-09", "category": "RBI Policy", "sub_event": "Policy Decision", "description": "RBI MPC Meeting April 2025", "historical_bias": "Bullish (dovish cycle)"},
    {"date": "2025-06-06", "category": "RBI Policy", "sub_event": "Policy Decision", "description": "RBI MPC Meeting June 2025", "historical_bias": "Neutral"},
    {"date": "2025-08-08", "category": "RBI Policy", "sub_event": "Policy Decision", "description": "RBI MPC Meeting August 2025", "historical_bias": "Neutral"},
    {"date": "2025-10-08", "category": "RBI Policy", "sub_event": "Policy Decision", "description": "RBI MPC Meeting October 2025", "historical_bias": "Neutral"},
    {"date": "2025-12-05", "category": "RBI Policy", "sub_event": "Policy Decision", "description": "RBI MPC Meeting December 2025", "historical_bias": "Neutral"},
    # RBI Policy 2026
    {"date": "2026-02-06", "category": "RBI Policy", "sub_event": "Policy Decision", "description": "RBI MPC Meeting February 2026", "historical_bias": "Neutral"},
    {"date": "2026-04-08", "category": "RBI Policy", "sub_event": "Policy Decision", "description": "RBI MPC Meeting April 2026", "historical_bias": "Neutral"},

    # US Fed FOMC Dates 2025-2026
    {"date": "2025-03-19", "category": "US Fed", "sub_event": "FOMC Decision", "description": "US Fed FOMC Rate Decision March 2025", "historical_bias": "Bearish"},
    {"date": "2025-05-07", "category": "US Fed", "sub_event": "FOMC Decision", "description": "US Fed FOMC Rate Decision May 2025", "historical_bias": "Neutral"},
    {"date": "2025-06-18", "category": "US Fed", "sub_event": "FOMC Decision", "description": "US Fed FOMC Rate Decision June 2025", "historical_bias": "Neutral"},
    {"date": "2025-07-30", "category": "US Fed", "sub_event": "FOMC Decision", "description": "US Fed FOMC Rate Decision July 2025", "historical_bias": "Neutral"},
    {"date": "2025-09-17", "category": "US Fed", "sub_event": "FOMC Decision", "description": "US Fed FOMC Rate Decision Sept 2025", "historical_bias": "Neutral"},
    {"date": "2025-10-29", "category": "US Fed", "sub_event": "FOMC Decision", "description": "US Fed FOMC Rate Decision Oct 2025", "historical_bias": "Neutral"},
    {"date": "2025-12-10", "category": "US Fed", "sub_event": "FOMC Decision", "description": "US Fed FOMC Rate Decision Dec 2025", "historical_bias": "Neutral"},
    {"date": "2026-01-28", "category": "US Fed", "sub_event": "FOMC Decision", "description": "US Fed FOMC Rate Decision Jan 2026", "historical_bias": "Neutral"},
    {"date": "2026-03-18", "category": "US Fed", "sub_event": "FOMC Decision", "description": "US Fed FOMC Rate Decision Mar 2026", "historical_bias": "Neutral"},

    # US CPI Release Dates 2025-2026 (approximate — usually 2nd Tue/Wed of month)
    {"date": "2025-03-12", "category": "US CPI", "sub_event": "CPI Data Release", "description": "US CPI February 2025 data release", "historical_bias": "Volatile"},
    {"date": "2025-04-10", "category": "US CPI", "sub_event": "CPI Data Release", "description": "US CPI March 2025 data release", "historical_bias": "Volatile"},
    {"date": "2025-05-13", "category": "US CPI", "sub_event": "CPI Data Release", "description": "US CPI April 2025 data release", "historical_bias": "Volatile"},
    {"date": "2025-06-11", "category": "US CPI", "sub_event": "CPI Data Release", "description": "US CPI May 2025 data release", "historical_bias": "Volatile"},

    # US Jobs / NFP (first Friday of month)
    {"date": "2025-03-07", "category": "US Jobs", "sub_event": "NFP Release", "description": "US Non-Farm Payrolls February 2025", "historical_bias": "Volatile"},
    {"date": "2025-04-04", "category": "US Jobs", "sub_event": "NFP Release", "description": "US Non-Farm Payrolls March 2025", "historical_bias": "Volatile"},
    {"date": "2025-05-02", "category": "US Jobs", "sub_event": "NFP Release", "description": "US Non-Farm Payrolls April 2025", "historical_bias": "Volatile"},
    {"date": "2025-06-06", "category": "US Jobs", "sub_event": "NFP Release", "description": "US Non-Farm Payrolls May 2025", "historical_bias": "Volatile"},

    # India Quarterly Results Season
    {"date": "2025-04-10", "category": "Earnings Season", "sub_event": "Q4 Results Start", "description": "Q4 FY25 Earnings Season Begins (TCS/Infy)", "historical_bias": "Volatile"},
    {"date": "2025-07-10", "category": "Earnings Season", "sub_event": "Q1 Results Start", "description": "Q1 FY26 Earnings Season Begins", "historical_bias": "Volatile"},
    {"date": "2025-10-10", "category": "Earnings Season", "sub_event": "Q2 Results Start", "description": "Q2 FY26 Earnings Season Begins", "historical_bias": "Volatile"},
    {"date": "2026-01-12", "category": "Earnings Season", "sub_event": "Q3 Results Start", "description": "Q3 FY26 Earnings Season Begins", "historical_bias": "Volatile"},

    # India Budget
    {"date": "2026-02-01", "category": "Union Budget", "sub_event": "Budget Day", "description": "Union Budget 2026-27 (Expected)", "historical_bias": "Volatile"},

    # India CPI (approx)
    {"date": "2025-03-12", "category": "India CPI", "sub_event": "India CPI Release", "description": "India CPI February 2025", "historical_bias": "Neutral"},
    {"date": "2025-04-14", "category": "India CPI", "sub_event": "India CPI Release", "description": "India CPI March 2025", "historical_bias": "Neutral"},

    # GST Council (quarterly)
    {"date": "2025-06-21", "category": "GST", "sub_event": "GST Council Meet", "description": "GST Council Meeting (Expected Q2 2025)", "historical_bias": "Neutral"},
    {"date": "2025-09-20", "category": "GST", "sub_event": "GST Council Meet", "description": "GST Council Meeting (Expected Q3 2025)", "historical_bias": "Neutral"},

    # State Elections (expected, approximate)
    {"date": "2025-11-15", "category": "Elections", "sub_event": "State Election Result", "description": "Bihar State Election Results 2025 (Expected)", "historical_bias": "Volatile"},
]

# Event category descriptions for UI
EVENT_CATEGORY_INFO = {
    "Rate Cut": {"emoji": "📉", "color": "green", "desc": "RBI reduces repo rate — boosts liquidity"},
    "Rate Hike": {"emoji": "📈", "color": "red", "desc": "RBI raises repo rate — tightens liquidity"},
    "Rate Hold": {"emoji": "⏸️", "color": "yellow", "desc": "RBI keeps rate unchanged"},
    "Budget Day": {"emoji": "📋", "color": "purple", "desc": "Union Budget announcement"},
    "Fed Rate Hike": {"emoji": "🇺🇸📈", "color": "red", "desc": "US Federal Reserve rate increase"},
    "Fed Rate Cut": {"emoji": "🇺🇸📉", "color": "green", "desc": "US Federal Reserve rate cut"},
    "General Election Result": {"emoji": "🗳️", "color": "blue", "desc": "India General Election result"},
    "State Election Result": {"emoji": "🗳️", "color": "blue", "desc": "India State Election result"},
    "US Presidential Result": {"emoji": "🇺🇸🗳️", "color": "blue", "desc": "US Presidential Election result"},
    "Bond Yield Spike": {"emoji": "📊", "color": "red", "desc": "US Treasury 10Y yield spikes — equity selloff"},
    "Yield Curve Inversion": {"emoji": "⚠️", "color": "red", "desc": "2Y-10Y yield curve inverts — recession signal"},
    "Bond Yield Drop": {"emoji": "📊", "color": "green", "desc": "US Treasury yields drop — risk-on sentiment"},
    "CPI Surprise High": {"emoji": "🔥", "color": "red", "desc": "US inflation higher than expected"},
    "CPI Below Estimate": {"emoji": "❄️", "color": "green", "desc": "US inflation lower than expected"},
    "NFP Strong": {"emoji": "💼", "color": "red", "desc": "Strong US jobs — hawkish Fed risk"},
    "NFP Weak": {"emoji": "💼", "color": "green", "desc": "Weak US jobs — dovish Fed hope"},
    "Oil Price Spike": {"emoji": "🛢️📈", "color": "red", "desc": "Oil price surge — inflation risk for India"},
    "Oil Price Crash": {"emoji": "🛢️📉", "color": "green", "desc": "Oil price crash — good for India's CAD"},
    "Oil Price Drop": {"emoji": "🛢️📉", "color": "green", "desc": "Oil price decline — positive for India"},
    "GST Launch": {"emoji": "🏛️", "color": "purple", "desc": "GST system launch"},
    "GST Rate Cut": {"emoji": "🏛️📉", "color": "green", "desc": "GST rates reduced on items"},
    "GST Rate Hike": {"emoji": "🏛️📈", "color": "red", "desc": "GST rates increased on items"},
    "India CPI High": {"emoji": "🇮🇳🔥", "color": "red", "desc": "India inflation exceeds RBI tolerance band"},
    "India CPI Low": {"emoji": "🇮🇳❄️", "color": "green", "desc": "India inflation within comfortable range"},
    "FII Massive Sell": {"emoji": "💸", "color": "red", "desc": "Foreign investors sell heavily"},
    "FII Massive Buy": {"emoji": "💰", "color": "green", "desc": "Foreign investors buy heavily"},
    "IT Earnings Beat": {"emoji": "💻✅", "color": "green", "desc": "IT sector earnings beat expectations"},
    "IT Earnings Miss": {"emoji": "💻❌", "color": "red", "desc": "IT sector earnings disappoint"},
    "Bank Earnings Beat": {"emoji": "🏦✅", "color": "green", "desc": "Banking sector earnings beat"},
    "Bank Earnings Miss": {"emoji": "🏦❌", "color": "red", "desc": "Banking sector earnings miss"},
    "COVID Crash": {"emoji": "🦠", "color": "red", "desc": "COVID pandemic impact"},
    "COVID Bottom": {"emoji": "🦠📈", "color": "green", "desc": "COVID market bottom — recovery begins"},
    "Demonetization": {"emoji": "💵❌", "color": "red", "desc": "Currency demonetization shock"},
    "INR Crash": {"emoji": "₹📉", "color": "red", "desc": "Indian Rupee hits new low"},
    "Major IPO": {"emoji": "🆕", "color": "purple", "desc": "Major IPO listing"},
    "Adani Crisis": {"emoji": "⚠️", "color": "red", "desc": "Adani Group crisis"},
    "Terror Attack": {"emoji": "💥", "color": "red", "desc": "Terror attack — geopolitical shock"},
    "Lehman Collapse": {"emoji": "🏦💥", "color": "red", "desc": "Lehman Brothers bankruptcy — GFC trigger"},
    "GFC Bottom": {"emoji": "📈", "color": "green", "desc": "Global Financial Crisis market bottom"},
    "Flash Crash": {"emoji": "⚡", "color": "red", "desc": "Market flash crash event"},
    "US Downgrade": {"emoji": "🇺🇸⬇️", "color": "red", "desc": "US credit rating downgrade"},
    "Taper Tantrum": {"emoji": "📉", "color": "red", "desc": "Fed taper announcement — EM selloff"},
    "China Devaluation": {"emoji": "🇨🇳", "color": "red", "desc": "China yuan devaluation shock"},
    "Volmageddon": {"emoji": "🌋", "color": "red", "desc": "Volatility blowup — VIX spike"},
    "Dec 2018 Crash": {"emoji": "🎄📉", "color": "red", "desc": "December 2018 market crash"},
    "China Crash": {"emoji": "🇨🇳📉", "color": "red", "desc": "China stock market crash"},
    "Oil Supply Shock": {"emoji": "🛢️⚡", "color": "red", "desc": "Oil supply disruption"},
    "Trump Liberation Day": {"emoji": "🇺🇸📉", "color": "red", "desc": "Trump sweeping tariff announcement"},
    "Market Crash": {"emoji": "📉💥", "color": "red", "desc": "Major market crash event"},
    "Market Bottom": {"emoji": "📈🟢", "color": "green", "desc": "Market bottom — recovery starts"},
    "Market Peak": {"emoji": "📈🔴", "color": "red", "desc": "Market hits all-time high before correction"},
}


class EconomicEventsEngine:
    """Provides historical economic event backtesting and upcoming event alerts."""

    def get_historical_events(self, category: Optional[str] = None) -> List[Dict]:
        """Return all historical events, optionally filtered by category."""
        events = HISTORICAL_EVENTS
        if category:
            events = [e for e in events if e["category"] == category or e["sub_event"] == category]
        return events

    def get_upcoming_events(self, days_ahead: int = 14) -> List[Dict]:
        """Return scheduled events within the next N days."""
        today = datetime.now().date()
        cutoff = today + timedelta(days=days_ahead)

        upcoming = []
        for event in UPCOMING_EVENTS_CALENDAR:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
            if today <= event_date <= cutoff:
                days_away = (event_date - today).days
                info = EVENT_CATEGORY_INFO.get(event.get("sub_event", ""), {})
                upcoming.append({
                    **event,
                    "days_away": days_away,
                    "urgency": "imminent" if days_away <= 2 else "soon" if days_away <= 5 else "upcoming",
                    "emoji": info.get("emoji", "📅"),
                    "color": info.get("color", "slate"),
                })

        # Sort by nearest first
        upcoming.sort(key=lambda x: x["days_away"])
        return upcoming

    def get_event_categories(self) -> List[Dict]:
        """Return unique sub-event categories available for backtesting with metadata."""
        categories = {}
        for e in HISTORICAL_EVENTS:
            sub = e["sub_event"]
            if sub not in categories:
                info = EVENT_CATEGORY_INFO.get(sub, {})
                categories[sub] = {
                    "sub_event": sub,
                    "category": e["category"],
                    "count": 0,
                    "emoji": info.get("emoji", "📅"),
                    "color": info.get("color", "slate"),
                    "desc": info.get("desc", ""),
                }
            categories[sub]["count"] += 1
        return sorted(categories.values(), key=lambda x: (-x["count"], x["sub_event"]))

    def get_events_in_window(self, days_ahead: int = 14) -> List[Dict]:
        """Get events impacting the next N days — for forecast integration."""
        upcoming = self.get_upcoming_events(days_ahead=days_ahead)
        # Also check historical events on same calendar dates (anniversary alerts)
        today = datetime.now()
        alerts = list(upcoming)

        for event in HISTORICAL_EVENTS:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d")
            # Check if the anniversary falls within the window
            try:
                anniversary = event_date.replace(year=today.year)
            except ValueError:
                # e.g. Feb 29 in a non-leap year — skip
                continue
            days_to_anni = (anniversary.date() - today.date()).days
            if 0 <= days_to_anni <= days_ahead:
                alerts.append({
                    "date": anniversary.strftime("%Y-%m-%d"),
                    "category": event["category"],
                    "sub_event": event["sub_event"],
                    "description": f"Anniversary: {event['description']}",
                    "days_away": days_to_anni,
                    "urgency": "info",
                    "is_anniversary": True,
                    "original_bias": event["expected_bias"],
                })

        alerts.sort(key=lambda x: x.get("days_away", 999))
        return alerts


    def backtest_event_category(self, sub_event: str, symbol: str = "^NSEI", window_days: int = 5) -> Dict:
        """
        Backtest market reaction to a specific event sub-category.
        Measures same-day, T+1, T+3, T+5 returns for each historical occurrence.
        """
        # Filter events
        events = [e for e in HISTORICAL_EVENTS if e["sub_event"] == sub_event]
        if not events:
            return {"error": f"No historical events found for '{sub_event}'."}

        # Fetch market data via Kite-first pipeline (falls back to yfinance)
        earliest_date = min(e["date"] for e in events)
        start = (datetime.strptime(earliest_date, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")

        try:
            fetcher = MarketDataFetcher()
            raw_df = fetcher.fetch_stock_data(symbol, start_date=start)
        except Exception as e:
            return {"error": f"Failed to fetch market data: {e}"}

        if raw_df is None or raw_df.empty:
            return {"error": "No market data available."}

        # Normalize to expected format (Close column, DatetimeIndex)
        hist = raw_df.copy()
        # Ensure we have a 'Close' column (MarketDataFetcher uses lowercase)
        if 'close' in hist.columns and 'Close' not in hist.columns:
            hist = hist.rename(columns={'close': 'Close', 'open': 'Open', 'high': 'High', 'low': 'Low', 'volume': 'Volume'})
        if 'date' in hist.columns:
            hist.index = pd.to_datetime(hist['date'])
        hist.index = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index
        hist['daily_return'] = hist['Close'].pct_change() * 100 if 'daily_return' not in hist.columns else hist['daily_return']

        results = []
        for event in events:
            event_date = pd.Timestamp(event["date"])

            # Find the nearest trading day (event day or next trading day)
            valid_dates = hist.index[hist.index >= event_date]
            if valid_dates.empty:
                continue
            nearest_trading = valid_dates[0]
            idx = hist.index.get_loc(nearest_trading)

            # Same-day return
            same_day = hist['daily_return'].iloc[idx] if idx < len(hist) else None

            # Forward returns
            def get_forward_return(offset):
                target_idx = idx + offset
                if target_idx < len(hist) and idx < len(hist):
                    return ((hist['Close'].iloc[target_idx] / hist['Close'].iloc[idx]) - 1) * 100
                return None

            t1 = get_forward_return(1)
            t3 = get_forward_return(3)
            t5 = get_forward_return(5)

            sd = _safe_round(same_day)
            direction = "Up" if sd and sd > 0 else "Down" if sd and sd < 0 else "Flat"

            results.append({
                "date": event["date"],
                "description": event["description"],
                "expected_bias": event["expected_bias"],
                "same_day_return": sd,
                "t1_return": _safe_round(t1),
                "t3_return": _safe_round(t3),
                "t5_return": _safe_round(t5),
                "direction": direction,
            })

        if not results:
            return {"error": "Could not match any events with market data."}

        # Aggregate statistics
        same_day_returns = [r["same_day_return"] for r in results if r["same_day_return"] is not None]
        t5_returns = [r["t5_return"] for r in results if r["t5_return"] is not None]

        up_count = sum(1 for r in same_day_returns if r > 0)
        down_count = sum(1 for r in same_day_returns if r < 0)
        total = len(same_day_returns)

        # Average T+1 and T+3
        t1_returns = [r["t1_return"] for r in results if r["t1_return"] is not None]
        t3_returns = [r["t3_return"] for r in results if r["t3_return"] is not None]

        stats = {
            "total_events": total,
            "up_count": up_count,
            "down_count": down_count,
            "win_rate": _safe_round((up_count / total * 100), 1) if total > 0 else 0,
            "avg_same_day": _safe_round(sum(same_day_returns) / total) if total > 0 else 0,
            "avg_t1_return": _safe_round(sum(t1_returns) / len(t1_returns)) if t1_returns else 0,
            "avg_t3_return": _safe_round(sum(t3_returns) / len(t3_returns)) if t3_returns else 0,
            "avg_t5_return": _safe_round(sum(t5_returns) / len(t5_returns)) if t5_returns else 0,
            "max_gain": _safe_round(max(same_day_returns)) if same_day_returns else 0,
            "max_loss": _safe_round(min(same_day_returns)) if same_day_returns else 0,
            "bias": "Bullish" if up_count > down_count else "Bearish" if down_count > up_count else "Neutral",
        }

        # Category info
        info = EVENT_CATEGORY_INFO.get(sub_event, {})

        # Next scheduled occurrence
        next_occurrence = None
        today = datetime.now().date()
        for ev in UPCOMING_EVENTS_CALENDAR:
            ev_date = datetime.strptime(ev["date"], "%Y-%m-%d").date()
            if ev.get("sub_event", "").startswith(sub_event.split(" ")[0]) or ev.get("category") == events[0].get("category"):
                if ev_date > today:
                    next_occurrence = {
                        "date": ev["date"],
                        "description": ev["description"],
                        "days_away": (ev_date - today).days,
                    }
                    break

        return {
            "sub_event": sub_event,
            "symbol": symbol,
            "emoji": info.get("emoji", "📅"),
            "desc": info.get("desc", ""),
            "stats": stats,
            "events": results,
            "next_occurrence": next_occurrence,
        }
