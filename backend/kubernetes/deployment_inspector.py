from backend.kubernetes.kubectl_executor import execute_kubectl
from backend.core.logger import log


def inspect_deployments(namespace: str = "--all-namespaces") -> dict:
    """
    Inspects all deployments and finds unhealthy ones.
    Like running: kubectl get deployments -A
    """
    log.info("Starting deployment inspection...")

    if namespace == "--all-namespaces":
        cmd = [
            "kubectl", "get", "deployments",
            "-A", "-o", "wide"
        ]
    else:
        cmd = [
            "kubectl", "get", "deployments",
            "-n", namespace,
            "-o", "wide"
        ]

    result = execute_kubectl(cmd)

    if not result["success"]:
        log.error("Failed to get deployments from cluster")
        return {
            "success": False,
            "error": result["error"],
            "unhealthy_deployments": [],
            "all_deployments": []
        }

    all_deployments = []
    unhealthy_deployments = []
    lines = result["output"].split("\n")

    for line in lines[1:]:
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) < 5:
            continue

        if namespace == "--all-namespaces":
            dep_namespace = parts[0]
            name = parts[1]
            ready = parts[2]
            up_to_date = parts[3]
            available = parts[4]
        else:
            dep_namespace = namespace
            name = parts[0]
            ready = parts[1]
            up_to_date = parts[2]
            available = parts[3]

        try:
            ready_count, desired_count = ready.split("/")
            ready_count = int(ready_count)
            desired_count = int(desired_count)
        except Exception:
            ready_count = 0
            desired_count = 0

        deployment = {
            "name": name,
            "namespace": dep_namespace,
            "ready": ready,
            "ready_count": ready_count,
            "desired_count": desired_count,
            "up_to_date": up_to_date,
            "available": available,
            "is_healthy": ready_count == desired_count
        }

        all_deployments.append(deployment)

        if ready_count != desired_count:
            log.warning(
                f"Unhealthy deployment: {name} "
                f"in {dep_namespace} - "
                f"Ready: {ready_count}/{desired_count}"
            )
            unhealthy_deployments.append(deployment)

    log.info(
        f"Deployment inspection complete. "
        f"Total: {len(all_deployments)}, "
        f"Unhealthy: {len(unhealthy_deployments)}"
    )

    return {
        "success": True,
        "total_deployments": len(all_deployments),
        "unhealthy_deployments": unhealthy_deployments,
        "all_deployments": all_deployments,
        "has_unhealthy": len(unhealthy_deployments) > 0
    }


def describe_deployment(
    deployment_name: str,
    namespace: str = "default"
) -> dict:
    """
    Gets detailed info about a specific deployment.
    Like running: kubectl describe deployment <name>
    """
    log.info(f"Describing deployment: {deployment_name}")

    result = execute_kubectl([
        "kubectl", "describe", "deployment",
        deployment_name,
        "-n", namespace
    ])

    if not result["success"]:
        log.error(
            f"Failed to describe deployment: {deployment_name}"
        )
        return {
            "success": False,
            "error": result["error"]
        }

    return {
        "success": True,
        "details": result["output"]
    }