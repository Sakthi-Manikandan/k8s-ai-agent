from backend.kubernetes.kubectl_executor import execute_kubectl
from backend.core.logger import log


def collect_pod_logs(pod_name: str, namespace: str = "default") -> dict:
    """
    Collects logs from a specific pod.
    Like running: kubectl logs <pod-name> -n <namespace>
    """
    log.info(f"Collecting logs for pod: {pod_name} in {namespace}")

    result = execute_kubectl([
        "kubectl", "logs",
        pod_name,
        "-n", namespace,
        "--tail=50",
        "--timestamps"
    ])

    previous_result = execute_kubectl([
        "kubectl", "logs",
        pod_name,
        "-n", namespace,
        "--tail=50",
        "--previous",
        "--timestamps"
    ])

    error_keywords = [
        "error",
        "exception",
        "fatal",
        "failed",
        "connection refused",
        "cannot connect",
        "missing",
        "not found",
        "permission denied",
        "oomkilled",
        "killed",
        "crash"
    ]

    current_logs = result["output"] if result["success"] else ""
    previous_logs = previous_result["output"] \
        if previous_result["success"] else ""

    error_lines = []
    all_logs = current_logs + "\n" + previous_logs

    for line in all_logs.split("\n"):
        if any(keyword in line.lower() for keyword in error_keywords):
            error_lines.append(line.strip())

    log.info(
        f"Log collection complete for {pod_name}. "
        f"Found {len(error_lines)} error lines"
    )

    return {
        "pod_name": pod_name,
        "namespace": namespace,
        "current_logs": current_logs,
        "previous_logs": previous_logs,
        "error_lines": error_lines,
        "has_errors": len(error_lines) > 0
    }


def collect_logs_for_problematic_pods(problematic_pods: list) -> dict:
    """
    Collects logs for ALL problematic pods found
    by the pod inspector.
    """
    log.info(
        f"Collecting logs for "
        f"{len(problematic_pods)} problematic pods"
    )

    all_logs = {}

    for pod in problematic_pods:
        pod_name = pod["name"]
        namespace = pod["namespace"]
        pod_logs = collect_pod_logs(pod_name, namespace)
        all_logs[pod_name] = pod_logs

    return all_logs