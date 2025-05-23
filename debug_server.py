import redis
import json
import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Create a simple FastAPI app for debugging
app = FastAPI()

# Connect to Redis
redis_client = redis.from_url("redis://localhost:6379")

@app.get("/")
async def root():
    return {"message": "Debug server is running"}

@app.get("/redis-keys")
async def get_redis_keys():
    try:
        # List all keys in Redis
        keys = redis_client.keys("task:*")
        return {"status": "success", "keys": [key.decode('utf-8') for key in keys]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/redis-get/{task_id}")
async def get_redis_data(task_id: str):
    try:
        # Get raw data from Redis
        task_data = redis_client.get(f"task:{task_id}")
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

if __name__ == "__main__":
    print("Starting debug server on port 8097...")
    uvicorn.run(app, host="0.0.0.0", port=8097)
