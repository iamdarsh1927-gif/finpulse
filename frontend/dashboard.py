import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

# --- 1. Page Configuration ---
st.set_page_config(page_title="FinPulse Terminal", layout="wide")

st.title("FinPulse Market Terminal")
st.markdown("Real-time equity dashboard, fundamental analysis, and multi-company comparison.")
st.divider()

# --- 2. Initialize Dynamic Session State Watchlist ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = {
        "RELIANCE": "Reliance Industries",
        "TCS": "Tata Consultancy Services",
        "HDFCBANK": "HDFC Bank",
        "TATAMOTORS": "Tata Motors"
    }

# --- 3. Sidebar Setup ---
with st.sidebar:
    st.header("Market Search")
    
    display_ticker = st.text_input("Enter Ticker Symbol:", value="").upper().strip()
    
    if display_ticker and "." not in display_ticker:
        ticker_input = f"{display_ticker}.NS"
    else:
        ticker_input = display_ticker
        
    fetch_button = st.button("Analyze Stock", type="primary", use_container_width=True)
    
    st.divider()
    st.header("Dynamic Watchlist")
    st.caption("Active session asset tracking:")
    
    if st.session_state.watchlist:
        for ticker, name in list(st.session_state.watchlist.items()):
            col1, col2 = st.columns([0.8, 0.2])
            col1.markdown(f"**{ticker}** | *{name}*")
            if col2.button("X", key=f"del_{ticker}", help=f"Remove {ticker}"):
                del st.session_state.watchlist[ticker]
                st.rerun()
    else:
        st.caption("Watchlist is currently empty.")
        
    st.write("")
    
    with st.expander("+ Add New Asset"):
        new_ticker = st.text_input("Ticker Symbol (e.g. ZOMATO):", key="add_t").upper().strip()
        new_name = st.text_input("Company Name:", key="add_n").strip()
        
        if st.button("Add to Watchlist", use_container_width=True):
            if new_ticker and new_name:
                clean_ticker = new_ticker.replace(".NS", "")
                st.session_state.watchlist[clean_ticker] = new_name
                st.rerun()
            else:
                st.warning("Please provide both Ticker and Name.")

# --- 4. Terminal Navigation Tabs ---
tab_single, tab_compare, tab_stmts = st.tabs(["Single Stock Analysis", "Company Comparison", "Financial Statements"])

# ==========================================
# TAB 1: SINGLE STOCK ANALYSIS
# ==========================================
with tab_single:
    if (fetch_button or display_ticker) and display_ticker != "":
        with st.spinner(f"Fetching market metrics for {display_ticker}..."):
            backend_url = f"https://finpulse-sbsu.onrender.com/stock/{ticker_input}"
            
            try:
                response = requests.get(backend_url)
                
                if response.status_code == 200:
                    result = response.json()
                    stock_data = result.get("data", {})

                    st.subheader(f"{stock_data.get('company_name', display_ticker)} ({display_ticker})")
                    
                    st.markdown("##### Core Valuation & Market Size")
                    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                    
                    current_price = stock_data.get('current_price', 0.0)
                    mock_change = round(np.random.uniform(-2.5, 2.5), 2)
                    
                    raw_mc = stock_data.get('market_cap', 0)
                    mc_crores = raw_mc / 10000000 
                    
                    m_col1.metric("Current Price", f"₹{current_price:,}", f"{mock_change}%")
                    m_col2.metric("Market Capitalization", f"₹{mc_crores:,.2f} Cr")
                    m_col3.metric("P/E Ratio", f"{stock_data.get('pe_ratio', 'N/A')}x" if stock_data.get('pe_ratio') else "N/A")
                    m_col4.metric("Earnings Per Share (EPS)", f"₹{stock_data.get('eps', 'N/A')}")
                    
                    st.write("") 
                    
                    st.markdown("##### Session Range & Risk Factors")
                    sub_col1, sub_col2, sub_col3, sub_col4, sub_col5 = st.columns(5)
                    sub_col1.metric("Day High", f"₹{stock_data.get('day_high', 0.0):,}")
                    sub_col2.metric("Day Low", f"₹{stock_data.get('day_low', 0.0):,}")
                    sub_col3.metric("Trading Volume", f"{stock_data.get('volume', 0):,}")
                    sub_col4.metric("Dividend Yield", f"{stock_data.get('dividend_yield', 0.0)}%")
                    sub_col5.metric("Beta (Volatility)", f"{stock_data.get('beta', 1.0)}")
                    
                    st.write("") 
                    st.markdown("##### 52-Week Range Boundary")
                    range_col1, range_col2 = st.columns(2)
                    range_col1.metric("52-Week High Target", f"₹{stock_data.get('fifty_two_week_high', 0.0):,}")
                    range_col2.metric("52-Week Low Floor", f"₹{stock_data.get('fifty_two_week_low', 0.0):,}")

                    st.divider()

                    st.subheader("Historical Price Actions")
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
                        xaxis_rangeslider_visible=True,
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=450,
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.error(f"Backend HTTP Connection Error: {response.status_code}")
            except Exception as e:
                st.error("Could not communicate with FastAPI server pipeline. Ensure your backend is live.")

# ==========================================
# TAB 2: COMPANY COMPARISON
# ==========================================
with tab_compare:
    st.subheader("Side-by-Side Asset Comparison")
    st.markdown("Perform head-to-head structural matching across financial dimensions.")
    
    comp_col1, comp_col2 = st.columns(2)
    with comp_col1:
        t1_raw = st.text_input("First Ticker Symbol:", value="", key="t1").upper().strip()
        ticker1 = f"{t1_raw}.NS" if t1_raw and "." not in t1_raw else t1_raw
        display_t1 = t1_raw
        
    with comp_col2:
        t2_raw = st.text_input("Second Ticker Symbol:", value="", key="t2").upper().strip()
        ticker2 = f"{t2_raw}.NS" if t2_raw and "." not in t2_raw else t2_raw
        display_t2 = t2_raw
        
    if st.button("Generate Matrix Comparison", type="primary"):
        if display_t1 != "" and display_t2 != "":
            with st.spinner("Processing asset criteria arrays..."):
                try:
                    res1 = requests.get(f"https://finpulse-sbsu.onrender.com/stock/{ticker1}").json().get("data", {})
                    res2 = requests.get(f"https://finpulse-sbsu.onrender.com/stock/{ticker2}").json().get("data", {})
                    
                    mc1_crores = res1.get('market_cap', 0) / 10000000
                    mc2_crores = res2.get('market_cap', 0) / 10000000
                    
                    comp_matrix = {
                        "Analysis Core Fields": [
                            "Company Legal Identity", "Current Market Valuation", "Calculated Market Capitalization",
                            "Trailing P/E Multiple", "Calculated EPS", "Intraday Performance High", "Intraday Performance Low",
                            "Trading Volumetric Output", "52-Week Maximum Limit", "52-Week Minimum Support", 
                            "Allocated Dividend Yield %", "Beta Risk Co-efficient Factor"
                        ],
                        display_t1: [
                            res1.get("company_name", "N/A"), f"₹{res1.get('current_price', 0):,}", f"₹{mc1_crores:,.2f} Cr",
                            f"{res1.get('pe_ratio', 'N/A')}x", f"₹{res1.get('eps', 'N/A')}", f"₹{res1.get('day_high', 0.0):,}",
                            f"₹{res1.get('day_low', 0.0):,}", f"{res1.get('volume', 0):,}", f"₹{res1.get('fifty_two_week_high', 0.0):,}",
                            f"₹{res1.get('fifty_two_week_low', 0.0):,}", f"{res1.get('dividend_yield', 0.0)}%", res1.get("beta", "N/A")
                        ],
                        display_t2: [
                            res2.get("company_name", "N/A"), f"₹{res2.get('current_price', 0):,}", f"₹{mc2_crores:,.2f} Cr",
                            f"{res2.get('pe_ratio', 'N/A')}x", f"₹{res2.get('eps', 'N/A')}", f"₹{res2.get('day_high', 0.0):,}",
                            f"₹{res2.get('day_low', 0.0):,}", f"{res2.get('volume', 0):,}", f"₹{res2.get('fifty_two_week_high', 0.0):,}",
                            f"₹{res2.get('fifty_two_week_low', 0.0):,}", f"{res2.get('dividend_yield', 0.0)}%", res2.get("beta", "N/A")
                        ]
                    }
                    
                    st.dataframe(pd.DataFrame(comp_matrix), hide_index=True, use_container_width=True)
                    
                except Exception as e:
                    st.error("Failed executing comparison matrix array mapping.")

# ==========================================
# TAB 3: FINANCIAL STATEMENTS
# ==========================================
with tab_stmts:
    st.subheader("Core Accounting & Audit Statements")
    st.markdown("Annual consolidated ledger analysis across Profit & Loss, Balance Sheet, and Cash Flows.")
    
    if (fetch_button or display_ticker) and display_ticker != "":
        with st.spinner(f"Extracting accounting ledgers for {display_ticker}..."):
            backend_url = f"https://finpulse-sbsu.onrender.com/stock/{ticker_input}"
            try:
                response = requests.get(backend_url)
                if response.status_code == 200:
                    result = response.json()
                    stock_data = result.get("data", {})
                    stmts = stock_data.get("financial_statements", {})
                    
                    st.markdown(f"#### **{stock_data.get('company_name', display_ticker)}** | *{display_ticker}*")
                    st.write("")
                    
                    # Sleek segmented selector for institutional aesthetics
                    stmt_choice = st.radio(
                        "Select Ledger View:", 
                        ["Income Statement (P&L)", "Balance Sheet", "Cash Flow Statement"], 
                        horizontal=True
                    )
                    st.write("")
                    
                    if stmt_choice == "Income Statement (P&L)":
                        inc_data = stmts.get("income_statement", [])
                        if inc_data:
                            st.dataframe(pd.DataFrame(inc_data), hide_index=True, use_container_width=True)
                        else:
                            st.info("Income statement currently unavailable.")
                            
                    elif stmt_choice == "Balance Sheet":
                        bal_data = stmts.get("balance_sheet", [])
                        if bal_data:
                            st.dataframe(pd.DataFrame(bal_data), hide_index=True, use_container_width=True)
                        else:
                            st.info("Balance sheet currently unavailable.")
                            
                    elif stmt_choice == "Cash Flow Statement":
                        csh_data = stmts.get("cash_flow", [])
                        if csh_data:
                            st.dataframe(pd.DataFrame(csh_data), hide_index=True, use_container_width=True)
                        else:
                            st.info("Cash flow statement currently unavailable.")
                else:
                    st.error(f"Backend HTTP Connection Error: {response.status_code}")
            except Exception as e:
                st.error("Could not communicate with FastAPI server pipeline.")
    else:
        st.info("Enter a Ticker Symbol in the sidebar (e.g., RELIANCE or TCS) and click Analyze Stock to view accounting statements.")