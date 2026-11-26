import pytest

from app.modules.administration.domain import (
    CategoryValidationError,
    name_key,
    normalize_description,
    normalize_name,
    validate_slug,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  کوتاهی مو ", "کوتاهی مو"),
        ("Hair  Cut", "Hair Cut"),
        ("رنگ", "رنگ"),
    ],
)
def test_normalize_name_trims_and_collapses_whitespace(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "a", "\tنام", "نام\x00", "x" * 81])
def test_normalize_name_rejects_invalid_values(raw: str) -> None:
    with pytest.raises(CategoryValidationError) as error:
        normalize_name(raw)
    assert error.value.field == "name"


def test_name_key_is_case_insensitive_and_whitespace_stable() -> None:
    assert name_key("Hair") == name_key("  hair ")
    assert name_key("Hair  Cut") == name_key("hair cut")
    assert name_key("کوتاهی مو") == name_key("کوتاهی مو")


@pytest.mark.parametrize(
    "slug",
    ["haircut", "hair-cut", "nails2", "a", "a-b-c", "x" * 80],
)
def test_valid_slugs_are_accepted(slug: str) -> None:
    assert validate_slug(slug) == slug


@pytest.mark.parametrize(
    "slug",
    [
        "",
        "   ",
        "Hair",
        "hair cut",
        "-hair",
        "hair-",
        "hair--cut",
        "hair_cut",
        "کوتاهی",
        "x" * 81,
        "hair/../cut",
    ],
)
def test_invalid_slugs_are_rejected(slug: str) -> None:
    with pytest.raises(CategoryValidationError) as error:
        validate_slug(slug)
    assert error.value.field == "slug"


@pytest.mark.parametrize("value", [None, "", "   "])
def test_empty_description_becomes_none(value: str | None) -> None:
    assert normalize_description(value) is None


def test_description_is_trimmed_and_allows_newlines() -> None:
    assert normalize_description("  خط اول\nخط دوم  ") == "خط اول\nخط دوم"


def test_description_rejects_control_characters_and_overlong_text() -> None:
    for value in ("نام\x00", "x" * 501):
        with pytest.raises(CategoryValidationError) as error:
            normalize_description(value)
        assert error.value.field == "description"
