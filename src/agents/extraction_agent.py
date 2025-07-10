"""
Extraction Agent

Agent responsible for extracting content from URLs and documents.
Demonstrates A2A communication with the Orchestrator and MCP client capabilities.
"""

from typing import Dict
from .base_agent import BaseAgent, MCPClientMixin
from ..protocols.acp_schema import ACPMessage, ACPMsgType, TaskAssignPayload, StatusUpdatePayload, DataSubmitPayload, LogBroadcastPayload
from ..protocols.mcp_schemas import MCPContext


class ExtractionAgent(BaseAgent, MCPClientMixin):
    """
    Agent that extracts raw text content from URLs and documents.
    
    This agent demonstrates:
    - A2A communication with the OrchestratorAgent
    - MCP client functionality for content extraction
    - Progress reporting during long-running operations
    - Broadcasting status updates to the logging system
    """
    
    def __init__(self, agent_id: str = "extraction_agent", orchestrator_id: str = "orchestrator", 
                 message_bus: Dict = None):
        """
        Initialize the Extraction Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            orchestrator_id: ID of the orchestrator agent for communication
            message_bus: Shared message bus for inter-agent communication
        """
        BaseAgent.__init__(self, agent_id, message_bus)
        MCPClientMixin.__init__(self)
        
        self.orchestrator_id = orchestrator_id
        self.current_task = None
        
        print(f"[{self.agent_id}] Initialized with orchestrator: {orchestrator_id}")
    
    def handle_message(self, message: ACPMessage):
        """
        Handle incoming messages from other agents.
        
        Args:
            message: ACP message to process
        """
        print(f"[{self.agent_id}] Received {message.msg_type.value} from {message.sender_id}")
        
        if message.msg_type == ACPMsgType.TASK_ASSIGN:
            self._handle_task_assignment(message)
        else:
            print(f"[{self.agent_id}] Unhandled message type: {message.msg_type.value}")
    
    def _handle_task_assignment(self, message: ACPMessage):
        """
        Handle a task assignment from the orchestrator.
        
        Args:
            message: Task assignment message
        """
        payload = TaskAssignPayload(**message.payload)
        
        if payload.task_type == "extract_content":
            self._extract_content_from_url(payload.task_data)
        else:
            print(f"[{self.agent_id}] Unknown task type: {payload.task_type}")
    
    def _extract_content_from_url(self, task_data: Dict):
        """
        Extract content from a URL using MCP tools.
        
        Args:
            task_data: Dictionary containing URL and other extraction parameters
        """
        url = task_data.get("url")
        task_id = task_data.get("task_id", "unknown")
        
        if not url:
            print(f"[{self.agent_id}] Error: No URL provided in task data")
            return
        
        print(f"[{self.agent_id}] Starting content extraction from: {url}")
        
        # Send status update to orchestrator
        status_message = self.create_message(
            receiver_id=self.orchestrator_id,
            msg_type=ACPMsgType.STATUS_UPDATE,
            payload=StatusUpdatePayload(
                status="starting_extraction",
                progress=0.0,
                task_id=task_id
            ).model_dump()
        )
        self.send_message(status_message)
        
        try:
            # Create MCP context for progress notifications
            mcp_context = MCPContext(session_id=f"{self.agent_id}_{task_id}")
            
            # Call the browse_and_extract tool via MCP
            extraction_params = {
                "url": url
            }
            
            # This will demonstrate MCP Progress Notifications
            result = self.call_mcp_tool(
                server_name="primary_tooling",
                tool_name="browse_and_extract", 
                params=extraction_params,
                mcp_context=mcp_context
            )
            
            # Send successful result back to orchestrator
            data_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.DATA_SUBMIT,
                payload=DataSubmitPayload(
                    data_type="extracted_content",
                    data=result,
                    source=url,
                    task_id=task_id
                ).model_dump()
            )
            self.send_message(data_message)
            
            # Broadcast completion log
            log_message = self.create_message(
                topic="logs",
                msg_type=ACPMsgType.LOG_BROADCAST,
                payload=LogBroadcastPayload(
                    level="INFO",
                    message=f"Extraction complete for URL: {url} ({result.get('word_count', 0)} words)",
                    component=self.agent_id
                ).model_dump()
            )
            self.send_message(log_message)
            
            print(f"[{self.agent_id}] Successfully extracted content from {url}")
            
        except Exception as e:
            error_msg = f"Failed to extract content from {url}: {e}"
            print(f"[{self.agent_id}] ERROR: {error_msg}")
            
            # Send error status to orchestrator
            error_status = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.STATUS_UPDATE,
                payload=StatusUpdatePayload(
                    status=f"extraction_failed: {error_msg}",
                    progress=0.0,
                    task_id=task_id
                ).model_dump()
            )
            self.send_message(error_status)
            
            # Broadcast error log
            error_log = self.create_message(
                topic="logs",
                msg_type=ACPMsgType.LOG_BROADCAST,
                payload=LogBroadcastPayload(
                    level="ERROR",
                    message=f"Extraction failed for URL: {url} - {error_msg}",
                    component=self.agent_id
                ).model_dump()
            )
            self.send_message(error_log)
    
    def get_capabilities(self) -> Dict[str, str]:
        """
        Return the capabilities of this agent.
        
        Returns:
            Dictionary describing agent capabilities
        """
        return {
            "agent_type": "ExtractionAgent",
            "primary_function": "content_extraction",
            "supported_sources": ["web_urls", "documents"],
            "mcp_servers_required": ["primary_tooling"],
            "communication_patterns": ["A2A_with_orchestrator", "broadcast_logging"]
        }
