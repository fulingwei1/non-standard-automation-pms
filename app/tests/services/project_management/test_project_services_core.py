# -*- coding: utf-8 -*-
"""
项目管理服务核心分支测试（简化版）
专注于核心分支覆盖，确保测试能快速运行

覆盖服务：
- progress_service.py - 进度管理
- stage_advance_service.py - 阶段推进
- health_calculator.py - 健康度计算
- milestone_service.py - 里程碑管理
"""

import pytest
from datetime import date, timedelta

from app.models.enums import IssueStatusEnum, ProjectHealthEnum
from app.models.issue import Issue, IssueTypeEnum
from app.models.progress import Task
from app.models.project import Machine, Project, ProjectMilestone, ProjectStatusLog
from app.services.health_calculator import HealthCalculator
from app.services.milestone_service import MilestoneService
from app.services.stage_advance_service import (
    validate_target_stage,
    validate_stage_advancement,
    update_project_stage_and_status,
    create_status_log,
    create_installation_dispatch_orders,
)
from app.schemas.project import MilestoneCreate, MilestoneUpdate


# ========== 进度服务测试 ==========

class TestProgressServiceBranches:
    """进度服务核心分支测试"""

    def test_progress_summary_with_tasks(self, db_session, test_project):
        """分支：有任务的项目进度汇总"""
        from app.services.progress_service import get_project_progress_summary

        # 创建不同状态的任务（使用Task模型）
        tasks = [
            Task(
                project_id=test_project.id,
                task_name="已完成任务",
                status="DONE",
                progress_percent=100,
            ),
            Task(
                project_id=test_project.id,
                task_name="进行中任务",
                status="TODO",
                progress_percent=50,
            ),
        ]
        db_session.add_all(tasks)
        db_session.commit()

        summary = get_project_progress_summary(db_session, test_project.id)

        # 基本断言
        assert "project_id" in summary
        assert summary["project_id"] == test_project.id

    def test_progress_summary_empty(self, db_session, test_project):
        """分支：无任务的项目"""
        from app.services.progress_service import get_project_progress_summary

        summary = get_project_progress_summary(db_session, test_project.id)

        assert summary["total_tasks"] == 0


# ========== 阶段推进服务测试 ==========

class TestStageAdvanceServiceBranches:
    """阶段推进服务核心分支测试"""

    def test_validate_target_stage_valid(self):
        """分支：有效的目标阶段"""
        for stage in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']:
            validate_target_stage(stage)  # 不应抛出异常

    def test_validate_target_stage_invalid(self):
        """分支：无效的目标阶段"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            validate_target_stage("S10")
        assert exc.value.status_code == 400

    def test_validate_stage_advancement_forward(self):
        """分支：向前推进（正常）"""
        validate_stage_advancement("S3", "S4")

    def test_validate_stage_advancement_backward(self):
        """分支：向后回退（异常）"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            validate_stage_advancement("S5", "S3")

    def test_update_stage_s1_to_s2(self, db_session, test_project):
        """分支：S1→S2阶段流转"""
        test_project.stage = "S1"
        test_project.status = "ST01"
        db_session.commit()

        new_status = update_project_stage_and_status(
            db=db_session,
            project=test_project,
            target_stage="S2",
            old_stage="S1",
            old_status="ST01",
        )

        assert test_project.stage == "S2"
        assert new_status == "ST03"

    def test_create_status_log(self, db_session, test_project):
        """分支：创建状态日志"""
        create_status_log(
            db=db_session,
            project_id=test_project.id,
            old_stage="S3",
            new_stage="S4",
            old_status="ST05",
            new_status="ST07",
            old_health="H1",
            new_health="H2",
            reason="测试推进",
            changed_by=1,
        )

        log = db_session.query(ProjectStatusLog).filter(
            ProjectStatusLog.project_id == test_project.id
        ).first()

        assert log is not None
        assert log.new_stage == "S4"

    def test_create_installation_dispatch_s8(self, db_session, test_project):
        """分支：S8阶段自动创建派工单"""
        machine = Machine(
            project_id=test_project.id,
            machine_code="MC001",
            machine_no="PN001",
            machine_name="测试设备",
        )
        db_session.add(machine)
        db_session.commit()

        create_installation_dispatch_orders(
            db=db_session,
            project=test_project,
            target_stage="S8",
            old_stage="S7",
        )

        from app.models.installation_dispatch import InstallationDispatchOrder
        orders = db_session.query(InstallationDispatchOrder).filter(
            InstallationDispatchOrder.project_id == test_project.id
        ).all()

        assert len(orders) >= 1

    def test_no_dispatch_not_s8(self, db_session, test_project):
        """分支：非S8阶段不创建派工单"""
        create_installation_dispatch_orders(
            db=db_session,
            project=test_project,
            target_stage="S7",
            old_stage="S6",
        )

        from app.models.installation_dispatch import InstallationDispatchOrder
        orders = db_session.query(InstallationDispatchOrder).filter(
            InstallationDispatchOrder.project_id == test_project.id
        ).all()

        assert len(orders) == 0


# ========== 健康度计算服务测试 ==========

class TestHealthCalculatorBranches:
    """健康度计算服务核心分支测试"""

    def test_h4_status_st30(self, db_session, test_project):
        """分支：状态为ST30(已结项) - H4"""
        calculator = HealthCalculator(db_session)
        test_project.status = "ST30"
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H4.value

    def test_h3_blocked_status(self, db_session, test_project):
        """分支：阻塞状态 - H3"""
        calculator = HealthCalculator(db_session)
        test_project.status = "ST14"  # 缺料阻塞
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H3.value

    def test_h3_blocking_issues(self, db_session, test_project):
        """分支：有严重阻塞问题 - H3"""
        calculator = HealthCalculator(db_session)
        issue = Issue(
            project_id=test_project.id,
            title="阻塞问题",
            issue_type=IssueTypeEnum.BLOCKER,
            status=IssueStatusEnum.OPEN,
            priority="CRITICAL",
        )
        db_session.add(issue)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H3.value

    def test_h2_rectification_status(self, db_session, test_project):
        """分支：整改状态 - H2"""
        calculator = HealthCalculator(db_session)
        test_project.status = "ST22"  # FAT整改中
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H2.value

    def test_h2_deadline_approaching(self, db_session, test_project):
        """分支：交期临近 - H2"""
        calculator = HealthCalculator(db_session)
        test_project.planned_end_date = date.today() + timedelta(days=5)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H2.value

    def test_h2_overdue_milestones(self, db_session, test_project):
        """分支：逾期里程碑 - H2"""
        calculator = HealthCalculator(db_session)
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

    def test_h2_high_priority_issues(self, db_session, test_project):
        """分支：高优先级问题 - H2"""
        calculator = HealthCalculator(db_session)
        issue = Issue(
            project_id=test_project.id,
            title="高优先级问题",
            issue_type=IssueTypeEnum.TASK,
            status=IssueStatusEnum.OPEN,
            priority="HIGH",
        )
        db_session.add(issue)
        db_session.commit()

        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H2.value

    def test_h1_normal_project(self, db_session, test_project):
        """分支：正常项目 - H1"""
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(test_project)
        assert health == ProjectHealthEnum.H1.value

    def test_calculate_and_update_changed(self, db_session, test_project):
        """分支：健康度变化时更新"""
        calculator = HealthCalculator(db_session)
        test_project.health = "H1"
        test_project.status = "ST14"  # 阻塞状态
        db_session.commit()

        result = calculator.calculate_and_update(test_project, auto_save=True)

        assert result["changed"] is True
        assert result["old_health"] == "H1"
        assert result["new_health"] == "H3"

    def test_batch_calculate(self, db_session):
        """分支：批量计算项目健康度"""
        calculator = HealthCalculator(db_session)

        # 创建多个项目
        projects = [
            Project(
                project_code=f"PJ26030700{i}",
                project_name=f"测试项目{i}",
                stage="S4",
                status="ST07" if i % 2 == 0 else "ST14",
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
        assert result["updated"] >= 2


# ========== 里程碑服务测试 ==========

class TestMilestoneServiceBranches:
    """里程碑服务核心分支测试"""

    def test_create_milestone(self, db_session, test_project):
        """分支：创建里程碑"""
        service = MilestoneService(db_session)
        data = MilestoneCreate(
            project_id=test_project.id,
            milestone_name="设计评审",
            planned_date=date.today() + timedelta(days=10),
            is_key=True,
            status="PENDING",
        )

        milestone = service.create(data)

        assert milestone.milestone_name == "设计评审"
        assert milestone.is_key is True

    def test_get_by_project(self, db_session, test_project):
        """分支：按项目查询里程碑"""
        service = MilestoneService(db_session)

        # 创建里程碑
        for i in range(3):
            milestone = ProjectMilestone(
                project_id=test_project.id,
                milestone_name=f"里程碑{i}",
                planned_date=date.today() + timedelta(days=i * 5),
                status="PENDING",
            )
            db_session.add(milestone)
        db_session.commit()

        result = service.get_by_project(test_project.id)

        assert len(result) >= 3

    def test_complete_milestone(self, db_session, test_project):
        """分支：完成里程碑"""
        service = MilestoneService(db_session)

        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="待完成里程碑",
            planned_date=date.today(),
            status="IN_PROGRESS",
        )
        db_session.add(milestone)
        db_session.commit()

        result = service.complete_milestone(milestone_id=milestone.id)

        assert result.status == "COMPLETED"
        assert result.actual_date is not None

    def test_update_milestone(self, db_session, test_project):
        """分支：更新里程碑"""
        service = MilestoneService(db_session)

        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="原名称",
            planned_date=date.today(),
            status="PENDING",
        )
        db_session.add(milestone)
        db_session.commit()

        update_data = MilestoneUpdate(milestone_name="新名称")
        updated = service.update(milestone.id, update_data)

        assert updated.milestone_name == "新名称"


# ========== 综合流程测试 ==========

class TestProjectManagementFlowBranches:
    """项目管理综合流程分支测试"""

    def test_full_stage_advancement_flow(self, db_session, test_project):
        """分支：完整的阶段推进流程"""
        # 1. 验证阶段
        validate_target_stage("S4")
        validate_stage_advancement("S3", "S4")

        # 2. 更新阶段
        test_project.stage = "S3"
        test_project.status = "ST05"
        db_session.commit()

        new_status = update_project_stage_and_status(
            db=db_session,
            project=test_project,
            target_stage="S4",
            old_stage="S3",
            old_status="ST05",
        )

        # 3. 记录日志
        create_status_log(
            db=db_session,
            project_id=test_project.id,
            old_stage="S3",
            new_stage="S4",
            old_status="ST05",
            new_status=new_status,
            old_health="H1",
            new_health="H1",
            reason="完整流程测试",
            changed_by=1,
        )

        # 验证
        assert test_project.stage == "S4"
        logs = db_session.query(ProjectStatusLog).filter(
            ProjectStatusLog.project_id == test_project.id
        ).count()
        assert logs >= 1

    def test_project_health_update_on_issue(self, db_session, test_project):
        """分支：问题导致健康度变化"""
        calculator = HealthCalculator(db_session)

        # 初始正常状态
        test_project.health = "H1"
        db_session.commit()

        # 添加阻塞问题
        issue = Issue(
            project_id=test_project.id,
            title="严重问题",
            issue_type=IssueTypeEnum.BLOCKER,
            status=IssueStatusEnum.OPEN,
            priority="CRITICAL",
        )
        db_session.add(issue)
        db_session.commit()

        # 重新计算健康度
        result = calculator.calculate_and_update(test_project, auto_save=True)

        assert result["changed"] is True
        assert result["new_health"] == "H3"
