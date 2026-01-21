# -*- coding: utf-8 -*-
"""
Tests for scheduling_suggestion_service service
Covers: app/services/scheduling_suggestion_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 164 lines
Batch: 1
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.scheduling_suggestion_service import SchedulingSuggestionService
from app.models.project import Project
from app.models.material import MaterialReadiness
from app.models.organization import Customer


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        priority="P1",
        planned_end_date=date.today() + timedelta(days=10),
        contract_amount=Decimal("200000.00")
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_customer(db_session: Session):
    """创建测试客户"""
    customer = Customer(
        customer_name="测试客户",
        customer_code="C001",
        customer_level="A"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def test_material_readiness(db_session: Session, test_project):
    """创建测试物料齐套度"""
    readiness = MaterialReadiness(
        project_id=test_project.id,
        readiness_rate=0.8
    )
    db_session.add(readiness)
    db_session.commit()
    db_session.refresh(readiness)
    return readiness


class TestSchedulingSuggestionService:
    """Test suite for SchedulingSuggestionService."""

    def test_calculate_priority_score_basic(self, db_session, test_project):
        """测试计算优先级评分 - 基础场景"""
        result = SchedulingSuggestionService.calculate_priority_score(
            db_session,
            test_project
        )
        
        assert result is not None
        assert 'total_score' in result
        assert 'factors' in result
        assert result['total_score'] > 0
        assert 'priority' in result['factors']

    def test_calculate_priority_score_with_readiness(self, db_session, test_project, test_material_readiness):
        """测试计算优先级评分 - 带齐套度"""
        result = SchedulingSuggestionService.calculate_priority_score(
            db_session,
            test_project,
            test_material_readiness
        )
        
        assert result is not None
        assert 'total_score' in result
        assert 'readiness' in result['factors']
        assert result['factors']['readiness']['score'] > 0

    def test_calculate_priority_score_different_priorities(self, db_session):
        """测试不同优先级评分"""
        priorities = ['P1', 'P2', 'P3', 'P4', 'P5']
        scores = []
        
        for priority in priorities:
            project = Project(
                project_code=f"PJ_{priority}",
                project_name=f"测试项目{priority}",
                priority=priority,
                planned_end_date=date.today() + timedelta(days=30),
                contract_amount=Decimal("100000.00")
            )
            db_session.add(project)
            db_session.commit()
            
            result = SchedulingSuggestionService.calculate_priority_score(
                db_session,
                project
            )
            scores.append(result['total_score'])
            db_session.delete(project)
            db_session.commit()
        
        # P1应该得分最高
        assert scores[0] > scores[-1]

    def test_calculate_priority_score_priority_mapping(self, db_session):
        """测试优先级映射（HIGH/MEDIUM/LOW）"""
        project = Project(
            project_code="PJ_HIGH",
            project_name="高优先级项目",
            priority="HIGH",
            planned_end_date=date.today() + timedelta(days=30),
            contract_amount=Decimal("100000.00")
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        result = SchedulingSuggestionService.calculate_priority_score(
            db_session,
            project
        )
        
        assert result is not None
        assert result['factors']['priority']['score'] == 30  # HIGH映射到P1

    def test_calculate_priority_score_deadline_pressure(self, db_session):
        """测试交期压力评分"""
        # 紧急项目（7天内）
        urgent_project = Project(
            project_code="PJ_URGENT",
            project_name="紧急项目",
            priority="P1",
            planned_end_date=date.today() + timedelta(days=5),
            contract_amount=Decimal("100000.00")
        )
        db_session.add(urgent_project)
        db_session.commit()
        
        result_urgent = SchedulingSuggestionService.calculate_priority_score(
            db_session,
            urgent_project
        )
        
        # 不紧急项目（60天以上）
        normal_project = Project(
            project_code="PJ_NORMAL",
            project_name="普通项目",
            priority="P1",
            planned_end_date=date.today() + timedelta(days=90),
            contract_amount=Decimal("100000.00")
        )
        db_session.add(normal_project)
        db_session.commit()
        
        result_normal = SchedulingSuggestionService.calculate_priority_score(
            db_session,
            normal_project
        )
        
        # 紧急项目应该得分更高
        assert result_urgent['total_score'] > result_normal['total_score']
        assert result_urgent['factors']['deadline_pressure']['score'] > result_normal['factors']['deadline_pressure']['score']

    def test_calculate_priority_score_customer_importance(self, db_session, test_customer):
        """测试客户重要度评分"""
        project = Project(
            project_code="PJ_CUSTOMER",
            project_name="客户项目",
            priority="P3",
            planned_end_date=date.today() + timedelta(days=30),
            contract_amount=Decimal("100000.00"),
            customer_id=test_customer.id
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        result = SchedulingSuggestionService.calculate_priority_score(
            db_session,
            project
        )
        
        assert result is not None
        assert 'customer_importance' in result['factors']
        assert result['factors']['customer_importance']['score'] == 15  # A级客户

    def test_calculate_priority_score_contract_amount(self, db_session):
        """测试合同金额评分"""
        # 大金额项目
        large_project = Project(
            project_code="PJ_LARGE",
            project_name="大金额项目",
            priority="P3",
            planned_end_date=date.today() + timedelta(days=30),
            contract_amount=Decimal("600000.00")
        )
        db_session.add(large_project)
        db_session.commit()
        
        result_large = SchedulingSuggestionService.calculate_priority_score(
            db_session,
            large_project
        )
        
        # 小金额项目
        small_project = Project(
            project_code="PJ_SMALL",
            project_name="小金额项目",
            priority="P3",
            planned_end_date=date.today() + timedelta(days=30),
            contract_amount=Decimal("50000.00")
        )
        db_session.add(small_project)
        db_session.commit()
        
        result_small = SchedulingSuggestionService.calculate_priority_score(
            db_session,
            small_project
        )
        
        # 大金额项目应该得分更高
        assert result_large['factors']['contract_amount']['score'] > result_small['factors']['contract_amount']['score']

    def test_generate_scheduling_suggestions(self, db_session):
        """测试生成排产建议"""
        # 创建多个项目
        projects = []
        for i in range(3):
            project = Project(
                project_code=f"PJ{i:03d}",
                project_name=f"测试项目{i}",
                priority="P1",
                planned_end_date=date.today() + timedelta(days=10 + i * 5),
                contract_amount=Decimal("100000.00")
            )
            db_session.add(project)
            projects.append(project)
        db_session.commit()
        
        result = SchedulingSuggestionService.generate_scheduling_suggestions(
            db_session,
            limit=10
        )
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) <= 10

    def test_generate_scheduling_suggestions_with_filters(self, db_session):
        """测试带筛选条件的排产建议"""
        result = SchedulingSuggestionService.generate_scheduling_suggestions(
            db_session,
            stage="S4",  # 加工制造阶段
            limit=5
        )
        
        assert result is not None
        assert isinstance(result, list)
