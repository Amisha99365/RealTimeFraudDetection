from datetime import datetime, timedelta, timezone

from src.core.schemas import TransactionChannel, TransactionRecord
from src.detection.engine import FraudDetectionEngine
from src.features.store import FeatureStore


def _txn(
    user_id: str,
    amount: float,
    *,
    device_id: str | None = "dev1",
    country_code: str = "IN",
    timestamp: datetime | None = None,
    ip_address: str | None = None,
    merchant_id: str | None = None,
) -> TransactionRecord:
    return TransactionRecord(
        user_id=user_id,
        amount=amount,
        currency="INR",
        channel=TransactionChannel.UPI,
        device_id=device_id,
        country_code=country_code,
        timestamp=timestamp or datetime.now(timezone.utc),
        ip_address=ip_address,
        merchant_id=merchant_id,
    )


def test_round_amount_rule() -> None:
    engine = FraudDetectionEngine(feature_store=FeatureStore())
    result = engine.assess(_txn("user_r", 10000.0))
    assert any(hit.rule_id == "ROUND_AMOUNT" for hit in result.rules_triggered)


def test_amount_deviation_rule() -> None:
    store = FeatureStore()
    engine = FraudDetectionEngine(feature_store=store)
    base = datetime.now(timezone.utc)

    for i in range(4):
        engine.assess(_txn("user_d", 500.0, timestamp=base + timedelta(minutes=i)))

    result = engine.assess(_txn("user_d", 8000.0, timestamp=base + timedelta(minutes=5)))
    assert any(hit.rule_id == "AMOUNT_DEVIATION" for hit in result.rules_triggered)
