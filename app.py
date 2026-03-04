"""
Astro-Finance: Nakshatra Stock Market Analysis System
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pytz
import numpy as np

from config import (
    PAGE_CONFIG, APP_TITLE, APP_SUBTITLE,
    PLANET_COLORS, ELEMENT_COLORS, GANA_COLORS, DIRECTION_COLORS,
    DEFAULT_START_DATE
)
from modules.moon_calculator import MoonCalculator
from modules.market_data import MarketDataFetcher
from modules.analysis_engine import NakshatraAnalyzer
from modules.astro_correlation import AstroCorrelationEngine
from modules.nakshatra_database import get_all_nakshatras, get_nakshatra_by_number

IST = pytz.timezone('Asia/Kolkata')

# ─── Page Config ────────────────────────────────────────────────────
st.set_page_config(**PAGE_CONFIG)

# ─── Custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .main { font-family: 'Inter', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%);
    }

    .hero-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }

    .hero-card h1 { font-size: 2.2rem; margin-bottom: 4px; }
    .hero-card p { font-size: 1rem; opacity: 0.9; }

    .metric-card {
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); }
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card .label {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.6);
        margin-top: 4px;
    }

    .nakshatra-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin: 2px;
    }
    .badge-bullish { background: rgba(0,200,83,0.15); color: #00C853; border: 1px solid rgba(0,200,83,0.3); }
    .badge-bearish { background: rgba(255,23,68,0.15); color: #FF1744; border: 1px solid rgba(255,23,68,0.3); }
    .badge-neutral { background: rgba(158,158,158,0.15); color: #9E9E9E; border: 1px solid rgba(158,158,158,0.3); }

    .insight-box {
        background: rgba(255,255,255,0.05);
        border-left: 4px solid #667eea;
        border-radius: 0 8px 8px 0;
        padding: 16px;
        margin: 12px 0;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a3e 0%, #0f0c29 100%);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)


# ─── Session State ──────────────────────────────────────────────────
if 'merged_data' not in st.session_state:
    st.session_state.merged_data = None
if 'summary_data' not in st.session_state:
    st.session_state.summary_data = None
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False


# ─── Initialize modules ────────────────────────────────────────────
@st.cache_resource
def get_moon_calculator():
    return MoonCalculator()

@st.cache_resource
def get_analyzer():
    return NakshatraAnalyzer()

@st.cache_resource
def get_correlation_engine():
    return AstroCorrelationEngine()


moon_calc = get_moon_calculator()
analyzer = get_analyzer()
corr_engine = get_correlation_engine()


# ─── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌙 Astro-Finance")
    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigate",
        ["🏠 Dashboard", "📊 Nakshatra Analysis", "🔬 Statistical Tests",
         "🌌 Astro-Correlation", "🪐 Planet Analysis", "📖 Nakshatra Encyclopedia", "⚙️ Settings"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Quick current nakshatra
    try:
        current = moon_calc.get_current_nakshatra()
        st.markdown("### 🌙 Current Moon Position")
        st.markdown(f"**{current['nakshatra_name']}** ({current['nakshatra_sanskrit']})")
        st.markdown(f"Pada: **{current['pada']}** | {current['ruling_planet']}")
        st.markdown(f"Sidereal: **{current['moon_longitude_sidereal']:.2f}°**")

        tendency = current.get('historical_market_tendency', 'Neutral')
        badge_class = 'badge-bullish' if tendency == 'Bullish' else (
            'badge-bearish' if tendency == 'Bearish' else 'badge-neutral'
        )
        st.markdown(
            f'<span class="nakshatra-badge {badge_class}">{tendency}</span>',
            unsafe_allow_html=True
        )
    except Exception as e:
        st.warning(f"Moon calculation: {e}")

    st.markdown("---")
    st.caption("© 2026 Astro-Finance | Nakshatra Market Analysis")


# ═══════════════════════════════════════════════════════════════
# PAGE: Dashboard
# ═══════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    # Hero section
    st.markdown(f"""
    <div class="hero-card">
        <h1>{APP_TITLE}</h1>
        <p>{APP_SUBTITLE}</p>
        <p style="opacity:0.7; font-size:0.85rem;">
            Correlating Moon's journey through 27 Vedic Nakshatras with NSE market movements
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Today's Insight
    try:
        insight = analyzer.generate_today_insight()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="value">{insight['current_nakshatra']}</div>
                <div class="label">Current Nakshatra</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="value">Pada {insight['pada']}</div>
                <div class="label">{insight['ruling_planet']}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="value">{insight['moon_longitude']:.1f}°</div>
                <div class="label">Sidereal Longitude</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            tendency = insight['historical_tendency']
            color = '#00C853' if tendency == 'Bullish' else '#FF1744' if tendency == 'Bearish' else '#FFA500'
            st.markdown(f"""
            <div class="metric-card">
                <div class="value" style="background:none;-webkit-text-fill-color:{color};">{tendency}</div>
                <div class="label">Historical Tendency</div>
            </div>
            """, unsafe_allow_html=True)

        # Financial traits
        st.markdown("### 💡 Today's Trading Insight")
        st.markdown(f"""
        <div class="insight-box">
            <strong>✅ Favorable for:</strong> {', '.join(insight['favorable_for'])}<br>
            <strong>❌ Unfavorable for:</strong> {', '.join(insight['unfavorable_for'])}<br>
            <strong>🎯 Financial Traits:</strong> {', '.join(insight['financial_traits'])}<br>
            <strong>🎨 Lucky Colors:</strong> {', '.join(insight['lucky_colors'])} |
            <strong>🔢 Lucky Numbers:</strong> {', '.join(map(str, insight['lucky_numbers']))}
        </div>
        """, unsafe_allow_html=True)

        if insight.get('transition'):
            t = insight['transition']
            st.info(f"🔄 **Nakshatra Transition Today:** {t['from_nakshatra']} → {t['to_nakshatra']} at {t['transition_time']}")

    except Exception as e:
        st.error(f"Error generating insight: {e}")

    # Data Loading Section
    st.markdown("---")
    st.markdown("### 📥 Load Analysis Data")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        start_date = st.date_input("Start Date", value=datetime(2020, 1, 1))
    with col_b:
        end_date = st.date_input("End Date", value=datetime.now())
    with col_c:
        symbol = st.selectbox("Market Index", ["^NSEI (NIFTY 50)", "^NSEBANK (Bank NIFTY)"])
        symbol_code = symbol.split(" ")[0]

    if st.button("🚀 Load & Analyze Data", type="primary", use_container_width=True):
        with st.spinner("Fetching market data and calculating Nakshatras..."):
            merged = analyzer.build_merged_dataset(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                symbol=symbol_code
            )

            if not merged.empty:
                st.session_state.merged_data = merged
                summary = analyzer.nakshatra_performance_summary(merged)
                st.session_state.summary_data = summary
                st.session_state.analysis_done = True
                st.success(f"✅ Loaded {len(merged)} trading days with Nakshatra data!")
            else:
                st.error("❌ Could not fetch data. Please check your internet connection.")

    # Show quick stats if data is loaded
    if st.session_state.analysis_done and st.session_state.summary_data is not None:
        summary = st.session_state.summary_data
        merged = st.session_state.merged_data

        st.markdown("### 📊 Quick Overview")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Trading Days", f"{len(merged):,}")
        c2.metric("Avg Daily Return", f"{merged['daily_return'].mean():.4f}%")
        c3.metric("Best Nakshatra", summary.iloc[0]['nakshatra_name'])
        c4.metric("Worst Nakshatra", summary.iloc[-1]['nakshatra_name'])

        # Quick chart - mean returns by nakshatra
        fig = px.bar(
            summary.sort_values('nakshatra_number'),
            x='nakshatra_name',
            y='mean_return',
            color='mean_return',
            color_continuous_scale=['#FF1744', '#FFD700', '#00C853'],
            title="Average Daily Return by Nakshatra",
            labels={'mean_return': 'Mean Return (%)', 'nakshatra_name': 'Nakshatra'}
        )
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_tickangle=-45,
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# PAGE: Nakshatra Analysis
# ═══════════════════════════════════════════════════════════════
elif page == "📊 Nakshatra Analysis":
    st.markdown("## 📊 Nakshatra Performance Analysis")

    if not st.session_state.analysis_done:
        st.warning("⚠️ Please load data from the Dashboard first.")
        st.stop()

    summary = st.session_state.summary_data
    merged = st.session_state.merged_data

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Performance Table", "📊 Charts", "🏆 Rankings", "🔍 Deep Dive"])

    with tab1:
        st.markdown("### Nakshatra Performance Summary")
        display_cols = [
            'nakshatra_name', 'nakshatra_sanskrit', 'ruling_planet',
            'trading_days', 'mean_return', 'median_return', 'std_dev',
            'win_rate', 'bullish_days', 'bearish_days',
            'avg_gain', 'avg_loss', 'cumulative_return'
        ]
        st.dataframe(
            summary[display_cols].style.background_gradient(
                cmap='RdYlGn', subset=['mean_return', 'win_rate', 'cumulative_return']
            ),
            use_container_width=True,
            height=700
        )

    with tab2:
        chart_type = st.selectbox("Select Chart", [
            "Mean Return by Nakshatra",
            "Win Rate by Nakshatra",
            "Volatility (Std Dev) by Nakshatra",
            "Cumulative Return by Nakshatra",
            "Return Distribution Heatmap",
        ])

        sorted_summary = summary.sort_values('nakshatra_number')

        if chart_type == "Mean Return by Nakshatra":
            fig = go.Figure()
            colors = ['#00C853' if v > 0 else '#FF1744' for v in sorted_summary['mean_return']]
            fig.add_trace(go.Bar(
                x=sorted_summary['nakshatra_name'],
                y=sorted_summary['mean_return'],
                marker_color=colors,
                text=sorted_summary['mean_return'].round(4),
                textposition='outside'
            ))
            fig.update_layout(
                title="Average Daily Return by Nakshatra",
                yaxis_title="Mean Return (%)",
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=500,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Win Rate by Nakshatra":
            fig = px.bar(
                sorted_summary, x='nakshatra_name', y='win_rate',
                color='win_rate',
                color_continuous_scale=['#FF1744', '#FFD700', '#00C853'],
                title="Win Rate by Nakshatra (%)",
                text='win_rate'
            )
            fig.add_hline(y=50, line_dash="dash", line_color="white", opacity=0.5,
                         annotation_text="50% baseline")
            fig.update_layout(
                template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', height=500, xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Volatility (Std Dev) by Nakshatra":
            fig = px.bar(
                sorted_summary, x='nakshatra_name', y='std_dev',
                color='std_dev',
                color_continuous_scale=['#00C853', '#FFD700', '#FF1744'],
                title="Volatility (Std Dev of Returns) by Nakshatra",
            )
            fig.update_layout(
                template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', height=500, xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Cumulative Return by Nakshatra":
            fig = go.Figure()
            colors = ['#00C853' if v > 0 else '#FF1744' for v in sorted_summary['cumulative_return']]
            fig.add_trace(go.Bar(
                x=sorted_summary['nakshatra_name'],
                y=sorted_summary['cumulative_return'],
                marker_color=colors,
            ))
            fig.update_layout(
                title="Cumulative Return by Nakshatra",
                yaxis_title="Cumulative Return (%)",
                template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', height=500, xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Return Distribution Heatmap":
            # Heatmap: Nakshatra vs Day of Week
            heatmap_data = merged.pivot_table(
                values='daily_return', index='nakshatra_name',
                columns='day_of_week', aggfunc='mean'
            )
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            heatmap_data = heatmap_data.reindex(columns=day_order)

            fig = px.imshow(
                heatmap_data,
                color_continuous_scale='RdYlGn',
                title="Mean Return: Nakshatra × Day of Week",
                labels={'color': 'Mean Return (%)'},
                aspect='auto'
            )
            fig.update_layout(
                template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', height=700,
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### 🏆 Top Performing Nakshatras")
        top5 = summary.nlargest(5, 'mean_return')
        for i, row in top5.iterrows():
            st.markdown(f"""
            <div class="insight-box">
                <strong>#{top5.index.get_loc(i)+1} {row['nakshatra_name']}</strong>
                ({row['nakshatra_sanskrit']}) |
                Mean Return: <span style="color:#00C853">{row['mean_return']:.4f}%</span> |
                Win Rate: {row['win_rate']}% |
                {row['ruling_planet']}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📉 Bottom Performing Nakshatras")
        bottom5 = summary.nsmallest(5, 'mean_return')
        for i, row in bottom5.iterrows():
            st.markdown(f"""
            <div class="insight-box" style="border-left-color: #FF1744;">
                <strong>#{bottom5.index.get_loc(i)+1} {row['nakshatra_name']}</strong>
                ({row['nakshatra_sanskrit']}) |
                Mean Return: <span style="color:#FF1744">{row['mean_return']:.4f}%</span> |
                Win Rate: {row['win_rate']}% |
                {row['ruling_planet']}
            </div>
            """, unsafe_allow_html=True)

    with tab4:
        st.markdown("### 🔍 Deep Dive into a Nakshatra")
        all_naks = get_all_nakshatras()
        nak_names = [f"{n['number']}. {n['name_english']} ({n['name_sanskrit']})" for n in all_naks]
        selected_nak = st.selectbox("Select Nakshatra", nak_names)
        nak_num = int(selected_nak.split('.')[0])

        nak_data = merged[merged['nakshatra_number'] == nak_num]
        nak_info = get_nakshatra_by_number(nak_num)

        if len(nak_data) > 0:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Trading Days", len(nak_data))
            returns = nak_data['daily_return'].dropna()
            c2.metric("Mean Return", f"{returns.mean():.4f}%")
            c3.metric("Win Rate", f"{(returns > 0).sum()/len(returns)*100:.1f}%")
            c4.metric("Volatility", f"{returns.std():.4f}%")

            # Return distribution
            fig = px.histogram(
                nak_data, x='daily_return', nbins=50,
                title=f"Return Distribution – {nak_info['name_english']}",
                color_discrete_sequence=['#667eea'],
            )
            fig.add_vline(x=0, line_dash="dash", line_color="white")
            fig.add_vline(x=returns.mean(), line_dash="dot", line_color="#FFD700",
                         annotation_text=f"Mean: {returns.mean():.4f}%")
            fig.update_layout(
                template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Properties
            st.markdown(f"""
            **Ruling Planet:** {nak_info['ruling_planet']} |
            **Ruling Deity:** {nak_info['ruling_deity']} |
            **Element:** {nak_info['element']} |
            **Gana:** {nak_info['gana']}

            **Western Star:** {nak_info['star_name_western']} ({nak_info['common_name_western']})
            """)
        else:
            st.info("No trading days found for this Nakshatra in the loaded data range.")


# ═══════════════════════════════════════════════════════════════
# PAGE: Statistical Tests
# ═══════════════════════════════════════════════════════════════
elif page == "🔬 Statistical Tests":
    st.markdown("## 🔬 Statistical Significance Tests")

    if not st.session_state.analysis_done:
        st.warning("⚠️ Please load data from the Dashboard first.")
        st.stop()

    merged = st.session_state.merged_data

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ANOVA Test")
        st.markdown("*Are mean returns significantly different across Nakshatras?*")

        anova = analyzer.run_anova_test(merged)
        if "error" not in anova:
            color = "#00C853" if anova['result'] == "Significant" else "#FF1744"
            st.markdown(f"""
            <div class="metric-card">
                <div class="value" style="background:none;-webkit-text-fill-color:{color};">{anova['result']}</div>
                <div class="label">p = {anova['p_value']:.6f}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            - **F-Statistic:** {anova['f_statistic']:.4f}
            - **p-value:** {anova['p_value']:.6f}
            - **Groups:** {anova['num_groups']}
            - **Observations:** {anova['total_observations']:,}
            """)

            st.markdown(f"""
            <div class="insight-box">
                {anova['interpretation']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(anova["error"])

    with col2:
        st.markdown("### Chi-Square Test")
        st.markdown("*Is market direction independent of Nakshatra?*")

        chi2 = analyzer.run_chi_square_test(merged)
        if "error" not in chi2:
            color = "#00C853" if chi2['result'] == "Significant" else "#FF1744"
            st.markdown(f"""
            <div class="metric-card">
                <div class="value" style="background:none;-webkit-text-fill-color:{color};">{chi2['result']}</div>
                <div class="label">p = {chi2['p_value']:.6f}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            - **χ² Statistic:** {chi2['chi_square_statistic']:.4f}
            - **p-value:** {chi2['p_value']:.6f}
            - **Degrees of Freedom:** {chi2['degrees_of_freedom']}
            """)

            st.markdown(f"""
            <div class="insight-box">
                {chi2['interpretation']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(chi2["error"])


# ═══════════════════════════════════════════════════════════════
# PAGE: Astro-Correlation
# ═══════════════════════════════════════════════════════════════
elif page == "🌌 Astro-Correlation":
    st.markdown("## 🌌 Advanced Astro-Correlation Engine")
    st.markdown("Quantitatively prove the statistical impact of planetary events on market sectors.")
    
    tab1, tab2 = st.tabs(["📊 Event Backtesting", "🌡️ Sector Heatmaps"])
    
    with tab1:
        st.markdown("### Test Planetary Events")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
             symbol_input = st.selectbox("Symbol", ["^NSEI", "^NSEBANK", "^CNXIT", "RELIANCE.NS", "TCS.NS"])
        with col2:
             planet_input = st.selectbox("Planet", ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"])
        with col3:
             event_input = st.selectbox("Event Type", ["Retrograde", "Direct", "High Speed"])
        with col4:
             years_input = st.number_input("Lookback Years", min_value=1, max_value=20, value=10)
             
        if st.button("Run Astro-Backtest", use_container_width=True):
             with st.spinner(f"Backtesting {planet_input} {event_input} on {symbol_input}..."):
                  res = corr_engine.backtest_event(symbol_input, planet_input, event_input, years=years_input)
                  
                  if "error" in res:
                       st.error(res["error"])
                  else:
                       stats = res['stats']
                       
                       # Header
                       color = "#00C853" if stats['is_significant'] else "#FFA500"
                       sig_text = "Statistically Significant" if stats['is_significant'] else "Not Significant"
                       st.markdown(f"""
                       <div class="metric-card" style="margin-bottom: 20px;">
                           <div class="value" style="background:none;-webkit-text-fill-color:{color};">{sig_text}</div>
                           <div class="label">p-value: {stats['p_value']:.4f}</div>
                       </div>
                       """, unsafe_allow_html=True)
                       
                       # Comparison Metrics
                       c1, c2 = st.columns(2)
                       with c1:
                           st.markdown(f"#### During {planet_input} {event_input}")
                           st.metric("Average Daily Return", f"{stats['event_mean_return']:.3f}%")
                           st.metric("Win Rate", f"{stats['event_win_rate']:.1f}%")
                           st.caption(f"Sample Size: {stats['event_days']} days")
                           
                       with c2:
                           st.markdown(f"#### Normal Days")
                           st.metric("Average Daily Return", f"{stats['normal_mean_return']:.3f}%")
                           st.metric("Win Rate", f"{stats['normal_win_rate']:.1f}%")
                           st.caption(f"Sample Size: {stats['normal_days']} days")
                           
                       st.info(stats['interpretation'])
                       
    with tab2:
        st.markdown("### Planet-to-Sector Correlation")
        st.write("Generate a Pearson correlation matrix showing exactly which planetary speeds align with which asset classes.")
        
        heatmap_years = st.slider("Correlation Window (Years)", 1, 10, 5)
        
        if st.button("Generate Heatmap Array", use_container_width=True):
             with st.spinner("Generating Matrix..."):
                 symbols_to_test = ["^NSEI", "^NSEBANK", "^CNXIT", "RELIANCE.NS", "HDFCBANK.NS"]
                 planets_to_test = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
                 
                 h_res = corr_engine.generate_correlation_heatmap(symbols_to_test, planets_to_test, years=heatmap_years)
                 
                 if "error" in h_res:
                     st.error(h_res["error"])
                 else:
                     matrix = h_res["matrix"]
                     # Convert to dataframe
                     df_corr = pd.DataFrame(matrix).T
                     
                     fig = px.imshow(
                          df_corr,
                          color_continuous_scale='RdBu_r',
                          zmin=-0.1, zmax=0.1, # Correlations to daily speeds are small but notable
                          title=f"Planetary Speed vs Sector Returns ({h_res['period']})",
                          labels={'color': 'Pearson r'},
                          aspect='auto',
                          text_auto='.3f'
                     )
                     fig.update_layout(
                          template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)',
                          paper_bgcolor='rgba(0,0,0,0)', height=500
                     )
                     st.plotly_chart(fig, use_container_width=True)
                     
                     st.caption("*Values represent the Pearson correlation coefficient between the daily orbital speed of the planet and the daily return of the underlying asset. Negative values on Mercury/Venus often imply Retrograde (negative speed) pushes the asset up.*")

# ═══════════════════════════════════════════════════════════════
# PAGE: Planet Analysis
# ═══════════════════════════════════════════════════════════════
elif page == "🪐 Planet Analysis":
    st.markdown("## 🪐 Ruling Planet & Element Analysis")

    if not st.session_state.analysis_done:
        st.warning("⚠️ Please load data from the Dashboard first.")
        st.stop()

    merged = st.session_state.merged_data

    tab1, tab2, tab3 = st.tabs(["🪐 By Planet", "🔥 By Element", "👥 By Gana"])

    with tab1:
        planet_df = analyzer.ruling_planet_analysis(merged)
        if not planet_df.empty:
            fig = go.Figure()
            colors = [PLANET_COLORS.get(p, '#999') for p in planet_df['ruling_planet']]
            fig.add_trace(go.Bar(
                x=planet_df['ruling_planet'],
                y=planet_df['mean_return'],
                marker_color=colors,
                text=planet_df['mean_return'].round(4),
                textposition='outside',
            ))
            fig.update_layout(
                title="Mean Return by Ruling Planet",
                yaxis_title="Mean Return (%)",
                template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', height=450, xaxis_tickangle=-30,
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(planet_df, use_container_width=True)

    with tab2:
        element_df = analyzer.element_analysis(merged)
        if not element_df.empty:
            fig = go.Figure()
            colors = [ELEMENT_COLORS.get(e, '#999') for e in element_df['element']]
            fig.add_trace(go.Bar(
                x=element_df['element'],
                y=element_df['mean_return'],
                marker_color=colors,
                text=element_df['mean_return'].round(4),
                textposition='outside',
            ))
            fig.update_layout(
                title="Mean Return by Element",
                yaxis_title="Mean Return (%)",
                template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', height=450,
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(element_df, use_container_width=True)

    with tab3:
        gana_df = analyzer.gana_analysis(merged)
        if not gana_df.empty:
            fig = go.Figure()
            colors = [GANA_COLORS.get(g, '#999') for g in gana_df['gana']]
            fig.add_trace(go.Bar(
                x=gana_df['gana'],
                y=gana_df['mean_return'],
                marker_color=colors,
                text=gana_df['mean_return'].round(4),
                textposition='outside',
            ))
            fig.update_layout(
                title="Mean Return by Gana (Nature)",
                yaxis_title="Mean Return (%)",
                template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', height=450,
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(gana_df, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# PAGE: Nakshatra Encyclopedia
# ═══════════════════════════════════════════════════════════════
elif page == "📖 Nakshatra Encyclopedia":
    st.markdown("## 📖 Nakshatra Encyclopedia")
    st.markdown("Complete reference for all 27 Vedic Nakshatras")

    all_naks = get_all_nakshatras()

    # Search
    search = st.text_input("🔍 Search Nakshatra", placeholder="Type name...")
    if search:
        all_naks = [n for n in all_naks if search.lower() in n['name_english'].lower()
                    or search.lower() in n.get('name_sanskrit', '').lower()
                    or search.lower() in n.get('star_name_western', '').lower()]

    for nak in all_naks:
        tendency = nak.get('historical_market_tendency', 'Neutral')
        badge = 'badge-bullish' if tendency == 'Bullish' else (
            'badge-bearish' if tendency == 'Bearish' else 'badge-neutral')

        with st.expander(
            f"#{nak['number']} {nak['name_english']} ({nak['name_sanskrit']}) — {nak['ruling_planet']}"
        ):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                **English:** {nak['name_english']} | **Sanskrit:** {nak['name_sanskrit']}

                **Western Star:** {nak['star_name_western']} ({nak['common_name_western']})

                **Degree Range:** {nak['degree_range_start']:.2f}° — {nak['degree_range_end']:.2f}°

                **Ruling Planet:** {nak['ruling_planet']}

                **Ruling Deity:** {nak['ruling_deity']}

                **Element:** {nak['element']} | **Gana:** {nak['gana']}

                **Symbol:** {nak['symbol']} | **Yoni:** {nak['yoni']}
                """)
            with c2:
                st.markdown(f"""
                **Financial Traits:** {', '.join(nak['financial_traits'])}

                **Favorable For:** {', '.join(nak['favorable_for'])}

                **Unfavorable For:** {', '.join(nak['unfavorable_for'])}

                **Lucky Colors:** {', '.join(nak['lucky_colors'])}

                **Lucky Numbers:** {', '.join(map(str, nak['lucky_numbers']))}

                **Lucky Days:** {', '.join(nak['lucky_days'])}
                """)


# ═══════════════════════════════════════════════════════════════
# PAGE: Settings
# ═══════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.markdown("## ⚙️ Settings & Configuration")

    st.markdown("### Swiss Ephemeris")
    st.info("The system uses Swiss Ephemeris (pyswisseph) for Moon calculations with Lahiri Ayanamsa.")

    st.markdown("### Data Sources")
    st.markdown("""
    - **Market Data:** yfinance (Yahoo Finance API)
    - **Astronomical Data:** Swiss Ephemeris (Lahiri Ayanamsa)
    - **Cache:** SQLite database at `data/market_cache.db`
    """)

    st.markdown("### About")
    st.markdown("""
    **Astro-Finance** correlates the Moon's position in Vedic Nakshatras with NSE stock market performance.

    This tool is for **research and educational purposes only**. Past astrological patterns do not guarantee future results.
    Always consult a financial advisor before making investment decisions.
    """)

    st.markdown("### ⚠️ Disclaimer")
    st.warning("""
    This application combines Vedic astrology with financial data analysis for educational
    and research purposes. It does NOT constitute financial advice. Stock market investments
    are subject to market risks. Past performance is not indicative of future results.
    """)
