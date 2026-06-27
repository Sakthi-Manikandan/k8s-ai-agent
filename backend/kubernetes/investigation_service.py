from backend.kubernetes.pod_inspector import inspect_pods
from backend.kubernetes.log_collector import collect_logs_for_problematic_pods
from backend.kubernetes.event_analyzer import analyze_events
from backend.kubernetes.deployment_inspector import inspect_deployments
from backend.kubernetes.network_inspector import inspect_network
from backend.core.logger import log


def run_investigation(namespace: str = "--all-namespaces") -> dict:
    """
    Runs the complete Kubernetes investigation.
    Orchestrates all inspectors and returns
    a complete investigation report!
    """
    log.info("=" * 50)
    log.info("Starting full Kubernetes investigation...")
    log.info("=" * 50)

    investigation = {
        "status": "investigating",
        "pods": {},
        "logs": {},
        "events": {},
        "deployments": {},
        "network": {},
        "summary": {}
    }

    # Step 1 — Check pods
    log.info("Step 1/5: Inspecting pods...")
    pod_results = inspect_pods()
    investigation["pods"] = pod_results

    # Step 2 — Collect logs from problematic pods
    log.info("Step 2/5: Collecting logs...")
    if pod_results.get("problematic_pods"):
        log_results = collect_logs_for_problematic_pods(
            pod_results["problematic_pods"]
        )
        investigation["logs"] = log_results
    else:
        log.info("No problematic pods found")
        investigation["logs"] = {}

    # Step 3 — Analyze events
    log.info("Step 3/5: Analyzing events...")
    event_results = analyze_events()
    investigation["events"] = event_results

    # Step 4 — Inspect deployments
    log.info("Step 4/5: Inspecting deployments...")
    deployment_results = inspect_deployments()
    investigation["deployments"] = deployment_results

    # Step 5 — Check networking
    log.info("Step 5/5: Checking networking...")
    network_results = inspect_network()
    investigation["network"] = network_results

    # Build summary
    investigation["summary"] = {
        "total_pods": pod_results.get("total_pods", 0),
        "problematic_pods": len(
            pod_results.get("problematic_pods", [])
        ),
        "critical_events": len(
            event_results.get("critical_events", [])
        ),
        "unhealthy_deployments": len(
            deployment_results.get("unhealthy_deployments", [])
        ),
        "network_issues": len(
            network_results.get("issues", [])
        ),
        "cluster_healthy": (
            pod_results.get("healthy", True) and
            not event_results.get("has_critical_events", False) and
            not deployment_results.get("has_unhealthy", False) and
            not network_results.get("has_issues", False)
        )
    }

    investigation["status"] = "complete"

    log.info("=" * 50)
    log.info(
        f"Investigation complete! "
        f"Cluster healthy: "
        f"{investigation['summary']['cluster_healthy']}"
    )
    log.info("=" * 50)

    return investigation