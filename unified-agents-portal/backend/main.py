from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import json

from models import (
    get_db, init_db, Agent, Task, AgentConnection, APIKey, SessionLocal
)

app = FastAPI(title="Unified Agents Control Portal", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scheduler for automated tasks
scheduler = AsyncIOScheduler()

# In-memory task status tracking
task_status = {}

class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    agent_type: str = "api"  # api, local_model
    config: Dict[str, Any] = {}

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    agent_id: int
    schedule: Optional[str] = None  # Cron expression

class TaskTrigger(BaseModel):
    input_data: Optional[Dict[str, Any]] = {}

class ConnectionCreate(BaseModel):
    source_agent_id: int
    target_agent_id: int
    connection_type: Optional[str] = "data_flow"
    description: Optional[str] = None

class APIKeyCreate(BaseModel):
    name: str
    key_value: str
    provider: str

@app.on_event("startup")
async def startup_event():
    init_db()
    scheduler.start()
    print("✅ Unified Agents Control Portal started!")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Unified Agents Control Portal",
        "endpoints": {
            "agents": "/agents",
            "tasks": "/tasks",
            "connections": "/connections",
            "graph": "/graph",
            "api_keys": "/api-keys"
        }
    }

# Agent endpoints
@app.get("/agents")
async def get_agents(db: SessionLocal = Depends(get_db)):
    agents = db.query(Agent).all()
    return [{
        "id": a.id,
        "name": a.name,
        "description": a.description,
        "agent_type": a.agent_type,
        "config": a.config,
        "is_active": a.is_active,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in agents]

@app.post("/agents")
async def create_agent(agent: AgentCreate, db: SessionLocal = Depends(get_db)):
    db_agent = Agent(**agent.dict())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return {"id": db_agent.id, "name": db_agent.name, "message": "Agent created successfully"}

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: int, db: SessionLocal = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "agent_type": agent.agent_type,
        "config": agent.config,
        "is_active": agent.is_active,
        "created_at": agent.created_at.isoformat() if agent.created_at else None
    }

@app.put("/agents/{agent_id}")
async def update_agent(agent_id: int, agent_update: AgentUpdate, db: SessionLocal = Depends(get_db)):
    db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = agent_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_agent, key, value)
    
    db.commit()
    db.refresh(db_agent)
    return {"message": "Agent updated successfully", "agent": db_agent.name}

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: int, db: SessionLocal = Depends(get_db)):
    db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(db_agent)
    db.commit()
    return {"message": "Agent deleted successfully"}

# Task endpoints
@app.get("/tasks")
async def get_tasks(db: SessionLocal = Depends(get_db)):
    tasks = db.query(Task).all()
    return [{
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "agent_id": t.agent_id,
        "status": t.status,
        "schedule": t.schedule,
        "last_run": t.last_run.isoformat() if t.last_run else None,
        "next_run": t.next_run.isoformat() if t.next_run else None,
        "result": t.result,
        "created_at": t.created_at.isoformat() if t.created_at else None
    } for t in tasks]

@app.post("/tasks")
async def create_task(task: TaskCreate, db: SessionLocal = Depends(get_db)):
    db_task = Task(**task.dict())
    
    # Schedule the task if cron expression provided
    if task.schedule:
        try:
            trigger = CronTrigger.from_crontab(task.schedule)
            scheduler.add_job(
                execute_task,
                trigger=trigger,
                args=[db_task.id],
                id=f"task_{db_task.id}",
                replace_existing=True
            )
            db_task.next_run = trigger.get_next_fire_time(None, datetime.now())
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid cron expression: {str(e)}")
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return {"id": db_task.id, "name": db_task.name, "message": "Task created successfully"}

@app.post("/tasks/{task_id}/trigger")
async def trigger_task(task_id: int, task_data: TaskTrigger, background_tasks: BackgroundTasks, db: SessionLocal = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    background_tasks.add_task(execute_task, task_id, task_data.input_data)
    return {"message": "Task triggered manually", "task_id": task_id}

async def execute_task(task_id: int, input_data: Dict[str, Any] = {}):
    """Execute a task and update its status"""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        
        task.status = "running"
        task.last_run = datetime.utcnow()
        db.commit()
        
        # Get the agent associated with this task
        agent = db.query(Agent).filter(Agent.id == task.agent_id).first()
        if not agent:
            task.status = "failed"
            task.result = {"error": "Agent not found"}
            db.commit()
            return
        
        # Simulate task execution based on agent type
        result = await run_agent_task(agent, input_data)
        
        task.status = "completed"
        task.result = result
        task.last_run = datetime.utcnow()
        
        # Calculate next run time if scheduled
        if task.schedule:
            trigger = CronTrigger.from_crontab(task.schedule)
            task.next_run = trigger.get_next_fire_time(None, datetime.now())
        
        db.commit()
        
    except Exception as e:
        task.status = "failed"
        task.result = {"error": str(e)}
        db.commit()
    finally:
        db.close()

async def run_agent_task(agent: Agent, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run agent task based on configuration"""
    await asyncio.sleep(1)  # Simulate processing time
    
    if agent.agent_type == "local_model":
        # Simulate local model execution
        return {
            "status": "success",
            "agent": agent.name,
            "model": agent.config.get("model_name", "local-model"),
            "input": input_data,
            "output": f"Processed by {agent.name} using local model"
        }
    else:
        # Simulate API-based agent execution
        api_key = agent.config.get("api_key_name")
        return {
            "status": "success",
            "agent": agent.name,
            "provider": agent.config.get("provider", "unknown"),
            "input": input_data,
            "output": f"Processed by {agent.name} via API"
        }

# Connection endpoints
@app.get("/connections")
async def get_connections(db: SessionLocal = Depends(get_db)):
    connections = db.query(AgentConnection).all()
    return [{
        "id": c.id,
        "source_agent_id": c.source_agent_id,
        "target_agent_id": c.target_agent_id,
        "connection_type": c.connection_type,
        "description": c.description
    } for c in connections]

@app.post("/connections")
async def create_connection(connection: ConnectionCreate, db: SessionLocal = Depends(get_db)):
    # Validate agents exist
    source_agent = db.query(Agent).filter(Agent.id == connection.source_agent_id).first()
    target_agent = db.query(Agent).filter(Agent.id == connection.target_agent_id).first()
    
    if not source_agent or not target_agent:
        raise HTTPException(status_code=404, detail="One or both agents not found")
    
    db_connection = AgentConnection(**connection.dict())
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return {"id": db_connection.id, "message": "Connection created successfully"}

@app.delete("/connections/{connection_id}")
async def delete_connection(connection_id: int, db: SessionLocal = Depends(get_db)):
    db_connection = db.query(AgentConnection).filter(AgentConnection.id == connection_id).first()
    if not db_connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    db.delete(db_connection)
    db.commit()
    return {"message": "Connection deleted successfully"}

# Graph visualization endpoint
@app.get("/graph")
async def get_graph_data(db: SessionLocal = Depends(get_db)):
    """Get data for graphical visualization of agent connections"""
    agents = db.query(Agent).all()
    connections = db.query(AgentConnection).all()
    tasks = db.query(Task).all()
    
    nodes = []
    for agent in agents:
        agent_tasks = [t for t in tasks if t.agent_id == agent.id]
        nodes.append({
            "id": agent.id,
            "label": agent.name,
            "type": "agent",
            "agent_type": agent.agent_type,
            "is_active": agent.is_active,
            "tasks_count": len(agent_tasks),
            "active_tasks": len([t for t in agent_tasks if t.status == "running"])
        })
    
    edges = []
    for conn in connections:
        edges.append({
            "from": conn.source_agent_id,
            "to": conn.target_agent_id,
            "label": conn.connection_type,
            "description": conn.description
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "total_agents": len(nodes),
        "total_connections": len(edges)
    }

# API Key endpoints
@app.get("/api-keys")
async def get_api_keys(db: SessionLocal = Depends(get_db)):
    keys = db.query(APIKey).all()
    return [{
        "id": k.id,
        "name": k.name,
        "provider": k.provider,
        "is_active": k.is_active,
        "created_at": k.created_at.isoformat() if k.created_at else None,
        "key_preview": f"{k.key_value[:8]}..." if len(k.key_value) > 8 else k.key_value
    } for k in keys]

@app.post("/api-keys")
async def create_api_key(api_key: APIKeyCreate, db: SessionLocal = Depends(get_db)):
    db_key = APIKey(**api_key.dict())
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return {"id": db_key.id, "name": db_key.name, "message": "API key created successfully"}

@app.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: int, db: SessionLocal = Depends(get_db)):
    db_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not db_key:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(db_key)
    db.commit()
    return {"message": "API key deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
