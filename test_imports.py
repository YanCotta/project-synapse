#!/usr/bin/env python3
"""
Quick test to verify Project Synapse imports and basic functionality
"""

try:
    print("🧪 Testing Project Synapse imports...")
    
    # Test protocol imports
    from src.protocols.acp_schema import ACPMessage, ACPMsgType
    from src.protocols.mcp_schemas import SearchWebParams, MCPContext
    print("✅ Protocol schemas imported successfully")
    
    # Test MCP server imports
    from src.mcp_servers.primary_server import PrimaryToolingServer
    from src.mcp_servers.filesystem_server import FileSystemServer
    print("✅ MCP servers imported successfully")
    
    # Test agent imports
    from src.agents.base_agent import BaseAgent
    from src.agents.orchestrator import OrchestratorAgent
    print("✅ Agent classes imported successfully")
    
    # Test basic functionality
    server = PrimaryToolingServer()
    print("✅ MCP server instantiation works")
    
    print("\n🎉 Project Synapse is ready to run!")
    print("Execute: python main.py")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    print("Please check your Python environment and dependencies")
