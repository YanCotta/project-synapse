"""
FastAPI Primary Tooling MCP Server

Provides web search and content extraction tools via HTTP endpoints.
Demonstrates MCP Progress Notifications through Server-Sent Events.
"""

import asyncio
import json
import time
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from ..protocols.mcp_schemas import (
    SearchWebParams, BrowseAndExtractParams,
    SearchWebResponse, BrowseAndExtractResponse
)


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: float


def create_primary_app() -> FastAPI:
    """Create and configure the Primary Tooling FastAPI application."""
    
    app = FastAPI(
        title="Primary Tooling MCP Server",
        description="Web search and content extraction tools with progress notifications",
        version="1.0.0"
    )

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint for container orchestration."""
        return HealthResponse(
            status="healthy",
            service="primary_tooling",
            timestamp=time.time()
        )

    @app.post("/tools/search_web", response_model=Dict[str, Any])
    async def search_web_endpoint(params: SearchWebParams):
        """
        Search the web for information related to the query.
        
        This endpoint provides the search_web MCP tool functionality
        via HTTP POST request.
        """
        print(f"[PrimaryToolingServer] HTTP: Searching web for: '{params.query}'")
        
        # Simulate search processing time
        await asyncio.sleep(0.5)
        
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
        
        print(f"[PrimaryToolingServer] HTTP: Found {len(mock_results)} results")
        return response.model_dump()

    @app.post("/tools/browse_and_extract")
    async def browse_and_extract_streaming(params: BrowseAndExtractParams):
        """
        Browse a URL and extract its main text content with streaming progress.
        
        This endpoint demonstrates MCP Progress Notifications by sending
        Server-Sent Events during the extraction process.
        """
        print(f"[PrimaryToolingServer] HTTP: Starting streaming extraction from: {params.url}")
        
        async def progress_generator():
            """Generate progress events and final result."""
            try:
                # Phase 1: Connect to URL
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "message": "Connecting to URL...",
                        "percentage": 10,
                        "phase": "connection"
                    })
                }
                await asyncio.sleep(1)
                
                # Phase 2: Download content
                yield {
                    "event": "progress", 
                    "data": json.dumps({
                        "message": "Downloading content...",
                        "percentage": 30,
                        "phase": "download"
                    })
                }
                await asyncio.sleep(1)
                
                # Phase 3: Parse HTML
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "message": "Parsing HTML structure...",
                        "percentage": 60,
                        "phase": "parsing"
                    })
                }
                await asyncio.sleep(1)
                
                # Phase 4: Extract text
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "message": "Extracting main content...",
                        "percentage": 80,
                        "phase": "extraction"
                    })
                }
                await asyncio.sleep(0.5)
                
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
                    """
                elif "post-quantum" in params.url:
                    mock_content = """
                    The National Institute of Standards and Technology (NIST) has been leading efforts 
                    to standardize post-quantum cryptographic algorithms. After years of evaluation, 
                    NIST has selected several algorithms for standardization including CRYSTALS-Kyber 
                    for key establishment and CRYSTALS-Dilithium for digital signatures.
                    """
                else:
                    mock_content = f"""
                    This is extracted content from {params.url}. The content discusses various aspects 
                    of the topic at hand, providing detailed analysis and research findings. 
                    
                    The document covers multiple perspectives and includes references to current academic 
                    work in the field. This extraction demonstrates the capability to process web content 
                    and extract meaningful text for further analysis and synthesis.
                    """
                
                word_count = len(mock_content.split())
                
                # Final progress update
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "message": "Extraction complete",
                        "percentage": 100,
                        "phase": "complete"
                    })
                }
                
                # Send final result
                response = BrowseAndExtractResponse(
                    url=params.url,
                    title=f"Research Article - {params.url.split('/')[-1].replace('-', ' ').title()}",
                    content=mock_content.strip(),
                    word_count=word_count
                )
                
                yield {
                    "event": "result",
                    "data": json.dumps(response.model_dump())
                }
                
                print(f"[PrimaryToolingServer] HTTP: Extracted {word_count} words from {params.url}")
                
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": str(e),
                        "message": f"Failed to extract content from {params.url}"
                    })
                }
        
        return EventSourceResponse(progress_generator())

    @app.get("/")
    async def root():
        """Root endpoint with server information."""
        return {
            "service": "Primary Tooling MCP Server",
            "version": "1.0.0",
            "tools": ["search_web", "browse_and_extract"],
            "endpoints": {
                "health": "/health",
                "search": "/tools/search_web",
                "extract": "/tools/browse_and_extract"
            }
        }

    return app


# For direct running (development)
if __name__ == "__main__":
    import uvicorn
    app = create_primary_app()
    uvicorn.run(app, host="0.0.0.0", port=8001)
