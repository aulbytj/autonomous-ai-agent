# Autonomous AI Agent MCP

A FastAPI-based Mission Control Program (MCP) that analyzes tasks and context.

## Features

- Task processing and analysis
- Context analysis
- Basic code analysis
- FastAPI REST API

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python mcp.py
```

3. Make requests to the API:
```bash
curl -X POST http://localhost:8091/tasks/execute \
-H "Content-Type: application/json" \
-d '{"task": "Your task here", "context": {"key": "value"}}'
```

The server will run on http://localhost:8000

## API Endpoints

### Execute Task
- POST `/tasks/execute`
- Body: JSON with `task` and optional `context`
- Response: Task result and status

## Example Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/tasks/execute",
    json={
        "task": "Analyze this code and suggest improvements",
        "context": {
            "code": "def add(a, b): return a + b"
        }
    }
)
print(response.json())
```

## Requirements
- Python 3.8+
- Anthropic API key
- Claude 3 Sonnet model access
