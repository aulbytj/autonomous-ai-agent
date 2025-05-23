import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI()

class TaskRequest(BaseModel):
    task: str
    context: dict = {}

class TaskResponse(BaseModel):
    result: str
    status: str

# Context7 MCP implementation
class Context7MCP:
    def __init__(self):
        self.context = {}
        
    def process_task(self, task: str, context: dict) -> str:
        # Process the task with context
        response = f"Processing task: {task}\n"
        
        # Analyze context
        if context:
            response += "Context analysis:\n"
            for key, value in context.items():
                response += f"- {key}: {value}\n"
        
        # Add basic task analysis
        response += "\nTask analysis:\n"
        if "code" in context:
            code = context["code"]
            response += f"- Code analysis: {self.analyze_code(code)}\n"
        
        return response
    
    def analyze_code(self, code: str) -> str:
        # Basic code analysis
        analysis = []
        if "def" in code:
            analysis.append("Function definition detected")
        if "return" in code:
            analysis.append("Return statement found")
        if len(code.split()) < 10:
            analysis.append("Function is very concise")
        
        return ", ".join(analysis)

@app.post("/tasks/execute")
async def execute_task(request: TaskRequest):
    try:
        # Initialize Context7 MCP
        mcp = Context7MCP()
        
        # Process the task
        result = mcp.process_task(request.task, request.context)
        
        return TaskResponse(
            result=result,
            status="success"
        )
    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)
