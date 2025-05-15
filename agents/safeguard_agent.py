from fastapi import Body
from typing import Dict, Any

from common.types import Message

from agents.base_agent import BaseAgent
from config.config import SAFEGUARD_CONFIG
from models.guard_model import Guard2Model


class SafeguardAgent(BaseAgent):
    """
    Agent that checks user queries for vulnerabilities using Guard-2
    """
    
    def __init__(self):
        """Initialize the safeguard agent"""
        super().__init__(SAFEGUARD_CONFIG)
        self.guard_model = Guard2Model()
        
        # Register the endpoint for this agent
        @self.app.post("/agent/task")
        async def handle_task(message: Dict[str, Any] = Body(...)):
            user_message = Message.model_validate(message.get("message", {}))
            response = await self.process_message(user_message)
            return {"message": response.model_dump()}
        
    async def process_message(self, message: Message) -> Message:
        """
        Process a message by checking for vulnerabilities
        
        Args:
            message: The message to process
            
        Returns:
            Message: The response message with safety information
        """
        # Extract text from message
        query_text = self.get_text_from_message(message)
        
        # Check for vulnerabilities using Guard-2
        safety_result = await self.guard_model.check_vulnerability(query_text)
        
        # Create response
        if safety_result["is_safe"]:
            response_text = f"SAFE: {safety_result['explanation']}"
        else:
            response_text = f"UNSAFE: {safety_result['explanation']}"
            
        return self.create_text_message(response_text) 