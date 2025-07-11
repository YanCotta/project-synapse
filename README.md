# Project Synapse 🧠

> **Note:** This repository contains two primary branches:
> - 🌳 **[`educational-simulation`](https://github.com/YanCotta/project-synapse/tree/educational-simulation):** A "pseudo-code" simulation with detailed documentation, perfect for understanding the architectural concepts of ACP, A2A, and MCP without needing to run a live application.
> - 🚀 **[`working-app`](https://github.com/YanCotta/project-synapse/tree/working-app):** A fully functional, asynchronous version of the system using FastAPI, RabbitMQ, and asyncio. Explore this branch for a real-world implementation.

**A comprehensive engineering blueprint showcasing Agent Communication Protocol (ACP), Agent-to-Agent (A2A), and Model Context Protocol (MCP) capabilities through a collaborative research swarm.**

> *"Where artificial intelligence meets elegant architecture"*

## 🎯 Project Status

**✅ COMPLETE** - All implementation phases finished with comprehensive documentation

### Current Implementation Status

| Component | Status | Description |
|-----------|--------|-------------|
| 🏗️ **Project Structure** | ✅ Complete | Full directory structure with organized modules |
| 📋 **Protocol Definitions** | ✅ Complete | ACP & MCP schemas with Pydantic validation |
| 🔧 **MCP Servers** | ✅ Complete | 3 servers demonstrating all MCP capabilities |
| 🤖 **Agent Swarm** | ✅ Complete | 7 specialized agents with unique communication patterns |
| 🚀 **Main Orchestration** | ✅ Complete | Full workflow automation and monitoring |
| 📚 **Documentation** | ✅ Complete | In-depth technical documentation and guides |

## 🌟 Key Features & Demonstrations

### Agent Communication Protocol (ACP)
- **✅ Structured Messaging**: Type-safe communication with Pydantic validation
- **✅ Direct & Broadcast**: Both A2A direct messages and pub/sub topic broadcasts  
- **✅ Workflow Coordination**: Complex multi-agent research workflows
- **✅ Error Handling**: Comprehensive error reporting and recovery mechanisms

### Agent-to-Agent (A2A) Patterns  
- **✅ Command & Control**: Orchestrator coordinating specialized worker agents
- **✅ Peer Review**: FactChecker agent providing validation services to peers
- **✅ Pub/Sub Broadcasting**: Logger agent monitoring system-wide activity
- **✅ Request-Response**: Sophisticated interaction patterns between agents

### Model Context Protocol (MCP)
- **✅ Progress Notifications**: Real-time progress reporting during long operations
- **✅ MCP Roots Security**: Filesystem access restricted to approved directories
- **✅ MCP Sampling**: AI-assisted text generation with role reversal patterns
- **✅ Tool Integration**: Secure, observable tool access for agents

## 🏛️ System Architecture

### 🤖 Agent Ecosystem

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Orchestrator   │◄──►│  Search Agent   │◄──►│ Extraction Agent│
│  (Coordinator)  │    │  (Discovery)    │    │  (Processing)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Fact Checker    │    │  Synthesis      │    │  File Save      │
│ (Validation)    │    │  (Generation)   │    │  (Secure I/O)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Logger Agent   │
                       │  (Monitoring)   │
                       └─────────────────┘
```

### 🔧 MCP Server Infrastructure

| Server | Purpose | Tools | Demonstrates |
|--------|---------|-------|--------------|
| **Primary Tooling** | Web operations | `search_web`, `browse_and_extract` | Progress Notifications |
| **Filesystem** | Secure file I/O | `save_file` | MCP Roots Security |
| **User Interaction** | AI assistance | `rephrase_sentence` | MCP Sampling |

## 🚀 Getting Started

### Prerequisites
- Python 3.8+ 
- Required dependencies in `requirements.txt`

### Quick Start

```bash
# Clone and setup
git clone https://github.com/YanCotta/project-synapse.git
cd project-synapse
pip install -r requirements.txt

# Run the demonstration
python main.py
```

### What You'll See

The system will automatically:

1. **🔧 Initialize Infrastructure**: Start all MCP servers with security boundaries
2. **🤖 Launch Agent Swarm**: Boot 7 specialized agents with distinct roles
3. **🔬 Execute Research Workflow**: Investigate "What is the impact of quantum computing on cryptography?"
4. **📊 Monitor Progress**: Real-time logging and progress tracking
5. **📝 Generate Report**: Synthesized research report saved securely to `output/reports/`

## 🏗️ Project Structure

```
project-synapse/
├── 📁 src/
│   ├── 📁 agents/              # 7 specialized agents
│   │   ├── 🎯 orchestrator.py      # Central coordinator
│   │   ├── 🔍 search_agent.py      # Web search capabilities  
│   │   ├── 📄 extraction_agent.py   # Content extraction
│   │   ├── ✅ fact_checker_agent.py # Claim validation
│   │   ├── ✍️ synthesis_agent.py    # Report generation
│   │   ├── 💾 file_save_agent.py    # Secure file operations
│   │   ├── 📊 logger_agent.py       # System monitoring
│   │   └── 🧩 base_agent.py         # Common agent functionality
│   ├── 📁 mcp_servers/         # MCP server implementations
│   │   ├── 🌐 primary_server.py     # Web tools with progress
│   │   ├── 🔒 filesystem_server.py  # Secure file ops
│   │   └── 🎨 user_interaction.py   # AI sampling demos
│   └── 📁 protocols/           # Communication schemas
│       ├── 📡 acp_schema.py         # Agent Communication Protocol
│       └── 🔧 mcp_schemas.py        # Model Context Protocol
├── 📁 docs/                   # Comprehensive documentation
│   ├── 🏛️ ARCHITECTURE.md          # System architecture guide
│   ├── 📡 ACP_SPEC.md               # ACP protocol specification  
│   └── 🔧 MCP_IN_DEPTH.md          # MCP implementation guide
├── 📁 output/                 # Generated content
│   ├── 📁 reports/            # Research reports (MCP Roots secured)
│   └── 📁 data/               # Extracted data
├── 🚀 main.py                 # System entry point
├── 📋 requirements.txt        # Python dependencies
└── 📖 README.md              # This file
```

## 🎓 Learning Objectives

Project Synapse serves as both a working system and an educational resource demonstrating:

### 1. Advanced Multi-Agent Patterns
- **Workflow Coordination**: How agents collaborate on complex tasks
- **Role Specialization**: Each agent has a distinct purpose and communication style
- **Error Handling**: Robust error reporting and recovery mechanisms
- **System Monitoring**: Comprehensive observability and logging

### 2. Protocol Implementation  
- **Type Safety**: Pydantic models ensuring message validation
- **Routing Mechanisms**: Both direct and broadcast communication patterns
- **Security Models**: MCP Roots preventing unauthorized file access
- **Progress Reporting**: Real-time feedback for long-running operations

### 3. Architectural Best Practices
- **Separation of Concerns**: Clear boundaries between agents, protocols, and tools
- **Extensibility**: Easy to add new agents, tools, and communication patterns
- **Testability**: Modular design enabling component-level testing
- **Documentation**: Comprehensive guides for understanding and extending

## 🔬 Technical Deep Dives

### Agent Communication Protocol (ACP)
Explore our custom messaging protocol that enables type-safe, structured communication between agents with support for both direct messaging and publish-subscribe patterns.

[📖 Read the ACP Specification →](docs/ACP_SPEC.md)

### Model Context Protocol (MCP)  
Discover how we implement MCP's advanced features including progress notifications, security boundaries, and AI sampling patterns.

[📖 Read the MCP Guide →](docs/MCP_IN_DEPTH.md)

### System Architecture
Understand the complete system design, from agent threading models to security architectures and scalability considerations.

[📖 Read the Architecture Guide →](docs/ARCHITECTURE.md)

## 🎪 Demo Highlights

When you run `python main.py`, you'll witness:

### 🔄 Real-Time Progress Notifications
```
[MCP Progress] Connecting to URL... (10%)
[MCP Progress] Downloading content... (30%)  
[MCP Progress] Parsing HTML structure... (60%)
[MCP Progress] Extracting main content... (80%)
[MCP Progress] Extraction complete (100%)
```

### 🛡️ Security Boundary Enforcement
```
[FileSystemServer] SECURITY VIOLATION: Access denied: 
'/etc/passwd' is outside allowed roots.
Allowed roots: ['/output/reports', '/output/data']
```

### 🤝 Agent Collaboration
```
[Orchestrator] Assigned search task task_a1b2c3d4 to SearchAgent
[SearchAgent] Web search completed: found 3 results
[ExtractionAgent] Starting content extraction from: https://example.com
[SynthesisAgent] Report synthesized: 1,247 words, 3 sources  
```

### 📊 System-Wide Monitoring
```
[Logger] System health check: healthy - 7 active components
[Logger] Research workflow completed successfully
```

## 🛠️ Customization & Extension

### Adding New Agents
```python
class CustomAgent(BaseAgent, MCPClientMixin):
    def handle_message(self, message: ACPMessage):
        # Implement custom message handling
        pass
```

### Creating New MCP Tools  
```python  
def custom_tool(self, params: CustomParams) -> Dict:
    # Implement tool logic with progress reporting
    mcp_context.report_progress("Processing...", 50)
    return {"result": "success"}
```

### Defining New Message Types
```python
class CustomPayload(BaseModel):
    custom_field: str
    options: Dict[str, Any]
```

## 🔮 Future Enhancements

While Project Synapse is complete as an educational demonstration, potential enhancements include:

- **🌐 Distributed Deployment**: Move from single-process to distributed agent deployment
- **⚡ Async Processing**: Implement async/await patterns for improved concurrency
- **🔄 StreamableHTTP**: Upgrade from stdio-like to HTTP-based MCP transport
- **📈 Metrics & Monitoring**: Integration with Prometheus/Grafana  
- **🧪 Testing Framework**: Comprehensive unit and integration test suite
- **🔌 Plugin System**: Dynamic agent and tool loading capabilities

## 🤝 Contributing

Project Synapse is designed as an educational reference implementation. While it's feature-complete for its intended purpose, we welcome:

- **📝 Documentation improvements**
- **🐛 Bug reports and fixes**  
- **💡 Enhancement suggestions**
- **📚 Educational use cases and examples**

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🎯 Key Takeaways

Project Synapse demonstrates that sophisticated multi-agent systems can be built with:

1. **🏗️ Clear Architecture**: Well-defined separation between communication, coordination, and tool execution
2. **🔒 Security First**: MCP Roots ensuring agents cannot access unauthorized resources  
3. **👀 Full Observability**: Comprehensive logging and monitoring of all system interactions
4. **🚀 Real Scalability**: Patterns that extend from demo to production environments
5. **📖 Complete Documentation**: Every component explained with examples and best practices

---

**Ready to explore the future of multi-agent systems?**

```bash
python main.py
```

*Watch as seven specialized agents collaborate to research quantum computing's impact on cryptography, demonstrating the power of ACP, A2A, and MCP protocols in action.* 🧠✨
A collaborative research swarm in order to educationally showcase (and for me to gain more experience on) ACP, MCP and A2A
