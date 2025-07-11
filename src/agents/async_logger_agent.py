"""
Async Logger Agent

Central logging and monitoring agent using pub/sub pattern.
Demonstrates async message bus topic subscription.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

from .async_base_agent import AsyncBaseAgent
from ..protocols.acp_schema import (
    ACPMessage, ACPMsgType, TaskAssignPayload, StatusUpdatePayload,
    LogBroadcastPayload, DataSubmitPayload
)

logger = logging.getLogger(__name__)


class AsyncLoggerAgent(AsyncBaseAgent):
    """
    Asynchronous agent that handles system-wide logging and monitoring.
    
    Demonstrates:
    - Pub/sub pattern with topic subscription
    - Async message bus monitoring
    - Log aggregation and filtering
    - System health monitoring
    """
    
    def __init__(self, agent_id: str, message_bus, mcp_servers: Dict[str, str] = None):
        """Initialize the async logger agent."""
        super().__init__(agent_id, message_bus, mcp_servers or {})
        
        self.orchestrator_id = "orchestrator"
        self.log_buffer = deque(maxlen=1000)  # Keep last 1000 log entries
        self.agent_status = {}  # Track agent statuses
        self.log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.filter_level = "INFO"  # Default filter level
        
        # Statistics
        self.message_count = 0
        self.log_count_by_level = {level: 0 for level in self.log_levels}
        self.agent_activity = {}
        
        logger.info(f"[{self.agent_id}] Async Logger Agent initialized")
    
    async def handle_message(self, message: ACPMessage):
        """Handle incoming ACP messages - primarily log broadcasts."""
        try:
            self.message_count += 1
            
            if message.msg_type == ACPMsgType.LOG_BROADCAST:
                await self._handle_log_broadcast(message)
            elif message.msg_type == ACPMsgType.STATUS_UPDATE:
                await self._handle_status_update(message)
            elif message.msg_type == ACPMsgType.TASK_ASSIGN:
                await self._handle_task_assignment(message)
            else:
                # Log all other message types for monitoring
                await self._log_message_activity(message)
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error handling message: {e}")
    
    async def _handle_log_broadcast(self, message: ACPMessage):
        """Handle log broadcast messages."""
        try:
            payload = LogBroadcastPayload(**message.payload)
            
            # Create log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": payload.level,
                "message": payload.message,
                "component": payload.component,
                "correlation_id": payload.correlation_id,
                "sender_id": message.sender_id
            }
            
            # Add to buffer
            self.log_buffer.append(log_entry)
            
            # Update statistics
            if payload.level in self.log_count_by_level:
                self.log_count_by_level[payload.level] += 1
            
            # Update agent activity
            if payload.component:
                if payload.component not in self.agent_activity:
                    self.agent_activity[payload.component] = {
                        "first_seen": log_entry["timestamp"],
                        "last_activity": log_entry["timestamp"],
                        "message_count": 0,
                        "error_count": 0
                    }
                
                self.agent_activity[payload.component]["last_activity"] = log_entry["timestamp"]
                self.agent_activity[payload.component]["message_count"] += 1
                
                if payload.level in ["ERROR", "CRITICAL"]:
                    self.agent_activity[payload.component]["error_count"] += 1
            
            # Filter and log based on level
            if self._should_log_level(payload.level):
                log_method = getattr(logger, payload.level.lower(), logger.info)
                log_method(f"[{payload.component}] {payload.message}")
            
            # Check for error patterns that need attention
            await self._analyze_log_patterns(log_entry)
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error processing log broadcast: {e}")
    
    async def _handle_status_update(self, message: ACPMessage):
        """Handle status update messages for monitoring."""
        try:
            payload = StatusUpdatePayload(**message.payload)
            
            # Update agent status tracking
            sender_id = message.sender_id
            self.agent_status[sender_id] = {
                "status": payload.status,
                "progress": payload.progress,
                "task_id": payload.task_id,
                "last_update": datetime.utcnow().isoformat()
            }
            
            # Log status changes
            status_msg = f"Status update from {sender_id}: {payload.status}"
            if payload.progress is not None:
                status_msg += f" ({payload.progress:.1f}%)"
            
            logger.debug(f"[{self.agent_id}] {status_msg}")
            
            # Create log entry for status monitoring
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": status_msg,
                "component": "logger_agent",
                "correlation_id": None,
                "sender_id": self.agent_id,
                "event_type": "status_update",
                "agent_id": sender_id,
                "task_id": payload.task_id
            }
            
            self.log_buffer.append(log_entry)
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error processing status update: {e}")
    
    async def _handle_task_assignment(self, message: ACPMessage):
        """Handle task assignments for logger operations."""
        try:
            payload = TaskAssignPayload(**message.payload)
            
            if payload.task_type == "generate_report":
                await self._generate_log_report(payload.task_data)
            elif payload.task_type == "set_log_level":
                await self._set_log_level(payload.task_data)
            elif payload.task_type == "get_agent_status":
                await self._report_agent_status(payload.task_data)
            else:
                logger.warning(f"[{self.agent_id}] Unknown task type: {payload.task_type}")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in task assignment: {e}")
    
    async def _log_message_activity(self, message: ACPMessage):
        """Log general message activity for monitoring."""
        activity_msg = f"Message activity: {message.msg_type.value} from {message.sender_id}"
        if message.receiver_id:
            activity_msg += f" to {message.receiver_id}"
        elif message.topic:
            activity_msg += f" on topic {message.topic}"
        
        logger.debug(f"[{self.agent_id}] {activity_msg}")
    
    async def _analyze_log_patterns(self, log_entry: Dict):
        """Analyze log patterns for alerts and notifications."""
        try:
            # Check for error spikes
            if log_entry["level"] in ["ERROR", "CRITICAL"]:
                recent_errors = [
                    entry for entry in list(self.log_buffer)[-10:]
                    if entry["level"] in ["ERROR", "CRITICAL"]
                ]
                
                if len(recent_errors) >= 3:
                    alert_msg = f"High error rate detected: {len(recent_errors)} errors in last 10 messages"
                    logger.warning(f"[{self.agent_id}] ALERT: {alert_msg}")
                    
                    # Send alert to orchestrator
                    alert_data = {
                        "alert_type": "high_error_rate",
                        "recent_errors": recent_errors,
                        "error_count": len(recent_errors),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    alert_message = self.create_message(
                        receiver_id=self.orchestrator_id,
                        msg_type=ACPMsgType.DATA_SUBMIT,
                        payload=DataSubmitPayload(
                            data_type="system_alert",
                            data=alert_data,
                            source="logger_agent"
                        ).model_dump()
                    )
                    
                    await self.send_message(alert_message)
            
            # Check for agent silence (no activity for extended period)
            await self._check_agent_health()
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in log pattern analysis: {e}")
    
    async def _check_agent_health(self):
        """Check for agents that haven't been active recently."""
        try:
            current_time = datetime.utcnow()
            silence_threshold = 300  # 5 minutes in seconds
            
            for agent_id, activity in self.agent_activity.items():
                last_activity = datetime.fromisoformat(activity["last_activity"])
                silence_duration = (current_time - last_activity).total_seconds()
                
                if silence_duration > silence_threshold:
                    warning_msg = f"Agent {agent_id} silent for {silence_duration:.0f} seconds"
                    logger.warning(f"[{self.agent_id}] HEALTH CHECK: {warning_msg}")
                    
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in agent health check: {e}")
    
    async def _generate_log_report(self, task_data: Dict):
        """Generate comprehensive log report."""
        try:
            report_type = task_data.get("report_type", "summary")
            
            if report_type == "summary":
                report = await self._generate_summary_report()
            elif report_type == "detailed":
                report = await self._generate_detailed_report()
            elif report_type == "agent_activity":
                report = await self._generate_agent_activity_report()
            else:
                report = {"error": f"Unknown report type: {report_type}"}
            
            # Send report to orchestrator
            report_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.DATA_SUBMIT,
                payload=DataSubmitPayload(
                    data_type="log_report",
                    data=report,
                    source="logger_agent"
                ).model_dump()
            )
            
            await self.send_message(report_message)
            logger.info(f"[{self.agent_id}] Log report generated: {report_type}")
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error generating log report: {e}")
    
    async def _generate_summary_report(self) -> Dict:
        """Generate summary log report."""
        return {
            "report_type": "summary",
            "timestamp": datetime.utcnow().isoformat(),
            "total_messages": self.message_count,
            "total_logs": len(self.log_buffer),
            "log_counts_by_level": self.log_count_by_level,
            "active_agents": len(self.agent_activity),
            "agents_with_errors": len([
                agent for agent, activity in self.agent_activity.items()
                if activity["error_count"] > 0
            ])
        }
    
    async def _generate_detailed_report(self) -> Dict:
        """Generate detailed log report."""
        recent_logs = list(self.log_buffer)[-50:]  # Last 50 logs
        
        return {
            "report_type": "detailed",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": await self._generate_summary_report(),
            "recent_logs": recent_logs,
            "agent_status": self.agent_status
        }
    
    async def _generate_agent_activity_report(self) -> Dict:
        """Generate agent activity report."""
        return {
            "report_type": "agent_activity",
            "timestamp": datetime.utcnow().isoformat(),
            "agent_activity": self.agent_activity,
            "agent_status": self.agent_status
        }
    
    async def _set_log_level(self, task_data: Dict):
        """Set logging filter level."""
        try:
            new_level = task_data.get("level", "INFO").upper()
            
            if new_level in self.log_levels:
                old_level = self.filter_level
                self.filter_level = new_level
                
                logger.info(f"[{self.agent_id}] Log level changed from {old_level} to {new_level}")
            else:
                logger.error(f"[{self.agent_id}] Invalid log level: {new_level}")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error setting log level: {e}")
    
    async def _report_agent_status(self, task_data: Dict):
        """Report current agent status."""
        try:
            status_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_status": self.agent_status,
                "message_count": self.message_count,
                "log_buffer_size": len(self.log_buffer),
                "filter_level": self.filter_level
            }
            
            # Send status report
            status_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.DATA_SUBMIT,
                payload=DataSubmitPayload(
                    data_type="logger_status",
                    data=status_report,
                    source="logger_agent"
                ).model_dump()
            )
            
            await self.send_message(status_message)
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error reporting agent status: {e}")
    
    def _should_log_level(self, log_level: str) -> bool:
        """Check if log level should be processed based on filter."""
        try:
            current_index = self.log_levels.index(self.filter_level)
            log_index = self.log_levels.index(log_level)
            return log_index >= current_index
        except ValueError:
            return True  # Log unknown levels
    
    def get_capabilities(self) -> Dict[str, str]:
        """Return agent capabilities."""
        return {
            "agent_type": "logger_agent",
            "primary_function": "system_logging_monitoring",
            "subscription_topics": ["logs"],
            "supported_tasks": ["generate_report", "set_log_level", "get_agent_status"],
            "pub_sub_pattern": True,
            "async_capable": True,
            "monitoring_features": ["log_aggregation", "error_pattern_detection", "agent_health_monitoring"]
        }
