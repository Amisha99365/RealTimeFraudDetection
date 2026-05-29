from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator
from enum import Enum
from uuid import uuid4
import re


class TransactionChannel(str, Enum):
    BANKING = "banking"
    UPI = "upi"
    ECOMMERCE = "ecommerce"
    CREDIT_CARD = "credit_card"
    INSURANCE = "insurance"
    PAYMENT_GATEWAY = "payment_gateway"


class FraudDecision(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


_USER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


class TransactionRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    amount: float = Field(..., gt=0, le=10_000_000)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    channel: TransactionChannel
    merchant_id: str | None = Field(default=None, max_length=64)
    device_id: str | None = Field(default=None, max_length=128)
    ip_address: str | None = Field(default=None, max_length=45)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    timestamp: datetime | None = None

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: str) -> str:
        if not _USER_ID_PATTERN.match(value):
            raise ValueError("user_id may only contain letters, numbers, underscores, hyphens, and dots")
        return value

    @field_validator("currency", "country_code")
    @classmethod
    def uppercase_codes(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class RuleHit(BaseModel):
    rule_id: str
    description: str
    score: float = Field(..., ge=0.0, le=1.0)


class FraudAssessment(BaseModel):
    transaction_id: str
    user_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    decision: FraudDecision
    rules_triggered: list[RuleHit]
    assessed_at: datetime
    message: str = ""


class TransactionRecord(BaseModel):
    transaction_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    amount: float
    currency: str
    channel: TransactionChannel
    merchant_id: str | None = None
    device_id: str | None = None
    ip_address: str | None = None
    country_code: str | None = None
    timestamp: datetime

    @classmethod
    def from_request(cls, request: TransactionRequest) -> "TransactionRecord":
        return cls(
            user_id=request.user_id,
            amount=request.amount,
            currency=request.currency,
            channel=request.channel,
            merchant_id=request.merchant_id,
            device_id=request.device_id,
            ip_address=request.ip_address,
            country_code=request.country_code,
            timestamp=request.timestamp or datetime.now(timezone.utc),
        )


class DashboardStats(BaseModel):
    total_scored: int
    total_blocked: int
    total_reviewed: int
    total_allowed: int
    recent_count: int


class HealthResponse(BaseModel):
    status: str
    service: str
    secure: bool
    version: str
