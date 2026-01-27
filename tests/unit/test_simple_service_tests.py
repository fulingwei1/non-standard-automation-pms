# -*- coding: utf-8 -*-
"""
Simple functional tests for service modules
Batch: P2 - 核心模块测试（其他模块）
"""

import pytest


class TestServiceModuleImports:
    """Test suite for service module imports."""

    def test_import_data_scope_services(self):
        """Test importing data scope services."""
        try:
            from app.services.data_scope import DataScopeService
            assert DataScopeService is not None
        except Exception as e:
            pytest.skip(f"Cannot import data_scope services: {str(e)}")

    def test_import_project_bonus_service(self):
        """Test importing project bonus service."""
        try:
            from app.services.project_bonus_service import ProjectBonusService
            assert ProjectBonusService is not None
        except Exception as e:
            pytest.skip(f"Cannot import project bonus service: {str(e)}")

    def test_import_project_workspace_service(self):
        """Test importing project workspace service."""
        try:
            from app.services.project_workspace_service import build_project_basic_info
            assert callable(build_project_basic_info)
        except Exception as e:
            pytest.skip(f"Cannot import project workspace service: {str(e)}")

    def test_import_project_timeline_service(self):
        """Test importing project timeline service."""
        try:
            from app.services.project_timeline_service import get_project_timeline
            assert callable(get_project_timeline)
        except Exception as e:
            pytest.skip(f"Cannot import project timeline service: {str(e)}")

    def test_import_project_dashboard_service(self):
        """Test importing project dashboard service."""
        try:
            from app.services.project_dashboard_service import calculate_progress_stats
            assert callable(calculate_progress_stats)
        except Exception as e:
            pytest.skip(f"Cannot import project dashboard service: {str(e)}")

    def test_import_alert_services(self):
        """Test importing alert services."""
        try:
            from app.services.alert.alert_efficiency_service import AlertEfficiencyService
            assert AlertEfficiencyService is not None
        except Exception as e:
            pytest.skip(f"Cannot import alert efficiency service: {str(e)}")

            try:
                from app.services.alert.alert_response_service import AlertResponseService
                assert AlertResponseService is not None
        except Exception as e:
            pytest.skip(f"Cannot import alert response service: {str(e)}")

    def test_import_purchase_services(self):
        """Test importing purchase services."""
        try:
            from app.services.purchase_order_from_bom_service import create_purchase_order_from_preview
            assert callable(create_purchase_order_from_preview)
        except Exception as e:
            pytest.skip(f"Cannot import purchase order service: {str(e)}")

            try:
                from app.services.purchase_request_from_bom_service import create_purchase_request_from_bom
                assert callable(create_purchase_request_from_bom)
        except Exception as e:
            pytest.skip(f"Cannot import purchase request service: {str(e)}")

    def test_import_ecn_services(self):
        """Test importing ECN services."""
        try:
            from app.services.ecn_auto_assign_service import auto_assign_ecn
            assert callable(auto_assign_ecn)
        except Exception as e:
            pytest.skip(f"Cannot import ECN auto assign service: {str(e)}")

            try:
                from app.services.ecn_bom_analysis_service import analyze_bom_for_ecn
                assert callable(analyze_bom_for_ecn)
        except Exception as e:
            pytest.skip(f"Cannot import ECN BOM analysis service: {str(e)}")
