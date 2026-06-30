from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.database import engine, SessionLocal
from database import models
from backend.finance_client import fetch_stock_info

app = FastAPI(title="FinPulse API")
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the FinPulse API!"}

@app.get("/health")
def check_health():
    return {"status": "Server is healthy and running!"}

@app.get("/stock/{ticker_symbol}")
def get_and_save_stock(ticker_symbol: str, db: Session = Depends(get_db)):
    ticker_symbol = ticker_symbol.upper().strip()
    
    stock_data = fetch_stock_info(ticker_symbol)
    
    if "error" in stock_data:
        return stock_data
    

    existing_stock = db.query(models.StockData).filter(models.StockData.ticker == ticker_symbol).first()
    
    if existing_stock:
        existing_stock.current_price = stock_data["current_price"]
        existing_stock.market_cap = stock_data["market_cap"]
        existing_stock.pe_ratio = stock_data["pe_ratio"]
        existing_stock.eps = stock_data["eps"]
        existing_stock.day_high = stock_data["day_high"]
        existing_stock.day_low = stock_data["day_low"]
        existing_stock.volume = stock_data["volume"]
        existing_stock.fifty_two_week_high = stock_data["fifty_two_week_high"]
        existing_stock.fifty_two_week_low = stock_data["fifty_two_week_low"]
        existing_stock.dividend_yield = stock_data["dividend_yield"]
        existing_stock.beta = stock_data["beta"]
    else:
        new_stock = models.StockData(
            ticker=stock_data["ticker"],
            company_name=stock_data["company_name"],
            current_price=stock_data["current_price"],
            market_cap=stock_data["market_cap"],
            pe_ratio=stock_data["pe_ratio"],
            eps=stock_data["eps"],
            day_high=stock_data["day_high"],
            day_low=stock_data["day_low"],
            volume=stock_data["volume"],
            fifty_two_week_high=stock_data["fifty_two_week_high"],
            fifty_two_week_low=stock_data["fifty_two_week_low"],
            dividend_yield=stock_data["dividend_yield"],
            beta=stock_data["beta"]
        )
        db.add(new_stock)
        
    # --- NEW RACE CONDITION PROTECTION ---
    try:
        db.commit()
    except IntegrityError:
        # If two requests try to save the exact same new ticker at the exact same time,
        # cancel this duplicate save to prevent a crash.
        db.rollback()
        
    return {"message": f"Successfully fetched data for {ticker_symbol}!", "data": stock_data}