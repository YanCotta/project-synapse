"""
Message Bus Package

Provides RabbitMQ-based messaging infrastructure for async agent communication.
"""

from .rabbitmq_bus import RabbitMQBus

__all__ = ["RabbitMQBus"]
