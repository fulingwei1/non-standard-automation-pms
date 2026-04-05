# -*- coding: utf-8 -*-
"""
项目风险服务分支测试

覆盖服务：
- ProjectRiskService - 项目风险计算与升级
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.pmo import PmoProjectRisk
from app.models.project import Project, ProjectMilestone
from app.models.project.risk_history import ProjectRiskHistory, ProjectRiskSnapshot
from app.services.project.project_risk_service import ProjectRiskService


class TestProjectRiskService:
    """项目风险服务测试"""

    @pytest.fixture
    def risk_service(self, db_session):
        """创建风险服务实例"""
        return ProjectRiskService(db_session)

    def test_calculate_project_risk_basic(self, db_session, risk_service, test_project):
        """分支：基础风险计算 - 正常项目"""
        result = risk_service.calculate_project_risk(test_project.id)

        assert result["project_id"] == test_project.id
        assert result["project_code"] == test_project.project_code
        assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert "risk_factors" in result

    def test_calculate_project_risk_not_found(self, risk_service):
        """分支：项目不存在"""
        with pytest.raises(ValueError, match="项目不存在"):
            risk_service.calculate_project_risk(99999)

    def test_calculate_risk_with_overdue_milestones(
        self, db_session, risk_service, test_project
    ):
        """分支：存在逾期里程碑 - 触发CRITICAL风险（100%逾期）"""
        # 创建已过期的里程碑
        overdue_milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="逾期里程碑",
            planned_date=date.today() - timedelta(days=30),
            status="NOT_STARTED",
        )
        db_session.add(overdue_milestone)
        db_session.commit()

        result = risk_service.calculate_project_risk(test_project.id)

        # 逾期里程碑比例 1/1 = 100% >= 50% -> CRITICAL
        assert result["risk_level"] == "CRITICAL"
        assert result["risk_factors"]["overdue_milestones_count"] == 1
        assert result["risk_factors"]["overdue_milestone_ratio"] == 1.0

    def test_calculate_risk_with_high_pmo_risks(
        self, db_session, risk_service, test_project
    ):
        """分支：存在多个HIGH级别PMO风险 - 触发HIGH风险"""
        # 清除里程碑
        db_session.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == test_project.id
        ).delete()
        
        # 创建HIGH级别风险
        high_risk = PmoProjectRisk(
            project_id=test_project.id,
            risk_no="RISK001",
            risk_name="高风险项",
            risk_level="HIGH",
            status="OPEN",
            risk_category="TECHNICAL",
        )
        high_risk2 = PmoProjectRisk(
            project_id=test_project.id,
            risk_no="RISK002",
            risk_name="高风险项2",
            risk_level="HIGH",
            status="OPEN",
            risk_category="TECHNICAL",
        )
        db_session.add_all([high_risk, high_risk2])
        db_session.commit()

        result = risk_service.calculate_project_risk(test_project.id)

        # HIGH风险数量>=2 -> HIGH
        assert result["risk_level"] == "HIGH"
        assert result["risk_factors"]["high_risks_count"] == 2

    def test_calculate_risk_with_critical_pmo_risk(
        self, db_session, risk_service, test_project
    ):
        """分支：存在CRITICAL级别PMO风险 - 触发CRITICAL风险"""
        # 清除里程碑
        db_session.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == test_project.id
        ).delete()
        
        critical_risk = PmoProjectRisk(
            project_id=test_project.id,
            risk_no="RISK003",
            risk_name="严重风险",
            risk_level="CRITICAL",
            status="OPEN",
            risk_category="TECHNICAL",
        )
        db_session.add(critical_risk)
        db_session.commit()

        result = risk_service.calculate_project_risk(test_project.id)

        # 有CRITICAL风险 -> CRITICAL
        assert result["risk_level"] == "CRITICAL"
        assert result["risk_factors"]["critical_risks_count"] == 1

    def test_calculate_risk_with_schedule_variance(
        self, db_session, risk_service, test_project
    ):
        """分支：进度偏差<-20% 触发HIGH风险（无里程碑和高风险时）"""
        # 清除里程碑，确保只测试进度偏差因素
        db_session.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == test_project.id
        ).delete()
        
        # 设置项目进度为0，已开始30天，计划60天
        test_project.progress_pct = Decimal("0")
        test_project.planned_start_date = date.today() - timedelta(days=30)
        test_project.planned_end_date = date.today() + timedelta(days=30)
        db_session.commit()

        result = risk_service.calculate_project_risk(test_project.id)

        # 进度偏差约 -50% < -20% -> HIGH
        assert result["risk_level"] == "HIGH"

    def test_auto_upgrade_risk_level_new(self, db_session, risk_service, test_project):
        """分支：首次计算风险 - 无历史记录"""
        result = risk_service.auto_upgrade_risk_level(test_project.id)

        assert result["old_risk_level"] == "LOW"  # 默认值
        assert "new_risk_level" in result
        assert "is_upgrade" in result

    def test_auto_upgrade_risk_level_upgrade(
        self, db_session, risk_service, test_project
    ):
        """分支：风险等级升级"""
        # 先创建一条历史记录
        history = ProjectRiskHistory(
            project_id=test_project.id,
            old_risk_level="LOW",
            new_risk_level="LOW",
            risk_factors={},
            triggered_by="TEST",
            triggered_at=datetime.now() - timedelta(days=1),
        )
        db_session.add(history)
        db_session.commit()

        # 添加逾期里程碑触发升级
        overdue_milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="逾期里程碑",
            planned_date=date.today() - timedelta(days=30),
            status="NOT_STARTED",
        )
        db_session.add(overdue_milestone)
        db_session.commit()

        result = risk_service.auto_upgrade_risk_level(test_project.id)

        # 应该记录了新的历史
        assert "risk_factors" in result

    def test_get_risk_history(self, db_session, risk_service, test_project):
        """分支：获取风险历史"""
        # 创建历史记录
        for i in range(3):
            history = ProjectRiskHistory(
                project_id=test_project.id,
                old_risk_level="LOW",
                new_risk_level="MEDIUM",
                risk_factors={},
                triggered_by="TEST",
                triggered_at=datetime.now() - timedelta(days=i),
            )
            db_session.add(history)
        db_session.commit()

        histories = risk_service.get_risk_history(test_project.id)

        assert len(histories) == 3

    def test_get_risk_history_with_limit(self, db_session, risk_service, test_project):
        """分支：限制返回数量"""
        # 创建5条历史记录
        for i in range(5):
            history = ProjectRiskHistory(
                project_id=test_project.id,
                old_risk_level="LOW",
                new_risk_level="MEDIUM",
                risk_factors={},
                triggered_by="TEST",
                triggered_at=datetime.now() - timedelta(days=i),
            )
            db_session.add(history)
        db_session.commit()

        histories = risk_service.get_risk_history(test_project.id, limit=2)

        assert len(histories) == 2

    def test_create_risk_snapshot(self, db_session, risk_service, test_project):
        """分支：创建风险快照"""
        snapshot = risk_service.create_risk_snapshot(test_project.id)

        assert snapshot.project_id == test_project.id
        assert snapshot.risk_level is not None
        assert snapshot.snapshot_date is not None

    def test_get_risk_trend(self, db_session, risk_service, test_project):
        """分支：获取风险趋势"""
        # 创建多条快照
        for i in range(3):
            snapshot = ProjectRiskSnapshot(
                project_id=test_project.id,
                snapshot_date=datetime.now() - timedelta(days=i * 10),
                risk_level="MEDIUM",
                overdue_milestones_count=1,
                total_milestones_count=5,
                overdue_tasks_count=0,
                open_risks_count=2,
                high_risks_count=1,
                risk_factors={},
            )
            db_session.add(snapshot)
        db_session.commit()

        trend = risk_service.get_risk_trend(test_project.id, days=30)

        assert len(trend) == 3

    def test_batch_calculate_risks_empty(self, db_session, risk_service):
        """分支：批量计算 - 无项目"""
        results = risk_service.batch_calculate_risks()

        assert len(results) == 0

    def test_batch_calculate_risks_with_projects(
        self, db_session, risk_service, test_project
    ):
        """分支：批量计算 - 有项目"""
        results = risk_service.batch_calculate_risks(active_only=False)

        assert len(results) >= 1