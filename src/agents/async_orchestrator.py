"""
Async Orchestrator Agent

Central coordination agent that manages the research workflow asynchronously.
Demonstrates A2A command and control patterns with async message handling.
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

from .async_base_agent import AsyncBaseAgent, generate_task_id
from ..protocols.acp_schema import (
    ACPMessage, ACPMsgType, TaskAssignPayload, 
    StatusUpdatePayload, DataSubmitPayload, LogBroadcastPayload
)

logger = logging.getLogger(__name__)


class AsyncOrchestratorAgent(AsyncBaseAgent):
    """
    Asynchronous orchestrator agent that coordinates research workflows.
    
    Responsibilities:
    - Task decomposition and assignment
    - Progress tracking across multiple agents
    - Result aggregation and synthesis coordination
    - Workflow state management
    """
    
    def __init__(self, agent_id: str, message_bus, mcp_servers: Dict[str, str]):
        """Initialize the async orchestrator agent."""
        super().__init__(agent_id, message_bus, mcp_servers)
        
        # Workflow state
        self.current_query: str = ""
        self.current_task_id: str = ""
        self.search_results: List[Dict] = []
        self.extracted_content: List[Dict] = []
        self.synthesis_report: Dict = {}
        self.workflow_start_time: datetime = None
        
        # Agent status tracking
        self.agent_status: Dict[str, str] = {}
        
        logger.info(f"[{self.agent_id}] Async Orchestrator initialized")
    
    async def handle_message(self, message: ACPMessage):
        """Handle incoming ACP messages asynchronously."""
        try:
            if message.msg_type == ACPMsgType.STATUS_UPDATE:
                await self._handle_status_update(message)
            elif message.msg_type == ACPMsgType.DATA_SUBMIT:
                await self._handle_data_submission(message)
            else:
                logger.warning(f"[{self.agent_id}] Unhandled message type: {message.msg_type.value}")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error handling message: {e}")
    
    async def start_research(self, query: str):
        """
        Initiate a research workflow for the given query.
        
        Args:
            query: Research question to investigate
        """
        logger.info(f"[{self.agent_id}] Starting research workflow: '{query}'")
        
        # Initialize workflow state
        self.current_query = query
        self.current_task_id = generate_task_id()
        self.workflow_start_time = datetime.now()
        
        # Reset collections
        self.search_results.clear()
        self.extracted_content.clear()
        self.synthesis_report.clear()
        
        # Broadcast workflow start
        await self._broadcast_log("INFO", f"Research workflow started: '{query}'")
        
        # Start with web search
        await self._assign_search_task(query)
    
    async def _assign_search_task(self, query: str):
        """Assign web search task to SearchAgent."""
        task_data = {
            "query": query,
            "task_id": self.current_task_id,
            "max_results": 5
        }
        
        search_message = self.create_message(
            receiver_id="search_agent",
            msg_type=ACPMsgType.TASK_ASSIGN,
            payload=TaskAssignPayload(
                task_type="web_search",
                task_data=task_data,
                priority=1
            ).model_dump()
        )
        
        await self.send_message(search_message)
        logger.info(f"[{self.agent_id}] Assigned search task for: '{query}'")
    
    async def _handle_status_update(self, message: ACPMessage):
        """Process status updates from other agents."""
        payload = StatusUpdatePayload(**message.payload)
        sender_id = message.sender_id
        
        # Update agent status tracking
        self.agent_status[sender_id] = payload.status
        
        logger.info(f"[{self.agent_id}] Status from {sender_id}: {payload.status}")
        
        # Handle specific status updates
        if "failed" in payload.status.lower():
            await self._handle_agent_failure(sender_id, payload.status)
    
    async def _handle_data_submission(self, message: ACPMessage):
        """Process data submissions from other agents."""
        payload = DataSubmitPayload(**message.payload)
        sender_id = message.sender_id
        
        logger.info(f"[{self.agent_id}] Received {payload.data_type} from {sender_id}")
        
        if payload.data_type == "search_results":
            await self._handle_search_results(payload, sender_id)
        elif payload.data_type == "extracted_content":
            await self._handle_extracted_content(payload, sender_id)
        elif payload.data_type == "synthesis_report":
            await self._handle_synthesis_report(payload, sender_id)
        else:
            logger.warning(f"[{self.agent_id}] Unknown data type: {payload.data_type}")
    
    async def _handle_search_results(self, payload: DataSubmitPayload, sender_id: str):
        """Process search results and assign extraction tasks."""
        search_data = payload.data
        results = search_data.get("results", [])
        
        self.search_results.extend(results)
        
        logger.info(f"[{self.agent_id}] Received {len(results)} search results")
        
        # Assign extraction tasks for top results
        extraction_tasks = []
        for i, result in enumerate(results[:3]):  # Extract from top 3 results
            url = result.get("url", "")
            if url:
                extraction_tasks.append(self._assign_extraction_task(url, f"source_{i+1}"))
        
        # Execute extraction tasks concurrently
        if extraction_tasks:
            await asyncio.gather(*extraction_tasks)
    
    async def _assign_extraction_task(self, url: str, source_desc: str):
        """Assign content extraction task to ExtractionAgent."""
        task_data = {
            "url": url,
            "task_id": self.current_task_id,
            "source_description": source_desc
        }
        
        extraction_message = self.create_message(
            receiver_id="extraction_agent",
            msg_type=ACPMsgType.TASK_ASSIGN,
            payload=TaskAssignPayload(
                task_type="extract_content",
                task_data=task_data,
                priority=2
            ).model_dump()
        )
        
        await self.send_message(extraction_message)
        logger.info(f"[{self.agent_id}] Assigned extraction task for: {url}")
    
    async def _handle_extracted_content(self, payload: DataSubmitPayload, sender_id: str):
        """Process extracted content and trigger synthesis when ready."""
        content_data = payload.data
        self.extracted_content.append(content_data)
        
        content_length = content_data.get("word_count", 0)
        logger.info(f"[{self.agent_id}] Received extracted content ({content_length} words)")
        
        # If we have enough content, start synthesis
        if len(self.extracted_content) >= 2:  # Wait for at least 2 sources
            await self._assign_synthesis_task()
    
    async def _assign_synthesis_task(self):
        """Assign synthesis task to create the research report."""
        task_data = {
            "query": self.current_query,
            "search_results": self.search_results,
            "extracted_content": self.extracted_content,
            "task_id": self.current_task_id
        }
        
        synthesis_message = self.create_message(
            receiver_id="synthesis_agent",
            msg_type=ACPMsgType.TASK_ASSIGN,
            payload=TaskAssignPayload(
                task_type="synthesize_research",
                task_data=task_data,
                priority=1
            ).model_dump()
        )
        
        await self.send_message(synthesis_message)
        logger.info(f"[{self.agent_id}] Assigned synthesis task")
    
    async def _handle_synthesis_report(self, payload: DataSubmitPayload, sender_id: str):
        """Process completed synthesis report and save to file."""
        report_data = payload.data
        self.synthesis_report = report_data
        
        word_count = report_data.get("word_count", 0)
        logger.info(f"[{self.agent_id}] Received synthesis report ({word_count} words)")
        
        # Assign file save task
        await self._assign_file_save_task(report_data)
    
    async def _assign_file_save_task(self, report_data: Dict):
        """Assign file save task to persist the final report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_report_{timestamp}.md"
        file_path = f"output/reports/{filename}"
        
        task_data = {
            "file_path": file_path,
            "content": report_data.get("report_content", ""),
            "task_id": self.current_task_id
        }
        
        save_message = self.create_message(
            receiver_id="file_save_agent",
            msg_type=ACPMsgType.TASK_ASSIGN,
            payload=TaskAssignPayload(
                task_type="save_file",
                task_data=task_data,
                priority=1
            ).model_dump()
        )
        
        await self.send_message(save_message)
        logger.info(f"[{self.agent_id}] Assigned file save task: {file_path}")
        
        # Broadcast workflow completion
        await self._broadcast_workflow_completion()
    
    async def _handle_agent_failure(self, agent_id: str, error_status: str):
        """Handle agent failures and implement recovery strategies."""
        logger.warning(f"[{self.agent_id}] Agent failure detected: {agent_id} - {error_status}")
        
        await self._broadcast_log("WARNING", f"Agent {agent_id} failed: {error_status}")
        
        # Implement basic retry logic
        if "search" in agent_id and len(self.search_results) == 0:
            logger.info(f"[{self.agent_id}] Retrying search task due to failure")
            await asyncio.sleep(5)  # Wait before retry
            await self._assign_search_task(self.current_query)
    
    async def _broadcast_log(self, level: str, message: str):
        """Broadcast log message to all subscribers."""
        log_message = self.create_message(
            topic="logs",
            msg_type=ACPMsgType.LOG_BROADCAST,
            payload=LogBroadcastPayload(
                level=level,
                message=message,
                component=self.agent_id
            ).model_dump()
        )
        
        await self.send_message(log_message)
    
    async def _broadcast_workflow_completion(self):
        """Broadcast workflow completion status."""
        if self.workflow_start_time:
            duration = datetime.now() - self.workflow_start_time
            duration_str = str(duration).split('.')[0]  # Remove microseconds
        else:
            duration_str = "unknown"
        
        completion_message = (
            f"Research workflow completed successfully! "
            f"Query: '{self.current_query}' | "
            f"Duration: {duration_str} | "
            f"Sources: {len(self.extracted_content)} | "
            f"Report words: {self.synthesis_report.get('word_count', 0)}"
        )
        
        await self._broadcast_log("INFO", completion_message)
        
        logger.info(f"[{self.agent_id}] 🎉 Workflow completed: {completion_message}")
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status and metrics."""
        return {
            "agent_id": self.agent_id,
            "current_query": self.current_query,
            "task_id": self.current_task_id,
            "workflow_start_time": self.workflow_start_time.isoformat() if self.workflow_start_time else None,
            "search_results_count": len(self.search_results),
            "extracted_content_count": len(self.extracted_content),
            "synthesis_complete": bool(self.synthesis_report),
            "agent_status": self.agent_status.copy(),
            "running": self.running
        }
