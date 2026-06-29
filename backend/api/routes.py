from fastapi import APIRouter, HTTPException
from backend.models.schemas import (
    InvestigateRequest,
    InvestigateResponse,
    ApproveActionRequest,
    HealthResponse,
    DiagnosisResponse
)
from backend.services.agent_service import (
    run_full_agent_pipeline,
    execute_approved_actions
)
from backend.core.logger import log
from backend.db.database import (
    save_investigation,
    save_action,
    get_recent_investigations,
    get_investigation_stats,
    init_database
)
from datetime import datetime
import uuid

# Router instance
# Think of this like a mini FastAPI app
# that handles specific routes!
router = APIRouter()

# Temporary in-memory storage for pipelines
# In production this would be a database!
pipeline_store = {}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Simple health check endpoint.
    Like a heartbeat for our API!
    """
    return HealthResponse(
        status="healthy",
        service="k8s-ai-agent",
        version="1.0.0"
    )


@router.post("/investigate", response_model=InvestigateResponse)
async def investigate(request: InvestigateRequest):
    """
    Runs the full AI agent pipeline.
    
    Flow:
    1. Investigate K8s cluster
    2. AI analyzes findings
    3. Returns diagnosis + suggested actions
    4. Waits for human approval!
    """
    log.info(
        f"Investigation requested for "
        f"namespace: {request.namespace}"
    )

    try:
        # Run full pipeline
        result = run_full_agent_pipeline(request.namespace)

        # Generate unique ID for this pipeline
        # So we can reference it when approving!
        pipeline_id = str(uuid.uuid4())

        # Store pipeline result temporarily
        pipeline_store[pipeline_id] = result
        
        # Add timestamp to result
        result["timestamp"] = datetime.now().isoformat()

        # Save to database
        save_investigation(
        pipeline_id,
        request.namespace,
        result
       )

        # Build diagnosis response
        diagnosis = result.get("diagnosis", {})
        diagnosis_response = DiagnosisResponse(
            root_cause=diagnosis.get("root_cause"),
            explanation=diagnosis.get("explanation"),
            suggested_fix=diagnosis.get("suggested_fix"),
            kubectl_commands=diagnosis.get("kubectl_commands", []),
            prevention=diagnosis.get("prevention"),
            confidence=diagnosis.get("confidence")
        )

        log.info(
            f"Investigation complete! "
            f"Pipeline ID: {pipeline_id}"
        )

        return InvestigateResponse(
            status=result["status"],
            pipeline_id=pipeline_id,
            summary=result.get("investigation", {}).get("summary"),
            diagnosis=diagnosis_response,
            suggested_actions=result.get("suggested_actions", [])
        )

    except Exception as e:
        log.error(f"Investigation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Investigation failed: {str(e)}"
        )


@router.post("/approve")
async def approve_action(request: ApproveActionRequest):
    """
    Executes an approved action!
    
    User clicks Approve in dashboard
    → Frontend sends action_index + pipeline_id
    → We execute that specific action
    → Return result!
    
    This is the Human in the Loop endpoint!
    """
    log.info(
        f"Approval received for action "
        f"{request.action_index} in "
        f"pipeline {request.pipeline_id}"
    )

    # Get pipeline from store
    pipeline_result = pipeline_store.get(request.pipeline_id)

    if not pipeline_result:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found! "
                   "Please run investigation first!"
        )

    try:
        # Execute only the approved action
        updated_result = execute_approved_actions(
            pipeline_result,
            [request.action_index]
        )

        executed = updated_result.get("executed_actions", [])

        if executed:
           action_result = executed[0]["result"]

           # Save approved action to database
           save_action(
               request.pipeline_id,
               executed[0]["action"],
               approved=True,
               result=action_result
            )

           return {
             "status": "success",
             "message": action_result.get("message"),
             "action": executed[0]["action"]["action_type"]
           }

        return {
            "status": "failed",
            "message": "No actions were executed!"
        }
    except Exception as e:
        log.error(f"Action execution failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Action failed: {str(e)}"
        )


@router.get("/pipelines")
async def get_pipelines():
    """
    Returns all pipeline IDs stored in memory.
    Like an investigation history!
    """
    return {
        "total": len(pipeline_store),
        "pipelines": list(pipeline_store.keys())
    }
    
    
@router.get("/history")
async def get_history():
    """
    Returns recent investigation history!
    """
    investigations = get_recent_investigations(limit=10)
    stats = get_investigation_stats()

    return {
        "stats": stats,
        "investigations": investigations
    }