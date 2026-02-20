# -*- coding: utf-8 -*-
"""
项目风险服务测试 - 完整覆盖

测试范围：
1. 风险因子计算 - 里程碑、PMO风险、进度
2. 风险等级评估 - LOW/MEDIUM/HIGH/CRITICAL
3. 风险升级检测 - 历史记录、通知
4. 批量风险计算 - 多项目处理
5. 风险快照与趋势 - 数据分析

创建日期: 2026-02-21
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from app.services.project.project_risk_service import ProjectRiskService


# ==================== Fixtures ====================


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return MagicMock()


@pytest.fixture
def risk_service(mock_db):
    """创建风险服务实例"""
    return ProjectRiskService(mock_db)


@pytest.fixture
def mock_project():
    """Mock项目对象"""
    project = MagicMock()
    project.id = 1
    project.project_code = "PJ-TEST-001"
    project.project_name = "测试项目"
    project.progress_pct = Decimal("50.0")
    project.planned_start_date = date.today() - timedelta(days=30)
    project.planned_end_date = date.today() + timedelta(days=30)
    project.actual_start_date = date.today() - timedelta(days=30)
    project.contract_date = date.today() - timedelta(days=40)
    return project


@pytest.fixture
def mock_milestones():
    """Mock里程碑列表"""
    milestones = []
    
    # 逾期里程碑1 - 逾期5天
    m1 = MagicMock()
    m1.planned_date = date.today() - timedelta(days=5)
    m1.status = "IN_PROGRESS"
    milestones.append(m1)
    
    # 逾期里程碑2 - 逾期10天
    m2 = MagicMock()
    m2.planned_date = date.today() - timedelta(days=10)
    m2.status = "NOT_STARTED"
    milestones.append(m2)
    
    # 正常里程碑
    m3 = MagicMock()
    m3.planned_date = date.today() + timedelta(days=5)
    m3.status = "NOT_STARTED"
    milestones.append(m3)
    
    return milestones


@pytest.fixture
def mock_pmo_risks():
    """Mock PMO风险列表"""
    risks = []
    
    # CRITICAL风险
    r1 = MagicMock()
    r1.risk_level = "CRITICAL"
    r1.status = "IDENTIFIED"
    risks.append(r1)
    
    # HIGH风险
    r2 = MagicMock()
    r2.risk_level = "HIGH"
    r2.status = "MONITORING"
    risks.append(r2)
    
    # MEDIUM风险
    r3 = MagicMock()
    r3.risk_level = "MEDIUM"
    r3.status = "MONITORING"
    risks.append(r3)
    
    return risks


# ==================== 测试里程碑风险因子 ====================


def test_calculate_milestone_factors_no_milestones(risk_service, mock_db):
    """测试无里程碑场景"""
    # Mock查询返回0
    mock_db.query().filter().scalar.return_value = 0
    mock_db.query().filter().all.return_value = []
    
    factors = risk_service._calculate_milestone_factors(1, date.today())
    
    assert factors["total_milestones_count"] == 0
    assert factors["overdue_milestones_count"] == 0
    assert factors["overdue_milestone_ratio"] == 0
    assert factors["max_overdue_days"] == 0


def test_calculate_milestone_factors_with_overdue(risk_service, mock_db, mock_milestones):
    """测试有逾期里程碑"""
    # Mock查询结果
    mock_db.query().filter().scalar.return_value = 3
    mock_db.query().filter().all.return_value = mock_milestones[:2]  # 2个逾期
    
    factors = risk_service._calculate_milestone_factors(1, date.today())
    
    assert factors["total_milestones_count"] == 3
    assert factors["overdue_milestones_count"] == 2
    assert factors["overdue_milestone_ratio"] == 0.67  # 约2/3
    assert factors["max_overdue_days"] == 10


def test_calculate_milestone_factors_all_on_track(risk_service, mock_db):
    """测试所有里程碑都正常"""
    mock_db.query().filter().scalar.return_value = 5
    mock_db.query().filter().all.return_value = []  # 无逾期
    
    factors = risk_service._calculate_milestone_factors(1, date.today())
    
    assert factors["overdue_milestones_count"] == 0
    assert factors["overdue_milestone_ratio"] == 0.0


# ==================== 测试PMO风险因子 ====================


def test_calculate_pmo_risk_factors_no_risks(risk_service, mock_db):
    """测试无PMO风险"""
    mock_db.query().filter().all.return_value = []
    
    factors = risk_service._calculate_pmo_risk_factors(1)
    
    assert factors["open_risks_count"] == 0
    assert factors["high_risks_count"] == 0
    assert factors["critical_risks_count"] == 0


def test_calculate_pmo_risk_factors_with_risks(risk_service, mock_db, mock_pmo_risks):
    """测试有多种级别的PMO风险"""
    mock_db.query().filter().all.return_value = mock_pmo_risks
    
    factors = risk_service._calculate_pmo_risk_factors(1)
    
    assert factors["open_risks_count"] == 3
    assert factors["high_risks_count"] == 2  # CRITICAL + HIGH
    assert factors["critical_risks_count"] == 1


def test_calculate_pmo_risk_factors_only_low_risks(risk_service, mock_db):
    """测试只有低风险"""
    low_risk = MagicMock()
    low_risk.risk_level = "LOW"
    low_risk.status = "MONITORING"
    
    mock_db.query().filter().all.return_value = [low_risk]
    
    factors = risk_service._calculate_pmo_risk_factors(1)
    
    assert factors["open_risks_count"] == 1
    assert factors["high_risks_count"] == 0
    assert factors["critical_risks_count"] == 0


# ==================== 测试进度风险因子 ====================


def test_calculate_progress_factors_basic(risk_service, mock_project):
    """测试基础进度因子计算"""
    factors = risk_service._calculate_progress_factors(mock_project)
    
    assert factors["progress_pct"] == 50.0
    assert "schedule_variance" in factors


def test_calculate_progress_factors_on_schedule(risk_service, mock_project):
    """测试进度正常的项目"""
    mock_project.progress_pct = Decimal("50.0")
    
    factors = risk_service._calculate_progress_factors(mock_project)
    
    # 50%完成，时间过半，进度偏差应该接近0
    assert factors["progress_pct"] == 50.0
    assert abs(factors["schedule_variance"]) < 10  # 允许小幅偏差


def test_calculate_progress_factors_behind_schedule(risk_service, mock_project):
    """测试进度落后"""
    mock_project.progress_pct = Decimal("20.0")  # 实际进度20%
    
    factors = risk_service._calculate_progress_factors(mock_project)
    
    # 进度偏差应该为负
    assert factors["schedule_variance"] < 0


def test_calculate_progress_factors_no_planned_end_date(risk_service, mock_project):
    """测试无计划结束日期"""
    mock_project.planned_end_date = None
    
    factors = risk_service._calculate_progress_factors(mock_project)
    
    assert factors["schedule_variance"] == 0


def test_calculate_progress_factors_zero_duration(risk_service, mock_project):
    """测试零工期项目"""
    mock_project.planned_start_date = date.today()
    mock_project.planned_end_date = date.today()
    
    factors = risk_service._calculate_progress_factors(mock_project)
    
    assert factors["schedule_variance"] == 0


# ==================== 测试风险等级计算 ====================


def test_calculate_risk_level_low(risk_service):
    """测试低风险等级"""
    factors = {
        "overdue_milestone_ratio": 0.05,
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "schedule_variance": -5,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "LOW"


def test_calculate_risk_level_medium_by_milestone(risk_service):
    """测试中等风险 - 里程碑逾期10-30%"""
    factors = {
        "overdue_milestone_ratio": 0.15,
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "MEDIUM"


def test_calculate_risk_level_medium_by_one_high_risk(risk_service):
    """测试中等风险 - 1个高风险"""
    factors = {
        "overdue_milestone_ratio": 0.0,
        "critical_risks_count": 0,
        "high_risks_count": 1,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "MEDIUM"


def test_calculate_risk_level_medium_by_schedule(risk_service):
    """测试中等风险 - 进度偏差10-20%"""
    factors = {
        "overdue_milestone_ratio": 0.0,
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "schedule_variance": -12,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "MEDIUM"


def test_calculate_risk_level_high_by_milestone(risk_service):
    """测试高风险 - 里程碑逾期30-50%"""
    factors = {
        "overdue_milestone_ratio": 0.35,
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "HIGH"


def test_calculate_risk_level_high_by_two_high_risks(risk_service):
    """测试高风险 - 2个及以上高风险"""
    factors = {
        "overdue_milestone_ratio": 0.0,
        "critical_risks_count": 0,
        "high_risks_count": 2,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "HIGH"


def test_calculate_risk_level_high_by_schedule(risk_service):
    """测试高风险 - 进度偏差>20%"""
    factors = {
        "overdue_milestone_ratio": 0.0,
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "schedule_variance": -25,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "HIGH"


def test_calculate_risk_level_critical_by_milestone(risk_service):
    """测试严重风险 - 里程碑逾期>=50%"""
    factors = {
        "overdue_milestone_ratio": 0.6,
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "CRITICAL"


def test_calculate_risk_level_critical_by_critical_risk(risk_service):
    """测试严重风险 - 有CRITICAL风险"""
    factors = {
        "overdue_milestone_ratio": 0.0,
        "critical_risks_count": 1,
        "high_risks_count": 0,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "CRITICAL"


# ==================== 测试风险升级判定 ====================


def test_is_risk_upgrade_true_cases(risk_service):
    """测试风险升级判定 - 升级场景"""
    assert risk_service._is_risk_upgrade("LOW", "MEDIUM") is True
    assert risk_service._is_risk_upgrade("LOW", "HIGH") is True
    assert risk_service._is_risk_upgrade("LOW", "CRITICAL") is True
    assert risk_service._is_risk_upgrade("MEDIUM", "HIGH") is True
    assert risk_service._is_risk_upgrade("MEDIUM", "CRITICAL") is True
    assert risk_service._is_risk_upgrade("HIGH", "CRITICAL") is True


def test_is_risk_upgrade_false_cases(risk_service):
    """测试风险升级判定 - 非升级场景"""
    assert risk_service._is_risk_upgrade("MEDIUM", "LOW") is False
    assert risk_service._is_risk_upgrade("HIGH", "LOW") is False
    assert risk_service._is_risk_upgrade("HIGH", "MEDIUM") is False
    assert risk_service._is_risk_upgrade("CRITICAL", "HIGH") is False
    assert risk_service._is_risk_upgrade("LOW", "LOW") is False


# ==================== 测试完整风险计算 ====================


@patch.object(ProjectRiskService, '_calculate_milestone_factors')
@patch.object(ProjectRiskService, '_calculate_pmo_risk_factors')
@patch.object(ProjectRiskService, '_calculate_progress_factors')
@patch.object(ProjectRiskService, '_calculate_risk_level')
def test_calculate_project_risk_success(
    mock_risk_level, mock_progress, mock_pmo, mock_milestone,
    risk_service, mock_db, mock_project
):
    """测试完整的项目风险计算流程"""
    # Mock查询项目
    mock_db.query().filter().first.return_value = mock_project
    
    # Mock各个因子计算
    mock_milestone.return_value = {"total_milestones_count": 5, "overdue_milestones_count": 2, "overdue_milestone_ratio": 0.4, "max_overdue_days": 10}
    mock_pmo.return_value = {"open_risks_count": 3, "high_risks_count": 1, "critical_risks_count": 0}
    mock_progress.return_value = {"progress_pct": 50.0, "schedule_variance": -5}
    mock_risk_level.return_value = "MEDIUM"
    
    result = risk_service.calculate_project_risk(1)
    
    assert result["project_id"] == 1
    assert result["project_code"] == "PJ-TEST-001"
    assert result["risk_level"] == "MEDIUM"
    assert "risk_factors" in result
    assert result["risk_factors"]["total_milestones_count"] == 5
    assert result["risk_factors"]["open_risks_count"] == 3
    assert "calculated_at" in result["risk_factors"]


def test_calculate_project_risk_project_not_found(risk_service, mock_db):
    """测试项目不存在"""
    mock_db.query().filter().first.return_value = None
    
    with pytest.raises(ValueError, match="项目不存在"):
        risk_service.calculate_project_risk(999)


# ==================== 测试风险快照 ====================


@patch.object(ProjectRiskService, 'calculate_project_risk')
def test_create_risk_snapshot(mock_calc, risk_service, mock_db):
    """测试创建风险快照"""
    mock_calc.return_value = {
        "project_id": 1,
        "project_code": "PJ-TEST-001",
        "risk_level": "MEDIUM",
        "risk_factors": {
            "overdue_milestones_count": 2,
            "total_milestones_count": 5,
            "overdue_tasks_count": 0,
            "open_risks_count": 3,
            "high_risks_count": 1,
        }
    }
    
    snapshot = risk_service.create_risk_snapshot(1)
    
    assert snapshot.project_id == 1
    assert snapshot.risk_level == "MEDIUM"
    assert snapshot.overdue_milestones_count == 2
    assert snapshot.total_milestones_count == 5
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


# ==================== 测试历史查询 ====================


def test_get_risk_history(risk_service, mock_db):
    """测试获取风险历史"""
    mock_history = [MagicMock(), MagicMock()]
    mock_db.query().filter().order_by().limit().all.return_value = mock_history
    
    result = risk_service.get_risk_history(1, limit=10)
    
    assert len(result) == 2
    assert result == mock_history


def test_get_risk_history_default_limit(risk_service, mock_db):
    """测试默认限制50条"""
    mock_db.query().filter().order_by().limit().all.return_value = []
    
    risk_service.get_risk_history(1)
    
    # 验证limit被调用且值为50
    mock_db.query().filter().order_by().limit.assert_called_with(50)


# ==================== 测试趋势分析 ====================


def test_get_risk_trend(risk_service, mock_db):
    """测试获取风险趋势"""
    mock_snapshot1 = MagicMock()
    mock_snapshot1.snapshot_date = datetime.now()
    mock_snapshot1.risk_level = "MEDIUM"
    mock_snapshot1.overdue_milestones_count = 2
    mock_snapshot1.open_risks_count = 3
    mock_snapshot1.high_risks_count = 1
    
    mock_db.query().filter().order_by().all.return_value = [mock_snapshot1]
    
    result = risk_service.get_risk_trend(1, days=30)
    
    assert len(result) == 1
    assert result[0]["risk_level"] == "MEDIUM"
    assert result[0]["overdue_milestones"] == 2
    assert result[0]["open_risks"] == 3
    assert result[0]["high_risks"] == 1
    assert "date" in result[0]


# ==================== 测试批量计算 ====================


@patch.object(ProjectRiskService, 'auto_upgrade_risk_level')
def test_batch_calculate_risks_all_projects(mock_auto, risk_service, mock_db):
    """测试批量计算所有激活项目"""
    mock_projects = [
        MagicMock(id=1, is_active=True),
        MagicMock(id=2, is_active=True),
    ]
    mock_db.query().filter().all.return_value = mock_projects
    mock_auto.side_effect = [
        {"project_id": 1, "project_code": "PJ-001", "new_risk_level": "LOW"},
        {"project_id": 2, "project_code": "PJ-002", "new_risk_level": "MEDIUM"},
    ]
    
    results = risk_service.batch_calculate_risks()
    
    assert len(results) == 2
    assert results[0]["project_id"] == 1
    assert results[1]["project_id"] == 2


@patch.object(ProjectRiskService, 'auto_upgrade_risk_level')
def test_batch_calculate_risks_specific_projects(mock_auto, risk_service, mock_db):
    """测试批量计算指定项目"""
    mock_project = MagicMock(id=1, is_active=True)
    mock_db.query().filter().all.return_value = [mock_project]
    mock_auto.return_value = {"project_id": 1, "project_code": "PJ-001", "new_risk_level": "LOW"}
    
    results = risk_service.batch_calculate_risks(project_ids=[1])
    
    assert len(results) == 1
    assert results[0]["project_id"] == 1


@patch.object(ProjectRiskService, 'auto_upgrade_risk_level')
def test_batch_calculate_risks_with_error(mock_auto, risk_service, mock_db, caplog):
    """测试批量计算时错误处理"""
    import logging
    
    mock_project = MagicMock(id=1, project_code="PJ-ERR", is_active=True)
    mock_db.query().filter().all.return_value = [mock_project]
    mock_auto.side_effect = Exception("计算失败")
    
    with caplog.at_level(logging.ERROR):
        results = risk_service.batch_calculate_risks()
    
    assert len(results) == 1
    assert "error" in results[0]
    assert "计算失败" in results[0]["error"]


# ==================== 测试自动升级 ====================


@patch.object(ProjectRiskService, 'calculate_project_risk')
@patch.object(ProjectRiskService, '_send_risk_upgrade_notification')
@patch.object(ProjectRiskService, '_is_risk_upgrade')
def test_auto_upgrade_risk_level_no_history(mock_upgrade, mock_notify, mock_calc, risk_service, mock_db):
    """测试无历史记录时的自动升级"""
    mock_calc.return_value = {
        "project_id": 1,
        "project_code": "PJ-001",
        "risk_level": "MEDIUM",
        "risk_factors": {}
    }
    mock_db.query().filter().order_by().first.return_value = None  # 无历史
    mock_upgrade.return_value = True
    
    result = risk_service.auto_upgrade_risk_level(1)
    
    assert result["old_risk_level"] == "LOW"  # 默认值
    assert result["new_risk_level"] == "MEDIUM"
    assert result["is_upgrade"] is True
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@patch.object(ProjectRiskService, 'calculate_project_risk')
@patch.object(ProjectRiskService, '_send_risk_upgrade_notification')
def test_auto_upgrade_risk_level_with_history(mock_notify, mock_calc, risk_service, mock_db, mock_project):
    """测试有历史记录时的升级检测"""
    mock_calc.return_value = {
        "project_id": 1,
        "project_code": "PJ-001",
        "risk_level": "HIGH",
        "risk_factors": {}
    }
    
    # Mock历史记录
    mock_history = MagicMock()
    mock_history.new_risk_level = "MEDIUM"
    mock_db.query().filter().order_by().first.return_value = mock_history
    
    # Mock项目查询（用于通知）
    mock_db.query().filter().first.return_value = mock_project
    
    result = risk_service.auto_upgrade_risk_level(1)
    
    assert result["old_risk_level"] == "MEDIUM"
    assert result["new_risk_level"] == "HIGH"
    assert result["is_upgrade"] is True
    mock_notify.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app/services/project/project_risk_service", "--cov-report=term-missing"])
