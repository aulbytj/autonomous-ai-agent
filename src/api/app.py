from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import json
import asyncio
import os
import logging
import uuid
from datetime import datetime
from src.core.orchestrator import Orchestrator
from src.models.task import TaskRequest, TaskResponse, Subtask, TaskStatus, ExecutionLogEntry
from src.config.cors_config import get_cors_config
from src.config.environment import ENV_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper functions
def calculate_replay_duration(logs, speed):
    """Calculate the duration of a replay based on logs and speed."""
    if not logs or len(logs) < 2:
        return 0
    
    try:
        start_time = datetime.fromisoformat(logs[0].get('timestamp', ''))
        end_time = datetime.fromisoformat(logs[-1].get('timestamp', ''))
        duration_seconds = (end_time - start_time).total_seconds()
        return duration_seconds / speed
    except Exception as e:
        logger.error(f"Error calculating replay duration: {str(e)}")
        return 0

# Initialize FastAPI app
app = FastAPI()

# Configure CORS based on environment
cors_config = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["allow_origins"],
    allow_credentials=cors_config["allow_credentials"],
    allow_methods=cors_config["allow_methods"],
    allow_headers=cors_config["allow_headers"],
)

# Initialize orchestrator with Redis client
orchestrator = Orchestrator()

@app.post("/tasks/submit")
async def submit_task(request: TaskRequest):
    """Submit a new task to the orchestrator."""
    try:
        # Validate task
        if not await orchestrator.validate_task(request):
            raise HTTPException(status_code=400, detail="Invalid task")
            
        # Create task ID
        task_id = str(uuid.uuid4())
        
        # Plan task
        subtasks = await orchestrator.plan_task(request)
        
        # Create task response
        response = TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            subtasks=[st.dict() for st in subtasks]
        )
        
        # Store in Redis if available
        if orchestrator.redis:
            try:
                redis_expiration = ENV_CONFIG["redis_expiration_seconds"]
                
                # Store task response
                orchestrator.redis.set(f"task:{task_id}", json.dumps(response.dict()), ex=redis_expiration)
                
                # Store the original request for context
                orchestrator.redis.set(f"task_request:{task_id}", json.dumps(request.dict()), ex=redis_expiration)
                
                # Initialize empty logs
                orchestrator.redis.set(f"task_logs:{task_id}", json.dumps([]), ex=redis_expiration)
                
                logger.info(f"Task {task_id} data stored in Redis successfully")
            except Exception as redis_err:
                logger.error(f"Error storing task data in Redis: {str(redis_err)}")
                logger.warning("Continuing with task execution despite Redis storage failure")
        else:
            logger.warning(f"Redis unavailable, task {task_id} data will not be persisted")
        
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
        # Check if Redis is available
        if not orchestrator.redis:
            logger.error("Redis connection unavailable")
            raise HTTPException(status_code=503, detail="Storage service unavailable")
            
        # Get raw data from Redis
        try:
            task_data = orchestrator.redis.get(f"task:{task_id}")
            if not task_data:
                logger.error(f"Task {task_id} not found in Redis")
                raise HTTPException(status_code=404, detail="Task not found")
                
            # Convert bytes to string and parse JSON
            task_str = task_data.decode('utf-8')
            
            # Parse JSON
            try:
                task_dict = json.loads(task_str)
                logger.info(f"Task status for {task_id}: {task_dict}")
                return task_dict  # FastAPI will automatically convert this to JSON
            except json.JSONDecodeError as je:
                logger.error(f"Invalid JSON for task {task_id}: {je}")
                raise HTTPException(status_code=500, detail="Invalid task data")
        except redis.RedisError as re:
            logger.error(f"Redis error while fetching task {task_id}: {str(re)}")
            raise HTTPException(status_code=503, detail="Storage service error")
            
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    """Get execution logs for a task."""
    try:
        # Get logs from Redis
        logs_data = orchestrator.redis.get(f"task_logs:{task_id}")
        if not logs_data:
            logger.error(f"Logs for task {task_id} not found in Redis")
            return {"logs": []}
            
        # Convert bytes to string and parse JSON
        logs_str = logs_data.decode('utf-8')
        
        # Parse JSON
        try:
            logs = json.loads(logs_str)
            return {"logs": logs}
        except json.JSONDecodeError as je:
            logger.error(f"Invalid JSON for task logs {task_id}: {je}")
            raise HTTPException(status_code=500, detail="Invalid logs data")
            
    except Exception as e:
        logger.error(f"Error getting task logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}/replay")
async def get_task_replay(task_id: str, speed: float = Query(1.0, gt=0, le=10)):
    """Get task execution replay data with configurable speed."""
    try:
        # Get task data
        task_data = orchestrator.redis.get(f"task:{task_id}")
        if not task_data:
            logger.error(f"Task {task_id} not found in Redis")
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get logs data
        logs_data = orchestrator.redis.get(f"task_logs:{task_id}")
        if not logs_data:
            logger.error(f"Logs for task {task_id} not found in Redis")
            return {"replay": {"task": json.loads(task_data), "logs": [], "speed": speed}}
        
        # Parse data
        task = json.loads(task_data)
        logs = json.loads(logs_data)
        
        # Sort logs by timestamp
        sorted_logs = sorted(logs, key=lambda x: x.get('timestamp', ''))
        
        # Create replay data
        replay_data = {
            "task": task,
            "logs": sorted_logs,
            "speed": speed,
            "duration": calculate_replay_duration(sorted_logs, speed)
        }
        
        return {"replay": replay_data}
        
    except Exception as e:
        logger.error(f"Error getting task replay: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test/redis/{task_id}")
async def test_redis(task_id: str):
    """Test endpoint to directly access Redis data."""
    try:
        # Get raw data from Redis
        task_data = orchestrator.redis.get(f"task:{task_id}")
        if not task_data:
            return {"status": "error", "message": f"Task {task_id} not found in Redis"}
            
        # Convert bytes to string
        task_str = task_data.decode('utf-8')
        
        # Parse JSON
        try:
            task_dict = json.loads(task_str)
            return {"status": "success", "data": task_dict, "raw": task_str}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON", "raw": task_str}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/test/redis-keys")
async def test_redis_keys():
    """Test endpoint to list all task keys in Redis."""
    try:
        # List all keys in Redis
        keys = orchestrator.redis.keys("task:*")
        return {"status": "success", "keys": [key.decode('utf-8') for key in keys]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/tasks")
async def get_all_tasks():
    """Get a list of all tasks for task history."""
    try:
        # Check if Redis is available
        if not orchestrator.redis:
            logger.error("Redis unavailable for task history")
            raise HTTPException(status_code=503, detail="Storage service unavailable")
            
        # List all task keys in Redis
        keys = orchestrator.redis.keys("task:*")
        
        # Extract task IDs from keys
        task_ids = [key.decode('utf-8').replace('task:', '') for key in keys]
        
        logger.info(f"Found {len(task_ids)} tasks in history")
        return {"status": "success", "tasks": task_ids}
    except Exception as e:
        error_msg = f"Error fetching task history: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task and its associated data."""
    try:
        # Check if Redis is available
        if not orchestrator.redis:
            logger.error("Redis connection unavailable for task deletion")
            raise HTTPException(status_code=503, detail="Storage service unavailable")
            
        # Check if task exists
        task_key = f"task:{task_id}"
        if not orchestrator.redis.exists(task_key):
            raise HTTPException(status_code=404, detail="Task not found")
            
        # Delete task data
        orchestrator.redis.delete(task_key)
        orchestrator.redis.delete(f"task_request:{task_id}")
        orchestrator.redis.delete(f"task_logs:{task_id}")
        
        logger.info(f"Task {task_id} deleted successfully")
        return {"status": "success", "message": f"Task {task_id} deleted successfully"}
    except redis.RedisError as re:
        logger.error(f"Redis error deleting task {task_id}: {str(re)}")
        raise HTTPException(status_code=503, detail="Storage service error")
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint with service status."""
    # Check Redis connection
    redis_status = False
    try:
        if orchestrator.redis:
            orchestrator.redis.ping()
            redis_status = True
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
    
    # Return health status with service information
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": True,  # API is running if this endpoint is reachable
            "redis": redis_status
        },
        "environment": ENV_CONFIG["environment"]
    }

@app.post("/api/test-submit")
async def test_submit(request: dict):
    """Test endpoint for task submission."""
    try:
        logger.info(f"Received test submission: {request}")
        # Create a simple response with a random task ID
        task_id = str(uuid.uuid4())
        return {
            "status": "success",
            "task_id": task_id,
            "message": "Test task submission successful",
            "request_received": request
        }
    except Exception as e:
        logger.error(f"Error in test submission: {str(e)}")
        return {"status": "error", "message": str(e)}
@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task updates."""
    await websocket.accept()
    pubsub = None
    
    try:
        # Check if Redis is available
        if not orchestrator.redis:
            logger.error("Redis connection unavailable for WebSocket")
            await websocket.send_json({
                "error": "Storage service unavailable",
                "task_id": task_id,
                "status": "ERROR"
            })
            return
        
        try:
            # Initial status
            task_data = orchestrator.redis.get(f"task:{task_id}")
            if task_data:
                await websocket.send_text(task_data.decode('utf-8'))
            else:
                await websocket.send_json({
                    "warning": "Task not found",
                    "task_id": task_id,
                    "status": "NOT_FOUND"
                })
            
            # Subscribe to task updates
            pubsub = orchestrator.redis.pubsub()
            pubsub.subscribe(f"task_updates:{task_id}")
            
            # Listen for updates
            while True:
                try:
                    message = pubsub.get_message(timeout=1.0)
                    if message and message['type'] == 'message':
                        data = message['data'].decode('utf-8')
                        await websocket.send_text(data)
                        
                        # Check if task is completed or failed
                        try:
                            task_dict = json.loads(data)
                            if task_dict.get('status') in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                                break
                        except json.JSONDecodeError:
                            pass
                except redis.RedisError as re:
                    logger.error(f"Redis error during WebSocket updates: {str(re)}")
                    await websocket.send_json({
                        "error": "Storage service error",
                        "task_id": task_id,
                        "status": "ERROR"
                    })
                    break
                    
                # Check if client is still connected
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                except asyncio.TimeoutError:
                    pass  # No message from client, continue
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for task {task_id}")
                    break
        except redis.RedisError as re:
            logger.error(f"Redis error initializing WebSocket: {str(re)}")
            await websocket.send_json({
                "error": "Storage service error",
                "task_id": task_id,
                "status": "ERROR"
            })
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "error": f"WebSocket error: {str(e)}",
                "task_id": task_id,
                "status": "ERROR"
            })
        except:
            pass
    finally:
        # Unsubscribe and close
        if pubsub:
            try:
                pubsub.unsubscribe(f"task_updates:{task_id}")
                pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub: {str(e)}")

@app.websocket("/ws/{task_id}/logs")
async def logs_websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task logs."""
    await websocket.accept()
    pubsub = None
    
    try:
        # Check if Redis is available
        if not orchestrator.redis:
            logger.error("Redis connection unavailable for WebSocket logs")
            await websocket.send_json({
                "error": "Storage service unavailable",
                "task_id": task_id,
                "status": "ERROR"
            })
            return
        
        try:
            # Initial logs
            logs_data = orchestrator.redis.get(f"task_logs:{task_id}")
            if logs_data:
                logs = json.loads(logs_data.decode('utf-8'))
                await websocket.send_json({"logs": logs})
                last_log_count = len(logs)
            else:
                await websocket.send_json({
                    "warning": "Task logs not found",
                    "task_id": task_id,
                    "status": "NOT_FOUND"
                })
                last_log_count = 0
            
            # Subscribe to log updates
            pubsub = orchestrator.redis.pubsub()
            pubsub.subscribe(f"task_logs:{task_id}")
            
            # Listen for updates
            while True:
                try:
                    # Check for new messages
                    message = pubsub.get_message(timeout=1.0)
                    if message and message['type'] == 'message':
                        data = message['data'].decode('utf-8')
                        logs = json.loads(data)
                        
                        # Only send if there are new logs
                        if len(logs) > last_log_count:
                            # Send only the new logs
                            new_logs = logs[last_log_count:]
                            await websocket.send_json({"new_logs": new_logs})
                            last_log_count = len(logs)
                    
                    # Check if task is completed or failed
                    task_data = orchestrator.redis.get(f"task:{task_id}")
                    if task_data:
                        try:
                            task_dict = json.loads(task_data.decode('utf-8'))
                            if task_dict.get('status') in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                                # Send one final update
                                logs_data = orchestrator.redis.get(f"task_logs:{task_id}")
                                if logs_data:
                                    logs = json.loads(logs_data.decode('utf-8'))
                                    if len(logs) > last_log_count:
                                        new_logs = logs[last_log_count:]
                                        await websocket.send_json({"new_logs": new_logs})
                                break
                        except json.JSONDecodeError:
                            pass
                except redis.RedisError as re:
                    logger.error(f"Redis error during WebSocket logs updates: {str(re)}")
                    await websocket.send_json({
                        "error": "Storage service error",
                        "task_id": task_id,
                        "status": "ERROR"
                    })
                    break
                    
                # Check if client is still connected
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                except asyncio.TimeoutError:
                    pass  # No message from client, continue
                except WebSocketDisconnect:
                    logger.info(f"WebSocket logs disconnected for task {task_id}")
                    break
        except redis.RedisError as re:
            logger.error(f"Redis error initializing WebSocket logs: {str(re)}")
            await websocket.send_json({
                "error": "Storage service error",
                "task_id": task_id,
                "status": "ERROR"
            })
                
    except Exception as e:
        logger.error(f"WebSocket logs error: {str(e)}")
        try:
            await websocket.send_json({
                "error": f"WebSocket logs error: {str(e)}",
                "task_id": task_id,
                "status": "ERROR"
            })
        except:
            pass
    finally:
        # Unsubscribe and close
        if pubsub:
            try:
                pubsub.unsubscribe(f"task_logs:{task_id}")
                pubsub.close()
            except Exception as e:
                logger.error(f"Error closing logs pubsub: {str(e)}")

@app.websocket("/ws/{task_id}/replay")
async def replay_websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for task execution replay."""
    await websocket.accept()
    
    try:
        # Check if Redis is available
        if not orchestrator.redis:
            logger.error("Redis connection unavailable for WebSocket replay")
            await websocket.send_json({
                "error": "Storage service unavailable",
                "task_id": task_id,
                "status": "ERROR"
            })
            return
        
        try:
            # Get task logs
            logs_data = orchestrator.redis.get(f"task_logs:{task_id}")
            if not logs_data:
                await websocket.send_json({"error": "No logs found for replay", "task_id": task_id})
                return
                
            # Parse logs
            logs = json.loads(logs_data.decode('utf-8'))
            
            # Get replay speed (default: 1x)
            speed = 1.0
            
            # Send initial state
            await websocket.send_json({"type": "replay_start", "total_events": len(logs)})
            
            # Replay logs with timing
            for i, log in enumerate(logs):
                # Send event
                await websocket.send_json({
                    "type": "replay_event",
                    "event": log,
                    "index": i,
                    "total": len(logs)
                })
                
                # Wait for next event (simulate original timing)
                if i < len(logs) - 1:
                    try:
                        # Calculate time difference between events
                        current_time = datetime.fromisoformat(log["timestamp"].replace('Z', '+00:00'))
                        next_time = datetime.fromisoformat(logs[i+1]["timestamp"].replace('Z', '+00:00'))
                        
                        # Calculate delay, but cap it to avoid long waits
                        delay = (next_time - current_time).total_seconds() / speed
                        delay = min(delay, 2.0)  # Cap at 2 seconds
                        
                        # Wait
                        await asyncio.sleep(delay)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error calculating replay timing: {str(e)}")
                        await asyncio.sleep(0.5)  # Default delay if timing calculation fails
                
                # Check for control messages from client
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                    
                    # Handle control messages
                    if data.get("command") == "pause":
                        # Wait for resume
                        while True:
                            try:
                                cmd = await asyncio.wait_for(websocket.receive_json(), timeout=None)
                                if cmd.get("command") == "resume":
                                    break
                                elif cmd.get("command") == "speed":
                                    speed = float(cmd.get("value", 1.0))
                            except Exception:
                                break
                    elif data.get("command") == "speed":
                        speed = float(data.get("value", 1.0))
                        
                except asyncio.TimeoutError:
                    pass  # No control message, continue
                except WebSocketDisconnect:
                    logger.info(f"Replay WebSocket disconnected for task {task_id}")
                    return
            
            # Send completion
            await websocket.send_json({"type": "replay_complete"})
        except redis.RedisError as re:
            logger.error(f"Redis error during replay: {str(re)}")
            await websocket.send_json({
                "error": "Storage service error during replay",
                "task_id": task_id,
                "status": "ERROR"
            })
            
    except Exception as e:
        logger.error(f"Replay WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"error": str(e), "task_id": task_id})
        except:
            pass
