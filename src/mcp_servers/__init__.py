# MCP Servers Package

# FastAPI production servers (current implementation)
from .fastapi_primary_server import create_primary_app
from .fastapi_filesystem_server import create_filesystem_app

# Create app instances for backwards compatibility
primary_server_app = create_primary_app()
filesystem_server_app = create_filesystem_app()

__all__ = [
    "create_primary_app",
    "create_filesystem_app",
    "primary_server_app",
    "filesystem_server_app"
]
