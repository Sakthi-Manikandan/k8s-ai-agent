from fastapi import APIRouter
from backend.models.schemas import (
    InvestigateRequest,
    ApproveActionRequest,
    HealthResponse,
    InvestigateResponse,
    DiagnosisResponse
)
from backend.services.agent_service import (
    run_full_agent_pipeline,
    execute_approved_actions
)
from backend.db.database import (
    save_investigation,
    save_action,
    get_recent_investigations,
    get_investigation_stats
)
from backend.core.logger import log
from datetime import datetime
import uuid

router = APIRouter()

# In-memory storage for active pipelines
# In production, use database!
pipeline_store = {}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Used by Kubernetes probes!
    """
    return HealthResponse(
        status="healthy",
        service="k8s-ai-agent",
        version="0.1.0"
    )


@router.post("/investigate", response_model=InvestigateResponse)
async def investigate(request: InvestigateRequest):
    """
    Start a full investigation of the cluster.
    Runs all 5 inspectors + AI diagnosis.
    """
    log.info(f"Investigation requested for namespace: {request.namespace}")

    pipeline_id = str(uuid.uuid4())

    try:
        # Run the full agent pipeline
        result = await run_full_agent_pipeline(request.namespace)

        # Add pipeline metadata
        result["pipeline_id"] = pipeline_id
        result["timestamp"] = datetime.now().isoformat()
        result["namespace"] = request.namespace

        # Store in memory for this session
        pipeline_store[pipeline_id] = result

        # SAVE TO DATABASE!
        save_success = save_investigation(
            pipeline_id,
            request.namespace,
            result
        )

        if save_success:
            log.info(f"Investigation {pipeline_id} saved to database!")
        else:
            log.warning(f"Failed to save investigation {pipeline_id} to database")

        return InvestigateResponse(
            status="success",
            pipeline_id=pipeline_id,
            namespace=request.namespace,
            investigation=result.get("investigation", {}),
            diagnosis=result.get("diagnosis", {}),
            suggested_actions=result.get("suggested_actions", []),
            timestamp=result["timestamp"]
        )

    except Exception as e:
        log.error(f"Investigation failed: {str(e)}")
        return InvestigateResponse(
            status="error",
            pipeline_id=pipeline_id,
            error=str(e)
        )


@router.post("/approve")
async def approve_action(request: ApproveActionRequest):
    """
    User approves an action and we execute it!
    """
    log.info(
        f"Action approval requested for "
        f"pipeline {request.pipeline_id}, "
        f"action index {request.action_index}"
    )

    # Get the pipeline result
    pipeline = pipeline_store.get(request.pipeline_id)

    if not pipeline:
        return {
            "status": "error",
            "message": "Pipeline not found!"
        }

    # Execute approved actions
    executed = execute_approved_actions(
        pipeline,
        [request.action_index]
    )

    if executed:
        action_result = executed[0]["result"]
        action = executed[0]["action"]

        # SAVE ACTION TO DATABASE!
        save_action(
            request.pipeline_id,
            action,
            approved=True,
            result=action_result
        )

        log.info(f"Action executed and saved: {action.get('action_type')}")

        return {
            "status": "success",
            "message": action_result.get("message"),
            "action": action.get("action_type")
        }
    else:
        return {
            "status": "error",
            "message": "Failed to execute action"
        }


@router.get("/history")
async def get_history():
    """
    Returns investigation history and statistics!
    """
    log.info("History requested")

    investigations = get_recent_investigations(limit=20)
    stats = get_investigation_stats()

    log.info(
        f"Returning {len(investigations)} investigations "
        f"from database"
    )

    return {
        "stats": stats,
        "investigations": investigations
    }


@router.get("/pipelines")
async def get_pipelines():
    """
    Returns list of active pipelines.
    """
    return {
        "count": len(pipeline_store),
        "pipeline_ids": list(pipeline_store.keys())
    }