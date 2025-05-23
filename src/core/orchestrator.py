import uuid
import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any, Set
import redis
from datetime import datetime
from src.models.task import TaskRequest, TaskResponse, Subtask, TaskStatus, SubtaskDependency, ExecutionLogEntry
from src.utils import json_utils
from src.agents.agent_factory import AgentFactory
from src.utils.container_manager import ContainerManager
from src.config.environment import ENV_CONFIG

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, redis_url: str = None):
        # Use environment configuration
        self.redis_url = redis_url or ENV_CONFIG["redis_url"]
        
        # Initialize Redis with connection error handling
        try:
            self.redis = redis.from_url(self.redis_url)
            # Test the connection
            self.redis.ping()
            logger.info(f"Successfully connected to Redis at {self.redis_url}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis at {self.redis_url}: {str(e)}")
            logger.warning("Orchestrator will operate with limited functionality without Redis")
            self.redis = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {str(e)}")
            self.redis = None
            
        self.agent_factory = AgentFactory()
        self.use_containers = ENV_CONFIG["use_containers"]
        self.container_manager = ContainerManager() if self.use_containers else None
        self.redis_expiration = ENV_CONFIG["redis_expiration_seconds"]
        
        # Initialize agent pool
        self.agent_pool = {
            "web_research": 0,
            "code_generation": 0,
            "data_analysis": 0,
            "content_creation": 0
        }
        self.task_queue = []

    async def validate_task(self, task: TaskRequest) -> bool:
        """Validate task input and requirements."""
        # Basic validation
        if not task.task:
            logger.error("Task validation failed: Empty task description")
            return False
            
        # Check if Redis is available for task storage
        if not self.redis:
            logger.warning("Task validation warning: Redis unavailable, task progress may not be saved")
            # We still return True as the task can be executed even without Redis
            # The caller should handle the Redis unavailability appropriately
            
        # Check if the task description is too long
        if len(task.task) > 10000:  # Arbitrary limit to prevent abuse
            logger.error(f"Task validation failed: Task description too long ({len(task.task)} chars)")
            return False
            
        return True

    async def plan_task(self, task: TaskRequest) -> List[Subtask]:
        """Generate execution plan with sub-tasks using the PlannerAgent."""
        # Create a planning subtask
        planning_subtask = Subtask(
            id=str(uuid.uuid4()),
            type="planner",
            status=TaskStatus.PENDING,
            description="Analyze task complexity and generate execution plan"
        )
        
        # Execute the planning subtask
        planner_agent = self.agent_factory.get_agent("planner")
        if not planner_agent:
            logger.error("No planner agent available")
            return []
            
        # Create context for the planner
        context = {
            'task': task.task,
            'priority': task.priority,
            'context': task.context
        }
        
        # Execute planning
        updated_planning_subtask = await planner_agent.execute(planning_subtask, context)
        
        if updated_planning_subtask.status != TaskStatus.COMPLETED:
            logger.error(f"Planning failed: {updated_planning_subtask.error}")
            return [planning_subtask]
            
        # Parse the planning result to create subtasks
        subtasks = [planning_subtask]  # Include the planning subtask itself
        
        try:
            # Extract the execution plan from the planning result
            execution_plan_text = updated_planning_subtask.result
            
            # Parse the execution plan to identify subtasks
            # This is a simplified parsing of the markdown format produced by the planner
            subtask_types = []
            dependencies = {}
            
            for line in execution_plan_text.split('\n'):
                if line.startswith('### '):
                    # Extract subtask type from heading
                    parts = line.strip('# ').split('.')  # Split by period after number
                    if len(parts) > 1:
                        subtask_type = parts[1].strip().lower().replace(' ', '_')
                        subtask_types.append(subtask_type)
                elif '**Dependencies**:' in line and subtask_types:
                    # Extract dependencies for the current subtask
                    current_type = subtask_types[-1]
                    deps_part = line.split('**Dependencies**:')[1].strip()
                    if deps_part != 'None':
                        deps = [d.strip().lower().replace(' ', '_') for d in deps_part.split(',')]
                        dependencies[current_type] = deps
            
            # Create subtasks based on the execution plan
            subtask_ids = {}
            
            for subtask_type in subtask_types:
                if subtask_type != 'planner':  # Skip planner as we already created it
                    subtask_id = str(uuid.uuid4())
                    subtask = Subtask(
                        id=subtask_id,
                        type=subtask_type,
                        status=TaskStatus.PENDING,
                        description=f"Execute {subtask_type.replace('_', ' ')} task"
                    )
                    subtasks.append(subtask)
                    subtask_ids[subtask_type] = subtask_id
            
            # Add dependencies
            for subtask in subtasks:
                if subtask.type in dependencies:
                    subtask.dependencies = []
                    for dep_type in dependencies[subtask.type]:
                        if dep_type in subtask_ids:
                            subtask.dependencies.append(
                                SubtaskDependency(subtask_id=subtask_ids[dep_type])
                            )
        except Exception as e:
            logger.error(f"Error parsing planning result: {str(e)}")
            # If parsing fails, fall back to basic planning
            return self._basic_plan_task(task)
        
        return subtasks
        
    def _basic_plan_task(self, task: TaskRequest) -> List[Subtask]:
        """Fallback method for basic task planning without the planner agent."""
        subtasks = []
        
        # Add appropriate subtasks based on task type
        if "research" in task.task.lower():
            subtasks.append(Subtask(
                id=str(uuid.uuid4()),
                type="web_research",
                status=TaskStatus.PENDING,
                description="Research information related to the task"
            ))
        
        if "code" in task.task.lower():
            subtasks.append(Subtask(
                id=str(uuid.uuid4()),
                type="code_generation",
                status=TaskStatus.PENDING,
                description="Generate code based on task requirements"
            ))
        
        if "analyze" in task.task.lower():
            subtasks.append(Subtask(
                id=str(uuid.uuid4()),
                type="data_analysis",
                status=TaskStatus.PENDING,
                description="Analyze data related to the task"
            ))
        
        if "write" in task.task.lower():
            subtasks.append(Subtask(
                id=str(uuid.uuid4()),
                type="content_creation",
                status=TaskStatus.PENDING,
                description="Create content based on task requirements"
            ))
            
        if not subtasks:
            subtasks.append(Subtask(
                id=str(uuid.uuid4()),
                type="general_execution",
                status=TaskStatus.PENDING,
                description="Execute the general task"
            ))
        
        return subtasks

    async def execute_task(self, task_id: str):
        """Execute task with subtasks in parallel, respecting dependencies."""
        try:
            # Get task from Redis
            task_data = self.redis.get(f"task:{task_id}")
            if not task_data:
                logger.error(f"Task {task_id} not found in Redis")
                return
                
            task_dict = json_utils.loads(task_data)
            task = TaskResponse(**task_dict)
            task.subtasks = [Subtask(**st) for st in task_dict['subtasks']]
            
            # Update task status to in progress
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = datetime.utcnow()
            self.redis.set(f"task:{task_id}", json_utils.dumps(task.dict()), ex=604800)
            
            # Get the original task request for context
            task_request_data = self.redis.get(f"task_request:{task_id}")
            task_context = {}
            if task_request_data:
                task_request = json_utils.loads(task_request_data)
                task_context = task_request.get('context', {})
                task_context['task'] = task_request.get('task', '')
            
            # Store execution logs for replay
            execution_logs = []
            
            # Create a mapping of subtask IDs to subtasks for easier reference
            subtask_map = {subtask.id: subtask for subtask in task.subtasks}
            
            # Track completed and failed subtasks
            completed_subtasks = {}
            failed_subtasks = set()
            
            # Track which subtasks are ready to execute (no dependencies or all dependencies satisfied)
            ready_subtasks = []
            for subtask in task.subtasks:
                if subtask.status == TaskStatus.PENDING:
                    if not hasattr(subtask, 'dependencies') or not subtask.dependencies:
                        ready_subtasks.append(subtask)
            
            # Execute subtasks in parallel, respecting dependencies
            while ready_subtasks or any(st.status == TaskStatus.IN_PROGRESS for st in task.subtasks):
                # Start executing ready subtasks
                running_tasks = []
                for subtask in ready_subtasks:
                    # Check if this subtask has any dependencies that failed
                    has_failed_dependency = False
                    if hasattr(subtask, 'dependencies') and subtask.dependencies:
                        for dep in subtask.dependencies:
                            if dep.subtask_id in failed_subtasks:
                                has_failed_dependency = True
                                break
                    
                    if has_failed_dependency:
                        # Mark this subtask as failed due to dependency failure
                        subtask.status = TaskStatus.FAILED
                        subtask.error = "Dependency failed"
                        subtask.updated_at = datetime.utcnow()
                        failed_subtasks.add(subtask.id)
                        
                        # Log the failure
                        execution_logs.append({
                            'timestamp': datetime.utcnow().isoformat(),
                            'subtask_id': subtask.id,
                            'subtask_type': subtask.type,
                            'action': 'failed',
                            'details': 'Dependency failed'
                        })
                    else:
                        # Update context with results from completed subtasks
                        current_context = task_context.copy()
                        if completed_subtasks:
                            current_context['subtask_results'] = list(completed_subtasks.values())
                        
                        # Get the appropriate agent for this subtask type
                        agent = self.agent_factory.get_agent(subtask.type)
                        if not agent:
                            logger.error(f"No agent available for subtask type: {subtask.type}")
                            subtask.status = TaskStatus.FAILED
                            subtask.error = f"No agent available for type: {subtask.type}"
                            subtask.updated_at = datetime.utcnow()
                            failed_subtasks.add(subtask.id)
                            
                            # Log the failure
                            execution_logs.append({
                                'timestamp': datetime.utcnow().isoformat(),
                                'subtask_id': subtask.id,
                                'subtask_type': subtask.type,
                                'action': 'failed',
                                'details': 'No agent available'
                            })
                            continue
                        
                        # Mark as in progress
                        subtask.status = TaskStatus.IN_PROGRESS
                        subtask.updated_at = datetime.utcnow()
                        
                        # Log the start of execution
                        execution_logs.append({
                            'timestamp': datetime.utcnow().isoformat(),
                            'subtask_id': subtask.id,
                            'subtask_type': subtask.type,
                            'action': 'started',
                            'details': f"Executing with {agent.__class__.__name__}"
                        })
                        
                        # Start executing the subtask asynchronously
                        task_coroutine = self._execute_subtask(agent, subtask, current_context, execution_logs)
                        running_tasks.append(asyncio.create_task(task_coroutine))
                
                # Clear the ready list as we've started all of them
                ready_subtasks = []
                
                # Wait for at least one subtask to complete or a short timeout
                if running_tasks:
                    done, pending = await asyncio.wait(
                        running_tasks,
                        timeout=0.1,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Process completed subtasks
                    for done_task in done:
                        try:
                            completed_subtask = await done_task
                            
                            # Update the subtask in our map
                            subtask_map[completed_subtask.id] = completed_subtask
                            
                            if completed_subtask.status == TaskStatus.COMPLETED:
                                # Add to completed subtasks
                                completed_subtasks[completed_subtask.id] = {
                                    'id': completed_subtask.id,
                                    'type': completed_subtask.type,
                                    'result': completed_subtask.result
                                }
                            elif completed_subtask.status == TaskStatus.FAILED:
                                # Add to failed subtasks
                                failed_subtasks.add(completed_subtask.id)
                        except Exception as e:
                            logger.error(f"Error processing completed subtask: {str(e)}")
                else:
                    # If no tasks are running, wait a bit to avoid busy-waiting
                    await asyncio.sleep(0.1)
                
                # Check for new ready subtasks
                for subtask in task.subtasks:
                    if subtask.status == TaskStatus.PENDING:
                        # Check if all dependencies are satisfied
                        dependencies_satisfied = True
                        if hasattr(subtask, 'dependencies') and subtask.dependencies:
                            for dep in subtask.dependencies:
                                dep_subtask = subtask_map.get(dep.subtask_id)
                                if not dep_subtask or dep_subtask.status != TaskStatus.COMPLETED:
                                    dependencies_satisfied = False
                                    break
                        
                        if dependencies_satisfied:
                            ready_subtasks.append(subtask)
                
                # Update task progress
                completed_count = sum(1 for st in task.subtasks if st.status == TaskStatus.COMPLETED)
                total_count = len(task.subtasks)
                task.progress = completed_count / total_count if total_count > 0 else 0
                task.updated_at = datetime.utcnow()
                
                # Update Redis with current task state
                self.redis.set(f"task:{task_id}", json_utils.dumps(task.dict()), ex=604800)
                
                # Store execution logs
                self.redis.set(f"task_logs:{task_id}", json.dumps(execution_logs), ex=604800)
            
            # Update task status based on subtasks
            if all(st.status == TaskStatus.COMPLETED for st in task.subtasks):
                task.status = TaskStatus.COMPLETED
                task.result = self._generate_final_result(task.subtasks)
                
                # Log task completion
                execution_logs.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': 'task_completed',
                    'details': 'All subtasks completed successfully'
                })
            elif any(st.status == TaskStatus.FAILED for st in task.subtasks):
                task.status = TaskStatus.FAILED
                task.error = "One or more subtasks failed"
                
                # Log task failure
                execution_logs.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': 'task_failed',
                    'details': 'One or more subtasks failed'
                })
            
            # Final Redis updates
            self.redis.set(f"task:{task_id}", json_utils.dumps(task.dict()), ex=604800)
            self.redis.set(f"task_logs:{task_id}", json.dumps(execution_logs), ex=604800)
            logger.info(f"Task {task_id} status: {task.status}")
                
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}")
            
    async def _execute_subtask(self, agent, subtask, context, execution_logs):
        """Execute a single subtask and return the updated subtask."""
        try:
            logger.info(f"Executing subtask {subtask.id} of type {subtask.type}")
            
            # Check if the agent is available
            if agent is None:
                error_msg = f"No agent available for type {subtask.type}"
                logger.error(error_msg)
                subtask.status = TaskStatus.FAILED
                subtask.error = error_msg
                subtask.updated_at = datetime.utcnow()
                
                # Log the error
                log_entry = ExecutionLogEntry(
                    timestamp=datetime.utcnow(),
                    subtask_id=subtask.id,
                    subtask_type=subtask.type,
                    action="failed",
                    details=error_msg
                )
                execution_logs.append(log_entry.dict())
                
                return subtask
            
            # Update subtask status
            subtask.status = TaskStatus.IN_PROGRESS
            subtask.updated_at = datetime.utcnow()
            
            # Check if we should use container isolation
            if self.use_containers and self.container_manager and subtask.type != "planner":
                # Execute in container
                log_entry = ExecutionLogEntry(
                    timestamp=datetime.utcnow(),
                    subtask_id=subtask.id,
                    subtask_type=subtask.type,
                    action="container_started",
                    details=f"Starting container for {subtask.type}"
                )
                execution_logs.append(log_entry.dict())
                
                # Execute the subtask in a container
                container_result = await self.container_manager.execute_in_container(
                    agent_type=subtask.type,
                    subtask_id=subtask.id,
                    context=context
                )
                
                # Update subtask with container information
                subtask.container_id = container_result.get("container_id")
                
                # Update subtask based on container result
                if container_result.get("status") == "completed":
                    subtask.status = TaskStatus.COMPLETED
                    subtask.result = container_result.get("result")
                    subtask.progress = 1.0
                else:
                    subtask.status = TaskStatus.FAILED
                    subtask.error = container_result.get("error") or "Container execution failed"
                    subtask.progress = 0.0
                
                # Log container execution
                log_entry = ExecutionLogEntry(
                    timestamp=datetime.utcnow(),
                    subtask_id=subtask.id,
                    subtask_type=subtask.type,
                    action="container_completed" if subtask.status == TaskStatus.COMPLETED else "container_failed",
                    details=f"Container execution {subtask.status}"
                )
                execution_logs.append(log_entry.dict())
            else:
                # Execute directly with the agent
                updated_subtask = await agent.execute(subtask, context)
                
                # Update subtask fields
                subtask.status = updated_subtask.status
                subtask.progress = updated_subtask.progress
                subtask.result = updated_subtask.result
                subtask.error = updated_subtask.error
                
                # Log the completion
                log_entry = ExecutionLogEntry(
                    timestamp=datetime.utcnow(),
                    subtask_id=subtask.id,
                    subtask_type=subtask.type,
                    action="completed" if subtask.status == TaskStatus.COMPLETED else "failed",
                    details=f"Progress: {subtask.progress * 100:.1f}%"
                )
                execution_logs.append(log_entry.dict())
            
            # Update timestamp
            subtask.updated_at = datetime.utcnow()
            
            logger.info(f"Subtask {subtask.id} status: {subtask.status} with progress {subtask.progress * 100:.1f}%")
            return subtask
            
        except Exception as e:
            error_msg = f"Error executing subtask {subtask.id}: {str(e)}"
            logger.error(error_msg)
            
            # Update the subtask with error information
            subtask.status = TaskStatus.FAILED
            subtask.error = error_msg
            subtask.updated_at = datetime.utcnow()
            
            # Log the error
            log_entry = ExecutionLogEntry(
                timestamp=datetime.utcnow(),
                subtask_id=subtask.id,
                subtask_type=subtask.type,
                action="failed",
                details=error_msg
            )
            execution_logs.append(log_entry.dict())
            
            return subtask
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}")
            
    def _generate_final_result(self, subtasks: List[Subtask]) -> str:
        """Generate a final result summary from all subtask results."""
        result = "# Task Execution Summary\n\n"
        
        for subtask in subtasks:
            result += f"## {subtask.type.replace('_', ' ').title()}\n\n"
            if subtask.result:
                # Extract the most important parts if result is too long
                subtask_result = subtask.result
                if len(subtask_result) > 500:
                    # Try to find section breaks
                    sections = subtask_result.split('\n##')
                    if len(sections) > 1:
                        # Include first section and summary of others
                        result += sections[0] + "\n\n"
                        result += f"*...plus {len(sections)-1} more sections...*\n\n"
                    else:
                        # Just truncate with ellipsis
                        result += subtask_result[:500] + "...\n\n"
                else:
                    result += subtask_result + "\n\n"
            else:
                result += "*No results provided*\n\n"
        
        return result
