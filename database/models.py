from sqlalchemy import Column, Integer, String, Float
from database.database import Base

class StockData(Base):
    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True)
    company_name = Column(String)
    current_price = Column(Float)
    market_cap = Column(Float)
    pe_ratio = Column(Float)
    eps = Column(Float)
    
    # --- New Fields Added ---
    day_high = Column(Float)
    day_low = Column(Float)
    volume = Column(Integer)
    fifty_two_week_high = Column(Float)
    fifty_two_week_low = Column(Float)
    dividend_yield = Column(Float)
    beta = Column(Float)