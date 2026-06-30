import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

# --- 1. Page Configuration ---
st.set_page_config(page_title="FinPulse Terminal", page_icon="📈", layout="wide")

st.title("📈 FinPulse Market Terminal")
st.markdown("Real-time equity dashboard, fundamental analysis, and multi-company comparison.")
st.divider()

# --- 2. Sidebar Setup (With Auto-.NS Background Logic) ---
with st.sidebar:
    st.header("🔍 Market Search")
    # Users type standard clean names (e.g., TCS, RELIANCE, WAAREERTL)
    display_ticker = st.text_input("Enter Ticker Symbol:", value="RELIANCE").upper().strip()
    
    # Silently append .NS behind the scenes for the API request if no dot is present
    if display_ticker and "." not in display_ticker:
        ticker_input = f"{display_ticker}.NS"
    else:
        ticker_input = display_ticker
        
    fetch_button = st.button("Analyze Stock", type="primary", use_container_width=True)
    
    st.divider()
    st.header("📋 Tracked Watchlist")
    # Cleaned up visual presentation without .NS text clutter
    watchlist = ["RELIANCE", "TCS", "HDFCBANK", "WAAREERTL", "NORTHARC"]
    for w_ticker in watchlist:
        st.code(w_ticker, language="markdown")

# --- 3. Terminal Navigation Tabs ---
tab_single, tab_compare = st.tabs(["📊 Single Stock Analysis", "⚖️ Company Comparison"])

# ==========================================
# TAB 1: SINGLE STOCK ANALYSIS
# ==========================================
with tab_single:
    if fetch_button or ticker_input:
        with st.spinner(f"Fetching market metrics for {display_ticker}..."):
            backend_url = f"http://127.0.0.1:8001/stock/{ticker_input}"
            
            try:
                response = requests.get(backend_url)
                
                if response.status_code == 200:
                    result = response.json()
                    stock_data = result.get("data", {})

                    st.subheader(f"🏢 {stock_data.get('company_name', display_ticker)} ({display_ticker})")
                    
                    # Row 1: Primary Valuation Metrics
                    st.markdown("##### **Core Valuation & Market Size**")
                    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                    current_price = stock_data.get('current_price', 0.0)
                    mock_change = round(np.random.uniform(-2.5, 2.5), 2)
                    
                    m_col1.metric("Current Price", f"₹{current_price:,}", f"{mock_change}%")
                    m_col2.metric("Market Capitalization", f"₹{stock_data.get('market_cap', 0):,}")
                    m_col3.metric("P/E Ratio", f"{stock_data.get('pe_ratio', 'N/A')}x" if stock_data.get('pe_ratio') else "N/A")
                    m_col4.metric("Earnings Per Share (EPS)", f"₹{stock_data.get('eps', 'N/A')}")
                    
                    st.write("") # Structural spacing layout element
                    
                    # Row 2: Secondary Trading & Volatility Metrics
                    st.markdown("##### **Session Range & Risk Factors**")
                    sub_col1, sub_col2, sub_col3, sub_col4, sub_col5 = st.columns(5)
                    sub_col1.metric("Day High", f"₹{stock_data.get('day_high', 0.0):,}")
                    sub_col2.metric("Day Low", f"₹{stock_data.get('day_low', 0.0):,}")
                    sub_col3.metric("Trading Volume", f"{stock_data.get('volume', 0):,}")
                    sub_col4.metric("Dividend Yield", f"{stock_data.get('dividend_yield', 0.0)}%")
                    sub_col5.metric("Beta (Volatility)", f"{stock_data.get('beta', 1.0)}")
                    
                    st.write("") # Structural spacing layout element
                    st.markdown("##### **52-Week Range Boundary**")
                    range_col1, range_col2 = st.columns(2)
                    range_col1.metric("52-Week High Target", f"₹{stock_data.get('fifty_two_week_high', 0.0):,}")
                    range_col2.metric("52-Week Low Floor", f"₹{stock_data.get('fifty_two_week_low', 0.0):,}")

                    st.divider()

                    # Interactive Candlestick Chart Area
                    st.subheader("📊 Historical Price Actions")
                    dates = pd.date_range(end=date.today(), periods=30)
                    opens, highs, lows, closes = [], [], [], []
                    base_price = current_price
                    
                    for _ in range(30):
                        daily_move = base_price * np.random.normal(0, 0.015)
                        o = base_price
                        c = base_price + daily_move
                        h = max(o, c) + abs(base_price * np.random.uniform(0, 0.008))
                        l = min(o, c) - abs(base_price * np.random.uniform(0, 0.008))
                        opens.append(o); highs.append(h); lows.append(l); closes.append(c)
                        base_price = c
                    
                    opens.reverse(); highs.reverse(); lows.reverse(); closes.reverse()
                    
                    fig = go.Figure(data=[go.Candlestick(x=dates, open=opens, high=highs, low=lows, close=closes)])
                    fig.update_layout(
                        xaxis_rangeslider_visible=True, # Maintained interactive timeline slider
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=450,
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.error(f"Backend HTTP Connection Error: {response.status_code}")
            except Exception as e:
                st.error("Could not communicate with FastAPI server pipeline. Is your backend processing requests on Port 8001?")

# ==========================================
# TAB 2: COMPANY COMPARISON
# ==========================================
with tab_compare:
    st.subheader("⚖️ Side-by-Side Asset Comparison")
    st.markdown("Perform head-to-head structural matching across financial dimensions.")
    
    comp_col1, comp_col2 = st.columns(2)
    with comp_col1:
        t1_raw = st.text_input("First Ticker Symbol:", value="RELIANCE", key="t1").upper().strip()
        ticker1 = f"{t1_raw}.NS" if t1_raw and "." not in t1_raw else t1_raw
        display_t1 = t1_raw
        
    with comp_col2:
        t2_raw = st.text_input("Second Ticker Symbol:", value="WAAREERTL", key="t2").upper().strip()
        ticker2 = f"{t2_raw}.NS" if t2_raw and "." not in t2_raw else t2_raw
        display_t2 = t2_raw
        
    if st.button("Generate Matrix Comparison", type="primary"):
        with st.spinner("Processing asset criteria arrays..."):
            try:
                res1 = requests.get(f"http://127.0.0.1:8001/stock/{ticker1}").json().get("data", {})
                res2 = requests.get(f"http://127.0.0.1:8001/stock/{ticker2}").json().get("data", {})
                
                comp_matrix = {
                    "Analysis Core Fields": [
                        "Company Legal Identity", "Current Market Valuation Price", "Calculated Market Capitalization",
                        "Trailing P/E Multiple", "Calculated EPS", "Intraday Performance High", "Intraday Performance Low",
                        "Trading Volumetric Output", "52-Week Maximum Limit", "52-Week Minimum Support", 
                        "Allocated Dividend Yield %", "Beta Risk Co-efficient Factor"
                    ],
                    display_t1: [
                        res1.get("company_name", "N/A"), f"₹{res1.get('current_price', 0):,}", f"₹{res1.get('market_cap', 0):,}",
                        f"{res1.get('pe_ratio', 'N/A')}x", f"₹{res1.get('eps', 'N/A')}", f"₹{res1.get('day_high', 0.0):,}",
                        f"₹{res1.get('day_low', 0.0):,}", f"{res1.get('volume', 0):,}", f"₹{res1.get('fifty_two_week_high', 0.0):,}",
                        f"₹{res1.get('fifty_two_week_low', 0.0):,}", f"{res1.get('dividend_yield', 0.0)}%", res1.get("beta", "N/A")
                    ],
                    display_t2: [
                        res2.get("company_name", "N/A"), f"₹{res2.get('current_price', 0):,}", f"₹{res2.get('market_cap', 0):,}",
                        f"{res2.get('pe_ratio', 'N/A')}x", f"₹{res2.get('eps', 'N/A')}", f"₹{res2.get('day_high', 0.0):,}",
                        f"₹{res2.get('day_low', 0.0):,}", f"{res2.get('volume', 0):,}", f"₹{res2.get('fifty_two_week_high', 0.0):,}",
                        f"₹{res2.get('fifty_two_week_low', 0.0):,}", f"{res2.get('dividend_yield', 0.0)}%", res2.get("beta", "N/A")
                    ]
                }
                
                st.dataframe(pd.DataFrame(comp_matrix), hide_index=True, use_container_width=True)
                
            except Exception as e:
                st.error("Failed executing comparison matrix array mapping. Make sure backend endpoints are listening.")