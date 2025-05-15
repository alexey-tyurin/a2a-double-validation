import os
from typing import Dict, Any, Optional

import google.adk as adk
from google.adk.generative_models import GenerativeModel

from config.config import GEMMA_MODEL


class GemmaModel:
    """
    Interface for Gemma 3 model using Google ADK
    """
    
    def __init__(self):
        """
        Initialize the Gemma 3 model using Google ADK
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
            
        adk.init(api_key=api_key)
        self.model = GenerativeModel(model_name=GEMMA_MODEL)
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query with Gemma 3
        
        Args:
            user_query: The user query to process
            
        Returns:
            Dict: A dictionary containing the model response
        """
        # Format prompt for Gemma 3
        prompt = f"""
        User query: {user_query}
        
        Please provide a thorough, accurate, and helpful response to this query.
        """
        
        # Generate response
        response = await self.model.generate_content_async(prompt)
        
        # Extract response text
        response_text = response.text
        
        return {
            "response": response_text,
            "original_query": user_query
        } 