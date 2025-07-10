"""
Synthesis Agent

Agent responsible for synthesizing research findings into a coherent report.
Demonstrates MCP Sampling for AI-assisted text generation.
"""

from typing import Dict, List
from .base_agent import BaseAgent, MCPClientMixin
from ..protocols.acp_schema import ACPMessage, ACPMsgType, TaskAssignPayload, StatusUpdatePayload, DataSubmitPayload, LogBroadcastPayload


class SynthesisAgent(BaseAgent, MCPClientMixin):
    """
    Agent that synthesizes research findings into coherent reports.
    
    Demonstrates MCP Sampling for AI-assisted text generation and rephrasing.
    """
    
    def __init__(self, agent_id: str = "synthesis_agent", orchestrator_id: str = "orchestrator", 
                 message_bus: Dict = None):
        """Initialize the Synthesis Agent."""
        BaseAgent.__init__(self, agent_id, message_bus)
        MCPClientMixin.__init__(self)
        
        self.orchestrator_id = orchestrator_id
        
        print(f"[{self.agent_id}] Synthesis Agent initialized")
    
    def handle_message(self, message: ACPMessage):
        """Handle incoming messages."""
        if message.msg_type == ACPMsgType.TASK_ASSIGN:
            self._handle_task_assignment(message)
        else:
            print(f"[{self.agent_id}] Unhandled message type: {message.msg_type.value}")
    
    def _handle_task_assignment(self, message: ACPMessage):
        """Handle synthesis task assignments."""
        payload = TaskAssignPayload(**message.payload)
        
        if payload.task_type == "synthesize_report":
            self._synthesize_research_report(payload.task_data)
        else:
            print(f"[{self.agent_id}] Unknown task type: {payload.task_type}")
    
    def _synthesize_research_report(self, task_data: Dict):
        """Synthesize research findings into a comprehensive report."""
        query = task_data.get("query")
        search_results = task_data.get("search_results", [])
        extracted_content = task_data.get("extracted_content", [])
        task_id = task_data.get("task_id", "unknown")
        
        print(f"[{self.agent_id}] Synthesizing report for: '{query}'")
        
        # Send status update
        status_message = self.create_message(
            receiver_id=self.orchestrator_id,
            msg_type=ACPMsgType.STATUS_UPDATE,
            payload=StatusUpdatePayload(
                status="synthesizing_report",
                progress=10.0,
                task_id=task_id
            ).model_dump()
        )
        self.send_message(status_message)
        
        try:
            # Create the report structure
            report_sections = []
            
            # Introduction
            intro = self._create_introduction(query)
            improved_intro = self._improve_text_with_mcp(intro)
            report_sections.append(f"## Introduction\n\n{improved_intro}")
            
            # Findings from each source
            for i, content in enumerate(extracted_content):
                section_title = f"Source {i+1} Analysis"
                section_content = self._create_source_analysis(content)
                improved_content = self._improve_text_with_mcp(section_content)
                report_sections.append(f"## {section_title}\n\n{improved_content}")
            
            # Synthesis and conclusions
            conclusion = self._create_conclusion(query, extracted_content)
            improved_conclusion = self._improve_text_with_mcp(conclusion)
            report_sections.append(f"## Synthesis and Conclusions\n\n{improved_conclusion}")
            
            # Combine all sections
            full_report = f"# Research Report: {query}\n\n" + "\n\n".join(report_sections)
            
            # Add metadata
            metadata = self._create_metadata(search_results, extracted_content)
            full_report += f"\n\n## Research Metadata\n\n{metadata}"
            
            # Send completed report
            data_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.DATA_SUBMIT,
                payload=DataSubmitPayload(
                    data_type="synthesis_report",
                    data={
                        "report_content": full_report,
                        "word_count": len(full_report.split()),
                        "sections": len(report_sections),
                        "sources_analyzed": len(extracted_content)
                    },
                    source="synthesis_engine",
                    task_id=task_id
                ).model_dump()
            )
            self.send_message(data_message)
            
            # Broadcast completion log
            log_message = self.create_message(
                topic="logs",
                msg_type=ACPMsgType.LOG_BROADCAST,
                payload=LogBroadcastPayload(
                    level="INFO",
                    message=f"Research report synthesized: {len(full_report.split())} words, {len(extracted_content)} sources",
                    component=self.agent_id
                ).model_dump()
            )
            self.send_message(log_message)
            
        except Exception as e:
            print(f"[{self.agent_id}] Synthesis failed: {e}")
            
            # Send error status
            error_status = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.STATUS_UPDATE,
                payload=StatusUpdatePayload(
                    status=f"synthesis_failed: {e}",
                    progress=0.0,
                    task_id=task_id
                ).model_dump()
            )
            self.send_message(error_status)
    
    def _create_introduction(self, query: str) -> str:
        """Create an introduction section for the report."""
        return f"""This research report examines the topic: "{query}". The analysis draws from multiple sources to provide a comprehensive overview of current understanding, key developments, and implications in this area. This investigation aims to synthesize available information and present findings in a structured manner."""
    
    def _create_source_analysis(self, content_data: Dict) -> str:
        """Create analysis text for a single source."""
        url = content_data.get("url", "Unknown source")
        content = content_data.get("content", "")
        word_count = content_data.get("word_count", 0)
        
        # Extract key points (simplified for demo)
        sentences = content.split(". ")[:3]  # First 3 sentences
        key_points = ". ".join(sentences) + "."
        
        return f"""**Source:** {url}
**Content Length:** {word_count} words

**Key Findings:**
{key_points}

This source provides valuable insights into the research topic and contributes important perspective to our overall understanding."""
    
    def _create_conclusion(self, query: str, extracted_content: List[Dict]) -> str:
        """Create a conclusion section synthesizing all sources."""
        source_count = len(extracted_content)
        total_words = sum(content.get("word_count", 0) for content in extracted_content)
        
        return f"""Based on analysis of {source_count} sources totaling {total_words} words of content, several key themes emerge regarding {query}. The research reveals convergent findings across multiple sources, suggesting robust understanding in this area. Further investigation could explore specific aspects in greater depth, but the current analysis provides a solid foundation for understanding the topic."""
    
    def _create_metadata(self, search_results: List[Dict], extracted_content: List[Dict]) -> str:
        """Create metadata section with research details."""
        lines = [
            f"**Sources Searched:** {len(search_results)}",
            f"**Content Extracted:** {len(extracted_content)}",
            f"**Total Words Analyzed:** {sum(content.get('word_count', 0) for content in extracted_content)}",
            "",
            "**Source URLs:**"
        ]
        
        for i, content in enumerate(extracted_content, 1):
            url = content.get("url", "Unknown")
            lines.append(f"{i}. {url}")
        
        return "\n".join(lines)
    
    def _improve_text_with_mcp(self, text: str) -> str:
        """
        Improve text using MCP Sampling for sentence rephrasing.
        
        This demonstrates MCP Sampling where the agent requests AI assistance
        for text generation and improvement.
        """
        try:
            # Split into sentences and improve key ones
            sentences = text.split(". ")
            improved_sentences = []
            
            for sentence in sentences:
                if len(sentence.strip()) > 50:  # Only improve longer sentences
                    try:
                        # Call MCP sampling tool
                        rephrase_params = {"sentence": sentence.strip()}
                        result = self.call_mcp_tool(
                            server_name="user_interaction",
                            tool_name="rephrase_sentence",
                            params=rephrase_params
                        )
                        
                        improved_sentence = result.get("rephrased", sentence.strip())
                        improved_sentences.append(improved_sentence)
                        
                        print(f"[{self.agent_id}] Improved sentence using MCP Sampling")
                        
                    except Exception as e:
                        print(f"[{self.agent_id}] MCP rephrasing failed, using original: {e}")
                        improved_sentences.append(sentence.strip())
                else:
                    improved_sentences.append(sentence.strip())
            
            return ". ".join(improved_sentences)
            
        except Exception as e:
            print(f"[{self.agent_id}] Text improvement failed: {e}")
            return text  # Return original if improvement fails
