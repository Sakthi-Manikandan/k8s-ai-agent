from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InvestigationRecord(BaseModel):
    """
    Represents a saved investigation in database.
    """
    id: str
    timestamp: str
    namespace: str
    status: str
    total_pods: int = 0
    problematic_pods: int = 0
    critical_events: int = 0
    network_issues: int = 0
    cluster_healthy: bool = False
    root_cause: Optional[str] = None
    confidence: Optional[int] = None
    suggested_fix: Optional[str] = None
    created_at: Optional[str] = None


class ActionRecord(BaseModel):
    """
    Represents a saved action in database.
    """
    id: Optional[int] = None
    investigation_id: str
    action_type: str
    reason: Optional[str] = None
    command: Optional[str] = None
    risk: Optional[str] = None
    approved: bool = False
    executed: bool = False
    result: Optional[str] = None
    timestamp: Optional[str] = None


class InvestigationStats(BaseModel):
    """
    Statistics about all investigations.
    """
    total: int = 0
    unhealthy: int = 0
    avg_confidence: Optional[float] = None
    last_investigation: Optional[str] = None