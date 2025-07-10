"""
Model Context Protocol (MCP) Schema Definitions

This module defines the Pydantic models for MCP tool parameters
and responses used in Project Synapse.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class SearchWebParams(BaseModel):
    """
    Parameters for the search_web MCP tool.
    
    This tool searches the web for information related to the query
    and returns a list of relevant URLs and snippets.
    """
    query: str = Field(..., description="Search query to find relevant information")


class BrowseAndExtractParams(BaseModel):
    """
    Parameters for the browse_and_extract MCP tool.
    
    This tool browses a URL and extracts the main text content.
    It demonstrates MCP Progress Notifications during the extraction process.
    """
    url: str = Field(..., description="URL to browse and extract content from")


class SaveFileParams(BaseModel):
    """
    Parameters for the save_file MCP tool.
    
    This tool saves content to a file with security restrictions.
    It demonstrates MCP Roots for secure file system access.
    """
    file_path: str = Field(..., description="Path where the file should be saved")
    content: str = Field(..., description="Content to write to the file")


class RephraseSentenceParams(BaseModel):
    """
    Parameters for the rephrase_sentence MCP tool.
    
    This tool rephrases a sentence to improve clarity or style.
    It demonstrates MCP Sampling for AI-assisted text generation.
    """
    sentence: str = Field(..., description="Sentence to be rephrased")


# Response Models

class SearchWebResponse(BaseModel):
    """Response structure for search_web tool."""
    results: List[Dict[str, str]] = Field(..., description="List of search results")
    query_processed: str = Field(..., description="Processed version of the query")


class BrowseAndExtractResponse(BaseModel):
    """Response structure for browse_and_extract tool."""
    url: str = Field(..., description="URL that was processed")
    title: Optional[str] = Field(None, description="Page title if available")
    content: str = Field(..., description="Extracted text content")
    word_count: int = Field(..., description="Number of words extracted")


class SaveFileResponse(BaseModel):
    """Response structure for save_file tool."""
    success: bool = Field(..., description="Whether the file was saved successfully")
    file_path: str = Field(..., description="Path where the file was saved")
    bytes_written: int = Field(..., description="Number of bytes written")


class RephraseSentenceResponse(BaseModel):
    """Response structure for rephrase_sentence tool."""
    original: str = Field(..., description="Original sentence")
    rephrased: str = Field(..., description="Rephrased version")
    improvement_type: str = Field(..., description="Type of improvement made")


# MCP Context and Progress Models

class MCPContext(BaseModel):
    """
    Simulated MCP context object for handling progress notifications
    and other MCP-specific functionality.
    """
    session_id: str = Field(..., description="Unique session identifier")
    progress_callbacks: List[Any] = Field(default_factory=list, description="Progress callback functions")
    
    def report_progress(self, message: str, percentage: Optional[float] = None):
        """
        Report progress during a long-running MCP operation.
        
        Args:
            message: Human-readable progress message
            percentage: Optional progress percentage (0-100)
        """
        progress_info = {
            "message": message,
            "percentage": percentage,
            "session_id": self.session_id
        }
        print(f"[MCP Progress] {message}" + (f" ({percentage}%)" if percentage else ""))
        
        # In a real implementation, this would call registered callbacks
        for callback in self.progress_callbacks:
            callback(progress_info)


class MCPError(Exception):
    """Base exception for MCP-related errors."""
    pass


class MCPSecurityError(MCPError):
    """Exception raised when MCP security constraints are violated."""
    pass


class MCPToolNotFoundError(MCPError):
    """Exception raised when a requested MCP tool is not available."""
    pass
