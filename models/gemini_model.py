import os
from typing import Dict, Any, Optional
import json

import google.adk as adk
from google.adk.generative_models import GenerativeModel

from config.config import GEMINI_MODEL


class GeminiModel:
    """
    Interface for Gemini 2.0 Flash model using Google ADK
    """
    
    def __init__(self):
        """
        Initialize the Gemini 2.0 Flash model using Google ADK
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
            
        adk.init(api_key=api_key)
        self.model = GenerativeModel(model_name=GEMINI_MODEL)
    
    async def evaluate_response(self, user_query: str, response: str) -> Dict[str, Any]:
        """
        Evaluate a response for completeness and validity
        
        Args:
            user_query: The original user query
            response: The response to evaluate
            
        Returns:
            Dict: A dictionary containing the evaluation results
        """
        # Format prompt for Gemini 2.0
        prompt = f"""
        You are an expert evaluator of AI responses. Please evaluate the following response to the given user query.
        
        User Query: {user_query}
        
        Response: {response}
        
        Please provide your evaluation in the following JSON format:
        {{
            "rating": <integer from 1 to 5>,
            "explanation": <explanation of your evaluation>
        }}
        
        Where:
        - Rating 1 = Poor (does not address the query)
        - Rating 2 = Below Average (partially addresses the query but has significant gaps)
        - Rating 3 = Average (addresses the query but could be improved)
        - Rating 4 = Good (addresses the query well)
        - Rating 5 = Excellent (addresses the query completely and provides additional value)
        
        Provide just the JSON format with no additional text.
        """
        
        # Generate evaluation
        evaluation = await self.model.generate_content_async(prompt)
        
        # Parse the evaluation result
        try:
            evaluation_text = evaluation.text.strip()
            # Extract the JSON from the response if it's surrounded by other text
            start_idx = evaluation_text.find('{')
            end_idx = evaluation_text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = evaluation_text[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                result = json.loads(evaluation_text)
            
            # Ensure result has required fields
            if "rating" not in result or "explanation" not in result:
                raise ValueError("Response missing required fields")
                
            return {
                "rating": int(result["rating"]),
                "explanation": result["explanation"],
                "user_query": user_query,
                "evaluated_response": response
            }
        except Exception as e:
            # Fallback for parsing errors
            return {
                "rating": 3,
                "explanation": f"Error parsing evaluation: {str(e)}. Original response: {evaluation_text}",
                "user_query": user_query,
                "evaluated_response": response
            } 