"""
Orchestrator Agent

The project manager agent that coordinates all other agents in the research workflow.
Demonstrates A2A command and control patterns.
"""

from typing import Dict, List, Any
from .base_agent import BaseAgent, generate_task_id
from ..protocols.acp_schema import (
    ACPMessage, ACPMsgType, TaskAssignPayload, 
    StatusUpdatePayload, DataSubmitPayload, LogBroadcastPayload
)


class OrchestratorAgent(BaseAgent):
    """
    Central coordination agent that manages the research workflow.
    
    This agent demonstrates:
    - A2A command and control patterns
    - Task decomposition and assignment
    - Progress tracking across multiple agents
    - Result aggregation and synthesis coordination
    """
    
    def __init__(self, agent_id: str = "orchestrator", message_bus: Dict = None):
        """
        Initialize the Orchestrator Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            message_bus: Shared message bus for inter-agent communication
        """
        super().__init__(agent_id, message_bus)
        
        # Track ongoing tasks and their status
        self.active_tasks = {}
        self.completed_tasks = {}
        self.agent_status = {}
        
        # Research workflow state
        self.current_research_query = None
        self.search_results = []
        self.extracted_content = []
        self.validated_facts = []
        self.final_report = None
        
        # Agent IDs for coordination
        self.search_agent_id = "search_agent"
        self.extraction_agent_id = "extraction_agent"
        self.fact_checker_agent_id = "fact_checker_agent"
        self.synthesis_agent_id = "synthesis_agent"
        self.file_save_agent_id = "file_save_agent"
        
        print(f"[{self.agent_id}] Orchestrator initialized and ready to coordinate research")
    
    def handle_message(self, message: ACPMessage):
        """
        Handle incoming messages from other agents and external requests.
        
        Args:
            message: ACP message to process
        """
        print(f"[{self.agent_id}] Received {message.msg_type.value} from {message.sender_id}")
        
        if message.msg_type == ACPMsgType.TASK_ASSIGN:
            self._handle_research_request(message)
        elif message.msg_type == ACPMsgType.STATUS_UPDATE:
            self._handle_status_update(message)
        elif message.msg_type == ACPMsgType.DATA_SUBMIT:
            self._handle_data_submission(message)
        else:
            print(f"[{self.agent_id}] Unhandled message type: {message.msg_type.value}")
    
    def _handle_research_request(self, message: ACPMessage):
        """
        Handle a new research request and initiate the workflow.
        
        Args:
            message: Task assignment message with research query
        """
        payload = TaskAssignPayload(**message.payload)
        
        if payload.task_type == "research_query":
            research_query = payload.task_data.get("query")
            self.current_research_query = research_query
            
            print(f"[{self.agent_id}] Starting research workflow for: '{research_query}'")
            
            # Broadcast research start
            self._broadcast_log("INFO", f"Research workflow initiated: {research_query}")
            
            # Step 1: Assign search task
            self._assign_search_task(research_query)
        else:
            print(f"[{self.agent_id}] Unknown research task type: {payload.task_type}")
    
    def _assign_search_task(self, query: str):
        """
        Assign web search task to the SearchAgent.
        
        Args:
            query: Research query to search for
        """
        task_id = generate_task_id()
        
        search_task = self.create_message(
            receiver_id=self.search_agent_id,
            msg_type=ACPMsgType.TASK_ASSIGN,
            payload=TaskAssignPayload(
                task_type="web_search",
                task_data={
                    "query": query,
                    "task_id": task_id,
                    "max_results": 5
                },
                priority=1
            ).model_dump()
        )
        
        self.active_tasks[task_id] = {
            "type": "web_search",
            "agent": self.search_agent_id,
            "status": "assigned",
            "query": query
        }
        
        self.send_message(search_task)
        print(f"[{self.agent_id}] Assigned search task {task_id} to SearchAgent")
    
    def _handle_status_update(self, message: ACPMessage):
        """
        Handle status updates from working agents.
        
        Args:
            message: Status update message
        """
        payload = StatusUpdatePayload(**message.payload)
        
        if payload.task_id in self.active_tasks:
            self.active_tasks[payload.task_id]["status"] = payload.status
            self.active_tasks[payload.task_id]["progress"] = payload.progress
        
        self.agent_status[message.sender_id] = {
            "last_status": payload.status,
            "progress": payload.progress,
            "task_id": payload.task_id
        }
        
        print(f"[{self.agent_id}] Status update from {message.sender_id}: {payload.status}")
    
    def _handle_data_submission(self, message: ACPMessage):
        """
        Handle data submissions from agents and coordinate next steps.
        
        Args:
            message: Data submission message
        """
        payload = DataSubmitPayload(**message.payload)
        
        print(f"[{self.agent_id}] Received {payload.data_type} from {message.sender_id}")
        
        if payload.data_type == "search_results":
            self._handle_search_results(payload, message.sender_id)
        elif payload.data_type == "extracted_content":
            self._handle_extracted_content(payload, message.sender_id)
        elif payload.data_type == "fact_check_result":
            self._handle_fact_check_result(payload, message.sender_id)
        elif payload.data_type == "synthesis_report":
            self._handle_synthesis_report(payload, message.sender_id)
        else:
            print(f"[{self.agent_id}] Unknown data type: {payload.data_type}")
    
    def _handle_search_results(self, payload: DataSubmitPayload, sender_id: str):
        """
        Process search results and assign extraction tasks.
        
        Args:
            payload: Data submission payload with search results
            sender_id: ID of the agent that sent the results
        """
        search_data = payload.data
        results = search_data.get("results", [])
        
        self.search_results.extend(results)
        print(f"[{self.agent_id}] Received {len(results)} search results")
        
        # Assign extraction tasks for each URL
        for i, result in enumerate(results[:3]):  # Limit to top 3 results
            self._assign_extraction_task(result["url"], f"search_result_{i}")
        
        self._broadcast_log("INFO", f"Assigned extraction tasks for {len(results[:3])} URLs")
    
    def _assign_extraction_task(self, url: str, source_desc: str):
        """
        Assign content extraction task to the ExtractionAgent.
        
        Args:
            url: URL to extract content from
            source_desc: Description of the source
        """
        task_id = generate_task_id()
        
        extraction_task = self.create_message(
            receiver_id=self.extraction_agent_id,
            msg_type=ACPMsgType.TASK_ASSIGN,
            payload=TaskAssignPayload(
                task_type="extract_content",
                task_data={
                    "url": url,
                    "source_description": source_desc,
                    "task_id": task_id
                },
                priority=2
            ).model_dump()
        )
        
        self.active_tasks[task_id] = {
            "type": "content_extraction",
            "agent": self.extraction_agent_id,
            "status": "assigned",
            "url": url
        }
        
        self.send_message(extraction_task)
        print(f"[{self.agent_id}] Assigned extraction task {task_id} for {url}")
    
    def _handle_extracted_content(self, payload: DataSubmitPayload, sender_id: str):
        """
        Process extracted content and potentially assign fact-checking.
        
        Args:
            payload: Data submission payload with extracted content
            sender_id: ID of the agent that sent the content
        """
        content_data = payload.data
        self.extracted_content.append(content_data)
        
        content_length = content_data.get("word_count", 0)
        print(f"[{self.agent_id}] Received extracted content ({content_length} words)")
        
        # If we have enough content, start synthesis
        if len(self.extracted_content) >= 2:  # Wait for at least 2 sources
            self._assign_synthesis_task()
    
    def _assign_synthesis_task(self):
        """Assign the final synthesis task to create the research report."""
        task_id = generate_task_id()
        
        synthesis_task = self.create_message(
            receiver_id=self.synthesis_agent_id,
            msg_type=ACPMsgType.TASK_ASSIGN,
            payload=TaskAssignPayload(
                task_type="synthesize_report",
                task_data={
                    "query": self.current_research_query,
                    "search_results": self.search_results,
                    "extracted_content": self.extracted_content,
                    "task_id": task_id
                },
                priority=1
            ).model_dump()
        )
        
        self.active_tasks[task_id] = {
            "type": "synthesis",
            "agent": self.synthesis_agent_id,
            "status": "assigned",
            "query": self.current_research_query
        }
        
        self.send_message(synthesis_task)
        print(f"[{self.agent_id}] Assigned synthesis task {task_id} to SynthesisAgent")
    
    def _handle_synthesis_report(self, payload: DataSubmitPayload, sender_id: str):
        """
        Handle the final synthesized report and save it.
        
        Args:
            payload: Data submission payload with the final report
            sender_id: ID of the agent that sent the report
        """
        report_data = payload.data
        self.final_report = report_data
        
        print(f"[{self.agent_id}] Received final research report")
        
        # Assign file saving task
        self._assign_file_save_task(report_data)
        
        self._broadcast_log("INFO", "Research workflow completed successfully")
    
    def _assign_file_save_task(self, report_data: Dict):
        """
        Assign task to save the final report to file.
        
        Args:
            report_data: The synthesized report data
        """
        task_id = generate_task_id()
        
        # Create filename based on query
        query_slug = self.current_research_query.lower().replace(" ", "_")[:30]
        filename = f"research_report_{query_slug}_{task_id}.md"
        
        save_task = self.create_message(
            receiver_id=self.file_save_agent_id,
            msg_type=ACPMsgType.TASK_ASSIGN,
            payload=TaskAssignPayload(
                task_type="save_report",
                task_data={
                    "filename": filename,
                    "content": report_data.get("report_content", ""),
                    "task_id": task_id
                },
                priority=1
            ).model_dump()
        )
        
        self.active_tasks[task_id] = {
            "type": "file_save",
            "agent": self.file_save_agent_id,
            "status": "assigned",
            "filename": filename
        }
        
        self.send_message(save_task)
        print(f"[{self.agent_id}] Assigned file save task {task_id}")
    
    def _broadcast_log(self, level: str, message: str):
        """
        Broadcast a log message to all listening agents.
        
        Args:
            level: Log level (INFO, DEBUG, WARNING, ERROR)
            message: Log message content
        """
        log_message = self.create_message(
            topic="logs",
            msg_type=ACPMsgType.LOG_BROADCAST,
            payload=LogBroadcastPayload(
                level=level,
                message=message,
                component=self.agent_id
            ).model_dump()
        )
        self.send_message(log_message)
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get the current status of the research workflow.
        
        Returns:
            Dictionary containing workflow status information
        """
        return {
            "current_query": self.current_research_query,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "search_results": len(self.search_results),
            "extracted_content": len(self.extracted_content),
            "final_report_ready": self.final_report is not None,
            "agent_status": self.agent_status
        }
