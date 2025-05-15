from fastapi import Body
from typing import Dict, Any

from common.types import Message

from agents.base_agent import BaseAgent
from config.config import PROCESSOR_CONFIG
from models.gemma_model import GemmaModel


class ProcessorAgent(BaseAgent):
    """
    Agent that processes user queries using Gemma 3
    """
    
    def __init__(self):
        """Initialize the processor agent"""
        super().__init__(PROCESSOR_CONFIG)
        self.gemma_model = GemmaModel()
        
        # Register the endpoint for this agent
        @self.app.post("/agent/task")
        async def handle_task(message: Dict[str, Any] = Body(...)):
            user_message = Message.model_validate(message.get("message", {}))
            response = await self.process_message(user_message)
            return {"message": response.model_dump()}
    
    async def process_message(self, message: Message) -> Message:
        """
        Process a user query using Gemma 3
        
        Args:
            message: The message containing the user query
            
        Returns:
            Message: The response message with Gemma's answer
        """
        # Extract query from message
        query_text = self.get_text_from_message(message)
        
        # Process the query with Gemma 3
        result = await self.gemma_model.process_query(query_text)
        
        # Return response
        return self.create_text_message(result["response"]) 