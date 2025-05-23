import logging
import asyncio
import uuid
import os
import json
from typing import Dict, Any, Optional
import docker
from docker.errors import DockerException
from src.config.environment import ENV_CONFIG

logger = logging.getLogger(__name__)

class ContainerManager:
    """
    Manages Docker containers for isolated agent execution.
    This class handles the creation, execution, and cleanup of containers.
    """
    
    def __init__(self):
        """Initialize the container manager with Docker client."""
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {str(e)}")
            self.client = None
        
        # Default image to use for containers
        self.default_image = "python:3.9-slim"
        
        # Map of agent types to Docker images
        self.agent_images = {
            "web_research": "python:3.9-slim",
            "data_analysis": "python:3.9-slim",
            "code_generation": "python:3.9-slim",
            "content_creation": "python:3.9-slim",
            "general_execution": "python:3.9-slim",
        }
        
        # Track running containers
        self.containers = {}
    
    async def create_container(self, agent_type: str, subtask_id: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Create a new container for the specified agent type.
        
        Args:
            agent_type: The type of agent to create a container for
            subtask_id: The ID of the subtask to execute
            context: The context data for the subtask
            
        Returns:
            Container ID if successful, None otherwise
        """
        if not self.client:
            logger.error("Docker client not available")
            return None
        
        try:
            # Determine the image to use
            image = self.agent_images.get(agent_type, self.default_image)
            
            # Create a unique name for the container
            container_name = f"agent-{agent_type}-{subtask_id[:8]}"
            
            # Prepare context data as environment variables
            env = {
                "SUBTASK_ID": subtask_id,
                "AGENT_TYPE": agent_type,
                "TASK_CONTEXT": json.dumps(context)
            }
            
            # Create the container
            container = self.client.containers.create(
                image=image,
                name=container_name,
                environment=env,
                detach=True,
                # Add resource limits from environment config
                mem_limit=ENV_CONFIG["container_memory_limit"],
                cpu_quota=ENV_CONFIG["container_cpu_quota"],
                network_mode="bridge",
                # Mount the agent code
                volumes={
                    os.path.abspath("./src/agents"): {
                        "bind": "/app/agents",
                        "mode": "ro"
                    }
                },
                working_dir="/app",
                command="python -c 'import os, json, time; print(\"Agent container started\"); time.sleep(2); print(json.dumps({\"status\": \"completed\", \"result\": f\"Simulated result for {os.environ[\"AGENT_TYPE\"]} agent\"}))'",
            )
            
            container_id = container.id
            self.containers[subtask_id] = container_id
            
            logger.info(f"Created container {container_id} for subtask {subtask_id}")
            return container_id
            
        except Exception as e:
            logger.error(f"Error creating container for subtask {subtask_id}: {str(e)}")
            return None
    
    async def start_container(self, container_id: str) -> bool:
        """
        Start a previously created container.
        
        Args:
            container_id: The ID of the container to start
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Docker client not available")
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"Started container {container_id}")
            return True
        except Exception as e:
            logger.error(f"Error starting container {container_id}: {str(e)}")
            return False
    
    async def get_container_logs(self, container_id: str) -> str:
        """
        Get the logs from a container.
        
        Args:
            container_id: The ID of the container
            
        Returns:
            Container logs as a string
        """
        if not self.client:
            logger.error("Docker client not available")
            return ""
        
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs().decode('utf-8')
            return logs
        except Exception as e:
            logger.error(f"Error getting logs for container {container_id}: {str(e)}")
            return ""
    
    async def get_container_status(self, container_id: str) -> Dict[str, Any]:
        """
        Get the status of a container.
        
        Args:
            container_id: The ID of the container
            
        Returns:
            Dictionary with container status information
        """
        if not self.client:
            logger.error("Docker client not available")
            return {"status": "error", "message": "Docker client not available"}
        
        try:
            container = self.client.containers.get(container_id)
            container_info = container.attrs
            
            # Extract relevant status information
            status = {
                "id": container_id,
                "status": container_info["State"]["Status"],
                "running": container_info["State"]["Running"],
                "exit_code": container_info["State"]["ExitCode"] if "ExitCode" in container_info["State"] else None,
                "started_at": container_info["State"]["StartedAt"] if "StartedAt" in container_info["State"] else None,
                "finished_at": container_info["State"]["FinishedAt"] if "FinishedAt" in container_info["State"] else None
            }
            
            return status
        except Exception as e:
            logger.error(f"Error getting status for container {container_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def stop_container(self, container_id: str) -> bool:
        """
        Stop a running container.
        
        Args:
            container_id: The ID of the container to stop
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Docker client not available")
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=5)
            logger.info(f"Stopped container {container_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping container {container_id}: {str(e)}")
            return False
    
    async def remove_container(self, container_id: str) -> bool:
        """
        Remove a container.
        
        Args:
            container_id: The ID of the container to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Docker client not available")
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
            
            # Remove from tracking
            for subtask_id, cid in list(self.containers.items()):
                if cid == container_id:
                    del self.containers[subtask_id]
            
            logger.info(f"Removed container {container_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing container {container_id}: {str(e)}")
            return False
    
    async def execute_in_container(self, agent_type: str, subtask_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a subtask in an isolated container.
        
        Args:
            agent_type: The type of agent to execute
            subtask_id: The ID of the subtask
            context: The context data for the subtask
            
        Returns:
            Dictionary with execution results
        """
        # Create container
        container_id = await self.create_container(agent_type, subtask_id, context)
        if not container_id:
            return {
                "status": "failed",
                "error": "Failed to create container",
                "container_id": None
            }
        
        try:
            # Start container
            if not await self.start_container(container_id):
                return {
                    "status": "failed",
                    "error": "Failed to start container",
                    "container_id": container_id
                }
            
            # Wait for container to complete (with timeout)
            max_wait_time = 60  # Maximum wait time in seconds
            wait_interval = 1  # Check interval in seconds
            
            for _ in range(max_wait_time // wait_interval):
                status = await self.get_container_status(container_id)
                if status.get("status") == "exited":
                    break
                await asyncio.sleep(wait_interval)
            
            # Get container logs
            logs = await self.get_container_logs(container_id)
            
            # Parse the result from logs
            result = None
            for line in logs.splitlines():
                try:
                    data = json.loads(line)
                    if isinstance(data, dict) and "status" in data:
                        result = data
                        break
                except:
                    continue
            
            if not result:
                result = {
                    "status": "completed" if status.get("exit_code") == 0 else "failed",
                    "result": logs if status.get("exit_code") == 0 else None,
                    "error": logs if status.get("exit_code") != 0 else None
                }
            
            # Add container info
            result["container_id"] = container_id
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing in container for subtask {subtask_id}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "container_id": container_id
            }
        finally:
            # Clean up container (can be done asynchronously)
            asyncio.create_task(self.remove_container(container_id))
    
    async def cleanup(self):
        """Clean up all containers managed by this instance."""
        if not self.client:
            return
        
        for subtask_id, container_id in list(self.containers.items()):
            try:
                await self.remove_container(container_id)
            except Exception as e:
                logger.error(f"Error cleaning up container {container_id}: {str(e)}")
