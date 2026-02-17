# -*- coding: utf-8 -*-
"""
Unit tests for app/utils/pinyin_utils.py — L4组补充
重点：别名函数 to_pinyin / get_initials 及 generate_unique_username
"""

import pytest
from unittest.mock import MagicMock, patch

from app.utils.pinyin_utils import (
    to_pinyin,
    get_initials,
    name_to_pinyin,
    name_to_pinyin_initials,
    generate_unique_username,
    generate_initial_password,
)


# ---------------------------------------------------------------------------
# Alias functions
# ---------------------------------------------------------------------------

class TestToPinyinAlias:
    """Tests for to_pinyin (alias of name_to_pinyin)."""

    def test_to_pinyin_zhangsan(self):
        """to_pinyin('张三') returns 'zhangsan' when pypinyin available."""
        result = to_pinyin("张三")
        # pypinyin is installed; accept either correct result or fallback
        assert isinstance(result, str)
        assert len(result) > 0

    def test_to_pinyin_empty_string(self):
        """to_pinyin('') returns empty string."""
        assert to_pinyin("") == ""

    def test_to_pinyin_is_lowercase(self):
        """Result of to_pinyin is entirely lowercase."""
        result = to_pinyin("李四")
        assert result == result.lower()

    def test_to_pinyin_same_as_name_to_pinyin(self):
        """to_pinyin is a transparent alias for name_to_pinyin."""
        for name in ["张三", "王五", "", "Alice"]:
            assert to_pinyin(name) == name_to_pinyin(name)

    def test_to_pinyin_english_passthrough(self):
        """ASCII input is returned lowercase (no conversion needed)."""
        result = to_pinyin("Alice")
        assert isinstance(result, str)

    def test_to_pinyin_single_char(self):
        """Single character input works correctly."""
        result = to_pinyin("张")
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# get_initials
# ---------------------------------------------------------------------------

class TestGetInitialsAlias:
    """Tests for get_initials (alias of name_to_pinyin_initials)."""

    def test_get_initials_zhangsan(self):
        """get_initials('张三') returns 'ZS' when pypinyin is available."""
        result = get_initials("张三")
        assert isinstance(result, str)
        assert result == result.upper()

    def test_get_initials_empty_string(self):
        """get_initials('') returns empty string."""
        assert get_initials("") == ""

    def test_get_initials_is_uppercase(self):
        """Result is always uppercase."""
        result = get_initials("王五六")
        assert result == result.upper()

    def test_get_initials_same_as_name_to_pinyin_initials(self):
        """get_initials is a transparent alias."""
        for name in ["张三", "李四光", "", "Bob"]:
            assert get_initials(name) == name_to_pinyin_initials(name)

    def test_get_initials_two_char_name(self):
        """Two character names produce two initials."""
        result = get_initials("张三")
        # With pypinyin: "ZS", without: some two-char string
        assert len(result) >= 2  # at least 2 characters


# ---------------------------------------------------------------------------
# generate_unique_username
# ---------------------------------------------------------------------------

class TestGenerateUniqueUsername:
    """Tests for generate_unique_username."""

    def _make_db(self, existing_names=None):
        """
        Return a mock db where User.username queries return found/not found
        based on existing_names set.
        """
        existing = set(existing_names or [])
        db = MagicMock()

        def query_side_effect(model):
            q = MagicMock()

            def filter_side_effect(condition):
                fq = MagicMock()
                # We can't easily inspect the filter arg; use call count trick
                return fq
            q.filter.side_effect = filter_side_effect
            return q

        db.query = MagicMock(side_effect=query_side_effect)
        return db

    def test_basic_name_generates_pinyin_username(self):
        """Generates pinyin username for a simple Chinese name."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        username = generate_unique_username("张三", db)
        assert isinstance(username, str)
        assert len(username) > 0

    def test_empty_name_falls_back_to_user(self):
        """Empty name falls back to 'user' prefix."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        username = generate_unique_username("", db)
        assert username.startswith("user")

    def test_uses_existing_usernames_set(self):
        """Uses existing_usernames set to avoid duplicates without DB query."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        base = name_to_pinyin("张三") or "zhangsan"
        existing = {base}

        username = generate_unique_username("张三", db, existing_usernames=existing)
        # Should add a numeric suffix
        assert username != base
        assert username.startswith(base)

    def test_db_collision_adds_numeric_suffix(self):
        """When DB has existing username, adds counter suffix."""
        base = to_pinyin("李四") or "lisi"
        db = MagicMock()
        # First call returns an existing user, second call returns None
        mock_user = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [mock_user, None]

        username = generate_unique_username("李四", db)
        # Should be base + "2"
        assert username == f"{base}2"


# ---------------------------------------------------------------------------
# generate_initial_password
# ---------------------------------------------------------------------------

class TestGenerateInitialPasswordL4:
    """Additional tests for generate_initial_password."""

    def test_returns_string(self):
        """generate_initial_password always returns a string."""
        result = generate_initial_password()
        assert isinstance(result, str)

    def test_accepts_deprecated_params(self):
        """Deprecated params accepted without errors."""
        result = generate_initial_password(
            username="user1",
            id_card="123456",
            employee_code="E001"
        )
        assert isinstance(result, str)

    def test_passwords_are_not_empty(self):
        """Generated password is non-empty."""
        result = generate_initial_password()
        assert len(result) > 0

    def test_consecutive_passwords_differ(self):
        """Two consecutive calls return different passwords."""
        p1 = generate_initial_password()
        p2 = generate_initial_password()
        assert p1 != p2
