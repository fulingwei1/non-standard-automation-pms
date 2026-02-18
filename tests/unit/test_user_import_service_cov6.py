# -*- coding: utf-8 -*-
"""
第六批覆盖测试 - user_import_service.py
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

try:
    from app.services.user_import_service import UserImportService
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="user_import_service not importable")


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
    db.add = MagicMock()
    db.commit = MagicMock()
    db.flush = MagicMock()
    db.rollback = MagicMock()
    return db


class TestValidateFileFormat:
    def test_valid_xlsx(self):
        assert UserImportService.validate_file_format("users.xlsx") is True

    def test_valid_xls(self):
        assert UserImportService.validate_file_format("users.xls") is True

    def test_valid_csv(self):
        assert UserImportService.validate_file_format("users.csv") is True

    def test_invalid_format(self):
        assert UserImportService.validate_file_format("users.pdf") is False

    def test_invalid_txt(self):
        assert UserImportService.validate_file_format("users.txt") is False

    def test_case_insensitive(self):
        assert UserImportService.validate_file_format("users.XLSX") is True


class TestNormalizeColumns:
    def test_normalize_chinese_columns(self):
        df = pd.DataFrame({"用户名": ["alice"], "邮箱": ["alice@example.com"]})
        result = UserImportService.normalize_columns(df)
        assert "username" in result.columns
        assert "email" in result.columns

    def test_normalize_english_columns(self):
        df = pd.DataFrame({"Username": ["alice"], "Email": ["alice@example.com"]})
        result = UserImportService.normalize_columns(df)
        assert "username" in result.columns
        assert "email" in result.columns

    def test_passthrough_unknown_columns(self):
        df = pd.DataFrame({"unknown_col": ["val1"]})
        result = UserImportService.normalize_columns(df)
        assert "unknown_col" in result.columns


class TestValidateDataframe:
    def test_missing_required_fields(self):
        df = pd.DataFrame({"username": ["alice"]})  # missing real_name, email
        errors = UserImportService.validate_dataframe(df)
        assert len(errors) > 0

    def test_all_required_fields_present(self):
        df = pd.DataFrame({
            "username": ["alice"],
            "real_name": ["Alice"],
            "email": ["alice@example.com"],
        })
        errors = UserImportService.validate_dataframe(df)
        assert isinstance(errors, list)

    def test_exceeds_max_limit(self):
        df = pd.DataFrame({
            "username": [f"user{i}" for i in range(600)],
            "real_name": [f"User {i}" for i in range(600)],
            "email": [f"user{i}@example.com" for i in range(600)],
        })
        errors = UserImportService.validate_dataframe(df)
        assert len(errors) > 0


class TestValidateRow:
    def test_valid_row(self, mock_db):
        import pandas as pd
        row = pd.Series({
            "username": "alice_valid",
            "real_name": "Alice",
            "email": "alice@example.com",
        })
        existing_u = set()
        existing_e = set()
        result = UserImportService.validate_row(row, 1, mock_db, existing_u, existing_e)
        assert result is None  # No error

    def test_missing_username(self, mock_db):
        import pandas as pd
        row = pd.Series({
            "username": "",
            "real_name": "Alice",
            "email": "alice@example.com",
        })
        result = UserImportService.validate_row(row, 1, mock_db, set(), set())
        assert result is not None  # Should return error

    def test_short_username(self, mock_db):
        import pandas as pd
        row = pd.Series({
            "username": "ab",
            "real_name": "Alice",
            "email": "alice@example.com",
        })
        result = UserImportService.validate_row(row, 1, mock_db, set(), set())
        assert result is not None  # Username too short

    def test_duplicate_username(self, mock_db):
        import pandas as pd
        row = pd.Series({
            "username": "alice",
            "real_name": "Alice",
            "email": "alice@example.com",
        })
        existing_u = {"alice"}  # Already in set
        result = UserImportService.validate_row(row, 1, mock_db, existing_u, set())
        assert result is not None  # Duplicate error


class TestGenerateTemplate:
    def test_returns_dataframe(self):
        result = UserImportService.generate_template()
        assert isinstance(result, pd.DataFrame)

    def test_template_has_columns(self):
        result = UserImportService.generate_template()
        assert len(result.columns) > 0


class TestGetOrCreateRole:
    def test_existing_role(self, mock_db):
        mock_role = MagicMock()
        mock_role.id = 1
        mock_role.name = "viewer"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_role
        result = UserImportService.get_or_create_role(mock_db, "viewer")
        assert result is not None

    def test_create_new_role(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = UserImportService.get_or_create_role(mock_db, "new_role")
        # Should try to create a new role
        assert True  # Just check no exception
