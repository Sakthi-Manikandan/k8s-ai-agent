from backend.core.logger import log


def build_system_prompt() -> str:
    """
    System prompt that makes LLM behave like
    a Senior Kubernetes SRE!
    """
    return """You are a Senior Kubernetes SRE (Site Reliability Engineer) 
with 10+ years of experience troubleshooting production Kubernetes clusters.

Your job is to:
1. Analyze Kubernetes investigation data
2. Identify the root cause of failures
3. Suggest practical fixes
4. Provide kubectl commands to resolve issues
5. Give a confidence score for your diagnosis

Always respond in this EXACT JSON format:
{
    "root_cause": "Brief description of the root cause",
    "explanation": "Detailed explanation of what went wrong and why",
    "suggested_fix": "Step by step fix instructions",
    "kubectl_commands": [
        "kubectl command 1",
        "kubectl command 2"
    ],
    "prevention": "How to prevent this in future",
    "confidence": 85
}

Be specific, practical and beginner friendly.
Never give vague answers.
Always base your diagnosis on the evidence provided.
If cluster is healthy, say so clearly."""


def build_investigation_prompt(investigation: dict) -> str:
    """
    Converts investigation data into a
    clear prompt for the LLM!
    """
    log.info("Building investigation prompt...")

    # Extract data from investigation
    summary = investigation.get("summary", {})
    pods = investigation.get("pods", {})
    events = investigation.get("events", {})
    deployments = investigation.get("deployments", {})
    network = investigation.get("network", {})
    logs = investigation.get("logs", {})

    # Build prompt
    prompt = f"""
## Kubernetes Cluster Investigation Report

### Summary
- Total Pods: {summary.get('total_pods', 0)}
- Problematic Pods: {summary.get('problematic_pods', 0)}
- Critical Events: {summary.get('critical_events', 0)}
- Unhealthy Deployments: {summary.get('unhealthy_deployments', 0)}
- Network Issues: {summary.get('network_issues', 0)}
- Cluster Healthy: {summary.get('cluster_healthy', False)}

### Problematic Pods
"""

    # Add problematic pods
    problematic_pods = pods.get("problematic_pods", [])
    if problematic_pods:
        for pod in problematic_pods:
            prompt += f"""
- Pod: {pod['name']}
  Namespace: {pod['namespace']}
  Status: {pod['status']}
  Ready: {pod['ready']}
  Restarts: {pod['restarts']}
"""
    else:
        prompt += "No problematic pods found.\n"

    # Add critical events
    prompt += "\n### Critical Events\n"
    critical_events = events.get("critical_events", [])
    if critical_events:
        for event in critical_events[:10]:  # Max 10 events
            prompt += f"""
- Event: {event['reason']}
  Object: {event['object']}
  Message: {event['message']}
  Type: {event['type']}
"""
    else:
        prompt += "No critical events found.\n"

    # Add unhealthy deployments
    prompt += "\n### Unhealthy Deployments\n"
    unhealthy = deployments.get("unhealthy_deployments", [])
    if unhealthy:
        for dep in unhealthy:
            prompt += f"""
- Deployment: {dep['name']}
  Namespace: {dep['namespace']}
  Ready: {dep['ready']}
  Available: {dep['available']}
"""
    else:
        prompt += "No unhealthy deployments found.\n"

    # Add network issues
    prompt += "\n### Network Issues\n"
    network_issues = network.get("issues", [])
    if network_issues:
        for issue in network_issues:
            prompt += f"""
- Type: {issue['type']}
  Service: {issue['service']}
  Namespace: {issue['namespace']}
  Message: {issue['message']}
"""
    else:
        prompt += "No network issues found.\n"

    # Add pod logs with errors
    prompt += "\n### Pod Logs (Errors Only)\n"
    if logs:
        for pod_name, pod_logs in logs.items():
            error_lines = pod_logs.get("error_lines", [])
            if error_lines:
                prompt += f"\nPod: {pod_name}\n"
                for line in error_lines[:10]:  # Max 10 lines
                    prompt += f"  {line}\n"
    else:
        prompt += "No error logs found.\n"
    
    prompt += """
### Your Task
Based on the investigation data above:
1. Identify the root cause
2. Explain what went wrong
3. Suggest a practical fix
4. Provide kubectl commands
5. Give confidence score

Respond ONLY in the JSON format specified."""

    log.info("Investigation prompt built successfully!")
    return prompt