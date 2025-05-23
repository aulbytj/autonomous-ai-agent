import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from src.models.task import Subtask

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agent implementations."""
    
    def __init__(self):
        self.name = self.__class__.__name__
        
    @abstractmethod
    async def execute(self, subtask: Subtask, context: Dict[str, Any] = None) -> Subtask:
        """
        Execute the agent's specific task.
        
        Args:
            subtask: The subtask to execute
            context: Additional context for task execution
            
        Returns:
            Updated subtask with results
        """
        pass
    
    async def update_progress(self, subtask: Subtask, progress: float, 
                             result: Optional[str] = None, 
                             error: Optional[str] = None) -> Subtask:
        """
        Update the subtask progress.
        
        Args:
            subtask: The subtask to update
            progress: Progress value between 0.0 and 1.0
            result: Optional result string
            error: Optional error message
            
        Returns:
            Updated subtask
        """
        subtask.progress = max(0.0, min(1.0, progress))  # Clamp between 0 and 1
        subtask.updated_at = datetime.utcnow()
        
        if result is not None:
            subtask.result = result
            
        if error is not None:
            subtask.error = error
            
        return subtask
    
    def __str__(self):
        return f"{self.name} Agent"
