# -*- coding: utf-8 -*-
"""
生产计划服务测试
目标覆盖率: 60%+
测试用例数: 10个
"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.production.plan_service import ProductionPlanService
from app.models.production import ProductionPlan, Workshop
from app.models.project import Project


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock(spec=Session)
    db.query = Mock(return_value=Mock())
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return ProductionPlanService(db=mock_db)


@pytest.fixture
def sample_plan():
    """创建示例生产计划"""
    plan = Mock(spec=ProductionPlan)
    plan.id = 1
    plan.plan_no = "PLAN-2024-001"
    plan.payment_name = "测试计划"
    plan.plan_type = "PRODUCTION"
    plan.project_id = 1
    plan.workshop_id = 1
    plan.plan_start_date = date(2024, 1, 1)
    plan.plan_end_date = date(2024, 1, 31)
    plan.status = "DRAFT"
    plan.progress = 0
    plan.description = "测试计划描述"
    plan.created_by = 1
    plan.approved_by = None
    plan.approved_at = None
    plan.remark = None
    plan.created_at = datetime(2024, 1, 1)
    plan.updated_at = datetime(2024, 1, 1)
    return plan


@pytest.fixture
def sample_project():
    """创建示例项目"""
    project = Mock(spec=Project)
    project.id = 1
    project.project_name = "测试项目"
    return project


@pytest.fixture
def sample_workshop():
    """创建示例车间"""
    workshop = Mock(spec=Workshop)
    workshop.id = 1
    workshop.workshop_name = "车间A"
    return workshop


class TestProductionPlanService:
    """生产计划服务测试类"""
    
    def test_build_plan_response(self, service, sample_plan, sample_project, sample_workshop, mock_db):
        """测试构建计划响应"""
        # 设置mock查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        
        # 模拟查询项目
        project_query = Mock()
        project_query.filter.return_value = project_query
        project_query.first.return_value = sample_project
        
        # 模拟查询车间
        workshop_query = Mock()
        workshop_query.filter.return_value = workshop_query
        workshop_query.first.return_value = sample_workshop
        
        # 根据查询的模型返回不同的mock
        def query_side_effect(model):
            if model == Project:
                return project_query
            elif model == Workshop:
                return workshop_query
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # 调用方法
        response = service._build_plan_response(sample_plan)
        
        # 验证响应
        assert response.id == 1
        assert response.plan_no == "PLAN-2024-001"
        assert response.project_name == "测试项目"
        assert response.workshop_name == "车间A"
        
    @patch('app.services.production.plan_service.get_or_404')
    @patch('app.services.production.plan_service.apply_pagination')
    def test_list_plans(self, mock_pagination, mock_get_or_404, service, sample_plan, mock_db):
        """测试查询生产计划列表"""
        # 设置mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_db.query.return_value = mock_query
        
        mock_pagination.return_value.all.return_value = [sample_plan]
        
        # 创建pagination对象
        pagination = Mock()
        pagination.offset = 0
        pagination.limit = 10
        pagination.to_response = Mock(return_value={"items": [], "total": 1})
        
        # 调用方法
        result = service.list_plans(
            pagination=pagination,
            status="DRAFT"
        )
        
        # 验证结果
        assert "items" in result or "total" in result
        
    @patch('app.services.production.plan_service.generate_plan_no')
    @patch('app.services.production.plan_service.get_or_404')
    @patch('app.services.production.plan_service.save_obj')
    def test_create_plan(self, mock_save, mock_get_or_404, mock_gen_no, service, sample_project, sample_workshop, mock_db):
        """测试创建生产计划"""
        # 设置mock
        mock_gen_no.return_value = "PLAN-2024-001"
        mock_get_or_404.side_effect = [sample_project, sample_workshop]
        
        # 创建计划输入
        plan_in = Mock()
        plan_in.project_id = 1
        plan_in.workshop_id = 1
        plan_in.model_dump.return_value = {
            "payment_name": "新计划",
            "plan_type": "PRODUCTION",
            "plan_start_date": date(2024, 1, 1),
            "plan_end_date": date(2024, 1, 31),
        }
        
        # 模拟返回的计划
        created_plan = Mock(spec=ProductionPlan)
        created_plan.id = 1
        created_plan.plan_no = "PLAN-2024-001"
        created_plan.payment_name = "新计划"
        created_plan.plan_type = "PRODUCTION"
        created_plan.project_id = 1
        created_plan.workshop_id = 1
        created_plan.plan_start_date = date(2024, 1, 1)
        created_plan.plan_end_date = date(2024, 1, 31)
        created_plan.status = "DRAFT"
        created_plan.progress = 0
        created_plan.created_by = 1
        created_plan.approved_by = None
        created_plan.approved_at = None
        created_plan.remark = None
        created_plan.description = None
        created_plan.created_at = datetime.now()
        created_plan.updated_at = datetime.now()
        
        # 设置查询mock
        mock_project_query = Mock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = sample_project
        
        mock_workshop_query = Mock()
        mock_workshop_query.filter.return_value = mock_workshop_query
        mock_workshop_query.first.return_value = sample_workshop
        
        def query_side_effect(model):
            if model == Project:
                return mock_project_query
            elif model == Workshop:
                return mock_workshop_query
            return Mock()
        
        mock_db.query.side_effect = query_side_effect
        
        # Mock save_obj to capture the plan
        def save_side_effect(db, obj):
            # 将创建的plan的属性复制到obj
            for key, value in vars(created_plan).items():
                setattr(obj, key, value)
        
        mock_save.side_effect = save_side_effect
        
        # 调用方法
        result = service.create_plan(plan_in, current_user_id=1)
        
        # 验证结果
        assert result.plan_no == "PLAN-2024-001"
        assert result.status == "DRAFT"
        
    @patch('app.services.production.plan_service.get_or_404')
    def test_get_plan(self, mock_get_or_404, service, sample_plan, sample_project, sample_workshop, mock_db):
        """测试获取生产计划详情"""
        # 设置mock
        mock_get_or_404.return_value = sample_plan
        
        # 设置查询mock
        mock_project_query = Mock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = sample_project
        
        mock_workshop_query = Mock()
        mock_workshop_query.filter.return_value = mock_workshop_query
        mock_workshop_query.first.return_value = sample_workshop
        
        def query_side_effect(model):
            if model == Project:
                return mock_project_query
            elif model == Workshop:
                return mock_workshop_query
            return Mock()
        
        mock_db.query.side_effect = query_side_effect
        
        # 调用方法
        result = service.get_plan(plan_id=1)
        
        # 验证结果
        assert result.id == 1
        assert result.plan_no == "PLAN-2024-001"
        
    @patch('app.services.production.plan_service.get_or_404')
    @patch('app.services.production.plan_service.save_obj')
    def test_update_plan(self, mock_save, mock_get_or_404, service, sample_plan, sample_project, sample_workshop, mock_db):
        """测试更新生产计划"""
        # 设置mock
        sample_plan.status = "DRAFT"
        mock_get_or_404.return_value = sample_plan
        
        # 创建更新输入
        plan_in = Mock()
        plan_in.model_dump.return_value = {
            "payment_name": "更新后的计划"
        }
        
        # 设置查询mock
        mock_project_query = Mock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = sample_project
        
        mock_workshop_query = Mock()
        mock_workshop_query.filter.return_value = mock_workshop_query
        mock_workshop_query.first.return_value = sample_workshop
        
        def query_side_effect(model):
            if model == Project:
                return mock_project_query
            elif model == Workshop:
                return mock_workshop_query
            return Mock()
        
        mock_db.query.side_effect = query_side_effect
        
        # 调用方法
        service.update_plan(plan_id=1, plan_in=plan_in)
        
        # 验证更新
        assert sample_plan.payment_name == "更新后的计划"
        
    @patch('app.services.production.plan_service.get_or_404')
    def test_update_plan_not_draft(self, mock_get_or_404, service, sample_plan):
        """测试更新非草稿状态的计划（应该失败）"""
        # 设置mock
        sample_plan.status = "APPROVED"
        mock_get_or_404.return_value = sample_plan
        
        plan_in = Mock()
        plan_in.model_dump.return_value = {}
        
        # 验证抛出异常
        with pytest.raises(HTTPException) as exc:
            service.update_plan(plan_id=1, plan_in=plan_in)
        assert exc.value.status_code == 400
        
    @patch('app.services.production.plan_service.get_or_404')
    def test_submit_plan(self, mock_get_or_404, service, sample_plan, mock_db):
        """测试提交计划审批"""
        # 设置mock
        sample_plan.status = "DRAFT"
        mock_get_or_404.return_value = sample_plan
        
        # 调用方法
        result = service.submit_plan(plan_id=1)
        
        # 验证状态变更
        assert sample_plan.status == "SUBMITTED"
        assert result["message"] == "计划已提交审批"
        
    @patch('app.services.production.plan_service.get_or_404')
    def test_submit_plan_not_draft(self, mock_get_or_404, service, sample_plan):
        """测试提交非草稿状态的计划（应该失败）"""
        # 设置mock
        sample_plan.status = "APPROVED"
        mock_get_or_404.return_value = sample_plan
        
        # 验证抛出异常
        with pytest.raises(HTTPException) as exc:
            service.submit_plan(plan_id=1)
        assert exc.value.status_code == 400
        
    @patch('app.services.production.plan_service.get_or_404')
    def test_approve_plan(self, mock_get_or_404, service, sample_plan, mock_db):
        """测试审批生产计划"""
        # 设置mock
        sample_plan.status = "SUBMITTED"
        mock_get_or_404.return_value = sample_plan
        
        # 调用方法
        result = service.approve_plan(
            plan_id=1,
            approved=True,
            approval_note="审批通过",
            current_user_id=2
        )
        
        # 验证状态和审批信息
        assert sample_plan.status == "APPROVED"
        assert sample_plan.approved_by == 2
        assert sample_plan.approved_at is not None
        assert result["message"] == "审批成功"
        
    @patch('app.services.production.plan_service.get_or_404')
    def test_publish_plan(self, mock_get_or_404, service, sample_plan, mock_db):
        """测试发布生产计划"""
        # 设置mock
        sample_plan.status = "APPROVED"
        mock_get_or_404.return_value = sample_plan
        
        # 调用方法
        result = service.publish_plan(plan_id=1)
        
        # 验证状态变更
        assert sample_plan.status == "PUBLISHED"
        assert result["message"] == "计划已发布"
