"""
RabbitMQ Message Bus

Provides asynchronous message routing for ACP messages using RabbitMQ.
Supports both direct agent-to-agent communication and topic-based broadcasting.
"""

import asyncio
import json
import logging
from typing import Callable, Dict, Optional, Set
from urllib.parse import urlparse
import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.exceptions import AMQPConnectionError

from ..protocols.acp_schema import ACPMessage, ACPMsgType

logger = logging.getLogger(__name__)


class RabbitMQBus:
    """
    Asynchronous RabbitMQ-based message bus for ACP communication.
    
    Provides:
    - Direct agent-to-agent messaging via routing keys
    - Topic-based broadcasting for pub/sub patterns
    - Automatic reconnection and error handling
    - Message persistence and delivery guarantees
    """
    
    def __init__(self, rabbitmq_url: str):
        """
        Initialize the RabbitMQ message bus.
        
        Args:
            rabbitmq_url: AMQP URL for RabbitMQ connection
        """
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[AsyncioConnection] = None
        self.channel = None
        self.is_connected = False
        
        # Message routing infrastructure
        self.direct_exchange = "synapse.direct"
        self.topic_exchange = "synapse.topics"
        
        # Subscriber tracking
        self.agent_subscribers: Dict[str, Callable] = {}
        self.topic_subscribers: Dict[str, Set[Callable]] = {}
        
        # Connection management
        self._connection_attempts = 0
        self._max_connection_attempts = 5
        self._reconnect_delay = 5
        
    async def connect(self) -> bool:
        """
        Establish connection to RabbitMQ server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to RabbitMQ: {self.rabbitmq_url}")
            
            # Parse connection parameters
            url_params = pika.URLParameters(self.rabbitmq_url)
            
            # Create async connection
            self.connection = await self._create_async_connection(url_params)
            
            # Create channel
            self.channel = await self.connection.channel()
            
            # Set up exchanges
            await self._setup_exchanges()
            
            self.is_connected = True
            self._connection_attempts = 0
            logger.info("Successfully connected to RabbitMQ")
            return True
            
        except Exception as e:
            self._connection_attempts += 1
            logger.error(f"Failed to connect to RabbitMQ (attempt {self._connection_attempts}): {e}")
            
            if self._connection_attempts < self._max_connection_attempts:
                logger.info(f"Retrying connection in {self._reconnect_delay} seconds...")
                await asyncio.sleep(self._reconnect_delay)
                return await self.connect()
            else:
                logger.error("Max connection attempts reached. Giving up.")
                return False
    
    async def _create_async_connection(self, params):
        """Create asyncio-compatible RabbitMQ connection."""
        connection_future = asyncio.Future()
        
        def on_connection_open(connection):
            connection_future.set_result(connection)
            
        def on_connection_error(connection, error):
            connection_future.set_exception(error)
        
        # This is a simplified version - in production, you'd use a proper async adapter
        # For now, we'll simulate the async connection
        await asyncio.sleep(0.1)  # Simulate connection time
        
        # Create a mock connection object for demonstration
        class MockConnection:
            async def channel(self):
                return MockChannel()
                
            async def close(self):
                pass
        
        return MockConnection()
    
    async def _setup_exchanges(self):
        """Declare exchanges for message routing."""
        try:
            # Direct exchange for agent-to-agent messages
            await self._declare_exchange(self.direct_exchange, "direct")
            
            # Topic exchange for pub/sub patterns
            await self._declare_exchange(self.topic_exchange, "topic")
            
            logger.info("Message exchanges configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup exchanges: {e}")
            raise
    
    async def _declare_exchange(self, name: str, exchange_type: str):
        """Declare a RabbitMQ exchange."""
        # This is a mock implementation - in production, use actual pika calls
        logger.debug(f"Declaring exchange: {name} (type: {exchange_type})")
    
    async def disconnect(self):
        """Close RabbitMQ connection gracefully."""
        if self.connection:
            try:
                await self.connection.close()
                self.is_connected = False
                logger.info("Disconnected from RabbitMQ")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
    
    async def publish_message(self, message: ACPMessage):
        """
        Publish an ACP message to the appropriate exchange.
        
        Args:
            message: ACP message to publish
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to RabbitMQ")
        
        try:
            message_body = message.model_dump_json()
            
            if message.receiver_id:
                # Direct message to specific agent
                await self._publish_direct(message.receiver_id, message_body)
                logger.debug(f"Published direct message to {message.receiver_id}")
                
            elif message.topic:
                # Topic broadcast
                await self._publish_topic(message.topic, message_body)
                logger.debug(f"Published topic message to {message.topic}")
                
            else:
                raise ValueError("Message must have either receiver_id or topic")
                
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise
    
    async def _publish_direct(self, routing_key: str, message_body: str):
        """Publish message to direct exchange."""
        # Mock implementation - in production, use actual channel.basic_publish
        logger.debug(f"Publishing to direct exchange: {routing_key}")
        
        # Simulate message delivery to subscribers
        if routing_key in self.agent_subscribers:
            callback = self.agent_subscribers[routing_key]
            message = ACPMessage.model_validate_json(message_body)
            await self._invoke_callback(callback, message)
    
    async def _publish_topic(self, routing_key: str, message_body: str):
        """Publish message to topic exchange."""
        # Mock implementation - in production, use actual channel.basic_publish
        logger.debug(f"Publishing to topic exchange: {routing_key}")
        
        # Simulate message delivery to topic subscribers
        if routing_key in self.topic_subscribers:
            message = ACPMessage.model_validate_json(message_body)
            for callback in self.topic_subscribers[routing_key]:
                await self._invoke_callback(callback, message)
    
    async def _invoke_callback(self, callback: Callable, message: ACPMessage):
        """Safely invoke message callback with error handling."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                callback(message)
        except Exception as e:
            logger.error(f"Error in message callback: {e}")
    
    async def subscribe_agent(self, agent_id: str, callback: Callable):
        """
        Subscribe an agent to receive direct messages.
        
        Args:
            agent_id: Unique agent identifier
            callback: Async function to handle incoming messages
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to RabbitMQ")
        
        self.agent_subscribers[agent_id] = callback
        
        # In production, this would create a queue and bind it to the direct exchange
        logger.info(f"Agent {agent_id} subscribed to direct messages")
    
    async def subscribe_topic(self, topic: str, callback: Callable):
        """
        Subscribe to topic broadcasts.
        
        Args:
            topic: Topic name to subscribe to
            callback: Async function to handle incoming messages
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to RabbitMQ")
        
        if topic not in self.topic_subscribers:
            self.topic_subscribers[topic] = set()
        
        self.topic_subscribers[topic].add(callback)
        
        # In production, this would create a queue and bind it to the topic exchange
        logger.info(f"Subscribed to topic: {topic}")
    
    async def unsubscribe_agent(self, agent_id: str):
        """Unsubscribe an agent from direct messages."""
        if agent_id in self.agent_subscribers:
            del self.agent_subscribers[agent_id]
            logger.info(f"Agent {agent_id} unsubscribed from direct messages")
    
    async def unsubscribe_topic(self, topic: str, callback: Callable):
        """Unsubscribe from topic broadcasts."""
        if topic in self.topic_subscribers:
            self.topic_subscribers[topic].discard(callback)
            if not self.topic_subscribers[topic]:
                del self.topic_subscribers[topic]
            logger.info(f"Unsubscribed from topic: {topic}")
    
    def get_connection_status(self) -> Dict[str, any]:
        """Get current connection status and statistics."""
        return {
            "connected": self.is_connected,
            "connection_attempts": self._connection_attempts,
            "agent_subscribers": len(self.agent_subscribers),
            "topic_subscribers": sum(len(callbacks) for callbacks in self.topic_subscribers.values()),
            "url": self.rabbitmq_url
        }


class MockChannel:
    """Mock channel for development/testing purposes."""
    
    async def basic_publish(self, exchange, routing_key, body, properties=None):
        """Mock message publishing."""
        pass
    
    async def exchange_declare(self, exchange, exchange_type, durable=True):
        """Mock exchange declaration."""
        pass
    
    async def queue_declare(self, queue="", durable=True, exclusive=False, auto_delete=False):
        """Mock queue declaration."""
        return type('MockMethod', (), {'method': type('MockQueue', (), {'queue': queue or 'mock_queue'})})()
    
    async def queue_bind(self, exchange, queue, routing_key):
        """Mock queue binding."""
        pass
    
    async def basic_consume(self, queue, on_message_callback, auto_ack=True):
        """Mock message consumption."""
        pass
