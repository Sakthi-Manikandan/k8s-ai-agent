from pydantic import BaseModel
from typing import Optional


class InvestigateRequest(BaseModel):
    """
    What frontend sends to start investigation.
    """
    namespace: str = "--all-namespaces"


class ApproveActionRequest(BaseModel):
    """
    What frontend sends when user approves an action.
    """
    action_index: int
    pipeline_id: str


class HealthResponse(BaseModel):
    """
    Health check response.
    """
    status: str
    service: str
    version: str


class ActionItem(BaseModel):
    """
    A single suggested action.
    """
    action_type: str
    reason: str
    command: str
    risk: str
    approved: bool = False
    namespace: Optional[str] = None
    pod: Optional[str] = None
    deployment: Optional[str] = None


class DiagnosisResponse(BaseModel):
    """
    Full diagnosis response sent to frontend.
    """
    root_cause: Optional[str] = None
    explanation: Optional[str] = None
    suggested_fix: Optional[str] = None
    kubectl_commands: Optional[list] = None
    prevention: Optional[str] = None
    confidence: Optional[int] = None


class InvestigateResponse(BaseModel):
    """
    Full pipeline response sent to frontend.
    """
    status: str
    pipeline_id: str
    summary: Optional[dict] = None
    diagnosis: Optional[DiagnosisResponse] = None
    suggested_actions: Optional[list] = None
    error: Optional[str] = None