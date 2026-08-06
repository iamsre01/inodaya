from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Use the same engine as main models
from models import engine

Base = declarative_base()

# We'll use the existing SessionLocal from models

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    agent_type = Column(String, default="api")  # api, local_model, deep_research
    config = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="agent")
    connections = relationship("AgentConnection", foreign_keys="AgentConnection.source_agent_id", back_populates="source_agent")
    incoming_connections = relationship("AgentConnection", foreign_keys="AgentConnection.target_agent_id", back_populates="target_agent")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    status = Column(String, default="pending")  # pending, running, completed, failed
    schedule = Column(String)  # Cron expression
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("Agent", back_populates="tasks")

class AgentConnection(Base):
    __tablename__ = "agent_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    source_agent_id = Column(Integer, ForeignKey("agents.id"))
    target_agent_id = Column(Integer, ForeignKey("agents.id"))
    connection_type = Column(String, default="data_flow")
    description = Column(Text)
    
    source_agent = relationship("Agent", foreign_keys=[source_agent_id], back_populates="connections")
    target_agent = relationship("Agent", foreign_keys=[target_agent_id], back_populates="incoming_connections")

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)
    key_value = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class StockWatchlist(Base):
    """Configuration for stock analysis agent - stores watchlist and preferences"""
    __tablename__ = "stock_watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Default Watchlist")
    stocks = Column(JSON, default=["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"])
    risk_tolerance = Column(String, default="moderate")  # low, moderate, high
    sectors_focus = Column(JSON, default=[])  # e.g., ["Technology", "Healthcare"]
    min_market_cap = Column(Float, default=0)  # in billions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StockAnalysisHistory(Base):
    """Stores historical analysis results for learning"""
    __tablename__ = "stock_analysis_history"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    ticker = Column(String, nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    price_at_analysis = Column(Float)
    recommended_action = Column(String)  # BUY, SELL, HOLD
    reasoning = Column(JSON)
    sentiment_score = Column(Float)
    actual_price_after_1d = Column(Float)
    actual_price_after_7d = Column(Float)
    accuracy_score = Column(Float)  # Calculated later
    created_at = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("Task")
