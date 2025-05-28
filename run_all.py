#!/usr/bin/env python3
"""
A2A Double Validation System - Run All Agents

This script starts all agents in the A2A Double Validation system:
- Manager Agent (coordinates the flow)
- Safeguard Agent (checks for vulnerabilities)
- Processor Agent (processes queries)
- Critic Agent (evaluates responses)

Each agent runs its own A2A server for inter-agent communication.
The Manager Agent also runs a FastAPI server for external API access.
"""

import asyncio
import logging
import signal
import sys
from config.config import validate_environment, load_environment
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

# Global variable to track running tasks
running_tasks = []

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}. Shutting down...")
    for task in running_tasks:
        task.cancel()
    sys.exit(0)

async def main():
    """
    Main function to start all agents
    """
    # Load environment variables based on deployment type
    load_environment()
    
    # Validate that all required environment variables are set
    try:
        validate_environment()
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create all agents
    logger.info("Initializing all agents...")
    manager_agent = ManagerAgent()
    processor_agent = ProcessorAgent()
    critic_agent = CriticAgent()
    safeguard_agent = SafeguardAgent()
    
    # Start all agents
    logger.info("Starting all agents...")
    
    # Create tasks for all servers to run in parallel
    global running_tasks
    
    # A2A servers for all agents
    running_tasks.append(asyncio.create_task(manager_agent.start_server()))
    running_tasks.append(asyncio.create_task(processor_agent.start_server()))
    running_tasks.append(asyncio.create_task(critic_agent.start_server()))
    running_tasks.append(asyncio.create_task(safeguard_agent.start_server()))
    
    # Wait a moment for A2A servers to start before launching FastAPI
    await asyncio.sleep(2)
    
    # FastAPI server for Manager Agent only
    logger.info("Starting Manager Agent FastAPI server...")
    running_tasks.append(asyncio.create_task(manager_agent.start_api_server()))
    
    # Wait for all tasks to complete (they won't unless terminated)
    logger.info("All servers started successfully!")
    logger.info("Manager Agent API available at: http://localhost:9001")
    logger.info("Press Ctrl+C to terminate all agents.")
    
    try:
        await asyncio.gather(*running_tasks)
    except asyncio.CancelledError:
        logger.info("All tasks cancelled. Shutting down.")

if __name__ == "__main__":
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1) 