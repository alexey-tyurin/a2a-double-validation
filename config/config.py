import os
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Base configuration for all agents"""
    host: str = "localhost"
    port: int
    name: str
    description: str
    
class ServerConfig(BaseModel):
    """Configuration for the A2A server"""
    host: str = "localhost"
    port: int = 8000
    
# Agent configuration
MANAGER_CONFIG = AgentConfig(
    port=8001,
    name="Manager Agent",
    description="Agent that coordinates the process flow between agents"
)

SAFEGUARD_CONFIG = AgentConfig(
    port=8002,
    name="Safeguard Agent",
    description="Agent that checks user queries for vulnerabilities using Prompt Guard 2"
)

PROCESSOR_CONFIG = AgentConfig(
    port=8003,
    name="Processor Agent",
    description="Agent that processes user queries using Gemma 3"
)

CRITIC_CONFIG = AgentConfig(
    port=8004,
    name="Critic Agent",
    description="Agent that evaluates responses using Gemini 2.0 Flash"
)

# Model configuration
GUARD_MODEL = "meta-llama/Llama-Prompt-Guard-2-86M"
GEMMA_MODEL = "gemma-3-27b-it"  # Google's Gemma 3 model
GEMINI_MODEL = "gemini-2.0-flash"

# Environment variables that should be set
REQUIRED_ENV_VARS = [
    "GOOGLE_API_KEY",      # For Gemini models
    "VERTEX_AI_PROJECT",   # For Vertex AI
    "VERTEX_AI_LOCATION",  # For Vertex AI
    "HUGGINGFACE_TOKEN",   # For Prompt Guard 2 model
]

def validate_environment():
    """Validate that all required environment variables are set"""
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
    return True 