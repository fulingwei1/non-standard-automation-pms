# -*- coding: utf-8 -*-
"""
项目风险服务测试 - 完整覆盖

测试范围：
1. 风险识别 - 里程碑、PMO风险、进度
2. 风险评估 - 风险等级计算
3. 风险跟踪 - 历史记录、快照
4. 预警机制 - 升级检测、通知
5. 风险报告 - 趋势分析

创建日期: 2026-02-21
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord
from app.models.pmo import PmoProjectRisk
from app.models.project import Customer, Project, ProjectMilestone
from app.models.project.risk_history import ProjectRiskHistory, ProjectRiskSnapshot
from app.services.project.project_risk_service import ProjectRiskService


# ==================== Fixtures ====================


@pytest.fixture
def risk_service(db_session: Session):
    """创建风险服务实例"""
    return ProjectRiskService(db_session)


@pytest.fixture
def test_customer(db_session: Session):
    """创建测试客户"""
    customer = Customer(
        customer_code="CUST-RISK-001",
        customer_name="风险测试客户",
        contact_person="测试联系人",
        contact_phone="13800000000",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()
    return customer


@pytest.fixture
def test_project(db_session: Session, test_customer):
    """创建测试项目"""
    project = Project(
        project_code="PJ-RISK-001",
        project_name="风险测试项目",
        customer_id=test_customer.id,
        customer_name=test_customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        progress_pct=Decimal("30.0"),
        contract_date=date.today() - timedelta(days=60),
        planned_start_date=date.today() - timedelta(days=50),
        planned_end_date=date.today() + timedelta(days=100),
        actual_start_date=date.today() - timedelta(days=50),
        is_active=True,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_milestones(db_session: Session, test_project):
    """创建测试里程碑数据"""
    milestones = []
    
    # 正常里程碑
    m1 = ProjectMilestone(
        project_id=test_project.id,
        milestone_name="需求评审",
        planned_date=date.today() - timedelta(days=40),
        status="COMPLETED",
        completion_date=date.today() - timedelta(days=42),
    )
    
    # 逾期里程碑 - 逾期5天
    m2 = ProjectMilestone(
        project_id=test_project.id,
        milestone_name="设计评审",
        planned_date=date.today() - timedelta(days=5),
        status="IN_PROGRESS",
    )
    
    # 逾期里程碑 - 逾期15天
    m3 = ProjectMilestone(
        project_id=test_project.id,
        milestone_name="原型测试",
        planned_date=date.today() - timedelta(days=15),
        status="NOT_STARTED",
    )
    
    # 未来里程碑
    m4 = ProjectMilestone(
        project_id=test_project.id,
        milestone_name="验收测试",
        planned_date=date.today() + timedelta(days=30),
        status="NOT_STARTED",
    )
    
    milestones.extend([m1, m2, m3, m4])
    db_session.add_all(milestones)
    db_session.commit()
    return milestones


@pytest.fixture
def test_pmo_risks(db_session: Session, test_project):
    """创建测试PMO风险数据"""
    risks = []
    
    # CRITICAL级别风险
    r1 = PmoProjectRisk(
        project_id=test_project.id,
        risk_title="核心技术依赖第三方",
        risk_level="CRITICAL",
        status="IDENTIFIED",
    )
    
    # HIGH级别风险
    r2 = PmoProjectRisk(
        project_id=test_project.id,
        risk_title="关键人员可能离职",
        risk_level="HIGH",
        status="MONITORING",
    )
    
    # MEDIUM级别风险
    r3 = PmoProjectRisk(
        project_id=test_project.id,
        risk_title="供应商延期风险",
        risk_level="MEDIUM",
        status="MONITORING",
    )
    
    # 已解决风险（不计入）
    r4 = PmoProjectRisk(
        project_id=test_project.id,
        risk_title="已解决的风险",
        risk_level="HIGH",
        status="RESOLVED",
    )
    
    risks.extend([r1, r2, r3, r4])
    db_session.add_all(risks)
    db_session.commit()
    return risks


# ==================== 测试风险识别 ====================


def test_calculate_milestone_factors_no_milestones(risk_service, test_project):
    """测试无里程碑的情况"""
    factors = risk_service._calculate_milestone_factors(test_project.id, date.today())
    
    assert factors["total_milestones_count"] == 0
    assert factors["overdue_milestones_count"] == 0
    assert factors["overdue_milestone_ratio"] == 0
    assert factors["max_overdue_days"] == 0


def test_calculate_milestone_factors_with_overdue(risk_service, test_project, test_milestones):
    """测试有逾期里程碑的情况"""
    factors = risk_service._calculate_milestone_factors(test_project.id, date.today())
    
    assert factors["total_milestones_count"] == 4
    assert factors["overdue_milestones_count"] == 2  # 2个逾期
    assert factors["overdue_milestone_ratio"] == 0.5  # 50%
    assert factors["max_overdue_days"] == 15  # 最大逾期15天


def test_calculate_milestone_factors_all_completed(db_session, risk_service, test_project):
    """测试所有里程碑都已完成的情况"""
    milestone = ProjectMilestone(
        project_id=test_project.id,
        milestone_name="已完成里程碑",
        planned_date=date.today() - timedelta(days=10),
        status="COMPLETED",
        completion_date=date.today() - timedelta(days=12),
    )
    db_session.add(milestone)
    db_session.commit()
    
    factors = risk_service._calculate_milestone_factors(test_project.id, date.today())
    
    assert factors["overdue_milestones_count"] == 0
    assert factors["overdue_milestone_ratio"] == 0


def test_calculate_pmo_risk_factors_no_risks(risk_service, test_project):
    """测试无PMO风险的情况"""
    factors = risk_service._calculate_pmo_risk_factors(test_project.id)
    
    assert factors["open_risks_count"] == 0
    assert factors["high_risks_count"] == 0
    assert factors["critical_risks_count"] == 0


def test_calculate_pmo_risk_factors_with_risks(risk_service, test_project, test_pmo_risks):
    """测试有PMO风险的情况"""
    factors = risk_service._calculate_pmo_risk_factors(test_project.id)
    
    assert factors["open_risks_count"] == 3  # 3个未关闭（排除RESOLVED）
    assert factors["high_risks_count"] == 2  # 1个CRITICAL + 1个HIGH
    assert factors["critical_risks_count"] == 1  # 1个CRITICAL


def test_calculate_pmo_risk_factors_closed_not_counted(db_session, risk_service, test_project):
    """测试已关闭的风险不计入统计"""
    closed_risk = PmoProjectRisk(
        project_id=test_project.id,
        risk_title="已关闭风险",
        risk_level="CRITICAL",
        status="CLOSED",
    )
    db_session.add(closed_risk)
    db_session.commit()
    
    factors = risk_service._calculate_pmo_risk_factors(test_project.id)
    
    assert factors["critical_risks_count"] == 0


def test_calculate_progress_factors_basic(risk_service, test_project):
    """测试进度因子计算 - 基础情况"""
    factors = risk_service._calculate_progress_factors(test_project)
    
    assert factors["progress_pct"] == 30.0
    assert "schedule_variance" in factors


def test_calculate_progress_factors_schedule_variance(db_session, risk_service, test_project):
    """测试进度偏差计算"""
    # 更新项目进度为10%（低于预期进度）
    test_project.progress_pct = Decimal("10.0")
    db_session.commit()
    
    factors = risk_service._calculate_progress_factors(test_project)
    
    # 进度应该低于预期，有负偏差
    assert factors["schedule_variance"] < 0


def test_calculate_progress_factors_no_planned_end_date(db_session, risk_service, test_project):
    """测试无计划结束日期时的进度因子"""
    test_project.planned_end_date = None
    db_session.commit()
    
    factors = risk_service._calculate_progress_factors(test_project)
    
    assert factors["schedule_variance"] == 0


# ==================== 测试风险评估 ====================


def test_calculate_risk_level_low(risk_service):
    """测试低风险等级判定"""
    factors = {
        "overdue_milestone_ratio": 0.05,
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "schedule_variance": -5,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "LOW"


def test_calculate_risk_level_medium_by_milestone(risk_service):
    """测试中等风险 - 里程碑逾期>=10%"""
    factors = {
        "overdue_milestone_ratio": 0.15,
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "MEDIUM"


def test_calculate_risk_level_medium_by_high_risk(risk_service):
    """测试中等风险 - 1个高风险"""
    factors = {
        "overdue_milestone_ratio": 0.0,
        "critical_risks_count": 0,
        "high_risks_count": 1,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "MEDIUM"


def test_calculate_risk_level_medium_by_schedule_variance(risk_service):
    """测试中等风险 - 进度偏差<-10%"""
    factors = {
        "overdue_milestone_ratio": 0.0,
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "schedule_variance": -15,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "MEDIUM"


def test_calculate_risk_level_high_by_milestone(risk_service):
    """测试高风险 - 里程碑逾期>=30%"""
    factors = {
        "overdue_milestone_ratio": 0.35,
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "HIGH"


def test_calculate_risk_level_high_by_multiple_high_risks(risk_service):
    """测试高风险 - 2个及以上高风险"""
    factors = {
        "overdue_milestone_ratio": 0.0,
        "critical_risks_count": 0,
        "high_risks_count": 2,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "HIGH"


def test_calculate_risk_level_high_by_schedule_variance(risk_service):
    """测试高风险 - 进度偏差<-20%"""
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
    """测试严重风险 - 有严重级别风险"""
    factors = {
        "overdue_milestone_ratio": 0.0,
        "critical_risks_count": 1,
        "high_risks_count": 0,
        "schedule_variance": 0,
    }
    
    level = risk_service._calculate_risk_level(factors)
    assert level == "CRITICAL"


# ==================== 测试风险计算集成 ====================


def test_calculate_project_risk_success(risk_service, test_project, test_milestones, test_pmo_risks):
    """测试完整的项目风险计算"""
    result = risk_service.calculate_project_risk(test_project.id)
    
    assert result["project_id"] == test_project.id
    assert result["project_code"] == test_project.project_code
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "risk_factors" in result
    
    factors = result["risk_factors"]
    assert factors["total_milestones_count"] == 4
    assert factors["overdue_milestones_count"] == 2
    assert factors["open_risks_count"] == 3
    assert "calculated_at" in factors


def test_calculate_project_risk_project_not_exist(risk_service):
    """测试计算不存在的项目风险"""
    with pytest.raises(ValueError, match="项目不存在"):
        risk_service.calculate_project_risk(99999)


def test_calculate_project_risk_no_data(risk_service, test_project):
    """测试无数据时的风险计算"""
    result = risk_service.calculate_project_risk(test_project.id)
    
    assert result["risk_level"] == "LOW"
    assert result["risk_factors"]["total_milestones_count"] == 0
    assert result["risk_factors"]["open_risks_count"] == 0


# ==================== 测试风险升级检测 ====================


def test_is_risk_upgrade_true(risk_service):
    """测试风险升级判定 - 升级情况"""
    assert risk_service._is_risk_upgrade("LOW", "MEDIUM") is True
    assert risk_service._is_risk_upgrade("MEDIUM", "HIGH") is True
    assert risk_service._is_risk_upgrade("HIGH", "CRITICAL") is True
    assert risk_service._is_risk_upgrade("LOW", "CRITICAL") is True


def test_is_risk_upgrade_false(risk_service):
    """测试风险升级判定 - 非升级情况"""
    assert risk_service._is_risk_upgrade("MEDIUM", "LOW") is False
    assert risk_service._is_risk_upgrade("HIGH", "MEDIUM") is False
    assert risk_service._is_risk_upgrade("CRITICAL", "HIGH") is False
    assert risk_service._is_risk_upgrade("MEDIUM", "MEDIUM") is False


def test_is_risk_upgrade_unknown_level(risk_service):
    """测试未知风险等级的处理"""
    assert risk_service._is_risk_upgrade("UNKNOWN", "LOW") is False
    assert risk_service._is_risk_upgrade("LOW", "UNKNOWN") is False


# ==================== 测试自动升级 ====================


@patch("app.services.project.project_risk_service.ProjectRiskService._send_risk_upgrade_notification")
def test_auto_upgrade_risk_level_first_time(mock_notify, risk_service, test_project):
    """测试首次风险评估（无历史记录）"""
    result = risk_service.auto_upgrade_risk_level(test_project.id)
    
    assert result["project_id"] == test_project.id
    assert result["old_risk_level"] == "LOW"  # 默认值
    assert result["new_risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "risk_factors" in result


@patch("app.services.project.project_risk_service.ProjectRiskService._send_risk_upgrade_notification")
def test_auto_upgrade_risk_level_with_upgrade(mock_notify, db_session, risk_service, test_project, test_milestones, test_pmo_risks):
    """测试风险升级场景"""
    # 创建初始历史记录（LOW等级）
    initial_history = ProjectRiskHistory(
        project_id=test_project.id,
        old_risk_level="LOW",
        new_risk_level="LOW",
        risk_factors={},
        triggered_by="INIT",
        triggered_at=datetime.now() - timedelta(days=1),
    )
    db_session.add(initial_history)
    db_session.commit()
    
    # 执行风险评估（由于有逾期里程碑和PMO风险，应该升级）
    result = risk_service.auto_upgrade_risk_level(test_project.id)
    
    assert result["old_risk_level"] == "LOW"
    assert result["new_risk_level"] in ["MEDIUM", "HIGH", "CRITICAL"]
    assert result["is_upgrade"] is True
    
    # 验证通知被调用
    mock_notify.assert_called_once()


@patch("app.services.project.project_risk_service.ProjectRiskService._send_risk_upgrade_notification")
def test_auto_upgrade_risk_level_no_change(mock_notify, db_session, risk_service, test_project):
    """测试风险等级无变化"""
    # 创建历史记录
    history = ProjectRiskHistory(
        project_id=test_project.id,
        old_risk_level="LOW",
        new_risk_level="LOW",
        risk_factors={},
        triggered_by="SYSTEM",
        triggered_at=datetime.now() - timedelta(hours=1),
    )
    db_session.add(history)
    db_session.commit()
    
    result = risk_service.auto_upgrade_risk_level(test_project.id)
    
    assert result["old_risk_level"] == "LOW"
    assert result["new_risk_level"] == "LOW"
    assert result["is_upgrade"] is False
    
    # 无升级时不发送通知
    mock_notify.assert_not_called()


@patch("app.services.project.project_risk_service.ProjectRiskService._send_risk_upgrade_notification")
def test_auto_upgrade_risk_level_custom_trigger(mock_notify, risk_service, test_project):
    """测试自定义触发者"""
    result = risk_service.auto_upgrade_risk_level(test_project.id, triggered_by="USER:admin")
    
    # 验证历史记录
    history = (
        risk_service.db.query(ProjectRiskHistory)
        .filter(ProjectRiskHistory.project_id == test_project.id)
        .order_by(ProjectRiskHistory.triggered_at.desc())
        .first()
    )
    
    assert history is not None
    assert history.triggered_by == "USER:admin"


# ==================== 测试批量计算 ====================


@patch("app.services.project.project_risk_service.ProjectRiskService._send_risk_upgrade_notification")
def test_batch_calculate_risks_all_projects(mock_notify, db_session, risk_service, test_customer):
    """测试批量计算所有项目风险"""
    # 创建多个项目
    projects = []
    for i in range(3):
        project = Project(
            project_code=f"PJ-BATCH-{i+1:03d}",
            project_name=f"批量测试项目{i+1}",
            customer_id=test_customer.id,
            customer_name=test_customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
        )
        db_session.add(project)
        projects.append(project)
    db_session.commit()
    
    results = risk_service.batch_calculate_risks()
    
    assert len(results) >= 3  # 至少包含创建的3个项目
    assert all("project_id" in r for r in results)


@patch("app.services.project.project_risk_service.ProjectRiskService._send_risk_upgrade_notification")
def test_batch_calculate_risks_specific_projects(mock_notify, db_session, risk_service, test_project):
    """测试批量计算指定项目风险"""
    results = risk_service.batch_calculate_risks(project_ids=[test_project.id])
    
    assert len(results) == 1
    assert results[0]["project_id"] == test_project.id


@patch("app.services.project.project_risk_service.ProjectRiskService._send_risk_upgrade_notification")
def test_batch_calculate_risks_inactive_projects(mock_notify, db_session, risk_service, test_project):
    """测试批量计算时排除非激活项目"""
    test_project.is_active = False
    db_session.commit()
    
    results = risk_service.batch_calculate_risks(active_only=True)
    
    # 不应包含非激活项目
    project_ids = [r["project_id"] for r in results]
    assert test_project.id not in project_ids


@patch("app.services.project.project_risk_service.ProjectRiskService._send_risk_upgrade_notification")
def test_batch_calculate_risks_with_errors(mock_notify, db_session, risk_service, test_project, caplog):
    """测试批量计算时的错误处理"""
    # 删除项目但保留ID
    project_id = test_project.id
    db_session.delete(test_project)
    db_session.commit()
    
    with caplog.at_level(logging.ERROR):
        results = risk_service.batch_calculate_risks(project_ids=[project_id])
    
    # 应该记录错误但不抛出异常
    assert len(results) == 1
    assert "error" in results[0]


# ==================== 测试风险快照 ====================


def test_create_risk_snapshot_success(risk_service, test_project, test_milestones):
    """测试创建风险快照"""
    snapshot = risk_service.create_risk_snapshot(test_project.id)
    
    assert snapshot.project_id == test_project.id
    assert snapshot.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert snapshot.total_milestones_count == 4
    assert snapshot.overdue_milestones_count == 2
    assert snapshot.snapshot_date is not None
    assert snapshot.risk_factors is not None


def test_create_risk_snapshot_multiple(db_session, risk_service, test_project):
    """测试创建多个快照"""
    snapshot1 = risk_service.create_risk_snapshot(test_project.id)
    snapshot2 = risk_service.create_risk_snapshot(test_project.id)
    
    # 两个快照应该都被保存
    count = db_session.query(ProjectRiskSnapshot).filter(
        ProjectRiskSnapshot.project_id == test_project.id
    ).count()
    
    assert count == 2


# ==================== 测试历史查询 ====================


def test_get_risk_history_empty(risk_service, test_project):
    """测试获取空的风险历史"""
    history = risk_service.get_risk_history(test_project.id)
    
    assert len(history) == 0


def test_get_risk_history_with_records(db_session, risk_service, test_project):
    """测试获取风险历史记录"""
    # 创建历史记录
    for i in range(3):
        record = ProjectRiskHistory(
            project_id=test_project.id,
            old_risk_level="LOW",
            new_risk_level="MEDIUM" if i % 2 == 0 else "LOW",
            risk_factors={},
            triggered_by="SYSTEM",
            triggered_at=datetime.now() - timedelta(hours=i),
        )
        db_session.add(record)
    db_session.commit()
    
    history = risk_service.get_risk_history(test_project.id)
    
    assert len(history) == 3
    # 应该按时间倒序排列
    assert history[0].triggered_at > history[1].triggered_at


def test_get_risk_history_with_limit(db_session, risk_service, test_project):
    """测试历史记录数量限制"""
    # 创建5条历史记录
    for i in range(5):
        record = ProjectRiskHistory(
            project_id=test_project.id,
            old_risk_level="LOW",
            new_risk_level="MEDIUM",
            risk_factors={},
            triggered_by="SYSTEM",
            triggered_at=datetime.now() - timedelta(hours=i),
        )
        db_session.add(record)
    db_session.commit()
    
    history = risk_service.get_risk_history(test_project.id, limit=3)
    
    assert len(history) == 3


# ==================== 测试趋势分析 ====================


def test_get_risk_trend_empty(risk_service, test_project):
    """测试获取空的风险趋势"""
    trend = risk_service.get_risk_trend(test_project.id, days=30)
    
    assert len(trend) == 0


def test_get_risk_trend_with_snapshots(db_session, risk_service, test_project):
    """测试获取风险趋势数据"""
    # 创建快照
    for i in range(5):
        snapshot = ProjectRiskSnapshot(
            project_id=test_project.id,
            snapshot_date=datetime.now() - timedelta(days=i),
            risk_level="MEDIUM",
            overdue_milestones_count=i,
            total_milestones_count=10,
            overdue_tasks_count=0,
            open_risks_count=i * 2,
            high_risks_count=i,
            risk_factors={},
        )
        db_session.add(snapshot)
    db_session.commit()
    
    trend = risk_service.get_risk_trend(test_project.id, days=7)
    
    assert len(trend) == 5
    assert all("date" in t for t in trend)
    assert all("risk_level" in t for t in trend)
    assert all("overdue_milestones" in t for t in trend)


def test_get_risk_trend_time_range(db_session, risk_service, test_project):
    """测试趋势数据的时间范围过滤"""
    # 创建不同时间的快照
    recent_snapshot = ProjectRiskSnapshot(
        project_id=test_project.id,
        snapshot_date=datetime.now() - timedelta(days=5),
        risk_level="MEDIUM",
        overdue_milestones_count=1,
        total_milestones_count=10,
        overdue_tasks_count=0,
        open_risks_count=2,
        high_risks_count=1,
        risk_factors={},
    )
    
    old_snapshot = ProjectRiskSnapshot(
        project_id=test_project.id,
        snapshot_date=datetime.now() - timedelta(days=40),
        risk_level="LOW",
        overdue_milestones_count=0,
        total_milestones_count=10,
        overdue_tasks_count=0,
        open_risks_count=0,
        high_risks_count=0,
        risk_factors={},
    )
    
    db_session.add_all([recent_snapshot, old_snapshot])
    db_session.commit()
    
    # 只查询最近7天
    trend = risk_service.get_risk_trend(test_project.id, days=7)
    
    assert len(trend) == 1  # 只包含5天前的快照


# ==================== 测试通知机制 ====================


@patch("app.utils.scheduled_tasks.base.send_notification_for_alert")
def test_send_risk_upgrade_notification_success(mock_send, db_session, risk_service, test_project):
    """测试风险升级通知发送"""
    risk_service._send_risk_upgrade_notification(
        project_id=test_project.id,
        project_code=test_project.project_code,
        project_name=test_project.project_name,
        old_level="LOW",
        new_level="CRITICAL",
        risk_factors={
            "overdue_milestones_count": 3,
            "high_risks_count": 2,
            "schedule_variance": -15,
        },
    )
    
    # 验证预警记录被创建
    alert = db_session.query(AlertRecord).filter(
        AlertRecord.project_id == test_project.id
    ).first()
    
    assert alert is not None
    assert "RISK" in alert.alert_no
    assert "风险升级" in alert.alert_title
    assert test_project.project_name in alert.alert_title
    assert "LOW" in alert.alert_content
    assert "CRITICAL" in alert.alert_content
    
    # 验证通知函数被调用
    mock_send.assert_called_once()


@patch("app.utils.scheduled_tasks.base.send_notification_for_alert")
def test_send_risk_upgrade_notification_with_factors(mock_send, db_session, risk_service, test_project):
    """测试通知内容包含风险因子"""
    risk_factors = {
        "overdue_milestones_count": 5,
        "high_risks_count": 3,
        "schedule_variance": -25.5,
    }
    
    risk_service._send_risk_upgrade_notification(
        project_id=test_project.id,
        project_code=test_project.project_code,
        project_name=test_project.project_name,
        old_level="MEDIUM",
        new_level="HIGH",
        risk_factors=risk_factors,
    )
    
    alert = db_session.query(AlertRecord).filter(
        AlertRecord.project_id == test_project.id
    ).first()
    
    assert "逾期里程碑: 5个" in alert.alert_content
    assert "高风险项: 3个" in alert.alert_content
    assert "进度偏差: -25.5%" in alert.alert_content


@patch("app.utils.scheduled_tasks.base.send_notification_for_alert", side_effect=Exception("通知失败"))
def test_send_risk_upgrade_notification_error_handling(mock_send, db_session, risk_service, test_project, caplog):
    """测试通知发送失败时的错误处理"""
    with caplog.at_level(logging.ERROR):
        # 应该不抛出异常
        risk_service._send_risk_upgrade_notification(
            project_id=test_project.id,
            project_code=test_project.project_code,
            project_name=test_project.project_name,
            old_level="LOW",
            new_level="HIGH",
            risk_factors={},
        )
    
    # 验证错误被记录
    assert "创建风险升级预警失败" in caplog.text


# ==================== 综合场景测试 ====================


@patch("app.services.project.project_risk_service.ProjectRiskService._send_risk_upgrade_notification")
def test_complete_risk_workflow(mock_notify, db_session, risk_service, test_project):
    """测试完整的风险工作流"""
    # 1. 首次评估
    result1 = risk_service.auto_upgrade_risk_level(test_project.id)
    assert result1["old_risk_level"] == "LOW"
    
    # 2. 创建快照
    snapshot1 = risk_service.create_risk_snapshot(test_project.id)
    assert snapshot1.risk_level == result1["new_risk_level"]
    
    # 3. 添加逾期里程碑
    milestone = ProjectMilestone(
        project_id=test_project.id,
        milestone_name="逾期里程碑",
        planned_date=date.today() - timedelta(days=10),
        status="IN_PROGRESS",
    )
    db_session.add(milestone)
    db_session.commit()
    
    # 4. 再次评估（应该升级）
    result2 = risk_service.auto_upgrade_risk_level(test_project.id)
    
    # 5. 查询历史
    history = risk_service.get_risk_history(test_project.id)
    assert len(history) == 2
    
    # 6. 创建第二个快照
    snapshot2 = risk_service.create_risk_snapshot(test_project.id)
    
    # 7. 查询趋势
    trend = risk_service.get_risk_trend(test_project.id, days=1)
    assert len(trend) == 2


@patch("app.services.project.project_risk_service.ProjectRiskService._send_risk_upgrade_notification")
def test_edge_case_missing_dates(mock_notify, db_session, risk_service, test_customer):
    """测试缺少日期字段的边缘情况"""
    # 创建缺少日期的项目
    project = Project(
        project_code="PJ-NO-DATES",
        project_name="无日期项目",
        customer_id=test_customer.id,
        customer_name=test_customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        is_active=True,
        # 不设置任何日期字段
    )
    db_session.add(project)
    db_session.commit()
    
    # 应该能正常计算，不抛出异常
    result = risk_service.calculate_project_risk(project.id)
    assert result["risk_level"] == "LOW"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
