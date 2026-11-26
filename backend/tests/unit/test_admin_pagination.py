"""The pagination cursor is opaque, round-trips exactly, and never raises a 500."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.modules.administration.domain import (
    MAX_PAGE_LIMIT,
    decode_cursor,
    encode_cursor,
    ensure_limit_is_supported,
)
from app.modules.identity.domain import DomainValidationError

USER_ID = uuid.UUID("8f14e45f-ea2f-4c1b-9b7a-1f3c2d4e5f60")
MOMENT = datetime(2026, 11, 25, 10, 15, 30, tzinfo=UTC)


def test_a_cursor_round_trips_the_sort_key() -> None:
    moment, user_id = decode_cursor(encode_cursor(MOMENT, USER_ID))

    assert moment == MOMENT
    assert user_id == USER_ID


def test_a_cursor_is_url_safe_and_opaque() -> None:
    cursor = encode_cursor(MOMENT, USER_ID)

    assert str(USER_ID) not in cursor
    assert "=" not in cursor
    assert cursor == cursor.strip()


def test_an_offset_timezone_is_preserved() -> None:
    moment = datetime(2026, 11, 25, 13, 45, tzinfo=timezone(timedelta(hours=3, minutes=30)))

    decoded, _ = decode_cursor(encode_cursor(moment, USER_ID))

    assert decoded == moment


def test_a_naive_timestamp_is_encoded_as_utc() -> None:
    decoded, _ = decode_cursor(encode_cursor(MOMENT.replace(tzinfo=None), USER_ID))

    assert decoded == MOMENT


@pytest.mark.parametrize(
    "cursor",
    [
        "",
        "not-a-cursor",
        "!!!",
        encode_cursor(MOMENT, USER_ID) + "extra",
        "MjAyNi0xMS0yNVQxMDoxNTozMCswMDowMHxub3QtYS11dWlk",
        "MjAyNi0xMS0yNVQxMDoxNTozMHxub3QtYS11dWlk",
    ],
)
def test_a_malformed_cursor_is_a_client_error(cursor: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        decode_cursor(cursor)

    assert error.value.code == "INVALID_CURSOR"
    assert error.value.field == "cursor"


@pytest.mark.parametrize("limit", [1, MAX_PAGE_LIMIT])
def test_supported_page_sizes_are_accepted(limit: int) -> None:
    assert ensure_limit_is_supported(limit) == limit


@pytest.mark.parametrize("limit", [0, -1, MAX_PAGE_LIMIT + 1])
def test_unsupported_page_sizes_are_rejected(limit: int) -> None:
    with pytest.raises(DomainValidationError) as error:
        ensure_limit_is_supported(limit)

    assert error.value.code == "INVALID_PAGE_LIMIT"
