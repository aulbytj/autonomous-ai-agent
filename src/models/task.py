from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import json

class SubtaskDependency(BaseModel):
    """Represents a dependency on another subtask."""
    subtask_id: str
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ExecutionLogEntry(BaseModel):
    """Represents a log entry for task execution."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    subtask_id: Optional[str] = None
    subtask_type: Optional[str] = None
    action: str  # e.g., 'started', 'completed', 'failed'
    details: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class Subtask(BaseModel):
    id: str
    type: str
    status: str
    description: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    progress: float = 0.0
    dependencies: Optional[List[SubtaskDependency]] = None
    container_id: Optional[str] = None  # For container isolation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        
    def dict(self, **kwargs):
        # Get the dict representation
        d = super().dict(**kwargs)
        # Convert datetime objects to ISO format strings
        if 'created_at' in d and isinstance(d['created_at'], datetime):
            d['created_at'] = d['created_at'].isoformat()
        if 'updated_at' in d and isinstance(d['updated_at'], datetime):
            d['updated_at'] = d['updated_at'].isoformat()
        return d

class TaskRequest(BaseModel):
    task: str
    context: Dict[str, Any] = {}
    priority: int = 1
    agent_type: Optional[str] = None

    model_config = {
        "arbitrary_types_allowed": True
    }

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[str] = None
    error: Optional[str] = None
    progress: float = 0.0
    subtasks: List[Subtask]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        
    def dict(self, **kwargs):
        # Get the dict representation
        d = super().dict(**kwargs)
        # Convert datetime objects to ISO format strings
        if 'created_at' in d and isinstance(d['created_at'], datetime):
            d['created_at'] = d['created_at'].isoformat()
        if 'updated_at' in d and isinstance(d['updated_at'], datetime):
            d['updated_at'] = d['updated_at'].isoformat()
        # Convert subtasks
        if 'subtasks' in d:
            for subtask in d['subtasks']:
                if 'created_at' in subtask and isinstance(subtask['created_at'], datetime):
                    subtask['created_at'] = subtask['created_at'].isoformat()
                if 'updated_at' in subtask and isinstance(subtask['updated_at'], datetime):
                    subtask['updated_at'] = subtask['updated_at'].isoformat()
        return d
