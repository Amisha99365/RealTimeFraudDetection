from config.settings import settings
from src.core.schemas import FraudAssessment, TransactionRequest
from src.detection.engine import FraudDetectionEngine
from src.features.store import FeatureStore
from src.services.audit_log import AuditLog


class TransactionService:
    def __init__(self, engine: FraudDetectionEngine, audit_log: AuditLog) -> None:
        self._engine = engine
        self._audit_log = audit_log

    def process(self, request: TransactionRequest, source: str = "api") -> FraudAssessment:
        from src.core.schemas import TransactionRecord

        transaction = TransactionRecord.from_request(request)
        assessment = self._engine.assess(transaction)
        self._audit_log.record(assessment, request, source)
        return assessment


_feature_store: FeatureStore | None = None
_audit_log: AuditLog | None = None
_engine: FraudDetectionEngine | None = None
_service: TransactionService | None = None


def get_feature_store() -> FeatureStore:
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore(velocity_window_seconds=settings.velocity_window_seconds)
    return _feature_store


def get_audit_log() -> AuditLog:
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log


def get_engine() -> FraudDetectionEngine:
    global _engine
    if _engine is None:
        _engine = FraudDetectionEngine(feature_store=get_feature_store())
    return _engine


def get_transaction_service() -> TransactionService:
    global _service
    if _service is None:
        _service = TransactionService(engine=get_engine(), audit_log=get_audit_log())
    return _service
