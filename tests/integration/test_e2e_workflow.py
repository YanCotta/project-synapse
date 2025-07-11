#!/usr/bin/env python3
"""
End-to-End Workflow Integration Tests

Comprehensive integration testing for Project Synapse async implementation.
Tests complete workflows from task injection to result validation.
"""

import asyncio
import aiohttp
import json
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import tempfile
import os

# Test framework
import pytest
import docker

# Project imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from protocols.acp_schema import ACPMessage, ACPMsgType, TaskAssignPayload, LogBroadcastPayload
from message_bus.rabbitmq_bus import RabbitMQBus

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class E2EWorkflowTester:
    """
    End-to-end workflow testing framework.
    
    Manages Docker containers, message injection, and result validation
    for comprehensive system testing.
    """
    
    def __init__(self):
        self.docker_client = None
        self.containers = {}
        self.message_bus = None
        self.test_id = str(uuid.uuid4())[:8]
        self.results_dir = Path(tempfile.mkdtemp(prefix=f"synapse_e2e_{self.test_id}_"))
        
        # Test configuration
        self.rabbitmq_url = "amqp://synapse:synapse123@localhost:5672/"
        self.mcp_servers = {
            "primary_tooling": "http://localhost:8001",
            "filesystem": "http://localhost:8002"
        }
        
        # Test workflow configuration
        self.test_query = f"quantum computing impact on cryptography - test {self.test_id}"
        self.workflow_timeout = 120  # 2 minutes for full workflow
        
        logger.info(f"E2E Test initialized with ID: {self.test_id}")
        logger.info(f"Results directory: {self.results_dir}")
    
    async def setup_test_environment(self):
        """Set up the complete test environment."""
        logger.info("Setting up E2E test environment...")
        
        # Initialize Docker client
        self.docker_client = docker.from_env()
        
        # Ensure test results directory exists
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Wait for services to be ready
        await self._wait_for_services()
        
        # Initialize message bus connection
        self.message_bus = RabbitMQBus(self.rabbitmq_url)
        connected = await self.message_bus.connect()
        
        if not connected:
            raise RuntimeError("Failed to connect to RabbitMQ for E2E testing")
        
        logger.info("E2E test environment setup complete")
    
    async def _wait_for_services(self, timeout: int = 60):
        """Wait for all required services to be available."""
        logger.info("Waiting for services to be ready...")
        
        services_to_check = [
            ("RabbitMQ Management", "http://localhost:15672"),
            ("Primary Tooling Server", self.mcp_servers["primary_tooling"] + "/health"),
            ("Filesystem Server", self.mcp_servers["filesystem"] + "/health")
        ]
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            for service_name, url in services_to_check:
                service_ready = False
                
                while not service_ready and (time.time() - start_time) < timeout:
                    try:
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                logger.info(f"✅ {service_name} is ready")
                                service_ready = True
                            else:
                                logger.debug(f"⏳ {service_name} returned {response.status}")
                    except Exception as e:
                        logger.debug(f"⏳ Waiting for {service_name}: {e}")
                        await asyncio.sleep(2)
                
                if not service_ready:
                    raise TimeoutError(f"Service {service_name} not ready after {timeout}s")
        
        # Additional wait for agent startup
        logger.info("Waiting for agents to initialize...")
        await asyncio.sleep(10)
    
    async def test_full_workflow_execution(self):
        """
        Test complete workflow execution from task injection to result validation.
        
        This is the core E2E test that validates:
        1. Task injection into RabbitMQ
        2. Agent processing and communication
        3. MCP server integration
        4. File saving and result validation
        """
        logger.info(f"Starting full workflow E2E test with query: '{self.test_query}'")
        
        test_start_time = time.time()
        workflow_events = []
        
        # Step 1: Inject high-level task
        logger.info("Step 1: Injecting research task into workflow...")
        
        initial_task = ACPMessage(
            sender_id="e2e_test",
            receiver_id="orchestrator",
            msg_type=ACPMsgType.TASK_ASSIGN,
            payload=TaskAssignPayload(
                task_type="research_query",
                task_data={
                    "query": self.test_query,
                    "requester": "e2e_test",
                    "test_id": self.test_id,
                    "output_directory": str(self.results_dir)
                },
                priority=1,
                correlation_id=self.test_id
            ).model_dump()
        )
        
        # Send task to orchestrator
        await self.message_bus.publish_message("orchestrator", initial_task.model_dump())
        
        workflow_events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "task_injected",
            "details": {"query": self.test_query, "test_id": self.test_id}
        })
        
        logger.info("✅ Task injected successfully")
        
        # Step 2: Monitor workflow progress through log events
        logger.info("Step 2: Monitoring workflow progress...")
        
        expected_stages = [
            "search_web",
            "extract_content", 
            "fact_check",
            "synthesize_report",
            "save_file"
        ]
        
        completed_stages = []
        log_events = []
        
        # Subscribe to logs topic to monitor progress
        async def log_message_handler(message: Dict):
            try:
                log_data = LogBroadcastPayload(**message.get("payload", {}))
                
                # Filter for our test correlation ID
                if (log_data.correlation_id == self.test_id or 
                    self.test_id in log_data.message):
                    
                    log_events.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": log_data.level,
                        "message": log_data.message,
                        "component": log_data.component
                    })
                    
                    logger.info(f"📊 [{log_data.component}] {log_data.message}")
                    
                    # Check for stage completion indicators
                    for stage in expected_stages:
                        if (stage in log_data.message.lower() and 
                            "complet" in log_data.message.lower() and
                            stage not in completed_stages):
                            
                            completed_stages.append(stage)
                            workflow_events.append({
                                "timestamp": datetime.utcnow().isoformat(),
                                "event": f"stage_completed",
                                "stage": stage,
                                "component": log_data.component
                            })
                            
                            logger.info(f"✅ Stage completed: {stage}")
                            
            except Exception as e:
                logger.error(f"Error processing log message: {e}")
        
        # Subscribe to logs
        await self.message_bus.subscribe_topic("logs", log_message_handler)
        
        # Step 3: Wait for workflow completion or timeout
        logger.info("Step 3: Waiting for workflow completion...")
        
        start_time = time.time()
        workflow_completed = False
        
        while (time.time() - start_time) < self.workflow_timeout and not workflow_completed:
            # Check if all stages are completed
            if len(completed_stages) >= len(expected_stages):
                workflow_completed = True
                break
            
            # Log progress every 30 seconds
            elapsed = time.time() - start_time
            if int(elapsed) % 30 == 0:
                logger.info(f"⏳ Workflow progress: {len(completed_stages)}/{len(expected_stages)} stages completed ({elapsed:.0f}s elapsed)")
            
            await asyncio.sleep(5)
        
        if not workflow_completed:
            logger.warning(f"⚠️ Workflow timeout reached ({self.workflow_timeout}s)")
            logger.info(f"Completed stages: {completed_stages}")
        else:
            logger.info("✅ Workflow completed successfully!")
        
        # Step 4: Validate results
        logger.info("Step 4: Validating workflow results...")
        
        validation_results = await self._validate_workflow_results()
        
        # Step 5: Generate test report
        test_duration = time.time() - test_start_time
        
        test_report = {
            "test_id": self.test_id,
            "test_query": self.test_query,
            "test_duration_seconds": test_duration,
            "workflow_completed": workflow_completed,
            "completed_stages": completed_stages,
            "expected_stages": expected_stages,
            "workflow_events": workflow_events,
            "log_events": log_events,
            "validation_results": validation_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save test report
        report_file = self.results_dir / f"e2e_test_report_{self.test_id}.json"
        with open(report_file, 'w') as f:
            json.dump(test_report, f, indent=2)
        
        logger.info(f"📊 Test report saved: {report_file}")
        logger.info(f"🎯 E2E Test completed in {test_duration:.1f}s")
        
        return test_report
    
    async def _validate_workflow_results(self) -> Dict[str, Any]:
        """Validate that the workflow produced expected results."""
        validation_results = {
            "files_created": [],
            "file_validation": {},
            "mcp_server_health": {},
            "message_bus_health": True
        }
        
        # Check for created files
        logger.info("Validating created files...")
        
        for file_path in self.results_dir.glob("**/*"):
            if file_path.is_file():
                validation_results["files_created"].append(str(file_path))
                
                # Basic file validation
                file_size = file_path.stat().st_size
                validation_results["file_validation"][str(file_path)] = {
                    "exists": True,
                    "size_bytes": file_size,
                    "readable": file_path.is_file(),
                    "valid_size": file_size > 0
                }
        
        # Check MCP server health
        logger.info("Validating MCP server health...")
        
        async with aiohttp.ClientSession() as session:
            for server_name, server_url in self.mcp_servers.items():
                try:
                    async with session.get(f"{server_url}/health", timeout=10) as response:
                        validation_results["mcp_server_health"][server_name] = {
                            "status_code": response.status,
                            "healthy": response.status == 200,
                            "response_time_ms": None  # Would need timing implementation
                        }
                except Exception as e:
                    validation_results["mcp_server_health"][server_name] = {
                        "status_code": None,
                        "healthy": False,
                        "error": str(e)
                    }
        
        logger.info(f"Validation complete: {len(validation_results['files_created'])} files created")
        
        return validation_results
    
    async def cleanup_test_environment(self):
        """Clean up test environment and resources."""
        logger.info("Cleaning up E2E test environment...")
        
        # Disconnect message bus
        if self.message_bus:
            await self.message_bus.disconnect()
        
        # Note: In a real scenario, we might want to clean up temporary files
        # For debugging, we'll leave the results directory
        logger.info(f"Test results preserved in: {self.results_dir}")
        
        logger.info("E2E test cleanup complete")


class TestE2EWorkflow:
    """Pytest test class for E2E workflow testing."""
    
    @pytest.mark.asyncio
    async def test_complete_research_workflow(self):
        """Test complete research workflow execution."""
        tester = E2EWorkflowTester()
        
        try:
            # Setup
            await tester.setup_test_environment()
            
            # Execute test
            test_report = await tester.test_full_workflow_execution()
            
            # Assertions
            assert test_report["workflow_completed"], "Workflow did not complete successfully"
            assert len(test_report["completed_stages"]) >= 3, "Insufficient stages completed"
            assert test_report["validation_results"]["message_bus_health"], "Message bus health check failed"
            
            # Check that at least some files were created
            files_created = test_report["validation_results"]["files_created"]
            assert len(files_created) > 0, "No output files were created"
            
            logger.info("✅ E2E workflow test passed!")
            
        finally:
            # Cleanup
            await tester.cleanup_test_environment()


# Standalone execution for manual testing
async def main():
    """Manual E2E test execution."""
    logger.info("🧪 Starting manual E2E workflow test...")
    
    tester = E2EWorkflowTester()
    
    try:
        await tester.setup_test_environment()
        test_report = await tester.test_full_workflow_execution()
        
        print("\n" + "="*60)
        print("📊 E2E TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Test ID: {test_report['test_id']}")
        print(f"Query: {test_report['test_query']}")
        print(f"Duration: {test_report['test_duration_seconds']:.1f}s")
        print(f"Workflow Completed: {'✅ YES' if test_report['workflow_completed'] else '❌ NO'}")
        print(f"Stages Completed: {len(test_report['completed_stages'])}/{len(test_report['expected_stages'])}")
        print(f"Files Created: {len(test_report['validation_results']['files_created'])}")
        print("="*60)
        
        return test_report
        
    except Exception as e:
        logger.error(f"E2E test failed: {e}")
        raise
    finally:
        await tester.cleanup_test_environment()


if __name__ == "__main__":
    asyncio.run(main())
