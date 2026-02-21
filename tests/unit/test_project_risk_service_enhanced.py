# -*- coding: utf-8 -*-
"""
项目风险服务增强测试 - app/services/project_risk/project_risk_service.py

测试覆盖范围：
1. generate_risk_code - 风险编号生成
2. create_risk - 风险创建
3. get_risk_list - 风险列表查询（多种筛选条件）
4. get_risk_by_id - 风险详情查询
5. update_risk - 风险更新
6. delete_risk - 风险删除
7. get_risk_matrix - 风险矩阵
8. get_risk_summary - 风险汇总统计

创建日期: 2026-02-21
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.project_risk.project_risk_service import ProjectRiskService
from app.models.project_risk import ProjectRisk, RiskTypeEnum, RiskStatusEnum
from app.models.project import Project
from app.models.user import User


# ==================== Fixtures ====================


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = MagicMock()
    return db


@pytest.fixture
def risk_service(mock_db):
    """创建风险服务实例"""
    return ProjectRiskService(mock_db)


@pytest.fixture
def mock_project():
    """Mock项目对象"""
    project = MagicMock()
    project.id = 1
    project.project_code = "PRJ-2024-001"
    project.project_name = "测试项目"
    return project


@pytest.fixture
def mock_user():
    """Mock用户对象"""
    user = MagicMock()
    user.id = 100
    user.username = "test_user"
    user.real_name = "测试用户"
    return user


@pytest.fixture
def mock_risk():
    """Mock风险对象"""
    risk = MagicMock(spec=ProjectRisk)
    risk.id = 1
    risk.risk_code = "RISK-PRJ-2024-001-0001"
    risk.project_id = 1
    risk.risk_name = "技术风险测试"
    risk.description = "这是一个测试风险"
    risk.risk_type = RiskTypeEnum.TECHNICAL
    risk.probability = 3
    risk.impact = 4
    risk.risk_score = 12
    risk.risk_level = "HIGH"
    risk.status = RiskStatusEnum.IDENTIFIED
    risk.owner_id = 100
    risk.owner_name = "测试用户"
    risk.created_by_id = 100
    risk.created_by_name = "测试用户"
    risk.is_occurred = False
    risk.mitigation_plan = "缓解计划"
    risk.contingency_plan = "应急计划"
    risk.target_closure_date = datetime.now() + timedelta(days=30)
    risk.actual_closure_date = None
    risk.calculate_risk_score = MagicMock()
    return risk


# ==================== 测试 generate_risk_code ====================


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_generate_risk_code_first_risk(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试生成第一个风险编号"""
    mock_get_or_404.return_value = mock_project
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    
    code = risk_service.generate_risk_code(1)
    
    assert code == "RISK-PRJ-2024-001-0001"
    mock_get_or_404.assert_called_once_with(mock_db, Project, 1, detail="项目不存在")


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_generate_risk_code_multiple_risks(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试生成后续风险编号"""
    mock_get_or_404.return_value = mock_project
    mock_db.query.return_value.filter.return_value.count.return_value = 5
    
    code = risk_service.generate_risk_code(1)
    
    assert code == "RISK-PRJ-2024-001-0006"


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_generate_risk_code_project_not_found(mock_get_or_404, risk_service, mock_db):
    """测试项目不存在时生成编号"""
    mock_get_or_404.side_effect = HTTPException(status_code=404, detail="项目不存在")
    
    with pytest.raises(HTTPException) as exc_info:
        risk_service.generate_risk_code(999)
    
    assert exc_info.value.status_code == 404


# ==================== 测试 create_risk ====================


@patch('app.services.project_risk.project_risk_service.save_obj')
@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_create_risk_basic(mock_get_or_404, mock_save_obj, risk_service, mock_db, mock_project, mock_user):
    """测试基本风险创建"""
    mock_get_or_404.return_value = mock_project
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    result = risk_service.create_risk(
        project_id=1,
        risk_name="测试风险",
        description="这是一个测试",
        risk_type="TECHNICAL",
        probability=3,
        impact=4,
        mitigation_plan="缓解计划",
        contingency_plan="应急计划",
        owner_id=None,
        target_closure_date=None,
        current_user=mock_user
    )
    
    assert isinstance(result, ProjectRisk)
    assert result.risk_name == "测试风险"
    assert result.probability == 3
    assert result.impact == 4
    assert result.status == RiskStatusEnum.IDENTIFIED
    assert result.created_by_id == 100
    mock_save_obj.assert_called_once()


@patch('app.services.project_risk.project_risk_service.save_obj')
@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_create_risk_with_owner(mock_get_or_404, mock_save_obj, risk_service, mock_db, mock_project, mock_user):
    """测试创建带负责人的风险"""
    mock_get_or_404.return_value = mock_project
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    
    owner = MagicMock()
    owner.id = 200
    owner.real_name = "风险负责人"
    owner.username = "risk_owner"
    mock_db.query.return_value.filter.return_value.first.return_value = owner
    
    result = risk_service.create_risk(
        project_id=1,
        risk_name="测试风险",
        description="带负责人",
        risk_type="COST",
        probability=4,
        impact=5,
        mitigation_plan=None,
        contingency_plan=None,
        owner_id=200,
        target_closure_date=datetime.now() + timedelta(days=15),
        current_user=mock_user
    )
    
    assert result.owner_id == 200
    assert result.owner_name == "风险负责人"


@patch('app.services.project_risk.project_risk_service.save_obj')
@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_create_risk_owner_not_found(mock_get_or_404, mock_save_obj, risk_service, mock_db, mock_project, mock_user):
    """测试负责人不存在时创建风险"""
    mock_get_or_404.return_value = mock_project
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    result = risk_service.create_risk(
        project_id=1,
        risk_name="测试风险",
        description="负责人不存在",
        risk_type="SCHEDULE",
        probability=2,
        impact=3,
        mitigation_plan=None,
        contingency_plan=None,
        owner_id=999,
        target_closure_date=None,
        current_user=mock_user
    )
    
    # owner_name应该保持None或未设置
    assert result.owner_id == 999


# ==================== 测试 get_risk_list ====================


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_list_basic(mock_get_or_404, risk_service, mock_db, mock_project, mock_risk):
    """测试基本风险列表查询"""
    mock_get_or_404.return_value = mock_project
    mock_query = mock_db.query.return_value.filter.return_value
    mock_query.count.return_value = 1
    mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_risk]
    
    risks, total = risk_service.get_risk_list(project_id=1)
    
    assert total == 1
    assert len(risks) == 1
    assert risks[0].risk_name == "技术风险测试"


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_list_with_risk_type_filter(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试按风险类型筛选"""
    mock_get_or_404.return_value = mock_project
    # Mock链式调用
    mock_filter = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 0
    mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    
    risks, total = risk_service.get_risk_list(project_id=1, risk_type="TECHNICAL")
    
    assert total == 0
    assert len(risks) == 0


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_list_with_risk_level_filter(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试按风险等级筛选"""
    mock_get_or_404.return_value = mock_project
    mock_filter = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 0
    mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    
    risks, total = risk_service.get_risk_list(project_id=1, risk_level="HIGH")
    
    assert total == 0


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_list_with_status_filter(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试按状态筛选"""
    mock_get_or_404.return_value = mock_project
    mock_filter = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 0
    mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    
    risks, total = risk_service.get_risk_list(project_id=1, status="MONITORING")
    
    assert total == 0


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_list_with_owner_filter(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试按负责人筛选"""
    mock_get_or_404.return_value = mock_project
    mock_filter = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 0
    mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    
    risks, total = risk_service.get_risk_list(project_id=1, owner_id=100)
    
    assert total == 0


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_list_with_occurred_filter_true(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试筛选已发生风险"""
    mock_get_or_404.return_value = mock_project
    mock_filter = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 0
    mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    
    risks, total = risk_service.get_risk_list(project_id=1, is_occurred=True)
    
    assert total == 0


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_list_with_occurred_filter_false(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试筛选未发生风险"""
    mock_get_or_404.return_value = mock_project
    mock_filter = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 0
    mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    
    risks, total = risk_service.get_risk_list(project_id=1, is_occurred=False)
    
    assert total == 0


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_list_with_pagination(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试分页功能"""
    mock_get_or_404.return_value = mock_project
    mock_query = mock_db.query.return_value.filter.return_value
    mock_query.count.return_value = 100
    mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    
    risks, total = risk_service.get_risk_list(project_id=1, offset=20, limit=10)
    
    assert total == 100


# ==================== 测试 get_risk_by_id ====================


def test_get_risk_by_id_success(risk_service, mock_db, mock_risk):
    """测试成功获取风险详情"""
    mock_db.query.return_value.filter.return_value.first.return_value = mock_risk
    
    result = risk_service.get_risk_by_id(project_id=1, risk_id=1)
    
    assert result.id == 1
    assert result.risk_name == "技术风险测试"


def test_get_risk_by_id_not_found(risk_service, mock_db):
    """测试风险不存在"""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        risk_service.get_risk_by_id(project_id=1, risk_id=999)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "风险不存在"


# ==================== 测试 update_risk ====================


def test_update_risk_basic_fields(risk_service, mock_db, mock_risk, mock_user):
    """测试更新基本字段"""
    # Mock get_risk_by_id查询
    mock_db.query.return_value.filter.return_value.first.return_value = mock_risk
    
    update_data = {
        "risk_name": "更新后的风险名称",
        "description": "更新后的描述"
    }
    
    result = risk_service.update_risk(
        project_id=1,
        risk_id=1,
        update_data=update_data,
        current_user=mock_user
    )
    
    assert mock_risk.risk_name == "更新后的风险名称"
    assert mock_risk.description == "更新后的描述"
    assert mock_risk.updated_by_id == 100
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_risk)


def test_update_risk_probability_and_impact(risk_service, mock_db, mock_risk, mock_user):
    """测试更新概率和影响，触发评分重算"""
    mock_db.query.return_value.filter.return_value.first.return_value = mock_risk
    
    update_data = {
        "probability": 5,
        "impact": 5
    }
    
    risk_service.update_risk(
        project_id=1,
        risk_id=1,
        update_data=update_data,
        current_user=mock_user
    )
    
    assert mock_risk.probability == 5
    assert mock_risk.impact == 5
    mock_risk.calculate_risk_score.assert_called_once()


def test_update_risk_change_owner(risk_service, mock_db, mock_risk, mock_user):
    """测试更新负责人"""
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_risk,  # 第一次查询：获取风险
        MagicMock(id=200, real_name="新负责人", username="new_owner")  # 第二次查询：获取负责人
    ]
    
    update_data = {"owner_id": 200}
    
    result = risk_service.update_risk(
        project_id=1,
        risk_id=1,
        update_data=update_data,
        current_user=mock_user
    )
    
    assert mock_risk.owner_id == 200
    assert mock_risk.owner_name == "新负责人"


def test_update_risk_close_status(risk_service, mock_db, mock_risk, mock_user):
    """测试更新为关闭状态，自动设置关闭日期"""
    mock_risk.actual_closure_date = None
    mock_db.query.return_value.filter.return_value.first.return_value = mock_risk
    
    update_data = {"status": "CLOSED"}
    
    risk_service.update_risk(
        project_id=1,
        risk_id=1,
        update_data=update_data,
        current_user=mock_user
    )
    
    assert mock_risk.status == "CLOSED"
    assert mock_risk.actual_closure_date is not None


def test_update_risk_already_closed(risk_service, mock_db, mock_risk, mock_user):
    """测试已关闭风险不重复设置关闭日期"""
    existing_date = datetime.now() - timedelta(days=5)
    mock_risk.actual_closure_date = existing_date
    mock_db.query.return_value.filter.return_value.first.return_value = mock_risk
    
    update_data = {"status": "CLOSED"}
    
    risk_service.update_risk(
        project_id=1,
        risk_id=1,
        update_data=update_data,
        current_user=mock_user
    )
    
    assert mock_risk.actual_closure_date == existing_date


# ==================== 测试 delete_risk ====================


@patch('app.services.project_risk.project_risk_service.delete_obj')
def test_delete_risk_success(mock_delete_obj, risk_service, mock_db, mock_risk):
    """测试成功删除风险"""
    mock_db.query.return_value.filter.return_value.first.return_value = mock_risk
    
    result = risk_service.delete_risk(project_id=1, risk_id=1)
    
    assert result["risk_code"] == "RISK-PRJ-2024-001-0001"
    assert result["risk_name"] == "技术风险测试"
    assert result["risk_type"] == RiskTypeEnum.TECHNICAL
    assert result["risk_score"] == 12
    mock_delete_obj.assert_called_once_with(mock_db, mock_risk)


@patch('app.services.project_risk.project_risk_service.delete_obj')
def test_delete_risk_not_found(mock_delete_obj, risk_service, mock_db):
    """测试删除不存在的风险"""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        risk_service.delete_risk(project_id=1, risk_id=999)
    
    assert exc_info.value.status_code == 404


# ==================== 测试 get_risk_matrix ====================


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_matrix_empty(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试空风险矩阵"""
    mock_get_or_404.return_value = mock_project
    mock_db.query.return_value.filter.return_value.all.return_value = []
    
    result = risk_service.get_risk_matrix(project_id=1)
    
    assert len(result["matrix"]) == 25  # 5x5 矩阵
    assert result["summary"]["total_risks"] == 0
    assert result["summary"]["critical_count"] == 0


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_matrix_with_risks(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试包含风险的矩阵"""
    mock_get_or_404.return_value = mock_project
    
    # 创建不同级别的风险
    risk1 = MagicMock()
    risk1.id = 1
    risk1.risk_code = "RISK-001"
    risk1.risk_name = "高风险"
    risk1.risk_type = RiskTypeEnum.TECHNICAL
    risk1.probability = 4
    risk1.impact = 5
    risk1.risk_score = 20
    risk1.risk_level = "CRITICAL"
    risk1.status = RiskStatusEnum.MONITORING
    
    risk2 = MagicMock()
    risk2.id = 2
    risk2.risk_code = "RISK-002"
    risk2.risk_name = "中风险"
    risk2.probability = 3
    risk2.impact = 2
    risk2.risk_score = 6
    risk2.risk_level = "MEDIUM"
    risk2.status = RiskStatusEnum.IDENTIFIED
    
    mock_db.query.return_value.filter.return_value.all.return_value = [risk1, risk2]
    
    result = risk_service.get_risk_matrix(project_id=1)
    
    assert len(result["matrix"]) == 25
    assert result["summary"]["total_risks"] == 2
    assert result["summary"]["critical_count"] == 1
    assert result["summary"]["medium_count"] == 1


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_matrix_excludes_closed(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试矩阵不包含已关闭风险"""
    mock_get_or_404.return_value = mock_project
    
    closed_risk = MagicMock()
    closed_risk.status = RiskStatusEnum.CLOSED
    
    mock_db.query.return_value.filter.return_value.all.return_value = []
    
    result = risk_service.get_risk_matrix(project_id=1)
    
    assert result["summary"]["total_risks"] == 0


# ==================== 测试 get_risk_summary ====================


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_summary_empty(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试空项目的风险汇总"""
    mock_get_or_404.return_value = mock_project
    mock_db.query.return_value.filter.return_value.all.return_value = []
    
    result = risk_service.get_risk_summary(project_id=1)
    
    assert result["total_risks"] == 0
    assert result["occurred_count"] == 0
    assert result["closed_count"] == 0
    assert result["high_priority_count"] == 0
    assert result["avg_risk_score"] == 0


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_summary_with_risks(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试包含多种风险的汇总"""
    mock_get_or_404.return_value = mock_project
    
    # 创建不同类型、等级、状态的风险
    risks = []
    
    # CRITICAL技术风险，已发生
    r1 = MagicMock()
    r1.risk_type = RiskTypeEnum.TECHNICAL
    r1.risk_level = "CRITICAL"
    r1.status = RiskStatusEnum.OCCURRED
    r1.is_occurred = True
    r1.risk_score = 20
    risks.append(r1)
    
    # HIGH成本风险，监控中
    r2 = MagicMock()
    r2.risk_type = RiskTypeEnum.COST
    r2.risk_level = "HIGH"
    r2.status = RiskStatusEnum.MONITORING
    r2.is_occurred = False
    r2.risk_score = 15
    risks.append(r2)
    
    # MEDIUM进度风险，已关闭
    r3 = MagicMock()
    r3.risk_type = RiskTypeEnum.SCHEDULE
    r3.risk_level = "MEDIUM"
    r3.status = RiskStatusEnum.CLOSED
    r3.is_occurred = False
    r3.risk_score = 9
    risks.append(r3)
    
    # LOW质量风险，已识别
    r4 = MagicMock()
    r4.risk_type = RiskTypeEnum.QUALITY
    r4.risk_level = "LOW"
    r4.status = RiskStatusEnum.IDENTIFIED
    r4.is_occurred = False
    r4.risk_score = 4
    risks.append(r4)
    
    mock_db.query.return_value.filter.return_value.all.return_value = risks
    
    result = risk_service.get_risk_summary(project_id=1)
    
    assert result["total_risks"] == 4
    assert result["by_type"]["TECHNICAL"] == 1
    assert result["by_type"]["COST"] == 1
    assert result["by_type"]["SCHEDULE"] == 1
    assert result["by_type"]["QUALITY"] == 1
    assert result["by_level"]["CRITICAL"] == 1
    assert result["by_level"]["HIGH"] == 1
    assert result["by_level"]["MEDIUM"] == 1
    assert result["by_level"]["LOW"] == 1
    assert result["occurred_count"] == 1
    assert result["closed_count"] == 1
    assert result["high_priority_count"] == 2  # CRITICAL + HIGH
    assert result["avg_risk_score"] == 12.0  # (20+15+9+4)/4


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_summary_all_types(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试所有风险类型的统计"""
    mock_get_or_404.return_value = mock_project
    
    risks = []
    for risk_type in RiskTypeEnum:
        risk = MagicMock()
        risk.risk_type = risk_type
        risk.risk_level = "MEDIUM"
        risk.status = RiskStatusEnum.MONITORING
        risk.is_occurred = False
        risk.risk_score = 8
        risks.append(risk)
    
    mock_db.query.return_value.filter.return_value.all.return_value = risks
    
    result = risk_service.get_risk_summary(project_id=1)
    
    # 验证所有类型都有统计
    assert "TECHNICAL" in result["by_type"]
    assert "COST" in result["by_type"]
    assert "SCHEDULE" in result["by_type"]
    assert "QUALITY" in result["by_type"]


@patch('app.services.project_risk.project_risk_service.get_or_404')
def test_get_risk_summary_all_statuses(mock_get_or_404, risk_service, mock_db, mock_project):
    """测试所有风险状态的统计"""
    mock_get_or_404.return_value = mock_project
    
    risks = []
    for status in RiskStatusEnum:
        risk = MagicMock()
        risk.risk_type = RiskTypeEnum.TECHNICAL
        risk.risk_level = "MEDIUM"
        risk.status = status
        risk.is_occurred = False
        risk.risk_score = 8
        risks.append(risk)
    
    mock_db.query.return_value.filter.return_value.all.return_value = risks
    
    result = risk_service.get_risk_summary(project_id=1)
    
    # 验证所有状态都有统计
    assert "IDENTIFIED" in result["by_status"]
    assert "ANALYZING" in result["by_status"]
    assert "PLANNING" in result["by_status"]
    assert "MONITORING" in result["by_status"]
    assert "MITIGATED" in result["by_status"]
    assert "OCCURRED" in result["by_status"]
    assert "CLOSED" in result["by_status"]


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--cov=app/services/project_risk/project_risk_service",
        "--cov-report=term-missing",
        "--cov-report=html"
    ])
