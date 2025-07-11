# Production Deployment Guide

## 🚀 Project Synapse Production Deployment

This guide covers deploying Project Synapse in a production environment using Kubernetes with comprehensive monitoring.

### Prerequisites

#### Required Software
- Docker Engine 20.10+
- Kubernetes cluster (1.24+)
- kubectl configured
- Git

#### Hardware Requirements
- **Minimum**: 4 CPU cores, 8GB RAM, 20GB storage
- **Recommended**: 8 CPU cores, 16GB RAM, 50GB storage

### Deployment Options

## Option 1: Docker Compose (Development/Testing)

```bash
# Clone repository
git clone https://github.com/YanCotta/project-synapse.git
cd project-synapse

# Deploy with monitoring stack
docker-compose -f docker-compose.optimized.yml up --build

# Access services
# - Grafana: http://localhost:3000 (admin/synapse123)
# - Prometheus: http://localhost:9090
# - RabbitMQ: http://localhost:15672 (synapse/synapse123)
```

## Option 2: Kubernetes (Production)

```bash
# Deploy to cluster
./k8s/deploy.sh

# Verify deployment
kubectl get pods -n project-synapse

# Access monitoring
kubectl port-forward svc/grafana 3000:3000
kubectl port-forward svc/prometheus 9090:9090
```

### Monitoring & Observability

#### Metrics Available
- **HTTP Request Latency**: P50, P95, P99 percentiles
- **Request Rate**: Requests per second by service
- **Agent Task Processing**: Tasks processed by agent type
- **RabbitMQ Queue Depth**: Message queue monitoring
- **Resource Utilization**: CPU, memory, network usage

#### Grafana Dashboards
Pre-configured dashboards include:
- API Performance Overview
- Agent Activity Monitoring  
- Infrastructure Resource Usage
- RabbitMQ Message Flow

#### Alerting (Optional)
Configure alerts for:
- High request latency (>5s)
- Queue depth exceeding threshold
- Agent failure detection
- Resource exhaustion warnings

### Security Considerations

#### Network Security
- All inter-service communication within cluster network
- No external ports exposed except monitoring interfaces
- TLS termination at ingress (configure separately)

#### Application Security
- MCP Roots filesystem access controls
- Environment-based secret management
- Non-root container execution
- Resource limits enforced

### Scaling Guidelines

#### Horizontal Scaling
- **Primary Server**: Scale based on API load (2-4 replicas recommended)
- **Filesystem Server**: Single replica (shared storage considerations)
- **Agents**: Scale based on workload volume (1-2 replicas typical)
- **RabbitMQ**: Single node for simplicity (cluster for HA)

#### Resource Tuning
```yaml
# Example resource adjustments
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi" 
    cpu: "500m"
```

### Troubleshooting

#### Common Issues
1. **Pods not starting**: Check resource availability and image pull status
2. **Service connectivity**: Verify ConfigMap settings and network policies
3. **Performance issues**: Review metrics and adjust resource limits
4. **Storage problems**: Ensure PersistentVolumes are properly configured

#### Debugging Commands
```bash
# Check pod logs
kubectl logs -l app=project-synapse -n project-synapse

# Debug networking
kubectl exec -it <pod-name> -n project-synapse -- nslookup rabbitmq-service

# Resource usage
kubectl top pods -n project-synapse
```

### Backup & Recovery

#### Data Persistence
- **RabbitMQ**: Configure persistent volumes for message durability
- **Output Files**: Mount shared storage for agent-generated reports
- **Metrics**: Prometheus data retention configuration

#### Backup Strategy
```bash
# Backup Kubernetes manifests
kubectl get all -n project-synapse -o yaml > synapse-backup.yaml

# Export monitoring configuration
kubectl get configmap prometheus-config -o yaml > prometheus-backup.yaml
```

### Maintenance

#### Updates
1. Update container images in deployment manifests
2. Apply rolling updates: `kubectl rollout restart deployment/<name> -n project-synapse`
3. Monitor rollout: `kubectl rollout status deployment/<name> -n project-synapse`

#### Health Monitoring
- Monitor Grafana dashboards for anomalies
- Set up automated health checks
- Configure log aggregation (ELK stack recommended)

### Performance Optimization

#### Production Tuning
- Enable connection pooling (already configured)
- Adjust worker processes based on load
- Configure appropriate resource limits
- Enable metrics collection for optimization insights

#### Load Testing
```bash
# Run performance tests
python scripts/performance_test.py

# Monitor during load
python scripts/monitor_system.py
```

This production deployment provides enterprise-grade reliability, monitoring, and scalability for Project Synapse.
