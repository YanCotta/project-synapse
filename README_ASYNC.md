# Project Synapse - Async Implementation

This is the production-ready, fully functional asynchronous version of Project Synapse. It transforms the educational simulation into a real distributed system using modern async patterns and infrastructure.

## 🏗️ Architecture

### Core Components

1. **FastAPI MCP Servers** - HTTP-based Model Context Protocol servers
2. **RabbitMQ Message Bus** - Async message routing and pub/sub patterns
3. **Async Agents** - Concurrent agent execution with asyncio
4. **Docker Containers** - Containerized deployment with health checks

### Async Agent Ecosystem

| Agent | Purpose | Key Features |
|-------|---------|--------------|
| **AsyncOrchestratorAgent** | Workflow coordination | A2A command patterns, concurrent task assignment |
| **AsyncSearchAgent** | Web search operations | MCP Primary Tooling integration, search result processing |
| **AsyncExtractionAgent** | Content extraction | Streaming progress callbacks, async HTTP processing |
| **AsyncFactCheckerAgent** | Claim validation | Peer review patterns, evidence correlation |
| **AsyncSynthesisAgent** | Report generation | MCP Sampling simulation, structured content synthesis |
| **AsyncFileSaveAgent** | File operations | MCP Roots security, path validation |
| **AsyncLoggerAgent** | System monitoring | Pub/sub pattern, log aggregation, health monitoring |

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Git

### Installation

1. **Clone and setup:**
   ```bash
   git clone <repository>
   cd project-synapse
   git checkout working-app  # Async implementation branch
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start infrastructure:**
   ```bash
   docker-compose up -d
   ```

4. **Run the application:**
   ```bash
   python async_main.py
   ```

### Environment Configuration

Create a `.env` file:

```env
# Message Bus
RABBITMQ_URL=amqp://synapse:synapse123@localhost:5672/

# MCP Servers
PRIMARY_TOOLING_URL=http://localhost:8001
FILESYSTEM_URL=http://localhost:8002

# Research Configuration
RESEARCH_QUERY=quantum computing impact on cryptography
WORKFLOW_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
```

## 🔧 Development

### Project Structure

```
project-synapse/
├── async_main.py                    # Main async application
├── docker-compose.yml               # Multi-service deployment
├── requirements.txt                 # Async dependencies
├── test_async_implementation.py     # Comprehensive test suite
│
├── src/
│   ├── agents/                      # Async agent implementations
│   │   ├── async_base_agent.py     # Foundation class with MCP client
│   │   ├── async_orchestrator.py   # Workflow coordinator
│   │   ├── async_search_agent.py   # Web search via MCP
│   │   ├── async_extraction_agent.py # Content extraction with streaming
│   │   ├── async_fact_checker_agent.py # Claim validation
│   │   ├── async_synthesis_agent.py # Report generation
│   │   ├── async_file_save_agent.py # Secure file operations
│   │   └── async_logger_agent.py   # System monitoring
│   │
│   ├── mcp_servers/                 # FastAPI MCP implementations
│   │   ├── fastapi_primary_server.py # Web search and extraction
│   │   └── fastapi_filesystem_server.py # Secure file operations
│   │
│   ├── message_bus/                 # Async message infrastructure
│   │   └── rabbitmq_bus.py         # RabbitMQ integration
│   │
│   └── protocols/                   # Message schemas
│       ├── acp_schema.py           # Agent Communication Protocol
│       └── mcp_schemas.py          # Model Context Protocol
```

### Testing

Run the comprehensive test suite:

```bash
python test_async_implementation.py
```

Test coverage includes:
- Agent creation and initialization
- Message bus communication
- MCP client functionality
- Async operations and concurrency
- Workflow simulation
- Error handling and recovery

### Branch Strategy

- `main` - Original educational simulation
- `educational-simulation` - Preserved educational version
- `working-app` - Production async implementation (current)

## 🔄 Workflow Process

1. **Orchestrator** receives research query
2. **Search Agent** performs web search via MCP Primary Tooling
3. **Extraction Agent** processes content with streaming progress
4. **Fact Checker** validates claims with peer review patterns
5. **Synthesis Agent** generates comprehensive report
6. **File Save Agent** securely saves results with MCP Roots
7. **Logger Agent** monitors all activities via pub/sub

## 🛡️ Security Features

### MCP Roots Security
- Path validation for filesystem operations
- Security boundary enforcement
- Directory traversal prevention

### Message Validation
- Pydantic schema enforcement
- Type-safe message handling
- Input sanitization

### Container Security
- Multi-stage Docker builds
- Health check monitoring
- Resource limitations

## 📊 Monitoring and Logging

### Logger Agent Features
- **Log Aggregation** - Centralized system logging
- **Error Pattern Detection** - Automatic alert generation
- **Agent Health Monitoring** - Activity tracking and silence detection
- **Pub/Sub Pattern** - Topic-based message subscription

### Health Checks
- MCP server availability monitoring
- RabbitMQ connection health
- Agent lifecycle management
- Workflow progress tracking

## 🔌 Integration Patterns

### A2A (Agent-to-Agent) Communication
- **Command Pattern** - Structured task assignment
- **Event Pattern** - Status updates and notifications
- **Pub/Sub Pattern** - Topic-based broadcasting

### MCP (Model Context Protocol) Integration
- **HTTP Tooling** - RESTful tool invocation
- **Streaming Progress** - Real-time progress callbacks
- **Sampling Simulation** - Advanced content processing

## 🐳 Docker Deployment

### Services

| Service | Port | Purpose |
|---------|------|---------|
| rabbitmq | 5672, 15672 | Message broker and management UI |
| primary-tooling | 8001 | Web search and content extraction |
| filesystem-server | 8002 | Secure file operations |
| synapse-app | - | Main application container |

### Health Monitoring

All services include health checks:
- RabbitMQ management API
- FastAPI health endpoints
- Application process monitoring

## 📈 Performance Features

### Async Concurrency
- Non-blocking I/O operations
- Concurrent agent execution
- Streaming data processing
- Connection pooling

### Scalability
- Horizontal scaling with Docker Compose
- Message queue load distribution
- Stateless agent design
- Resource-efficient containers

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RABBITMQ_URL` | `amqp://synapse:synapse123@localhost:5672/` | Message bus connection |
| `PRIMARY_TOOLING_URL` | `http://localhost:8001` | Web search MCP server |
| `FILESYSTEM_URL` | `http://localhost:8002` | File operations MCP server |
| `RESEARCH_QUERY` | `quantum computing impact on cryptography` | Default research topic |
| `WORKFLOW_TIMEOUT` | `300` | Maximum workflow duration (seconds) |
| `LOG_LEVEL` | `INFO` | Application logging level |

### MCP Server Configuration

Both MCP servers support:
- CORS for cross-origin requests
- Health check endpoints
- Streaming response support
- Error handling and validation

## 🚨 Troubleshooting

### Common Issues

1. **RabbitMQ Connection Failed**
   ```bash
   docker-compose up rabbitmq
   # Wait for service to be ready
   docker-compose logs rabbitmq
   ```

2. **MCP Server Not Responding**
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8002/health
   ```

3. **Agent Startup Errors**
   ```bash
   python test_async_implementation.py
   # Check test results for specific failures
   ```

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

View detailed container logs:
```bash
docker-compose logs -f synapse-app
```

## 🤝 Contributing

1. **Development Setup**
   ```bash
   git checkout working-app
   pip install -r requirements.txt
   docker-compose up -d rabbitmq
   ```

2. **Testing**
   ```bash
   python test_async_implementation.py
   ```

3. **Code Style**
   - Follow asyncio patterns
   - Use type hints
   - Include comprehensive error handling
   - Add logging for debugging

4. **Commit Strategy**
   - Individual file commits for granular history
   - Descriptive commit messages
   - Feature branch workflow

## 📚 Technical Documentation

- [Architecture Documentation](docs/ARCHITECTURE.md)
- [ACP Protocol Specification](docs/ACP_SPEC.md)
- [MCP Integration Guide](docs/MCP_IN_DEPTH.md)
- [Implementation Status](docs/IMPLEMENTATION_COMPLETE.md)

## 🎯 Future Enhancements

- **Kubernetes Deployment** - Cloud-native orchestration
- **Distributed Tracing** - Request flow monitoring
- **Metrics Collection** - Prometheus integration
- **Auto-scaling** - Dynamic resource allocation
- **Circuit Breakers** - Resilience patterns
- **Rate Limiting** - API protection

---

**Project Synapse** - Transforming AI agent simulation into production-ready distributed systems.
