from fastapi import APIRouter, Depends, Request

from config.settings import settings
from src.api.security.auth import verify_api_key
from src.api.security.rate_limit import RateLimiter, get_client_ip
from src.core.schemas import FraudAssessment, TransactionRequest
from src.services.audit_log import AuditLog
from src.services.transaction_service import get_audit_log, get_transaction_service, TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])

_api_limiter = RateLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds)
_public_limiter = RateLimiter(settings.public_rate_limit_requests, settings.rate_limit_window_seconds)


@router.post("/score", response_model=FraudAssessment)
def score_transaction(
    request: TransactionRequest,
    http_request: Request,
    service: TransactionService = Depends(get_transaction_service),
    _api_key: str = Depends(verify_api_key),
) -> FraudAssessment:
    """Secure API endpoint — requires X-API-Key header."""
    _api_limiter.check(get_client_ip(http_request))
    return service.process(request, source="api")


@router.post("/check", response_model=FraudAssessment)
def check_transaction_public(
    request: TransactionRequest,
    http_request: Request,
    service: TransactionService = Depends(get_transaction_service),
) -> FraudAssessment:
    """Public dashboard endpoint — rate-limited, no API key required."""
    _public_limiter.check(get_client_ip(http_request))
    return service.process(request, source="dashboard")
