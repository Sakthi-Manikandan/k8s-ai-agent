#!/bin/bash
# Deploy K8s AI Agent to Kubernetes cluster

echo "🚀 Deploying K8s AI Agent..."

echo "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

echo "Setting up RBAC..."
kubectl apply -f k8s/serviceaccount.yaml

echo "Creating ConfigMap..."
kubectl apply -f k8s/configmap.yaml

echo "Creating Secrets..."
kubectl apply -f k8s/secret.yaml

echo "Deploying backend..."
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml

echo "Deploying frontend..."
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

echo "✅ Deployment complete!"
echo "Checking status..."
kubectl get all -n k8s-ai-agent