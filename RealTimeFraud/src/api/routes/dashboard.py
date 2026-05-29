from fastapi import APIRouter, Depends

from src.core.schemas import DashboardStats
from src.services.audit_log import AuditLog
from src.services.transaction_service import get_audit_log

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(audit_log: AuditLog = Depends(get_audit_log)) -> DashboardStats:
    data = audit_log.stats()
    return DashboardStats(**data)


@router.get("/recent")
def get_recent(audit_log: AuditLog = Depends(get_audit_log), limit: int = 15) -> list[dict]:
    return audit_log.recent(limit=min(limit, 50))
