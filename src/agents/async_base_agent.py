"""
Async Base Agent

Asynchronous base class for all agents in the Project Synapse system.
Provides async message handling, MCP client capabilities, and RabbitMQ integration.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import aiohttp
from urllib.parse import urljoin

from ..message_bus.rabbitmq_bus import RabbitMQBus
from ..protocols.acp_schema import ACPMessage, ACPMsgType

logger = logging.getLogger(__name__)


class AsyncBaseAgent(ABC):
    """
    Abstract base class for asynchronous agents.
    
    Provides:
    - Async message handling via RabbitMQ
    - HTTP-based MCP tool calls with progress support
    - Graceful lifecycle management
    - Error handling and recovery
    """
    
    def __init__(self, agent_id: str, message_bus: RabbitMQBus, mcp_servers: Dict[str, str]):
        """
        Initialize the async base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            message_bus: RabbitMQ message bus for communication
            mcp_servers: Dictionary mapping server names to URLs
        """
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.mcp_servers = mcp_servers
        
        # HTTP session for MCP calls
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Agent state
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        logger.info(f"[{self.agent_id}] Async agent initialized")
    
    async def start(self):
        """Start the agent with async session and message subscriptions."""
        try:
            # Create HTTP session for MCP calls
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            self.running = True
            
            # Subscribe to direct messages
            await self.message_bus.subscribe_agent(self.agent_id, self.handle_message)
            
            # Subscribe to topics if agent supports it
            if hasattr(self, 'subscribed_topics'):
                for topic in self.subscribed_topics:
                    await self.message_bus.subscribe_topic(topic, self.handle_message)
            
            # Start agent main loop
            loop_task = asyncio.create_task(self._agent_loop())
            self.tasks.append(loop_task)
            
            logger.info(f"[{self.agent_id}] Agent started successfully")
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to start agent: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Gracefully stop the agent."""
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Unsubscribe from messages
        try:
            await self.message_bus.unsubscribe_agent(self.agent_id)
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Error unsubscribing: {e}")
        
        # Close HTTP session
        if self.session:
            await self.session.close()
            
        logger.info(f"[{self.agent_id}] Agent stopped")
    
    async def _agent_loop(self):
        """Main agent processing loop."""
        while self.running:
            try:
                await self.periodic_task()
                await asyncio.sleep(1.0)  # 1 second interval
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.agent_id}] Error in agent loop: {e}")
                await asyncio.sleep(5.0)  # Back off on error
    
    @abstractmethod
    async def handle_message(self, message: ACPMessage):
        """
        Handle incoming ACP messages.
        
        Args:
            message: Incoming ACP message to process
        """
        pass
    
    async def periodic_task(self):
        """
        Override for periodic agent tasks.
        Called every second while agent is running.
        """
        pass
    
    async def send_message(self, message: ACPMessage):
        """
        Send ACP message via message bus.
        
        Args:
            message: ACP message to send
        """
        try:
            await self.message_bus.publish_message(message)
            logger.debug(f"[{self.agent_id}] Sent message: {message.msg_type.value}")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to send message: {e}")
            raise
    
    def create_message(self, receiver_id: str = None, topic: str = None, 
                      msg_type: ACPMsgType = None, payload: Dict = None) -> ACPMessage:
        """
        Create an ACP message with sender ID populated.
        
        Args:
            receiver_id: Target agent ID for direct messages
            topic: Topic name for broadcast messages
            msg_type: Type of message
            payload: Message payload
            
        Returns:
            Constructed ACP message
        """
        return ACPMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            topic=topic,
            msg_type=msg_type,
            payload=payload or {}
        )
    
    async def call_mcp_tool(self, server_name: str, tool_name: str, params: Dict) -> Dict:
        """
        Make async call to MCP server tool.
        
        Args:
            server_name: Name of MCP server
            tool_name: Name of tool to call
            params: Tool parameters
            
        Returns:
            Tool response data
        """
        if server_name not in self.mcp_servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server_url = self.mcp_servers[server_name]
        endpoint = f"/tools/{tool_name}"
        url = urljoin(server_url, endpoint)
        
        try:
            async with self.session.post(url, json=params) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"[{self.agent_id}] MCP call successful: {server_name}.{tool_name}")
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"MCP call failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"[{self.agent_id}] MCP call failed ({server_name}.{tool_name}): {e}")
            raise
    
    async def call_mcp_tool_streaming(self, server_name: str, tool_name: str, 
                                    params: Dict, progress_callback=None) -> Dict:
        """
        Make streaming MCP call with progress notifications.
        
        Args:
            server_name: Name of MCP server
            tool_name: Name of tool to call
            params: Tool parameters
            progress_callback: Optional callback for progress updates
            
        Returns:
            Final tool response
        """
        if server_name not in self.mcp_servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server_url = self.mcp_servers[server_name]
        endpoint = f"/tools/{tool_name}"
        url = urljoin(server_url, endpoint)
        
        try:
            async with self.session.post(url, json=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"MCP streaming call failed: {response.status} - {error_text}")
                
                # Handle Server-Sent Events
                async for line in response.content:
                    if line:
                        line_text = line.decode('utf-8').strip()
                        
                        if line_text.startswith('event: '):
                            event_type = line_text[7:]
                        elif line_text.startswith('data: '):
                            data_text = line_text[6:]
                            
                            try:
                                data = eval(data_text)  # In production, use json.loads
                                
                                if event_type == 'progress':
                                    await self._handle_progress(data, progress_callback)
                                elif event_type == 'result':
                                    logger.debug(f"[{self.agent_id}] MCP streaming call complete: {server_name}.{tool_name}")
                                    return data
                                elif event_type == 'error':
                                    raise Exception(f"MCP server error: {data}")
                                    
                            except Exception as e:
                                logger.warning(f"[{self.agent_id}] Failed to parse SSE data: {e}")
                
                raise Exception("Streaming response ended without result")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] MCP streaming call failed ({server_name}.{tool_name}): {e}")
            raise
    
    async def _handle_progress(self, progress_data: Dict, callback=None):
        """Handle progress notification from MCP server."""
        message = progress_data.get('message', 'Processing...')
        percentage = progress_data.get('percentage', 0)
        
        logger.info(f"[{self.agent_id}] Progress: {message} ({percentage}%)")
        
        if callback:
            try:
                await callback(progress_data)
            except Exception as e:
                logger.warning(f"[{self.agent_id}] Progress callback failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "running": self.running,
            "session_open": self.session is not None and not self.session.closed,
            "active_tasks": len([t for t in self.tasks if not t.done()]),
            "mcp_servers": list(self.mcp_servers.keys())
        }


class MCPClientMixin:
    """
    Mixin class providing MCP client functionality for backward compatibility.
    
    This maintains compatibility with the simulation version while providing
    real async HTTP-based MCP calls.
    """
    
    def __init__(self):
        """Initialize MCP client mixin."""
        pass
    
    async def call_mcp_tool_async(self, server_name: str, tool_name: str, 
                                params: Dict, mcp_context=None) -> Dict:
        """
        Async version of MCP tool call with optional context.
        
        Args:
            server_name: Name of MCP server
            tool_name: Name of tool to call
            params: Tool parameters
            mcp_context: Optional MCP context (for compatibility)
            
        Returns:
            Tool response data
        """
        # For tools that support streaming (like browse_and_extract)
        if tool_name in ['browse_and_extract'] and hasattr(self, 'call_mcp_tool_streaming'):
            return await self.call_mcp_tool_streaming(server_name, tool_name, params)
        else:
            return await self.call_mcp_tool(server_name, tool_name, params)


class TopicSubscriberMixin:
    """
    Mixin for agents that subscribe to topic broadcasts.
    """
    
    def __init__(self, subscribed_topics: List[str] = None):
        """
        Initialize topic subscriber.
        
        Args:
            subscribed_topics: List of topics to subscribe to
        """
        self.subscribed_topics = subscribed_topics or []


def generate_task_id() -> str:
    """Generate a unique task ID."""
    import uuid
    return str(uuid.uuid4())[:8]
