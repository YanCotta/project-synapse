
# Project Synapse Performance Report
Generated: 2025-07-11T09:57:55.199978

## Executive Summary
Performance baseline established for Phase 2 optimization analysis.

## Endpoint Performance Metrics

| Test | Avg Response (ms) | P95 Response (ms) | RPS | Success Rate | Memory (MB) |
|------|-------------------|-------------------|-----|--------------|-------------|
| Primary Health Check | 0.9 | 3.5 | 668.4 | 100.0% | 130.7 |
| Filesystem Health Check | 0.8 | 2.1 | 882.7 | 100.0% | 131.2 |
| Simple Search | 501.8 | 503.2 | 19.8 | 100.0% | 131.4 |
| Complex Search | 501.2 | 502.8 | 15.8 | 100.0% | 131.5 |
| Small File Save | 5.3 | 13.2 | 1447.2 | 100.0% | 131.8 |
| Large File Save | 2.2 | 3.7 | 707.9 | 100.0% | 132.2 |
| RabbitMQ API | 1.4 | 2.6 | 557.0 | 100.0% | 132.3 |

## Performance Analysis

**Fastest Endpoint**: Filesystem Health Check (0.8ms avg)
**Slowest Endpoint**: Simple Search (501.8ms avg)

## Optimization Opportunities

**Slow Endpoints (>500ms)**:
- Simple Search: 501.8ms
- Complex Search: 501.2ms

**High Memory Usage (>100MB)**:
- Primary Health Check: 130.7MB
- Filesystem Health Check: 131.2MB
- Simple Search: 131.4MB
- Complex Search: 131.5MB
- Small File Save: 131.8MB
- Large File Save: 132.2MB
- RabbitMQ API: 132.3MB

## Recommendations

1. **Response Time Optimization**: Focus on endpoints >200ms average
2. **Memory Optimization**: Monitor containers using >100MB consistently
3. **Error Handling**: Investigate any endpoints with <100% success rate
4. **Scaling Preparation**: Current performance suitable for development/testing
5. **Production Tuning**: Consider connection pooling, caching, and async optimizations
