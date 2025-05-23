import redis
import uvicorn
import uuid
import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List, Any

from src.models.task import TaskRequest, TaskResponse, Subtask, TaskStatus
from src.core.orchestrator import Orchestrator
from src.utils import json_utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator with Redis client
orchestrator = Orchestrator()

@app.get("/")
async def root():
    return {"message": "Autonomous AI Agent is running"}

@app.post("/tasks/submit")
async def submit_task(request: TaskRequest):
    """Submit a new task to the orchestrator."""
    try:
        # Validate task
        is_valid = await orchestrator.validate_task(request)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid task request")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Plan task execution
        subtasks = await orchestrator.plan_task(request)
        
        if not subtasks:
            raise HTTPException(status_code=400, detail="Could not plan task execution")
        
        # Create task response
        response = TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            subtasks=subtasks
        )
        
        # Store task response in Redis with expiration (7 days)
        orchestrator.redis.set(f"task:{task_id}", json_utils.dumps(response.dict()), ex=604800)  # 7 days
        
        # Store original task request for context
        orchestrator.redis.set(f"task_request:{task_id}", json_utils.dumps(request.dict()), ex=604800)  # 7 days
        
        # Add to queue
        orchestrator.task_queue.append(task_id)
        
        # Start execution
        asyncio.create_task(orchestrator.execute_task(task_id))
        
        logger.info(f"Task {task_id} submitted with {len(subtasks)} subtasks")
        return response
        
    except Exception as e:
        error_msg = f"Error submitting task: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status by ID."""
    try:
        # Get raw data from Redis
        task_data = orchestrator.redis.get(f"task:{task_id}")
        if not task_data:
            logger.error(f"Task {task_id} not found in Redis")
            raise HTTPException(status_code=404, detail="Task not found")
            
        # Convert bytes to string and parse JSON
        task_str = task_data.decode('utf-8')
        
        # Parse JSON
        try:
            task_dict = json_utils.loads(task_str)
            logger.info(f"Task status for {task_id}: {task_dict}")
            return task_dict  # FastAPI will automatically convert this to JSON
        except json.JSONDecodeError as je:
            logger.error(f"Invalid JSON for task {task_id}: {je}")
            raise HTTPException(status_code=500, detail="Invalid task data")
            
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test/redis-keys")
async def test_redis_keys():
    """Test endpoint to list all task keys in Redis."""
    try:
        # List all keys in Redis
        keys = orchestrator.redis.keys("task:*")
        return {"status": "success", "keys": [key.decode('utf-8') for key in keys]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task updates."""
    await websocket.accept()
    try:
        # Check if task exists
        task_data = orchestrator.redis.get(f"task:{task_id}")
        if not task_data:
            await websocket.send_json({"error": "Task not found"})
            await websocket.close()
            return
            
        # Send initial task state
        await websocket.send_text(task_data.decode('utf-8'))
        
        # Keep connection open for updates
        while True:
            await asyncio.sleep(1)  # Poll every second
            task_data = orchestrator.redis.get(f"task:{task_id}")
            if task_data:
                await websocket.send_text(task_data.decode('utf-8'))
            else:
                await websocket.send_json({"error": "Task not found"})
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket for task {task_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Autonomous AI Agent on port 8096...")
    uvicorn.run(app, host="0.0.0.0", port=8096)
