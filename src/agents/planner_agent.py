import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.models.task import Subtask, TaskStatus

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    """
    Agent responsible for analyzing task complexity and generating an execution plan.
    This agent creates a detailed breakdown of subtasks with dependencies.
    """
    
    async def execute(self, subtask: Subtask, context: Dict[str, Any]) -> Subtask:
        """
        Execute the planning process for a task.
        
        Args:
            subtask: The planning subtask to execute
            context: The task context including the original task description
            
        Returns:
            Updated subtask with planning results
        """
        logger.info(f"PlannerAgent executing subtask {subtask.id}")
        
        # Update subtask status
        subtask.status = TaskStatus.IN_PROGRESS
        subtask.progress = 0.2
        subtask.updated_at = datetime.utcnow()
        
        try:
            # Extract task description from context
            task_description = context.get('task', '')
            if not task_description:
                raise ValueError("No task description provided in context")
            
            # Analyze task complexity and generate execution plan
            execution_plan = await self._analyze_task(task_description)
            
            # Format the result
            result = self._format_execution_plan(execution_plan)
            
            # Update subtask with result
            subtask.result = result
            subtask.status = TaskStatus.COMPLETED
            subtask.progress = 1.0
            
        except Exception as e:
            logger.error(f"Error in PlannerAgent: {str(e)}")
            subtask.status = TaskStatus.FAILED
            subtask.error = f"Planning failed: {str(e)}"
            subtask.progress = 0.0
        
        subtask.updated_at = datetime.utcnow()
        return subtask
    
    async def _analyze_task(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze the task description and determine required subtasks and their dependencies.
        
        Args:
            task_description: The natural language task description
            
        Returns:
            A dictionary containing the execution plan
        """
        # Simulate analysis time
        await asyncio.sleep(1)
        
        # Initialize execution plan
        execution_plan = {
            "complexity": "medium",
            "estimated_time": "10-15 minutes",
            "subtasks": []
        }
        
        # Determine required agent types based on task description
        if "research" in task_description.lower() or "find" in task_description.lower() or "search" in task_description.lower():
            execution_plan["subtasks"].append({
                "type": "web_research",
                "description": "Research information related to the task",
                "dependencies": [],
                "priority": 1
            })
        
        if "analyze" in task_description.lower() or "data" in task_description.lower() or "statistics" in task_description.lower():
            execution_plan["subtasks"].append({
                "type": "data_analysis",
                "description": "Analyze data related to the task",
                "dependencies": ["web_research"] if "research" in task_description.lower() else [],
                "priority": 2 if "research" in task_description.lower() else 1
            })
        
        if "code" in task_description.lower() or "program" in task_description.lower() or "script" in task_description.lower():
            execution_plan["subtasks"].append({
                "type": "code_generation",
                "description": "Generate code based on task requirements",
                "dependencies": ["data_analysis"] if "analyze" in task_description.lower() else [],
                "priority": 3 if "analyze" in task_description.lower() else 1
            })
        
        if "write" in task_description.lower() or "create" in task_description.lower() or "generate" in task_description.lower() or "summarize" in task_description.lower():
            execution_plan["subtasks"].append({
                "type": "content_creation",
                "description": "Create content based on task requirements",
                "dependencies": ["web_research", "data_analysis", "code_generation"],
                "priority": 4
            })
        
        # If no specific subtasks were identified, add a general task execution
        if not execution_plan["subtasks"]:
            execution_plan["subtasks"].append({
                "type": "general_execution",
                "description": "Execute the general task",
                "dependencies": [],
                "priority": 1
            })
        
        # Add orchestration subtask to combine results
        execution_plan["subtasks"].append({
            "type": "result_orchestration",
            "description": "Combine results from all subtasks",
            "dependencies": [st["type"] for st in execution_plan["subtasks"]],
            "priority": 5
        })
        
        return execution_plan
    
    def _format_execution_plan(self, execution_plan: Dict[str, Any]) -> str:
        """
        Format the execution plan as a readable string.
        
        Args:
            execution_plan: The execution plan dictionary
            
        Returns:
            Formatted execution plan as a string
        """
        result = "# Task Execution Plan\n\n"
        
        result += f"**Complexity**: {execution_plan['complexity']}\n"
        result += f"**Estimated Time**: {execution_plan['estimated_time']}\n\n"
        
        result += "## Subtasks\n\n"
        
        # Sort subtasks by priority
        sorted_subtasks = sorted(execution_plan["subtasks"], key=lambda x: x["priority"])
        
        for i, subtask in enumerate(sorted_subtasks):
            result += f"### {i+1}. {subtask['type'].replace('_', ' ').title()}\n"
            result += f"- **Description**: {subtask['description']}\n"
            
            if subtask['dependencies']:
                result += "- **Dependencies**: " + ", ".join(dep.replace('_', ' ').title() for dep in subtask['dependencies']) + "\n"
            else:
                result += "- **Dependencies**: None\n"
                
            result += f"- **Priority**: {subtask['priority']}\n\n"
        
        return result
