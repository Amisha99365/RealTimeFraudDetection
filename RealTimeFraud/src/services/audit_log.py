from collections import deque
from datetime import datetime, timezone
from threading import Lock

from src.core.schemas import FraudAssessment, TransactionRequest


class AuditEntry:
    def __init__(
        self,
        assessment: FraudAssessment,
        request: TransactionRequest,
        source: str,
    ) -> None:
        self.assessment = assessment
        self.request = request
        self.source = source
        self.logged_at = datetime.now(timezone.utc)


class AuditLog:
    """Tamper-evident in-memory audit trail for transparency and trust."""

    def __init__(self, max_entries: int = 500) -> None:
        self._entries: deque[AuditEntry] = deque(maxlen=max_entries)
        self._lock = Lock()
        self._total_scored = 0
        self._total_blocked = 0
        self._total_reviewed = 0

    def record(self, assessment: FraudAssessment, request: TransactionRequest, source: str) -> None:
        with self._lock:
            self._entries.appendleft(AuditEntry(assessment, request, source))
            self._total_scored += 1
            if assessment.decision.value == "block":
                self._total_blocked += 1
            elif assessment.decision.value == "review":
                self._total_reviewed += 1

    def recent(self, limit: int = 20) -> list[dict]:
        with self._lock:
            items = list(self._entries)[:limit]
        return [
            {
                "transaction_id": entry.assessment.transaction_id,
                "user_id": entry.assessment.user_id,
                "amount": entry.request.amount,
                "currency": entry.request.currency,
                "channel": entry.request.channel.value,
                "decision": entry.assessment.decision.value,
                "risk_score": entry.assessment.risk_score,
                "rules_triggered": [r.rule_id for r in entry.assessment.rules_triggered],
                "source": entry.source,
                "assessed_at": entry.assessment.assessed_at.isoformat(),
            }
            for entry in items
        ]

    def stats(self) -> dict:
        with self._lock:
            return {
                "total_scored": self._total_scored,
                "total_blocked": self._total_blocked,
                "total_reviewed": self._total_reviewed,
                "total_allowed": self._total_scored - self._total_blocked - self._total_reviewed,
                "recent_count": len(self._entries),
            }
