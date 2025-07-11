"""
Async File Save Agent

Agent responsible for handling all filesystem operations securely with MCP Roots.
Demonstrates async MCP client with security restrictions.
"""

import logging
from typing import Dict

from .async_base_agent import AsyncBaseAgent, MCPClientMixin
from ..protocols.acp_schema import (
    ACPMessage, ACPMsgType, TaskAssignPayload, StatusUpdatePayload, 
    DataSubmitPayload, LogBroadcastPayload
)

logger = logging.getLogger(__name__)


class AsyncFileSaveAgent(AsyncBaseAgent, MCPClientMixin):
    """
    Asynchronous agent that handles secure file operations.
    
    Demonstrates:
    - Async MCP client with security restrictions
    - MCP Roots security boundary enforcement
    - File organization and naming strategies
    - Error handling for filesystem operations
    """
    
    def __init__(self, agent_id: str, message_bus, mcp_servers: Dict[str, str]):
        """Initialize the async file save agent."""
        AsyncBaseAgent.__init__(self, agent_id, message_bus, mcp_servers)
        MCPClientMixin.__init__(self)
        
        self.orchestrator_id = "orchestrator"
        
        logger.info(f"[{self.agent_id}] Async File Save Agent initialized")
    
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
        """Handle file save task assignments."""
        try:
            payload = TaskAssignPayload(**message.payload)
            
            if payload.task_type == "save_file":
                await self._save_file_securely(payload.task_data)
            else:
                logger.warning(f"[{self.agent_id}] Unknown task type: {payload.task_type}")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in task assignment: {e}")
            await self._send_error_status(str(e))
    
    async def _save_file_securely(self, task_data: Dict):
        """Save file content securely using MCP Roots security model."""
        file_path = task_data.get("file_path")
        content = task_data.get("content", "")
        task_id = task_data.get("task_id", "unknown")
        
        if not file_path:
            error_msg = "No file path provided for save operation"
            logger.error(f"[{self.agent_id}] {error_msg}")
            await self._send_error_status(error_msg, task_id)
            return
        
        if not content:
            logger.warning(f"[{self.agent_id}] Empty content provided for {file_path}")
        
        logger.info(f"[{self.agent_id}] Starting secure file save: {file_path}")
        
        try:
            # Send initial status update
            await self._send_status_update("file_save_starting", 10.0, task_id)
            
            # First, validate the path using MCP server
            await self._send_status_update("validating_path", 25.0, task_id)
            
            validation_result = await self._validate_file_path(file_path)
            
            if not validation_result.get("is_allowed", False):
                error_msg = f"File path not allowed by MCP Roots security: {file_path}"
                logger.error(f"[{self.agent_id}] SECURITY VIOLATION: {error_msg}")
                await self._send_error_status(error_msg, task_id)
                return
            
            logger.info(f"[{self.agent_id}] Path validation successful: {file_path}")
            
            # Prepare save parameters
            await self._send_status_update("preparing_file_save", 50.0, task_id)
            
            save_params = {
                "file_path": file_path,
                "content": content
            }
            
            logger.debug(f"[{self.agent_id}] Calling MCP save_file tool")
            
            # Call MCP filesystem server to save file
            result = await self.call_mcp_tool(
                server_name="filesystem",
                tool_name="save_file",
                params=save_params
            )
            
            # Process save result
            success = result.get("success", False)
            bytes_written = result.get("bytes_written", 0)
            saved_path = result.get("file_path", file_path)
            
            if success:
                logger.info(f"[{self.agent_id}] File saved successfully: {saved_path} ({bytes_written} bytes)")
                
                # Send completion status
                await self._send_status_update("file_save_complete", 100.0, task_id)
                
                # Send success result to orchestrator
                save_data = {
                    "file_path": saved_path,
                    "bytes_written": bytes_written,
                    "content_length": len(content),
                    "save_successful": True
                }
                
                data_message = self.create_message(
                    receiver_id=self.orchestrator_id,
                    msg_type=ACPMsgType.DATA_SUBMIT,
                    payload=DataSubmitPayload(
                        data_type="file_save_result",
                        data=save_data,
                        source="filesystem",
                        task_id=task_id
                    ).model_dump()
                )
                
                await self.send_message(data_message)
                
                # Broadcast success log
                log_message = self.create_message(
                    topic="logs",
                    msg_type=ACPMsgType.LOG_BROADCAST,
                    payload=LogBroadcastPayload(
                        level="INFO",
                        message=f"File saved successfully: {saved_path} ({bytes_written} bytes)",
                        component=self.agent_id
                    ).model_dump()
                )
                
                await self.send_message(log_message)
                
            else:
                error_msg = f"File save operation failed for {file_path}"
                logger.error(f"[{self.agent_id}] {error_msg}")
                await self._send_error_status(error_msg, task_id)
                
        except Exception as e:
            error_msg = f"File save failed for {file_path}: {e}"
            logger.error(f"[{self.agent_id}] {error_msg}")
            await self._send_error_status(error_msg, task_id)
            
            # Broadcast error log
            error_log = self.create_message(
                topic="logs",
                msg_type=ACPMsgType.LOG_BROADCAST,
                payload=LogBroadcastPayload(
                    level="ERROR",
                    message=f"File save failed: {file_path} - {error_msg}",
                    component=self.agent_id
                ).model_dump()
            )
            
            await self.send_message(error_log)
    
    async def _validate_file_path(self, file_path: str) -> Dict:
        """Validate file path using MCP filesystem server."""
        try:
            validation_params = {
                "path": file_path
            }
            
            result = await self.call_mcp_tool(
                server_name="filesystem",
                tool_name="validate_path",
                params=validation_params
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Path validation failed: {e}")
            return {"is_allowed": False, "error": str(e)}
    
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
        await self._send_status_update(f"file_save_failed: {error_message}", 0.0, task_id)
    
    def get_capabilities(self) -> Dict[str, str]:
        """Return agent capabilities."""
        return {
            "agent_type": "file_save_agent",
            "primary_function": "secure_file_operations",
            "mcp_tools": ["save_file", "validate_path"],
            "supported_tasks": ["save_file"],
            "security_model": "MCP Roots",
            "async_capable": True
        }
