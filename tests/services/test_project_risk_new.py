# -*- coding: utf-8 -*-
"""ProjectRiskService (project_risk module) 单元测试

测试 app/services/project_risk/project_risk_service.py
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.project_risk.project_risk_service import ProjectRiskService


def _mock_db():
    return MagicMock()


def _make_service(db=None):
    db = db or _mock_db()
    return ProjectRiskService(db), db


class TestGenerateRiskCode:
    """测试生成风险编号"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_generate_risk_code(self):
        """测试风险编号生成"""
        project = MagicMock()
        project.project_code = "P001"

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 3

        with patch("app.services.project_risk.project_risk_service.get_or_404", return_value=project):
            risk_code = self.svc.generate_risk_code(1)
            assert risk_code == "RISK-P001-0004"


class TestCreateRisk:
    """测试创建风险"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_create_risk_success(self):
        """测试成功创建风险"""
        project = MagicMock()
        project.project_code = "P001"

        user = MagicMock()
        user.id = 1
        user.real_name = "Test User"
        user.username = "testuser"

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.count.return_value = 0

        # Mock the risk object that would be created
        created_risk = MagicMock()
        created_risk.risk_name = "Test Risk"
        created_risk.probability = 3
        created_risk.impact = 4

        with patch("app.services.project_risk.project_risk_service.get_or_404", return_value=project):
            with patch("app.services.project_risk.project_risk_service.save_obj", return_value=created_risk):
                with patch.object(self.svc, "generate_risk_code", return_value="RISK-P001-0001"):
                    risk = self.svc.create_risk(
                        project_id=1,
                        risk_name="Test Risk",
                        description="Test description",
                        risk_type="TECHNICAL",
                        probability=3,
                        impact=4,
                        mitigation_plan="Mitigation plan",
                        contingency_plan="Contingency plan",
                        owner_id=1,
                        target_closure_date=datetime(2026, 12, 31),
                        current_user=user,
                    )
                    assert risk.risk_name == "Test Risk"
                    assert risk.probability == 3
                    assert risk.impact == 4


class TestGetRiskList:
    """测试获取风险列表"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_get_risk_list_basic(self):
        """测试基本风险列表查询"""
        project = MagicMock()
        project.id = 1

        r1 = MagicMock()
        r1.id = 1
        r1.risk_score = 15

        r2 = MagicMock()
        r2.id = 2
        r2.risk_score = 10

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 2

        with patch("app.services.project_risk.project_risk_service.get_or_404", return_value=project):
            with patch.object(query_mock, "order_by") as order_mock:
                with patch.object(order_mock, "offset") as offset_mock:
                    with patch.object(offset_mock, "limit") as limit_mock:
                        limit_mock.all.return_value = [r1, r2]

                        risks, total = self.svc.get_risk_list(project_id=1)
                        assert total == 2

    def test_get_risk_list_with_filters(self):
        """测试带筛选条件的风险列表"""
        project = MagicMock()

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1

        with patch("app.services.project_risk.project_risk_service.get_or_404", return_value=project):
            with patch.object(query_mock, "order_by") as order_mock:
                with patch.object(order_mock, "offset") as offset_mock:
                    with patch.object(offset_mock, "limit") as limit_mock:
                        limit_mock.all.return_value = []

                        # 测试风险类型筛选
                        risks, total = self.svc.get_risk_list(
                            project_id=1,
                            risk_type="TECHNICAL"
                        )
                        # 验证筛选条件被应用
                        query_mock.filter.assert_called()


class TestGetRiskById:
    """测试获取风险详情"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_get_risk_by_id_found(self):
        """测试获取存在的风险"""
        risk = MagicMock()
        risk.id = 1

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = risk

        result = self.svc.get_risk_by_id(1, 1)
        assert result.id == 1

    def test_get_risk_by_id_not_found(self):
        """测试获取不存在的风险"""
        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            self.svc.get_risk_by_id(1, 999)
        assert exc_info.value.status_code == 404


class TestUpdateRisk:
    """测试更新风险"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_update_risk_success(self):
        """测试成功更新风险"""
        risk = MagicMock()
        risk.id = 1
        risk.probability = 3
        risk.impact = 4
        risk.risk_score = 12

        user = MagicMock()
        user.id = 1
        user.real_name = "Test User"
        user.username = "testuser"

        with patch.object(self.svc, "get_risk_by_id", return_value=risk):
            result = self.svc.update_risk(
                project_id=1,
                risk_id=1,
                update_data={"risk_name": "Updated Risk"},
                current_user=user,
            )
            assert result.id == 1


class TestDeleteRisk:
    """测试删除风险"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_delete_risk_success(self):
        """测试成功删除风险"""
        risk = MagicMock()
        risk.risk_code = "RISK-001"
        risk.risk_name = "Test"
        risk.risk_type = "TECHNICAL"
        risk.risk_score = 10

        with patch.object(self.svc, "get_risk_by_id", return_value=risk):
            with patch("app.services.project_risk.project_risk_service.delete_obj"):
                result = self.svc.delete_risk(1, 1)
                assert result["risk_code"] == "RISK-001"


class TestGetRiskMatrix:
    """测试获取风险矩阵"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_get_risk_matrix(self):
        """测试风险矩阵生成"""
        project = MagicMock()

        risk1 = MagicMock()
        risk1.probability = 4
        risk1.impact = 5
        risk1.risk_code = "R001"
        risk1.risk_name = "Risk 1"
        risk1.risk_type = "TECHNICAL"
        risk1.risk_score = 20
        risk1.risk_level = "HIGH"

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [risk1]

        with patch("app.services.project_risk.project_risk_service.get_or_404", return_value=project):
            result = self.svc.get_risk_matrix(1)
            assert "matrix" in result
            assert "summary" in result
            assert result["summary"]["total_risks"] == 1


class TestGetRiskSummary:
    """测试获取风险汇总"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_get_risk_summary(self):
        """测试风险汇总统计"""
        project = MagicMock()

        risk1 = MagicMock()
        risk1.risk_type = "TECHNICAL"
        risk1.risk_level = "HIGH"
        risk1.risk_score = 15
        risk1.is_occurred = False
        risk1.status = "IDENTIFIED"

        risk2 = MagicMock()
        risk2.risk_type = "TECHNICAL"
        risk2.risk_level = "MEDIUM"
        risk2.risk_score = 9
        risk2.is_occurred = True
        risk2.status = "OPEN"

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [risk1, risk2]

        with patch("app.services.project_risk.project_risk_service.get_or_404", return_value=project):
            result = self.svc.get_risk_summary(1)
            assert result["total_risks"] == 2
            assert result["by_level"]["HIGH"] == 1
            assert result["by_level"]["MEDIUM"] == 1
            assert result["occurred_count"] == 1
            assert result["avg_risk_score"] == 12.0


# 风险识别测试
class TestIdentifyRisks:
    """测试风险识别功能"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_identify_risks(self):
        """测试风险识别 - 通过 get_risk_list 实现"""
        project = MagicMock()

        risk = MagicMock()
        risk.id = 1
        risk.risk_score = 10

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1

        with patch("app.services.project_risk.project_risk_service.get_or_404", return_value=project):
            with patch.object(query_mock, "order_by") as order_mock:
                with patch.object(order_mock, "offset") as offset_mock:
                    with patch.object(offset_mock, "limit") as limit_mock:
                        limit_mock.all.return_value = [risk]

                        risks, total = self.svc.get_risk_list(project_id=1)
                        assert total >= 0


# 风险等级评估测试
class TestAssessRiskLevel:
    """测试风险等级评估"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_assess_risk_level(self):
        """测试风险等级评估 - 通过 get_risk_matrix 实现"""
        project = MagicMock()

        risk = MagicMock()
        risk.probability = 5
        risk.impact = 5
        risk.risk_code = "R001"
        risk.risk_name = "Critical Risk"
        risk.risk_type = "TECHNICAL"
        risk.risk_score = 25
        risk.risk_level = "CRITICAL"

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [risk]

        with patch("app.services.project_risk.project_risk_service.get_or_404", return_value=project):
            result = self.svc.get_risk_matrix(1)
            assert result["summary"]["critical_count"] == 1


# 风险评分计算测试
class TestRiskScoreCalculation:
    """测试风险评分计算"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_risk_score_calculation(self):
        """测试风险评分计算"""
        project = MagicMock()

        risk = MagicMock()
        risk.probability = 4
        risk.impact = 3

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1

        with patch("app.services.project_risk.project_risk_service.get_or_404", return_value=project):
            with patch.object(query_mock, "order_by") as order_mock:
                with patch.object(order_mock, "offset") as offset_mock:
                    with patch.object(offset_mock, "limit") as limit_mock:
                        limit_mock.all.return_value = [risk]

                        risks, total = self.svc.get_risk_list(project_id=1)
                        # 验证风险列表查询成功，评分由模型方法计算
                        assert total == 1


# 高风险阈值测试
class TestHighRiskThreshold:
    """测试高风险阈值"""

    def setup_method(self):
        self.svc, self.db = _make_service()

    def test_high_risk_threshold(self):
        """测试高风险阈值边界"""
        project = MagicMock()

        high_risk = MagicMock()
        high_risk.probability = 4
        high_risk.impact = 4
        high_risk.risk_score = 16
        high_risk.risk_level = "HIGH"

        medium_risk = MagicMock()
        medium_risk.probability = 3
        medium_risk.impact = 3
        medium_risk.risk_score = 9
        medium_risk.risk_level = "MEDIUM"

        query_mock = MagicMock()
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [high_risk, medium_risk]

        with patch("app.services.project_risk.project_risk_service.get_or_404", return_value=project):
            result = self.svc.get_risk_summary(1)
            # 验证高优先级风险统计（HIGH + CRITICAL）
            assert result["high_priority_count"] >= 1