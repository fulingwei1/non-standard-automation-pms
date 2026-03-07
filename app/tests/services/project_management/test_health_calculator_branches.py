# -*- coding: utf-8 -*-
"""
项目健康度计算服务分支测试
测试 app/services/health_calculator.py 的各种分支逻辑

覆盖目标:
- H1正常状态判定分支
- H2有风险状态判定分支
- H3阻塞状态判定分支
- H4已完结状态判定分支
- 各种健康度影响因素分支（进度、成本、质量、里程碑等）
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertLevelEnum, IssueStatusEnum, ProjectHealthEnum
from app.models.issue import Issue, IssueTypeEnum
from app.models.progress import Task
from app.models.project import Project, ProjectMilestone
from app.services.health_calculator import HealthCalculator


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ260307001",
        project_name="测试项目",
        stage="S4",
        status="ST07",
        health="H1",
        progress_pct=Decimal("50.0"),
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        is_active=True,
        is_archived=False,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def calculator(db_session: Session):
    """创建健康度计算器"""
    return HealthCalculator(db_session)


class TestHealthH4ClosedBranches:
    """测试H4已完结状态的分支逻辑"""

    def test_h4_status_st30(self, db_session, calculator, test_project):
        """分支：状态为ST30(已结项) - H4"""
        test_project.status = "ST30"
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H4.value

    def test_h4_status_st99(self, db_session, calculator, test_project):
        """分支：状态为ST99(项目取消) - H4"""
        test_project.status = "ST99"
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H4.value


class TestHealthH3BlockedBranches:
    """测试H3阻塞状态的分支逻辑"""

    def test_h3_blocked_status_st14(self, db_session, calculator, test_project):
        """分支：状态为ST14(缺料阻塞) - H3"""
        test_project.status = "ST14"
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H3.value

    def test_h3_blocked_status_st19(self, db_session, calculator, test_project):
        """分支：状态为ST19(技术阻塞) - H3"""
        test_project.status = "ST19"
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H3.value

    def test_h3_blocked_critical_tasks(self, db_session, calculator, test_project):
        """分支：有关键任务阻塞 - H3"""
        # 创建阻塞任务
        task = Task(
            project_id=test_project.id,
            task_name="阻塞任务",
            status="BLOCKED",
        )
        db_session.add(task)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H3.value

    def test_h3_blocking_issues(self, db_session, calculator, test_project):
        """分支：有严重阻塞问题 - H3"""
        from datetime import datetime
        # 创建阻塞类型问题
        issue = Issue(
            project_id=test_project.id,
            title="阻塞问题",
            description="严重阻塞问题描述",
            issue_type=IssueTypeEnum.BLOCKER,
            status=IssueStatusEnum.OPEN,
            priority="CRITICAL",
            reporter_id=1,
            report_date=datetime.now(),
        )
        db_session.add(issue)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H3.value

    def test_h3_critical_shortage_alerts(self, db_session, calculator, test_project):
        """分支：有严重缺料预警 - H3"""
        # 创建预警规则
        rule = AlertRule(
            rule_name="缺料预警",
            rule_type="MATERIAL_SHORTAGE",
            condition="缺料",
        )
        db_session.add(rule)
        db_session.commit()

        # 创建严重预警
        alert = AlertRecord(
            project_id=test_project.id,
            rule_id=rule.id,
            alert_level=AlertLevelEnum.CRITICAL,
            status="PENDING",
            title="严重缺料",
        )
        db_session.add(alert)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H3.value


class TestHealthH2RiskBranches:
    """测试H2有风险状态的分支逻辑"""

    def test_h2_rectification_status_st22(self, db_session, calculator, test_project):
        """分支：状态为ST22(FAT整改中) - H2"""
        test_project.status = "ST22"
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H2.value

    def test_h2_rectification_status_st26(self, db_session, calculator, test_project):
        """分支：状态为ST26(SAT整改中) - H2"""
        test_project.status = "ST26"
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H2.value

    def test_h2_deadline_approaching(self, db_session, calculator, test_project):
        """分支：交期临近（7天内） - H2"""
        test_project.planned_end_date = date.today() + timedelta(days=5)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H2.value

    def test_h2_overdue_milestones(self, db_session, calculator, test_project):
        """分支：有逾期里程碑 - H2"""
        # 创建逾期的关键里程碑
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="逾期里程碑",
            planned_date=date.today() - timedelta(days=5),
            status="IN_PROGRESS",
            is_key=True,
        )
        db_session.add(milestone)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H2.value

    def test_h2_shortage_warnings(self, db_session, calculator, test_project):
        """分支：有缺料预警（非严重） - H2"""
        # 创建预警规则
        rule = AlertRule(
            rule_name="缺料预警",
            rule_type="MATERIAL_SHORTAGE",
            condition="缺料",
        )
        db_session.add(rule)
        db_session.commit()

        # 创建警告级别预警
        alert = AlertRecord(
            project_id=test_project.id,
            rule_id=rule.id,
            alert_level=AlertLevelEnum.WARNING,
            status="PENDING",
            title="缺料警告",
        )
        db_session.add(alert)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H2.value

    def test_h2_high_priority_issues(self, db_session, calculator, test_project):
        """分支：有高优先级未解决问题 - H2"""
        from datetime import datetime
        issue = Issue(
            project_id=test_project.id,
            title="高优先级问题",
            description="高优先级问题描述",
            issue_type=IssueTypeEnum.TASK,
            status=IssueStatusEnum.OPEN,
            priority="HIGH",
            reporter_id=1,
            report_date=datetime.now(),
        )
        db_session.add(issue)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H2.value

    def test_h2_schedule_variance(self, db_session, calculator, test_project):
        """分支：进度偏差超过阈值 - H2"""
        # 设置进度严重滞后（计划进度50%，实际30%）
        test_project.progress_pct = Decimal("30.0")
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H2.value


class TestHealthH1NormalBranches:
    """测试H1正常状态的分支逻辑"""

    def test_h1_normal_project(self, db_session, calculator, test_project):
        """分支：正常项目 - H1"""
        # 确保项目处于正常状态（无任何问题）
        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H1.value

    def test_h1_non_key_milestone_overdue(self, db_session, calculator, test_project):
        """分支：非关键里程碑逾期 - 仍为H1"""
        # 创建逾期的非关键里程碑（不影响健康度）
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="非关键里程碑",
            planned_date=date.today() - timedelta(days=5),
            status="IN_PROGRESS",
            is_key=False,  # 非关键
        )
        db_session.add(milestone)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H1.value


class TestHealthDetailsBranches:
    """测试健康度详细信息的分支逻辑"""

    def test_get_health_details(self, db_session, calculator, test_project):
        """分支：获取健康度详细诊断信息"""
        details = calculator.get_health_details(test_project)

        assert details["project_id"] == test_project.id
        assert details["project_code"] == test_project.project_code
        assert details["current_health"] == test_project.health
        assert details["calculated_health"] in ["H1", "H2", "H3", "H4"]
        assert "checks" in details
        assert "statistics" in details

    def test_get_health_details_with_issues(self, db_session, calculator, test_project):
        """分支：包含问题统计的详细信息"""
        from datetime import datetime
        # 创建各种问题
        issue = Issue(
            project_id=test_project.id,
            title="测试问题",
            description="测试问题描述",
            issue_type=IssueTypeEnum.BLOCKER,
            status=IssueStatusEnum.OPEN,
            priority="HIGH",
            reporter_id=1,
            report_date=datetime.now(),
        )
        db_session.add(issue)
        db_session.commit()

        details = calculator.get_health_details(test_project)

        assert details["statistics"]["blocking_issues"] >= 1
        assert details["checks"]["has_blocking_issues"] is True


class TestHealthCalculateAndUpdateBranches:
    """测试健康度计算并更新的分支逻辑"""

    def test_calculate_and_update_changed(self, db_session, calculator, test_project):
        """分支：健康度变化 - 更新项目"""
        test_project.health = "H1"
        test_project.status = "ST14"  # 设置为阻塞状态
        db_session.commit()

        result = calculator.calculate_and_update(test_project, auto_save=True)

        assert result["changed"] is True
        assert result["old_health"] == "H1"
        assert result["new_health"] == "H3"

        # 验证项目已更新
        db_session.refresh(test_project)
        assert test_project.health == "H3"

    def test_calculate_and_update_unchanged(self, db_session, calculator, test_project):
        """分支：健康度未变化 - 不更新"""
        test_project.health = "H1"
        db_session.commit()

        result = calculator.calculate_and_update(test_project, auto_save=True)

        assert result["changed"] is False
        assert result["old_health"] == "H1"
        assert result["new_health"] == "H1"

    def test_calculate_and_update_no_save(self, db_session, calculator, test_project):
        """分支：不自动保存"""
        test_project.health = "H1"
        test_project.status = "ST14"
        db_session.commit()

        result = calculator.calculate_and_update(test_project, auto_save=False)

        assert result["changed"] is True
        # 项目应该未更新
        db_session.refresh(test_project)
        assert test_project.health == "H1"  # 仍为旧值


class TestBatchCalculateBranches:
    """测试批量计算的分支逻辑"""

    def test_batch_calculate_all_projects(self, db_session, calculator):
        """分支：批量计算所有活跃项目"""
        # 创建多个项目
        projects = [
            Project(
                project_code=f"PJ26030700{i}",
                project_name=f"测试项目{i}",
                stage="S4",
                status="ST07" if i % 2 == 0 else "ST14",  # 一半正常，一半阻塞
                health="H1",
                is_active=True,
                is_archived=False,
            )
            for i in range(1, 6)
        ]
        db_session.add_all(projects)
        db_session.commit()

        result = calculator.batch_calculate(project_ids=None, batch_size=2)

        assert result["total"] >= 5
        assert result["updated"] >= 2  # 至少有阻塞项目被更新
        assert len(result["details"]) >= 5

    def test_batch_calculate_specific_projects(self, db_session, calculator):
        """分支：批量计算指定项目"""
        # 创建项目
        projects = [
            Project(
                project_code=f"PJ26030701{i}",
                project_name=f"指定项目{i}",
                stage="S4",
                status="ST07",
                health="H1",
                is_active=True,
                is_archived=False,
            )
            for i in range(1, 4)
        ]
        db_session.add_all(projects)
        db_session.commit()

        project_ids = [p.id for p in projects[:2]]  # 只计算前2个
        result = calculator.batch_calculate(project_ids=project_ids)

        assert result["total"] == 2

    def test_batch_calculate_with_batching(self, db_session, calculator):
        """分支：分批处理（性能优化）"""
        # 创建多个项目测试分批
        projects = [
            Project(
                project_code=f"PJ26030702{i}",
                project_name=f"批处理项目{i}",
                stage="S4",
                status="ST07",
                health="H1",
                is_active=True,
                is_archived=False,
            )
            for i in range(1, 11)  # 10个项目
        ]
        db_session.add_all(projects)
        db_session.commit()

        # 使用小批次大小测试
        result = calculator.batch_calculate(project_ids=None, batch_size=3)

        assert result["total"] >= 10


class TestHealthFactorsBranches:
    """测试各种健康度影响因素的分支逻辑"""

    def test_deadline_approaching_boundary(self, db_session, calculator, test_project):
        """分支：交期临近边界测试"""
        # 7天边界
        test_project.planned_end_date = date.today() + timedelta(days=7)
        db_session.commit()
        assert calculator._is_deadline_approaching(test_project, days=7) is True

        # 8天不触发
        test_project.planned_end_date = date.today() + timedelta(days=8)
        db_session.commit()
        assert calculator._is_deadline_approaching(test_project, days=7) is False

    def test_deadline_no_planned_end(self, db_session, calculator, test_project):
        """分支：无计划结束日期 - 不触发"""
        test_project.planned_end_date = None
        db_session.commit()

        assert calculator._is_deadline_approaching(test_project) is False

    def test_schedule_variance_calculation(self, db_session, calculator, test_project):
        """分支：进度偏差计算"""
        # 项目进行到一半时间，但进度只有20%（偏差30%）
        test_project.planned_start_date = date.today() - timedelta(days=30)
        test_project.planned_end_date = date.today() + timedelta(days=30)
        test_project.progress_pct = Decimal("20.0")
        db_session.commit()

        assert calculator._has_schedule_variance(test_project, threshold=10) is True

    def test_schedule_variance_no_dates(self, db_session, calculator, test_project):
        """分支：无计划日期 - 不计算偏差"""
        test_project.planned_start_date = None
        test_project.planned_end_date = None
        db_session.commit()

        assert calculator._has_schedule_variance(test_project) is False

    def test_milestone_not_key(self, db_session, calculator, test_project):
        """分支：非关键里程碑逾期 - 不触发"""
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="非关键逾期",
            planned_date=date.today() - timedelta(days=5),
            status="IN_PROGRESS",
            is_key=False,
        )
        db_session.add(milestone)
        db_session.commit()

        assert calculator._has_overdue_milestones(test_project) is False

    def test_milestone_completed(self, db_session, calculator, test_project):
        """分支：里程碑已完成 - 不触发"""
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="已完成里程碑",
            planned_date=date.today() - timedelta(days=5),
            status="COMPLETED",
            is_key=True,
        )
        db_session.add(milestone)
        db_session.commit()

        assert calculator._has_overdue_milestones(test_project) is False


class TestCalculateProjectHealthBranches:
    """测试项目健康度计算（不落库）的分支逻辑"""

    def test_calculate_project_health_not_found(self, db_session, calculator):
        """分支：项目不存在 - 抛出异常"""
        with pytest.raises(ValueError, match="not found"):
            calculator.calculate_project_health(99999)

    def test_calculate_project_health_with_factors(self, db_session, calculator, test_project):
        """分支：包含影响因素的计算"""
        # 添加一些风险因素
        issue = Issue(
            project_id=test_project.id,
            title="高优先级问题",
            issue_type=IssueTypeEnum.TASK,
            status=IssueStatusEnum.OPEN,
            priority="HIGH",
        )
        db_session.add(issue)
        db_session.commit()

        result = calculator.calculate_project_health(test_project.id)

        assert result["project_id"] == test_project.id
        assert "factors" in result
        assert "reason_codes" in result
        assert len(result["reason_codes"]) > 0  # 应该有触发的原因

    def test_calculate_project_health_no_change(self, db_session, calculator, test_project):
        """分支：健康度未变化"""
        result = calculator.calculate_project_health(test_project.id)

        assert result["changed"] is False
        assert result["old_health"] == result["new_health"]
