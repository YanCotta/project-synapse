"""
Search Agent

Agent responsible for finding information sources online using MCP web search tools.
"""

from typing import Dict
from .base_agent import BaseAgent, MCPClientMixin
from ..protocols.acp_schema import ACPMessage, ACPMsgType, TaskAssignPayload, StatusUpdatePayload, DataSubmitPayload, LogBroadcastPayload


class SearchAgent(BaseAgent, MCPClientMixin):
    """
    Agent that searches the web for information sources.
    
    Demonstrates MCP client functionality for web search operations.
    """
    
    def __init__(self, agent_id: str = "search_agent", orchestrator_id: str = "orchestrator", 
                 message_bus: Dict = None):
        """Initialize the Search Agent."""
        BaseAgent.__init__(self, agent_id, message_bus)
        MCPClientMixin.__init__(self)
        
        self.orchestrator_id = orchestrator_id
        
        print(f"[{self.agent_id}] Search Agent initialized")
    
    def handle_message(self, message: ACPMessage):
        """Handle incoming messages."""
        if message.msg_type == ACPMsgType.TASK_ASSIGN:
            self._handle_task_assignment(message)
        else:
            print(f"[{self.agent_id}] Unhandled message type: {message.msg_type.value}")
    
    def _handle_task_assignment(self, message: ACPMessage):
        """Handle search task assignments."""
        payload = TaskAssignPayload(**message.payload)
        
        if payload.task_type == "web_search":
            self._perform_web_search(payload.task_data)
        else:
            print(f"[{self.agent_id}] Unknown task type: {payload.task_type}")
    
    def _perform_web_search(self, task_data: Dict):
        """Perform web search using MCP tools."""
        query = task_data.get("query")
        task_id = task_data.get("task_id", "unknown")
        max_results = task_data.get("max_results", 5)
        
        print(f"[{self.agent_id}] Performing web search for: '{query}'")
        
        # Send status update
        status_message = self.create_message(
            receiver_id=self.orchestrator_id,
            msg_type=ACPMsgType.STATUS_UPDATE,
            payload=StatusUpdatePayload(
                status="searching_web",
                progress=25.0,
                task_id=task_id
            ).model_dump()
        )
        self.send_message(status_message)
        
        try:
            # Call MCP search tool
            search_params = {"query": query}
            result = self.call_mcp_tool(
                server_name="primary_tooling",
                tool_name="search_web",
                params=search_params
            )
            
            # Send results back to orchestrator
            data_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.DATA_SUBMIT,
                payload=DataSubmitPayload(
                    data_type="search_results",
                    data=result,
                    source="web_search",
                    task_id=task_id
                ).model_dump()
            )
            self.send_message(data_message)
            
            # Broadcast completion log
            results_count = len(result.get("results", []))
            log_message = self.create_message(
                topic="logs",
                msg_type=ACPMsgType.LOG_BROADCAST,
                payload=LogBroadcastPayload(
                    level="INFO",
                    message=f"Web search completed: found {results_count} results for '{query}'",
                    component=self.agent_id
                ).model_dump()
            )
            self.send_message(log_message)
            
        except Exception as e:
            print(f"[{self.agent_id}] Search failed: {e}")
            
            # Send error status
            error_status = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.STATUS_UPDATE,
                payload=StatusUpdatePayload(
                    status=f"search_failed: {e}",
                    progress=0.0,
                    task_id=task_id
                ).model_dump()
            )
            self.send_message(error_status)
