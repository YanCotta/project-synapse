"""
Async Search Agent

Agent responsible for finding information sources online using async MCP web search tools.
"""

import logging
from typing import Dict

from .async_base_agent import AsyncBaseAgent, MCPClientMixin
from ..protocols.acp_schema import (
    ACPMessage, ACPMsgType, TaskAssignPayload, StatusUpdatePayload, 
    DataSubmitPayload, LogBroadcastPayload
)

logger = logging.getLogger(__name__)


class AsyncSearchAgent(AsyncBaseAgent, MCPClientMixin):
    """
    Asynchronous agent that searches the web for information sources.
    
    Demonstrates:
    - Async MCP client functionality for web search operations
    - Integration with Primary Tooling MCP Server
    - Progress reporting during search operations
    - Error handling and graceful degradation
    """
    
    def __init__(self, agent_id: str, message_bus, mcp_servers: Dict[str, str]):
        """Initialize the async search agent."""
        AsyncBaseAgent.__init__(self, agent_id, message_bus, mcp_servers)
        MCPClientMixin.__init__(self)
        
        self.orchestrator_id = "orchestrator"
        
        logger.info(f"[{self.agent_id}] Async Search Agent initialized")
    
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
        """Handle search task assignments."""
        try:
            payload = TaskAssignPayload(**message.payload)
            
            if payload.task_type == "web_search":
                await self._perform_web_search(payload.task_data)
            else:
                logger.warning(f"[{self.agent_id}] Unknown task type: {payload.task_type}")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in task assignment: {e}")
            await self._send_error_status(str(e))
    
    async def _perform_web_search(self, task_data: Dict):
        """Perform web search using async MCP tools."""
        query = task_data.get("query")
        task_id = task_data.get("task_id", "unknown")
        max_results = task_data.get("max_results", 5)
        
        if not query:
            error_msg = "No search query provided"
            logger.error(f"[{self.agent_id}] {error_msg}")
            await self._send_error_status(error_msg)
            return
        
        logger.info(f"[{self.agent_id}] Starting web search for: '{query}'")
        
        try:
            # Send initial status update
            await self._send_status_update("searching", 10.0, task_id)
            
            # Call MCP search tool
            search_params = {
                "query": query
            }
            
            logger.debug(f"[{self.agent_id}] Calling MCP search tool with params: {search_params}")
            
            # Use async MCP call
            result = await self.call_mcp_tool(
                server_name="primary_tooling",
                tool_name="search_web",
                params=search_params
            )
            
            # Process results
            results = result.get("results", [])
            query_processed = result.get("query_processed", query)
            
            # Limit results if requested
            if max_results and len(results) > max_results:
                results = results[:max_results]
            
            logger.info(f"[{self.agent_id}] Search completed: {len(results)} results found")
            
            # Send progress update
            await self._send_status_update("search_complete", 100.0, task_id)
            
            # Send results to orchestrator
            search_data = {
                "query": query,
                "query_processed": query_processed,
                "results": results,
                "result_count": len(results)
            }
            
            data_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.DATA_SUBMIT,
                payload=DataSubmitPayload(
                    data_type="search_results",
                    data=search_data,
                    source="web_search",
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
                    message=f"Web search completed: '{query}' -> {len(results)} results",
                    component=self.agent_id
                ).model_dump()
            )
            
            await self.send_message(log_message)
            
            logger.info(f"[{self.agent_id}] Successfully completed search for: '{query}'")
            
        except Exception as e:
            error_msg = f"Web search failed for '{query}': {e}"
            logger.error(f"[{self.agent_id}] {error_msg}")
            
            # Send error status to orchestrator
            await self._send_error_status(error_msg, task_id)
            
            # Broadcast error log
            error_log = self.create_message(
                topic="logs",
                msg_type=ACPMsgType.LOG_BROADCAST,
                payload=LogBroadcastPayload(
                    level="ERROR",
                    message=f"Web search failed: '{query}' - {error_msg}",
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
        await self._send_status_update(f"search_failed: {error_message}", 0.0, task_id)
    
    def get_capabilities(self) -> Dict[str, str]:
        """Return agent capabilities."""
        return {
            "agent_type": "search_agent",
            "primary_function": "web_search",
            "mcp_tools": ["search_web"],
            "supported_tasks": ["web_search"],
            "async_capable": True
        }
