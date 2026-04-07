# -*- coding: utf-8 -*-
"""
项目财务服务分支测试

覆盖服务：
- ProjectFinanceService - 项目成本/预算统计
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from app.models.project import Project, ProjectCost
from app.models.user import User
from app.services.project.finance_service import ProjectFinanceService


class TestProjectFinanceService:
    """项目财务服务测试"""

    @pytest.fixture
    def finance_service(self, db_session):
        """创建财务服务实例"""
        return ProjectFinanceService(db_session)

    @pytest.fixture
    def mock_user(self, db_session):
        """创建模拟用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            real_name="测试用户",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_get_cost_summary_no_projects(self, finance_service, mock_user):
        """分支：无权限项目"""
        with patch.object(
            finance_service, "_get_accessible_project_ids", return_value=[]
        ):
            result = finance_service.get_cost_summary(mock_user)

            assert result["projects"] == 0
            assert result["total_cost"] == 0.0
            assert result["breakdown"] == {}
            assert result["top_projects"] == []

    def test_get_cost_summary_with_costs(
        self, db_session, finance_service, mock_user, test_project
    ):
        """分支：有成本数据"""
        # 创建成本记录
        cost1 = ProjectCost(
            project_id=test_project.id,
            cost_type="MATERIAL",
            amount=Decimal("10000.00"),
            cost_date=date.today() - timedelta(days=5),
        )
        cost2 = ProjectCost(
            project_id=test_project.id,
            cost_type="LABOR",
            amount=Decimal("5000.00"),
            cost_date=date.today() - timedelta(days=3),
        )
        cost3 = ProjectCost(
            project_id=test_project.id,
            cost_type="MATERIAL",
            amount=Decimal("3000.00"),
            cost_date=date.today() - timedelta(days=1),
        )
        db_session.add_all([cost1, cost2, cost3])
        db_session.commit()

        with patch.object(
            finance_service,
            "_get_accessible_project_ids",
            return_value=[test_project.id],
        ):
            result = finance_service.get_cost_summary(mock_user)

            assert result["projects"] == 1
            assert result["total_cost"] == 18000.00
            assert "MATERIAL" in result["breakdown"]
            assert result["breakdown"]["MATERIAL"] == 13000.00
            assert result["breakdown"]["LABOR"] == 5000.00

    def test_get_cost_summary_with_date_filter(
        self, db_session, finance_service, mock_user, test_project
    ):
        """分支：日期过滤"""
        # 创建不同日期的成本
        old_cost = ProjectCost(
            project_id=test_project.id,
            cost_type="MATERIAL",
            amount=Decimal("1000.00"),
            cost_date=date.today() - timedelta(days=100),
        )
        recent_cost = ProjectCost(
            project_id=test_project.id,
            cost_type="MATERIAL",
            amount=Decimal("2000.00"),
            cost_date=date.today() - timedelta(days=5),
        )
        db_session.add_all([old_cost, recent_cost])
        db_session.commit()

        with patch.object(
            finance_service,
            "_get_accessible_project_ids",
            return_value=[test_project.id],
        ):
            # 只查询近30天
            result = finance_service.get_cost_summary(
                mock_user, start_date=date.today() - timedelta(days=30)
            )

            assert result["total_cost"] == 2000.00

    def test_get_cost_summary_group_by_cost_type(
        self, db_session, finance_service, mock_user, test_project
    ):
        """分支：按成本类型分组"""
        costs = [
            ProjectCost(
                project_id=test_project.id,
                cost_type="MATERIAL",
                amount=Decimal("1000.00"),
                cost_date=date.today(),
            ),
            ProjectCost(
                project_id=test_project.id,
                cost_type="EQUIPMENT",
                amount=Decimal("2000.00"),
                cost_date=date.today(),
            ),
            ProjectCost(
                project_id=test_project.id,
                cost_type="MATERIAL",
                amount=Decimal("500.00"),
                cost_date=date.today(),
            ),
        ]
        db_session.add_all(costs)
        db_session.commit()

        with patch.object(
            finance_service,
            "_get_accessible_project_ids",
            return_value=[test_project.id],
        ):
            result = finance_service.get_cost_summary(
                mock_user, group_by="cost_type"
            )

            assert result["breakdown"]["MATERIAL"] == 1500.00
            assert result["breakdown"]["EQUIPMENT"] == 2000.00

    def test_get_cost_summary_top_projects(
        self, db_session, finance_service, mock_user, test_customer, test_project
    ):
        """分支：返回成本最高的项目"""
        # 创建另一个项目
        project2 = Project(
            project_code="PJ260307002",
            project_name="测试项目2",
            stage="S3",
            status="ST05",
            health="H1",
            budget_amount=Decimal("100000.00"),
            is_active=True,
            is_archived=False,
        )
        db_session.add(project2)
        db_session.commit()

        # 为两个项目添加不同金额的成本
        cost1 = ProjectCost(
            project_id=test_project.id,
            cost_type="MATERIAL",
            amount=Decimal("50000.00"),
            cost_date=date.today(),
        )
        cost2 = ProjectCost(
            project_id=project2.id,
            cost_type="MATERIAL",
            amount=Decimal("100000.00"),
            cost_date=date.today(),
        )
        db_session.add_all([cost1, cost2])
        db_session.commit()

        with patch.object(
            finance_service,
            "_get_accessible_project_ids",
            return_value=[test_project.id, project2.id],
        ):
            result = finance_service.get_cost_summary(mock_user)

            assert len(result["top_projects"]) <= 5
            # 验证排序（按金额降序）
            if len(result["top_projects"]) >= 2:
                assert result["top_projects"][0]["amount"] >= result["top_projects"][1]["amount"]

    def test_get_cost_summary_with_budget(
        self, db_session, finance_service, mock_user, test_project
    ):
        """分支：包含预算信息"""
        # 设置项目预算
        test_project.budget_amount = Decimal("100000.00")
        db_session.commit()

        # 添加成本
        cost = ProjectCost(
            project_id=test_project.id,
            cost_type="MATERIAL",
            amount=Decimal("30000.00"),
            cost_date=date.today(),
        )
        db_session.add(cost)
        db_session.commit()

        with patch.object(
            finance_service,
            "_get_accessible_project_ids",
            return_value=[test_project.id],
        ):
            result = finance_service.get_cost_summary(mock_user)

            assert result["budget"]["total_budget"] == 100000.00
            assert result["budget"]["variance"] == 70000.00  # 100000 - 30000

    def test_get_cost_summary_budget_exceeded(
        self, db_session, finance_service, mock_user, test_project
    ):
        """分支：预算超支"""
        # 设置较低预算
        test_project.budget_amount = Decimal("10000.00")
        db_session.commit()

        # 添加较高成本
        cost = ProjectCost(
            project_id=test_project.id,
            cost_type="MATERIAL",
            amount=Decimal("30000.00"),
            cost_date=date.today(),
        )
        db_session.add(cost)
        db_session.commit()

        with patch.object(
            finance_service,
            "_get_accessible_project_ids",
            return_value=[test_project.id],
        ):
            result = finance_service.get_cost_summary(mock_user)

            assert result["budget"]["variance"] == -20000.00  # 10000 - 30000

    def test_get_cost_summary_invalid_group_by(
        self, db_session, finance_service, mock_user, test_project
    ):
        """分支：无效的分组字段 - 回退到cost_type"""
        cost = ProjectCost(
            project_id=test_project.id,
            cost_type="MATERIAL",
            amount=Decimal("1000.00"),
            cost_date=date.today(),
        )
        db_session.add(cost)
        db_session.commit()

        with patch.object(
            finance_service,
            "_get_accessible_project_ids",
            return_value=[test_project.id],
        ):
            # 使用不存在的字段，应该回退到cost_type
            result = finance_service.get_cost_summary(
                mock_user, group_by="invalid_field"
            )

            assert "MATERIAL" in result["breakdown"]

    def test_get_cost_summary_null_cost_type(
        self, db_session, finance_service, mock_user, test_project
    ):
        """分支：空成本类型"""
        cost = ProjectCost(
            project_id=test_project.id,
            cost_type=None,
            amount=Decimal("1000.00"),
            cost_date=date.today(),
        )
        db_session.add(cost)
        db_session.commit()

        with patch.object(
            finance_service,
            "_get_accessible_project_ids",
            return_value=[test_project.id],
        ):
            result = finance_service.get_cost_summary(mock_user)

            assert "未分类" in result["breakdown"]
            assert result["breakdown"]["未分类"] == 1000.00