from fastapi import Body
from typing import Dict, Any

from common.types import Message

from agents.base_agent import BaseAgent
from config.config import PROCESSOR_CONFIG
from models.gemma_model import GemmaModel
from agent_processor.task_manager import ProcessorTaskManager


class ProcessorAgent(BaseAgent):
    """
    Agent that processes user queries using Gemini 1.5 Pro
    """
    
    def __init__(self):
        """Initialize the processor agent"""
        super().__init__(PROCESSOR_CONFIG)
        # Override the base task manager with processor-specific task manager
        self.task_manager = ProcessorTaskManager()
        self.a2a_server.task_manager = self.task_manager
        self.task_manager.register_task_handler(self.process_a2a_task)
        
        self.gemma_model = GemmaModel()
    
    async def process_message(self, message: Message) -> Message:
        """
        Process a user query using Gemini 1.5 Pro
        
        Args:
            message: The message containing the user query
            
        Returns:
            Message: The response message with Gemini's answer
        """
        # Extract query from message
        query_text = self.get_text_from_message(message)
        
        # Process the query with Gemini 1.5 Pro
        result = await self.gemma_model.process_query(query_text)
        
        # Return response
        return self.create_text_message(result["response"]) 