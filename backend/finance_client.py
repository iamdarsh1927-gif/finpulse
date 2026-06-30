import yfinance as yf
import hashlib

def get_deterministic_mock_value(ticker: str, seed_modifier: int, low_bound: float, high_bound: float) -> float:
    """Generates a consistent, unique mock percentage/value per ticker."""
    hash_input = f"{ticker}-{seed_modifier}".encode('utf-8')
    hash_val = int(hash_lib := hashlib.md5(hash_input).hexdigest(), 16)
    normalized = (hash_val % 10000) / 10000.0
    return round(low_bound + (normalized * (high_bound - low_bound)), 2)

def fetch_stock_info(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Raise an exception if yfinance returned empty/blocked data structure
        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info:
            raise Exception("Empty or blocked response structure from yfinance API.")

        return {
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice", 0.0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE") or info.get("forwardPE", 0.0),
            "eps": info.get("trailingEps", 0.0),
            "day_high": info.get("dayHigh", 0.0),
            "day_low": info.get("dayLow", 0.0),
            "volume": info.get("volume", 0),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0.0),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0.0),
            "dividend_yield": info.get("dividendYield", 0.0) * 100 if info.get("dividendYield") else 0.0,
            "beta": info.get("beta", 1.0)
        }

    except Exception as e:
        print(f"Yahoo Finance blocked or failed for '{ticker}'. Falling back to specialized Mock Data.")
        
        # Anchor base prices closely mapping realistic valuation structures per asset
        base_prices = {"RELIANCE.NS": 1250.0, "WAAREERTL.NS": 1420.0, "NORTHARC.NS": 220.0}
        base_price = base_prices.get(ticker, 500.0)
        
        # Deterministically generate matching metrics relative to the asset price base
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