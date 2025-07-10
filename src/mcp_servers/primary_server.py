"""
Primary MCP Tooling Server

This server provides web-related tools including search and content extraction.
It demonstrates MCP Progress Notifications during long-running operations.
"""

import time
from typing import Dict, List
from ..protocols.mcp_schemas import (
    SearchWebParams, BrowseAndExtractParams,
    SearchWebResponse, BrowseAndExtractResponse,
    MCPContext
)


class PrimaryToolingServer:
    """
    MCP server providing web search and content extraction tools.
    
    This server simulates web operations and demonstrates MCP capabilities
    including progress notifications for long-running tasks.
    """
    
    def __init__(self, server_id: str = "primary_tooling"):
        """
        Initialize the Primary Tooling Server.
        
        Args:
            server_id: Unique identifier for this server instance
        """
        self.server_id = server_id
        self.available_tools = ["search_web", "browse_and_extract"]
    
    def search_web(self, params: SearchWebParams) -> Dict:
        """
        Search the web for information related to the query.
        
        This is a simulated implementation that returns mock search results.
        In a real implementation, this would interface with search APIs.
        
        Args:
            params: Search parameters containing the query
            
        Returns:
            Dictionary containing search results
        """
        print(f"[PrimaryToolingServer] Searching web for: '{params.query}'")
        
        # Simulate search processing time
        time.sleep(0.5)
        
        # Mock search results based on query content
        mock_results = []
        if "quantum" in params.query.lower():
            mock_results = [
                {
                    "title": "Quantum Computing and Cryptography: Current State",
                    "url": "https://example.com/quantum-crypto-current",
                    "snippet": "Overview of how quantum computing affects current cryptographic methods..."
                },
                {
                    "title": "Post-Quantum Cryptography Standards",
                    "url": "https://example.com/post-quantum-standards",
                    "snippet": "NIST's guidelines for quantum-resistant encryption algorithms..."
                },
                {
                    "title": "Timeline of Quantum Computing Development",
                    "url": "https://example.com/quantum-timeline",
                    "snippet": "Historical development and future projections for quantum computers..."
                }
            ]
        else:
            # Generic mock results for other queries
            mock_results = [
                {
                    "title": f"Research Article: {params.query}",
                    "url": f"https://example.com/research-{len(params.query)}",
                    "snippet": f"Comprehensive analysis of {params.query} and related topics..."
                },
                {
                    "title": f"Academic Paper on {params.query}",
                    "url": f"https://example.com/academic-{hash(params.query) % 1000}",
                    "snippet": f"Peer-reviewed research covering various aspects of {params.query}..."
                }
            ]
        
        response = SearchWebResponse(
            results=mock_results,
            query_processed=params.query.strip().lower()
        )
        
        print(f"[PrimaryToolingServer] Found {len(mock_results)} results")
        return response.model_dump()
    
    def browse_and_extract(self, params: BrowseAndExtractParams, mcp_context: MCPContext) -> Dict:
        """
        Browse a URL and extract its main text content.
        
        This method demonstrates MCP Progress Notifications by reporting
        progress during the extraction process.
        
        Args:
            params: Parameters containing the URL to extract from
            mcp_context: MCP context for progress reporting
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        print(f"[PrimaryToolingServer] Starting extraction from: {params.url}")
        
        # Phase 1: Connect to URL
        mcp_context.report_progress("Connecting to URL...", 10)
        time.sleep(1)
        
        # Phase 2: Download content
        mcp_context.report_progress("Downloading content...", 30)
        time.sleep(1)
        
        # Phase 3: Parse HTML
        mcp_context.report_progress("Parsing HTML structure...", 60)
        time.sleep(1)
        
        # Phase 4: Extract text
        mcp_context.report_progress("Extracting main content...", 80)
        time.sleep(0.5)
        
        # Generate mock extracted content based on URL
        if "quantum-crypto" in params.url:
            mock_content = """
            Quantum computing represents a fundamental shift in computational paradigms that poses 
            significant challenges to current cryptographic systems. Traditional encryption methods, 
            particularly those based on RSA and elliptic curve cryptography, rely on the computational 
            difficulty of factoring large numbers or solving discrete logarithm problems.
            
            Quantum computers, utilizing Shor's algorithm, can efficiently solve these problems, 
            potentially rendering current public key cryptography obsolete. This has led to urgent 
            research into post-quantum cryptography - encryption methods that remain secure even 
            against quantum attacks.
            
            Current quantum computers are still in early stages, with limited qubit counts and 
            high error rates. However, projections suggest that cryptographically relevant quantum 
            computers could emerge within the next 10-20 years, necessitating proactive measures 
            in cryptographic infrastructure.
            """
        elif "post-quantum" in params.url:
            mock_content = """
            The National Institute of Standards and Technology (NIST) has been leading efforts 
            to standardize post-quantum cryptographic algorithms. After years of evaluation, 
            NIST has selected several algorithms for standardization:
            
            1. CRYSTALS-Kyber for key establishment
            2. CRYSTALS-Dilithium for digital signatures  
            3. FALCON for digital signatures (alternative)
            4. SPHINCS+ for digital signatures (stateless)
            
            These algorithms are based on mathematical problems believed to be hard even for 
            quantum computers, including lattice-based problems, hash-based signatures, and 
            code-based cryptography. Organizations are encouraged to begin transitioning to 
            these quantum-resistant algorithms to ensure long-term security.
            """
        else:
            mock_content = f"""
            This is extracted content from {params.url}. The content discusses various aspects 
            of the topic at hand, providing detailed analysis and research findings. 
            
            The document covers multiple perspectives and includes references to current academic 
            work in the field. Key points include methodological approaches, empirical findings, 
            and implications for future research directions.
            
            This extraction demonstrates the capability to process web content and extract 
            meaningful text for further analysis and synthesis.
            """
        
        # Final progress update
        mcp_context.report_progress("Extraction complete", 100)
        
        word_count = len(mock_content.split())
        
        response = BrowseAndExtractResponse(
            url=params.url,
            title=f"Research Article - {params.url.split('/')[-1].replace('-', ' ').title()}",
            content=mock_content.strip(),
            word_count=word_count
        )
        
        print(f"[PrimaryToolingServer] Extracted {word_count} words from {params.url}")
        return response.model_dump()
    
    def get_available_tools(self) -> List[str]:
        """Return a list of tools available on this server."""
        return self.available_tools.copy()
    
    def call_tool(self, tool_name: str, params: Dict, mcp_context: MCPContext = None) -> Dict:
        """
        Generic tool calling interface.
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool
            mcp_context: Optional MCP context for progress reporting
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool is not available
        """
        if tool_name == "search_web":
            search_params = SearchWebParams(**params)
            return self.search_web(search_params)
        elif tool_name == "browse_and_extract":
            extract_params = BrowseAndExtractParams(**params)
            if mcp_context is None:
                mcp_context = MCPContext(session_id="default")
            return self.browse_and_extract(extract_params, mcp_context)
        else:
            raise ValueError(f"Tool '{tool_name}' not available on {self.server_id}")
