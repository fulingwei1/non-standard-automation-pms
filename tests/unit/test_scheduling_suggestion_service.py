# -*- coding: utf-8 -*-
"""
Tests for scheduling_suggestion_service service
Covers: app/services/scheduling_suggestion_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 164 lines
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.scheduling_suggestion_service import SchedulingSuggestionService
from app.models.project import Project, Customer
from app.models.assembly_kit import MaterialReadiness
from tests.factories import ProjectFactory, CustomerFactory


class TestSchedulingSuggestionService:
    """Test suite for SchedulingSuggestionService."""

    def test_calculate_priority_score_basic(self, db_session):
        """测试计算项目优先级评分 - 基本场景"""
        customer = CustomerFactory()
        db_session.add(customer)
        db_session.flush()

        project = Project(
        project_code="PJ-SCHEDULE",
        project_name="测试排产项目",
        customer_id=customer.id,
        stage="S4",
        status="ST01",
        health="H1",
        priority="P1",
        contract_amount=Decimal("200000.00"),
        planned_end_date=date.today() + timedelta(days=10)
        )
        db_session.add(project)
        db_session.flush()

        result = SchedulingSuggestionService.calculate_priority_score(
        db_session,
        project
        )

        assert isinstance(result, dict)
        assert "total_score" in result
        assert "factors" in result
        assert "max_score" in result
        assert result["max_score"] == 100
        assert result["total_score"] > 0

    def test_calculate_priority_score_with_readiness(self, db_session):
        """测试计算项目优先级评分 - 带齐套分析"""
        customer = CustomerFactory()
        db_session.add(customer)
        db_session.flush()

        project = Project(
        project_code="PJ-SCHEDULE2",
        project_name="测试排产项目2",
        customer_id=customer.id,
        stage="S4",
        status="ST01",
        health="H1",
        priority="P2",
        contract_amount=Decimal("150000.00"),
        planned_end_date=date.today() + timedelta(days=20)
        )
        db_session.add(project)
        db_session.flush()

        from datetime import datetime
        readiness = MaterialReadiness(
        readiness_no=f"READY-{project.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        project_id=project.id,
        blocking_kit_rate=Decimal("80.0"),
        analysis_time=datetime.now()
        )
        db_session.add(readiness)
        db_session.flush()

        result = SchedulingSuggestionService.calculate_priority_score(
        db_session,
        project,
        readiness=readiness
        )

        assert isinstance(result, dict)
        assert "factors" in result
        assert "kit_rate" in result["factors"]
        assert result["factors"]["kit_rate"]["score"] > 0

    def test_calculate_priority_score_no_deadline(self, db_session):
        """测试计算项目优先级评分 - 无交期"""
        customer = CustomerFactory()
        db_session.add(customer)
        db_session.flush()

        project = Project(
        project_code="PJ-SCHEDULE3",
        project_name="测试排产项目3",
        customer_id=customer.id,
        stage="S4",
        status="ST01",
        health="H1",
        priority="P3",
        planned_end_date=None
        )
        db_session.add(project)
        db_session.commit()

        result = SchedulingSuggestionService.calculate_priority_score(
        db_session,
        project
        )

        assert isinstance(result, dict)
        assert "deadline" in result["factors"]
        assert result["factors"]["deadline"]["score"] == 5.0  # 无交期给最低分

    def test_calculate_deadline_pressure_urgent(self, db_session):
        """测试计算交期压力 - 紧急（7天内）"""
        project = Project(
        project_code="PJ-URGENT",
        project_name="紧急项目",
        stage="S4",
        status="ST01",
        health="H1",
        planned_end_date=date.today() + timedelta(days=5)
        )

        score = SchedulingSuggestionService._calculate_deadline_pressure(project)
        assert score == 25.0  # 距交期 ≤ 7天 = 25分

    def test_calculate_deadline_pressure_normal(self, db_session):
        """测试计算交期压力 - 正常（30-60天）"""
        project = Project(
        project_code="PJ-NORMAL",
        project_name="正常项目",
        stage="S4",
        status="ST01",
        health="H1",
        planned_end_date=date.today() + timedelta(days=45)
        )

        score = SchedulingSuggestionService._calculate_deadline_pressure(project)
        assert score == 10.0  # 距交期 ≤ 60天 = 10分

    def test_calculate_deadline_pressure_far(self, db_session):
        """测试计算交期压力 - 较远（>60天）"""
        project = Project(
        project_code="PJ-FAR",
        project_name="远期项目",
        stage="S4",
        status="ST01",
        health="H1",
        planned_end_date=date.today() + timedelta(days=90)
        )

        score = SchedulingSuggestionService._calculate_deadline_pressure(project)
        assert score == 5.0  # 距交期 > 60天 = 5分

    def test_calculate_contract_amount_score_high(self, db_session):
        """测试计算合同金额分数 - 高金额"""
        project = Project(
        project_code="PJ-HIGH",
        project_name="高金额项目",
        stage="S4",
        status="ST01",
        health="H1",
        contract_amount=Decimal("600000.00")
        )

        score = SchedulingSuggestionService._calculate_contract_amount_score(project)
        assert score == 10.0  # ≥ 50万 = 10分

    def test_calculate_contract_amount_score_medium(self, db_session):
        """测试计算合同金额分数 - 中等金额"""
        project = Project(
        project_code="PJ-MEDIUM",
        project_name="中等金额项目",
        stage="S4",
        status="ST01",
        health="H1",
        contract_amount=Decimal("150000.00")
        )

        score = SchedulingSuggestionService._calculate_contract_amount_score(project)
        # 150000 >= 100000，应该返回 5 分（≥ 10万 = 5分），而不是 7 分（≥ 20万 = 7分）
        assert score == 5.0  # ≥ 10万 = 5分

    def test_calculate_contract_amount_score_low(self, db_session):
        """测试计算合同金额分数 - 低金额"""
        project = Project(
        project_code="PJ-LOW",
        project_name="低金额项目",
        stage="S4",
        status="ST01",
        health="H1",
        contract_amount=Decimal("50000.00")
        )

        score = SchedulingSuggestionService._calculate_contract_amount_score(project)
        assert score == 3.0  # < 10万 = 3分

    def test_calculate_contract_amount_score_no_amount(self, db_session):
        """测试计算合同金额分数 - 无金额"""
        project = Project(
        project_code="PJ-NO-AMOUNT",
        project_name="无金额项目",
        stage="S4",
        status="ST01",
        health="H1",
        contract_amount=None
        )

        score = SchedulingSuggestionService._calculate_contract_amount_score(project)
        assert score == 3.0  # 无金额 = 3分

    def test_priority_score_mapping(self, db_session):
        """测试优先级分数映射"""
        priorities = ['P1', 'P2', 'P3', 'P4', 'P5']
        expected_scores = [30, 24, 18, 12, 6]

        for priority, expected_score in zip(priorities, expected_scores):
            project = Project(
            project_code=f"PJ-{priority}",
            project_name=f"测试项目{priority}",
            stage="S4",
            status="ST01",
            health="H1",
            priority=priority
            )

            result = SchedulingSuggestionService.calculate_priority_score(
            db_session,
            project
            )

            assert result["factors"]["priority"]["score"] == expected_score

    def test_priority_score_non_standard_priority(self, db_session):
        """测试非标准优先级格式"""
        customer = CustomerFactory()
        db_session.add(customer)
        db_session.flush()

        # 测试 HIGH/MEDIUM/LOW 格式
        for priority, expected in [('HIGH', 30), ('MEDIUM', 18), ('LOW', 6)]:
            project = Project(
            project_code=f"PJ-{priority}",
            project_name=f"测试项目{priority}",
            customer_id=customer.id,
            stage="S4",
            status="ST01",
            health="H1",
            priority=priority
            )
            db_session.add(project)
            db_session.flush()

            result = SchedulingSuggestionService.calculate_priority_score(
            db_session,
            project
            )

            assert result["factors"]["priority"]["score"] == expected
