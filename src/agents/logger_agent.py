"""
Logger Agent

Service agent that listens to broadcast messages and logs system activity.
Demonstrates A2A pub/sub pattern for system-wide monitoring.
"""

import time
from datetime import datetime
from typing import Dict, List
from .base_agent import BaseAgent, TopicSubscriberMixin
from ..protocols.acp_schema import ACPMessage, ACPMsgType, LogBroadcastPayload


class LoggerAgent(BaseAgent, TopicSubscriberMixin):
    """
    Service agent responsible for system-wide logging and monitoring.
    
    This agent demonstrates:
    - A2A pub/sub pattern by subscribing to broadcast topics
    - System-wide monitoring and observability
    - Log aggregation and formatting
    - Service agent pattern (provides utility to other agents)
    """
    
    def __init__(self, agent_id: str = "logger_agent", message_bus: Dict = None):
        """
        Initialize the Logger Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            message_bus: Shared message bus for inter-agent communication
        """
        BaseAgent.__init__(self, agent_id, message_bus)
        TopicSubscriberMixin.__init__(self, subscribed_topics=["logs"])
        
        # Log storage and configuration
        self.log_history = []
        self.max_log_entries = 1000
        self.log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.active_components = set()
        
        print(f"[{self.agent_id}] Logger service started - monitoring system activity")
        
        # Log the logger's own startup
        self._add_log_entry("INFO", "Logger service initialized", self.agent_id)
    
    def handle_message(self, message: ACPMessage):
        """
        Handle incoming messages, primarily log broadcasts.
        
        Args:
            message: ACP message to process
        """
        if message.msg_type == ACPMsgType.LOG_BROADCAST:
            self._handle_log_broadcast(message)
        else:
            # Log unexpected messages for debugging
            self._add_log_entry(
                "DEBUG", 
                f"Received unexpected message type: {message.msg_type.value} from {message.sender_id}",
                self.agent_id
            )
    
    def _handle_log_broadcast(self, message: ACPMessage):
        """
        Process a log broadcast message from any agent.
        
        Args:
            message: Log broadcast message
        """
        try:
            payload = LogBroadcastPayload(**message.payload)
            
            # Track active components
            component = payload.component or message.sender_id
            self.active_components.add(component)
            
            # Add to log history
            self._add_log_entry(payload.level, payload.message, component)
            
            # Display the log in real-time
            self._display_log_entry(payload.level, payload.message, component)
            
        except Exception as e:
            # Handle malformed log messages
            self._add_log_entry(
                "ERROR",
                f"Failed to process log broadcast from {message.sender_id}: {e}",
                self.agent_id
            )
    
    def _add_log_entry(self, level: str, message: str, component: str):
        """
        Add a log entry to the history.
        
        Args:
            level: Log level
            message: Log message
            component: Component that generated the log
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "level": level.upper(),
            "component": component,
            "message": message
        }
        
        self.log_history.append(log_entry)
        
        # Maintain maximum log history size
        if len(self.log_history) > self.max_log_entries:
            self.log_history = self.log_history[-self.max_log_entries:]
    
    def _display_log_entry(self, level: str, message: str, component: str):
        """
        Display a log entry to the console with formatting.
        
        Args:
            level: Log level
            message: Log message
            component: Component that generated the log
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding for different log levels (if supported)
        level_symbols = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "WARNING": "⚠️", 
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }
        
        symbol = level_symbols.get(level.upper(), "📝")
        
        # Format: [TIME] SYMBOL [LEVEL] [COMPONENT] MESSAGE
        log_line = f"[{timestamp}] {symbol} [{level.upper()}] [{component}] {message}"
        
        print(log_line)
    
    def get_log_summary(self, last_n_entries: int = 10) -> List[Dict]:
        """
        Get a summary of recent log entries.
        
        Args:
            last_n_entries: Number of recent entries to return
            
        Returns:
            List of recent log entries
        """
        return self.log_history[-last_n_entries:] if self.log_history else []
    
    def get_logs_by_level(self, level: str) -> List[Dict]:
        """
        Get all log entries for a specific level.
        
        Args:
            level: Log level to filter by
            
        Returns:
            List of log entries matching the level
        """
        return [entry for entry in self.log_history if entry["level"] == level.upper()]
    
    def get_logs_by_component(self, component: str) -> List[Dict]:
        """
        Get all log entries for a specific component.
        
        Args:
            component: Component name to filter by
            
        Returns:
            List of log entries from the component
        """
        return [entry for entry in self.log_history if entry["component"] == component]
    
    def get_system_health(self) -> Dict:
        """
        Get a summary of system health based on log analysis.
        
        Returns:
            Dictionary containing system health metrics
        """
        if not self.log_history:
            return {"status": "no_data", "active_components": 0}
        
        recent_logs = self.log_history[-50:]  # Last 50 entries
        
        # Count log levels in recent activity
        level_counts = {}
        for entry in recent_logs:
            level = entry["level"]
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Determine overall health status
        error_count = level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0)
        warning_count = level_counts.get("WARNING", 0)
        
        if error_count > 5:
            status = "critical"
        elif error_count > 0 or warning_count > 10:
            status = "degraded"
        elif level_counts.get("INFO", 0) > 0:
            status = "healthy"
        else:
            status = "quiet"
        
        return {
            "status": status,
            "active_components": len(self.active_components),
            "total_logs": len(self.log_history),
            "recent_activity": level_counts,
            "components": list(self.active_components)
        }
    
    def periodic_task(self):
        """
        Perform periodic logging maintenance tasks.
        
        This runs during each processing loop iteration.
        """
        # Every ~30 seconds (300 iterations of 0.1s each), log system status
        if hasattr(self, '_periodic_counter'):
            self._periodic_counter += 1
        else:
            self._periodic_counter = 0
        
        if self._periodic_counter % 300 == 0:  # Every 30 seconds
            health = self.get_system_health()
            self._add_log_entry(
                "DEBUG",
                f"System health check: {health['status']} - {health['active_components']} active components",
                self.agent_id
            )
    
    def export_logs(self, filename: str = None) -> str:
        """
        Export logs to a formatted string (could be saved to file).
        
        Args:
            filename: Optional filename for export context
            
        Returns:
            Formatted log export string
        """
        if not self.log_history:
            return "No logs available for export."
        
        lines = ["=== Project Synapse System Logs ===", ""]
        
        if filename:
            lines.append(f"Export Date: {datetime.now().isoformat()}")
            lines.append(f"Export File: {filename}")
            lines.append("")
        
        for entry in self.log_history:
            timestamp = entry["timestamp"][:19]  # Remove microseconds
            level = entry["level"]
            component = entry["component"]
            message = entry["message"]
            
            lines.append(f"[{timestamp}] [{level}] [{component}] {message}")
        
        return "\n".join(lines)
