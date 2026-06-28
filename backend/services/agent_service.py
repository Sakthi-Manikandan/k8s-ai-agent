from backend.kubernetes.investigation_service import run_investigation
from backend.ai.reasoning_engine import analyze_investigation
from backend.kubernetes.remediation import (
    get_suggested_actions,
    execute_approved_action
)
from backend.core.logger import log


def run_full_agent_pipeline(namespace: str = "--all-namespaces") -> dict:
    """
    Runs the complete AI agent pipeline!
    
    Flow:
    1. Investigate K8s cluster
    2. AI analyzes findings
    3. Suggests remediation actions
    4. Waits for human approval
    5. Executes approved actions
    
    This is the BRAIN of our entire project!
    """
    log.info("🤖 Starting AI Agent Pipeline...")

    pipeline_result = {
        "status": "running",
        "investigation": {},
        "diagnosis": {},
        "suggested_actions": [],
        "executed_actions": []
    }

    # Step 1 — Investigate cluster
    log.info("Pipeline Step 1/3: Investigating cluster...")
    investigation = run_investigation(namespace)
    pipeline_result["investigation"] = investigation

    # Step 2 — AI reasoning
    log.info("Pipeline Step 2/3: AI reasoning...")
    diagnosis_result = analyze_investigation(investigation)

    if not diagnosis_result["success"]:
        log.error("AI reasoning failed!")
        pipeline_result["status"] = "failed"
        pipeline_result["error"] = diagnosis_result.get("error")
        return pipeline_result

    diagnosis = diagnosis_result["diagnosis"]
    pipeline_result["diagnosis"] = diagnosis

    # Step 3 — Generate suggested actions
    log.info("Pipeline Step 3/3: Generating actions...")
    suggested_actions = get_suggested_actions(
        diagnosis,
        investigation
    )
    pipeline_result["suggested_actions"] = suggested_actions

    pipeline_result["status"] = "awaiting_approval"

    log.info(
        f"🤖 Pipeline complete! "
        f"Status: awaiting_approval "
        f"Actions suggested: {len(suggested_actions)}"
    )

    return pipeline_result


def execute_approved_actions(
    pipeline_result: dict,
    approved_action_indices: list
) -> dict:
    """
    Executes ONLY the actions approved by the user!
    
    approved_action_indices = list of action numbers
    the user clicked approve on!
    
    Example:
    User approved actions 0 and 2
    approved_action_indices = [0, 2]
    """
    log.info(
        f"Executing {len(approved_action_indices)} "
        f"approved actions..."
    )

    executed_actions = []
    suggested_actions = pipeline_result.get(
        "suggested_actions", []
    )

    for index in approved_action_indices:
        if index < len(suggested_actions):
            action = suggested_actions[index]

            # Mark as approved
            action["approved"] = True

            # Execute it
            result = execute_approved_action(action)
            executed_actions.append({
                "action": action,
                "result": result
            })

            if result["success"]:
                log.info(
                    f"✅ Action executed successfully: "
                    f"{action['action_type']}"
                )
            else:
                log.error(
                    f"❌ Action failed: "
                    f"{action['action_type']} - "
                    f"{result.get('error')}"
                )

    pipeline_result["executed_actions"] = executed_actions
    pipeline_result["status"] = "complete"

    return pipeline_result