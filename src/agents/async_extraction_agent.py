"""
Async Extraction Agent

Agent responsible for extracting content from URLs and documents asynchronously.
Demonstrates async MCP streaming with progress notifications.
"""

import logging
from typing import Dict

from .async_base_agent import AsyncBaseAgent, MCPClientMixin
from ..protocols.acp_schema import (
    ACPMessage, ACPMsgType, TaskAssignPayload, StatusUpdatePayload, 
    DataSubmitPayload, LogBroadcastPayload
)

logger = logging.getLogger(__name__)


class AsyncExtractionAgent(AsyncBaseAgent, MCPClientMixin):
    """
    Asynchronous agent that extracts raw text content from URLs and documents.
    
    This agent demonstrates:
    - Async MCP streaming with real-time progress notifications
    - Integration with Primary Tooling MCP Server for content extraction
    - Progress reporting during long-running operations
    - Error handling and recovery mechanisms
    """
    
    def __init__(self, agent_id: str, message_bus, mcp_servers: Dict[str, str]):
        """
        Initialize the async extraction agent.
        
        Args:
            agent_id: Unique identifier for this agent
            message_bus: RabbitMQ message bus for communication
            mcp_servers: Dictionary mapping MCP server names to URLs
        """
        AsyncBaseAgent.__init__(self, agent_id, message_bus, mcp_servers)
        MCPClientMixin.__init__(self)
        
        self.orchestrator_id = "orchestrator"
        self.current_task = None
        
        logger.info(f"[{self.agent_id}] Async Extraction Agent initialized")
    
    async def handle_message(self, message: ACPMessage):
        """Handle incoming ACP messages."""
        try:
            if message.msg_type == ACPMsgType.TASK_ASSIGN:
                await self._handle_task_assignment(message)
            else:
                logger.warning(f"[{self.agent_id}] Unhandled message type: {message.msg_type.value}")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error handling message: {e}")
    
    async def _handle_task_assignment(self, message: ACPMessage):
        """Handle content extraction task assignments."""
        try:
            payload = TaskAssignPayload(**message.payload)
            
            if payload.task_type == "extract_content":
                await self._extract_content_from_url(payload.task_data)
            else:
                logger.warning(f"[{self.agent_id}] Unknown task type: {payload.task_type}")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in task assignment: {e}")
            await self._send_error_status(str(e))
    
    async def _extract_content_from_url(self, task_data: Dict):
        """Extract content from URL with real-time progress monitoring."""
        url = task_data.get("url")
        task_id = task_data.get("task_id", "unknown")
        source_description = task_data.get("source_description", "unknown_source")
        
        if not url:
            error_msg = "No URL provided for extraction"
            logger.error(f"[{self.agent_id}] {error_msg}")
            await self._send_error_status(error_msg, task_id)
            return
        
        logger.info(f"[{self.agent_id}] Starting content extraction from: {url}")
        
        try:
            # Send initial status update
            await self._send_status_update("extraction_starting", 5.0, task_id)
            
            # Prepare extraction parameters
            extraction_params = {
                "url": url
            }
            
            logger.debug(f"[{self.agent_id}] Calling MCP extraction tool with params: {extraction_params}")
            
            # Create progress callback for streaming updates
            async def progress_callback(progress_data):
                """Handle progress updates from MCP streaming."""
                message = progress_data.get('message', 'Processing...')
                percentage = progress_data.get('percentage', 0)
                phase = progress_data.get('phase', 'unknown')
                
                # Forward progress to orchestrator
                status = f"extracting_{phase}: {message}"
                await self._send_status_update(status, percentage, task_id)
                
                logger.debug(f"[{self.agent_id}] Extraction progress: {message} ({percentage}%)")
            
            # Call streaming MCP tool with progress notifications
            result = await self.call_mcp_tool_streaming(
                server_name="primary_tooling",
                tool_name="browse_and_extract",
                params=extraction_params,
                progress_callback=progress_callback
            )
            
            # Process extraction result
            extracted_url = result.get("url", url)
            title = result.get("title", f"Content from {url}")
            content = result.get("content", "")
            word_count = result.get("word_count", 0)
            
            logger.info(f"[{self.agent_id}] Extraction completed: {word_count} words from {url}")
            
            # Send completion status
            await self._send_status_update("extraction_complete", 100.0, task_id)
            
            # Prepare data for submission
            extraction_data = {
                "url": extracted_url,
                "title": title,
                "content": content,
                "word_count": word_count,
                "source_description": source_description,
                "extraction_successful": True
            }
            
            # Send extracted content to orchestrator
            data_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.DATA_SUBMIT,
                payload=DataSubmitPayload(
                    data_type="extracted_content",
                    data=extraction_data,
                    source=url,
                    task_id=task_id
                ).model_dump()
            )
            
            await self.send_message(data_message)
            
            # Broadcast completion log
            log_message = self.create_message(
                topic="logs",
                msg_type=ACPMsgType.LOG_BROADCAST,
                payload=LogBroadcastPayload(
                    level="INFO",
                    message=f"Content extraction complete: {url} ({word_count} words)",
                    component=self.agent_id
                ).model_dump()
            )
            
            await self.send_message(log_message)
            
            logger.info(f"[{self.agent_id}] Successfully extracted content from {url}")
            
        except Exception as e:
            error_msg = f"Failed to extract content from {url}: {e}"
            logger.error(f"[{self.agent_id}] {error_msg}")
            
            # Send error status to orchestrator
            await self._send_error_status(error_msg, task_id)
            
            # Send failed extraction data
            failed_data = {
                "url": url,
                "title": f"Failed extraction from {url}",
                "content": "",
                "word_count": 0,
                "source_description": source_description,
                "extraction_successful": False,
                "error_message": error_msg
            }
            
            data_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.DATA_SUBMIT,
                payload=DataSubmitPayload(
                    data_type="extracted_content",
                    data=failed_data,
                    source=url,
                    task_id=task_id
                ).model_dump()
            )
            
            await self.send_message(data_message)
            
            # Broadcast error log
            error_log = self.create_message(
                topic="logs",
                msg_type=ACPMsgType.LOG_BROADCAST,
                payload=LogBroadcastPayload(
                    level="ERROR",
                    message=f"Content extraction failed: {url} - {error_msg}",
                    component=self.agent_id
                ).model_dump()
            )
            
            await self.send_message(error_log)
    
    async def _send_status_update(self, status: str, progress: float = None, task_id: str = None):
        """Send status update to orchestrator."""
        status_message = self.create_message(
            receiver_id=self.orchestrator_id,
            msg_type=ACPMsgType.STATUS_UPDATE,
            payload=StatusUpdatePayload(
                status=status,
                progress=progress,
                task_id=task_id
            ).model_dump()
        )
        
        await self.send_message(status_message)
        logger.debug(f"[{self.agent_id}] Status update sent: {status}")
    
    async def _send_error_status(self, error_message: str, task_id: str = None):
        """Send error status to orchestrator."""
        await self._send_status_update(f"extraction_failed: {error_message}", 0.0, task_id)
    
    def get_capabilities(self) -> Dict[str, str]:
        """Return agent capabilities."""
        return {
            "agent_type": "extraction_agent",
            "primary_function": "content_extraction",
            "mcp_tools": ["browse_and_extract"],
            "supported_tasks": ["extract_content"],
            "streaming_support": True,
            "progress_notifications": True,
            "async_capable": True
        }
