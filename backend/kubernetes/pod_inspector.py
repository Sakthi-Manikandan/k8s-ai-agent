from backend.kubernetes.kubectl_executor import execute_kubectl
from backend.core.logger import log


UNHEALTHY_STATES = [
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "Pending",
    "Error",
    "OOMKilled",
    "ContainerCreating",
    "ErrImagePull",
    "CreateContainerConfigError"
]


def inspect_pods(namespace: str = "--all-namespaces") -> dict:
    """
    Checks all pods in the cluster and finds unhealthy ones.
    Like running: kubectl get pods -A
    """
    log.info("Starting pod inspection...")

    # Build kubectl command based on namespace
    if namespace == "--all-namespaces":
     cmd = ["kubectl", "get", "pods", "-A", "-o", "wide"]
    else:
     cmd = ["kubectl", "get", "pods", "-n", namespace, "-o", "wide"]

    result = execute_kubectl(cmd)

    if not result["success"]:
        log.error("Failed to get pods from cluster")
        return {
            "healthy": False,
            "error": result["error"],
            "total_pods": 0,
            "problematic_pods": []
        }

    pods = []
    problematic_pods = []
    lines = result["output"].split("\n")

    for line in lines[1:]:
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) < 5:
            continue

        pod_namespace = parts[0]
        pod_name = parts[1]
        ready = parts[2]
        status = parts[3]
        restarts = parts[4]

        pod = {
            "name": pod_name,
            "namespace": pod_namespace,
            "status": status,
            "ready": ready,
            "restarts": restarts
        }

        pods.append(pod)

        is_unhealthy = any(
            state in status
            for state in UNHEALTHY_STATES
        )

        if is_unhealthy or status != "Running":
            log.warning(
                f"Unhealthy pod found: {pod_name} "
                f"in {pod_namespace} "
                f"with status {status}"
            )
            problematic_pods.append(pod)

    log.info(
        f"Pod inspection complete. "
        f"Total: {len(pods)}, "
        f"Problematic: {len(problematic_pods)}"
    )

    return {
        "healthy": len(problematic_pods) == 0,
        "total_pods": len(pods),
        "problematic_pods": problematic_pods,
        "all_pods": pods
    }