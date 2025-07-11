#!/usr/bin/env python3
"""
Async Main Application

Fully functional, asynchronous version of Project Synapse using:
- FastAPI MCP servers
- RabbitMQ message bus  
- asyncio for concurrent agent execution
"""

import asyncio
import os
import sys
import logging
from typing import Dict, List
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.message_bus.rabbitmq_bus import RabbitMQBus
from src.agents.async_orchestrator import AsyncOrchestratorAgent
from src.agents.async_search_agent import AsyncSearchAgent
from src.agents.async_extraction_agent import AsyncExtractionAgent
from src.agents.async_fact_checker_agent import AsyncFactCheckerAgent
from src.agents.async_synthesis_agent import AsyncSynthesisAgent
from src.agents.async_file_save_agent import AsyncFileSaveAgent
from src.agents.async_logger_agent import AsyncLoggerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/synapse.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


async def wait_for_mcp_servers(mcp_servers: Dict[str, str], timeout: int = 60):
    """
    Wait for MCP servers to become available.
    
    Args:
        mcp_servers: Dictionary of server name to URL mappings
        timeout: Maximum time to wait in seconds
    """
    import aiohttp
    
    logger.info("Waiting for MCP servers to become available...")
    
    async with aiohttp.ClientSession() as session:
        for server_name, server_url in mcp_servers.items():
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    async with session.get(f"{server_url}/health", timeout=5) as response:
                        if response.status == 200:
                            logger.info(f"✅ {server_name} server is ready ({server_url})")
                            break
                        else:
                            logger.warning(f"❌ {server_name} server returned {response.status}")
                            
                except Exception as e:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        logger.error(f"❌ Timeout waiting for {server_name} server at {server_url}")
                        raise TimeoutError(f"MCP server {server_name} not available after {timeout}s")
                    
                    logger.debug(f"⏳ Waiting for {server_name} server... ({e})")
                    await asyncio.sleep(2)


async def create_agents(message_bus: RabbitMQBus, mcp_servers: Dict[str, str]) -> List:
    """
    Create and configure all system agents.
    
    Args:
        message_bus: RabbitMQ message bus instance
        mcp_servers: MCP server URL mappings
        
    Returns:
        List of configured agent instances
    """
    agents = []
    
    try:
        # Create orchestrator agent
        orchestrator = AsyncOrchestratorAgent("orchestrator", message_bus, mcp_servers)
        agents.append(orchestrator)
        
        # Create worker agents
        search_agent = AsyncSearchAgent("search_agent", message_bus, mcp_servers)
        agents.append(search_agent)
        
        extraction_agent = AsyncExtractionAgent("extraction_agent", message_bus, mcp_servers)
        agents.append(extraction_agent)
        
        fact_checker = AsyncFactCheckerAgent("fact_checker_agent", message_bus, mcp_servers)
        agents.append(fact_checker)
        
        synthesis_agent = AsyncSynthesisAgent("synthesis_agent", message_bus, mcp_servers)
        agents.append(synthesis_agent)
        
        file_save_agent = AsyncFileSaveAgent("file_save_agent", message_bus, mcp_servers)
        agents.append(file_save_agent)
        
        # Create logger agent (subscribes to logs topic)
        logger_agent = AsyncLoggerAgent("logger_agent", message_bus, mcp_servers)
        agents.append(logger_agent)
        
        logger.info(f"Created {len(agents)} agents successfully")
        return agents
        
    except Exception as e:
        logger.error(f"Failed to create agents: {e}")
        raise


async def start_research_workflow(orchestrator: AsyncOrchestratorAgent, query: str):
    """
    Start the collaborative research workflow.
    
    Args:
        orchestrator: Orchestrator agent instance
        query: Research query to investigate
    """
    logger.info(f"🚀 Starting research workflow for: '{query}'")
    
    try:
        await orchestrator.start_research(query)
        logger.info("✅ Research workflow initiated successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start research workflow: {e}")
        raise


async def monitor_workflow_progress(agents: List, timeout: int = 300):
    """
    Monitor workflow progress and wait for completion.
    
    Args:
        agents: List of agent instances
        timeout: Maximum time to wait for completion in seconds
    """
    start_time = asyncio.get_event_loop().time()
    
    logger.info(f"⏳ Monitoring workflow progress (timeout: {timeout}s)")
    
    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        
        if elapsed > timeout:
            logger.warning(f"⏰ Workflow timeout reached ({timeout}s)")
            break
        
        # Check agent status
        running_agents = [agent for agent in agents if agent.running]
        
        if not running_agents:
            logger.info("✅ All agents have completed their tasks")
            break
        
        # Log progress every 30 seconds
        if int(elapsed) % 30 == 0:
            logger.info(f"⏳ Workflow running... ({int(elapsed)}s elapsed, {len(running_agents)} agents active)")
        
        await asyncio.sleep(5)
    
    logger.info("📊 Workflow monitoring complete")


async def main():
    """Main application entry point."""
    
    # Load environment variables
    load_dotenv()
    
    # Create necessary directories
    os.makedirs("output/reports", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logger.info("🧠 Starting Project Synapse - Async Implementation")
    logger.info("=" * 60)
    
    # Configuration
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://synapse:synapse123@localhost:5672/")
    
    mcp_servers = {
        "primary_tooling": os.getenv("PRIMARY_TOOLING_URL", "http://localhost:8001"),
        "filesystem": os.getenv("FILESYSTEM_URL", "http://localhost:8002"),
    }
    
    research_query = os.getenv("RESEARCH_QUERY", "quantum computing impact on cryptography")
    workflow_timeout = int(os.getenv("WORKFLOW_TIMEOUT", "300"))
    
    logger.info(f"🌐 RabbitMQ URL: {rabbitmq_url}")
    logger.info(f"🔧 MCP Servers: {mcp_servers}")
    logger.info(f"🔍 Research Query: {research_query}")
    
    # Initialize message bus
    message_bus = None
    agents = []
    
    try:
        # Connect to RabbitMQ
        logger.info("📡 Connecting to RabbitMQ message bus...")
        message_bus = RabbitMQBus(rabbitmq_url)
        
        if not await message_bus.connect():
            raise RuntimeError("Failed to connect to RabbitMQ")
        
        logger.info("✅ Connected to RabbitMQ successfully")
        
        # Wait for MCP servers
        await wait_for_mcp_servers(mcp_servers, timeout=60)
        
        # Create agents
        logger.info("🤖 Creating and configuring agents...")
        agents = await create_agents(message_bus, mcp_servers)
        
        # Start all agents
        logger.info("🚀 Starting agent processes...")
        await asyncio.gather(*[agent.start() for agent in agents])
        logger.info("✅ All agents started successfully")
        
        # Get orchestrator reference
        orchestrator = next(agent for agent in agents if agent.agent_id == "orchestrator")
        
        # Start research workflow
        await start_research_workflow(orchestrator, research_query)
        
        # Monitor progress
        await monitor_workflow_progress(agents, workflow_timeout)
        
        logger.info("🎉 Project Synapse workflow completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("⚠️  Received interrupt signal, shutting down...")
        
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        return 1
        
    finally:
        # Graceful shutdown
        logger.info("🛑 Shutting down Project Synapse...")
        
        # Stop all agents
        if agents:
            logger.info("Stopping agents...")
            await asyncio.gather(*[agent.stop() for agent in agents], return_exceptions=True)
        
        # Disconnect message bus
        if message_bus:
            logger.info("Disconnecting from RabbitMQ...")
            await message_bus.disconnect()
        
        logger.info("✅ Shutdown complete")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
