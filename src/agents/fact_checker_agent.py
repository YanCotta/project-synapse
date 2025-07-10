"""
Fact Checker Agent

Agent responsible for validating claims and data against multiple sources.
Demonstrates A2A peer review and negotiation patterns.
"""

from typing import Dict
from .base_agent import BaseAgent, MCPClientMixin
from ..protocols.acp_schema import (
    ACPMessage, ACPMsgType, TaskAssignPayload, StatusUpdatePayload, 
    DataSubmitPayload, LogBroadcastPayload, ValidationRequestPayload, ValidationResponsePayload
)


class FactCheckerAgent(BaseAgent, MCPClientMixin):
    """
    Agent that validates claims and facts against multiple sources.
    
    Demonstrates A2A peer review and negotiation patterns between agents.
    """
    
    def __init__(self, agent_id: str = "fact_checker_agent", orchestrator_id: str = "orchestrator", 
                 message_bus: Dict = None):
        """Initialize the Fact Checker Agent."""
        BaseAgent.__init__(self, agent_id, message_bus)
        MCPClientMixin.__init__(self)
        
        self.orchestrator_id = orchestrator_id
        
        print(f"[{self.agent_id}] Fact Checker Agent initialized")
    
    def handle_message(self, message: ACPMessage):
        """Handle incoming messages."""
        if message.msg_type == ACPMsgType.TASK_ASSIGN:
            self._handle_task_assignment(message)
        elif message.msg_type == ACPMsgType.VALIDATION_REQUEST:
            self._handle_validation_request(message)
        else:
            print(f"[{self.agent_id}] Unhandled message type: {message.msg_type.value}")
    
    def _handle_task_assignment(self, message: ACPMessage):
        """Handle fact-checking task assignments."""
        payload = TaskAssignPayload(**message.payload)
        
        if payload.task_type == "fact_check":
            self._perform_fact_check(payload.task_data)
        else:
            print(f"[{self.agent_id}] Unknown task type: {payload.task_type}")
    
    def _handle_validation_request(self, message: ACPMessage):
        """Handle direct validation requests from other agents."""
        payload = ValidationRequestPayload(**message.payload)
        
        print(f"[{self.agent_id}] Received validation request from {message.sender_id}")
        
        # Perform validation
        is_valid, confidence, evidence = self._validate_claim(payload.claim, payload.source_url)
        
        # Send validation response
        response = self.create_message(
            receiver_id=message.sender_id,
            msg_type=ACPMsgType.VALIDATION_RESPONSE,
            payload=ValidationResponsePayload(
                is_valid=is_valid,
                confidence=confidence,
                evidence=evidence,
                source=self.agent_id
            ).model_dump()
        )
        self.send_message(response)
    
    def _perform_fact_check(self, task_data: Dict):
        """Perform comprehensive fact-checking of provided content."""
        claims = task_data.get("claims", [])
        source_content = task_data.get("source_content", "")
        task_id = task_data.get("task_id", "unknown")
        
        print(f"[{self.agent_id}] Fact-checking {len(claims)} claims")
        
        # Send status update
        status_message = self.create_message(
            receiver_id=self.orchestrator_id,
            msg_type=ACPMsgType.STATUS_UPDATE,
            payload=StatusUpdatePayload(
                status="fact_checking",
                progress=10.0,
                task_id=task_id
            ).model_dump()
        )
        self.send_message(status_message)
        
        # Process each claim
        validation_results = []
        for i, claim in enumerate(claims):
            is_valid, confidence, evidence = self._validate_claim(claim)
            
            validation_results.append({
                "claim": claim,
                "is_valid": is_valid,
                "confidence": confidence,
                "evidence": evidence
            })
            
            # Update progress
            progress = 10 + (80 * (i + 1) / len(claims))
            status_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.STATUS_UPDATE,
                payload=StatusUpdatePayload(
                    status=f"validated_claim_{i+1}",
                    progress=progress,
                    task_id=task_id
                ).model_dump()
            )
            self.send_message(status_message)
        
        # Send results
        data_message = self.create_message(
            receiver_id=self.orchestrator_id,
            msg_type=ACPMsgType.DATA_SUBMIT,
            payload=DataSubmitPayload(
                data_type="fact_check_result",
                data={
                    "validations": validation_results,
                    "overall_confidence": sum(r["confidence"] for r in validation_results) / len(validation_results),
                    "claims_validated": len(validation_results)
                },
                source="fact_checker",
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
                message=f"Fact-checking completed: {len(validation_results)} claims validated",
                component=self.agent_id
            ).model_dump()
        )
        self.send_message(log_message)
    
    def _validate_claim(self, claim: str, source_url: str = None) -> tuple:
        """
        Validate a single claim (simplified implementation for demo).
        
        Args:
            claim: The claim to validate
            source_url: Optional source URL for context
            
        Returns:
            Tuple of (is_valid, confidence, evidence)
        """
        # Simplified validation logic for demonstration
        # In a real implementation, this would cross-reference multiple sources
        
        # Basic validation heuristics
        if "quantum" in claim.lower() and "cryptography" in claim.lower():
            # High confidence for quantum crypto claims (our demo topic)
            return True, 0.85, "Cross-referenced with multiple quantum computing sources"
        elif "NIST" in claim or "standard" in claim.lower():
            # High confidence for standards-related claims
            return True, 0.90, "Verified against official standards documentation"
        elif len(claim.split()) < 5:
            # Low confidence for very short claims
            return False, 0.30, "Insufficient detail for validation"
        else:
            # Moderate confidence for general claims
            return True, 0.65, "Consistent with general knowledge base"
