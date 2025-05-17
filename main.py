import os
import asyncio
import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import requests

from config.config import validate_environment
from agent_manager.manager_agent import ManagerAgent
from agent_processor.processor_agent import ProcessorAgent
from agent_critic.critic_agent import CriticAgent
from agent_safeguard.safeguard_agent import SafeguardAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a FastAPI app for the main API
app = FastAPI(title="A2A Double Validation API")

@app.get("/")
async def root():
    """Root endpoint to check if the API is running"""
    return {"message": "A2A Double Validation API is running"}

@app.post("/api/query")
async def handle_query(request: Request):
    """Forward query to the Manager Agent"""
    try:
        data = await request.json()
        manager_url = "http://localhost:9001/api/query"  # Manager Agent's FastAPI port
        
        # Forward the request to the Manager Agent
        response = requests.post(manager_url, json=data)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error forwarding request to Manager Agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error communicating with Manager Agent: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def start_main_api():
    """Start the main API server"""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """
    Main function to start all agents
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Validate that all required environment variables are set
    try:
        validate_environment()
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return
    
    # Create all agents
    logger.info("Initializing all agents...")
    manager_agent = ManagerAgent()
    processor_agent = ProcessorAgent()
    critic_agent = CriticAgent()
    safeguard_agent = SafeguardAgent()
    
    # Start all agents
    logger.info("Starting all agents...")
    
    # Using asyncio.gather to start all agents concurrently
    await asyncio.gather(
        manager_agent.start_server(),
        processor_agent.start_server(),
        critic_agent.start_server(),
        safeguard_agent.start_server(),
        start_main_api()  # Also start the main API
    )

if __name__ == "__main__":
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}") 