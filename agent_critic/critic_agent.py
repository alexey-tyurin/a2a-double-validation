import json
from fastapi import Body
from typing import Dict, Any

from common.types import Message

from agents.base_agent import BaseAgent
from config.config import CRITIC_CONFIG
from models.gemini_model import GeminiModel
from agent_critic.task_manager import CriticTaskManager


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
        # Get task ID from message metadata
        task_id = message.metadata.get('task_id') if hasattr(message, 'metadata') and isinstance(message.metadata, dict) else None
        
        # Call preprocess_task if we have a task_id and task manager
        if task_id and isinstance(self.task_manager, CriticTaskManager):
            from common.types import Task, TaskStatus, TaskState
            from datetime import datetime
            
            # Create a TaskStatus with required state
            status = TaskStatus(
                state=TaskState.SUBMITTED,
                timestamp=datetime.now()
            )
            
            # Create the Task with the required fields
            task = Task(
                id=task_id, 
                status=status,
                history=[message] if message else []
            )
            
            # Call preprocess_task
            task = await self.task_manager.preprocess_task(task)
        
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
            # Note: task_id was already retrieved from message.metadata above
            if task_id and isinstance(self.task_manager, CriticTaskManager):
                if task_id in self.task_manager.evaluation_scores:
                    self.task_manager.evaluation_scores[task_id]["score"] = evaluation.get('rating', 0)
                    self.task_manager.evaluation_scores[task_id]["feedback"] = evaluation.get('explanation', '')
            
            # Format evaluation as text
            evaluation_text = (
                f"Rating: {evaluation['rating']}/5\n\n"
                f"Explanation: {evaluation['explanation']}"
            )
            
            response_message = self.create_text_message(evaluation_text)
            
            # Call postprocess_task before returning
            if task_id and isinstance(self.task_manager, CriticTaskManager):
                # Update the task with the response
                task.status.message = response_message
                task.status.state = TaskState.COMPLETED
                task = await self.task_manager.postprocess_task(task)
            
            return response_message
        except Exception as e:
            return self.create_text_message(f"Error evaluating response: {str(e)}") 