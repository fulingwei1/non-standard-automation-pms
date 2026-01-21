# -*- coding: utf-8 -*-
"""
成本分析单元测试

覆盖 app/api/v1/endpoints/costs/analysis.py 的关键端点
"""

import pytest
# from sqlalchemy.orm import Session

from tests.factories import (
    ProjectFactory,
    ProjectCostFactory,
    MachineFactory,
)


class TestGetProjectCostSummary:
    """项目成本汇总测试"""

    def test_cost_summary_success(self, db_session: Session, test_project):
        """成功获取项目成本汇总"""
        ProjectCostFactory.create(
            project=test_project,
            cost_type="MATERIAL",
            amount=10000,
        )
        ProjectCostFactory.create(project=test_project, cost_type="LABOR", amount=5000)
        db_session.commit()

        from app.api.v1.endpoints.costs import analysis

        response = analysis.get_project_cost_summary(
            project_id=test_project.id, db_session=db_session
        )
        assert response.total_cost == 15000

    def test_cost_summary_empty_project(self, db_session: Session, test_project):
        """空项目的成本汇总应该为 0"""
        from app.api.v1.endpoints.costs import analysis

        response = analysis.get_project_cost_summary(
            project_id=test_project.id, db_session=db_session
        )
        assert response.total_cost == 0


class TestGetProjectCostAnalysis:
    """项目成本分析测试"""

    def test_cost_analysis_by_category(self, db_session: Session, test_project):
        """按成本类别分析"""
        ProjectCostFactory.create(
            project=test_project,
            cost_type="MATERIAL",
            amount=10000,
        )
        ProjectCostFactory.create(
            project=test_project,
            cost_type="LABOR",
            amount=5000,
        )
        db_session.commit()

        from app.api.v1.endpoints.costs import analysis

        response = analysis.get_project_cost_analysis(
            project_id=test_project.id, db_session=db_session
        )
        assert len(response.by_category) == 2

    def test_cost_analysis_by_machine(
        self, db_session: Session, test_project, test_machine
    ):
        """按设备分析成本"""
        ProjectCostFactory.create(
            project=test_project,
            machine=test_machine,
            cost_type="MATERIAL",
            amount=10000,
        )
        db_session.commit()

        from app.api.v1.endpoints.costs import analysis

        response = analysis.get_project_cost_analysis(
            project_id=test_project.id, db_session=db_session
        )
        assert len(response.by_machine) >= 1


class TestGetProjectProfitAnalysis:
    """项目利润分析测试"""

    def test_profit_analysis_success(self, db_session: Session, test_project):
        """成功获取项目利润分析"""
        # 设置项目预算
        test_project.budget_amount = 200000
        test_project.contract_amount = 150000
        db_session.commit()

        # 添加成本
        ProjectCostFactory.create(
            project=test_project, cost_type="MATERIAL", amount=80000
        )
        ProjectCostFactory.create(project=test_project, cost_type="LABOR", amount=30000)
        db_session.commit()

        from app.api.v1.endpoints.costs import analysis

        response = analysis.get_project_profit_analysis(
            project_id=test_project.id, db_session=db_session
        )
        assert response.total_cost == 110000
        assert response.budget_amount == 200000
        assert response.contract_amount == 150000


class TestGetCostTrends:
    """成本趋势测试"""

    def test_cost_trends_by_month(self, db_session: Session, test_project):
        """按月获取成本趋势"""
        from datetime import datetime, timedelta

        # 创建不同月份的成本记录
        for i in range(3):
            ProjectCostFactory.create(
                project=test_project,
                cost_type="MATERIAL",
                amount=10000 + i * 1000,
                created_at=datetime.now() - timedelta(days=90 - i * 30),
            )
        db_session.commit()

        from app.api.v1.endpoints.costs import analysis

        response = analysis.get_cost_trends(
            project_id=test_project.id,
            group_by="month",
            db_session=db_session,
        )
        assert len(response.data) >= 1


# Fixtures
@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = ProjectFactory.create(
        project_code="P2025001",
        stage="S5",
        budget_amount=200000,
        contract_amount=150000,
    )
    db_session.commit()
    return project


@pytest.fixture
def test_machine(db_session: Session, test_project):
    """创建测试设备"""
    machine = MachineFactory.create(
        project=test_project, machine_code="PN001", machine_name="测试机台"
    )
    db_session.commit()
    return machine
