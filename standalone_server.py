import redis
import json
import uvicorn
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

# Create a simple FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],
)

# Connect to Redis
redis_client = redis.from_url("redis://localhost:6379")

@app.get("/")
async def root():
    return {"message": "Standalone server is running"}

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    try:
        # Get raw data from Redis
        task_data = redis_client.get(f"task:{task_id}")
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")
            
        # Convert bytes to string and parse JSON
        task_dict = json.loads(task_data.decode('utf-8'))
        return task_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/keys")
async def get_keys():
    keys = redis_client.keys("task:*")
    return {"keys": [key.decode('utf-8') for key in keys]}

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint to verify API connectivity."""
    return {"status": "ok", "message": "API is running"}


# Task models
class TaskStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskRequest(BaseModel):
    task: str
    context: Dict[str, Any] = {}

class Subtask(BaseModel):
    id: str
    type: str
    description: str = ""
    status: str = TaskStatus.PENDING
    progress: float = 0.0
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = datetime.utcnow().isoformat()
    updated_at: str = datetime.utcnow().isoformat()

class TaskResponse(BaseModel):
    task_id: str
    status: str = TaskStatus.PENDING
    progress: float = 0.0
    result: Optional[str] = None
    error: Optional[str] = None
    subtasks: List[Subtask] = []
    created_at: str = datetime.utcnow().isoformat()
    updated_at: str = datetime.utcnow().isoformat()


@app.post("/tasks/submit")
async def submit_task(request: TaskRequest):
    """Submit a new task."""
    try:
        # Create task ID
        task_id = str(uuid.uuid4())
        
        # Create subtasks (simplified for standalone server)
        subtasks = [
            Subtask(
                id=str(uuid.uuid4()),
                type="research",
                description="Research information related to the task"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                type="analysis",
                description="Analyze the task requirements"
            ),
            Subtask(
                id=str(uuid.uuid4()),
                type="execution",
                description="Execute the task"
            )
        ]
        
        # Create task response
        response = TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            subtasks=subtasks
        )
        
        # Store in Redis with expiration (7 days)
        redis_client.set(f"task:{task_id}", json.dumps(response.dict()), ex=604800)  # 7 days
        
        # Store the original request for context
        redis_client.set(f"task_request:{task_id}", json.dumps(request.dict()), ex=604800)  # 7 days
        
        # Initialize empty logs
        redis_client.set(f"task_logs:{task_id}", json.dumps([]), ex=604800)  # 7 days
        
        # Simulate task execution (in a real system, this would be done asynchronously)
        # For this standalone server, we'll just update the task status after a delay
        import threading
        def update_task_status():
            import time
            import random
            
            # Update task to in progress
            task_data = redis_client.get(f"task:{task_id}")
            task_dict = json.loads(task_data.decode('utf-8'))
            task_dict['status'] = TaskStatus.IN_PROGRESS
            redis_client.set(f"task:{task_id}", json.dumps(task_dict), ex=604800)
            
            # Add log entry for task start
            logs = [{
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'task_started',
                'details': 'Task execution started'
            }]
            redis_client.set(f"task_logs:{task_id}", json.dumps(logs), ex=604800)
            
            # Update subtasks one by one
            for i, subtask in enumerate(task_dict['subtasks']):
                # Update subtask to in progress
                subtask['status'] = TaskStatus.IN_PROGRESS
                task_dict['subtasks'][i] = subtask
                redis_client.set(f"task:{task_id}", json.dumps(task_dict), ex=604800)
                
                # Add log entry for subtask start
                logs.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'subtask_id': subtask['id'],
                    'subtask_type': subtask['type'],
                    'action': 'started',
                    'details': f"Executing {subtask['type']} subtask"
                })
                redis_client.set(f"task_logs:{task_id}", json.dumps(logs), ex=604800)
                
                # Simulate work
                time.sleep(random.uniform(1, 3))
                
                # Update subtask progress
                for progress in [0.25, 0.5, 0.75, 1.0]:
                    subtask['progress'] = progress
                    task_dict['subtasks'][i] = subtask
                    redis_client.set(f"task:{task_id}", json.dumps(task_dict), ex=604800)
                    
                    # Add log entry for progress update
                    logs.append({
                        'timestamp': datetime.utcnow().isoformat(),
                        'subtask_id': subtask['id'],
                        'subtask_type': subtask['type'],
                        'action': 'progress',
                        'details': f"Progress: {int(progress * 100)}%"
                    })
                    redis_client.set(f"task_logs:{task_id}", json.dumps(logs), ex=604800)
                    
                    time.sleep(random.uniform(0.5, 1.5))
                
                # Complete the subtask
                subtask['status'] = TaskStatus.COMPLETED
                subtask['result'] = f"Completed {subtask['type']} with sample result"
                task_dict['subtasks'][i] = subtask
                redis_client.set(f"task:{task_id}", json.dumps(task_dict), ex=604800)
                
                # Add log entry for subtask completion
                logs.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'subtask_id': subtask['id'],
                    'subtask_type': subtask['type'],
                    'action': 'completed',
                    'details': f"Completed {subtask['type']} subtask"
                })
                redis_client.set(f"task_logs:{task_id}", json.dumps(logs), ex=604800)
                
                # Update overall task progress
                task_dict['progress'] = (i + 1) / len(task_dict['subtasks'])
                redis_client.set(f"task:{task_id}", json.dumps(task_dict), ex=604800)
            
            # Complete the task
            task_dict['status'] = TaskStatus.COMPLETED
            task_dict['result'] = "Task completed successfully with sample results"
            redis_client.set(f"task:{task_id}", json.dumps(task_dict), ex=604800)
            
            # Add log entry for task completion
            logs.append({
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'task_completed',
                'details': 'All subtasks completed successfully'
            })
            redis_client.set(f"task_logs:{task_id}", json.dumps(logs), ex=604800)
        
        # Start the background thread to update task status
        thread = threading.Thread(target=update_task_status)
        thread.daemon = True
        thread.start()
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    """Get execution logs for a task."""
    try:
        # Get logs from Redis
        logs_data = redis_client.get(f"task_logs:{task_id}")
        if not logs_data:
            return {"logs": []}
            
        logs = json.loads(logs_data.decode('utf-8'))
        return {"logs": logs}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}/replay")
async def get_task_replay(task_id: str, speed: float = Query(1.0, gt=0, le=10)):
    """Get task execution replay data."""
    try:
        # Get task data
        task_data = redis_client.get(f"task:{task_id}")
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")
            
        task = json.loads(task_data.decode('utf-8'))
        
        # Get logs
        logs_data = redis_client.get(f"task_logs:{task_id}")
        if not logs_data:
            logs = []
        else:
            logs = json.loads(logs_data.decode('utf-8'))
        
        # Calculate duration based on logs
        duration = 0
        if len(logs) >= 2:
            try:
                start_time = datetime.fromisoformat(logs[0].get('timestamp', ''))
                end_time = datetime.fromisoformat(logs[-1].get('timestamp', ''))
                duration = (end_time - start_time).total_seconds() / speed
            except:
                duration = len(logs) * 2  # Fallback duration
        
        return {
            "replay": {
                "task": task,
                "logs": logs,
                "speed": speed,
                "duration": duration
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task updates."""
    await websocket.accept()
    
    try:
        while True:
            # Get task from Redis
            task_data = redis_client.get(f"task:{task_id}")
            if task_data:
                task = json.loads(task_data.decode('utf-8'))
                await websocket.send_json(task)
            
            # Wait before sending the next update
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {str(e)}")


@app.websocket("/ws/{task_id}/logs")
async def logs_websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task logs updates."""
    await websocket.accept()
    
    try:
        last_log_count = 0
        
        while True:
            # Get logs from Redis
            logs_data = redis_client.get(f"task_logs:{task_id}")
            if logs_data:
                logs = json.loads(logs_data.decode('utf-8'))
                
                # Only send if there are new logs
                if len(logs) > last_log_count:
                    # Send only the new logs
                    new_logs = logs[last_log_count:]
                    await websocket.send_json({"new_logs": new_logs})
                    last_log_count = len(logs)
            
            # Wait before checking for new logs
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Logs WebSocket error: {str(e)}")


@app.websocket("/ws/{task_id}/replay")
async def replay_websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for task execution replay."""
    await websocket.accept()
    
    try:
        # Get initial message from client with replay settings
        settings = await websocket.receive_json()
        speed = float(settings.get("speed", 1.0))
        
        # Get logs from Redis
        logs_data = redis_client.get(f"task_logs:{task_id}")
        if not logs_data:
            await websocket.send_json({"error": "No logs available for replay"})
            return
            
        logs = json.loads(logs_data.decode('utf-8'))
        sorted_logs = sorted(logs, key=lambda x: x.get('timestamp', ''))
        
        # Send initial task state
        task_data = redis_client.get(f"task:{task_id}")
        if task_data:
            await websocket.send_json({"type": "task_initial", "data": json.loads(task_data.decode('utf-8'))})
        
        # Send logs with appropriate timing
        if sorted_logs:
            base_time = datetime.fromisoformat(sorted_logs[0].get('timestamp', datetime.utcnow().isoformat()))
            
            for i, log in enumerate(sorted_logs):
                # Calculate delay
                if i > 0 and 'timestamp' in log:
                    current_time = datetime.fromisoformat(log['timestamp'])
                    prev_time = datetime.fromisoformat(sorted_logs[i-1]['timestamp'])
                    delay = (current_time - prev_time).total_seconds() / speed
                    if delay > 0:
                        import asyncio
                        await asyncio.sleep(delay)
                
                # Send log entry
                await websocket.send_json({"type": "log_entry", "data": log})
                
                # Check if client wants to pause/stop
                try:
                    import asyncio
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                    if data.get("action") == "pause":
                        # Wait for resume command
                        while True:
                            cmd = await websocket.receive_json()
                            if cmd.get("action") == "resume":
                                break
                            elif cmd.get("action") == "stop":
                                return
                    elif data.get("action") == "stop":
                        return
                    elif data.get("action") == "set_speed":
                        speed = float(data.get("speed", speed))
                except:
                    pass
            
            # Send completion message
            await websocket.send_json({"type": "replay_complete"})
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Replay WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass

if __name__ == "__main__":
    print("Starting standalone server on port 8098...")
    uvicorn.run(app, host="0.0.0.0", port=8098)
