import os
from typing import Dict, Any, Optional

from langchain_google_vertexai import ChatVertexAI
from langchain.schema import HumanMessage

from config.config import GUARD_MODEL


class Guard2Model:
    """
    Interface for Guard-2 vulnerability detection model from Meta
    """
    
    def __init__(self):
        """
        Initialize the Guard-2 model using VertexAI
        """
        project = os.getenv("VERTEX_AI_PROJECT")
        location = os.getenv("VERTEX_AI_LOCATION")
        
        self.chat_model = ChatVertexAI(
            model_name=GUARD_MODEL,
            project=project,
            location=location,
            max_output_tokens=2048,
            temperature=0,
            top_p=0.95,
            verbose=True
        )
    
    async def check_vulnerability(self, user_query: str) -> Dict[str, Any]:
        """
        Check if a user query contains vulnerabilities
        
        Args:
            user_query: The user query to check
            
        Returns:
            Dict: A dictionary containing safety assessment
        """
        # Format prompt for Guard-2
        prompt = f"""
        Please analyze the following user query for any potential safety concerns
        or vulnerabilities. Provide a rating of SAFE or UNSAFE, followed by
        an explanation of your reasoning.
        
        User query: "{user_query}"
        
        Decision (SAFE/UNSAFE):
        """
        
        # Send to Guard-2 model
        response = await self.chat_model.ainvoke(
            [HumanMessage(content=prompt)]
        )
        
        # Parse the response
        response_text = response.content
        
        # Determine safety
        is_safe = "SAFE" in response_text.upper()
        
        return {
            "is_safe": is_safe,
            "explanation": response_text,
            "original_query": user_query
        } 