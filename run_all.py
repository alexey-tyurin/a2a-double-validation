#!/usr/bin/env python
"""
Run All Agents Script

This script runs all agents in the system:
- Manager Agent
- Processor Agent
- Critic Agent
- Safeguard Agent

Each agent can also be run individually using python -m agent_name
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

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
    
    try:
        # Using asyncio.gather to start all agents concurrently
        await asyncio.gather(
            manager_agent.start_server(),
            processor_agent.start_server(),
            critic_agent.start_server(),
            safeguard_agent.start_server()
        )
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"Error running agents: {e}")

if __name__ == "__main__":
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}") 