#!/usr/bin/env python3
"""
System Health Check Script

Validates that all Project Synapse services are running and healthy
before executing end-to-end tests.
"""

import asyncio
import aiohttp
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json

class SystemHealthChecker:
    """
    Comprehensive health check for Project Synapse deployment.
    
    Validates:
    - Docker containers are running
    - Services respond to health checks
    - RabbitMQ is accessible
    - MCP servers are responding
    """
    
    def __init__(self):
        self.docker_services = [
            "synapse-rabbitmq",
            "synapse-primary-tooling", 
            "synapse-filesystem",
            "synapse-agents"
        ]
        
        self.http_endpoints = {
            "RabbitMQ Management": "http://localhost:15672",
            "Primary Tooling Server": "http://localhost:8001/health",
            "Filesystem Server": "http://localhost:8002/health"
        }
        
        self.rabbitmq_config = {
            "host": "localhost",
            "port": 5672,
            "vhost": "/",
            "username": "synapse",
            "password": "synapse123"
        }
    
    def check_docker_containers(self) -> Dict[str, bool]:
        """Check if all required Docker containers are running."""
        print("🐳 Checking Docker containers...")
        
        container_status = {}
        
        try:
            # Get running containers
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}:{{.Status}}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            running_containers = {}
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    name, status = line.split(':', 1)
                    running_containers[name] = 'Up' in status
            
            # Check each required service
            for service in self.docker_services:
                is_running = running_containers.get(service, False)
                container_status[service] = is_running
                
                status_icon = "✅" if is_running else "❌"
                print(f"  {status_icon} {service}: {'Running' if is_running else 'Not Running'}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error checking Docker containers: {e}")
            for service in self.docker_services:
                container_status[service] = False
        
        return container_status
    
    async def check_http_endpoints(self) -> Dict[str, Dict]:
        """Check HTTP endpoint health."""
        print("🌐 Checking HTTP endpoints...")
        
        endpoint_status = {}
        
        async with aiohttp.ClientSession() as session:
            for name, url in self.http_endpoints.items():
                try:
                    start_time = time.time()
                    async with session.get(url, timeout=10) as response:
                        response_time = time.time() - start_time
                        
                        endpoint_status[name] = {
                            "healthy": response.status == 200,
                            "status_code": response.status,
                            "response_time_ms": round(response_time * 1000, 2)
                        }
                        
                        status_icon = "✅" if response.status == 200 else "❌"
                        print(f"  {status_icon} {name}: {response.status} ({response_time*1000:.1f}ms)")
                        
                except Exception as e:
                    endpoint_status[name] = {
                        "healthy": False,
                        "status_code": None,
                        "error": str(e)
                    }
                    
                    print(f"  ❌ {name}: {e}")
        
        return endpoint_status
    
    def check_rabbitmq_connection(self) -> Dict[str, any]:
        """Check RabbitMQ connection using management API."""
        print("🐰 Checking RabbitMQ connection...")
        
        rabbitmq_status = {
            "accessible": False,
            "vhost_accessible": False,
            "queues_exist": False,
            "error": None
        }
        
        try:
            # Use curl to check RabbitMQ management API
            management_url = f"http://guest:guest@localhost:15672/api/overview"
            
            result = subprocess.run(
                ["curl", "-s", "-u", "guest:guest", management_url],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                rabbitmq_status["accessible"] = True
                print("  ✅ RabbitMQ Management API accessible")
                
                # Try to parse response to get more details
                try:
                    api_data = json.loads(result.stdout)
                    rabbitmq_version = api_data.get("rabbitmq_version", "unknown")
                    print(f"  📊 RabbitMQ version: {rabbitmq_version}")
                except json.JSONDecodeError:
                    pass
                    
            else:
                rabbitmq_status["error"] = "Management API not accessible"
                print("  ❌ RabbitMQ Management API not accessible")
                
        except subprocess.TimeoutExpired:
            rabbitmq_status["error"] = "Connection timeout"
            print("  ❌ RabbitMQ connection timeout")
        except Exception as e:
            rabbitmq_status["error"] = str(e)
            print(f"  ❌ RabbitMQ check failed: {e}")
        
        return rabbitmq_status
    
    def check_project_structure(self) -> Dict[str, bool]:
        """Verify project structure and key files exist."""
        print("📁 Checking project structure...")
        
        required_files = [
            "async_main.py",
            "docker-compose.yml",
            "requirements.txt",
            "src/agents/async_orchestrator.py",
            "src/mcp_servers/fastapi_primary_server.py",
            "src/message_bus/rabbitmq_bus.py"
        ]
        
        structure_status = {}
        
        project_root = Path(__file__).parent.parent
        
        for file_path in required_files:
            full_path = project_root / file_path
            exists = full_path.exists()
            structure_status[file_path] = exists
            
            status_icon = "✅" if exists else "❌"
            print(f"  {status_icon} {file_path}")
        
        return structure_status
    
    async def run_comprehensive_health_check(self) -> Dict[str, any]:
        """Run all health checks and return comprehensive status."""
        print("🏥 Starting Project Synapse Health Check")
        print("=" * 50)
        
        health_report = {
            "timestamp": time.time(),
            "overall_healthy": True,
            "checks": {}
        }
        
        # Check 1: Project structure
        structure_status = self.check_project_structure()
        health_report["checks"]["project_structure"] = structure_status
        
        if not all(structure_status.values()):
            health_report["overall_healthy"] = False
            print("\n❌ Project structure check failed!")
        
        print()
        
        # Check 2: Docker containers
        container_status = self.check_docker_containers()
        health_report["checks"]["docker_containers"] = container_status
        
        if not all(container_status.values()):
            health_report["overall_healthy"] = False
            print("\n❌ Some Docker containers are not running!")
            print("Run: docker-compose up -d --build")
        
        print()
        
        # Check 3: HTTP endpoints (only if containers are running)
        if any(container_status.values()):
            endpoint_status = await self.check_http_endpoints()
            health_report["checks"]["http_endpoints"] = endpoint_status
            
            if not all(ep["healthy"] for ep in endpoint_status.values()):
                health_report["overall_healthy"] = False
                print("\n⚠️ Some HTTP endpoints are not healthy!")
        else:
            print("⏭️ Skipping HTTP endpoint checks (containers not running)")
            health_report["checks"]["http_endpoints"] = {}
        
        print()
        
        # Check 4: RabbitMQ
        rabbitmq_status = self.check_rabbitmq_connection()
        health_report["checks"]["rabbitmq"] = rabbitmq_status
        
        if not rabbitmq_status["accessible"]:
            health_report["overall_healthy"] = False
            print("\n❌ RabbitMQ is not accessible!")
        
        # Summary
        print("\n" + "=" * 50)
        if health_report["overall_healthy"]:
            print("✅ SYSTEM HEALTHY - Ready for E2E testing!")
        else:
            print("❌ SYSTEM ISSUES DETECTED - Fix before testing")
            print("\nQuick fixes:")
            print("1. docker-compose up -d --build")
            print("2. Wait 30 seconds for services to start")
            print("3. Re-run health check")
        
        print("=" * 50)
        
        return health_report


async def main():
    """Main health check execution."""
    checker = SystemHealthChecker()
    health_report = await checker.run_comprehensive_health_check()
    
    # Exit with appropriate code
    exit_code = 0 if health_report["overall_healthy"] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
