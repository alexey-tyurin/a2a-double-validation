import os
import asyncio
from typing import Callable, List, Optional, Dict, Any
from abc import ABC, abstractmethod
import uuid

from fastapi import FastAPI
import uvicorn

from common.types import (
    AgentCard, 
    AgentProvider, 
    AgentCapabilities, 
    AgentAuthentication,
    AgentSkill,
    Message,
    TextPart,
    Task,
    TaskStatus,
    TaskState
)
from common.server import A2AServer
from common.client import A2AClient

from config.config import AgentConfig
from utils.base_task_manager import BaseTaskManager


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the agent with configuration
        
        Args:
            config: Configuration for the agent
        """
        self.config = config
        self.app = FastAPI(title=config.name)
        self.card = self._create_agent_card()
        
        # A2A port is the base port
        self.a2a_port = self.config.port
        # FastAPI port is A2A port + 1000
        self.api_port = self.config.port + 1000
        
        # Create A2A server for agent communication with base task manager
        # This will be overridden by specific agent implementations
        self.task_manager = BaseTaskManager()
        self.a2a_server = A2AServer(
            host=self.config.host,
            port=self.a2a_port,
            task_manager=self.task_manager,
            agent_card=self.card  # Pass the agent card to the A2AServer
        )
        
        # Set up task callback for A2A protocol
        self.task_manager.register_task_handler(self.process_a2a_task)
        
        # Setup external API endpoints (not for agent-to-agent communication)
        self._setup_api_endpoints()
    
    def _setup_api_endpoints(self):
        """
        Set up external API endpoints (not for agent-to-agent communication)
        This method can be overridden by subclasses to add custom endpoints
        """
        pass
    
    def _create_agent_card(self) -> AgentCard:
        """
        Create an agent card with information about this agent
        
        Returns:
            AgentCard: Card describing this agent
        """
        return AgentCard(
            name=self.config.name,
            description=self.config.description,
            url=f"http://{self.config.host}:{self.config.port}",
            provider=AgentProvider(
                organization="A2A Double Validation"
            ),
            version="1.0.0",
            capabilities=AgentCapabilities(streaming=False),
            authentication=AgentAuthentication(schemes=["none"]),
            skills=[self._create_agent_skill()]
        )
    
    def _create_agent_skill(self) -> AgentSkill:
        """
        Create the skill for this agent
        
        Returns:
            AgentSkill: The skill for this agent
        """
        return AgentSkill(
            id=f"{self.config.name.lower().replace(' ', '-')}-skill",
            name=f"{self.config.name} Skill",
            description=self.config.description,
            tags=["a2a"]
        )
        
    async def start_server(self):
        """
        Start the agent server (both A2A server and FastAPI server)
        """
        # Start the A2A server
        await self.a2a_server.start()
        
        # Start the FastAPI server
        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.api_port  # Use the API port (A2A port + 1000)
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def process_a2a_task(self, task: Task) -> Task:
        """
        Process a task received through A2A protocol
        
        Args:
            task: The A2A task to process
            
        Returns:
            Task: The updated task with response
        """
        # Extract user message from history
        if task.history and len(task.history) > 0:
            message = task.history[-1]
            
            # Process the message
            response = await self.process_message(message)
            
            # Update task status
            task.status = TaskStatus(
                state=TaskState.COMPLETED,
                message=response
            )
        else:
            # No message in history, return error
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=self.create_text_message("No message found in task history")
            )
        
        return task
    
    @abstractmethod
    async def process_message(self, message: Message) -> Message:
        """
        Process a message from another agent
        
        Args:
            message: The message to process
            
        Returns:
            Message: The response message
        """
        pass
    
    async def send_message_to_agent(self, agent_url: str, message: Message) -> Message:
        """
        Send a message to another agent using A2A protocol
        
        Args:
            agent_url: The URL of the agent to send the message to
            message: The message to send
            
        Returns:
            Message: The response message
        """
        # Create A2A client for the agent
        client = A2AClient(url=agent_url)
        
        # Send message using A2A protocol
        response = await client.send_message(message)
        
        return response
    
    @staticmethod
    def create_text_message(text: str, role: str = "agent") -> Message:
        """
        Create a simple text message
        
        Args:
            text: The text content
            role: The role (agent or user)
            
        Returns:
            Message: A message with text content
        """
        return Message(
            role=role,
            parts=[TextPart(text=text)]
        )
    
    @staticmethod
    def get_text_from_message(message: Message) -> str:
        """
        Extract text from a message
        
        Args:
            message: The message to extract text from
            
        Returns:
            str: The extracted text
        """
        text_parts = [
            part.text for part in message.parts 
            if part.type == "text"
        ]
        return " ".join(text_parts) 