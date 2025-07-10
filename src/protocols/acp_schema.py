"""
Agent Communication Protocol (ACP) Schema Definitions

This module defines the Pydantic models for structured communication
between agents in the Project Synapse system.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ACPMsgType(Enum):
    """
    Enumeration of all message types supported by the Agent Communication Protocol.
    
    - TASK_ASSIGN: Assign a task to an agent
    - STATUS_UPDATE: Report progress or status changes
    - DATA_SUBMIT: Submit processed data or results
    - VALIDATION_REQUEST: Request validation of data or claims
    - VALIDATION_RESPONSE: Response to a validation request
    - LOG_BROADCAST: Broadcast log messages to all listening agents
    """
    TASK_ASSIGN = "task_assign"
    STATUS_UPDATE = "status_update"
    DATA_SUBMIT = "data_submit"
    VALIDATION_REQUEST = "validation_request"
    VALIDATION_RESPONSE = "validation_response"
    LOG_BROADCAST = "log_broadcast"


class ACPMessage(BaseModel):
    """
    Generic Agent Communication Protocol message structure.
    
    This model supports both direct agent-to-agent messages and broadcast messages.
    For direct messages, use receiver_id. For broadcasts, use topic.
    
    Attributes:
        sender_id: Unique identifier of the sending agent
        receiver_id: Unique identifier of the receiving agent (for direct messages)
        topic: Topic name for broadcast messages (alternative to receiver_id)
        msg_type: Type of message being sent
        payload: Flexible dictionary containing message-specific data
        timestamp: Optional timestamp for message tracking
    """
    sender_id: str = Field(..., description="Unique identifier of the sending agent")
    receiver_id: Optional[str] = Field(None, description="Target agent ID for direct messages")
    topic: Optional[str] = Field(None, description="Topic name for broadcast messages")
    msg_type: ACPMsgType = Field(..., description="Type of message being sent")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message-specific data")
    timestamp: Optional[str] = Field(None, description="Message timestamp")
    
    def model_post_init(self, __context: Any) -> None:
        """Validate that either receiver_id or topic is provided, but not both."""
        if not self.receiver_id and not self.topic:
            raise ValueError("Either receiver_id or topic must be provided")
        if self.receiver_id and self.topic:
            raise ValueError("Cannot specify both receiver_id and topic")


class TaskAssignPayload(BaseModel):
    """Payload structure for TASK_ASSIGN messages."""
    task_type: str = Field(..., description="Type of task to perform")
    task_data: Dict[str, Any] = Field(..., description="Task-specific parameters")
    priority: int = Field(default=1, description="Task priority (1=high, 5=low)")


class StatusUpdatePayload(BaseModel):
    """Payload structure for STATUS_UPDATE messages."""
    status: str = Field(..., description="Current status description")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    task_id: Optional[str] = Field(None, description="Associated task identifier")


class DataSubmitPayload(BaseModel):
    """Payload structure for DATA_SUBMIT messages."""
    data_type: str = Field(..., description="Type of data being submitted")
    data: Any = Field(..., description="The actual data payload")
    source: Optional[str] = Field(None, description="Source of the data")
    task_id: Optional[str] = Field(None, description="Associated task identifier")


class ValidationRequestPayload(BaseModel):
    """Payload structure for VALIDATION_REQUEST messages."""
    claim: str = Field(..., description="Claim or data to be validated")
    source_url: Optional[str] = Field(None, description="Original source URL")
    validation_type: str = Field(default="fact_check", description="Type of validation requested")


class ValidationResponsePayload(BaseModel):
    """Payload structure for VALIDATION_RESPONSE messages."""
    is_valid: bool = Field(..., description="Whether the claim is valid")
    confidence: float = Field(..., description="Confidence score (0-1)")
    evidence: Optional[str] = Field(None, description="Supporting evidence")
    source: Optional[str] = Field(None, description="Validation source")


class LogBroadcastPayload(BaseModel):
    """Payload structure for LOG_BROADCAST messages."""
    level: str = Field(..., description="Log level (INFO, DEBUG, WARNING, ERROR)")
    message: str = Field(..., description="Log message content")
    component: Optional[str] = Field(None, description="Component that generated the log")
