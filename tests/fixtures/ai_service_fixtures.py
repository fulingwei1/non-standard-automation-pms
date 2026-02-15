"""
AI服务测试Fixture
提供GLM-5、质量分析、资源调度等AI服务的Mock数据
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List


@pytest.fixture
def mock_glm_response():
    """Mock GLM-5 API响应"""
    return {
        "completion_date": "2026-04-15",
        "delay_days": 15,
        "confidence": 0.85,
        "risk_level": "high",
        "risk_factors": [
            "团队规模不足",
            "进度偏差较大",
            "剩余时间紧张"
        ],
        "recommendations": [
            "增加2名开发人员",
            "调整部分功能优先级",
            "增加加班时间"
        ]
    }


@pytest.fixture
def mock_schedule_prediction_data():
    """Mock进度预测数据"""
    return {
        "project_id": 1,
        "current_progress": 45.5,
        "planned_progress": 60.0,
        "remaining_days": 30,
        "team_size": 5,
        "predicted_completion_date": date(2026, 4, 15),
        "delay_days": 15,
        "confidence": 0.85,
        "risk_level": "high",
        "features": {
            "current_progress": 45.5,
            "planned_progress": 60.0,
            "progress_deviation": -14.5,
            "remaining_days": 30,
            "team_size": 5,
            "avg_daily_progress": 1.2,
            "required_daily_progress": 1.8,
            "velocity_ratio": 0.67,
            "complexity": "high"
        }
    }


@pytest.fixture
def mock_quality_risk_data():
    """Mock质量风险检测数据"""
    return {
        "project_id": 1,
        "module_name": "用户认证模块",
        "risk_level": "high",
        "risk_score": 75,
        "risk_category": "BUG",
        "risk_keywords": ["bug", "修复", "问题"],
        "abnormal_patterns": ["频繁修复", "多次返工"],
        "predicted_issues": [
            "可能存在架构问题",
            "需要增加单元测试"
        ],
        "rework_probability": 0.65,
        "estimated_impact_days": 5
    }


@pytest.fixture
def mock_wbs_decomposition():
    """Mock WBS分解数据"""
    return [
        {
            "level": 1,
            "wbs_code": "1.1",
            "task_name": "需求分析",
            "estimated_duration_days": 10,
            "estimated_hours": 80,
            "complexity": "medium",
            "task_type": "requirement"
        },
        {
            "level": 1,
            "wbs_code": "1.2",
            "task_name": "系统设计",
            "estimated_duration_days": 15,
            "estimated_hours": 120,
            "complexity": "high",
            "task_type": "design"
        },
        {
            "level": 1,
            "wbs_code": "1.3",
            "task_name": "开发实现",
            "estimated_duration_days": 40,
            "estimated_hours": 320,
            "complexity": "high",
            "task_type": "development"
        }
    ]


@pytest.fixture
def mock_resource_allocation():
    """Mock资源分配数据"""
    return {
        "user_id": 10,
        "wbs_suggestion_id": 1,
        "role": "后端开发",
        "allocated_hours": 80,
        "load_percentage": 75,
        "skill_match_score": 90,
        "experience_match_score": 85,
        "availability_score": 80,
        "performance_score": 88,
        "overall_match_score": 86,
        "recommendation_reason": "技能匹配度高，经验丰富，当前负载适中"
    }


@pytest.fixture
def mock_change_impact_data():
    """Mock变更影响分析数据"""
    return {
        "change_id": 1,
        "project_id": 1,
        "change_type": "REQUIREMENT",
        "affected_modules": ["用户模块", "订单模块", "支付模块"],
        "impact_score": 75,
        "risk_level": "high",
        "estimated_delay_days": 10,
        "affected_tasks_count": 15,
        "dependency_chain": [
            "用户模块 → 订单模块 → 支付模块"
        ]
    }


@pytest.fixture
def mock_ai_client_service():
    """Mock AI客户端服务"""
    with patch('app.services.ai_client_service.AIClientService') as mock:
        instance = MagicMock()
        
        # Mock chat方法
        async def mock_chat(*args, **kwargs):
            return {
                "choices": [{
                    "message": {
                        "content": '{"completion_date": "2026-04-15", "delay_days": 15, "confidence": 0.85, "risk_level": "high"}'
                    }
                }]
            }
        
        instance.chat = AsyncMock(side_effect=mock_chat)
        mock.return_value = instance
        yield mock


@pytest.fixture
def test_project_data():
    """测试项目数据"""
    return {
        "id": 1,
        "name": "测试项目A",
        "project_type": "WEB_DEV",
        "industry": "电商",
        "complexity": "high",
        "start_date": date(2026, 1, 1),
        "planned_end_date": date(2026, 6, 30),
        "current_progress": 45.5,
        "budget": 1000000,
        "team_size": 8
    }


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "id": 10,
        "username": "test_developer",
        "real_name": "张三",
        "role": "后端开发",
        "skill_tags": ["Python", "FastAPI", "PostgreSQL"],
        "hourly_rate": 200,
        "current_load": 60,
        "performance_rating": 4.5
    }


@pytest.fixture
def test_task_data():
    """测试任务数据"""
    return {
        "id": 100,
        "project_id": 1,
        "task_name": "实现用户认证功能",
        "task_type": "development",
        "estimated_hours": 40,
        "actual_hours": 0,
        "progress": 0,
        "priority": "high",
        "status": "pending",
        "assigned_to": None,
        "start_date": None,
        "end_date": None
    }


@pytest.fixture
def mock_database_session():
    """Mock数据库Session"""
    session = MagicMock()
    session.query = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.flush = MagicMock()
    return session


@pytest.fixture
def sample_work_logs():
    """示例工作日志数据"""
    return [
        {
            "date": date.today() - timedelta(days=1),
            "user": "开发A",
            "content": "修复了登录模块的bug，第3次修复了",
            "hours": 4
        },
        {
            "date": date.today() - timedelta(days=2),
            "user": "开发B",
            "content": "优化数据库查询性能，响应时间从2s降到500ms",
            "hours": 6
        },
        {
            "date": date.today() - timedelta(days=3),
            "user": "开发C",
            "content": "系统不稳定，经常崩溃，需要重新设计架构",
            "hours": 8
        }
    ]


@pytest.fixture
def mock_redis_client():
    """Mock Redis客户端"""
    with patch('app.utils.redis_client.redis_client') as mock:
        mock.get = MagicMock(return_value=None)
        mock.set = MagicMock(return_value=True)
        mock.delete = MagicMock(return_value=True)
        mock.expire = MagicMock(return_value=True)
        yield mock


@pytest.fixture
def performance_metrics():
    """性能指标数据"""
    return {
        "avg_daily_progress": 1.5,
        "velocity": 8.5,
        "burn_down_rate": 1.2,
        "team_efficiency": 0.85,
        "quality_score": 88,
        "on_time_delivery_rate": 0.75,
        "bug_density": 0.05,
        "test_coverage": 75
    }


@pytest.fixture
def cost_data():
    """成本数据"""
    return {
        "planned_cost": 1000000,
        "actual_cost": 550000,
        "remaining_budget": 450000,
        "burn_rate": 50000,
        "evm_metrics": {
            "pv": 600000,  # Planned Value
            "ev": 455000,  # Earned Value
            "ac": 550000,  # Actual Cost
            "cpi": 0.83,   # Cost Performance Index
            "spi": 0.76,   # Schedule Performance Index
        }
    }
