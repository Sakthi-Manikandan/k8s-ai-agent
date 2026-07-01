# Architecture Documentation

## System Overview

```
User Interface Layer (Streamlit)
        ↓
API Gateway (FastAPI)
        ↓
Business Logic (Agent Service)
        ├─→ Investigation Layer
        ├─→ AI Reasoning Layer
        ├─→ Remediation Layer
        └─→ Database Layer
```

## Component Deep Dive

### 1. Frontend (Streamlit)

**Location:** `frontend/app.py`

**Responsibilities:**
- Display cluster health metrics
- Show investigation results
- Allow user approval/rejection of actions
- Display investigation history
- Provide namespace selection

**Why Streamlit?**
- Zero frontend engineering needed
- Professional UI in pure Python
- Perfect for internal tools
- Fast iteration

**Key Functions:**
- `call_investigate()` - Makes POST request to backend
- `call_approve()` - Sends approval decision to backend
- `call_history()` - Fetches past investigations

---

### 2. Backend API (FastAPI)

**Location:** `backend/api/routes.py`

**Endpoints:**
```
GET  /api/v1/health           - Health check (K8s probes)
POST /api/v1/investigate      - Start investigation
POST /api/v1/approve          - Approve + execute action
GET  /api/v1/history          - Get investigation history
GET  /api/v1/pipelines        - List active pipelines
```

**Design Pattern:**
- Pipeline-based architecture
- Each request = one investigation pipeline
- Pipeline ID tracks investigation through lifecycle
- In-memory storage for active pipelines
- Database persistence for history

---

### 3. Investigation Layer

**Location:** `backend/kubernetes/`

**Components:**

#### Pod Inspector (`pod_inspector.py`)
```
kubectl get pods -n namespace -o wide
        ↓
Parse output and detect:
  ✗ CrashLoopBackOff
  ✗ ImagePullBackOff
  ✗ Pending
  ✗ Error
  ✗ OOMKilled
        ↓
Return: {healthy, total_pods, problematic_pods}
```

#### Event Analyzer (`event_analyzer.py`)
```
kubectl get events -A --sort-by=.lastTimestamp
        ↓
Detect critical events:
  ✗ FailedScheduling
  ✗ BackOff
  ✗ FailedPull
  ✗ OOMKilling
        ↓
Return: {critical_events, has_critical_events}
```

#### Log Collector (`log_collector.py`)
```
For each problematic pod:
  kubectl logs pod-name --tail=50
  kubectl logs pod-name --previous (if crashed)
        ↓
Scan for error keywords:
  error, exception, fatal, failed, etc.
        ↓
Return: {pod_logs with error details}
```

#### Deployment Inspector (`deployment_inspector.py`)
```
kubectl get deployments -n namespace
        ↓
Parse: ready count vs desired count
  Example: "1/3" = 1 ready, 3 desired
        ↓
Detect unhealthy:
  ready_count != desired_count
        ↓
Return: {unhealthy_deployments}
```

#### Network Inspector (`network_inspector.py`)
```
kubectl get svc -A
kubectl get endpoints -A
        ↓
Detect network issues:
  ✗ Service with no selector
  ✗ Service with empty endpoints
        ↓
Return: {network_issues}
```

#### Investigation Service (`investigation_service.py`)
```
Orchestrates all 5 inspectors in order:
  1. Inspect pods
  2. Collect logs (if issues found)
  3. Analyze events
  4. Inspect deployments
  5. Inspect networking
        ↓
Combine results into single investigation dict
        ↓
Return: {summary, detailed findings}
```

---

### 4. AI Reasoning Layer

**Location:** `backend/ai/`

#### Prompt Builder (`prompt_builder.py`)
```
Creates two prompts:

System Prompt:
"You are a senior K8s SRE with 10 years experience.
Analyze investigations and diagnose root causes.
Respond ONLY in JSON: {root_cause, explanation, ...}"

Investigation Prompt:
"Here's a cluster investigation:
- Pods: [list of problematic pods]
- Events: [critical events]
- Logs: [error messages]
- Deployments: [unhealthy deployments]

Diagnose the root cause."
```

#### LLM Client (`llm_client.py`)
```
POST to http://localhost:11434/api/chat (Ollama)
        ↓
Payload:
{
  "model": "llama3",
  "messages": [system_prompt, investigation_prompt],
  "temperature": 0.1,  # Deterministic
  "seed": 42,           # Reproducible
  "format": "json"      # Force JSON response
}
        ↓
Parse JSON response with diagnosis
```

#### Reasoning Engine (`reasoning_engine.py`)
```
Orchestrates prompt building + LLM call
        ↓
Returns: {root_cause, explanation, confidence, suggested_fix}
```

**Why Llama3?**
- **Free** — No API costs
- **Local** — No latency, privacy preserved
- **Easy to swap** — Change 2 lines to use OpenAI
- **Deterministic** — temperature=0.1, seed=42

---

### 5. Remediation Layer

**Location:** `backend/kubernetes/remediation.py`

**Remediation Actions:**

```
Action Type: restart_pod
├─ Trigger: CrashLoopBackOff, OOMKilled
├─ Command: kubectl delete pod {name} -n {namespace}
└─ Risk: LOW

Action Type: restart_deployment
├─ Trigger: Unhealthy deployment (0/N ready)
├─ Command: kubectl rollout restart deployment {name}
└─ Risk: MEDIUM

Action Type: fix_image
├─ Trigger: ImagePullBackOff, ErrImagePull
├─ Command: kubectl set image deployment/{name} {name}={correct}:{tag}
├─ Risk: HIGH
└─ Requires: Manual input (user provides correct tag)
```

**Approval Flow:**
```
1. generate_suggested_actions()
   → Maps findings to actions
   → Sets approved=False
   → Returns to frontend

2. User reviews in dashboard
   → Sees kubectl command
   → Reviews risk level
   → Clicks Approve or Reject

3. execute_approved_action()
   → Checks approved=True
   → Executes kubectl command
   → Returns result

4. save_action()
   → Records to database
   → Timestamp
   → Result
```

---

### 6. Database Layer

**Location:** `backend/db/`

**Schema:**

```sql
Table: investigations
├─ id (TEXT PRIMARY KEY)         # UUID
├─ timestamp (TEXT)              # ISO datetime
├─ namespace (TEXT)              # Namespace searched
├─ status (TEXT)                 # complete, error
├─ total_pods (INT)              # Total pods found
├─ problematic_pods (INT)        # Pods with issues
├─ critical_events (INT)         # Critical K8s events
├─ network_issues (INT)          # Network problems
├─ cluster_healthy (BOOL)        # Overall health
├─ root_cause (TEXT)             # AI diagnosis
├─ confidence (INT)              # 0-100
├─ suggested_fix (TEXT)          # What to do
├─ raw_diagnosis (TEXT)          # Full AI response
└─ created_at (DATETIME)         # Insert time

Table: actions
├─ id (INT PRIMARY KEY)
├─ investigation_id (FK)         # Links to investigation
├─ action_type (TEXT)            # restart_pod, etc.
├─ reason (TEXT)                 # Why this action
├─ command (TEXT)                # kubectl command
├─ risk (TEXT)                   # LOW, MEDIUM, HIGH
├─ approved (BOOL)               # User approved?
├─ executed (BOOL)               # Actually ran?
├─ result (TEXT)                 # kubectl output
└─ timestamp (DATETIME)          # When executed
```

**Queries:**
```python
# Save investigation
save_investigation(pipeline_id, namespace, result)

# Save action
save_action(investigation_id, action, approved, result)

# Get history (last 20 investigations)
get_recent_investigations(limit=20)

# Get statistics
get_investigation_stats()
  → {total, unhealthy, avg_confidence, last_investigation}
```

---

## Data Flow

### Complete Investigation Flow

```
1. USER ACTION
   User opens dashboard
   Selects namespace "default"
   Clicks "Investigate Cluster"
        ↓
2. FASTAPI RECEIVES REQUEST
   POST /api/v1/investigate
   Body: {namespace: "default"}
   Generates pipeline_id (UUID)
        ↓
3. INVESTIGATION SERVICE
   run_investigation(namespace="default")
   Calls 5 inspectors in sequence
   Combines results
        ↓
4. POD INSPECTOR
   kubectl get pods -n default -o wide
   Detects 2 pods in CrashLoopBackOff
        ↓
5. EVENT ANALYZER
   kubectl get events -A
   Finds 6 FailedScheduling events
        ↓
6. LOG COLLECTOR
   kubectl logs pod-name --tail=50
   Finds error: "image pull failed"
        ↓
7. DEPLOYMENT INSPECTOR
   kubectl get deployments -n default
   Found 1 unhealthy deployment
        ↓
8. NETWORK INSPECTOR
   kubectl get svc
   Found 1 service with no selector
        ↓
9. AI REASONING
   Build prompt with all findings
   POST to Ollama/OpenAI
   Get diagnosis: "Image pull failure from wrong tag"
   Confidence: 95%
        ↓
10. REMEDIATION SUGGESTIONS
    Map findings to actions:
    - Action 1: restart_pod
    - Action 2: restart_deployment
        ↓
11. DATABASE SAVE
    INSERT into investigations table
    INSERT into actions table (all marked unapproved)
        ↓
12. RETURN TO FRONTEND
    Status: success
    Pipeline ID: abc-123-def
    Investigation results
    Suggested actions
        ↓
13. FRONTEND DISPLAYS
    Shows cluster summary
    Shows AI diagnosis
    Shows suggested actions
    Shows Approve/Reject buttons
        ↓
14. USER APPROVES
    Clicks "Approve" on action 1
    POST /api/v1/approve
    Body: {pipeline_id: "abc-123-def", action_index: 0}
        ↓
15. EXECUTE ACTION
    Mark action as approved=True
    Run: kubectl delete pod broken-app-xxx
        ↓
16. SAVE RESULT
    UPDATE actions table
    Set executed=True, result="Pod deleted successfully"
        ↓
17. RETURN SUCCESS
    Frontend shows: "✅ Action executed!"
        ↓
18. QUERY HISTORY
    GET /api/v1/history
    Returns past 20 investigations from database
    Dashboard shows: "1 investigation in database"
```

---

## Design Patterns

### 1. Separation of Concerns
- **Inspectors** — Only gather data
- **AI Engine** — Only reason
- **Remediation** — Only execute
- **Database** — Only persist

### 2. Human-in-the-Loop
- Agent never acts without approval
- Every action requires explicit approval
- Full audit trail

### 3. Pipeline Pattern
- Each investigation = one pipeline
- Pipeline ID tracks through lifecycle
- Results stored in memory during session
- Results persisted in database

### 4. Least Privilege (RBAC)
```yaml
ClusterRole:
  rules:
  - apiGroups: [""]
    resources: [pods, events, services]
    verbs: [get, list, watch]     # READ only
  - apiGroups: [""]
    resources: [pods]
    verbs: [delete]               # DELETE pods only
  - apiGroups: ["apps"]
    resources: [deployments]
    verbs: [patch, update]        # PATCH deployments
```

---

## Error Handling

### Investigation Failures
```python
If kubectl fails:
  → Log error
  → Return {success: False, error: "..."}
  → Frontend shows error message
  → User can retry

If AI fails:
  → Log error
  → Return {success: False, error: "..."}
  → Frontend shows error message

If database fails:
  → Log warning
  → Continue (investigation still works)
  → User can still approve/reject
  → History might be missing
```

### Action Execution Failures
```python
If kubectl execution fails:
  → Log error
  → Return {success: False, error: "..."}
  → Frontend shows error
  → User can retry
  → Database records failure
```

---

## Performance Considerations

### Investigation Speed
```
pod_inspector:     ~500ms (depends on pod count)
event_analyzer:    ~300ms
log_collector:     ~1-2s  (depends on log size)
deployment_inspect:~300ms
network_inspect:   ~300ms
AI reasoning:      ~2-5s  (depends on model)
─────────────────
Total:             ~5-10 seconds
```

**Optimization opportunities:**
- Run inspectors in parallel (not sequential)
- Cache results between investigations
- Use incremental investigation (only changed resources)

### Database Performance
```
SQLite sufficient for:
  - <1000 investigations (typical POC)
  - <10,000 actions
  - <10 concurrent users

Migrate to PostgreSQL when:
  - >10,000 investigations
  - >100 concurrent users
  - Need distributed queries
```

---

## Security Architecture

### Authentication (Future)
```
OAuth2 → Verify user identity
RBAC → Control what user can do
Audit Log → Track user actions
```

### Authorization (Now)
```
ServiceAccount → Agent's identity
ClusterRole → What agent can do
ClusterRoleBinding → Bind them
Namespace → Isolate agent
```

### Secrets Management (Now)
```
ConfigMap → Non-sensitive config
Secret → Sensitive data (keys, tokens)
Never in code or environment files
```

---

## Deployment Architectures

### Local (POC)
```
Docker Desktop
    ↓
docker compose up
    ↓
Backend (8000) + Frontend (8501)
    ↓
Accesses minikube cluster
```

### Production (K8s)
```
Push to registry
    ↓
kubectl apply -f k8s/
    ↓
Agent pod in k8s-ai-agent namespace
    ↓
Uses ServiceAccount RBAC
    ↓
Persistent database (PostgreSQL)
    ↓
Monitored by Prometheus
```

---

## Future Architecture Changes

### Multi-Cluster
```
Single frontend
    ↓
Multiple backends (one per cluster)
    ↓
Unified database
    ↓
Investigate all clusters from one UI
```

### Incident Correlation
```
Investigation 1: Pod restart failed
Investigation 2: Network latency spike
Investigation 3: Database connections timeout
    ↓
AI groups them as related
    ↓
Suggests root cause: "Network partition"
```

### Custom Runbooks
```
Investigation result
    ↓
Matches against runbook database
    ↓
Suggests company-specific remediation
    ↓
Links to documentation
```

---

## Summary

**K8s AI Agent Architecture:**
1. **Layered** — Each layer has single responsibility
2. **Autonomous** — Gathers data automatically
3. **Safe** — Humans approve all actions
4. **Observable** — Full audit trail
5. **Scalable** — Easy to extend inspectors/actions
6. **Production-Ready** — Health checks, RBAC, monitoring-ready