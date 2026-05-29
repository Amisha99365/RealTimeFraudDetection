from datetime import datetime, timedelta, timezone

from src.core.schemas import TransactionChannel, TransactionRecord
from src.detection.engine import FraudDetectionEngine
from src.features.store import FeatureStore


def _make_transaction(
    user_id: str,
    amount: float,
    *,
    device_id: str | None = None,
    country_code: str | None = None,
    timestamp: datetime | None = None,
) -> TransactionRecord:
    return TransactionRecord(
        user_id=user_id,
        amount=amount,
        currency="INR",
        channel=TransactionChannel.UPI,
        device_id=device_id,
        country_code=country_code,
        timestamp=timestamp or datetime.now(timezone.utc),
    )


def test_low_risk_transaction_is_allowed() -> None:
    store = FeatureStore(velocity_window_seconds=300)
    engine = FraudDetectionEngine(feature_store=store, block_threshold=0.75, review_threshold=0.45)

    assessment = engine.assess(_make_transaction("user_a", 500.0, device_id="phone_1", country_code="IN"))

    assert assessment.decision.value == "allow"
    assert assessment.risk_score < 0.45
    assert assessment.rules_triggered == []


def test_high_amount_triggers_review_or_block() -> None:
    store = FeatureStore(velocity_window_seconds=300)
    engine = FraudDetectionEngine(feature_store=store, block_threshold=0.75, review_threshold=0.45)

    assessment = engine.assess(_make_transaction("user_b", 15000.0, device_id="phone_2", country_code="IN"))

    assert assessment.decision.value in {"review", "block"}
    assert any(hit.rule_id == "HIGH_AMOUNT" for hit in assessment.rules_triggered)


def test_velocity_spike_triggers_rule() -> None:
    store = FeatureStore(velocity_window_seconds=300)
    engine = FraudDetectionEngine(feature_store=store, block_threshold=0.75, review_threshold=0.45)

    base_time = datetime.now(timezone.utc)
    for offset in range(5):
        engine.assess(
            _make_transaction(
                "user_c",
                1000.0,
                device_id="phone_3",
                country_code="IN",
                timestamp=base_time + timedelta(seconds=offset * 10),
            )
        )

    assessment = engine.assess(
        _make_transaction(
            "user_c",
            1000.0,
            device_id="phone_3",
            country_code="IN",
            timestamp=base_time + timedelta(seconds=60),
        )
    )

    assert any(hit.rule_id == "VELOCITY_SPIKE" for hit in assessment.rules_triggered)
