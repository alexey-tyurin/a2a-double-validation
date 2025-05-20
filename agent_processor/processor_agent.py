from fastapi import Body
from typing import Dict, Any

from common.types import Message

from agents.base_agent import BaseAgent
from config.config import PROCESSOR_CONFIG
from models.gemma_model import GemmaModel
from agent_processor.task_manager import ProcessorTaskManager


class ProcessorAgent(BaseAgent):
    """
    Agent that processes user queries using Gemma 3
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
        Process a user query using Gemma 3
        
        Args:
            message: The message containing the user query
            
        Returns:
            Message: The response message with Gemma's answer
        """
        # Get task ID from message metadata
        task_id = message.metadata.get('task_id') if hasattr(message, 'metadata') and isinstance(message.metadata, dict) else None
        
        # Call preprocess_task if we have a task_id and task manager
        if task_id and isinstance(self.task_manager, ProcessorTaskManager):
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
        
        # Extract query from message
        query_text = self.get_text_from_message(message)
        
        # Process the query with Gemma 3
        result = await self.gemma_model.process_query(query_text)
        
        # Create response message
        response_message = self.create_text_message(result["response"])
        
        # Call postprocess_task before returning
        if task_id and isinstance(self.task_manager, ProcessorTaskManager):
            # Update the task with the response
            task.status.message = response_message
            task.status.state = TaskState.COMPLETED
            task = await self.task_manager.postprocess_task(task)
        
        # Return response
        return response_message 