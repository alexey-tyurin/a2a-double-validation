import asyncio
import os
from dotenv import load_dotenv

from agents.manager_agent import ManagerAgent
from agents.safeguard_agent import SafeguardAgent  
from agents.processor_agent import ProcessorAgent
from agents.critic_agent import CriticAgent

# Load environment variables
load_dotenv()

async def main():
    # Initialize agents
    manager = ManagerAgent()
    safeguard = SafeguardAgent()
    processor = ProcessorAgent()
    critic = CriticAgent()
    
    # Start all agent servers
    # Each agent has its own A2A server and FastAPI server
    await asyncio.gather(
        manager.start_server(),
        safeguard.start_server(),
        processor.start_server(),
        critic.start_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down A2A system...") 