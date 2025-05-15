import json
from fastapi import Body
from typing import Dict, Any

from common.types import Message

from agents.base_agent import BaseAgent
from config.config import CRITIC_CONFIG
from models.gemini_model import GeminiModel
from agents.task_managers import CriticTaskManager


class CriticAgent(BaseAgent):
    """
    Agent that evaluates responses using Gemini 1.5 Flash
    """
    
    def __init__(self):
        """Initialize the critic agent"""
        super().__init__(CRITIC_CONFIG)
        # Override the base task manager with critic-specific task manager
        self.task_manager = CriticTaskManager()
        self.a2a_server.task_manager = self.task_manager
        self.task_manager.register_task_handler(self.process_a2a_task)
        
        self.gemini_model = GeminiModel()
    
    async def process_message(self, message: Message) -> Message:
        """
        Evaluate a response to a user query
        
        Args:
            message: The message containing the user query and response to evaluate
            
        Returns:
            Message: The response message with evaluation
        """
        # The message should contain: "USER_QUERY ||| RESPONSE"
        text_content = self.get_text_from_message(message)
        
        try:
            # Split the content into user query and response
            parts = text_content.split(" ||| ")
            if len(parts) != 2:
                return self.create_text_message(
                    "Error: Message should contain 'USER_QUERY ||| RESPONSE'"
                )
                
            user_query, response = parts
            
            # Evaluate the response
            evaluation = await self.gemini_model.evaluate_response(user_query, response)
            
            # Store evaluation in the task manager
            task_id = getattr(message, 'task_id', None)
            if task_id and isinstance(self.task_manager, CriticTaskManager):
                if task_id in self.task_manager.evaluation_scores:
                    self.task_manager.evaluation_scores[task_id]["score"] = evaluation.get('rating', 0)
                    self.task_manager.evaluation_scores[task_id]["feedback"] = evaluation.get('explanation', '')
            
            # Format evaluation as text
            evaluation_text = (
                f"Rating: {evaluation['rating']}/5\n\n"
                f"Explanation: {evaluation['explanation']}"
            )
            
            return self.create_text_message(evaluation_text)
        except Exception as e:
            return self.create_text_message(f"Error evaluating response: {str(e)}") 