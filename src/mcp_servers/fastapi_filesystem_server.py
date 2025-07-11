"""
FastAPI Filesystem MCP Server

Provides secure file operations with MCP Roots security model via HTTP endpoints.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiofiles

from ..protocols.mcp_schemas import (
    SaveFileParams, SaveFileResponse, MCPSecurityError
)


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: float
    allowed_roots: List[str]


class PathValidationRequest(BaseModel):
    path: str


class PathValidationResponse(BaseModel):
    path: str
    is_allowed: bool
    resolved_path: str = None


def create_filesystem_app() -> FastAPI:
    """Create and configure the Filesystem FastAPI application."""
    
    # Initialize allowed roots from environment
    allowed_roots_env = os.getenv("ALLOWED_ROOTS", "/app/output,/app/temp")
    allowed_roots = [Path(root.strip()).resolve() for root in allowed_roots_env.split(",")]
    
    # Ensure allowed roots exist
    for root in allowed_roots:
        root.mkdir(parents=True, exist_ok=True)
    
    app = FastAPI(
        title="Filesystem MCP Server",
        description="Secure file operations with MCP Roots security model",
        version="1.0.0"
    )

    def _is_path_allowed(path_to_check: str) -> bool:
        """
        Verify that the given path is within one of the allowed roots.
        
        This is a critical security function that prevents directory traversal
        attacks and ensures file operations stay within approved boundaries.
        """
        try:
            # Resolve the path to handle relative paths and symlinks
            target_path = Path(path_to_check).resolve()
            
            # Check if the path is within any of the allowed roots
            for allowed_root in allowed_roots:
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

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint for container orchestration."""
        return HealthResponse(
            status="healthy",
            service="filesystem",
            timestamp=time.time(),
            allowed_roots=[str(root) for root in allowed_roots]
        )

    @app.post("/tools/save_file", response_model=Dict[str, Any])
    async def save_file_endpoint(params: SaveFileParams):
        """
        Save content to a file with security validation.
        
        This endpoint demonstrates MCP Roots by validating that the target
        path is within the allowed directory structure before performing
        any file operations.
        """
        print(f"[FileSystemServer] HTTP: Attempting to save file: {params.file_path}")
        
        # Critical security check using MCP Roots model
        if not _is_path_allowed(params.file_path):
            error_msg = (
                f"Access denied: '{params.file_path}' is outside allowed roots. "
                f"Allowed roots: {[str(r) for r in allowed_roots]}"
            )
            print(f"[FileSystemServer] HTTP: SECURITY VIOLATION: {error_msg}")
            raise HTTPException(status_code=403, detail=error_msg)
        
        try:
            # Resolve the full path
            target_path = Path(params.file_path).resolve()
            
            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content asynchronously
            async with aiofiles.open(target_path, 'w', encoding='utf-8') as f:
                await f.write(params.content)
            
            # Get file size for response
            file_size = target_path.stat().st_size
            
            response = SaveFileResponse(
                success=True,
                file_path=str(target_path),
                bytes_written=file_size
            )
            
            print(f"[FileSystemServer] HTTP: Successfully saved {file_size} bytes to {target_path}")
            return response.model_dump()
            
        except IOError as e:
            error_msg = f"Failed to save file '{params.file_path}': {e}"
            print(f"[FileSystemServer] HTTP: ERROR: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

    @app.post("/tools/validate_path", response_model=PathValidationResponse)
    async def validate_path_endpoint(request: PathValidationRequest):
        """
        Validate a path without performing any operations.
        
        Useful for clients to check if a path is allowed before attempting
        file operations.
        """
        is_allowed = _is_path_allowed(request.path)
        resolved_path = None
        
        if is_allowed:
            try:
                resolved_path = str(Path(request.path).resolve())
            except Exception:
                pass
        
        return PathValidationResponse(
            path=request.path,
            is_allowed=is_allowed,
            resolved_path=resolved_path
        )

    @app.get("/allowed_roots")
    async def get_allowed_roots():
        """
        Return the list of allowed root directories.
        
        This is useful for clients to understand the security boundaries.
        """
        return {
            "allowed_roots": [str(root) for root in allowed_roots],
            "total_roots": len(allowed_roots)
        }

    @app.get("/")
    async def root():
        """Root endpoint with server information."""
        return {
            "service": "Filesystem MCP Server",
            "version": "1.0.0",
            "tools": ["save_file", "validate_path"],
            "security_model": "MCP Roots",
            "allowed_roots": [str(root) for root in allowed_roots],
            "endpoints": {
                "health": "/health",
                "save_file": "/tools/save_file",
                "validate_path": "/tools/validate_path",
                "allowed_roots": "/allowed_roots"
            }
        }

    return app


# For direct running (development)
if __name__ == "__main__":
    import uvicorn
    app = create_filesystem_app()
    uvicorn.run(app, host="0.0.0.0", port=8002)
