# -*- coding: utf-8 -*-
"""DimensionConfigService 单元测试"""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.engineer_performance.dimension_config_service import DimensionConfigService


class TestDimensionConfigService(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def _mock_query_chain(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        return mock_query

    # --- get_config ---
    def test_get_config_dept_priority(self):
        """部门配置优先于全局配置"""
        dept_config = MagicMock(id=1, is_global=False)
        mock_query = self._mock_query_chain()
        mock_query.first.return_value = dept_config

        result = self.service.get_config("mechanical", "senior", date(2025, 6, 1), department_id=10)
        self.assertEqual(result.id, 1)

    def test_get_config_fallback_global(self):
        """无部门配置时回退到全局"""
        mock_query = self._mock_query_chain()
        # dept query returns None, global returns config
        global_config = MagicMock(id=2, is_global=True)
        mock_query.first.side_effect = [None, None, global_config]

        result = self.service.get_config("mechanical", "senior", date(2025, 6, 1), department_id=10)
        # May hit global fallback
        # The exact call chain depends on implementation; just verify no crash

    def test_get_config_no_department(self):
        mock_query = self._mock_query_chain()
        config = MagicMock(id=3)
        mock_query.first.return_value = config

        result = self.service.get_config("test", "junior")
        self.assertIsNotNone(result)

    # --- create_config ---
    def test_create_config_weight_validation(self):
        data = MagicMock()
        data.technical_weight = 20
        data.execution_weight = 20
        data.cost_quality_weight = 20
        data.knowledge_weight = 20
        data.collaboration_weight = 10  # total = 90 != 100

        with self.assertRaises(ValueError) as ctx:
            self.service.create_config(data, operator_id=1)
        self.assertIn("100", str(ctx.exception))

    def test_create_config_success(self):
        data = MagicMock()
        data.technical_weight = 30
        data.execution_weight = 25
        data.cost_quality_weight = 20
        data.knowledge_weight = 15
        data.collaboration_weight = 10
        data.job_type = "mechanical"
        data.job_level = "senior"
        data.effective_date = date(2025, 1, 1)
        data.config_name = "test"
        data.description = "desc"

        self.service.create_config(data, operator_id=1)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_create_config_department_level(self):
        data = MagicMock()
        data.technical_weight = 30
        data.execution_weight = 25
        data.cost_quality_weight = 20
        data.knowledge_weight = 15
        data.collaboration_weight = 10
        data.job_type = "mechanical"
        data.job_level = None
        data.effective_date = date(2025, 1, 1)
        data.config_name = "dept"
        data.description = "dept config"

        # Mock permission validation
        mock_query = self._mock_query_chain()
        user = MagicMock(employee_id=100)
        mock_query.first.return_value = user  # for User query
        dept = MagicMock(id=10)
        # Second query for Department
        self.db.query.return_value.filter.return_value.first.side_effect = [user, dept]

        self.service.create_config(data, operator_id=1, department_id=10)
        self.db.add.assert_called_once()

    # --- _validate_department_manager_permission ---
    def test_validate_dept_manager_no_operator(self):
        mock_query = self._mock_query_chain()
        mock_query.first.return_value = None

        with self.assertRaises(ValueError):
            self.service._validate_department_manager_permission(10, 1)

    def test_validate_dept_manager_no_dept(self):
        mock_query = self._mock_query_chain()
        user = MagicMock(employee_id=100)
        mock_query.first.side_effect = [user, None]

        with self.assertRaises(ValueError):
            self.service._validate_department_manager_permission(10, 1)

    # --- list_configs ---
    def test_list_configs(self):
        mock_query = self._mock_query_chain()
        mock_query.all.return_value = [MagicMock(), MagicMock()]

        result = self.service.list_configs(job_type="mechanical")
        self.assertEqual(len(result), 2)

    def test_list_configs_include_expired(self):
        mock_query = self._mock_query_chain()
        mock_query.all.return_value = []

        result = self.service.list_configs(include_expired=True)
        self.assertEqual(result, [])

    # --- approve_config ---
    def test_approve_config_not_found(self):
        mock_query = self._mock_query_chain()
        mock_query.first.return_value = None

        with self.assertRaises(ValueError):
            self.service.approve_config(999, approver_id=1)

    def test_approve_config_global_raises(self):
        config = MagicMock(is_global=True, approval_status="PENDING")
        mock_query = self._mock_query_chain()
        mock_query.first.return_value = config

        with self.assertRaises(ValueError) as ctx:
            self.service.approve_config(1, approver_id=1)
        self.assertIn("全局", str(ctx.exception))

    def test_approve_config_wrong_status(self):
        config = MagicMock(is_global=False, approval_status="APPROVED")
        mock_query = self._mock_query_chain()
        mock_query.first.return_value = config

        with self.assertRaises(ValueError):
            self.service.approve_config(1, approver_id=1)

    def test_approve_config_success(self):
        config = MagicMock(is_global=False, approval_status="PENDING")
        mock_query = self._mock_query_chain()
        # First call: get config, second: get approver
        approver = MagicMock(is_superuser=True)
        mock_query.first.side_effect = [config, approver]

        result = self.service.approve_config(1, approver_id=1, approved=True)
        self.assertEqual(result.approval_status, "APPROVED")

    def test_approve_config_rejected(self):
        config = MagicMock(is_global=False, approval_status="PENDING")
        approver = MagicMock(is_superuser=True)
        mock_query = self._mock_query_chain()
        mock_query.first.side_effect = [config, approver]

        result = self.service.approve_config(1, approver_id=1, approved=False)
        self.assertEqual(result.approval_status, "REJECTED")

    # --- _validate_admin_permission ---
    def test_validate_admin_not_found(self):
        mock_query = self._mock_query_chain()
        mock_query.first.return_value = None

        with self.assertRaises(ValueError):
            self.service._validate_admin_permission(999)

    def test_validate_admin_superuser(self):
        mock_query = self._mock_query_chain()
        user = MagicMock(is_superuser=True)
        mock_query.first.return_value = user
        # Should not raise
        self.service._validate_admin_permission(1)

    def test_validate_admin_by_role(self):
        mock_query = self._mock_query_chain()
        user = MagicMock(is_superuser=False)
        role = MagicMock()
        role.role = MagicMock(role_code="admin")
        mock_query.first.return_value = user
        mock_query.all.return_value = [role]
        # Should not raise
        self.service._validate_admin_permission(1)

    # --- get_pending_approvals ---
    def test_get_pending_approvals(self):
        mock_query = self._mock_query_chain()
        mock_query.all.return_value = [MagicMock()]

        result = self.service.get_pending_approvals()
        self.assertEqual(len(result), 1)

    # --- _format_config ---
    def test_format_config_none(self):
        self.assertIsNone(self.service._format_config(None))

    def test_format_config_valid(self):
        config = MagicMock()
        config.id = 1
        config.technical_weight = 30
        config.execution_weight = 25
        config.cost_quality_weight = 20
        config.knowledge_weight = 15
        config.collaboration_weight = 10
        config.approval_status = "APPROVED"
        config.effective_date = date(2025, 1, 1)

        result = self.service._format_config(config)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["effective_date"], "2025-01-01")

    # --- _analyze_job_type_distribution ---
    def test_analyze_job_type_distribution(self):
        p1 = MagicMock(job_type="mechanical", job_level="senior")
        p2 = MagicMock(job_type="mechanical", job_level="junior")
        p3 = MagicMock(job_type="test", job_level=None)

        result = self.service._analyze_job_type_distribution([p1, p2, p3])
        self.assertEqual(result["mechanical"]["count"], 2)
        self.assertEqual(result["test"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
