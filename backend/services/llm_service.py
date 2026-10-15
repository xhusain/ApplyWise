"""
Groq LLM Service
Handles all interactions with the Groq API
Implements retry logic, error handling, and response parsing
"""

from groq import Groq, AsyncGroq
from typing import List, Optional, Dict, Any
import asyncio
import logging
from functools import wraps
import time

from backend.config import get_settings
from backend.models.schemas import LLMMessage, LLMResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Custom exception for LLM service errors"""
    pass


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry failed API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator


class LLMService:
    """Service for interacting with Groq LLM API"""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.sync_client = Groq(api_key=settings.groq_api_key)
        self.default_model = settings.default_model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens
        logger.info(f"LLM Service initialized with model: {self.default_model}")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    async def generate(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion from Groq API
        
        Args:
            messages: List of conversation messages
            model: Model to use (defaults to config)
            temperature: Sampling temperature (defaults to config)
            max_tokens: Maximum tokens in response (defaults to config)
            **kwargs: Additional parameters for Groq API
            
        Returns:
            LLMResponse with content and metadata
            
        Raises:
            LLMServiceError: If API call fails
        """
        try:
            start_time = time.time()
            
            # Use defaults if not specified
            model = model or self.default_model
            temperature = temperature if temperature is not None else self.temperature
            max_tokens = max_tokens or self.max_tokens
            
            # Convert messages to dict format
            message_dicts = [msg.dict() if hasattr(msg, 'dict') else msg for msg in messages]
            
            logger.info(f"Generating completion with {model} (temp={temperature}, max_tokens={max_tokens})")

            response = await self.client.chat.completions.create(
                model=model,
                messages=message_dicts,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            elapsed_time = time.time() - start_time
            
            # Extract response
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            logger.info(f"✓ Generation completed in {elapsed_time:.2f}s - Tokens: {usage['total_tokens']}")
            
            return LLMResponse(
                content=content,
                model=model,
                usage=usage
            )
            
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise LLMServiceError(f"Failed to generate completion: {str(e)}")
    
    def generate_sync(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Synchronous generation (for testing/simple use cases)
        
        Args:
            messages: List of message dicts
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Generated text content
        """
        try:
            model = model or self.default_model
            temperature = temperature if temperature is not None else self.temperature
            max_tokens = max_tokens or self.max_tokens

            response = self.sync_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Sync generation failed: {str(e)}")
            raise LLMServiceError(f"Failed to generate completion: {str(e)}")
    
    async def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_message: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Convenience method for single-turn generation with system prompt
        
        Args:
            system_prompt: System instruction
            user_message: User query
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse
        """
        user_message = user_message or kwargs.pop("user_prompt", None)
        if user_message is None:
            raise LLMServiceError("generate_with_system_prompt requires user_message")

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message)
        ]
        return await self.generate(messages, **kwargs)

    def format_prompt(self, template: str, **variables) -> str:
        """
        Format a prompt template with variables
        
        Args:
            template: Prompt template with {variable} placeholders
            **variables: Variables to substitute
            
        Returns:
            Formatted prompt string
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            raise LLMServiceError(f"Missing template variable: {e}")


# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get singleton LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


if __name__ == "__main__":
    """Test the LLM service"""
    import asyncio
    
    async def test_llm():
        print("\n🧪 Testing LLM Service...\n")
        
        llm = get_llm_service()
        
        # Test 1: Simple generation
        print("Test 1: Simple generation")
        messages = [
            LLMMessage(role="system", content="You are a helpful assistant."),
            LLMMessage(role="user", content="Say hello in a creative way!")
        ]
        
        response = await llm.generate(messages, max_tokens=100)
        print(f"✓ Response: {response.content[:100]}...")
        print(f"✓ Tokens used: {response.usage['total_tokens']}\n")
        
        # Test 2: System prompt helper
        print("Test 2: System prompt helper")
        response = await llm.generate_with_system_prompt(
            system_prompt="You are a professional resume writer.",
            user_message="What are 3 key elements of a great resume?",
            max_tokens=200
        )
        print(f"✓ Response: {response.content[:150]}...")
        print(f"✓ Model: {response.model}\n")
        
        # Test 3: Prompt formatting
        print("Test 3: Prompt formatting")
        template = "Analyze this job title: {title} for {company}"
        formatted = llm.format_prompt(template, title="Senior Developer", company="Google")
        print(f"✓ Formatted: {formatted}\n")
        
        print("✅ All tests passed!")
    
    asyncio.run(test_llm())
