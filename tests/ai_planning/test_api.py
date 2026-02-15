# -*- coding: utf-8 -*-
"""
AI项目规划助手 API测试
"""

import pytest
import json
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Project, User
from app.models.ai_planning import AIProjectPlanTemplate, AIWbsSuggestion


client = TestClient(app)


@pytest.fixture
def auth_headers(db: Session):
    """获取认证头"""
    # TODO: 实现真实的认证逻辑
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def sample_project(db: Session):
    """创建测试项目"""
    project = Project(
        project_code="API_TEST_001",
        project_name="API测试项目",
        project_type="WEB_DEV",
        status="ST01"
    )
    db.add(project)
    db.commit()
    return project


class TestAIPlanningAPI:
    """AI项目规划API测试"""
    
    def test_generate_plan_api(self, auth_headers):
        """测试：生成项目计划API"""
        response = client.post(
            "/api/v1/ai-planning/generate-plan",
            headers=auth_headers,
            json={
                "project_name": "测试项目",
                "project_type": "WEB_DEV",
                "requirements": "开发一个电商网站",
                "industry": "电商",
                "complexity": "MEDIUM",
                "use_template": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "template_id" in data
        assert "estimated_duration_days" in data
    
    def test_list_templates_api(self, auth_headers):
        """测试：获取模板列表API"""
        response = client.get(
            "/api/v1/ai-planning/templates",
            headers=auth_headers,
            params={"project_type": "WEB_DEV"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_template_detail_api(self, db: Session, auth_headers):
        """测试：获取模板详情API"""
        # 创建测试模板
        template = AIProjectPlanTemplate(
            template_code="API_TPL_001",
            template_name="API测试模板",
            project_type="WEB_DEV",
            is_active=True
        )
        db.add(template)
        db.commit()
        
        response = client.get(
            f"/api/v1/ai-planning/templates/{template.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == template.id
    
    def test_decompose_wbs_api(self, sample_project, auth_headers):
        """测试：WBS分解API"""
        response = client.post(
            "/api/v1/ai-planning/decompose-wbs",
            headers=auth_headers,
            json={
                "project_id": sample_project.id,
                "max_level": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "suggestions" in data
    
    def test_get_wbs_suggestions_api(self, sample_project, auth_headers):
        """测试：获取WBS建议API"""
        response = client.get(
            f"/api/v1/ai-planning/wbs/{sample_project.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert data["project_id"] == sample_project.id
    
    def test_accept_wbs_api(self, db: Session, sample_project, auth_headers):
        """测试：采纳WBS建议API"""
        # 创建测试WBS
        wbs = AIWbsSuggestion(
            suggestion_code="API_WBS_001",
            project_id=sample_project.id,
            wbs_level=1,
            wbs_code="1",
            task_name="测试任务",
            estimated_duration_days=10,
            is_active=True
        )
        db.add(wbs)
        db.commit()
        
        response = client.patch(
            f"/api/v1/ai-planning/wbs/{wbs.id}/accept",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_reject_wbs_api(self, db: Session, sample_project, auth_headers):
        """测试：拒绝WBS建议API"""
        wbs = AIWbsSuggestion(
            suggestion_code="API_WBS_002",
            project_id=sample_project.id,
            wbs_level=1,
            wbs_code="1",
            task_name="测试任务",
            estimated_duration_days=10,
            is_active=True
        )
        db.add(wbs)
        db.commit()
        
        response = client.patch(
            f"/api/v1/ai-planning/wbs/{wbs.id}/reject",
            headers=auth_headers,
            params={"reason": "不符合需求"}
        )
        
        assert response.status_code == 200
    
    def test_allocate_resources_api(self, db: Session, sample_project, auth_headers):
        """测试：资源分配API"""
        wbs = AIWbsSuggestion(
            suggestion_code="API_WBS_RES_001",
            project_id=sample_project.id,
            wbs_level=1,
            wbs_code="1",
            task_name="测试任务",
            estimated_duration_days=10,
            is_active=True
        )
        db.add(wbs)
        db.commit()
        
        response = client.post(
            "/api/v1/ai-planning/allocate-resources",
            headers=auth_headers,
            json={
                "wbs_suggestion_id": wbs.id,
                "available_user_ids": None,
                "constraints": None
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_recommendations" in data
    
    def test_get_resource_allocations_api(self, sample_project, auth_headers):
        """测试：获取资源分配API"""
        response = client.get(
            f"/api/v1/ai-planning/allocations/{sample_project.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
    
    def test_optimize_schedule_api(self, sample_project, auth_headers):
        """测试：进度排期优化API"""
        response = client.post(
            "/api/v1/ai-planning/optimize-schedule",
            headers=auth_headers,
            json={
                "project_id": sample_project.id,
                "start_date": "2026-03-01",
                "constraints": None
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_duration_days" in data
        assert "gantt_data" in data
        assert "critical_path" in data
    
    def test_get_project_schedule_api(self, sample_project, auth_headers):
        """测试：获取项目进度API"""
        response = client.get(
            f"/api/v1/ai-planning/schedule/{sample_project.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
    
    def test_get_accuracy_statistics_api(self, auth_headers):
        """测试：准确性统计API"""
        response = client.get(
            "/api/v1/ai-planning/statistics/accuracy",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "wbs_accuracy" in data
        assert "resource_allocation_accuracy" in data
    
    def test_get_performance_statistics_api(self, auth_headers):
        """测试：性能统计API"""
        response = client.get(
            "/api/v1/ai-planning/statistics/performance",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_generation_time_seconds" in data
        assert "success_rate" in data
    
    def test_api_error_handling(self, auth_headers):
        """测试：API错误处理"""
        # 测试不存在的模板
        response = client.get(
            "/api/v1/ai-planning/templates/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_api_validation(self, auth_headers):
        """测试：API参数验证"""
        # 缺少必需参数
        response = client.post(
            "/api/v1/ai-planning/generate-plan",
            headers=auth_headers,
            json={
                "project_name": "测试"
                # 缺少 project_type 和 requirements
            }
        )
        
        assert response.status_code == 422  # 验证错误
