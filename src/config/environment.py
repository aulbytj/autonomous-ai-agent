"""
Environment configuration for the Autonomous AI Agent.
This module centralizes all environment variables and provides defaults.
"""
import os
from typing import Dict, Any

def get_env_config() -> Dict[str, Any]:
    """
    Get the environment configuration.
    
    Returns:
        Dictionary with environment configuration
    """
    return {
        # General settings
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "debug": os.environ.get("DEBUG", "true").lower() == "true",
        
        # Redis settings
        "redis_url": os.environ.get("REDIS_URL", "redis://localhost:6379"),
        "redis_expiration_seconds": int(os.environ.get("REDIS_EXPIRATION_SECONDS", "604800")),  # 7 days
        
        # API settings
        "api_host": os.environ.get("API_HOST", "0.0.0.0"),
        "api_port": int(os.environ.get("API_PORT", "8098")),
        
        # Container settings
        "use_containers": os.environ.get("USE_CONTAINERS", "false").lower() == "true",
        "container_memory_limit": os.environ.get("CONTAINER_MEMORY_LIMIT", "512m"),
        "container_cpu_quota": int(os.environ.get("CONTAINER_CPU_QUOTA", "50000")),  # 50% of CPU
        
        # Agent settings
        "max_agent_instances": int(os.environ.get("MAX_AGENT_INSTANCES", "5")),
        "agent_timeout_seconds": int(os.environ.get("AGENT_TIMEOUT_SECONDS", "60")),
        
        # Task settings
        "max_subtasks": int(os.environ.get("MAX_SUBTASKS", "10")),
        "max_task_execution_time": int(os.environ.get("MAX_TASK_EXECUTION_TIME", "300")),  # 5 minutes
    }

# Global environment configuration
ENV_CONFIG = get_env_config()
