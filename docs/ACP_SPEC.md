# Agent Communication Protocol (ACP) Specification

## Overview

The Agent Communication Protocol (ACP) is a structured messaging system designed for Project Synapse that enables robust, type-safe communication between intelligent agents. ACP provides the foundation for both direct agent-to-agent (A2A) interactions and publish-subscribe broadcast patterns.

## Core Principles

1. **Type Safety**: All messages use Pydantic models for validation and serialization
2. **Flexibility**: Support for both direct messaging and topic-based broadcasts  
3. **Observability**: Built-in logging and status tracking capabilities
4. **Extensibility**: Pluggable payload system for different message types

## Message Structure

### Base Message Format

All ACP messages follow a standardized structure defined by the `ACPMessage` model:

```python
class ACPMessage(BaseModel):
    sender_id: str              # Unique identifier of the sending agent
    receiver_id: Optional[str]  # Target agent ID (for direct messages)
    topic: Optional[str]        # Topic name (for broadcast messages)
    msg_type: ACPMsgType        # Type of message being sent
    payload: Dict[str, Any]     # Message-specific data
    timestamp: Optional[str]    # Message timestamp
```

### Message Types

ACP defines six core message types in the `ACPMsgType` enumeration:

| Message Type | Purpose | Direction | Payload Type |
|-------------|---------|-----------|--------------|
| `TASK_ASSIGN` | Assign work to an agent | Orchestrator → Worker | `TaskAssignPayload` |
| `STATUS_UPDATE` | Report progress/status | Worker → Orchestrator | `StatusUpdatePayload` |
| `DATA_SUBMIT` | Submit processed results | Worker → Orchestrator | `DataSubmitPayload` |
| `VALIDATION_REQUEST` | Request fact checking | Agent → FactChecker | `ValidationRequestPayload` |
| `VALIDATION_RESPONSE` | Respond to validation | FactChecker → Agent | `ValidationResponsePayload` |
| `LOG_BROADCAST` | System-wide logging | Any Agent → Topic | `LogBroadcastPayload` |

## Communication Patterns

### 1. Direct Agent-to-Agent (A2A) Communication

Direct A2A communication uses the `receiver_id` field to route messages to specific agents:

```python
# Orchestrator assigning task to SearchAgent
task_message = ACPMessage(
    sender_id="orchestrator",
    receiver_id="search_agent",
    msg_type=ACPMsgType.TASK_ASSIGN,
    payload=TaskAssignPayload(
        task_type="web_search",
        task_data={"query": "quantum computing cryptography"},
        priority=1
    ).model_dump()
)
```

### 2. Publish-Subscribe Broadcasting

Broadcast communication uses the `topic` field to send messages to all subscribed agents:

```python
# Logger broadcasting system event
log_message = ACPMessage(
    sender_id="extraction_agent",
    topic="logs",
    msg_type=ACPMsgType.LOG_BROADCAST,
    payload=LogBroadcastPayload(
        level="INFO",
        message="Content extraction completed successfully",
        component="extraction_agent"
    ).model_dump()
)
```

### 3. Request-Response Patterns

Some interactions follow request-response patterns, such as fact-checking:

```python
# Request validation
validation_request = ACPMessage(
    sender_id="synthesis_agent",
    receiver_id="fact_checker_agent", 
    msg_type=ACPMsgType.VALIDATION_REQUEST,
    payload=ValidationRequestPayload(
        claim="Quantum computers can break RSA encryption",
        source_url="https://example.com/quantum-crypto",
        validation_type="fact_check"
    ).model_dump()
)

# Response with validation result
validation_response = ACPMessage(
    sender_id="fact_checker_agent",
    receiver_id="synthesis_agent",
    msg_type=ACPMsgType.VALIDATION_RESPONSE, 
    payload=ValidationResponsePayload(
        is_valid=True,
        confidence=0.85,
        evidence="Cross-referenced with multiple academic sources",
        source="fact_checker_agent"
    ).model_dump()
)
```

## Payload Specifications

### TaskAssignPayload

Used for `TASK_ASSIGN` messages to delegate work to agents:

```python
class TaskAssignPayload(BaseModel):
    task_type: str                    # Type of task ("web_search", "extract_content", etc.)
    task_data: Dict[str, Any]         # Task-specific parameters
    priority: int = 1                 # Task priority (1=high, 5=low)
```

### StatusUpdatePayload

Used for `STATUS_UPDATE` messages to report progress:

```python
class StatusUpdatePayload(BaseModel):
    status: str                       # Current status description
    progress: Optional[float] = None  # Progress percentage (0-100)
    task_id: Optional[str] = None     # Associated task identifier
```

### DataSubmitPayload

Used for `DATA_SUBMIT` messages to return processed results:

```python
class DataSubmitPayload(BaseModel):
    data_type: str                    # Type of data ("search_results", "extracted_content", etc.)
    data: Any                         # The actual data payload
    source: Optional[str] = None      # Source of the data
    task_id: Optional[str] = None     # Associated task identifier
```

### LogBroadcastPayload

Used for `LOG_BROADCAST` messages for system-wide logging:

```python
class LogBroadcastPayload(BaseModel):
    level: str                        # Log level ("INFO", "DEBUG", "WARNING", "ERROR")
    message: str                      # Log message content
    component: Optional[str] = None   # Component that generated the log
```

## Message Routing and Delivery

### Message Bus Architecture

Project Synapse uses a centralized message bus for routing ACP messages:

```python
class MessageBus:
    def __init__(self):
        self.agents = {}  # agent_id -> agent_instance mapping
    
    def route_message(self, message: ACPMessage):
        if message.receiver_id:
            # Direct message routing
            if message.receiver_id in self.agents:
                target_agent = self.agents[message.receiver_id]
                target_agent.receive_message(message)
        elif message.topic:
            # Broadcast message routing
            for agent in self.agents.values():
                if hasattr(agent, 'subscribed_topics'):
                    if message.topic in agent.subscribed_topics:
                        agent.receive_message(message)
```

### Agent Message Handling

Agents implement the `handle_message` method to process incoming ACP messages:

```python
class ExampleAgent(BaseAgent):
    def handle_message(self, message: ACPMessage):
        if message.msg_type == ACPMsgType.TASK_ASSIGN:
            self._handle_task_assignment(message)
        elif message.msg_type == ACPMsgType.STATUS_UPDATE:
            self._handle_status_update(message)
        # ... handle other message types
```

## Error Handling and Validation

### Message Validation

All ACP messages are validated using Pydantic models:

```python
try:
    message = ACPMessage(**raw_message_data)
    payload = TaskAssignPayload(**message.payload)
except ValidationError as e:
    print(f"Invalid ACP message: {e}")
    # Handle validation error
```

### Error Reporting

Agents can report errors through status updates:

```python
error_status = ACPMessage(
    sender_id=self.agent_id,
    receiver_id="orchestrator",
    msg_type=ACPMsgType.STATUS_UPDATE,
    payload=StatusUpdatePayload(
        status=f"task_failed: {error_message}",
        progress=0.0,
        task_id=task_id
    ).model_dump()
)
```

## Security Considerations

### Message Authenticity

- All messages include a `sender_id` for traceability
- Message bus validates sender identity before routing
- Agents should validate expected sender for sensitive operations

### Access Control

- Topic subscriptions control which agents receive broadcast messages
- Direct messaging requires knowledge of target agent ID
- Payload validation prevents malformed data injection

### Audit Trail

- All messages can include timestamps for audit logging
- LoggerAgent maintains comprehensive message history
- Message routing through central bus enables monitoring

## Best Practices

### Message Design

1. **Use Specific Payload Types**: Define custom payload models for different message types
2. **Include Task IDs**: Use task identifiers to correlate related messages
3. **Provide Progress Updates**: Send regular status updates for long-running tasks
4. **Handle Failures Gracefully**: Always send error status updates when tasks fail

### Agent Implementation

1. **Validate Message Types**: Check `msg_type` before processing messages
2. **Implement Timeouts**: Don't wait indefinitely for responses
3. **Use Appropriate Communication Patterns**: Choose direct vs. broadcast appropriately
4. **Log Important Events**: Use `LOG_BROADCAST` for system observability

### Performance Optimization

1. **Batch Related Messages**: Combine multiple updates into single messages when appropriate
2. **Use Async Processing**: Handle messages asynchronously to prevent blocking
3. **Implement Backpressure**: Monitor queue sizes and implement flow control
4. **Cache Frequently Used Data**: Avoid repeated data submissions

## Example Workflows

### Research Workflow

```
1. System → Orchestrator: TASK_ASSIGN(research_query)
2. Orchestrator → SearchAgent: TASK_ASSIGN(web_search)
3. SearchAgent → Orchestrator: STATUS_UPDATE(searching)
4. SearchAgent → Orchestrator: DATA_SUBMIT(search_results)
5. Orchestrator → ExtractionAgent: TASK_ASSIGN(extract_content)
6. ExtractionAgent → Topic("logs"): LOG_BROADCAST(extraction_started)
7. ExtractionAgent → Orchestrator: DATA_SUBMIT(extracted_content)
8. Orchestrator → SynthesisAgent: TASK_ASSIGN(synthesize_report)
9. SynthesisAgent → Orchestrator: DATA_SUBMIT(final_report)
```

### Fact-Checking Workflow

```
1. SynthesisAgent → FactCheckerAgent: VALIDATION_REQUEST(claim)
2. FactCheckerAgent → SynthesisAgent: VALIDATION_RESPONSE(result)
3. SynthesisAgent → Topic("logs"): LOG_BROADCAST(fact_check_complete)
```

## Conclusion

The Agent Communication Protocol provides a robust foundation for building complex multi-agent systems like Project Synapse. Its combination of type safety, flexible routing, and comprehensive error handling enables agents to collaborate effectively while maintaining system observability and reliability.
