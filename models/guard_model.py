import os
import re
from typing import Dict, Any, Optional
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

from config.config import GUARD_MODEL


class Guard2Model:
    """
    Interface for Guard-2 vulnerability detection model from Meta
    """
    
    def __init__(self):
        """
        Initialize the Guard-2 model using HuggingFace transformers
        """
        # Get HuggingFace token from environment variables
        huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
        if not huggingface_token:
            raise ValueError("HUGGINGFACE_TOKEN environment variable is not set")
        
        # Define model storage location
        model_dir = Path("prompt_guard")
        model_dir.mkdir(exist_ok=True)
        
        # Check if we're using GPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        
        # Load model and tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                GUARD_MODEL,
                token=huggingface_token,
                cache_dir=model_dir
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                GUARD_MODEL,
                token=huggingface_token,
                cache_dir=model_dir,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map=device
            )
            
            # Create a text generation pipeline
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if device == "cuda" else -1
            )
        except Exception as e:
            raise ValueError(f"Failed to load Guard-2 model: {str(e)}")
    
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
        
        # Generate response using the model
        response_list = self.pipe(
            prompt,
            max_new_tokens=512,
            temperature=0.1,
            top_p=0.95,
            do_sample=True
        )
        
        # Extract response text
        response_text = response_list[0]["generated_text"]
        
        # Remove the prompt from the response
        response_text = response_text.replace(prompt, "").strip()
        
        # Determine safety based on presence of "UNSAFE" in response
        is_safe = "UNSAFE" not in response_text.upper()
        
        return {
            "is_safe": is_safe,
            "explanation": response_text,
            "original_query": user_query
        } 