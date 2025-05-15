import asyncio
import uuid
from fastapi import Body, Request
from typing import Dict, Any

from common.types import Message
from common.client import A2AClient

from agents.base_agent import BaseAgent
from config.config import MANAGER_CONFIG, SAFEGUARD_CONFIG, PROCESSOR_CONFIG, CRITIC_CONFIG
from agents.task_managers import ManagerTaskManager


class ManagerAgent(BaseAgent):
    """
    Agent that coordinates the process flow between agents
    """
    
    def __init__(self):
        """Initialize the manager agent"""
        super().__init__(MANAGER_CONFIG)
        # Override the base task manager with manager-specific task manager
        self.task_manager = ManagerTaskManager()
        self.a2a_server.task_manager = self.task_manager
        self.task_manager.register_task_handler(self.process_a2a_task)
        
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
            
            # Create a unique task ID for this workflow
            task_id = str(uuid.uuid4())
            
            # Create user message
            user_message = self.create_text_message(user_query, role="user")
            
            # Add task_id to message for tracking
            setattr(user_message, 'task_id', task_id)
            
            # Initialize task in manager's task tracker
            if isinstance(self.task_manager, ManagerTaskManager):
                await self.task_manager.preprocess_task({
                    "id": task_id,
                    "status": None,
                    "history": [user_message],
                    "artifacts": []
                })
            
            # Process through the agent flow
            response = await self.process_message(user_message)
            
            # Complete task in manager's task tracker
            if isinstance(self.task_manager, ManagerTaskManager):
                await self.task_manager.postprocess_task({
                    "id": task_id,
                    "status": None,
                    "history": [user_message, response],
                    "artifacts": []
                })
            
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
        task_id = getattr(message, 'task_id', str(uuid.uuid4()))
        
        # Ensure we have a task manager and tracking is set up
        if isinstance(self.task_manager, ManagerTaskManager):
            if task_id not in self.task_manager.workflow_states:
                await self.task_manager.preprocess_task({
                    "id": task_id,
                    "status": None,
                    "history": [message],
                    "artifacts": []
                })
        
        # Step 1: Check for vulnerabilities with Safeguard Agent
        try:
            # Update workflow state
            if isinstance(self.task_manager, ManagerTaskManager):
                self.task_manager.advance_workflow(task_id, "safeguard")
            
            # Send message to Safeguard Agent using A2A protocol
            safeguard_response = await self.send_message_to_agent(self.safeguard_url, message)
            safeguard_text = self.get_text_from_message(safeguard_response)
            
            # Register the safeguard task
            if isinstance(self.task_manager, ManagerTaskManager):
                self.task_manager.register_agent_task(task_id, "safeguard", getattr(safeguard_response, 'task_id', None))
            
            # Check if the query is safe
            if safeguard_text.startswith("UNSAFE"):
                # Complete workflow with unsafe result
                if isinstance(self.task_manager, ManagerTaskManager):
                    self.task_manager.advance_workflow(task_id, "complete")
                
                return self.create_text_message(
                    "I apologize, but your query contains content that cannot be processed as it may violate our safety guidelines."
                )
            
            # Step 2: Process with Processor Agent if safe
            if isinstance(self.task_manager, ManagerTaskManager):
                self.task_manager.advance_workflow(task_id, "processor")
            
            processor_response = await self.send_message_to_agent(self.processor_url, message)
            processor_text = self.get_text_from_message(processor_response)
            
            # Register the processor task
            if isinstance(self.task_manager, ManagerTaskManager):
                self.task_manager.register_agent_task(task_id, "processor", getattr(processor_response, 'task_id', None))
            
            # Step 3: Get evaluation from Critic Agent
            if isinstance(self.task_manager, ManagerTaskManager):
                self.task_manager.advance_workflow(task_id, "critic")
            
            critic_message = self.create_text_message(
                f"{user_query} ||| {processor_text}"
            )
            # Add task_id to critic message for tracking
            setattr(critic_message, 'task_id', task_id)
            
            critic_response = await self.send_message_to_agent(self.critic_url, critic_message)
            critic_text = self.get_text_from_message(critic_response)
            
            # Register the critic task
            if isinstance(self.task_manager, ManagerTaskManager):
                self.task_manager.register_agent_task(task_id, "critic", getattr(critic_response, 'task_id', None))
                self.task_manager.advance_workflow(task_id, "complete")
            
            # Step 4: Construct final response with processor result and critic evaluation
            final_response = (
                f"{processor_text}\n\n"
                f"---\n"
                f"Response Evaluation: {critic_text}"
            )
            
            return self.create_text_message(final_response)
            
        except Exception as e:
            # Mark workflow as failed
            if isinstance(self.task_manager, ManagerTaskManager):
                self.task_manager.advance_workflow(task_id, "complete")
            
            return self.create_text_message(
                f"An error occurred while processing your request: {str(e)}"
            ) 