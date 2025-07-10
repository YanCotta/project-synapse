# Project Synapse Architecture

## System Overview

Project Synapse is a comprehensive demonstration of advanced multi-agent system patterns, showcasing three critical protocols for modern AI systems:

- **ACP (Agent Communication Protocol)**: Structured, type-safe messaging between agents
- **A2A (Agent-to-Agent)**: Direct collaboration and peer review patterns  
- **MCP (Model Context Protocol)**: Secure tool integration with progress monitoring

The system implements a collaborative research workflow where specialized agents work together to investigate complex questions, extract information from multiple sources, and synthesize comprehensive reports.

## Architecture Components

### Core Agent Types

#### 1. OrchestratorAgent (Central Coordinator)
- **Role**: Project manager and workflow coordinator
- **Communication Pattern**: A2A command and control
- **Key Responsibilities**:
  - Task decomposition and assignment
  - Progress tracking across multiple agents
  - Result aggregation and workflow coordination
  - Error handling and recovery

#### 2. SearchAgent (Information Discovery)
- **Role**: Web search and source identification
- **Communication Pattern**: MCP client for web tools
- **Key Responsibilities**:
  - Execute web searches via MCP tools
  - Return ranked search results
  - Handle search failures gracefully

#### 3. ExtractionAgent (Content Processing)
- **Role**: Extract content from web sources
- **Communication Pattern**: MCP client with progress notifications
- **Key Responsibilities**:
  - Process URLs and extract text content
  - Report progress during long operations
  - Handle various content types and formats

#### 4. FactCheckerAgent (Validation Service)
- **Role**: Validate claims and verify information
- **Communication Pattern**: A2A peer review and negotiation
- **Key Responsibilities**:
  - Cross-reference claims against sources
  - Provide confidence scores for validation
  - Support both direct validation requests and batch processing

#### 5. SynthesisAgent (Report Generation)
- **Role**: Synthesize findings into coherent reports
- **Communication Pattern**: MCP client for AI-assisted writing
- **Key Responsibilities**:
  - Combine multiple sources into unified reports
  - Use MCP Sampling for text improvement
  - Structure findings logically

#### 6. FileSaveAgent (Secure I/O)
- **Role**: Handle all filesystem operations
- **Communication Pattern**: MCP client with security restrictions
- **Key Responsibilities**:
  - Save reports and data files securely
  - Enforce MCP Roots security boundaries
  - Manage file organization and naming

#### 7. LoggerAgent (System Monitor)
- **Role**: System-wide logging and observability
- **Communication Pattern**: A2A pub/sub subscriber
- **Key Responsibilities**:
  - Aggregate logs from all system components
  - Provide system health monitoring
  - Enable debugging and audit trails

### MCP Server Infrastructure

#### 1. PrimaryToolingServer
- **Purpose**: Web search and content extraction tools
- **Tools Provided**:
  - `search_web`: Web search with mock results
  - `browse_and_extract`: Content extraction with progress notifications
- **Demonstrates**: MCP Progress Notifications

#### 2. FileSystemServer  
- **Purpose**: Secure file operations with path restrictions
- **Tools Provided**:
  - `save_file`: Write files within allowed directories only
- **Demonstrates**: MCP Roots security model

#### 3. UserInteractionServer
- **Purpose**: AI-assisted text generation and improvement
- **Tools Provided**:
  - `rephrase_sentence`: Improve sentence clarity and style
- **Demonstrates**: MCP Sampling pattern

## Communication Flow Architecture

### Message Bus System

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Agent A       │    │   Message Bus    │    │   Agent B       │
│                 │    │                  │    │                 │
│  send_message() │───▶│  route_message() │───▶│ receive_message │
│                 │    │                  │    │                 │
│  Outbox Queue   │    │  Agent Registry  │    │  Inbox Queue    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Routing Mechanisms

1. **Direct Routing**: Messages with `receiver_id` are delivered to specific agents
2. **Topic Broadcasting**: Messages with `topic` are delivered to all subscribers
3. **Error Handling**: Unroutable messages are logged and handled gracefully

## Security Architecture

### MCP Roots Implementation

```
Filesystem Security Boundary:
┌─────────────────────────────────────────┐
│            System Root (/)              │
│  ┌─────────────────────────────────────┐│
│  │       Project Root                  ││
│  │  ┌─────────────┐  ┌─────────────┐  ││
│  │  │ /output/    │  │ /temp/      │  ││  ← Allowed Roots
│  │  │  reports/   │  │             │  ││
│  │  │  data/      │  │             │  ││
│  │  └─────────────┘  └─────────────┘  ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
          ↑                    ↑
      Allowed            Access Denied
```

### Security Boundaries

1. **Agent Isolation**: Agents cannot directly access filesystem or network
2. **Tool Mediation**: All external access goes through MCP servers
3. **Path Validation**: Filesystem operations restricted to approved directories
4. **Input Validation**: All messages validated with Pydantic schemas

## Data Flow Architecture

### Research Workflow Data Flow

```
Query Input
    ↓
┌─────────────────┐
│ Orchestrator    │
│ Agent           │
└─────────────────┘
    ↓ (task assignment)
┌─────────────────┐      ┌─────────────────┐
│ Search Agent    │────▶ │ MCP Primary     │
│                 │      │ Tooling Server  │
└─────────────────┘      └─────────────────┘
    ↓ (search results)
┌─────────────────┐
│ Orchestrator    │
│ Agent           │
└─────────────────┘
    ↓ (extraction tasks)
┌─────────────────┐      ┌─────────────────┐
│ Extraction      │────▶ │ MCP Primary     │
│ Agent           │      │ Tooling Server  │
└─────────────────┘      └─────────────────┘
    ↓ (extracted content)
┌─────────────────┐      ┌─────────────────┐
│ Synthesis       │────▶ │ MCP User        │
│ Agent           │      │ Interaction     │
└─────────────────┘      └─────────────────┘
    ↓ (final report)
┌─────────────────┐      ┌─────────────────┐
│ File Save       │────▶ │ MCP Filesystem  │
│ Agent           │      │ Server          │
└─────────────────┘      └─────────────────┘
```

## Concurrency and Threading Model

### Agent Threading Architecture

Each agent runs in its own thread with:

1. **Message Processing Loop**: Continuously processes incoming messages
2. **Inbox Queue**: Thread-safe queue for incoming messages
3. **Outbox Queue**: Thread-safe queue for outgoing messages
4. **Periodic Tasks**: Optional background maintenance tasks

### Thread Safety Measures

- **Queue-Based Communication**: All inter-agent communication uses thread-safe queues
- **Message Immutability**: ACP messages are immutable after creation
- **Atomic Operations**: Critical operations are atomic to prevent race conditions
- **Graceful Shutdown**: All threads support clean shutdown procedures

## Scalability Considerations

### Current Architecture Limitations

1. **Single Process**: All agents run in one Python process
2. **Shared Memory**: Limited by single-machine memory constraints
3. **Synchronous Processing**: Some operations block agent threads

### Potential Scaling Improvements

1. **Distributed Deployment**: Move to distributed agent deployment
2. **Asynchronous Processing**: Implement async/await patterns
3. **Load Balancing**: Distribute work across multiple agent instances
4. **Persistent Queues**: Use Redis or similar for message persistence

## Monitoring and Observability

### Logging Architecture

```
All Agents ──┐
             │ LOG_BROADCAST
             ▼
    ┌─────────────────┐
    │ Logger Agent    │
    │                 │
    │ • Real-time     │
    │   display       │
    │ • Log history   │
    │ • Health        │
    │   monitoring    │
    │ • Export        │
    │   capabilities  │
    └─────────────────┘
```

### Health Monitoring

- **Agent Status Tracking**: Monitor running state of all agents
- **Message Flow Analysis**: Track message patterns and bottlenecks
- **Error Rate Monitoring**: Aggregate and analyze system errors
- **Performance Metrics**: Track processing times and throughput

## Extension Points

### Adding New Agents

1. Inherit from `BaseAgent` base class
2. Implement `handle_message()` method for ACP processing
3. Optionally use `MCPClientMixin` for tool access
4. Register with message bus for communication

### Adding New MCP Tools

1. Create tool method on appropriate MCP server
2. Define Pydantic models for parameters and responses
3. Implement security validation if needed
4. Register tool with agents that need access

### Custom Communication Patterns

1. Define new `ACPMsgType` values
2. Create corresponding payload models
3. Implement handling logic in relevant agents
4. Update documentation and examples

## Performance Characteristics

### Message Processing

- **Latency**: ~1-10ms for direct messages in current implementation
- **Throughput**: ~1000 messages/second per agent thread
- **Memory Usage**: ~10-50MB per agent depending on data processed

### MCP Tool Execution

- **Search Operations**: ~500ms simulated web search
- **Content Extraction**: ~3-5 seconds with progress notifications
- **File Operations**: ~10-100ms depending on file size

## Deployment Architecture

### Development Setup

```yaml
project-synapse/
├── src/
│   ├── agents/          # Agent implementations
│   ├── mcp_servers/     # MCP server implementations  
│   └── protocols/       # ACP and MCP schemas
├── docs/               # Architecture documentation
├── output/             # Generated reports and data
└── main.py            # System entry point
```

### Production Considerations

For production deployment, consider:

1. **Containerization**: Docker containers for each component
2. **Service Discovery**: Registry for locating MCP servers
3. **Configuration Management**: Environment-based configuration
4. **Monitoring Integration**: Prometheus/Grafana for metrics
5. **Log Aggregation**: ELK stack for centralized logging

## Conclusion

Project Synapse's architecture demonstrates how modern multi-agent systems can be built with clear separation of concerns, robust communication protocols, and comprehensive security models. The combination of ACP for agent coordination, A2A for peer collaboration, and MCP for tool integration provides a solid foundation for building sophisticated AI systems that are both powerful and maintainable.
