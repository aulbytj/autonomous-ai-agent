"""
CORS configuration for the Autonomous AI Agent API.
This module provides environment-specific CORS settings.
"""
import os
from typing import List

def get_allowed_origins() -> List[str]:
    """
    Get the list of allowed origins based on the environment.
    
    In development mode, all origins are allowed.
    In production mode, only specified origins are allowed.
    
    Returns:
        List of allowed origins
    """
    # Check if we're in production mode
    is_production = os.environ.get('ENVIRONMENT', 'development').lower() == 'production'
    
    if is_production:
        # In production, only allow specific origins
        origins_str = os.environ.get('ALLOWED_ORIGINS', 'https://autonomous-ai-agent.example.com')
        return origins_str.split(',')
    else:
        # In development, allow all origins for easier testing
        return ["*"]

def get_cors_config() -> dict:
    """
    Get the complete CORS configuration based on the environment.
    
    Returns:
        Dictionary with CORS configuration
    """
    return {
        "allow_origins": get_allowed_origins(),
        "allow_credentials": True,
        "allow_methods": ["*"] if os.environ.get('ENVIRONMENT', 'development').lower() != 'production' else ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["*"] if os.environ.get('ENVIRONMENT', 'development').lower() != 'production' else ["Content-Type", "Authorization", "Accept"],
    }
