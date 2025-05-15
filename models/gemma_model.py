import os
from typing import Dict, Any, Optional

import google.generativeai as genai

from config.config import GEMMA_MODEL


class GemmaModel:
    """
    Interface for Gemma 3 model using Google Generative AI
    """
    
    def __init__(self):
        """
        Initialize the Gemma 3 model using Google Generative AI
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=GEMMA_MODEL)
    
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
        response = await self._generate_content_async(prompt)
        
        # Extract response text
        response_text = response.text
        
        return {
            "response": response_text,
            "original_query": user_query
        }
    
    async def _generate_content_async(self, prompt: str):
        """
        Generate content asynchronously
        
        Args:
            prompt: The prompt to generate content for
            
        Returns:
            Response: The response from the model
        """
        # This is a wrapper that can be replaced with true async calls when available
        import asyncio
        return await asyncio.to_thread(self.model.generate_content, prompt) 