from abc import ABC, abstractmethod

from config.settings import settings
from src.core.schemas import RuleHit, TransactionRecord
from src.features.store import FeatureStore


class FraudRule(ABC):
    rule_id: str
    description: str

    @abstractmethod
    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        ...


class HighAmountRule(FraudRule):
    rule_id = "HIGH_AMOUNT"
    description = "Transaction amount exceeds configured threshold"

    def __init__(self, threshold: float) -> None:
        self._threshold = threshold

    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        if transaction.amount <= self._threshold:
            return None

        excess_ratio = min((transaction.amount - self._threshold) / self._threshold, 1.0)
        score = 0.5 + (0.4 * excess_ratio)
        return RuleHit(rule_id=self.rule_id, description=self.description, score=score)


class VelocityRule(FraudRule):
    rule_id = "VELOCITY_SPIKE"
    description = "Too many transactions in a short time window"

    def __init__(self, max_transactions: int) -> None:
        self._max_transactions = max_transactions

    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        count = features.transaction_count_in_window(transaction.user_id, transaction.timestamp)
        if count < self._max_transactions:
            return None

        overflow = count - self._max_transactions + 1
        score = min(0.55 + (0.15 * overflow), 1.0)
        return RuleHit(rule_id=self.rule_id, description=self.description, score=score)


class VelocityAmountRule(FraudRule):
    rule_id = "VELOCITY_AMOUNT"
    description = "Total transaction volume in window exceeds safe limit"

    def __init__(self, amount_threshold: float) -> None:
        self._amount_threshold = amount_threshold

    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        total = features.total_amount_in_window(transaction.user_id, transaction.timestamp)
        projected = total + transaction.amount
        if projected <= self._amount_threshold:
            return None

        overflow_ratio = min((projected - self._amount_threshold) / self._amount_threshold, 1.0)
        score = 0.5 + (0.35 * overflow_ratio)
        return RuleHit(
            rule_id=self.rule_id,
            description=f"{self.description} (₹{projected:,.0f} in window)",
            score=score,
        )


class NewDeviceRule(FraudRule):
    rule_id = "NEW_DEVICE"
    description = "Transaction from an unseen device for this user"

    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        if not transaction.device_id:
            return None

        user_features = features.get_user_features(transaction.user_id)
        if not user_features.known_devices or transaction.device_id in user_features.known_devices:
            return None

        return RuleHit(rule_id=self.rule_id, description=self.description, score=0.35)


class GeoAnomalyRule(FraudRule):
    rule_id = "GEO_ANOMALY"
    description = "Transaction from an unseen country for this user"

    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        if not transaction.country_code:
            return None

        user_features = features.get_user_features(transaction.user_id)
        if not user_features.known_countries or transaction.country_code in user_features.known_countries:
            return None

        return RuleHit(rule_id=self.rule_id, description=self.description, score=0.4)


class AmountDeviationRule(FraudRule):
    rule_id = "AMOUNT_DEVIATION"
    description = "Amount significantly higher than user's typical spending"

    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        user_features = features.get_user_features(transaction.user_id)
        if user_features.total_transaction_count < 3:
            return None

        average = features.average_amount(transaction.user_id)
        if average is None or average <= 0:
            return None

        if transaction.amount <= average * 3:
            return None

        deviation_ratio = min((transaction.amount / average - 3) / 5, 1.0)
        score = 0.4 + (0.35 * deviation_ratio)
        return RuleHit(
            rule_id=self.rule_id,
            description=f"{self.description} (avg ₹{average:,.0f})",
            score=score,
        )


class RoundAmountRule(FraudRule):
    rule_id = "ROUND_AMOUNT"
    description = "Suspicious round-number transaction (common in fraud testing)"

    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        if transaction.amount < 5000:
            return None
        if transaction.amount % 1000 != 0:
            return None

        return RuleHit(rule_id=self.rule_id, description=self.description, score=0.25)


class NightTransactionRule(FraudRule):
    rule_id = "ODD_HOUR"
    description = "Large transaction during unusual hours (midnight–5 AM)"

    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        hour = transaction.timestamp.hour
        if not (0 <= hour < 5):
            return None
        if transaction.amount < 5000:
            return None

        return RuleHit(rule_id=self.rule_id, description=self.description, score=0.3)


class BlocklistRule(FraudRule):
    rule_id = "BLOCKLIST_MATCH"
    description = "Transaction matches a blocked IP or merchant"

    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        if features.is_blocked_ip(transaction.ip_address):
            return RuleHit(
                rule_id=self.rule_id,
                description="Blocked IP address detected",
                score=0.95,
            )
        if features.is_blocked_merchant(transaction.merchant_id):
            return RuleHit(
                rule_id=self.rule_id,
                description="Blocked merchant detected",
                score=0.95,
            )
        return None


class MissingDeviceHighAmountRule(FraudRule):
    rule_id = "NO_DEVICE_HIGH_AMOUNT"
    description = "High-value transaction without device fingerprint"

    def __init__(self, threshold: float) -> None:
        self._threshold = threshold

    def evaluate(
        self,
        transaction: TransactionRecord,
        features: FeatureStore,
    ) -> RuleHit | None:
        if transaction.device_id:
            return None
        if transaction.amount < self._threshold:
            return None

        return RuleHit(rule_id=self.rule_id, description=self.description, score=0.45)


def build_default_rules(
    high_amount_threshold: float | None = None,
    velocity_max_transactions: int | None = None,
    velocity_amount_threshold: float | None = None,
) -> list[FraudRule]:
    threshold = high_amount_threshold or settings.high_amount_threshold
    max_tx = velocity_max_transactions or settings.velocity_max_transactions
    amount_threshold = velocity_amount_threshold or settings.velocity_amount_threshold

    return [
        BlocklistRule(),
        HighAmountRule(threshold=threshold),
        VelocityRule(max_transactions=max_tx),
        VelocityAmountRule(amount_threshold=amount_threshold),
        AmountDeviationRule(),
        NewDeviceRule(),
        GeoAnomalyRule(),
        RoundAmountRule(),
        NightTransactionRule(),
        MissingDeviceHighAmountRule(threshold=threshold * 0.5),
    ]
