# Autonomous AI Agent

A powerful AI agent system that can execute complex tasks autonomously with parallel subtask execution, real-time progress tracking, and execution replay. The system features specialized agents for different task types, centralized configuration management, and robust error handling.

## Features

- Natural language task processing and analysis
- Intelligent task breakdown with the Planner Agent
- Specialized agents for different task types (Web Research, Data Analysis, Code Generation, Content Creation)
- Parallel execution of subtasks with dependency management
- Isolated execution in Docker containers with configurable resource limits
- Real-time progress tracking via WebSockets
- Task execution replay with playback controls
- Global dark/light theme with persistent user preferences
- Centralized configuration management for easy deployment
- Robust error handling and recovery

## Setup

### Backend Setup

1. Install backend dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (copy from example):
```bash
cp .env.example .env
```

3. Start Redis server (required for task storage and real-time updates):
```bash
redis-server
```

4. Run the backend server:
```bash
python standalone_server.py
```

The backend server will run on http://localhost:8098

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install frontend dependencies:
```bash
npm install
```

3. Run the frontend development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Task Execution Workflow

1. **Task Submission**: User submits a natural language task description via the UI or API
2. **Task Planning**: The Planner Agent analyzes the task and breaks it down into subtasks with dependencies
3. **Parallel Execution**: Subtasks are executed in parallel, respecting dependencies
4. **Real-time Updates**: Progress is streamed to the user via WebSockets
5. **Result Compilation**: Results from all subtasks are combined into a final result
6. **Execution Replay**: Users can replay the entire execution process with playback controls

## Container Isolation

The system supports executing agents in isolated Docker containers for security and resource management:

1. Set `USE_CONTAINERS=true` in your `.env` file to enable container isolation
2. Ensure Docker is installed and running on your system
3. The system will automatically create, manage, and clean up containers for each subtask

## API Endpoints

### Submit Task
- POST `/tasks/submit`
- Body: JSON with `task` and optional `context`
- Response: Task ID and initial status

### Get Task Status
- GET `/tasks/{task_id}`
- Response: Current task status, progress, and results

### Get Task Logs
- GET `/tasks/{task_id}/logs`
- Response: Execution logs for the task

### Get Task Replay
- GET `/tasks/{task_id}/replay?speed={speed}`
- Response: Replay data for task execution visualization

### WebSocket Endpoints
- `/ws/{task_id}` - Real-time task status updates
- `/ws/{task_id}/logs` - Real-time task logs
- `/ws/{task_id}/replay` - Task execution replay stream

## Configuration

The system uses a centralized configuration approach with environment variables:

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Customize the configuration for your environment:
```
# General Configuration
ENVIRONMENT=development  # Options: development, production
DEBUG=true

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_EXPIRATION_SECONDS=604800  # 7 days

# Container Configuration
USE_CONTAINERS=false
CONTAINER_MEMORY_LIMIT=512m
CONTAINER_CPU_QUOTA=50000  # 50% of CPU

# API Configuration
API_HOST=0.0.0.0
API_PORT=8098

# CORS Configuration (for production)
ALLOWED_ORIGINS=https://your-domain.com
```

## Example Usage

### Python API Client

```python
import requests

# Submit a new task
response = requests.post(
    "http://localhost:8096/tasks/submit",
    json={
        "task": "Research the latest advancements in quantum computing and summarize them",
        "context": {
            "priority": 1,
            "max_depth": 3
        }
    }
)

task_id = response.json()["task_id"]
print(f"Task submitted with ID: {task_id}")

# Get task status
status_response = requests.get(f"http://localhost:8096/tasks/{task_id}")
print(status_response.json())

# Get task logs
logs_response = requests.get(f"http://localhost:8096/tasks/{task_id}/logs")
print(logs_response.json())
```

### WebSocket Client

```javascript
// Connect to real-time task updates
const socket = new WebSocket(`ws://localhost:8096/ws/${taskId}`);

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Task update:', data);
  // Update UI with task status
};
```

## Requirements

### Backend
- Python 3.8+
- Redis server
- Docker (optional, for container isolation)

### Frontend
- Node.js 16+
- npm or yarn

## Architecture

The system is built with a modular architecture:

- **Frontend**: Next.js React application with real-time WebSocket connections
  - Global theme context for consistent dark/light mode across components
  - Centralized API service with unified error handling
  - Responsive UI with playback controls for task execution replay

- **Backend**: FastAPI Python server with async task processing
  - Environment-specific CORS configuration for security
  - Centralized configuration management via environment variables
  - Robust error handling and logging

- **Agents**: Specialized AI agents for different task types
  - PlannerAgent: Analyzes tasks and creates execution plans
  - WebResearchAgent: Gathers information from the web
  - DataAnalysisAgent: Processes and analyzes data
  - CodeGenerationAgent: Generates code solutions
  - ContentCreationAgent: Creates written content

- **Orchestrator**: Manages task planning and execution
  - Parallel subtask execution with dependency resolution
  - Progress tracking and reporting
  - Result compilation and summarization

- **Container Manager**: Handles isolated execution in Docker containers
  - Configurable resource limits (memory, CPU)
  - Secure isolation of agent execution
  - Automatic cleanup of container resources

- **Storage**: Redis for task data and execution logs
  - Configurable expiration for task data
  - Real-time data streaming via WebSockets
