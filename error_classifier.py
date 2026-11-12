from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorKind(str, Enum):
    NETWORK = "network"
    AUTH_ACCOUNT = "auth_account"
    RATE_LIMIT = "rate_limit"
    REQUEST = "request"
    SERVER = "server"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Classification:
    kind: ErrorKind
    label: str
    should_failover: bool
    reason: str


NETWORK_TERMS = ("dns", "name resolution", "connection timeout", "timed out", "connection reset", "proxy error", "network unreachable", "temporary failure in name resolution")
ACCOUNT_TERMS = ("invalid token", "token invalid", "expired token", "token expired", "insufficient balance", "balance exhausted", "quota exhausted", "insufficient quota", "billing hard limit", "account suspended", "account disabled", "permission denied", "access denied", "model access revoked", "no permission", "余额不足", "额度耗尽", "令牌无效", "令牌过期", "权限不足", "账户停用", "账号停用")
QUOTA_TERMS = ("insufficient_quota", "quota_exceeded", "billing_hard_limit", "credit balance is too low", "out of credits", "billing limit")
RATE_TERMS = ("rate_limit", "rate limit", "too many requests", "requests per minute")


def classify_error(status_code: int | None, body: str = "", exception: BaseException | str | None = None) -> Classification:
    text = (body + " " + (str(exception) if exception is not None else "")).casefold()
    if any(term in text for term in NETWORK_TERMS):
        return Classification(ErrorKind.NETWORK, "network failure", False, "Transport failures do not trigger provider failover")
    if any(term in text for term in ACCOUNT_TERMS + QUOTA_TERMS):
        return Classification(ErrorKind.AUTH_ACCOUNT, "authentication/account failure", True, "Provider explicitly reported an account, credential, or access failure")
    if status_code == 401:
        return Classification(ErrorKind.AUTH_ACCOUNT, "unauthorized", True, "HTTP 401")
    if status_code == 403:
        return Classification(ErrorKind.AUTH_ACCOUNT, "forbidden", True, "HTTP 403 indicates denied access")
    if status_code == 429 or any(term in text for term in RATE_TERMS):
        return Classification(ErrorKind.RATE_LIMIT, "rate limited", False, "Rate limiting is not proof of exhausted account quota")
    if status_code in (400, 404):
        return Classification(ErrorKind.REQUEST, "request or model error", False, "Request/model errors are not credential failures")
    if status_code is not None and status_code >= 500:
        return Classification(ErrorKind.SERVER, "provider server error", False, "Transient server errors require retry/circuit handling")
    return Classification(ErrorKind.UNKNOWN, "unclassified error", False, "Insufficient evidence to switch providers")
