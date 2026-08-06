from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    agent_type = Column(String, default="api")  # api, local_model
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
    name = Column(String, nullable=False)
    key_value = Column(String, nullable=False)
    provider = Column(String)  # openai, anthropic, local, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./agents.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
