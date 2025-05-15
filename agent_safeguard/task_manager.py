import logging
from typing import Any, Dict

from utils.base_task_manager import BaseTaskManager
from common.types import Task, TaskStatus, TaskState

logger = logging.getLogger(__name__)

class SafeguardTaskManager(BaseTaskManager):
    """
    Task manager for the Safeguard Agent that handles all lifecycle operations
    specific to checking user queries for vulnerabilities using Guard-2
    """
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing SafeguardTaskManager")
        self.vulnerability_checks = {}  # Store vulnerability check results by task ID
    
    async def preprocess_task(self, task: Task) -> Task:
        """
        Preprocess a task before handling it
        
        Args:
            task: The task to preprocess
            
        Returns:
            Task: The preprocessed task
        """
        logger.info(f"Preprocessing task {task.id} for Safeguard Agent")
        # Initialize vulnerability check data
        self.vulnerability_checks[task.id] = {
            "is_safe": None,  # Will be set to boolean after check
            "risk_level": "unknown",
            "risk_factors": [],
            "check_complete": False
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
        logger.info(f"Postprocessing task {task.id} for Safeguard Agent")
        
        # Mark vulnerability check as complete
        if task.id in self.vulnerability_checks:
            self.vulnerability_checks[task.id]["check_complete"] = True
        
        return task
    
    def get_safety_check_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get the safety check result for a task
        
        Args:
            task_id: The ID of the task
            
        Returns:
            Dict[str, Any]: The safety check result
        """
        if task_id in self.vulnerability_checks:
            return self.vulnerability_checks[task_id]
        return {
            "is_safe": None, 
            "risk_level": "unknown", 
            "risk_factors": [], 
            "check_complete": False
        } 