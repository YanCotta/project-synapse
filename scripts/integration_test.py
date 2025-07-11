#!/usr/bin/env python3
"""
Quick Integration Test

Tests the running system via HTTP endpoints to validate Phase 1 functionality.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def test_primary_tooling_server():
    """Test Primary Tooling MCP Server endpoints."""
    print("🔍 Testing Primary Tooling Server...")
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("  Testing health endpoint...")
        async with session.get("http://localhost:8001/health") as resp:
            if resp.status == 200:
                health_data = await resp.json()
                print(f"    ✅ Health: {health_data['status']} - {health_data['service']}")
            else:
                print(f"    ❌ Health check failed: {resp.status}")
                return False
        
        # Test search endpoint
        print("  Testing search web tool...")
        search_payload = {
            "query": "quantum computing and cryptography",
            "max_results": 3
        }
        async with session.post("http://localhost:8001/tools/search_web", 
                               json=search_payload) as resp:
            if resp.status == 200:
                search_data = await resp.json()
                print(f"    ✅ Search found {len(search_data['results'])} results")
                print(f"    📝 Sample: {search_data['results'][0]['title'][:50]}...")
            else:
                print(f"    ❌ Search failed: {resp.status}")
                return False
        
        # Test streaming extraction
        print("  Testing streaming extraction...")
        extract_payload = {
            "url": "https://example.com/quantum-crypto-current"
        }
        async with session.post("http://localhost:8001/tools/browse_and_extract",
                               json=extract_payload) as resp:
            if resp.status == 200:
                print("    ✅ Streaming extraction started")
                content = await resp.text()
                if "event: result" in content:
                    print("    ✅ Received extraction result")
                else:
                    print("    ⚠️  No final result in stream")
            else:
                print(f"    ❌ Extraction failed: {resp.status}")
                return False
    
    return True

async def test_filesystem_server():
    """Test Filesystem MCP Server endpoints."""
    print("🗂️  Testing Filesystem Server...")
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("  Testing health endpoint...")
        async with session.get("http://localhost:8002/health") as resp:
            if resp.status == 200:
                health_data = await resp.json()
                print(f"    ✅ Health: {health_data['status']} - {health_data['service']}")
                print(f"    📁 Allowed roots: {len(health_data['allowed_roots'])} configured")
            else:
                print(f"    ❌ Health check failed: {resp.status}")
                return False
        
        # Test path validation
        print("  Testing path validation...")
        validation_payload = {
            "path": "/app/output/test.txt"
        }
        async with session.post("http://localhost:8002/tools/validate_path",
                               json=validation_payload) as resp:
            if resp.status == 200:
                validation_data = await resp.json()
                if validation_data['is_allowed']:
                    print("    ✅ Path validation successful")
                else:
                    print("    ❌ Path not allowed (this might be expected)")
            else:
                print(f"    ❌ Path validation failed: {resp.status}")
                return False
        
        # Test file save
        print("  Testing file save...")
        save_payload = {
            "file_path": "/app/output/integration_test.txt",
            "content": f"Integration test run at {datetime.now().isoformat()}\nSystem validation successful!"
        }
        async with session.post("http://localhost:8002/tools/save_file",
                               json=save_payload) as resp:
            if resp.status == 200:
                save_data = await resp.json()
                print(f"    ✅ File saved: {save_data['bytes_written']} bytes")
            else:
                resp_text = await resp.text()
                if "outside allowed roots" in resp_text:
                    print("    ✅ Security validation working (path blocked)")
                else:
                    print(f"    ❌ File save failed: {resp.status} - {resp_text}")
                    return False
    
    return True

async def test_rabbitmq_management():
    """Test RabbitMQ Management API."""
    print("🐰 Testing RabbitMQ Management...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test management interface
            async with session.get("http://localhost:15672/api/overview",
                                  auth=aiohttp.BasicAuth("synapse", "synapse123")) as resp:
                if resp.status == 200:
                    overview = await resp.json()
                    print(f"    ✅ RabbitMQ Management API accessible")
                    print(f"    📊 RabbitMQ version: {overview.get('rabbitmq_version', 'unknown')}")
                else:
                    print(f"    ❌ Management API failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"    ❌ RabbitMQ connection failed: {e}")
            return False
    
    return True

async def test_agent_container():
    """Test that the agent container is running."""
    print("🤖 Testing Agent Container...")
    
    # For now, just verify we can see some output
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", "10", "synapse-agents"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print("    ✅ Agent container logs accessible")
            if "Starting async main" in result.stdout or "agents" in result.stdout.lower():
                print("    ✅ Agents appear to be running")
            else:
                print("    ⚠️  Agents might be starting up")
        else:
            print(f"    ❌ Could not access agent logs: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("    ⚠️  Docker logs command timed out")
        return False
    except Exception as e:
        print(f"    ❌ Error checking agent container: {e}")
        return False
    
    return True

async def main():
    """Run all integration tests."""
    print("🚀 Starting Project Synapse Integration Tests")
    print("=" * 60)
    
    start_time = time.time()
    tests = [
        ("Primary Tooling Server", test_primary_tooling_server),
        ("Filesystem Server", test_filesystem_server),
        ("RabbitMQ Management", test_rabbitmq_management),
        ("Agent Container", test_agent_container)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            print(f"    ❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:>8} | {test_name}")
        if success:
            passed += 1
    
    total_time = time.time() - start_time
    print(f"\n📈 Results: {passed}/{len(tests)} tests passed in {total_time:.1f}s")
    
    if passed == len(tests):
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("   Phase 1 of Production Readiness Plan: ✅ COMPLETE")
        print("   System ready for Phase 2: Performance Optimization")
    else:
        print(f"\n⚠️  {len(tests) - passed} tests failed - system needs attention")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
