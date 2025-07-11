#!/usr/bin/env python3
"""
Performance Testing & Optimization Suite

Establishes performance baselines and identifies optimization opportunities
for Project Synapse production deployment.
"""

import asyncio
import aiohttp
import time
import statistics
import json
import psutil
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import concurrent.futures

@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""
    test_name: str
    total_requests: int
    duration: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    requests_per_second: float
    success_rate: float
    errors: List[str]
    memory_usage_mb: float
    cpu_usage_percent: float

class PerformanceTester:
    """
    Comprehensive performance testing suite for Project Synapse.
    
    Tests:
    - HTTP endpoint response times under load
    - Memory usage during operations
    - CPU utilization patterns
    - Concurrent request handling
    - Resource scaling characteristics
    """
    
    def __init__(self):
        self.endpoints = {
            "primary_health": "http://localhost:8001/health",
            "filesystem_health": "http://localhost:8002/health", 
            "primary_search": "http://localhost:8001/tools/search_web",
            "filesystem_save": "http://localhost:8002/tools/save_file",
            "rabbitmq_overview": "http://localhost:15672/api/overview"
        }
        
        self.test_payloads = {
            "search_simple": {"query": "machine learning", "max_results": 3},
            "search_complex": {"query": "quantum computing cryptography blockchain artificial intelligence", "max_results": 5},
            "file_save_small": {"file_path": "/app/output/perf_test_small.txt", "content": "Small test file"},
            "file_save_large": {"file_path": "/app/output/perf_test_large.txt", "content": "Large test content\n" * 1000}
        }

    async def measure_response_time(self, session: aiohttp.ClientSession, 
                                  url: str, method: str = "GET", 
                                  payload: Optional[Dict] = None,
                                  auth: Optional[aiohttp.BasicAuth] = None) -> Tuple[float, bool, str]:
        """Measure single request response time."""
        start_time = time.time()
        error_msg = ""
        success = False
        
        try:
            if method == "GET":
                async with session.get(url, auth=auth) as resp:
                    await resp.text()
                    success = resp.status < 400
                    if not success:
                        error_msg = f"HTTP {resp.status}"
            else:  # POST
                async with session.post(url, json=payload, auth=auth) as resp:
                    await resp.text()
                    success = resp.status < 400
                    if not success:
                        error_msg = f"HTTP {resp.status}"
                        
        except Exception as e:
            error_msg = str(e)
            
        duration = time.time() - start_time
        return duration, success, error_msg

    def get_system_metrics(self) -> Tuple[float, float]:
        """Get current system resource usage."""
        try:
            # Get memory usage of Python processes
            memory_mb = 0
            cpu_percent = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        memory_mb += proc.info['memory_info'].rss / 1024 / 1024
                        cpu_percent += proc.info['cpu_percent'] or 0
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            return memory_mb, cpu_percent
        except Exception:
            return 0.0, 0.0

    async def run_load_test(self, test_name: str, url: str, method: str = "GET",
                          payload: Optional[Dict] = None, auth: Optional[aiohttp.BasicAuth] = None,
                          concurrent_requests: int = 10, total_requests: int = 100) -> PerformanceMetrics:
        """Run load test against specific endpoint."""
        print(f"  🔄 Running {test_name} ({concurrent_requests} concurrent, {total_requests} total)")
        
        response_times = []
        errors = []
        successful_requests = 0
        
        start_time = time.time()
        start_memory, start_cpu = self.get_system_metrics()
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def bounded_request(session):
            async with semaphore:
                duration, success, error = await self.measure_response_time(
                    session, url, method, payload, auth
                )
                return duration, success, error
        
        # Run all requests
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=50)
        ) as session:
            tasks = [bounded_request(session) for _ in range(total_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            else:
                duration, success, error = result
                response_times.append(duration)
                if success:
                    successful_requests += 1
                elif error:
                    errors.append(error)
        
        end_time = time.time()
        end_memory, end_cpu = self.get_system_metrics()
        
        # Calculate metrics
        total_duration = end_time - start_time
        avg_memory = (start_memory + end_memory) / 2
        avg_cpu = (start_cpu + end_cpu) / 2
        
        if response_times:
            avg_response = statistics.mean(response_times)
            min_response = min(response_times)
            max_response = max(response_times)
            p95_response = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 5 else max_response
        else:
            avg_response = min_response = max_response = p95_response = 0.0
        
        rps = successful_requests / total_duration if total_duration > 0 else 0.0
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        
        return PerformanceMetrics(
            test_name=test_name,
            total_requests=total_requests,
            duration=total_duration,
            avg_response_time=avg_response,
            min_response_time=min_response,
            max_response_time=max_response,
            p95_response_time=p95_response,
            requests_per_second=rps,
            success_rate=success_rate,
            errors=errors[:10],  # Limit to first 10 errors
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu
        )

    async def test_endpoint_performance(self) -> List[PerformanceMetrics]:
        """Test performance of all key endpoints."""
        print("🎯 Testing Endpoint Performance...")
        
        test_configs = [
            # Health checks - light load
            ("Primary Health Check", self.endpoints["primary_health"], "GET", None, None, 5, 20),
            ("Filesystem Health Check", self.endpoints["filesystem_health"], "GET", None, None, 5, 20),
            
            # Search endpoints - medium load
            ("Simple Search", self.endpoints["primary_search"], "POST", self.test_payloads["search_simple"], None, 10, 50),
            ("Complex Search", self.endpoints["primary_search"], "POST", self.test_payloads["search_complex"], None, 8, 40),
            
            # File operations - heavy load
            ("Small File Save", self.endpoints["filesystem_save"], "POST", self.test_payloads["file_save_small"], None, 15, 60),
            ("Large File Save", self.endpoints["filesystem_save"], "POST", self.test_payloads["file_save_large"], None, 5, 20),
            
            # RabbitMQ API
            ("RabbitMQ API", self.endpoints["rabbitmq_overview"], "GET", None, aiohttp.BasicAuth("synapse", "synapse123"), 3, 15)
        ]
        
        results = []
        for test_name, url, method, payload, auth, concurrent, total in test_configs:
            try:
                metrics = await self.run_load_test(test_name, url, method, payload, auth, concurrent, total)
                results.append(metrics)
                print(f"    ✅ {test_name}: {metrics.avg_response_time*1000:.1f}ms avg, {metrics.requests_per_second:.1f} RPS")
            except Exception as e:
                print(f"    ❌ {test_name} failed: {e}")
        
        return results

    def get_docker_stats(self) -> Dict[str, Dict]:
        """Get Docker container resource usage."""
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                return {}
            
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            stats = {}
            
            for line in lines:
                parts = line.split('\t')
                if len(parts) >= 4:
                    container = parts[0]
                    cpu = parts[1].replace('%', '')
                    memory = parts[2]
                    network = parts[3]
                    
                    stats[container] = {
                        'cpu_percent': cpu,
                        'memory_usage': memory,
                        'network_io': network
                    }
            
            return stats
        except Exception as e:
            print(f"    ⚠️  Could not get Docker stats: {e}")
            return {}

    def generate_performance_report(self, metrics: List[PerformanceMetrics], docker_stats: Dict) -> str:
        """Generate comprehensive performance report."""
        report_time = datetime.now().isoformat()
        
        report = f"""
# Project Synapse Performance Report
Generated: {report_time}

## Executive Summary
Performance baseline established for Phase 2 optimization analysis.

## Endpoint Performance Metrics

| Test | Avg Response (ms) | P95 Response (ms) | RPS | Success Rate | Memory (MB) |
|------|-------------------|-------------------|-----|--------------|-------------|
"""
        
        for metric in metrics:
            report += f"| {metric.test_name} | {metric.avg_response_time*1000:.1f} | {metric.p95_response_time*1000:.1f} | {metric.requests_per_second:.1f} | {metric.success_rate*100:.1f}% | {metric.memory_usage_mb:.1f} |\n"
        
        report += "\n## Performance Analysis\n\n"
        
        # Find fastest and slowest endpoints
        fastest = min(metrics, key=lambda m: m.avg_response_time)
        slowest = max(metrics, key=lambda m: m.avg_response_time)
        
        report += f"**Fastest Endpoint**: {fastest.test_name} ({fastest.avg_response_time*1000:.1f}ms avg)\n"
        report += f"**Slowest Endpoint**: {slowest.test_name} ({slowest.avg_response_time*1000:.1f}ms avg)\n\n"
        
        # Identify optimization opportunities
        report += "## Optimization Opportunities\n\n"
        
        slow_endpoints = [m for m in metrics if m.avg_response_time > 0.5]  # > 500ms
        if slow_endpoints:
            report += "**Slow Endpoints (>500ms)**:\n"
            for endpoint in slow_endpoints:
                report += f"- {endpoint.test_name}: {endpoint.avg_response_time*1000:.1f}ms\n"
        
        high_memory = [m for m in metrics if m.memory_usage_mb > 100]
        if high_memory:
            report += "\n**High Memory Usage (>100MB)**:\n"
            for endpoint in high_memory:
                report += f"- {endpoint.test_name}: {endpoint.memory_usage_mb:.1f}MB\n"
        
        error_endpoints = [m for m in metrics if m.success_rate < 1.0]
        if error_endpoints:
            report += "\n**Endpoints with Errors**:\n"
            for endpoint in error_endpoints:
                report += f"- {endpoint.test_name}: {endpoint.success_rate*100:.1f}% success rate\n"
                if endpoint.errors:
                    report += f"  Errors: {', '.join(endpoint.errors[:3])}\n"
        
        # Docker container stats
        if docker_stats:
            report += "\n## Container Resource Usage\n\n"
            report += "| Container | CPU % | Memory | Network I/O |\n"
            report += "|-----------|-------|--------|-------------|\n"
            for container, stats in docker_stats.items():
                report += f"| {container} | {stats['cpu_percent']} | {stats['memory_usage']} | {stats['network_io']} |\n"
        
        report += "\n## Recommendations\n\n"
        report += "1. **Response Time Optimization**: Focus on endpoints >200ms average\n"
        report += "2. **Memory Optimization**: Monitor containers using >100MB consistently\n"
        report += "3. **Error Handling**: Investigate any endpoints with <100% success rate\n"
        report += "4. **Scaling Preparation**: Current performance suitable for development/testing\n"
        report += "5. **Production Tuning**: Consider connection pooling, caching, and async optimizations\n"
        
        return report

async def main():
    """Run complete performance testing suite."""
    print("🚀 Project Synapse Performance Testing Suite")
    print("=" * 60)
    print("Phase 2: Performance Optimization & Baseline Establishment")
    print("=" * 60)
    
    tester = PerformanceTester()
    
    # Run performance tests
    start_time = time.time()
    endpoint_metrics = await tester.test_endpoint_performance()
    
    # Get Docker statistics
    print("\n📊 Collecting Docker container statistics...")
    docker_stats = tester.get_docker_stats()
    
    # Generate report
    print("\n📝 Generating performance report...")
    report = tester.generate_performance_report(endpoint_metrics, docker_stats)
    
    # Save report
    report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Display summary
    total_time = time.time() - start_time
    print(f"\n📈 Performance testing completed in {total_time:.1f}s")
    print(f"📄 Detailed report saved to: {report_file}")
    
    # Show key metrics
    print("\n🔍 Key Performance Indicators:")
    if endpoint_metrics:
        avg_response = statistics.mean([m.avg_response_time for m in endpoint_metrics])
        total_rps = sum([m.requests_per_second for m in endpoint_metrics])
        overall_success = statistics.mean([m.success_rate for m in endpoint_metrics])
        
        print(f"  📊 Average Response Time: {avg_response*1000:.1f}ms")
        print(f"  🚀 Total Requests/Second: {total_rps:.1f}")
        print(f"  ✅ Overall Success Rate: {overall_success*100:.1f}%")
        
        if avg_response < 0.2:  # < 200ms
            print(f"  🎯 Performance: EXCELLENT")
        elif avg_response < 0.5:  # < 500ms
            print(f"  🎯 Performance: GOOD")
        else:
            print(f"  🎯 Performance: NEEDS OPTIMIZATION")
    
    print("\n✅ Phase 2 Performance Baseline: ESTABLISHED")
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
