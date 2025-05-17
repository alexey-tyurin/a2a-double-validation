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

@app.get("/status")
async def status():
    """Health check endpoint that also shows agent status"""
    try:
        # Check if Manager Agent is running
        manager_status = "Unknown"
        try:
            response = requests.get("http://localhost:9001/")
            if response.status_code == 200:
                manager_status = "Running"
        except:
            manager_status = "Not Running"
        
        return {
            "status": "OK",
            "agents": {
                "manager": {
                    "status": manager_status,
                    "a2a_port": 8001,
                    "api_port": 9001
                },
                "processor": {
                    "status": "A2A Only",
                    "a2a_port": 8003
                },
                "critic": {
                    "status": "A2A Only",
                    "a2a_port": 8004
                },
                "safeguard": {
                    "status": "A2A Only",
                    "a2a_port": 8002
                }
            }
        }
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return {"status": "Error", "message": str(e)}

async def start_main_api():
    """Start the main API server"""
    # Use port 8005 for main API to avoid conflict with other services
    config = uvicorn.Config(app, host="0.0.0.0", port=8005)
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
    
    # Create tasks for all servers to run in parallel
    tasks = []
    
    # A2A servers for all agents
    tasks.append(asyncio.create_task(manager_agent.start_server()))
    tasks.append(asyncio.create_task(processor_agent.start_server()))
    tasks.append(asyncio.create_task(critic_agent.start_server()))
    tasks.append(asyncio.create_task(safeguard_agent.start_server()))
    
    # Wait a moment for A2A servers to start before launching FastAPI
    await asyncio.sleep(1)
    
    # FastAPI server for Manager Agent only
    logger.info("Starting Manager Agent FastAPI server...")
    tasks.append(asyncio.create_task(manager_agent.start_api_server()))
    
    # Start the main API
    logger.info("Starting Main API server...")
    tasks.append(asyncio.create_task(start_main_api()))
    
    # Wait for all tasks to complete (they won't unless terminated)
    logger.info("All servers started. Press Ctrl+C to terminate.")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}") 