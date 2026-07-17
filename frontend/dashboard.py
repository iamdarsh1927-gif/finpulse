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

# --- 2. Institutional Table Styling Helper ---
def render_styled_ledger(data_list):
    """Transforms raw dictionary lists into Bloomberg-style financial ledgers"""
    if not data_list:
        st.info("Statement currently unavailable.")
        return
        
    df = pd.DataFrame(data_list)
    year_cols = [col for col in df.columns if col != "Accounting Metric"]
    
    # 1. Apply typography: Left-align labels, Right-align monospace numbers
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
        
    # 2. Apply theme-agnostic highlighting to headline financial totals
    def highlight_headline_metrics(row):
        metric = str(row["Accounting Metric"]).lower()
        headline_terms = [
            "sales", "revenue", "operating profit", "net profit", 
            "total liabilities", "total assets", "total borrowings", 
            "net cash flow", "operating activity"
        ]
        if any(term in metric for term in headline_terms):
            # Creates a subtle bold highlight bar across the entire row
            return ['background-color: rgba(128, 128, 128, 0.15); font-weight: 700;' for _ in row]
        return ['' for _ in row]
        
    styler.apply(highlight_headline_metrics, axis=1)
    
    # 3. Dynamic height calculation to eliminate awkward inner scrollbars
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

# --- 4. Sidebar Setup ---
# --- 4. Sidebar Setup ---
with st.sidebar:
    # 1. Master Stock Directory (Shared by both Market Search & Add to Watchlist)
    # You can add as many NSE/BSE companies here as you want!
    NSE_DIRECTORY = {
        "RELIANCE": "Reliance Industries Ltd",
        "TCS": "Tata Consultancy Services",
        "HDFCBANK": "HDFC Bank Ltd",
        "INFY": "Infosys Ltd",
        "ICICIBANK": "ICICI Bank Ltd",
        "HINDUNILVR": "Hindustan Unilever Ltd",
        "SBIN": "State Bank of India",
        "BHARTIARTL": "Bharti Airtel Ltd",
        "ITC": "ITC Ltd",
        "KOTAKBANK": "Kotak Mahindra Bank",
        "LT": "Larsen & Toubro Ltd",
        "TATAMOTORS": "Tata Motors Ltd",
        "AXISBANK": "Axis Bank Ltd",
        "ADANIENT": "Adani Enterprises",
        "MARUTI": "Maruti Suzuki India",
        "SUNPHARMA": "Sun Pharmaceutical",
        "TITAN": "Titan Company Ltd",
        "BAJFINANCE": "Bajaj Finance Ltd",
        "WIPRO": "Wipro Ltd",
        "ZOMATO": "Zomato Ltd",
        "WAAREERTL": "Waaree Renewable Technologies",
        "NORTHARC": "Northern Arc Capital"
    }
    
    # Format into searchable strings: "RELIANCE | Reliance Industries Ltd"
    search_options = [f"{ticker} | {name}" for ticker, name in NSE_DIRECTORY.items()]

    st.header("Market Search")
    
    # Market Search Autocomplete Box
    selected_option = st.selectbox(
        "Search Company or Ticker:",
        options=search_options,
        index=None,  # Keeps box empty by default
        placeholder="Type company name (e.g. Tata, HDFC)..."
    )
    
    if selected_option:
        display_ticker = selected_option.split(" | ")[0]
        ticker_input = f"{display_ticker}.NS"
    else:
        display_ticker = ""
        ticker_input = ""
        
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
        # Watchlist Autocomplete Box (Reuses the same search_options!)
        selected_add = st.selectbox(
            "Search & Select Company to Add:",
            options=search_options,
            index=None,
            placeholder="Type name to add...",
            key="add_asset_select"
        )
        
        if st.button("Add to Watchlist", use_container_width=True):
            if selected_add:
                # Automatically split "TICKER | Company Name" into separate variables
                parts = selected_add.split(" | ")
                clean_ticker = parts[0]
                clean_name = parts[1]
                
                # Save into session state and reload UI
                st.session_state.watchlist[clean_ticker] = clean_name
                st.rerun()
            else:
                st.warning("Please select a company from the list.")
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
                    
                    # Apply institutional rendering to chosen ledger
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