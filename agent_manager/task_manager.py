import logging
import asyncio
from typing import Any, Dict, List, Optional

from utils.base_task_manager import BaseTaskManager
from common.types import Task, TaskStatus, TaskState

logger = logging.getLogger(__name__)

class ManagerTaskManager(BaseTaskManager):
    """
    Task manager for the Manager Agent that handles all lifecycle operations
    specific to coordinating process flow between agents
    """
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing ManagerTaskManager")
        self.workflow_states = {}  # Store workflow states by task ID
        self.agent_tasks = {}  # Map parent task IDs to child agent tasks
    
    async def preprocess_task(self, task: Task) -> Task:
        """
        Preprocess a task before handling it
        
        Args:
            task: The task to preprocess
            
        Returns:
            Task: The preprocessed task
        """
        task_id = task["id"] if isinstance(task, dict) else task.id
        logger.info(f"Preprocessing task {task_id} for Manager Agent")
        
        # Initialize workflow state for this task
        self.workflow_states[task_id] = {
            "current_stage": "init",
            "completed_stages": [],
            "pending_stages": ["safeguard", "processor", "critic"],
            "workflow_complete": False
        }
        
        # Initialize agent tasks mapping
        self.agent_tasks[task_id] = {
            "safeguard_task_id": None,
            "processor_task_id": None,
            "critic_task_id": None
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
        task_id = task["id"] if isinstance(task, dict) else task.id
        logger.info(f"Postprocessing task {task_id} for Manager Agent")
        
        # Mark workflow as complete
        if task_id in self.workflow_states:
            self.workflow_states[task_id]["workflow_complete"] = True
            self.workflow_states[task_id]["current_stage"] = "complete"
        
        return task
    
    def register_agent_task(self, parent_task_id: str, agent_type: str, agent_task_id: str) -> None:
        """
        Register an agent task with its parent task
        
        Args:
            parent_task_id: The ID of the parent task
            agent_type: The type of agent (safeguard, processor, critic)
            agent_task_id: The ID of the agent task
        """
        if parent_task_id in self.agent_tasks:
            if agent_type == "safeguard":
                self.agent_tasks[parent_task_id]["safeguard_task_id"] = agent_task_id
            elif agent_type == "processor":
                self.agent_tasks[parent_task_id]["processor_task_id"] = agent_task_id
            elif agent_type == "critic":
                self.agent_tasks[parent_task_id]["critic_task_id"] = agent_task_id
    
    def advance_workflow(self, task_id: str, next_stage: str) -> None:
        """
        Advance the workflow to the next stage
        
        Args:
            task_id: The ID of the task
            next_stage: The next stage to advance to
        """
        if task_id in self.workflow_states:
            current_stage = self.workflow_states[task_id]["current_stage"]
            
            # Add current stage to completed stages
            if current_stage != "init" and current_stage != "complete":
                if current_stage not in self.workflow_states[task_id]["completed_stages"]:
                    self.workflow_states[task_id]["completed_stages"].append(current_stage)
            
            # Set new current stage
            self.workflow_states[task_id]["current_stage"] = next_stage
            
            # Remove from pending stages
            if next_stage in self.workflow_states[task_id]["pending_stages"]:
                self.workflow_states[task_id]["pending_stages"].remove(next_stage)
    
    def get_workflow_state(self, task_id: str) -> Dict[str, Any]:
        """
        Get the workflow state for a task
        
        Args:
            task_id: The ID of the task
            
        Returns:
            Dict[str, Any]: The workflow state
        """
        if task_id in self.workflow_states:
            return self.workflow_states[task_id]
        return {
            "current_stage": "unknown",
            "completed_stages": [],
            "pending_stages": [],
            "workflow_complete": False
        } 