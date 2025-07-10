"""
Base Agent Class

Common functionality and interfaces for all agents in Project Synapse.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from queue import Queue
from threading import Thread, Event
from ..protocols.acp_schema import ACPMessage, ACPMsgType


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Project Synapse system.
    
    Provides common functionality for message handling, lifecycle management,
    and communication with other agents through the message bus.
    """
    
    def __init__(self, agent_id: str, message_bus: Dict = None):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            message_bus: Shared message bus for inter-agent communication
        """
        self.agent_id = agent_id
        self.message_bus = message_bus or {}
        self.inbox = Queue()
        self.outbox = Queue()
        self.running = False
        self.stop_event = Event()
        self.thread = None
        
        # Register with message bus
        if self.message_bus is not None:
            self.message_bus[self.agent_id] = self
    
    def start(self):
        """Start the agent's message processing thread."""
        if not self.running:
            self.running = True
            self.stop_event.clear()
            self.thread = Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print(f"[{self.agent_id}] Agent started")
    
    def stop(self):
        """Stop the agent's message processing thread."""
        if self.running:
            self.running = False
            self.stop_event.set()
            if self.thread:
                self.thread.join(timeout=1.0)
            print(f"[{self.agent_id}] Agent stopped")
    
    def _run_loop(self):
        """Main agent processing loop (runs in separate thread)."""
        print(f"[{self.agent_id}] Starting processing loop")
        
        while self.running and not self.stop_event.is_set():
            try:
                # Process incoming messages
                if not self.inbox.empty():
                    message = self.inbox.get_nowait()
                    self.handle_message(message)
                
                # Allow subclasses to perform periodic tasks
                self.periodic_task()
                
                # Small delay to prevent busy waiting
                self.stop_event.wait(0.1)
                
            except Exception as e:
                print(f"[{self.agent_id}] Error in processing loop: {e}")
    
    def send_message(self, message: ACPMessage):
        """
        Send a message to another agent or broadcast to a topic.
        
        Args:
            message: ACP message to send
        """
        self.outbox.put(message)
        
        # Route message through message bus
        if self.message_bus:
            if message.receiver_id:
                # Direct message to specific agent
                if message.receiver_id in self.message_bus:
                    target_agent = self.message_bus[message.receiver_id]
                    target_agent.receive_message(message)
                else:
                    print(f"[{self.agent_id}] Warning: Agent '{message.receiver_id}' not found")
            elif message.topic:
                # Broadcast to all agents listening to topic
                for agent in self.message_bus.values():
                    if hasattr(agent, 'subscribed_topics') and message.topic in agent.subscribed_topics:
                        agent.receive_message(message)
    
    def receive_message(self, message: ACPMessage):
        """
        Receive a message from another agent.
        
        Args:
            message: ACP message received
        """
        self.inbox.put(message)
    
    def create_message(self, receiver_id: str = None, topic: str = None, 
                      msg_type: ACPMsgType = None, payload: Dict = None) -> ACPMessage:
        """
        Create an ACP message with this agent as sender.
        
        Args:
            receiver_id: Target agent ID for direct messages
            topic: Topic for broadcast messages
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
    
    @abstractmethod
    def handle_message(self, message: ACPMessage):
        """
        Handle an incoming message.
        
        Must be implemented by subclasses to define agent-specific behavior.
        
        Args:
            message: ACP message to handle
        """
        pass
    
    def periodic_task(self):
        """
        Perform periodic tasks (called during each processing loop iteration).
        
        Can be overridden by subclasses for periodic maintenance tasks.
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Dictionary containing agent status information
        """
        return {
            "agent_id": self.agent_id,
            "running": self.running,
            "inbox_size": self.inbox.qsize(),
            "outbox_size": self.outbox.qsize()
        }


class MCPClientMixin:
    """
    Mixin class providing MCP client capabilities to agents.
    
    Agents that need to interact with MCP servers should inherit from this
    in addition to BaseAgent.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mcp_servers = {}
    
    def register_mcp_server(self, server_name: str, server_instance):
        """
        Register an MCP server for use by this agent.
        
        Args:
            server_name: Name to identify the server
            server_instance: The MCP server instance
        """
        self.mcp_servers[server_name] = server_instance
        print(f"[{self.agent_id}] Registered MCP server: {server_name}")
    
    def call_mcp_tool(self, server_name: str, tool_name: str, params: Dict, 
                      mcp_context=None) -> Dict:
        """
        Call a tool on an MCP server.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            params: Parameters for the tool
            mcp_context: Optional MCP context for progress reporting
            
        Returns:
            Result from the MCP tool
            
        Raises:
            ValueError: If server or tool is not available
        """
        if server_name not in self.mcp_servers:
            raise ValueError(f"MCP server '{server_name}' not registered")
        
        server = self.mcp_servers[server_name]
        
        print(f"[{self.agent_id}] Calling {server_name}.{tool_name}")
        
        try:
            if mcp_context:
                result = server.call_tool(tool_name, params, mcp_context)
            else:
                result = server.call_tool(tool_name, params)
            
            print(f"[{self.agent_id}] MCP tool call successful")
            return result
            
        except Exception as e:
            print(f"[{self.agent_id}] MCP tool call failed: {e}")
            raise


class TopicSubscriberMixin:
    """
    Mixin class for agents that subscribe to broadcast topics.
    
    Agents that need to listen to LOG_BROADCAST or other topic-based
    messages should inherit from this mixin.
    """
    
    def __init__(self, *args, subscribed_topics: List[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribed_topics = subscribed_topics or []
        print(f"[{self.agent_id}] Subscribed to topics: {self.subscribed_topics}")
    
    def subscribe_to_topic(self, topic: str):
        """
        Subscribe to a broadcast topic.
        
        Args:
            topic: Topic name to subscribe to
        """
        if topic not in self.subscribed_topics:
            self.subscribed_topics.append(topic)
            print(f"[{self.agent_id}] Subscribed to topic: {topic}")
    
    def unsubscribe_from_topic(self, topic: str):
        """
        Unsubscribe from a broadcast topic.
        
        Args:
            topic: Topic name to unsubscribe from
        """
        if topic in self.subscribed_topics:
            self.subscribed_topics.remove(topic)
            print(f"[{self.agent_id}] Unsubscribed from topic: {topic}")


def generate_task_id() -> str:
    """Generate a unique task ID."""
    return str(uuid.uuid4())[:8]
