import os
import re
from typing import Dict, Any, Optional
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from config.config import GUARD_MODEL


class Guard2Model:
    """
    Interface for Prompt Guard 2 vulnerability detection model from Meta
    """
    
    def __init__(self):
        """
        Initialize the Prompt Guard 2 model using HuggingFace transformers
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
            
            self.model = AutoModelForSequenceClassification.from_pretrained(
                GUARD_MODEL,
                token=huggingface_token,
                cache_dir=model_dir,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map=device
            )
        except Exception as e:
            raise ValueError(f"Failed to load Prompt Guard 2 model: {str(e)}")
    
    async def check_vulnerability(self, user_query: str) -> Dict[str, Any]:
        """
        Check if a user query contains vulnerabilities
        
        Args:
            user_query: The user query to check
            
        Returns:
            Dict: A dictionary containing safety assessment
        """
        # Tokenize input
        inputs = self.tokenizer(user_query, return_tensors="pt").to(self.model.device)
        
        # Get classification results
        with torch.no_grad():
            logits = self.model(**inputs).logits
        
        # Get predicted class (0 = benign, 1 = malicious)
        predicted_class_id = logits.argmax().item()
        class_name = self.model.config.id2label[predicted_class_id]
        
        # Determine safety (benign means safe)
        is_safe = predicted_class_id == 0

        return {
            "is_safe": is_safe,
            "explanation": f"Classification: {class_name}",
            "original_query": user_query
        } 