import asyncio
import logging
import sys
import os
from config.config import validate_environment, load_environment
from agent_manager.manager_agent import ManagerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """
    Main function to start the Manager Agent
    """
    try:
        # Load environment variables based on deployment type
        load_environment()
        
        # Validate environment
        validate_environment()
        
        # Create and start the agent
        agent = ManagerAgent()
        
        # In Cloud Run, only start the API server since it's the external-facing service
        # In local mode, start both A2A server and API server
        if os.getenv("DEPLOYMENT_ENV") == "cloud":
            logger.info("Starting Manager Agent in Cloud Run mode (API server only)")
            await agent.start_api_server()
        else:
            logger.info("Starting Manager Agent in local mode (both A2A and API servers)")
            # Start both A2A server and API server
            await asyncio.gather(
                agent.start_server(),
                agent.start_api_server()
            )
        
    except Exception as e:
        logger.error(f"Failed to start Manager Agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Manager Agent stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1) 