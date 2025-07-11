#!/usr/bin/env python3
"""
Workflow Test - Inject Task via RabbitMQ

Simulates a user creating a research task by directly publishing to RabbitMQ.
"""

import asyncio
import aioamqp
import json
import uuid
from datetime import datetime

async def inject_research_task():
    """Inject a research task into the system via RabbitMQ."""
    
    print("🚀 Injecting Research Task...")
    
    try:
        # Connect to RabbitMQ
        transport, protocol = await aioamqp.connect(
            host='localhost',
            port=5672,
            login='synapse',
            password='synapse123',
            virtualhost='/'
        )
        
        channel = await protocol.channel()
        
        # Ensure the orchestrator queue exists
        await channel.queue_declare(queue_name='orchestrator', durable=True)
        
        # Create a research task message
        task_id = str(uuid.uuid4())[:8]
        message = {
            "sender_id": "user_interface",
            "receiver_id": "orchestrator",
            "topic": None,
            "msg_type": "TASK_ASSIGN",
            "payload": {
                "task_id": task_id,
                "task_type": "research_report",
                "query": "quantum computing impact on current cryptographic security methods",
                "requirements": [
                    "Search for recent developments in quantum computing",
                    "Analyze impact on RSA and AES encryption",
                    "Extract key findings from research papers",
                    "Synthesize comprehensive report",
                    "Include timeline for cryptographic migration"
                ],
                "priority": "normal",
                "deadline": "2025-07-11T17:30:00Z"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish the message
        await channel.basic_publish(
            payload=json.dumps(message).encode('utf-8'),
            exchange_name='',
            routing_key='orchestrator',
            properties={
                'delivery_mode': 2,  # Make message persistent
                'content_type': 'application/json'
            }
        )
        
        print(f"✅ Task injected successfully!")
        print(f"   Task ID: {task_id}")
        print(f"   Query: {message['payload']['query']}")
        print(f"   Target: orchestrator queue")
        
        await protocol.close()
        transport.close()
        
        return task_id
        
    except Exception as e:
        print(f"❌ Failed to inject task: {e}")
        return None

async def monitor_task_progress(task_id: str, duration: int = 60):
    """Monitor the task progress by checking logs and output."""
    
    print(f"\n📊 Monitoring task {task_id} for {duration} seconds...")
    
    import docker
    client = docker.from_env()
    
    start_time = asyncio.get_event_loop().time()
    last_log_count = 0
    
    while (asyncio.get_event_loop().time() - start_time) < duration:
        try:
            # Check agent container logs
            container = client.containers.get("synapse-agents")
            logs = container.logs(tail=10).decode('utf-8')
            
            if task_id in logs:
                print(f"   📝 Task {task_id} found in agent logs!")
                
            # Check for new output files
            import os
            output_dir = "/home/yan/Documents/Git/project-synapse/output/reports"
            if os.path.exists(output_dir):
                files = [f for f in os.listdir(output_dir) if f.endswith('.md')]
                if len(files) > last_log_count:
                    print(f"   📄 New report files detected: {len(files)} total")
                    last_log_count = len(files)
                    
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"   ⚠️ Monitoring error: {e}")
            await asyncio.sleep(5)
    
    print(f"✅ Monitoring complete for task {task_id}")

async def main():
    """Main workflow test function."""
    print("🧪 Project Synapse Workflow Test")
    print("=" * 50)
    
    # Inject task
    task_id = await inject_research_task()
    
    if task_id:
        # Monitor progress
        await monitor_task_progress(task_id, duration=90)
        
        # Check final results
        print(f"\n📋 Final Results Summary:")
        
        import os
        output_dir = "/home/yan/Documents/Git/project-synapse/output/reports"
        if os.path.exists(output_dir):
            files = [f for f in os.listdir(output_dir) if f.endswith('.md')]
            print(f"   📄 Total report files: {len(files)}")
            
            # Show the most recent file
            if files:
                latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(output_dir, f)))
                file_path = os.path.join(output_dir, latest_file)
                file_size = os.path.getsize(file_path)
                print(f"   📝 Latest report: {latest_file} ({file_size} bytes)")
        
        print(f"\n🎯 Workflow test complete!")
    else:
        print("❌ Cannot monitor - task injection failed")

if __name__ == "__main__":
    asyncio.run(main())
