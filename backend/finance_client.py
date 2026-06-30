import requests
from bs4 import BeautifulSoup
import hashlib

# Keep the deterministic mock as an absolute final fail-safe
def get_deterministic_mock_value(ticker: str, seed_modifier: int, low_bound: float, high_bound: float) -> float:
    hash_input = f"{ticker}-{seed_modifier}".encode('utf-8')
    hash_val = int(hash_lib := hashlib.md5(hash_input).hexdigest(), 16)
    normalized = (hash_val % 10000) / 10000.0
    return round(low_bound + (normalized * (high_bound - low_bound)), 2)

def fetch_stock_info(ticker: str) -> dict:
    try:
        # 1. Switch target to Google Finance
        symbol = ticker.replace(".NS", "")
        url = f"https://www.google.com/finance/quote/{symbol}:NSE"
        
        # 2. Mimic a standard Windows Chrome Browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        # 3. Fetch the raw website code
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Google Finance returned {response.status_code}")
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 4. Extract Company Name
        name_div = soup.find('div', class_='zzDege')
        company_name = name_div.text.strip() if name_div else symbol
        
        # 5. Extract Current Price
        price_div = soup.find('div', class_='YMlKec fxKbKc')
        if not price_div:
            raise Exception("Price not found. Ticker may be invalid.")
            
        def clean_num(text):
            # Removes currency symbols/commas, converts abbreviations (T, B, M, K) into real numbers
            text = text.replace('₹', '').replace('$', '').replace(',', '').strip()
            if text == '-' or not text: return 0.0
            mult = 1
            if text.endswith('T'): mult = 1e12; text = text[:-1]
            elif text.endswith('B'): mult = 1e9; text = text[:-1]
            elif text.endswith('M'): mult = 1e6; text = text[:-1]
            elif text.endswith('K'): mult = 1e3; text = text[:-1]
            try: return float(text) * mult
            except: return 0.0

        current_price = clean_num(price_div.text)
        
        # 6. Extract all available fundamental stats from the Google grid
        stats = {}
        for item in soup.find_all('div', class_='gyFHrc'):
            label = item.find('div', class_='mfs7Pt')
            value = item.find('div', class_='P6K39c')
            if label and value:
                stats[label.text.strip()] = value.text.strip()
                
        # 7. Safely parse ranges
        day_parts = stats.get("Day range", "0 - 0").split('-')
        day_low = clean_num(day_parts[0])
        day_high = clean_num(day_parts[1]) if len(day_parts) > 1 else day_low
        
        year_parts = stats.get("Year range", "0 - 0").split('-')
        wk52_low = clean_num(year_parts[0])
        wk52_high = clean_num(year_parts[1]) if len(year_parts) > 1 else wk52_low
        
        pe_ratio = clean_num(stats.get("P/E ratio", "0"))
        
        return {
            "ticker": ticker,
            "company_name": company_name,
            "current_price": current_price,
            "market_cap": clean_num(stats.get("Market cap", "0")),
            "pe_ratio": pe_ratio,
            "eps": round(current_price / pe_ratio, 2) if pe_ratio > 0 else 0.0,
            "day_high": day_high,
            "day_low": day_low,
            "volume": int(clean_num(stats.get("Volume", "0"))),
            "fifty_two_week_high": wk52_high,
            "fifty_two_week_low": wk52_low,
            "dividend_yield": clean_num(stats.get("Dividend yield", "0%").replace('%', '')),
            "beta": get_deterministic_mock_value(ticker, 6, 0.6, 1.6) # Google doesn't display Beta, use fallback
        }

    except Exception as e:
        print(f"Scraper failed for '{ticker}': {e}. Falling back to Mock Data.")
        
        # --- The Absolute Final Fallback ---
        base_prices = {"RELIANCE.NS": 1250.0, "WAAREERTL.NS": 1420.0, "NORTHARC.NS": 220.0}
        base_price = base_prices.get(ticker, 500.0)
        
        current_price = base_price * get_deterministic_mock_value(ticker, 1, 0.96, 1.04)
        pe_ratio = get_deterministic_mock_value(ticker, 2, 12.0, 45.0) if "NORTHARC" in ticker or "RELIANCE" in ticker else get_deterministic_mock_value(ticker, 2, 60.0, 95.0)
        
        return {
            "ticker": ticker,
            "company_name": f"{ticker.split('.')[0]} Industries Ltd (Mock Data)",
            "current_price": round(current_price, 2),
            "market_cap": int(current_price * get_deterministic_mock_value(ticker, 3, 50_000_000, 80_000_000)),
            "pe_ratio": round(pe_ratio, 2),
            "eps": round(current_price / pe_ratio, 2),
            "day_high": round(current_price * 1.02, 2),
            "day_low": round(current_price * 0.98, 2),
            "volume": int(get_deterministic_mock_value(ticker, 4, 100_000, 5_000_000)),
            "fifty_two_week_high": round(current_price * 1.35, 2),
            "fifty_two_week_low": round(current_price * 0.65, 2),
            "dividend_yield": get_deterministic_mock_value(ticker, 5, 0.0, 2.5),
            "beta": get_deterministic_mock_value(ticker, 6, 0.6, 1.6)
        }