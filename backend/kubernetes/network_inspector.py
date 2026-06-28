from backend.kubernetes.kubectl_executor import execute_kubectl
from backend.core.logger import log


def inspect_network(namespace: str = "--all-namespaces") -> dict:
    """
    Inspects services and networking in the cluster.
    Like running: kubectl get svc -A
    """
    log.info("Starting network inspection...")

    if namespace == "--all-namespaces":
        services_result = execute_kubectl([
            "kubectl", "get", "svc",
            "-A", "-o", "wide"
        ])
        endpoints_result = execute_kubectl([
            "kubectl", "get", "endpoints",
            "-A"
        ])
    else:
        services_result = execute_kubectl([
            "kubectl", "get", "svc",
            "-n", namespace,
            "-o", "wide"
        ])
        endpoints_result = execute_kubectl([
            "kubectl", "get", "endpoints",
            "-n", namespace
        ])

    if not services_result["success"]:
        log.error("Failed to get services from cluster")
        return {
            "success": False,
            "error": services_result["error"],
            "services": [],
            "issues": []
        }

    services = []
    issues = []
    lines = services_result["output"].split("\n")

    for line in lines[1:]:
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) < 5:
            continue

        if namespace == "--all-namespaces":
            service = {
                "namespace": parts[0],
                "name": parts[1],
                "type": parts[2],
                "cluster_ip": parts[3],
                "ports": parts[4],
                "selector": parts[-1] if len(parts) > 5 else "none"
            }
        else:
            service = {
                "namespace": namespace,
                "name": parts[0],
                "type": parts[1],
                "cluster_ip": parts[2],
                "ports": parts[3],
                "selector": parts[-1] if len(parts) > 4 else "none"
            }

        services.append(service)

        if service["selector"] == "none" or \
                service["selector"] == "<none>":
            log.warning(
                f"Service with no selector: "
                f"{service['name']} in "
                f"{service['namespace']}"
            )
            issues.append({
                "type": "NoSelector",
                "service": service["name"],
                "namespace": service["namespace"],
                "message": "Service has no selector - "
                           "traffic will not reach any pod!"
            })

    if endpoints_result["success"]:
        endpoint_lines = endpoints_result["output"].split("\n")

        for line in endpoint_lines[1:]:
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            if namespace == "--all-namespaces":
                ep_namespace = parts[0]
                name = parts[1]
                endpoints = parts[2]
            else:
                ep_namespace = namespace
                name = parts[0]
                endpoints = parts[1] if len(parts) > 1 else "<none>"

            if endpoints == "<none>":
                log.warning(
                    f"Empty endpoints for service: "
                    f"{name} in {ep_namespace}"
                )
                issues.append({
                    "type": "SelectorMismatch",
                    "service": name,
                    "namespace": ep_namespace,
                    "message": "Service has no endpoints - "
                               "selector may not match pod labels!"
                })

    log.info(
        f"Network inspection complete. "
        f"Total services: {len(services)}, "
        f"Issues: {len(issues)}"
    )

    return {
        "success": True,
        "total_services": len(services),
        "services": services,
        "issues": issues,
        "has_issues": len(issues) > 0
    }