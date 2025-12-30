"""
Database Models
===============

SQLAlchemy models for persisting trading state.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from .db_manager import Base

class TradeRecord(Base):
    """Persisted trade record."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(50))
    side = Column(String(10))
    entry_price = Column(Float)
    exit_price = Column(Float)
    amount = Column(Float)
    pnl_usd = Column(Float)
    pnl_pct = Column(Float)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime)
    strategy_name = Column(String(100))
    regime_at_entry = Column(String(50))
    meta_data = Column(JSON)

class SystemEvent(Base):
    """Log of critical system events (restarts, errors, circuit breaker trips)."""
    __tablename__ = "system_events"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(50))
    component = Column(String(50))
    message = Column(String(500))
    details = Column(JSON)
