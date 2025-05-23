import logging
from typing import Dict, Type, Optional

from src.agents.base_agent import BaseAgent
from src.agents.web_research_agent import WebResearchAgent
from src.agents.data_analysis_agent import DataAnalysisAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.code_generation_agent import CodeGenerationAgent
from src.agents.content_creation_agent import ContentCreationAgent

logger = logging.getLogger(__name__)

class AgentFactory:
    """Factory for creating agent instances based on agent type."""
    
    def __init__(self):
        # Register agent types
        self._agent_types: Dict[str, Type[BaseAgent]] = {
            "planner": PlannerAgent,
            "web_research": WebResearchAgent,
            "data_analysis": DataAnalysisAgent,
            "code_generation": CodeGenerationAgent,
            "content_creation": ContentCreationAgent,
            "general_execution": WebResearchAgent,  # Still using WebResearchAgent for general execution
            "result_orchestration": DataAnalysisAgent,  # Still using DataAnalysisAgent for result orchestration
        }
        
        # Cache for agent instances
        self._agent_instances: Dict[str, BaseAgent] = {}
    
    def get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """
        Get an agent instance for the specified type.
        
        Args:
            agent_type: The type of agent to get
            
        Returns:
            An agent instance or None if the type is not supported
        """
        # Check if we already have an instance
        if agent_type in self._agent_instances:
            return self._agent_instances[agent_type]
        
        # Check if we support this agent type
        if agent_type not in self._agent_types:
            logger.warning(f"Unsupported agent type: {agent_type}")
            return None
        
        # Create a new instance
        agent_class = self._agent_types[agent_type]
        agent = agent_class()
        
        # Cache the instance
        self._agent_instances[agent_type] = agent
        
        logger.info(f"Created new agent instance: {agent}")
        return agent
    
    def register_agent_type(self, agent_type: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register a new agent type.
        
        Args:
            agent_type: The type identifier for the agent
            agent_class: The agent class to instantiate for this type
        """
        self._agent_types[agent_type] = agent_class
        logger.info(f"Registered new agent type: {agent_type}")
        
        # Clear any cached instance
        if agent_type in self._agent_instances:
            del self._agent_instances[agent_type]
