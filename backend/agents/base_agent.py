"""
Base Agent Abstract Class
Defines the interface and common functionality for all specialist agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import logging
from datetime import datetime

from backend.models.schemas import AgentOutput, AgentType, AgentPattern, AgentStatus
from backend.services.llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all specialist agents
    
    Each agent must implement:
    - agent_type: Identifies the agent
    - agent_pattern: Design pattern used (ReAct, Chain-of-Thought, etc.)
    - execute: Main processing logic
    """
    
    def __init__(self, agent_type: AgentType = None, agent_pattern: AgentPattern = None):
        """
        Initialize BaseAgent.

        Subclasses may pass `agent_type` and `agent_pattern` here, or set them
        after calling `super().__init__()`.
        """
        self.llm_service: LLMService = get_llm_service()
        self.agent_type: AgentType = agent_type
        self.agent_pattern: AgentPattern = agent_pattern
        self.execution_time: float = 0.0
        logger.info(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        """
        Execute the agent's main logic
        
        Args:
            input_data: Input parameters specific to each agent
            
        Returns:
            AgentOutput with reasoning, results, and metadata
        """
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> AgentOutput:
        """
        Wrapper that handles timing, error handling, and output formatting
        
        Args:
            input_data: Input parameters
            
        Returns:
            AgentOutput with execution metadata
        """
        logger.info(f"🤖 {self.agent_type.value} agent starting ({self.agent_pattern.value} pattern)")
        start_time = time.time()
        
        try:
            # Execute agent logic
            result = await self.execute(input_data)
            
            # Ensure output has correct metadata
            result.agent_type = self.agent_type
            result.agent_pattern = self.agent_pattern
            result.execution_time = time.time() - start_time
            result.timestamp = datetime.now()
            result.status = AgentStatus.COMPLETED
            
            logger.info(f"✓ {self.agent_type.value} completed in {result.execution_time:.2f}s")
            return result
            
        except ValueError:
            # Validation errors should propagate so callers can handle them explicitly
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"✗ {self.agent_type.value} failed: {str(e)}")
            
            return AgentOutput(
                agent_type=self.agent_type,
                agent_pattern=self.agent_pattern,
                status=AgentStatus.FAILED,
                reasoning=f"Agent failed with error: {str(e)}",
                output={"error": str(e)},
                execution_time=execution_time,
                timestamp=datetime.now()
            )
    
    def create_system_prompt(self, role: str, instructions: str) -> str:
        """
        Helper to create consistent system prompts
        
        Args:
            role: Agent's role description
            instructions: Specific instructions
            
        Returns:
            Formatted system prompt
        """
        return f"""You are a {role} in an AI job application system.

Your responsibilities:
{instructions}

Design Pattern: {self.agent_pattern.value}

Provide clear reasoning for your decisions and structure your output appropriately."""
    
    def validate_input(self, input_data: Dict[str, Any], required_keys: list) -> None:
        """
        Validate that input contains required keys
        
        Args:
            input_data: Input dictionary
            required_keys: List of required key names
            
        Raises:
            ValueError: If required keys are missing
        """
        missing = [key for key in required_keys if key not in input_data]
        if missing:
            raise ValueError(f"Missing required input keys: {', '.join(missing)}")


class ToolUseAgent(BaseAgent):
    """
    Extended base class for agents that use external tools
    Provides tool registry and execution framework
    """
    def __init__(self, agent_type: AgentType = None, agent_pattern: AgentPattern = None):
        # Allow subclasses to pass agent metadata through to BaseAgent
        super().__init__(agent_type=agent_type, agent_pattern=agent_pattern)
        self.tools: Dict[str, callable] = {}
    
    def register_tool(self, name: str, function: callable = None, func: callable = None, description: str = ""):
        """
        Register a tool that the agent can use
        
        Args:
            name: Tool identifier
            function: Callable tool function
            description: What the tool does
        """
        # Accept either `function=` or `func=` keyword from callers
        callable_obj = function or func
        if not callable_obj:
            raise ValueError("register_tool requires a callable via `function` or `func` parameter")

        self.tools[name] = {
            "function": callable_obj,
            "description": description
        }
        logger.info(f"Registered tool: {name}")
    
    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a registered tool
        
        Args:
            tool_name: Name of tool to use
            **kwargs: Arguments for the tool
            
        Returns:
            Tool output
            
        Raises:
            ValueError: If tool doesn't exist
        """
        if tool_name not in self.tools:
            available = ", ".join(self.tools.keys())
            raise ValueError(f"Tool '{tool_name}' not found. Available: {available}")
        
        logger.info(f"Using tool: {tool_name}")
        tool = self.tools[tool_name]
        return await tool["function"](**kwargs)
    
    def get_tools_description(self) -> str:
        """Get description of all available tools"""
        if not self.tools:
            return "No tools available."
        
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(f"- {name}: {tool['description']}")
        
        return "\n".join(descriptions)


if __name__ == "__main__":
    """Test the base agent class"""
    import asyncio
    from backend.models.schemas import AgentType, AgentPattern
    
    class TestAgent(BaseAgent):
        """Simple test agent"""
        
        def __init__(self):
            super().__init__()
            self.agent_type = AgentType.JOB_FINDER
            self.agent_pattern = AgentPattern.REACT
        
        async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
            self.validate_input(input_data, ["test_key"])
            
            # Simulate some work
            await asyncio.sleep(0.5)
            
            return AgentOutput(
                agent_type=self.agent_type,
                agent_pattern=self.agent_pattern,
                status=AgentStatus.COMPLETED,
                reasoning="Test reasoning trace",
                output={"result": "Test completed successfully"},
                execution_time=0.0
            )
    
    async def test_base_agent():
        print("\n🧪 Testing Base Agent...\n")
        
        agent = TestAgent()
        
        # Test successful execution
        result = await agent.run({"test_key": "test_value"})
        assert result.status == AgentStatus.COMPLETED
        print(f"✓ Agent executed successfully")
        print(f"✓ Execution time: {result.execution_time:.2f}s")
        print(f"✓ Pattern: {result.agent_pattern}")
        
        # Test input validation
        try:
            await agent.run({"wrong_key": "value"})
            print("✗ Validation should have failed")
        except:
            print("✓ Input validation working")
        
        print("\n✅ All tests passed!")
    
    asyncio.run(test_base_agent())
