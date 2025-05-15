import os
import asyncio
from typing import Callable, List, Optional, Dict, Any
from abc import ABC, abstractmethod

from fastapi import FastAPI
import uvicorn

from common.types import (
    AgentCard, 
    AgentProvider, 
    AgentCapabilities, 
    AgentAuthentication,
    AgentSkill,
    Message,
    TextPart
)
from common.server import A2AServer
from common.client import A2AClient

from config.config import AgentConfig


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
        Start the agent server
        """
        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port
        )
        server = uvicorn.Server(config)
        await server.serve()
    
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