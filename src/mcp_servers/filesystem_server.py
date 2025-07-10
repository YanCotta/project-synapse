"""
Filesystem MCP Server

This server provides secure file operations with root restrictions.
It demonstrates MCP Roots security model for filesystem access control.
"""

import os
from pathlib import Path
from typing import List, Dict
from ..protocols.mcp_schemas import (
    SaveFileParams, SaveFileResponse,
    MCPSecurityError
)


class FileSystemServer:
    """
    MCP server providing secure file system operations.
    
    This server implements the MCP Roots security model, restricting
    file operations to predefined allowed directories.
    """
    
    def __init__(self, allowed_roots: List[str], server_id: str = "filesystem"):
        """
        Initialize the Filesystem Server with security constraints.
        
        Args:
            allowed_roots: List of directory paths where file operations are permitted
            server_id: Unique identifier for this server instance
        """
        self.server_id = server_id
        self.allowed_roots = [Path(root).resolve() for root in allowed_roots]
        self.available_tools = ["save_file"]
        
        # Ensure allowed roots exist
        for root in self.allowed_roots:
            root.mkdir(parents=True, exist_ok=True)
            
        print(f"[FileSystemServer] Initialized with roots: {[str(r) for r in self.allowed_roots]}")
    
    def _is_path_allowed(self, path_to_check: str) -> bool:
        """
        Verify that the given path is within one of the allowed roots.
        
        This is a critical security function that prevents directory traversal
        attacks and ensures file operations stay within approved boundaries.
        
        Args:
            path_to_check: The file path to validate
            
        Returns:
            True if the path is allowed, False otherwise
        """
        try:
            # Resolve the path to handle relative paths and symlinks
            target_path = Path(path_to_check).resolve()
            
            # Check if the path is within any of the allowed roots
            for allowed_root in self.allowed_roots:
                try:
                    # This will raise ValueError if target_path is not relative to allowed_root
                    target_path.relative_to(allowed_root)
                    return True
                except ValueError:
                    continue
            
            return False
            
        except (OSError, ValueError) as e:
            # Path resolution failed - definitely not allowed
            print(f"[FileSystemServer] Path validation error for '{path_to_check}': {e}")
            return False
    
    def save_file(self, params: SaveFileParams) -> Dict:
        """
        Save content to a file with security validation.
        
        This method demonstrates MCP Roots by validating that the target
        path is within the allowed directory structure before performing
        any file operations.
        
        Args:
            params: Parameters containing file path and content
            
        Returns:
            Dictionary containing operation result
            
        Raises:
            MCPSecurityError: If the path is outside allowed roots
        """
        print(f"[FileSystemServer] Attempting to save file: {params.file_path}")
        
        # Critical security check using MCP Roots model
        if not self._is_path_allowed(params.file_path):
            error_msg = (
                f"Access denied: '{params.file_path}' is outside allowed roots. "
                f"Allowed roots: {[str(r) for r in self.allowed_roots]}"
            )
            print(f"[FileSystemServer] SECURITY VIOLATION: {error_msg}")
            raise MCPSecurityError(error_msg)
        
        try:
            # Resolve the full path
            target_path = Path(params.file_path).resolve()
            
            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(params.content)
            
            # Get file size for response
            file_size = target_path.stat().st_size
            
            response = SaveFileResponse(
                success=True,
                file_path=str(target_path),
                bytes_written=file_size
            )
            
            print(f"[FileSystemServer] Successfully saved {file_size} bytes to {target_path}")
            return response.model_dump()
            
        except IOError as e:
            error_msg = f"Failed to save file '{params.file_path}': {e}"
            print(f"[FileSystemServer] ERROR: {error_msg}")
            
            response = SaveFileResponse(
                success=False,
                file_path=params.file_path,
                bytes_written=0
            )
            return response.model_dump()
    
    def list_allowed_roots(self) -> List[str]:
        """
        Return the list of allowed root directories.
        
        This is useful for clients to understand the security boundaries.
        """
        return [str(root) for root in self.allowed_roots]
    
    def validate_path(self, path: str) -> Dict[str, bool]:
        """
        Validate a path without performing any operations.
        
        Args:
            path: Path to validate
            
        Returns:
            Dictionary with validation result
        """
        is_allowed = self._is_path_allowed(path)
        return {
            "path": path,
            "is_allowed": is_allowed,
            "resolved_path": str(Path(path).resolve()) if is_allowed else None
        }
    
    def get_available_tools(self) -> List[str]:
        """Return a list of tools available on this server."""
        return self.available_tools.copy()
    
    def call_tool(self, tool_name: str, params: Dict) -> Dict:
        """
        Generic tool calling interface.
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool is not available
        """
        if tool_name == "save_file":
            save_params = SaveFileParams(**params)
            return self.save_file(save_params)
        else:
            raise ValueError(f"Tool '{tool_name}' not available on {self.server_id}")


class UserInteractionServer:
    """
    Simulated client-side MCP server for user interactions.
    
    This server demonstrates MCP Sampling by providing AI-assisted
    text rephrasing capabilities.
    """
    
    def __init__(self, server_id: str = "user_interaction"):
        """Initialize the User Interaction Server."""
        self.server_id = server_id
        self.available_tools = ["rephrase_sentence"]
    
    def rephrase_sentence(self, params: Dict) -> Dict:
        """
        Rephrase a sentence to improve clarity or style.
        
        This simulates MCP Sampling where the client requests AI assistance
        for text generation tasks.
        
        Args:
            params: Parameters containing the sentence to rephrase
            
        Returns:
            Dictionary containing the rephrased sentence
        """
        from ..protocols.mcp_schemas import RephraseSentenceParams, RephraseSentenceResponse
        
        rephrase_params = RephraseSentenceParams(**params)
        original = rephrase_params.sentence
        
        print(f"[UserInteractionServer] Rephrasing: '{original}'")
        
        # Simple rephrasing logic (in real implementation, this would use AI)
        rephrased = self._improve_sentence(original)
        improvement_type = self._detect_improvement_type(original, rephrased)
        
        response = RephraseSentenceResponse(
            original=original,
            rephrased=rephrased,
            improvement_type=improvement_type
        )
        
        print(f"[UserInteractionServer] Rephrased to: '{rephrased}'")
        return response.model_dump()
    
    def _improve_sentence(self, sentence: str) -> str:
        """Apply simple improvements to a sentence."""
        improved = sentence.strip()
        
        # Simple improvements for demonstration
        replacements = {
            "very good": "excellent",
            "very bad": "terrible", 
            "a lot of": "numerous",
            "thing": "element",
            "stuff": "material",
            "get": "obtain",
            "make": "create",
            "big": "substantial",
            "small": "minimal"
        }
        
        for old, new in replacements.items():
            improved = improved.replace(old, new)
        
        # Ensure proper capitalization
        if improved and not improved[0].isupper():
            improved = improved[0].upper() + improved[1:]
        
        return improved
    
    def _detect_improvement_type(self, original: str, rephrased: str) -> str:
        """Detect what type of improvement was made."""
        if len(rephrased) > len(original):
            return "expansion"
        elif len(rephrased) < len(original):
            return "concision"
        elif original != rephrased:
            return "clarity"
        else:
            return "no_change"
    
    def get_available_tools(self) -> List[str]:
        """Return a list of tools available on this server."""
        return self.available_tools.copy()
    
    def call_tool(self, tool_name: str, params: Dict) -> Dict:
        """
        Generic tool calling interface.
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool is not available
        """
        if tool_name == "rephrase_sentence":
            return self.rephrase_sentence(params)
        else:
            raise ValueError(f"Tool '{tool_name}' not available on {self.server_id}")
