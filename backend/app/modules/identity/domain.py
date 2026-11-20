"""Framework-free identity and registration rules.

Everything in this module is a pure function or value object. It deliberately imports no web
framework and no database library so the rules can be tested and reused without infrastructure.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from functools import lru_cache
from typing import TypeGuard
from zoneinfo import available_timezones

EMAIL_MAX_LENGTH = 254

FULL_NAME_MIN_LENGTH = 2
FULL_NAME_MAX_LENGTH = 100

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128

REJECTION_REASON_MAX_LENGTH = 500

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
_UNSAFE_ENCODED_REDIRECT_SEQUENCES = ("%00", "%0a", "%0d", "%5c")


class DomainValidationError(ValueError):
    """A rule violation that the API layer can map to a stable error code."""

    def __init__(self, code: str, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field


def normalize_email(value: str) -> str:
    """Trim and lowercase an address, rejecting malformed or overlong input.

    The normalized form is what the application stores and looks up, so it must be identical for
    registration, login, and the administrator commands.
    """

    email = value.strip().lower()

    if (
        not email
        or len(email) > EMAIL_MAX_LENGTH
        or ".." in email
        or _CONTROL_CHARACTERS.search(email)
        or not _EMAIL_PATTERN.fullmatch(email)
    ):
        raise DomainValidationError(
            "INVALID_EMAIL",
            "Enter a valid email address of at most 254 characters.",
            "email",
        )

    local_part, _, domain = email.partition("@")
    if local_part.startswith(".") or local_part.endswith("."):
        raise DomainValidationError(
            "INVALID_EMAIL",
            "Enter a valid email address of at most 254 characters.",
            "email",
        )
    if domain.startswith(".") or domain.endswith("."):
        raise DomainValidationError(
            "INVALID_EMAIL",
            "Enter a valid email address of at most 254 characters.",
            "email",
        )

    return email


def validate_password(password: str) -> str:
    """Enforce the length policy and return the password unchanged.

    Passwords are never trimmed: whitespace is a valid character, but an entirely blank password
    is not. No composition rules are imposed.
    """

    if (
        len(password) < PASSWORD_MIN_LENGTH
        or len(password) > PASSWORD_MAX_LENGTH
        or not password.strip()
    ):
        raise DomainValidationError(
            "INVALID_PASSWORD",
            "The password must be 12-128 characters and must not be blank.",
            "password",
        )
    return password


def normalize_full_name(value: str) -> str:
    """Trim a display name and reject blank, overlong, or control-character input.

    Unicode is allowed because names are not restricted to Latin letters. Internal whitespace is
    preserved; only the ends are trimmed.
    """

    name = value.strip()

    if (
        len(name) < FULL_NAME_MIN_LENGTH
        or len(name) > FULL_NAME_MAX_LENGTH
        or _CONTROL_CHARACTERS.search(name)
    ):
        raise DomainValidationError(
            "INVALID_FULL_NAME",
            "Enter a name of 2-100 characters without control characters.",
            "full_name",
        )
    return name


class Role(StrEnum):
    """The roles stored in ``user_roles.role``."""

    CUSTOMER = "customer"
    SALON_OWNER = "salon_owner"
    ADMIN = "admin"


ROLE_VALUES: tuple[str, ...] = tuple(role.value for role in Role)

# Public registration can only ever assign the customer capability. Owner applicants receive the
# same base role during registration and gain ``salon_owner`` only through administrator approval.
PUBLIC_REGISTRATION_ROLES: frozenset[Role] = frozenset({Role.CUSTOMER})

# After signup, an administrator may grant these roles. ``customer`` is never granted through the
# role endpoint, and unknown roles are rejected.
GRANTABLE_ROLES: frozenset[Role] = frozenset({Role.ADMIN, Role.SALON_OWNER})


def normalize_grantable_role(value: str) -> Role:
    """Return the requested role when an administrator may grant it."""

    try:
        role = Role(value)
    except ValueError as error:
        raise DomainValidationError(
            "INVALID_ROLE",
            "Only the admin and salon_owner roles can be granted.",
            "role",
        ) from error

    if role not in GRANTABLE_ROLES:
        raise DomainValidationError(
            "INVALID_ROLE",
            "Only the admin and salon_owner roles can be granted.",
            "role",
        )
    return role


class UserStatus(StrEnum):
    """The account statuses stored in ``users.status``."""

    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


USER_STATUS_VALUES: tuple[str, ...] = tuple(status.value for status in UserStatus)

# A pending owner becomes active on approval or rejected on rejection. Suspension applies to active
# accounts, and a suspended account can be restored. Rejected accounts have no path back in F-001.
USER_STATUS_TRANSITIONS: Mapping[UserStatus, frozenset[UserStatus]] = {
    UserStatus.PENDING_APPROVAL: frozenset({UserStatus.ACTIVE, UserStatus.REJECTED}),
    UserStatus.ACTIVE: frozenset({UserStatus.SUSPENDED}),
    UserStatus.SUSPENDED: frozenset({UserStatus.ACTIVE}),
    UserStatus.REJECTED: frozenset(),
}


def can_authenticate(status: UserStatus) -> bool:
    """Only an active account may hold a session."""

    return status is UserStatus.ACTIVE


def session_is_valid(
    *,
    expires_at: datetime,
    revoked_at: datetime | None,
    user_status: UserStatus,
    now: datetime,
) -> bool:
    """A session is usable only before expiry, when not revoked, for an active account."""

    if revoked_at is not None:
        return False
    if expires_at <= now:
        return False
    return can_authenticate(user_status)


def can_transition_user_status(current: UserStatus, target: UserStatus) -> bool:
    return target in USER_STATUS_TRANSITIONS[current]


def ensure_user_status_transition(current: UserStatus, target: UserStatus) -> None:
    if not can_transition_user_status(current, target):
        raise DomainValidationError(
            "INVALID_STATUS_TRANSITION",
            f"An account cannot move from {current.value} to {target.value}.",
            "status",
        )


class OwnerApplicationStatus(StrEnum):
    """The review states stored in ``owner_applications.status``."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


APPLICATION_STATUS_VALUES: tuple[str, ...] = tuple(
    status.value for status in OwnerApplicationStatus
)

APPLICATION_STATUS_TRANSITIONS: Mapping[
    OwnerApplicationStatus, frozenset[OwnerApplicationStatus]
] = {
    OwnerApplicationStatus.PENDING: frozenset(
        {OwnerApplicationStatus.APPROVED, OwnerApplicationStatus.REJECTED}
    ),
    OwnerApplicationStatus.APPROVED: frozenset(),
    OwnerApplicationStatus.REJECTED: frozenset(),
}


def can_transition_application_status(
    current: OwnerApplicationStatus,
    target: OwnerApplicationStatus,
) -> bool:
    return target in APPLICATION_STATUS_TRANSITIONS[current]


def ensure_application_status_transition(
    current: OwnerApplicationStatus,
    target: OwnerApplicationStatus,
) -> None:
    if not can_transition_application_status(current, target):
        raise DomainValidationError(
            "INVALID_APPLICATION_TRANSITION",
            f"An application cannot move from {current.value} to {target.value}.",
            "status",
        )


def validate_rejection_reason(reason: str | None) -> str:
    """Trim and validate the administrator's rejection reason."""

    cleaned = "" if reason is None else reason.strip()

    if not cleaned or len(cleaned) > REJECTION_REASON_MAX_LENGTH:
        raise DomainValidationError(
            "INVALID_REJECTION_REASON",
            "Give a rejection reason of 1-500 characters.",
            "reason",
        )
    return cleaned


@lru_cache(maxsize=1)
def _available_timezones() -> frozenset[str]:
    return frozenset(available_timezones())


def validate_timezone(value: str) -> str:
    """Validate an IANA time zone name such as ``Asia/Tehran``."""

    timezone = value.strip()

    if not timezone or timezone not in _available_timezones():
        raise DomainValidationError(
            "INVALID_TIMEZONE",
            "Choose a valid IANA time zone.",
            "timezone",
        )
    return timezone


# Active ISO 4217 currency codes. Keeping the list in the domain avoids a runtime dependency and
# makes the accepted values explicit and reviewable.
_ISO_4217_CODES: frozenset[str] = frozenset(
    """
    AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BOV BRL BSD
    BTN BWP BYN BZD CAD CDF CHE CHF CHW CLF CLP CNY COP COU CRC CUC CUP CVE CZK DJF DKK DOP
    DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG HUF IDR ILS INR
    IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD
    MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MXV MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB
    PEN PGK PHP PKR PLN PYG QAR RON RSD RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SLL SOS SRD
    SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX USD USN UYI UYU UYW UZS
    VED VES VND VUV WST XAF XAG XAU XBA XBB XBC XBD XCD XCG XDR XOF XPD XPF XPT XSU XTS XUA
    XXX YER ZAR ZMW ZWG
    """.split()  # noqa: SIM905 - one aligned block is easier to audit than 170 literals
)


def validate_currency(value: str) -> str:
    """Validate and uppercase an ISO 4217 currency code such as ``USD``."""

    currency = value.strip().upper()

    if currency not in _ISO_4217_CODES:
        raise DomainValidationError(
            "INVALID_CURRENCY",
            "Choose a valid ISO 4217 currency code.",
            "currency",
        )
    return currency


def is_safe_redirect_path(value: object) -> TypeGuard[str]:
    """Accept only local absolute paths that cannot leave the site.

    ``//host`` and backslashes are rejected because browsers can treat them as protocol-relative
    URLs. Raw or percent-encoded control characters are rejected to prevent header injection and
    response splitting.
    """

    if not isinstance(value, str) or not value:
        return False
    if not value.startswith("/") or value.startswith("//"):
        return False
    if "\\" in value:
        return False
    if any(
        character.isspace() or ord(character) < 0x20 or ord(character) == 0x7F
        for character in value
    ):
        return False

    lowered = value.lower()
    return not any(sequence in lowered for sequence in _UNSAFE_ENCODED_REDIRECT_SEQUENCES)


def safe_redirect_path(value: str | None, default: str = "/account") -> str:
    """Return the requested path when it is safe, otherwise the default path."""

    return value if is_safe_redirect_path(value) else default
