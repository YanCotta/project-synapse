"""
Project Synapse - Main Entry Point

Comprehensive demonstration of ACP (Agent Communication Protocol), 
A2A (Agent-to-Agent), and MCP (Model Context Protocol) capabilities
through a collaborative research swarm.

This script initializes all components and orchestrates a complete
research workflow to showcase the system's capabilities.
"""

import time
import os
from typing import Dict, Any

# Import MCP Servers
from src.mcp_servers.primary_server import PrimaryToolingServer
from src.mcp_servers.filesystem_server import FileSystemServer, UserInteractionServer

# Import Agents
from src.agents.orchestrator import OrchestratorAgent
from src.agents.search_agent import SearchAgent
from src.agents.extraction_agent import ExtractionAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.agents.file_save_agent import FileSaveAgent
from src.agents.logger_agent import LoggerAgent

# Import Protocol Schemas
from src.protocols.acp_schema import ACPMessage, ACPMsgType, TaskAssignPayload
from src.protocols.mcp_schemas import MCPContext


class ProjectSynapseSystem:
    """
    Main system coordinator for Project Synapse.
    
    Manages the initialization, configuration, and coordination of all
    agents and MCP servers in the research workflow.
    """
    
    def __init__(self):
        """Initialize the Project Synapse system."""
        print("=" * 60)
        print("🧠 PROJECT SYNAPSE - Advanced Multi-Agent Research System")
        print("=" * 60)
        print("Initializing ACP, A2A, and MCP showcase...")
        print()
        
        # System components
        self.message_bus = {}
        self.mcp_servers = {}
        self.agents = {}
        self.workflow_active = False
        
        # Configuration
        self.output_directory = "output"
        self.allowed_roots = [
            os.path.abspath(os.path.join(self.output_directory, "reports")),
            os.path.abspath(os.path.join(self.output_directory, "data"))
        ]
        
        # Ensure output directories exist
        os.makedirs(os.path.join(self.output_directory, "reports"), exist_ok=True)
        os.makedirs(os.path.join(self.output_directory, "data"), exist_ok=True)
    
    def initialize_mcp_servers(self):
        """Initialize all MCP servers with their respective capabilities."""
        print("🔧 Initializing MCP Servers...")
        
        # Primary Tooling Server (web search and extraction)
        self.mcp_servers["primary_tooling"] = PrimaryToolingServer("primary_tooling")
        print("  ✅ Primary Tooling Server: Web search and content extraction")
        
        # Filesystem Server (secure file operations with MCP Roots)
        self.mcp_servers["filesystem"] = FileSystemServer(
            allowed_roots=self.allowed_roots,
            server_id="filesystem"
        )
        print(f"  ✅ Filesystem Server: Secure file operations")
        print(f"     📁 Allowed roots: {[str(r) for r in self.allowed_roots]}")
        
        # User Interaction Server (MCP Sampling for text improvement)
        self.mcp_servers["user_interaction"] = UserInteractionServer("user_interaction")
        print("  ✅ User Interaction Server: AI-assisted text rephrasing")
        
        print()
    
    def initialize_agents(self):
        """Initialize all agents and configure their MCP server connections."""
        print("🤖 Initializing Agent Swarm...")
        
        # Logger Agent (service agent with pub/sub pattern)
        self.agents["logger"] = LoggerAgent("logger_agent", self.message_bus)
        print("  📊 Logger Agent: System monitoring and log aggregation")
        
        # Orchestrator Agent (central coordinator)
        self.agents["orchestrator"] = OrchestratorAgent("orchestrator", self.message_bus)
        print("  🎯 Orchestrator Agent: Workflow coordination and task management")
        
        # Search Agent (MCP client for web search)
        self.agents["search"] = SearchAgent("search_agent", "orchestrator", self.message_bus)
        self.agents["search"].register_mcp_server("primary_tooling", self.mcp_servers["primary_tooling"])
        print("  🔍 Search Agent: Web search capabilities via MCP")
        
        # Extraction Agent (MCP client with progress notifications)
        self.agents["extraction"] = ExtractionAgent("extraction_agent", "orchestrator", self.message_bus)
        self.agents["extraction"].register_mcp_server("primary_tooling", self.mcp_servers["primary_tooling"])
        print("  📄 Extraction Agent: Content extraction with MCP progress notifications")
        
        # Synthesis Agent (MCP client for text improvement)
        self.agents["synthesis"] = SynthesisAgent("synthesis_agent", "orchestrator", self.message_bus)
        self.agents["synthesis"].register_mcp_server("user_interaction", self.mcp_servers["user_interaction"])
        print("  ✍️  Synthesis Agent: Report generation with MCP sampling")
        
        # File Save Agent (MCP client with security restrictions)
        self.agents["file_save"] = FileSaveAgent("file_save_agent", "orchestrator", self.message_bus)
        self.agents["file_save"].register_mcp_server("filesystem", self.mcp_servers["filesystem"])
        print("  💾 File Save Agent: Secure file operations via MCP Roots")
        
        print()
    
    def start_agents(self):
        """Start all agents in the correct order."""
        print("🚀 Starting Agent Processing Threads...")
        
        # Start in dependency order
        agent_start_order = ["logger", "orchestrator", "search", "extraction", "synthesis", "file_save"]
        
        for agent_name in agent_start_order:
            if agent_name in self.agents:
                self.agents[agent_name].start()
                print(f"  ✅ {agent_name.title()} Agent started")
                time.sleep(0.1)  # Small delay for clean startup
        
        print()
    
    def stop_agents(self):
        """Stop all agents gracefully."""
        print("🛑 Stopping Agent Processing Threads...")
        
        for agent_name, agent in self.agents.items():
            agent.stop()
            print(f"  ✅ {agent_name.title()} Agent stopped")
        
        print()
    
    def initiate_research_workflow(self, research_query: str):
        """
        Initiate a complete research workflow.
        
        Args:
            research_query: The research question to investigate
        """
        print(f"🔬 Initiating Research Workflow")
        print(f"📝 Query: \"{research_query}\"")
        print()
        
        self.workflow_active = True
        
        # Create initial task assignment for the orchestrator
        initial_task = ACPMessage(
            sender_id="system",
            receiver_id="orchestrator", 
            msg_type=ACPMsgType.TASK_ASSIGN,
            payload=TaskAssignPayload(
                task_type="research_query",
                task_data={
                    "query": research_query,
                    "requester": "system"
                },
                priority=1
            ).model_dump()
        )
        
        # Send the task to the orchestrator
        orchestrator = self.agents["orchestrator"]
        orchestrator.receive_message(initial_task)
        
        print("✅ Research workflow initiated!")
        print("📡 Monitoring agent communications...")
        print()
    
    def monitor_workflow(self, timeout_seconds: int = 120):
        """
        Monitor the workflow progress and wait for completion.
        
        Args:
            timeout_seconds: Maximum time to wait for workflow completion
        """
        start_time = time.time()
        last_status_time = start_time
        
        print("⏱️  Workflow Monitoring Started")
        print(f"⏰ Timeout: {timeout_seconds} seconds")
        print("-" * 50)
        
        while self.workflow_active and (time.time() - start_time) < timeout_seconds:
            current_time = time.time()
            
            # Print status every 10 seconds
            if current_time - last_status_time >= 10:
                elapsed = int(current_time - start_time)
                orchestrator = self.agents["orchestrator"]
                status = orchestrator.get_workflow_status()
                
                print(f"[{elapsed:03d}s] Active: {status['active_tasks']} | "
                      f"Search: {status['search_results']} | "
                      f"Content: {status['extracted_content']} | "
                      f"Report: {'✅' if status['final_report_ready'] else '⏳'}")
                
                last_status_time = current_time
                
                # Check if workflow is complete
                if status['final_report_ready'] and status['active_tasks'] == 0:
                    print()
                    print("🎉 Research workflow completed successfully!")
                    self.workflow_active = False
                    break
            
            time.sleep(1)
        
        if self.workflow_active:
            print()
            print("⚠️  Workflow timeout reached")
            self.workflow_active = False
        
        print("-" * 50)
    
    def display_system_summary(self):
        """Display a summary of system capabilities and status."""
        print()
        print("📊 SYSTEM SUMMARY")
        print("=" * 40)
        
        # Agent status
        print("🤖 Agents:")
        for name, agent in self.agents.items():
            status = agent.get_status()
            running_status = "🟢 Running" if status["running"] else "🔴 Stopped"
            print(f"  {name.title()}: {running_status}")
        
        print()
        
        # MCP Server capabilities
        print("🔧 MCP Servers:")
        for name, server in self.mcp_servers.items():
            tools = server.get_available_tools()
            print(f"  {name.title()}: {', '.join(tools)}")
        
        print()
        
        # Logger system health
        if "logger" in self.agents:
            logger = self.agents["logger"]
            health = logger.get_system_health()
            print(f"🏥 System Health: {health['status'].upper()}")
            print(f"📈 Total Logs: {health['total_logs']}")
            print(f"⚡ Active Components: {health['active_components']}")
        
        print()
    
    def run_demonstration(self, research_query: str = None):
        """
        Run a complete demonstration of Project Synapse capabilities.
        
        Args:
            research_query: Optional research query (uses default if not provided)
        """
        if research_query is None:
            research_query = "What is the impact of quantum computing on cryptography?"
        
        try:
            # Phase 1: System Initialization
            self.initialize_mcp_servers()
            self.initialize_agents()
            self.start_agents()
            
            # Small delay to ensure all agents are ready
            time.sleep(2)
            
            # Phase 2: Research Workflow
            self.initiate_research_workflow(research_query)
            self.monitor_workflow(timeout_seconds=60)
            
            # Phase 3: Results and Summary
            self.display_system_summary()
            
            print("🎯 DEMONSTRATION HIGHLIGHTS:")
            print("  📡 ACP: Structured agent communication with typed messages")
            print("  🤝 A2A: Direct agent collaboration and peer coordination") 
            print("  🔒 MCP: Secure tool integration with progress notifications")
            print("  🛡️  MCP Roots: Filesystem security with path restrictions")
            print("  🎨 MCP Sampling: AI-assisted text generation and improvement")
            print()
            
        except KeyboardInterrupt:
            print("\n⚠️  Demonstration interrupted by user")
        except Exception as e:
            print(f"\n❌ Demonstration error: {e}")
        finally:
            # Clean shutdown
            self.stop_agents()
            print("✅ Project Synapse demonstration completed")


def main():
    """Main entry point for Project Synapse."""
    # Create and run the system
    system = ProjectSynapseSystem()
    
    # You can customize the research query here
    custom_query = "What is the impact of quantum computing on cryptography?"
    
    # Run the complete demonstration
    system.run_demonstration(custom_query)


if __name__ == "__main__":
    main()
