import asyncio
import logging
import sys
from config.config import validate_environment, load_environment
from agent_safeguard.safeguard_agent import SafeguardAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """
    Main function to start the Safeguard Agent
    """
    try:
        # Load environment variables based on deployment type
        load_environment()
        
        # Validate environment
        validate_environment()
        
        # Create and start the agent
        agent = SafeguardAgent()
        
        # Start the agent's server
        await agent.start_server()
        
    except Exception as e:
        logger.error(f"Failed to start Safeguard Agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Safeguard Agent stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1) 