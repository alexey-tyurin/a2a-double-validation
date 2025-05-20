from fastapi import Body
from typing import Dict, Any

from common.types import Message

from agents.base_agent import BaseAgent
from config.config import SAFEGUARD_CONFIG
from models.guard_model import Guard2Model
from agent_safeguard.task_manager import SafeguardTaskManager


class SafeguardAgent(BaseAgent):
    """
    Agent that checks user queries for vulnerabilities using Guard-2
    """
    
    def __init__(self):
        """Initialize the safeguard agent"""
        super().__init__(SAFEGUARD_CONFIG)
        # Override the base task manager with safeguard-specific task manager
        self.task_manager = SafeguardTaskManager()
        self.a2a_server.task_manager = self.task_manager
        self.task_manager.register_task_handler(self.process_a2a_task)
        
        self.guard_model = Guard2Model()
        
    async def process_message(self, message: Message) -> Message:
        """
        Process a message by checking for vulnerabilities
        
        Args:
            message: The message to process
            
        Returns:
            Message: The response message with safety information
        """
        # Get task ID from message metadata
        task_id = message.metadata.get('task_id') if hasattr(message, 'metadata') and isinstance(message.metadata, dict) else None
        
        # Call preprocess_task if we have a task_id and task manager
        if task_id and isinstance(self.task_manager, SafeguardTaskManager):
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
            
        # Extract text from message
        query_text = self.get_text_from_message(message)
        
        # Check for vulnerabilities using Guard-2
        safety_result = await self.guard_model.check_vulnerability(query_text)
        
        # Store safety check in the task manager
        if task_id and isinstance(self.task_manager, SafeguardTaskManager):
            if task_id in self.task_manager.vulnerability_checks:
                self.task_manager.vulnerability_checks[task_id]["is_safe"] = safety_result.get('is_safe', False)
                self.task_manager.vulnerability_checks[task_id]["risk_level"] = safety_result.get('risk_level', 'high')

        # Create response
        if safety_result["is_safe"]:
            response_text = f"SAFE: {safety_result['explanation']}"
        else:
            response_text = f"UNSAFE: {safety_result['explanation']}"
            
        return self.create_text_message(response_text) 