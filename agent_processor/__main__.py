import os
import asyncio
import logging

from dotenv import load_dotenv

from config.config import validate_environment
from agent_processor.processor_agent import ProcessorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """
    Main function to start the Processor Agent
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Validate that all required environment variables are set
    try:
        validate_environment()
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return
    
    logger.info("Starting Processor Agent...")
    
    # Create and start the agent
    agent = ProcessorAgent()
    
    try:
        # Start the agent's server
        await agent.start_server()
    except KeyboardInterrupt:
        logger.info("Processor Agent stopped by user")
    except Exception as e:
        logger.error(f"Error running Processor Agent: {e}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 