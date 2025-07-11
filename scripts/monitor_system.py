#!/usr/bin/env python3
"""
Real-time System Monitoring

Continuously monitors Project Synapse system resources and performance
to identify patterns and optimization opportunities.
"""

import asyncio
import time
import json
import psutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List
import aiohttp

class SystemMonitor:
    """
    Continuous system monitoring for Project Synapse.
    
    Tracks:
    - Docker container resource usage
    - HTTP endpoint response times
    - System memory and CPU
    - Network I/O patterns
    """
    
    def __init__(self, monitoring_duration: int = 300):  # 5 minutes default
        self.monitoring_duration = monitoring_duration
        self.data_points = []
        self.endpoints = {
            "primary_health": "http://localhost:8001/health",
            "filesystem_health": "http://localhost:8002/health",
        }
    
    async def get_endpoint_health(self) -> Dict[str, float]:
        """Check response times of key endpoints."""
        health_data = {}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for name, url in self.endpoints.items():
                start_time = time.time()
                try:
                    async with session.get(url) as resp:
                        await resp.text()
                        if resp.status == 200:
                            health_data[name] = (time.time() - start_time) * 1000  # ms
                        else:
                            health_data[name] = -1  # Error indicator
                except Exception:
                    health_data[name] = -1  # Error indicator
        
        return health_data
    
    def get_docker_container_stats(self) -> Dict[str, Dict]:
        """Get detailed Docker container statistics."""
        try:
            # Get container stats
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", 
                 "{{.Container}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                return {}
            
            stats = {}
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split(',')
                if len(parts) >= 6:
                    container = parts[0]
                    
                    # Parse CPU percentage
                    cpu_str = parts[1].replace('%', '')
                    try:
                        cpu_percent = float(cpu_str)
                    except ValueError:
                        cpu_percent = 0.0
                    
                    # Parse memory usage (e.g., "123.4MiB / 2GiB")
                    memory_parts = parts[2].split(' / ')
                    memory_used_str = memory_parts[0].replace('MiB', '').replace('GiB', '').replace('B', '')
                    try:
                        if 'GiB' in parts[2]:
                            memory_used_mb = float(memory_used_str) * 1024
                        else:
                            memory_used_mb = float(memory_used_str)
                    except ValueError:
                        memory_used_mb = 0.0
                    
                    # Parse memory percentage
                    mem_percent_str = parts[3].replace('%', '')
                    try:
                        mem_percent = float(mem_percent_str)
                    except ValueError:
                        mem_percent = 0.0
                    
                    stats[container] = {
                        'cpu_percent': cpu_percent,
                        'memory_mb': memory_used_mb,
                        'memory_percent': mem_percent,
                        'network_io': parts[4],
                        'block_io': parts[5]
                    }
            
            return stats
        except Exception as e:
            print(f"Error getting Docker stats: {e}")
            return {}
    
    def get_system_resources(self) -> Dict[str, float]:
        """Get overall system resource usage."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_available_gb': psutil.virtual_memory().available / (1024**3),
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
            }
        except Exception:
            return {}
    
    async def collect_metrics(self) -> Dict:
        """Collect comprehensive system metrics."""
        timestamp = datetime.now().isoformat()
        
        # Collect all metrics concurrently where possible
        endpoint_health = await self.get_endpoint_health()
        docker_stats = self.get_docker_container_stats()
        system_resources = self.get_system_resources()
        
        return {
            'timestamp': timestamp,
            'endpoint_health': endpoint_health,
            'docker_containers': docker_stats,
            'system_resources': system_resources
        }
    
    async def run_monitoring(self):
        """Run continuous monitoring for specified duration."""
        print(f"🔍 Starting system monitoring for {self.monitoring_duration} seconds...")
        print("📊 Collecting metrics every 10 seconds...")
        
        start_time = time.time()
        sample_count = 0
        
        while (time.time() - start_time) < self.monitoring_duration:
            try:
                metrics = await self.collect_metrics()
                self.data_points.append(metrics)
                sample_count += 1
                
                # Display current status
                current_time = datetime.now().strftime('%H:%M:%S')
                endpoint_status = "🟢" if all(v > 0 for v in metrics['endpoint_health'].values()) else "🔴"
                
                cpu_usage = metrics['system_resources'].get('cpu_percent', 0)
                memory_usage = metrics['system_resources'].get('memory_percent', 0)
                
                print(f"  [{current_time}] {endpoint_status} CPU: {cpu_usage:.1f}% | Memory: {memory_usage:.1f}% | Sample: {sample_count}")
                
                # Wait 10 seconds before next sample
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"    ⚠️  Error collecting metrics: {e}")
                await asyncio.sleep(5)
        
        print(f"✅ Monitoring completed. Collected {len(self.data_points)} data points.")
    
    def analyze_performance_trends(self) -> Dict:
        """Analyze collected metrics for trends and patterns."""
        if not self.data_points:
            return {}
        
        analysis = {
            'monitoring_duration': self.monitoring_duration,
            'samples_collected': len(self.data_points),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Endpoint response time analysis
        endpoint_trends = {}
        for point in self.data_points:
            for endpoint, response_time in point['endpoint_health'].items():
                if endpoint not in endpoint_trends:
                    endpoint_trends[endpoint] = []
                if response_time > 0:  # Valid response time
                    endpoint_trends[endpoint].append(response_time)
        
        endpoint_analysis = {}
        for endpoint, times in endpoint_trends.items():
            if times:
                endpoint_analysis[endpoint] = {
                    'avg_response_ms': sum(times) / len(times),
                    'min_response_ms': min(times),
                    'max_response_ms': max(times),
                    'uptime_percentage': (len(times) / len(self.data_points)) * 100
                }
        
        analysis['endpoint_performance'] = endpoint_analysis
        
        # System resource trends
        cpu_values = []
        memory_values = []
        
        for point in self.data_points:
            sys_res = point.get('system_resources', {})
            if 'cpu_percent' in sys_res:
                cpu_values.append(sys_res['cpu_percent'])
            if 'memory_percent' in sys_res:
                memory_values.append(sys_res['memory_percent'])
        
        if cpu_values:
            analysis['system_cpu'] = {
                'avg_percent': sum(cpu_values) / len(cpu_values),
                'max_percent': max(cpu_values),
                'min_percent': min(cpu_values)
            }
        
        if memory_values:
            analysis['system_memory'] = {
                'avg_percent': sum(memory_values) / len(memory_values),
                'max_percent': max(memory_values),
                'min_percent': min(memory_values)
            }
        
        # Container resource trends
        container_analysis = {}
        container_names = set()
        
        for point in self.data_points:
            for container in point.get('docker_containers', {}):
                container_names.add(container)
        
        for container in container_names:
            cpu_usage = []
            memory_usage = []
            
            for point in self.data_points:
                container_data = point.get('docker_containers', {}).get(container, {})
                if 'cpu_percent' in container_data:
                    cpu_usage.append(container_data['cpu_percent'])
                if 'memory_mb' in container_data:
                    memory_usage.append(container_data['memory_mb'])
            
            if cpu_usage or memory_usage:
                container_analysis[container] = {}
                if cpu_usage:
                    container_analysis[container]['cpu'] = {
                        'avg_percent': sum(cpu_usage) / len(cpu_usage),
                        'max_percent': max(cpu_usage)
                    }
                if memory_usage:
                    container_analysis[container]['memory'] = {
                        'avg_mb': sum(memory_usage) / len(memory_usage),
                        'max_mb': max(memory_usage)
                    }
        
        analysis['container_performance'] = container_analysis
        
        return analysis
    
    def generate_monitoring_report(self, analysis: Dict) -> str:
        """Generate comprehensive monitoring report."""
        report = f"""
# Project Synapse Monitoring Report
Generated: {analysis.get('analysis_timestamp', 'Unknown')}

## Monitoring Summary
- **Duration**: {analysis.get('monitoring_duration', 0)} seconds
- **Samples Collected**: {analysis.get('samples_collected', 0)}
- **Sampling Interval**: 10 seconds

## Endpoint Performance Trends

"""
        
        endpoint_perf = analysis.get('endpoint_performance', {})
        if endpoint_perf:
            report += "| Endpoint | Avg Response (ms) | Min (ms) | Max (ms) | Uptime % |\n"
            report += "|----------|-------------------|----------|----------|-----------|\n"
            
            for endpoint, metrics in endpoint_perf.items():
                report += f"| {endpoint} | {metrics['avg_response_ms']:.1f} | {metrics['min_response_ms']:.1f} | {metrics['max_response_ms']:.1f} | {metrics['uptime_percentage']:.1f}% |\n"
        
        # System resources
        system_cpu = analysis.get('system_cpu', {})
        system_memory = analysis.get('system_memory', {})
        
        if system_cpu or system_memory:
            report += "\n## System Resource Utilization\n\n"
            
            if system_cpu:
                report += f"**CPU Usage**:\n"
                report += f"- Average: {system_cpu['avg_percent']:.1f}%\n"
                report += f"- Peak: {system_cpu['max_percent']:.1f}%\n"
                report += f"- Minimum: {system_cpu['min_percent']:.1f}%\n\n"
            
            if system_memory:
                report += f"**Memory Usage**:\n"
                report += f"- Average: {system_memory['avg_percent']:.1f}%\n"
                report += f"- Peak: {system_memory['max_percent']:.1f}%\n"
                report += f"- Minimum: {system_memory['min_percent']:.1f}%\n\n"
        
        # Container performance
        container_perf = analysis.get('container_performance', {})
        if container_perf:
            report += "## Container Resource Usage\n\n"
            
            for container, metrics in container_perf.items():
                report += f"**{container}**:\n"
                
                if 'cpu' in metrics:
                    cpu = metrics['cpu']
                    report += f"- CPU: {cpu['avg_percent']:.1f}% avg, {cpu['max_percent']:.1f}% peak\n"
                
                if 'memory' in metrics:
                    memory = metrics['memory']
                    report += f"- Memory: {memory['avg_mb']:.1f}MB avg, {memory['max_mb']:.1f}MB peak\n"
                
                report += "\n"
        
        # Recommendations
        report += "## Performance Insights\n\n"
        
        if endpoint_perf:
            slow_endpoints = [name for name, metrics in endpoint_perf.items() 
                            if metrics['avg_response_ms'] > 100]
            if slow_endpoints:
                report += f"**Slow Endpoints**: {', '.join(slow_endpoints)} (>100ms average)\n"
        
        if system_cpu and system_cpu['avg_percent'] > 50:
            report += f"**High CPU Usage**: Average {system_cpu['avg_percent']:.1f}% - consider optimization\n"
        
        if system_memory and system_memory['avg_percent'] > 80:
            report += f"**High Memory Usage**: Average {system_memory['avg_percent']:.1f}% - monitor for leaks\n"
        
        report += "\n**Next Steps**: Use these metrics to guide Phase 2 optimization efforts.\n"
        
        return report

async def main():
    """Run system monitoring and generate report."""
    print("🚀 Project Synapse System Monitoring")
    print("=" * 50)
    print("Phase 2: Performance Monitoring & Analysis")
    print("=" * 50)
    
    # Ask for monitoring duration
    try:
        duration = int(input("Enter monitoring duration in seconds (default 60): ") or "60")
    except ValueError:
        duration = 60
    
    monitor = SystemMonitor(monitoring_duration=duration)
    
    # Run monitoring
    await monitor.run_monitoring()
    
    # Analyze results
    print("\n📊 Analyzing performance trends...")
    analysis = monitor.analyze_performance_trends()
    
    # Generate report
    print("📝 Generating monitoring report...")
    report = monitor.generate_monitoring_report(analysis)
    
    # Save report
    report_file = f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Save raw data for further analysis
    data_file = f"monitoring_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(data_file, 'w') as f:
        json.dump({
            'analysis': analysis,
            'raw_data': monitor.data_points
        }, f, indent=2)
    
    print(f"\n✅ Monitoring completed!")
    print(f"📄 Report saved to: {report_file}")
    print(f"📊 Raw data saved to: {data_file}")
    
    # Display key insights
    if analysis.get('endpoint_performance'):
        print("\n🔍 Key Insights:")
        for endpoint, metrics in analysis['endpoint_performance'].items():
            status = "🟢" if metrics['uptime_percentage'] > 99 else "🟡" if metrics['uptime_percentage'] > 95 else "🔴"
            print(f"  {status} {endpoint}: {metrics['avg_response_ms']:.1f}ms avg, {metrics['uptime_percentage']:.1f}% uptime")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
