from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from src.core.schemas import TransactionRecord


@dataclass
class UserFeatures:
    recent_transactions: deque = field(default_factory=deque)
    recent_amounts: deque = field(default_factory=deque)
    known_devices: set[str] = field(default_factory=set)
    known_countries: set[str] = field(default_factory=set)
    known_ips: set[str] = field(default_factory=set)
    all_amounts: list[float] = field(default_factory=list)
    total_transaction_count: int = 0
    last_transaction_at: datetime | None = None


class FeatureStore:
    """In-memory rolling feature store for real-time fraud signals."""

    def __init__(self, velocity_window_seconds: int = 300) -> None:
        self._velocity_window = timedelta(seconds=velocity_window_seconds)
        self._users: dict[str, UserFeatures] = defaultdict(UserFeatures)
        self._blocked_ips: set[str] = set()
        self._blocked_merchants: set[str] = set()

    def get_user_features(self, user_id: str) -> UserFeatures:
        return self._users[user_id]

    def record_transaction(self, transaction: TransactionRecord) -> None:
        features = self._users[transaction.user_id]
        self._prune_old_entries(features, transaction.timestamp)

        features.recent_transactions.append(transaction.timestamp)
        features.recent_amounts.append(transaction.amount)
        features.all_amounts.append(transaction.amount)
        features.total_transaction_count += 1
        features.last_transaction_at = transaction.timestamp

        if transaction.device_id:
            features.known_devices.add(transaction.device_id)
        if transaction.country_code:
            features.known_countries.add(transaction.country_code)
        if transaction.ip_address:
            features.known_ips.add(transaction.ip_address)

    def transaction_count_in_window(self, user_id: str, as_of: datetime) -> int:
        features = self._users[user_id]
        self._prune_old_entries(features, as_of)
        return len(features.recent_transactions)

    def total_amount_in_window(self, user_id: str, as_of: datetime) -> float:
        features = self._users[user_id]
        self._prune_old_entries(features, as_of)
        return float(sum(features.recent_amounts))

    def average_amount(self, user_id: str) -> float | None:
        features = self._users[user_id]
        if not features.all_amounts:
            return None
        return sum(features.all_amounts) / len(features.all_amounts)

    def is_blocked_ip(self, ip_address: str | None) -> bool:
        return bool(ip_address and ip_address in self._blocked_ips)

    def is_blocked_merchant(self, merchant_id: str | None) -> bool:
        return bool(merchant_id and merchant_id in self._blocked_merchants)

    def _prune_old_entries(self, features: UserFeatures, as_of: datetime) -> None:
        cutoff = as_of - self._velocity_window
        while features.recent_transactions and features.recent_transactions[0] < cutoff:
            features.recent_transactions.popleft()
            if features.recent_amounts:
                features.recent_amounts.popleft()
