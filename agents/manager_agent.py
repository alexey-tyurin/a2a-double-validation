import asyncio
from fastapi import Body, Request
from typing import Dict, Any

from common.types import Message
from common.client import A2AClient

from agents.base_agent import BaseAgent
from config.config import MANAGER_CONFIG, SAFEGUARD_CONFIG, PROCESSOR_CONFIG, CRITIC_CONFIG


class ManagerAgent(BaseAgent):
    """
    Agent that coordinates the process flow between agents
    """
    
    def __init__(self):
        """Initialize the manager agent"""
        super().__init__(MANAGER_CONFIG)
        
        # Construct agent URLs for A2A communication
        self.safeguard_url = f"http://{SAFEGUARD_CONFIG.host}:{SAFEGUARD_CONFIG.port}"
        self.processor_url = f"http://{PROCESSOR_CONFIG.host}:{PROCESSOR_CONFIG.port}"
        self.critic_url = f"http://{CRITIC_CONFIG.host}:{CRITIC_CONFIG.port}"
    
    def _setup_api_endpoints(self):
        """Set up external API endpoints for user interaction"""
        @self.app.post("/api/query")
        async def handle_user_query(request: Request):
            data = await request.json()
            user_query = data.get("query", "")
            
            # Create user message
            user_message = self.create_text_message(user_query, role="user")
            
            # Process through the agent flow
            response = await self.process_message(user_message)
            
            # Return the final response
            return {"response": self.get_text_from_message(response)}
    
    async def process_message(self, message: Message) -> Message:
        """
        Process a user message through the entire agent flow
        
        Args:
            message: The user message to process
            
        Returns:
            Message: The final response message
        """
        user_query = self.get_text_from_message(message)
        
        # Step 1: Check for vulnerabilities with Safeguard Agent
        try:
            # Send message to Safeguard Agent using A2A protocol
            safeguard_response = await self.send_message_to_agent(self.safeguard_url, message)
            safeguard_text = self.get_text_from_message(safeguard_response)
            
            # Check if the query is safe
            if safeguard_text.startswith("UNSAFE"):
                return self.create_text_message(
                    "I apologize, but your query contains content that cannot be processed as it may violate our safety guidelines."
                )
                
            # Step 2: Process with Processor Agent if safe
            processor_response = await self.send_message_to_agent(self.processor_url, message)
            processor_text = self.get_text_from_message(processor_response)
            
            # Step 3: Get evaluation from Critic Agent
            critic_message = self.create_text_message(
                f"{user_query} ||| {processor_text}"
            )
            critic_response = await self.send_message_to_agent(self.critic_url, critic_message)
            critic_text = self.get_text_from_message(critic_response)
            
            # Step 4: Construct final response with processor result and critic evaluation
            final_response = (
                f"{processor_text}\n\n"
                f"---\n"
                f"Response Evaluation: {critic_text}"
            )
            
            return self.create_text_message(final_response)
            
        except Exception as e:
            return self.create_text_message(
                f"An error occurred while processing your request: {str(e)}"
            ) 