#!/usr/bin/env python3
"""
Simple System Test

A straightforward test to verify all services are working.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def test_system():
    """Test all system components."""
    print("🔍 Testing Project Synapse System...")
    
    # Test 1: Health checks for all services
    print("\n📊 Testing Service Health Checks...")
    
    services = [
        ("RabbitMQ Management", "http://localhost:15672"),
        ("Primary Tooling Server", "http://localhost:8001/health"),
        ("Filesystem Server", "http://localhost:8002/health"),
        ("Prometheus", "http://localhost:9090/-/ready"),
        ("Grafana", "http://localhost:3000/api/health")
    ]
    
    async with aiohttp.ClientSession() as session:
        for service_name, url in services:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        print(f"  ✅ {service_name}: HEALTHY")
                    else:
                        print(f"  ❌ {service_name}: UNHEALTHY (status: {response.status})")
            except Exception as e:
                print(f"  ❌ {service_name}: UNREACHABLE ({str(e)})")
    
    # Test 2: Test MCP Server Tools
    print("\n🛠️ Testing MCP Server Tools...")
    
    async with aiohttp.ClientSession() as session:
        # Test Primary Tooling Server - search_web
        try:
            search_params = {"query": "quantum computing cryptography"}
            async with session.post(
                "http://localhost:8001/tools/search_web", 
                json=search_params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"  ✅ Primary Server search_web: SUCCESS (found {len(result.get('results', []))} results)")
                else:
                    print(f"  ❌ Primary Server search_web: FAILED (status: {response.status})")
        except Exception as e:
            print(f"  ❌ Primary Server search_web: ERROR ({str(e)})")
        
        # Test Filesystem Server - validate_path
        try:
            validate_params = {"path": "/app/output"}
            async with session.post(
                "http://localhost:8002/tools/validate_path", 
                json=validate_params,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"  ✅ Filesystem Server validate_path: SUCCESS (allowed: {result.get('is_allowed')})")
                else:
                    print(f"  ❌ Filesystem Server validate_path: FAILED (status: {response.status})")
        except Exception as e:
            print(f"  ❌ Filesystem Server validate_path: ERROR ({str(e)})")
    
    # Test 3: Check Agent Container
    print("\n🤖 Testing Agent Container...")
    try:
        import docker
        client = docker.from_env()
        container = client.containers.get("synapse-agents")
        if container.status == "running":
            print(f"  ✅ Agent Container: RUNNING")
            
            # Check recent logs
            logs = container.logs(tail=5).decode('utf-8').strip()
            if logs:
                print(f"  📝 Recent Agent Logs:")
                for line in logs.split('\n')[-3:]:
                    print(f"    {line}")
        else:
            print(f"  ❌ Agent Container: NOT RUNNING (status: {container.status})")
    except Exception as e:
        print(f"  ❌ Agent Container: ERROR ({str(e)})")
    
    # Test 4: Check Metrics
    print("\n📈 Testing Monitoring Stack...")
    
    async with aiohttp.ClientSession() as session:
        # Check Prometheus metrics
        try:
            async with session.get(
                "http://localhost:9090/api/v1/query?query=up",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    up_services = len([m for m in result.get('data', {}).get('result', []) 
                                     if m.get('value', ['', '0'])[1] == '1'])
                    print(f"  ✅ Prometheus: {up_services} services UP")
                else:
                    print(f"  ❌ Prometheus: FAILED (status: {response.status})")
        except Exception as e:
            print(f"  ❌ Prometheus: ERROR ({str(e)})")
    
    print("\n🎯 System Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_system())
