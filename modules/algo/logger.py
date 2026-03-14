from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

# Can switch this to SQLite for local ease during dev, 
# but User requested PostgreSQL. 
# Providing fallback to SQLite if DB_URL not defined.
DATABASE_URL = os.getenv("ALGO_DB_URL", "sqlite:///algo_trades.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class GlobalMarketLog(Base):
    __tablename__ = "global_market"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    sp500_change = Column(Float)
    nasdaq_change = Column(Float)
    nikkei_change = Column(Float)
    hangseng_change = Column(Float)
    dax_change = Column(Float)
    crude_change = Column(Float)
    gold_change = Column(Float)
    usdinr_change = Column(Float)
    vix_level = Column(Float)
    
    global_score = Column(Integer)
    gift_nifty_gap = Column(Float)
    overall_bias = Column(String(50))

class SignalLog(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    direction = Column(String(10)) # BUY or SELL
    score = Column(Integer)
    
    step1_score = Column(Integer)
    step2_score = Column(Integer)
    step3_score = Column(Integer)
    step4_score = Column(Integer)
    global_bias_score = Column(Integer)
    
    entry_price = Column(Float)
    sl = Column(Float)
    target1 = Column(Float)
    target2 = Column(Float)
    
    trade_placed = Column(Boolean, default=False)

class TradeLog(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    direction = Column(String(10))
    entry = Column(Float)
    exit = Column(Float, nullable=True)
    
    pnl = Column(Float, nullable=True)
    exit_reason = Column(String(50), nullable=True) # SL, Target1, Target2, Time Exit
    duration = Column(Integer, nullable=True) # in minutes
    
    lot_size = Column(Integer)
    global_bias_at_entry = Column(Integer)


def init_db():
    """Initializes tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Algo DB tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Algo DB: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
