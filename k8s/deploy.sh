#!/bin/bash
# Kubernetes Deployment Script for Project Synapse
set -e

echo "🚀 Deploying Project Synapse to Kubernetes"
echo "=========================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✅ Connected to Kubernetes cluster"

# Create namespace if it doesn't exist
kubectl create namespace project-synapse --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Namespace 'project-synapse' ready"

# Apply ConfigMap first
echo "📋 Applying ConfigMap..."
kubectl apply -f k8s/configmap.yaml -n project-synapse

# Apply RabbitMQ
echo "🐰 Deploying RabbitMQ..."
kubectl apply -f k8s/rabbitmq-deployment.yaml -n project-synapse

# Wait for RabbitMQ to be ready
echo "⏳ Waiting for RabbitMQ to be ready..."
kubectl wait --for=condition=ready pod -l component=rabbitmq -n project-synapse --timeout=300s

# Apply MCP Servers
echo "🔧 Deploying MCP Servers..."
kubectl apply -f k8s/primary-server-deployment.yaml -n project-synapse
kubectl apply -f k8s/filesystem-server-deployment.yaml -n project-synapse

# Wait for MCP servers to be ready
echo "⏳ Waiting for MCP servers to be ready..."
kubectl wait --for=condition=ready pod -l component=primary-server -n project-synapse --timeout=300s
kubectl wait --for=condition=ready pod -l component=filesystem-server -n project-synapse --timeout=300s

# Apply Agents
echo "🤖 Deploying Agents..."
kubectl apply -f k8s/agents-deployment.yaml -n project-synapse

# Wait for agents to be ready
echo "⏳ Waiting for agents to be ready..."
kubectl wait --for=condition=ready pod -l component=agents -n project-synapse --timeout=300s

echo ""
echo "🎉 Project Synapse deployed successfully!"
echo ""
echo "📊 Monitoring Information:"
echo "  - Prometheus metrics: kubectl port-forward svc/prometheus 9090:9090 -n monitoring"
echo "  - Grafana dashboard: kubectl port-forward svc/grafana 3000:3000 -n monitoring"
echo ""
echo "🔍 Useful commands:"
echo "  - View logs: kubectl logs -l app=project-synapse -n project-synapse"
echo "  - Get pods: kubectl get pods -n project-synapse"
echo "  - Describe deployment: kubectl describe deployment <name> -n project-synapse"
echo ""
echo "🌐 Access Services:"
echo "  - RabbitMQ Management: kubectl port-forward svc/rabbitmq-service 15672:15672 -n project-synapse"
echo "  - Primary Server: kubectl port-forward svc/primary-server-service 8001:8001 -n project-synapse"
echo "  - Filesystem Server: kubectl port-forward svc/filesystem-server-service 8002:8002 -n project-synapse"
