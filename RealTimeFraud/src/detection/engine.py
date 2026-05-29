from datetime import datetime, timezone

from config.settings import settings
from src.core.schemas import FraudAssessment, FraudDecision, RuleHit, TransactionRecord
from src.detection.rules.base_rules import FraudRule, build_default_rules
from src.features.store import FeatureStore

_DECISION_MESSAGES = {
    FraudDecision.ALLOW: "Transaction verified. No fraud indicators detected.",
    FraudDecision.REVIEW: "Transaction flagged for manual review. Additional verification recommended.",
    FraudDecision.BLOCK: "Transaction blocked. Multiple high-risk fraud signals detected.",
}


class FraudDetectionEngine:
    """Evaluates transactions in real time using configurable rules."""

    def __init__(
        self,
        feature_store: FeatureStore,
        rules: list[FraudRule] | None = None,
        block_threshold: float | None = None,
        review_threshold: float | None = None,
    ) -> None:
        self._feature_store = feature_store
        self._rules = rules or build_default_rules()
        self._block_threshold = block_threshold or settings.risk_block_threshold
        self._review_threshold = review_threshold or settings.risk_review_threshold

    def assess(self, transaction: TransactionRecord) -> FraudAssessment:
        hits: list[RuleHit] = []
        for rule in self._rules:
            hit = rule.evaluate(transaction, self._feature_store)
            if hit:
                hits.append(hit)

        risk_score = self._aggregate_score(hits)
        decision = self._decide(risk_score)

        self._feature_store.record_transaction(transaction)

        return FraudAssessment(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            risk_score=round(risk_score, 4),
            decision=decision,
            rules_triggered=hits,
            assessed_at=datetime.now(timezone.utc),
            message=_DECISION_MESSAGES[decision],
        )

    def _aggregate_score(self, hits: list[RuleHit]) -> float:
        if not hits:
            return 0.0

        combined = 1.0
        for hit in hits:
            combined *= 1.0 - hit.score
        return min(1.0 - combined, 1.0)

    def _decide(self, risk_score: float) -> FraudDecision:
        if risk_score >= self._block_threshold:
            return FraudDecision.BLOCK
        if risk_score >= self._review_threshold:
            return FraudDecision.REVIEW
        return FraudDecision.ALLOW
