from backend.kubernetes.kubectl_executor import execute_kubectl
from backend.core.logger import log


def restart_pod(pod_name: str, namespace: str = "default") -> dict:
    """
    Restarts a specific pod.
    Like running: kubectl rollout restart deployment
    
    ⚠️ Only executes after human approval!
    """
    log.info(f"Restarting pod: {pod_name} in {namespace}")

    result = execute_kubectl([
        "kubectl", "delete", "pod",
        pod_name,
        "-n", namespace
    ])

    if result["success"]:
        log.info(f"Pod {pod_name} restarted successfully!")
        return {
            "success": True,
            "action": "restart_pod",
            "pod": pod_name,
            "namespace": namespace,
            "message": f"Pod {pod_name} deleted and "
                       f"will restart automatically!"
        }

    log.error(f"Failed to restart pod: {pod_name}")
    return {
        "success": False,
        "error": result["error"]
    }


def restart_deployment(
    deployment_name: str,
    namespace: str = "default"
) -> dict:
    """
    Restarts all pods in a deployment.
    Like running: kubectl rollout restart deployment <name>
    
    ⚠️ Only executes after human approval!
    """
    log.info(
        f"Restarting deployment: "
        f"{deployment_name} in {namespace}"
    )

    result = execute_kubectl([
        "kubectl", "rollout", "restart",
        "deployment", deployment_name,
        "-n", namespace
    ])

    if result["success"]:
        log.info(
            f"Deployment {deployment_name} "
            f"restarted successfully!"
        )
        return {
            "success": True,
            "action": "restart_deployment",
            "deployment": deployment_name,
            "namespace": namespace,
            "message": f"Deployment {deployment_name} "
                       f"rollout restart triggered!"
        }

    log.error(
        f"Failed to restart deployment: {deployment_name}"
    )
    return {
        "success": False,
        "error": result["error"]
    }


def scale_deployment(
    deployment_name: str,
    replicas: int,
    namespace: str = "default"
) -> dict:
    """
    Scales a deployment to specified replicas.
    Like running: kubectl scale deployment <name> --replicas=3
    
    ⚠️ Only executes after human approval!
    """
    log.info(
        f"Scaling deployment: {deployment_name} "
        f"to {replicas} replicas in {namespace}"
    )

    result = execute_kubectl([
        "kubectl", "scale", "deployment",
        deployment_name,
        f"--replicas={replicas}",
        "-n", namespace
    ])

    if result["success"]:
        log.info(
            f"Deployment {deployment_name} "
            f"scaled to {replicas} replicas!"
        )
        return {
            "success": True,
            "action": "scale_deployment",
            "deployment": deployment_name,
            "namespace": namespace,
            "replicas": replicas,
            "message": f"Deployment {deployment_name} "
                       f"scaled to {replicas} replicas!"
        }

    log.error(
        f"Failed to scale deployment: {deployment_name}"
    )
    return {
        "success": False,
        "error": result["error"]
    }


def get_suggested_actions(diagnosis: dict, investigation: dict) -> list:
    """
    Based on AI diagnosis, suggests what actions to take.
    
    ⚠️ These are SUGGESTIONS only!
    User must APPROVE before execution!
    
    This is the Human in the Loop pattern!
    """
    log.info("Generating suggested actions...")
    actions = []

    # Get problematic pods
    problematic_pods = investigation.get(
        "pods", {}
    ).get("problematic_pods", [])

    # Get root cause from diagnosis
    root_cause = diagnosis.get(
        "root_cause", ""
    ).lower()

    for pod in problematic_pods:
        pod_name = pod["name"]
        namespace = pod["namespace"]
        status = pod["status"]
# Suggest restart for CrashLoopBackOff
        if "crashloopbackoff" in status.lower():
            actions.append({
                "action_type": "restart_pod",
                "reason": f"Pod {pod_name} is in CrashLoopBackOff",
                "command": f"kubectl delete pod {pod_name} -n {namespace}",
                "pod": pod_name,
                "namespace": namespace,
                "risk": "LOW",
                "approved": False  # Waiting for human approval!
            })

        # Suggest image fix for ImagePullBackOff
        elif "imagepullbackoff" in status.lower():
            actions.append({
                "action_type": "check_image",
                "reason": f"Pod {pod_name} has ImagePullBackOff",
                "command": f"kubectl describe pod {pod_name} -n {namespace}",
                "pod": pod_name,
                "namespace": namespace,
                "risk": "LOW",
                "approved": False
            })

        # Suggest restart for OOMKilled
        elif "oomkilled" in status.lower():
            actions.append({
                "action_type": "restart_pod",
                "reason": f"Pod {pod_name} was OOMKilled",
                "command": f"kubectl delete pod {pod_name} -n {namespace}",
                "pod": pod_name,
                "namespace": namespace,
                "risk": "MEDIUM",
                "approved": False
            })

    # Suggest deployment restart for unhealthy deployments
    unhealthy_deployments = investigation.get(
        "deployments", {}
    ).get("unhealthy_deployments", [])

    for dep in unhealthy_deployments:
        actions.append({
            "action_type": "restart_deployment",
            "reason": f"Deployment {dep['name']} is unhealthy "
                      f"({dep['ready']} ready)",
            "command": f"kubectl rollout restart deployment "
                       f"{dep['name']} -n {dep['namespace']}",
            "deployment": dep["name"],
            "namespace": dep["namespace"],
            "risk": "MEDIUM",
            "approved": False
        })

    log.info(f"Generated {len(actions)} suggested actions")
    return actions


def execute_approved_action(action: dict) -> dict:
    """
    Executes an action ONLY after human approval!
    
    This is the key function that enforces
    Human in the Loop pattern!
    """
    # Safety check - must be approved!
    if not action.get("approved", False):
        log.warning("Action not approved! Skipping execution!")
        return {
            "success": False,
            "error": "Action not approved by user!"
        }

    action_type = action.get("action_type")

    log.info(f"Executing approved action: {action_type}")

    if action_type == "restart_pod":
        return restart_pod(
            action["pod"],
            action["namespace"]
        )

    elif action_type == "restart_deployment":
        return restart_deployment(
            action["deployment"],
            action["namespace"]
        )

    elif action_type == "scale_deployment":
        return scale_deployment(
            action["deployment"],
            action.get("replicas", 1),
            action["namespace"]
        )

    else:
        log.warning(f"Unknown action type: {action_type}")
        return {
            "success": False,
            "error": f"Unknown action type: {action_type}"
        }