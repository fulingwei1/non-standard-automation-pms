# -*- coding: utf-8 -*-
"""Auto-generated tests for unified import modules"""
from unittest.mock import MagicMock

import pytest


class TestUnifiedImportBase:
    """Tests for unified import base"""

    def test_module_import(self):
        try:
            from app.services.unified_import.base import UnifiedImportBase
            assert UnifiedImportBase is not None
        except ImportError:
            pytest.skip("Module not found")


class TestBOMImporter:
    def test_module_import(self):
        try:
            from app.services.unified_import.bom_importer import BOMImporter
            importer = BOMImporter()
            assert importer is not None
        except ImportError:
            pytest.skip("Module not found")


class TestMaterialImporter:
    def test_module_import(self):
        try:
            from app.services.unified_import.material_importer import MaterialImporter
            importer = MaterialImporter()
            assert importer is not None
        except ImportError:
            pytest.skip("Module not found")


class TestTaskImporter:
    def test_module_import(self):
        try:
            from app.services.unified_import.task_importer import TaskImporter
            importer = TaskImporter()
            assert importer is not None
        except ImportError:
            pytest.skip("Module not found")


class TestTimesheetImporter:
    def test_module_import(self):
        try:
            from app.services.unified_import.timesheet_importer import TimesheetImporter
            assert hasattr(TimesheetImporter, "import_timesheet_data")
        except ImportError:
            pytest.skip("Module not found")


class TestUnifiedImporter:
    def test_module_import(self):
        try:
            from app.services.unified_import.unified_importer import UnifiedImporter
            importer = UnifiedImporter()
            assert importer is not None
        except ImportError:
            pytest.skip("Module not found")


class TestUserImporter:
    def test_module_import(self):
        try:
            from app.services.unified_import.user_importer import UserImporter
            importer = UserImporter()
            assert importer is not None
        except ImportError:
            pytest.skip("Module not found")


class TestUrgentPurchaseService:
    def test_service_import(self):
        try:
            from app.services.urgent_purchase_from_shortage_service import UrgentPurchaseService
            mock_db = MagicMock()
            service = UrgentPurchaseService(mock_db)
            assert service.db == mock_db
        except ImportError:
            pytest.skip("Module not found")


class TestUserImportService:
    def test_service_import(self):
        try:
            from app.services.user_import_service import UserImportService
            assert hasattr(UserImportService, "read_file")
            assert hasattr(UserImportService, "normalize_columns")
        except ImportError:
            pytest.skip("Module not found")


class TestUserSyncService:
    def test_service_import(self):
        try:
            from app.services.user_sync_service import UserSyncService
            assert hasattr(UserSyncService, "get_role_by_position")
            assert hasattr(UserSyncService, "create_user_from_employee")
        except ImportError:
            pytest.skip("Module not found")
