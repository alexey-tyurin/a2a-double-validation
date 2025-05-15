import asyncio
import logging
from collections.abc import AsyncIterable
from uuid import uuid4
from typing import Callable, Any

from common.server.task_manager import InMemoryTaskManager
from common.types import (
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    JSONRPCResponse,
    Task,
    TaskStatus,
    TaskState,
    TaskStatusUpdateEvent,
    Artifact
)

logger = logging.getLogger(__name__)

class BaseTaskManager(InMemoryTaskManager):
    """
    Base task manager implementation that all agent-specific task managers will inherit from
    """
    
    def __init__(self):
        super().__init__()
        self.task_handler: Callable[[Task], Task] = None
        
    def register_task_handler(self, handler: Callable[[Task], Task]):
        """
        Register a handler for processing tasks
        
        Args:
            handler: A function that takes a Task and returns a Task
        """
        self.task_handler = handler
        
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle a send task request
        
        Args:
            request: The send task request
            
        Returns:
            SendTaskResponse: The response to the request
        """
        logger.info(f'Received task {request.params.id}')
        
        try:
            # Create or update the task
            task = await self.upsert_task(request.params)
            
            # Process the task if a handler is registered
            if self.task_handler:
                task.status = TaskStatus(state=TaskState.WORKING)
                processed_task = await self.task_handler(task)
                # Update the task in the store
                task = await self.update_store(
                    processed_task.id, 
                    processed_task.status, 
                    processed_task.artifacts or []
                )
            else:
                # Just mark as completed if no handler
                task.status = TaskStatus(state=TaskState.COMPLETED)
                await self.update_store(task.id, task.status, [])
            
            # Append history if needed
            result_task = self.append_task_history(task, request.params.historyLength)
            
            return SendTaskResponse(id=request.id, result=result_task)
        except Exception as e:
            logger.error(f'Error processing task: {e}')
            task.status = TaskStatus(state=TaskState.FAILED)
            await self.update_store(task.id, task.status, [])
            return SendTaskResponse(id=request.id, result=task)
    
    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """
        Handle a send task subscribe request (streaming)
        
        Args:
            request: The send task subscribe request
            
        Returns:
            AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse: The response to the request
        """
        logger.info(f'Received streaming task request {request.params.id}')
        
        # For simplicity, we'll create a minimal implementation
        # This is not a full streaming implementation
        try:
            # Set up SSE consumer for streaming
            sse_event_queue = await self.setup_sse_consumer(request.params.id)
            
            # Create or update the task
            task = await self.upsert_task(request.params)
            
            # Process the task if a handler is registered
            if self.task_handler:
                task.status = TaskStatus(state=TaskState.WORKING)
                
                # Create a status update event
                status_event = TaskStatusUpdateEvent(
                    id=task.id,
                    status=task.status,
                    final=False
                )
                
                # Enqueue the event for streaming
                await self.enqueue_events_for_sse(task.id, status_event)
                
                # Process the task
                processed_task = await self.task_handler(task)
                
                # Update the task in the store
                task = await self.update_store(
                    processed_task.id, 
                    processed_task.status, 
                    processed_task.artifacts or []
                )
                
                # Create a final status update event
                final_status_event = TaskStatusUpdateEvent(
                    id=task.id,
                    status=task.status,
                    final=True
                )
                
                # Enqueue the final event for streaming
                await self.enqueue_events_for_sse(task.id, final_status_event)
            else:
                # Just mark as completed if no handler
                task.status = TaskStatus(state=TaskState.COMPLETED)
                await self.update_store(task.id, task.status, [])
                
                # Create a final status update event
                final_status_event = TaskStatusUpdateEvent(
                    id=task.id,
                    status=task.status,
                    final=True
                )
                
                # Enqueue the final event for streaming
                await self.enqueue_events_for_sse(task.id, final_status_event)
            
            # Return the streaming response
            return await self.dequeue_events_for_sse(
                request.id, task.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f'Error in streaming task: {e}')
            return JSONRPCResponse(
                id=request.id,
                error={"code": -32000, "message": f"Internal error: {str(e)}"}
            ) 