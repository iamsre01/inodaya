# Unified Agents Control Portal

A comprehensive platform for managing AI agents with visual graph representation, task scheduling, and API key management.

## Features

✅ **Agent Management**
- Create and manage multiple AI agents
- Support for both API-based and local model agents
- Activate/deactivate agents dynamically

✅ **Visual Graph View**
- Interactive network graph showing agent connections
- Real-time visualization of data flow between agents
- Color-coded status indicators (active/inactive)

✅ **Task Scheduling**
- Create tasks for agents with cron-based scheduling
- Manual task triggering on-demand
- Real-time task status monitoring (pending, running, completed, failed)
- View task execution history and results

✅ **Agent Connections**
- Define connections between agents (data flow, control signals, event triggers)
- Visual representation in the network graph
- Manage connection relationships

✅ **API Key Management**
- Securely store API keys for different providers (OpenAI, Anthropic, Google, etc.)
- Support for local model configurations
- Key activation/deactivation

## Architecture

```
unified-agents-portal/
├── backend/
│   ├── main.py          # FastAPI application with all endpoints
│   ├── models.py        # SQLAlchemy database models
│   └── agents.db        # SQLite database (created on first run)
└── frontend/
    └── index.html       # Single-page application with Tailwind CSS
```

## Quick Start

### 1. Start the Backend Server

```bash
cd /workspace/unified-agents-portal/backend
python main.py
```

The API server will start on `http://localhost:8000`

### 2. Open the Frontend

Open `frontend/index.html` in your browser, or serve it with a simple HTTP server:

```bash
cd /workspace/unified-agents-portal/frontend
python -m http.server 3000
```

Then navigate to `http://localhost:3000`

## API Endpoints

### Agents
- `GET /agents` - List all agents
- `POST /agents` - Create a new agent
- `GET /agents/{id}` - Get agent details
- `PUT /agents/{id}` - Update agent
- `DELETE /agents/{id}` - Delete agent

### Tasks
- `GET /tasks` - List all tasks
- `POST /tasks` - Create a new task (with optional cron schedule)
- `POST /tasks/{id}/trigger` - Manually trigger a task
- `DELETE /tasks/{id}` - Delete a task

### Connections
- `GET /connections` - List all agent connections
- `POST /connections` - Create a connection between agents
- `DELETE /connections/{id}` - Delete a connection

### Graph Visualization
- `GET /graph` - Get nodes and edges data for visualization

### API Keys
- `GET /api-keys` - List all API keys
- `POST /api-keys` - Add a new API key
- `DELETE /api-keys/{id}` - Delete an API key

## Usage Examples

### Create an Agent (via UI or API)

```json
POST /agents
{
  "name": "Research Agent",
  "description": "Performs web research",
  "agent_type": "api",
  "config": {
    "provider": "openai",
    "model": "gpt-4"
  }
}
```

### Create a Scheduled Task

```json
POST /tasks
{
  "name": "Daily Research",
  "description": "Run research every morning",
  "agent_id": 1,
  "schedule": "0 9 * * *"  // Every day at 9 AM
}
```

### Connect Agents

```json
POST /connections
{
  "source_agent_id": 1,
  "target_agent_id": 2,
  "connection_type": "data_flow",
  "description": "Research results flow to analysis agent"
}
```

## Technology Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy - Database ORM
- APScheduler - Task scheduling
- SQLite - Lightweight database

**Frontend:**
- Vanilla JavaScript - No framework dependencies
- Tailwind CSS - Styling via CDN
- Vis.js - Network graph visualization

## Customization

### Adding Local Model Support

Edit the `run_agent_task` function in `backend/main.py` to integrate with your local model:

```python
async def run_agent_task(agent: Agent, input_data: Dict[str, Any]) -> Dict[str, Any]:
    if agent.agent_type == "local_model":
        # Integrate with Ollama, LM Studio, or other local model servers
        response = await call_local_model(
            model=agent.config.get("model_name"),
            prompt=input_data.get("prompt")
        )
        return {"output": response}
```

### Extending Agent Capabilities

Add custom logic based on agent configuration in the `run_agent_task` function.

## License

MIT License - Feel free to use and modify for your projects!
