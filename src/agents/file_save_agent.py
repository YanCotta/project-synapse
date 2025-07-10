"""
File Save Agent

Agent responsible for all filesystem operations with security controls.
Demonstrates MCP Roots security model for secure file operations.
"""

from typing import Dict
from .base_agent import BaseAgent, MCPClientMixin
from ..protocols.acp_schema import ACPMessage, ACPMsgType, TaskAssignPayload, StatusUpdatePayload, DataSubmitPayload, LogBroadcastPayload


class FileSaveAgent(BaseAgent, MCPClientMixin):
    """
    Agent that handles secure file operations.
    
    Demonstrates MCP Roots security model by restricting file operations
    to approved directories.
    """
    
    def __init__(self, agent_id: str = "file_save_agent", orchestrator_id: str = "orchestrator", 
                 message_bus: Dict = None):
        """Initialize the File Save Agent."""
        BaseAgent.__init__(self, agent_id, message_bus)
        MCPClientMixin.__init__(self)
        
        self.orchestrator_id = orchestrator_id
        
        print(f"[{self.agent_id}] File Save Agent initialized")
    
    def handle_message(self, message: ACPMessage):
        """Handle incoming messages."""
        if message.msg_type == ACPMsgType.TASK_ASSIGN:
            self._handle_task_assignment(message)
        else:
            print(f"[{self.agent_id}] Unhandled message type: {message.msg_type.value}")
    
    def _handle_task_assignment(self, message: ACPMessage):
        """Handle file save task assignments."""
        payload = TaskAssignPayload(**message.payload)
        
        if payload.task_type == "save_report":
            self._save_research_report(payload.task_data)
        else:
            print(f"[{self.agent_id}] Unknown task type: {payload.task_type}")
    
    def _save_research_report(self, task_data: Dict):
        """Save research report using secure MCP file operations."""
        filename = task_data.get("filename")
        content = task_data.get("content")
        task_id = task_data.get("task_id", "unknown")
        
        print(f"[{self.agent_id}] Saving research report: {filename}")
        
        # Send status update
        status_message = self.create_message(
            receiver_id=self.orchestrator_id,
            msg_type=ACPMsgType.STATUS_UPDATE,
            payload=StatusUpdatePayload(
                status="saving_file",
                progress=50.0,
                task_id=task_id
            ).model_dump()
        )
        self.send_message(status_message)
        
        try:
            # Construct secure file path (within allowed roots)
            safe_path = f"output/reports/{filename}"
            
            # Call MCP file save tool with security restrictions
            save_params = {
                "file_path": safe_path,
                "content": content
            }
            
            result = self.call_mcp_tool(
                server_name="filesystem",
                tool_name="save_file",
                params=save_params
            )
            
            # Send completion status
            data_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.DATA_SUBMIT,
                payload=DataSubmitPayload(
                    data_type="file_save_result",
                    data=result,
                    source=safe_path,
                    task_id=task_id
                ).model_dump()
            )
            self.send_message(data_message)
            
            # Broadcast completion log
            bytes_written = result.get("bytes_written", 0)
            log_message = self.create_message(
                topic="logs",
                msg_type=ACPMsgType.LOG_BROADCAST,
                payload=LogBroadcastPayload(
                    level="INFO",
                    message=f"Report saved successfully: {filename} ({bytes_written} bytes)",
                    component=self.agent_id
                ).model_dump()
            )
            self.send_message(log_message)
            
        except Exception as e:
            print(f"[{self.agent_id}] File save failed: {e}")
            
            # Send error status
            error_status = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.STATUS_UPDATE,
                payload=StatusUpdatePayload(
                    status=f"save_failed: {e}",
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
                    message=f"File save failed: {filename} - {e}",
                    component=self.agent_id
                ).model_dump()
            )
            self.send_message(error_log)
