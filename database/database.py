from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Define where our database file will live
# "sqlite:///./" means "create a file in the current root folder"
SQLALCHEMY_DATABASE_URL = "sqlite:///./finpulse.db"

# 2. Create the "Engine" (The actual connection to the database)
# connect_args={"check_same_thread": False} is required specifically for SQLite in FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Create a SessionLocal class. 
# Every time we want to read or write to the database, we will create a temporary "session" 
# to do the work, and then close it.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a Base class. 
# All of our future database tables (like a 'Stocks' table) will inherit from this class.
Base = declarative_base()