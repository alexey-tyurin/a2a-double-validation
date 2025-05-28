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
    "GOOGLE_API_KEY",      # For Gemini models (from Secret Manager in cloud)
    "VERTEX_AI_PROJECT",   # For Vertex AI (from env vars)
    "VERTEX_AI_LOCATION",  # For Vertex AI (from env vars)
    "HUGGINGFACE_TOKEN",   # For Prompt Guard 2 model (from Secret Manager in cloud)
]

def is_cloud_deployment():
    """Check if running in cloud deployment environment"""
    return os.getenv("DEPLOYMENT_ENV") == "cloud"

def load_environment():
    """Load environment variables based on deployment type"""
    if is_cloud_deployment():
        print("Running in cloud deployment mode")
        print("- Non-sensitive variables loaded from Cloud Run environment")
        print("- Sensitive credentials (GOOGLE_API_KEY, HUGGINGFACE_TOKEN) loaded from Secret Manager")
        # In cloud deployment, environment variables are already set by Cloud Run
        # Secrets are automatically mounted as environment variables by Cloud Run
        pass
    else:
        print("Running in local mode - loading from .env file")
        # Load from .env file for local development
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("Warning: python-dotenv not installed. Environment variables must be set manually.")

def validate_environment():
    """Validate that all required environment variables are set"""
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        deployment_type = "cloud" if is_cloud_deployment() else "local"
        if deployment_type == "cloud":
            error_msg = f"Missing required environment variables in Cloud Run deployment: {', '.join(missing_vars)}"
            error_msg += "\nFor GOOGLE_API_KEY and HUGGINGFACE_TOKEN: Check Secret Manager setup"
            error_msg += "\nFor VERTEX_AI_PROJECT and VERTEX_AI_LOCATION: Check --set-env-vars in deployment script"
        else:
            error_msg = f"Missing required environment variables in .env file: {', '.join(missing_vars)}"
            error_msg += "\nPlease set these variables in your .env file."
        raise EnvironmentError(error_msg)
    return True 