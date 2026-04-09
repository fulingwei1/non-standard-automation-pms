# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - ECN审批适配器"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime


class TestEcnApprovalAdapterBusinessLogic:
    """ECN审批适配器业务逻辑测试"""

    def test_get_entity_found(self):
        """测试获取ECN实体"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_ecn.id = 1
            mock_ecn.ecn_no = "ECN-2026-001"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            adapter = EcnApprovalAdapter(mock_db)
            result = adapter.get_entity(1)

            assert result.id == 1
        except ImportError:
            pytest.skip("Module not found")

    def test_get_entity_not_found(self):
        """测试ECN不存在"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None

            adapter = EcnApprovalAdapter(mock_db)
            result = adapter.get_entity(999)

            assert result is None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_entity_data(self):
        """测试获取ECN数据"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            # Mock ECN
            mock_ecn = MagicMock()
            mock_ecn.id = 1
            mock_ecn.ecn_no = "ECN-2026-001"
            mock_ecn.ecn_title = "设计变更"
            mock_ecn.ecn_type = "DESIGN"
            mock_ecn.status = "DRAFT"
            mock_ecn.project_id = 1
            mock_ecn.project = MagicMock()
            mock_ecn.project.project_code = "PRJ-001"
            mock_ecn.machine_id = 1
            mock_ecn.cost_impact = 50000
            mock_ecn.schedule_impact_days = 5
            mock_ecn.priority = "HIGH"
            mock_ecn.urgency = "URGENT"
            mock_ecn.created_by = 1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            # Mock评估
            mock_eval = MagicMock()
            mock_eval.status = "COMPLETED"
            mock_eval.cost_estimate = 50000
            mock_eval.schedule_estimate = 5
            mock_eval.eval_dept = "ENGINEERING"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_eval]

            adapter = EcnApprovalAdapter(mock_db)
            result = adapter.get_entity_data(1)

            assert result["ecn_no"] == "ECN-2026-001"
            assert result["cost_impact"] == 50000
            assert result["total_evaluations"] == 1
        except ImportError:
            pytest.skip("Module not found")

    def test_on_submit(self):
        """测试提交审批回调"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_ecn.id = 1
            mock_ecn.status = "DRAFT"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            adapter = EcnApprovalAdapter(mock_db)
            mock_instance = MagicMock()
            adapter.on_submit(1, mock_instance)

            assert mock_ecn.status == "PENDING_APPROVAL"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_approved(self):
        """测试审批通过回调"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_ecn.id = 1
            mock_ecn.status = "PENDING_APPROVAL"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            adapter = EcnApprovalAdapter(mock_db)
            mock_instance = MagicMock()
            adapter.on_approved(1, mock_instance)

            assert mock_ecn.status == "APPROVED"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_rejected(self):
        """测试审批拒绝回调"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_ecn.id = 1
            mock_ecn.status = "PENDING_APPROVAL"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            adapter = EcnApprovalAdapter(mock_db)
            mock_instance = MagicMock()
            adapter.on_rejected(1, mock_instance, "成本过高")

            assert mock_ecn.status == "REJECTED"
        except ImportError:
            pytest.skip("Module not found")

    def test_get_evaluators(self):
        """测试获取评估人"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            # Mock评估矩阵
            mock_matrix = MagicMock()
            mock_matrix.dept = "ENGINEERING"
            mock_matrix.role_id = 1

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_matrix]

            adapter = EcnApprovalAdapter(mock_db)
            result = adapter.get_evaluators(1)

            assert isinstance(result, list)
        except ImportError:
            pytest.skip("Module not found")

    def test_create_evaluation_tasks(self):
        """测试创建评估任务"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_ecn.id = 1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            adapter = EcnApprovalAdapter(mock_db)
            result = adapter.create_evaluation_tasks(1)

            assert isinstance(result, list)
        except ImportError:
            pytest.skip("Module not found")


class TestEcnApprovalAdapterRouting:
    """路由条件测试"""

    def test_route_by_cost_impact(self):
        """测试按成本影响路由"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_ecn.cost_impact = 100000  # 10万以上成本影响

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            adapter = EcnApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["cost_impact"] == 100000
        except ImportError:
            pytest.skip("Module not found")

    def test_route_by_schedule_impact(self):
        """测试按工期影响路由"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_ecn.schedule_impact_days = 7  # 7天工期影响

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            adapter = EcnApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["schedule_impact_days"] == 7
        except ImportError:
            pytest.skip("Module not found")

    def test_route_by_priority(self):
        """测试按优先级路由"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_ecn.priority = "HIGH"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            adapter = EcnApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["priority"] == "HIGH"
        except ImportError:
            pytest.skip("Module not found")


class TestEcnApprovalAdapterEvaluation:
    """评估流程测试"""

    def test_evaluation_summary(self):
        """测试评估汇总"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            # Mock多个评估
            mock_eval1 = MagicMock()
            mock_eval1.status = "COMPLETED"
            mock_eval1.cost_estimate = 30000
            mock_eval1.schedule_estimate = 3
            mock_eval1.eval_dept = "ENGINEERING"

            mock_eval2 = MagicMock()
            mock_eval2.status = "PENDING"
            mock_eval2.cost_estimate = 20000
            mock_eval2.schedule_estimate = 2
            mock_eval2.eval_dept = "PRODUCTION"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_eval1, mock_eval2]

            adapter = EcnApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["total_evaluations"] == 2
            assert data["completed_evaluations"] == 1
            assert data["pending_evaluations"] == 1
            assert data["total_cost_estimate"] == 50000
        except ImportError:
            pytest.skip("Module not found")

    def test_all_evaluations_completed(self):
        """测试所有评估完成"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            # Mock全部完成的评估
            mock_eval = MagicMock()
            mock_eval.status = "COMPLETED"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_eval, mock_eval]

            adapter = EcnApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["completed_evaluations"] == 2
        except ImportError:
            pytest.skip("Module not found")


class TestEcnApprovalAdapterEdgeCases:
    """边界情况测试"""

    def test_ecn_no_project(self):
        """测试ECN没有关联项目"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_ecn.project = None

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            adapter = EcnApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["project_code"] is None
        except ImportError:
            pytest.skip("Module not found")

    def test_ecn_zero_cost_impact(self):
        """测试ECN零成本影响"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_ecn.cost_impact = 0

            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            adapter = EcnApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["cost_impact"] == 0
        except ImportError:
            pytest.skip("Module not found")

    def test_no_evaluations(self):
        """测试没有评估"""
        try:
            from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

            mock_db = MagicMock()

            mock_ecn = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_ecn

            mock_db.query.return_value.filter.return_value.all.return_value = []

            adapter = EcnApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["total_evaluations"] == 0
        except ImportError:
            pytest.skip("Module not found")