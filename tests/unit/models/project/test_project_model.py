# -*- coding: utf-8 -*-
"""
Project Model 测试
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models.project.core import Project
from app.models.project.customer import Customer
from app.models.user import User


class TestProjectModel:
    """Project 模型测试"""

    def test_create_project_basic(self, db_session, sample_customer, sample_user):
        """测试基本项目创建"""
        project = Project(
            project_code="PRJ001",
            project_name="测试项目",
            customer_id=sample_customer.id,
            pm_id=sample_user.id,
            contract_amount=Decimal("100000.00")
        )
        db_session.add(project)
        db_session.commit()
        
        assert project.id is not None
        assert project.project_code == "PRJ001"
        assert project.project_name == "测试项目"
        assert project.contract_amount == Decimal("100000.00")

    def test_project_code_unique_constraint(self, db_session, sample_customer, sample_user):
        """测试项目编码唯一性约束"""
        project1 = Project(
            project_code="PRJ001",
            project_name="项目1",
            customer_id=sample_customer.id,
            pm_id=sample_user.id
        )
        db_session.add(project1)
        db_session.commit()
        
        project2 = Project(
            project_code="PRJ001",  # 相同的项目编码
            project_name="项目2",
            customer_id=sample_customer.id,
            pm_id=sample_user.id
        )
        db_session.add(project2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_project_customer_relationship(self, db_session, sample_project):
        """测试项目-客户关系"""
        db_session.refresh(sample_project)
        assert sample_project.customer is not None
        assert sample_project.customer.customer_name == "测试客户"
        assert sample_project.customer_id == sample_project.customer.id

    def test_project_manager_relationship(self, db_session, sample_project):
        """测试项目-项目经理关系"""
        db_session.refresh(sample_project)
        assert sample_project.pm is not None
        assert sample_project.pm.username == "testuser"
        assert sample_project.pm_id == sample_project.pm.id

    def test_project_default_values(self, db_session, sample_customer, sample_user):
        """测试项目默认值"""
        project = Project(
            project_code="PRJ002",
            project_name="默认值测试",
            customer_id=sample_customer.id,
            pm_id=sample_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        assert project.stage == "S1"
        assert project.status == "ST01"
        assert project.health == "H1"
        assert project.approval_status == "NONE"
        assert project.progress_pct == 0
        assert project.contract_amount == 0
        assert project.budget_amount == 0
        assert project.actual_cost == 0
        assert project.priority == "NORMAL"

    def test_project_date_fields(self, db_session, sample_customer, sample_user):
        """测试项目日期字段"""
        start_date = date.today()
        end_date = start_date + timedelta(days=90)
        
        project = Project(
            project_code="PRJ003",
            project_name="日期测试",
            customer_id=sample_customer.id,
            pm_id=sample_user.id,
            contract_date=start_date,
            planned_start_date=start_date,
            planned_end_date=end_date,
            actual_start_date=start_date
        )
        db_session.add(project)
        db_session.commit()
        
        assert project.contract_date == start_date
        assert project.planned_start_date == start_date
        assert project.planned_end_date == end_date
        assert project.actual_start_date == start_date
        assert project.actual_end_date is None

    def test_project_financial_fields(self, db_session, sample_customer, sample_user):
        """测试项目财务字段"""
        project = Project(
            project_code="PRJ004",
            project_name="财务测试",
            customer_id=sample_customer.id,
            pm_id=sample_user.id,
            contract_amount=Decimal("500000.00"),
            budget_amount=Decimal("450000.00"),
            actual_cost=Decimal("350000.00")
        )
        db_session.add(project)
        db_session.commit()
        
        assert project.contract_amount == Decimal("500000.00")
        assert project.budget_amount == Decimal("450000.00")
        assert project.actual_cost == Decimal("350000.00")
        
        # 测试成本差异计算
        cost_variance = project.budget_amount - project.actual_cost
        assert cost_variance == Decimal("100000.00")

    def test_project_status_transitions(self, db_session, sample_project):
        """测试项目状态转换"""
        assert sample_project.status == "ST01"
        
        sample_project.status = "ST02"
        db_session.commit()
        
        db_session.refresh(sample_project)
        assert sample_project.status == "ST02"

    def test_project_approval_status(self, db_session, sample_project):
        """测试项目审批状态"""
        assert sample_project.approval_status == "NONE"
        
        sample_project.approval_status = "PENDING"
        db_session.commit()
        
        db_session.refresh(sample_project)
        assert sample_project.approval_status == "PENDING"
        
        sample_project.approval_status = "APPROVED"
        db_session.commit()
        
        db_session.refresh(sample_project)
        assert sample_project.approval_status == "APPROVED"

    def test_project_progress_tracking(self, db_session, sample_project):
        """测试项目进度跟踪"""
        assert sample_project.progress_pct == 0
        
        sample_project.progress_pct = Decimal("35.50")
        db_session.commit()
        
        db_session.refresh(sample_project)
        assert sample_project.progress_pct == Decimal("35.50")
        
        sample_project.progress_pct = Decimal("100.00")
        db_session.commit()
        
        db_session.refresh(sample_project)
        assert sample_project.progress_pct == Decimal("100.00")

    def test_project_update(self, db_session, sample_project):
        """测试项目更新"""
        original_name = sample_project.project_name
        new_name = "更新后的项目名称"
        
        sample_project.project_name = new_name
        sample_project.description = "项目描述更新"
        db_session.commit()
        
        db_session.refresh(sample_project)
        assert sample_project.project_name == new_name
        assert sample_project.project_name != original_name
        assert sample_project.description == "项目描述更新"

    def test_project_delete(self, db_session, sample_customer, sample_user):
        """测试项目删除"""
        project = Project(
            project_code="PRJ_DELETE",
            project_name="待删除项目",
            customer_id=sample_customer.id,
            pm_id=sample_user.id
        )
        db_session.add(project)
        db_session.commit()
        project_id = project.id
        
        db_session.delete(project)
        db_session.commit()
        
        deleted_project = db_session.query(Project).filter_by(id=project_id).first()
        assert deleted_project is None
