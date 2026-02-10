"""
Pytest配置和测试夹具
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date, datetime

# 导入应用
import sys
sys.path.insert(0, '.')
from app.main import app


# ============== 测试客户端夹具 ==============

@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_client(client):
    """带认证的测试客户端（模拟登录用户）"""
    # 在实际项目中，这里应该设置认证token
    client.headers["Authorization"] = "Bearer test_token"
    client.headers["X-User-Id"] = "1"
    return client


# ============== 测试数据夹具 ==============

@pytest.fixture
def sample_project():
    """示例项目数据"""
    return {
        "project_code": "PRJ-TEST-001",
        "project_name": "测试项目",
        "customer_id": 1,
        "project_level": "B",
        "pm_id": 1,
        "te_id": 2,
        "plan_start_date": "2025-01-01",
        "plan_end_date": "2025-03-31",
        "plan_manhours": 500,
        "budget_amount": 200000,
        "description": "这是一个测试项目"
    }


@pytest.fixture
def sample_task():
    """示例任务数据"""
    return {
        "project_id": 1,
        "task_name": "测试任务",
        "wbs_code": "1.1",
        "phase": "方案设计",
        "task_type": "task",
        "owner_id": 1,
        "plan_start_date": "2025-01-10",
        "plan_end_date": "2025-01-20",
        "plan_manhours": 40,
        "weight": 10,
        "deliverable": "测试交付物",
        "description": "任务描述"
    }


@pytest.fixture
def sample_timesheet():
    """示例工时数据"""
    return {
        "project_id": 1,
        "task_id": 1,
        "work_date": "2025-01-15",
        "hours": 8,
        "work_content": "完成方案设计初稿",
        "overtime_type": "正常"
    }


@pytest.fixture
def sample_tasks_batch():
    """批量任务数据"""
    return [
        {
            "project_id": 1,
            "task_name": "任务1",
            "wbs_code": "1.1",
            "phase": "方案设计",
            "plan_start_date": "2025-01-10",
            "plan_end_date": "2025-01-15",
            "plan_manhours": 20
        },
        {
            "project_id": 1,
            "task_name": "任务2",
            "wbs_code": "1.2",
            "phase": "方案设计",
            "plan_start_date": "2025-01-16",
            "plan_end_date": "2025-01-20",
            "plan_manhours": 20,
            "predecessors": [{"task_id": 1, "link_type": "FS", "lag_days": 0}]
        }
    ]


# ============== 辅助函数 ==============

@pytest.fixture
def make_project(client, sample_project):
    """创建项目的工厂函数"""
    def _make_project(**kwargs):
        data = {**sample_project, **kwargs}
        response = client.post("/api/v1/projects", json=data)
        return response.json()
    return _make_project


@pytest.fixture
def make_task(client, sample_task):
    """创建任务的工厂函数"""
    def _make_task(**kwargs):
        data = {**sample_task, **kwargs}
        response = client.post("/api/v1/tasks", json=data)
        return response.json()
    return _make_task
