# Deployment Guide

## Quick Start (Local Development)

### Prerequisites
```bash
# Required
Docker Desktop (with Kubernetes enabled)
minikube start --driver=docker
kubectl
Git
Python 3.11

# Optional (for local LLM)
Ollama
ollama pull llama3
```

### Steps (5 minutes)

```bash
# 1. Clone
git clone https://github.com/Sakthiz/k8s-ai-agent.git
cd k8s-ai-agent

# 2. Virtual environment
python -m venv venv
source venv/Scripts/activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Env file
cp .env.example .env

# 5. Start services
docker compose up --build

# 6. Access
# Frontend: http://localhost:8501
# API: http://localhost:8000/docs
```

**Test it:**
```bash
# Terminal 1: Create broken deployment
kubectl create deployment broken-app --image=nginx:wrongtag123

# Terminal 2: Click Investigate in dashboard
# Watch agent detect and diagnose ImagePullBackOff!
```

---

## Production Deployment (Kubernetes)

### Prerequisites

```bash
# Kubernetes cluster (1.24+)
# kubectl access with admin rights
# Docker images built and pushed to registry
# PostgreSQL database (optional but recommended)
```

### Step 1: Build and Push Docker Images

```bash
# Build backend
docker build -f backend/Dockerfile -t your-registry/k8s-ai-agent-backend:v1.0.0 .
docker push your-registry/k8s-ai-agent-backend:v1.0.0

# Build frontend
docker build -f frontend/Dockerfile -t your-registry/k8s-ai-agent-frontend:v1.0.0 .
docker push your-registry/k8s-ai-agent-frontend:v1.0.0
```

### Step 2: Update K8s Manifests

Edit `k8s/backend-deployment.yaml`:
```yaml
image: your-registry/k8s-ai-agent-backend:v1.0.0  # Change this
```

Edit `k8s/frontend-deployment.yaml`:
```yaml
image: your-registry/k8s-ai-agent-frontend:v1.0.0  # Change this
```

### Step 3: Configure Secrets

Create Azure OpenAI secret:
```bash
kubectl create secret generic k8s-ai-agent-secret \
  -n k8s-ai-agent \
  --from-literal=OLLAMA_BASE_URL="https://your-openai.openai.azure.com/" \
  --from-literal=OPENAI_API_KEY="your-key-here" \
  --from-literal=OPENAI_API_VERSION="2023-05-15"
```

Or edit `k8s/secret.yaml` directly.

### Step 4: Deploy to K8s

```bash
# One command deployment!
bash k8s/deploy.sh

# Or manually:
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

# Verify
kubectl get all -n k8s-ai-agent
```

### Step 5: Access the Agent

```bash
# Port forward (local testing)
kubectl port-forward -n k8s-ai-agent \
  svc/k8s-ai-agent-frontend-svc 8501:8501

# Open browser: http://localhost:8501
```

Or expose via Ingress:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: k8s-ai-agent
  namespace: k8s-ai-agent
spec:
  rules:
  - host: k8s-ai-agent.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: k8s-ai-agent-frontend-svc
            port:
              number: 8501
```

---

## Production Checklist

### Security
- [ ] Enable RBAC for agent ServiceAccount
- [ ] Use Secrets for API keys (not ConfigMap)
- [ ] Enable network policies
- [ ] Run containers as non-root
- [ ] Set resource limits
- [ ] Enable pod security policies
- [ ] Scan images for vulnerabilities

### Database
- [ ] Migrate from SQLite to PostgreSQL
- [ ] Enable database backups
- [ ] Set up database replication
- [ ] Monitor database performance
- [ ] Enable database encryption at rest

### Monitoring
- [ ] Deploy Prometheus for metrics
- [ ] Deploy Grafana dashboards
- [ ] Set up alerting (if investigation fails)
- [ ] Monitor agent pod health
- [ ] Track investigation success rate

### Logging
- [ ] Send logs to ELK or CloudWatch
- [ ] Structured logging (JSON)
- [ ] Log retention policy
- [ ] Log alerting rules

### High Availability
- [ ] Run multiple backend replicas
- [ ] Use PodDisruptionBudget
- [ ] Auto-scale backend based on load
- [ ] Use ReadinessProbe
- [ ] Use LivenessProbe

---

## Troubleshooting

### Investigation Not Saving

**Problem:** Dashboard shows "0 investigations"

**Solution:**
```bash
# Check database file exists
ls -la data/investigations.db

# Check database tables
sqlite3 data/investigations.db ".tables"

# Check logs
kubectl logs -n k8s-ai-agent deployment/k8s-ai-agent-backend

# Reinitialize database
python -c "from backend.db.database import init_database; init_database()"
```

### Agent Can't Access Cluster

**Problem:** Pod investigation fails with "connection refused"

**Solution:**
```bash
# Verify RBAC binding
kubectl get clusterrolebinding | grep k8s-ai-agent

# Verify ServiceAccount mounted correctly
kubectl get sa -n k8s-ai-agent

# Test with kubectl from agent pod
kubectl exec -it pod/k8s-ai-agent-backend-xxx \
  -n k8s-ai-agent -- \
  kubectl get pods -A
```

### AI Diagnosis Not Working

**Problem:** Investigation completes but diagnosis is empty

**Solution:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check model is loaded
ollama list

# Check backend logs
kubectl logs -n k8s-ai-agent deployment/k8s-ai-agent-backend

# Test LLM directly
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3","messages":[{"role":"user","content":"test"}]}'
```

### Frontend Can't Connect to Backend

**Problem:** Dashboard shows "Failed to connect to API"

**Solution:**
```bash
# Check backend service
kubectl get svc -n k8s-ai-agent

# Check backend is running
kubectl get pods -n k8s-ai-agent

# Check service endpoints
kubectl get endpoints -n k8s-ai-agent k8s-ai-agent-backend-svc

# Test connectivity
kubectl run -it --rm debug --image=curlimages/curl -- \
  curl http://k8s-ai-agent-backend-svc:8000/api/v1/health
```

---

## Scaling

### Horizontal Scaling (Multiple Replicas)

Update `k8s/backend-deployment.yaml`:
```yaml
spec:
  replicas: 3  # Increase from 1
```

Then redeploy:
```bash
kubectl apply -f k8s/backend-deployment.yaml
```

### Vertical Scaling (More Resources)

Update resource limits:
```yaml
resources:
  requests:
    memory: "512Mi"  # Increase from 256Mi
    cpu: "500m"      # Increase from 250m
  limits:
    memory: "1Gi"    # Increase from 512Mi
    cpu: "1000m"     # Increase from 500m
```

---

## Updates and Rollbacks

### Rolling Update

```bash
# Update image
kubectl set image deployment/k8s-ai-agent-backend \
  k8s-ai-agent-backend=your-registry/k8s-ai-agent-backend:v1.1.0 \
  -n k8s-ai-agent

# Watch rollout
kubectl rollout status deployment/k8s-ai-agent-backend \
  -n k8s-ai-agent

# Check history
kubectl rollout history deployment/k8s-ai-agent-backend \
  -n k8s-ai-agent
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/k8s-ai-agent-backend \
  -n k8s-ai-agent

# Rollback to specific revision
kubectl rollout undo deployment/k8s-ai-agent-backend \
  --to-revision=2 \
  -n k8s-ai-agent
```

---

## Upgrade Steps (v1.0 → v2.0)

```bash
# 1. Backup database
kubectl exec -n k8s-ai-agent \
  pod/k8s-ai-agent-backend-xxx \
  -- cp -r /app/data /app/data-backup

# 2. Pull new images
docker pull your-registry/k8s-ai-agent-backend:v2.0.0
docker pull your-registry/k8s-ai-agent-frontend:v2.0.0

# 3. Update manifests
# Edit k8s/backend-deployment.yaml and frontend-deployment.yaml
# Change image tags to v2.0.0

# 4. Apply updates
kubectl apply -f k8s/

# 5. Verify
kubectl get pods -n k8s-ai-agent
kubectl logs -n k8s-ai-agent deployment/k8s-ai-agent-backend

# 6. Test
# Open dashboard and run investigation
# Verify history still shows old investigations
```

---

## Monitoring in Production

### Health Checks

```bash
# Check backend health
kubectl exec -n k8s-ai-agent \
  pod/k8s-ai-agent-backend-xxx \
  -- curl http://localhost:8000/api/v1/health

# Check frontend health
kubectl exec -n k8s-ai-agent \
  pod/k8s-ai-agent-frontend-xxx \
  -- curl http://localhost:8501/_stcore/health
```

### Logs

```bash
# View logs
kubectl logs -n k8s-ai-agent deployment/k8s-ai-agent-backend -f

# Search for errors
kubectl logs -n k8s-ai-agent \
  deployment/k8s-ai-agent-backend \
  | grep ERROR

# View previous pod logs (if crashed)
kubectl logs -n k8s-ai-agent \
  deployment/k8s-ai-agent-backend \
  --previous
```

### Metrics

```bash
# Check resource usage
kubectl top pod -n k8s-ai-agent

# Check disk space
kubectl exec -n k8s-ai-agent \
  pod/k8s-ai-agent-backend-xxx \
  -- df -h /app/data
```

---

## Database Migration (SQLite → PostgreSQL)

For production, migrate to PostgreSQL:

```bash
# 1. Set up PostgreSQL
# Option A: On cluster
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  --set auth.postgresPassword=secure-password \
  -n k8s-ai-agent

# Option B: Cloud (RDS, CloudSQL, etc.)

# 2. Update backend settings
export DB_URL="postgresql://user:pass@postgres:5432/k8s_ai_agent"

# 3. Run migrations
python -m alembic upgrade head  # (when we add migrations)

# 4. Export SQLite data
python scripts/migrate_sqlite_to_pg.py

# 5. Update deployment
# Change OLLAMA_BASE_URL to DATABASE_URL in ConfigMap
```

---

## Disaster Recovery

### Backup Strategy

```bash
# Daily backup of database
kubectl create cronjob backup-db --image=postgres:15 \
  --schedule="0 2 * * *" \
  -- bash -c "pg_dump postgres://... > /backups/db-$(date +%Y%m%d).sql"

# Backup to S3
kubectl create secret generic s3-credentials \
  --from-literal=access-key=xxx \
  --from-literal=secret-key=yyy \
  -n k8s-ai-agent
```

### Restore From Backup

```bash
# Restore database from backup
pg_restore -d k8s_ai_agent /backups/db-20240101.sql

# Restart agent
kubectl rollout restart deployment/k8s-ai-agent-backend \
  -n k8s-ai-agent
```

---

## Cost Optimization

### Right-sizing Resources

```yaml
# Current
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

# Can reduce to (for POC)
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "250m"
```

### Storage Optimization

```bash
# Check database size
kubectl exec -n k8s-ai-agent \
  pod/k8s-ai-agent-backend-xxx \
  -- du -sh /app/data

# Archive old investigations (>6 months)
# Delete: kubectl delete investigation --before=6m
```

---

## Summary

**Deployment Checklist:**
- [x] Build and push Docker images
- [x] Update manifests with registry
- [x] Deploy to Kubernetes
- [x] Verify agent is running
- [x] Configure monitoring
- [x] Set up backups
- [x] Test failover
- [x] Document runbooks

**Go live with confidence! 🚀**