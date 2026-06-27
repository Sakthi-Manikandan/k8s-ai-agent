from backend.kubernetes.kubectl_executor import execute_kubectl
from backend.core.logger import log


CRITICAL_EVENTS = [
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "Unhealthy",
    "OOMKilling",
    "FailedCreate",
    "FailedAttachVolume",
    "NetworkNotReady"
]


def analyze_events(namespace: str = "--all-namespaces") -> dict:
    """
    Reads Kubernetes events and finds critical ones.
    Like running: kubectl get events -A
    """
    log.info("Starting event analysis...")

    result = execute_kubectl([
        "kubectl", "get", "events",
        "-A",
        "--sort-by=.lastTimestamp"
    ])

    if not result["success"]:
        log.error("Failed to get events from cluster")
        return {
            "success": False,
            "error": result["error"],
            "critical_events": [],
            "all_events": []
        }

    all_events = []
    critical_events = []
    lines = result["output"].split("\n")

    for line in lines[1:]:
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) < 5:
            continue

        event = {
            "namespace": parts[0],
            "last_seen": parts[1],
            "type": parts[2],
            "reason": parts[3],
            "object": parts[4],
            "message": " ".join(parts[5:])
        }

        all_events.append(event)

        if event["reason"] in CRITICAL_EVENTS or \
                event["type"] == "Warning":
            log.warning(
                f"Critical event found: {event['reason']} "
                f"for {event['object']} - "
                f"{event['message']}"
            )
            critical_events.append(event)

    log.info(
        f"Event analysis complete. "
        f"Total: {len(all_events)}, "
        f"Critical: {len(critical_events)}"
    )

    return {
        "success": True,
        "total_events": len(all_events),
        "critical_events": critical_events,
        "all_events": all_events,
        "has_critical_events": len(critical_events) > 0
    }