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

# --- 2. Helper Functions (Styling & Live API Search Engine) ---
@st.cache_data(show_spinner=False, ttl=600)
def fetch_live_suggestions(query: str):
    """Queries Yahoo Finance Live Search API for dynamic, real-time stock autocomplete"""
    if not query or len(query.strip()) < 2:
        return []
        
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=12&newsCount=0"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=5).json()
        quotes = res.get("quotes", [])
        results = []
        for q in quotes:
            # Filter to only show actual tradable equities, ETFs, or Mutual Funds
            if q.get("quoteType") in ["EQUITY", "ETF", "MUTUALFUND", "INDEX"]:
                sym = q.get("symbol", "")
                name = q.get("shortname") or q.get("longname") or sym
                exch = q.get("exchDisp", "Market")
                results.append(f"{sym} | {name} ({exch})")
        return results
    except Exception:
        return []

def render_styled_ledger(data_list):
    """Transforms raw dictionary lists into Bloomberg-style financial ledgers"""
    if not data_list:
        st.info("Statement currently unavailable.")
        return
        
    df = pd.DataFrame(data_list)
    year_cols = [col for col in df.columns if col != "Accounting Metric"]
    
    styler = df.style\
        .set_properties(subset=["Accounting Metric"], **{
            'text-align': 'left', 
            'font-weight': '600'
        })\
        .set_properties(subset=year_cols, **{
            'text-align': 'right', 
            'font-family': 'Consolas, monospace',
            'font-size': '14px'
        })
        
    def highlight_headline_metrics(row):
        metric = str(row["Accounting Metric"]).lower()
        headline_terms = [
            "sales", "revenue", "operating profit", "net profit", 
            "total liabilities", "total assets", "total borrowings", 
            "net cash flow", "operating activity"
        ]
        if any(term in metric for term in headline_terms):
            return ['background-color: rgba(128, 128, 128, 0.15); font-weight: 700;' for _ in row]
        return ['' for _ in row]
        
    styler.apply(highlight_headline_metrics, axis=1)
    
    calc_height = (len(df) * 38) + 42
    
    st.dataframe(
        styler, 
        hide_index=True, 
        use_container_width=True,
        height=calc_height
    )

# --- 3. Initialize Dynamic Session State Watchlist ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = {
        "RELIANCE": "Reliance Industries",
        "TCS": "Tata Consultancy Services",
        "HDFCBANK": "HDFC Bank",
        "TATAMOTORS": "Tata Motors"
    }

# --- 4. Sidebar Setup (Live API Autocomplete) ---
with st.sidebar:
    st.header("Market Search")
    st.caption("Live Global & Indian Market Search")
    
    # Step 1: User types any company name
    search_query = st.text_input(
        "Type Company Name or Symbol:", 
        value="", 
        placeholder="e.g. Tata Power, Zomato, Apple..."
    ).strip()
    
    ticker_input = ""
    display_ticker = ""
    
    # Step 2: Instantly fetch live matching stocks from exchange API
    if search_query:
        suggestions = fetch_live_suggestions(search_query)
        if suggestions:
            chosen_asset = st.selectbox("Select exact match:", options=suggestions, key="search_select")
            if chosen_asset:
                # Extract ticker and clean display name automatically
                parts = chosen_asset.split(" | ")
                ticker_input = parts[0].strip()
                display_ticker = ticker_input.replace(".NS", "").replace(".BO", "")
        else:
            st.warning("No listed exchange matches found.")
            
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
        add_query = st.text_input("Search Company to Add:", value="", placeholder="e.g. Infosys, ITC...", key="add_q").strip()
        if add_query:
            add_suggestions = fetch_live_suggestions(add_query)
            if add_suggestions:
                chosen_add = st.selectbox("Select match to add:", options=add_suggestions, key="add_select")
                if st.button("Add to Watchlist", use_container_width=True):
                    if chosen_add:
                        parts = chosen_add.split(" | ")
                        clean_t = parts[0].replace(".NS", "").replace(".BO", "").strip()
                        # Extracts clean name without exchange tag
                        clean_n = parts[1].split(" (")[0].strip() if len(parts) > 1 else clean_t
                        st.session_state.watchlist[clean_t] = clean_n
                        st.rerun()
            else:
                st.warning("No matches found.")

# --- 5. Terminal Navigation Tabs ---
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
                    
                    stmt_choice = st.radio(
                        "Select Ledger View:", 
                        ["Income Statement (P&L)", "Balance Sheet", "Cash Flow Statement"], 
                        horizontal=True
                    )
                    st.write("")
                    
                    if stmt_choice == "Income Statement (P&L)":
                        render_styled_ledger(stmts.get("income_statement", []))
                    elif stmt_choice == "Balance Sheet":
                        render_styled_ledger(stmts.get("balance_sheet", []))
                    elif stmt_choice == "Cash Flow Statement":
                        render_styled_ledger(stmts.get("cash_flow", []))
                            
                    st.write("")
                    st.caption("ℹ️ **Note:** All monetary figures are reported in **Indian Rupees Crores (₹ Cr)** unless indicated as a percentage (%), ratio, or per-share metric.")
                else:
                    st.error(f"Backend HTTP Connection Error: {response.status_code}")
            except Exception as e:
                st.error("Could not communicate with FastAPI server pipeline.")
    else:
        st.info("Enter a Ticker Symbol in the sidebar (e.g., RELIANCE or TCS) and click Analyze Stock to view accounting statements.")