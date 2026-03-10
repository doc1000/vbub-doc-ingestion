"""Tests for tag_policy_service.validate_tags."""

import pytest

from ingestion_service.app.services.tag_policy_service import validate_tags


def test_none_returns_empty_list() -> None:
    assert validate_tags(None) == []


def test_empty_list_returns_empty_list() -> None:
    assert validate_tags([]) == []


def test_tags_are_lowercased_and_stripped() -> None:
    result = validate_tags(["  Finance ", "RESEARCH"])
    assert result == ["finance", "research"]


def test_empty_strings_are_discarded() -> None:
    result = validate_tags(["", "  ", "valid"])
    assert result == ["valid"]


def test_duplicates_are_removed_preserving_order() -> None:
    result = validate_tags(["alpha", "beta", "alpha", "gamma", "beta"])
    assert result == ["alpha", "beta", "gamma"]


def test_max_20_tags_accepted() -> None:
    tags = [f"tag{i}" for i in range(20)]
    result = validate_tags(tags)
    assert len(result) == 20


def test_21_tags_raises() -> None:
    tags = [f"tag{i}" for i in range(21)]
    with pytest.raises(ValueError, match="Too many tags"):
        validate_tags(tags)


def test_tag_over_50_chars_raises() -> None:
    long_tag = "a" * 51
    with pytest.raises(ValueError, match="exceeds the maximum length"):
        validate_tags([long_tag])


def test_tag_exactly_50_chars_accepted() -> None:
    tag = "a" * 50
    result = validate_tags([tag])
    assert result == [tag]
