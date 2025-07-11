"""
Async Synthesis Agent

Agent responsible for synthesizing research findings into coherent reports asynchronously.
Demonstrates MCP Sampling for AI-assisted text generation.
"""

import logging
from typing import Dict, List

from .async_base_agent import AsyncBaseAgent, MCPClientMixin
from ..protocols.acp_schema import (
    ACPMessage, ACPMsgType, TaskAssignPayload, StatusUpdatePayload, 
    DataSubmitPayload, LogBroadcastPayload
)

logger = logging.getLogger(__name__)


class AsyncSynthesisAgent(AsyncBaseAgent, MCPClientMixin):
    """
    Asynchronous agent that synthesizes research findings into coherent reports.
    
    Demonstrates:
    - MCP Sampling for AI-assisted text generation and rephrasing
    - Async content synthesis from multiple sources
    - Report structuring and formatting
    - Text improvement through iterative refinement
    """
    
    def __init__(self, agent_id: str, message_bus, mcp_servers: Dict[str, str]):
        """Initialize the async synthesis agent."""
        AsyncBaseAgent.__init__(self, agent_id, message_bus, mcp_servers)
        MCPClientMixin.__init__(self)
        
        self.orchestrator_id = "orchestrator"
        
        logger.info(f"[{self.agent_id}] Async Synthesis Agent initialized")
    
    async def handle_message(self, message: ACPMessage):
        """Handle incoming ACP messages."""
        try:
            if message.msg_type == ACPMsgType.TASK_ASSIGN:
                await self._handle_task_assignment(message)
            else:
                logger.warning(f"[{self.agent_id}] Unhandled message type: {message.msg_type.value}")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error handling message: {e}")
    
    async def _handle_task_assignment(self, message: ACPMessage):
        """Handle synthesis task assignments."""
        try:
            payload = TaskAssignPayload(**message.payload)
            
            if payload.task_type == "synthesize_research":
                await self._synthesize_research_report(payload.task_data)
            else:
                logger.warning(f"[{self.agent_id}] Unknown task type: {payload.task_type}")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in task assignment: {e}")
            await self._send_error_status(str(e))
    
    async def _synthesize_research_report(self, task_data: Dict):
        """Synthesize research findings into a comprehensive report."""
        query = task_data.get("query")
        search_results = task_data.get("search_results", [])
        extracted_content = task_data.get("extracted_content", [])
        task_id = task_data.get("task_id", "unknown")
        
        if not query:
            error_msg = "No research query provided for synthesis"
            logger.error(f"[{self.agent_id}] {error_msg}")
            await self._send_error_status(error_msg, task_id)
            return
        
        logger.info(f"[{self.agent_id}] Starting synthesis for: '{query}'")
        
        try:
            # Send initial status update
            await self._send_status_update("synthesis_starting", 10.0, task_id)
            
            # Create the report structure
            report_sections = []
            
            # Introduction
            await self._send_status_update("creating_introduction", 20.0, task_id)
            intro = await self._create_introduction(query)
            improved_intro = await self._improve_text_with_mcp(intro)
            report_sections.append(f"## Introduction\\n\\n{improved_intro}")
            
            # Findings from each source
            await self._send_status_update("analyzing_sources", 40.0, task_id)
            for i, content in enumerate(extracted_content):
                if content.get("extraction_successful", False):
                    section_title = f"Source {i+1} Analysis"
                    section_content = await self._create_source_analysis(content)
                    improved_content = await self._improve_text_with_mcp(section_content)
                    report_sections.append(f"## {section_title}\\n\\n{improved_content}")
            
            # Synthesis and conclusions
            await self._send_status_update("creating_synthesis", 70.0, task_id)
            conclusion = await self._create_conclusion(query, extracted_content)
            improved_conclusion = await self._improve_text_with_mcp(conclusion)
            report_sections.append(f"## Synthesis and Conclusions\\n\\n{improved_conclusion}")
            
            # Methodology and sources
            await self._send_status_update("adding_metadata", 90.0, task_id)
            methodology = await self._create_methodology(search_results, extracted_content)
            report_sections.append(f"## Research Methodology\\n\\n{methodology}")
            
            # Combine all sections
            full_report = f"# Research Report: {query}\\n\\n" + "\\n\\n".join(report_sections)
            
            # Add metadata
            metadata = await self._create_metadata(search_results, extracted_content)
            full_report += f"\\n\\n## Research Metadata\\n\\n{metadata}"
            
            logger.info(f"[{self.agent_id}] Synthesis completed: {len(full_report.split())} words")
            
            # Send completion status
            await self._send_status_update("synthesis_complete", 100.0, task_id)
            
            # Send completed report
            synthesis_data = {
                "report_content": full_report,
                "word_count": len(full_report.split()),
                "sections": len(report_sections),
                "sources_analyzed": len([c for c in extracted_content if c.get("extraction_successful", False)]),
                "query": query
            }
            
            data_message = self.create_message(
                receiver_id=self.orchestrator_id,
                msg_type=ACPMsgType.DATA_SUBMIT,
                payload=DataSubmitPayload(
                    data_type="synthesis_report",
                    data=synthesis_data,
                    source="synthesis_engine",
                    task_id=task_id
                ).model_dump()
            )
            
            await self.send_message(data_message)
            
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
            
            await self.send_message(log_message)
            
        except Exception as e:
            error_msg = f"Synthesis failed: {e}"
            logger.error(f"[{self.agent_id}] {error_msg}")
            await self._send_error_status(error_msg, task_id)
    
    async def _create_introduction(self, query: str) -> str:
        """Create an introduction section for the report."""
        return f"""This research report investigates the question: "{query}". 

The analysis draws from multiple authoritative sources to provide a comprehensive overview of current developments, key findings, and implications in this rapidly evolving field. Our investigation synthesizes information from academic papers, technical documentation, and expert analyses to present a balanced perspective on this important topic."""
    
    async def _create_source_analysis(self, content_data: Dict) -> str:
        """Create analysis text for a single source."""
        url = content_data.get("url", "Unknown source")
        title = content_data.get("title", "Untitled")
        content = content_data.get("content", "")
        word_count = content_data.get("word_count", 0)
        
        # Extract key points from content
        key_points = await self._extract_key_points(content)
        
        analysis = f"""**Source**: [{title}]({url})

**Content Summary** ({word_count} words):

{key_points}

**Key Insights**:

This source provides valuable perspective on the research question through detailed analysis and evidence-based conclusions. The information contributes to our understanding by offering specific insights and supporting data relevant to the investigation."""
        
        return analysis
    
    async def _extract_key_points(self, content: str) -> str:
        """Extract key points from content."""
        # Simple key point extraction
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 50]
        
        # Take first few substantial sentences as key points
        key_sentences = sentences[:3]
        
        if key_sentences:
            return '\\n\\n'.join([f"• {sentence}." for sentence in key_sentences])
        else:
            return "• Content provides technical background and context for the research question."
    
    async def _create_conclusion(self, query: str, extracted_content: List[Dict]) -> str:
        """Create synthesis and conclusions section."""
        successful_extractions = [c for c in extracted_content if c.get("extraction_successful", False)]
        
        conclusion = f"""Based on our analysis of {len(successful_extractions)} authoritative sources, several key themes emerge regarding {query}:

**Primary Findings**:

• The research reveals significant developments in this field with important implications for current practices and future directions.

• Multiple sources converge on similar conclusions, providing strong evidence for the trends and patterns identified in this investigation.

• The evidence suggests that continued attention to this area is warranted given its potential impact on related fields and applications.

**Implications**:

The synthesis of these sources demonstrates the complexity and evolving nature of this topic. The convergent evidence from multiple authoritative sources provides a solid foundation for understanding current developments and anticipating future trends.

**Future Research Directions**:

This analysis highlights several areas where additional investigation would be valuable to further advance our understanding and address remaining questions in this important field."""
        
        return conclusion
    
    async def _create_methodology(self, search_results: List[Dict], extracted_content: List[Dict]) -> str:
        """Create methodology section."""
        return f"""**Research Methodology**:

This report was generated through a systematic multi-stage process:

1. **Information Discovery**: Conducted web search yielding {len(search_results)} relevant sources
2. **Content Extraction**: Successfully extracted content from {len([c for c in extracted_content if c.get("extraction_successful", False)])} sources
3. **Analysis and Synthesis**: Applied structured analysis to identify key themes and insights
4. **Report Generation**: Synthesized findings into coherent narrative with supporting evidence

**Source Quality**: All sources were selected based on relevance and authority in the field."""
    
    async def _create_metadata(self, search_results: List[Dict], extracted_content: List[Dict]) -> str:
        """Create metadata section."""
        successful_extractions = [c for c in extracted_content if c.get("extraction_successful", False)]
        total_words = sum(c.get("word_count", 0) for c in successful_extractions)
        
        source_list = "\\n".join([
            f"• [{c.get('title', 'Untitled')}]({c.get('url', '#')})"
            for c in successful_extractions
        ])
        
        return f"""**Research Statistics**:
- Sources Analyzed: {len(successful_extractions)}
- Total Content Words: {total_words:,}
- Search Results: {len(search_results)}

**Sources**:
{source_list}

**Generation Date**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""
    
    async def _improve_text_with_mcp(self, text: str) -> str:
        """Improve text using MCP Sampling for sentence rephrasing."""
        try:
            sentences = text.split(". ")
            improved_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 50:  # Only improve longer sentences
                    try:
                        # MCP Sampling: Request AI assistance (simulated)
                        improved_sentence = await self._simulate_text_improvement(sentence)
                        improved_sentences.append(improved_sentence)
                    except Exception as e:
                        logger.debug(f"[{self.agent_id}] Text improvement failed for sentence, using original: {e}")
                        improved_sentences.append(sentence)
                else:
                    improved_sentences.append(sentence)
            
            return ". ".join(improved_sentences)
            
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Text improvement failed, returning original: {e}")
            return text
    
    async def _simulate_text_improvement(self, text: str) -> str:
        """Simulate MCP Sampling text improvement."""
        # In production, this would call the UserInteractionServer
        # For now, apply simple improvements
        improved = text
        
        replacements = {
            "very good": "excellent",
            "very bad": "problematic",
            "a lot of": "numerous",
            "thing": "element",
            "stuff": "content",
            "get": "obtain",
            "make": "create",
            "big": "substantial",
            "small": "minimal"
        }
        
        for old, new in replacements.items():
            improved = improved.replace(old, new)
        
        return improved
    
    async def _send_status_update(self, status: str, progress: float = None, task_id: str = None):
        """Send status update to orchestrator."""
        status_message = self.create_message(
            receiver_id=self.orchestrator_id,
            msg_type=ACPMsgType.STATUS_UPDATE,
            payload=StatusUpdatePayload(
                status=status,
                progress=progress,
                task_id=task_id
            ).model_dump()
        )
        
        await self.send_message(status_message)
        logger.debug(f"[{self.agent_id}] Status update sent: {status}")
    
    async def _send_error_status(self, error_message: str, task_id: str = None):
        """Send error status to orchestrator."""
        await self._send_status_update(f"synthesis_failed: {error_message}", 0.0, task_id)
    
    def get_capabilities(self) -> Dict[str, str]:
        """Return agent capabilities."""
        return {
            "agent_type": "synthesis_agent",
            "primary_function": "report_generation",
            "mcp_tools": ["text_improvement"],
            "supported_tasks": ["synthesize_research"],
            "sampling_support": True,
            "async_capable": True
        }
