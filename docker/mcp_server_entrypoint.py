#!/usr/bin/env python3
"""
MCP Server Entrypoint

Dynamically starts the appropriate FastAPI MCP server based on environment variables.
"""

import os
import sys
import uvicorn
from src.mcp_servers.fastapi_primary_server import create_primary_app
from src.mcp_servers.fastapi_filesystem_server import create_filesystem_app

def main():
    """Start the appropriate MCP server based on SERVER_TYPE environment variable."""
    server_type = os.getenv("SERVER_TYPE")
    port = int(os.getenv("PORT", 8000))
    
    if server_type == "primary_tooling":
        app = create_primary_app()
        print(f"Starting Primary Tooling MCP Server on port {port}")
    elif server_type == "filesystem":
        app = create_filesystem_app()
        print(f"Starting Filesystem MCP Server on port {port}")
    else:
        print(f"Unknown SERVER_TYPE: {server_type}")
        print("Valid options: primary_tooling, filesystem")
        sys.exit(1)
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
