"""Framework-free pagination rules for the administrator user list.

The cursor is opaque to clients on purpose: it carries the sort key of the last row on the page
(``created_at`` and ``id``), so the next page is a keyset query rather than an offset. An offset
would skip or repeat rows whenever a user is created between two requests.

Nothing here imports FastAPI or SQLAlchemy, so the encoding rules are unit-testable and cannot
leak persistence details into the HTTP layer.
"""

from __future__ import annotations

import base64
import binascii
import uuid
from datetime import UTC, datetime

from app.modules.identity.domain import DomainValidationError

DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 100
CURSOR_MAX_LENGTH = 512


def _invalid_cursor() -> DomainValidationError:
    return DomainValidationError(
        "INVALID_CURSOR",
        "The pagination cursor is not valid. Start again without a cursor.",
        "cursor",
    )


def encode_cursor(created_at: datetime, user_id: uuid.UUID) -> str:
    """Encode the sort key of the last row on a page as an opaque cursor.

    A naive timestamp is treated as UTC because the database always stores instants; the cursor
    must never depend on the server's local timezone.
    """

    moment = created_at if created_at.tzinfo is not None else created_at.replace(tzinfo=UTC)
    raw = f"{moment.isoformat()}|{user_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Return the sort key stored in ``cursor`` or raise ``INVALID_CURSOR``.

    Every malformed input — wrong alphabet, missing separator, unusable timestamp, unusable id,
    or a timestamp without a timezone — is the same client error. It must never become a 500.
    """

    padded = cursor + "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, UnicodeEncodeError, ValueError) as error:
        raise _invalid_cursor() from error

    moment_text, separator, id_text = raw.partition("|")
    if not separator or not moment_text or not id_text:
        raise _invalid_cursor()

    try:
        moment = datetime.fromisoformat(moment_text)
        user_id = uuid.UUID(id_text)
    except ValueError as error:
        raise _invalid_cursor() from error

    if moment.tzinfo is None:
        raise _invalid_cursor()

    return moment, user_id


def ensure_limit_is_supported(limit: int) -> int:
    """Reject a page size outside the supported range.

    The HTTP layer validates this too; the use case re-checks because it is the last place that
    can protect the database from an unbounded query.
    """

    if limit < 1 or limit > MAX_PAGE_LIMIT:
        raise DomainValidationError(
            "INVALID_PAGE_LIMIT",
            f"Choose a page size between 1 and {MAX_PAGE_LIMIT}.",
            "limit",
        )
    return limit
