import logging
from typing import Any

from utils.base_task_manager import BaseTaskManager
from common.types import Task, TaskStatus, TaskState

logger = logging.getLogger(__name__)

class CriticTaskManager(BaseTaskManager):
    """
    Task manager for the Critic Agent that handles all lifecycle operations
    specific to evaluating responses using Gemini 1.5 Flash
    """
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing CriticTaskManager")
        self.evaluation_scores = {}  # Store evaluation scores by task ID
    
    async def preprocess_task(self, task: Task) -> Task:
        """
        Preprocess a task before handling it
        
        Args:
            task: The task to preprocess
            
        Returns:
            Task: The preprocessed task
        """
        logger.info(f"Preprocessing task {task.id} for Critic Agent")
        # Initialize evaluation metadata for this task
        self.evaluation_scores[task.id] = {
            "score": 0.0,
            "feedback": "",
            "evaluation_complete": False
        }
        return task
    
    async def postprocess_task(self, task: Task) -> Task:
        """
        Postprocess a task after handling it
        
        Args:
            task: The task to postprocess
            
        Returns:
            Task: The postprocessed task
        """
        logger.info(f"Postprocessing task {task.id} for Critic Agent")
        
        # Mark evaluation as complete
        if task.id in self.evaluation_scores:
            self.evaluation_scores[task.id]["evaluation_complete"] = True
        
        return task
    
    def get_evaluation_result(self, task_id: str) -> dict:
        """
        Get the evaluation result for a task
        
        Args:
            task_id: The ID of the task
            
        Returns:
            dict: The evaluation result
        """
        if task_id in self.evaluation_scores:
            return self.evaluation_scores[task_id]
        return {"score": 0.0, "feedback": "No evaluation found", "evaluation_complete": False} 