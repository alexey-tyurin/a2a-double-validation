import os
import re
from typing import Dict, Any, Optional
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from config.config import GUARD_MODEL


class Guard2Model:
    """
    Interface for Llama Guard security model from Meta
    """
    
    def __init__(self):
        """
        Initialize the Llama Guard model using HuggingFace transformers
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
                torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
                device_map=device
            )
        except Exception as e:
            raise ValueError(f"Failed to load Llama Guard model: {str(e)}")
    
    async def check_vulnerability(self, user_query: str) -> Dict[str, Any]:
        """
        Check if a user query contains vulnerabilities
        
        Args:
            user_query: The user query to check
            
        Returns:
            Dict: A dictionary containing safety assessment
        """
        # Format chat for Llama Guard
        chat = [
            {"role": "user", "content": user_query}
        ]
        
        # Generate input ids from chat template
        input_ids = self.tokenizer.apply_chat_template(chat, return_tensors="pt").to(self.model.device)
        
        # Generate response
        with torch.no_grad():
            output = self.model.generate(input_ids=input_ids, max_new_tokens=100, pad_token_id=0)
        
        # Extract response text
        prompt_len = input_ids.shape[-1]
        response_text = self.tokenizer.decode(output[0][prompt_len:], skip_special_tokens=True)
        
        # Determine safety based on response
        is_safe = "safe" in response_text.lower()
        
        return {
            "is_safe": is_safe,
            "explanation": response_text,
            "original_query": user_query
        } 