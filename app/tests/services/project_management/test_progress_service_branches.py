# -*- coding: utf-8 -*-
"""
进度管理服务分支测试
测试 app/services/progress_service.py 的各种分支逻辑

覆盖目标：
- 进度更新分支（手动、自动）
- 进度聚合分支（项目级、阶段级、加权）
- 进度预测分支（延迟、超前、正常）
- 依赖处理分支（时序冲突、缺失依赖、循环依赖）
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.progress import ProgressLog, Task, TaskDependency
from app.models.task_center import TaskUnified
from app.models.project import Project, ProjectStage
from app.services.progress_service import (
    update_task_progress,
    aggregate_task_progress,
    get_project_progress_summary,
    ProgressAggregationService,
    ProgressAutoService,
)


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
        is_active=True,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_task(db_session: Session, test_project):
    """创建测试任务"""
    task = TaskUnified(
        task_code="TSK001",
        title="测试任务",
        task_type="PROJECT_WBS",
        project_id=test_project.id,
        assignee_id=1,
        status="ACCEPTED",
        progress=0,
        estimated_hours=Decimal("10.0"),
        is_active=True,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


class TestProgressUpdateBranches:
    """测试进度更新的分支逻辑"""

    def test_update_progress_success(self, db_session, test_task):
        """分支：正常更新进度"""
        task, result = update_task_progress(
            db=db_session,
            task_id=test_task.id,
            progress=50,
            updater_id=1,
            run_aggregation=False,
        )

        assert task.progress == 50
        assert task.status == "IN_PROGRESS"

    def test_update_progress_to_100(self, db_session, test_task):
        """分支：进度更新到100% - 自动完成"""
        task, result = update_task_progress(
            db=db_session,
            task_id=test_task.id,
            progress=100,
            updater_id=1,
            run_aggregation=False,
        )

        assert task.progress == 100
        assert task.status == "COMPLETED"
        assert task.actual_end_date is not None

    def test_update_progress_start_date(self, db_session, test_task):
        """分支：首次更新进度 - 记录开始日期"""
        test_task.actual_start_date = None
        db_session.commit()

        task, result = update_task_progress(
            db=db_session,
            task_id=test_task.id,
            progress=10,
            updater_id=1,
            run_aggregation=False,
        )

        assert task.actual_start_date == date.today()
        assert task.status == "IN_PROGRESS"

    def test_update_progress_with_actual_hours(self, db_session, test_task):
        """分支：更新进度并记录实际工时"""
        task, result = update_task_progress(
            db=db_session,
            task_id=test_task.id,
            progress=50,
            updater_id=1,
            actual_hours=Decimal("5.0"),
            run_aggregation=False,
        )

        assert task.progress == 50
        assert task.actual_hours == Decimal("5.0")

    def test_update_progress_task_not_found(self, db_session):
        """分支：任务不存在 - 抛出异常"""
        with pytest.raises(ValueError, match="任务不存在"):
            update_task_progress(
                db=db_session,
                task_id=99999,
                progress=50,
                updater_id=1,
            )

    def test_update_progress_not_assignee(self, db_session, test_task):
        """分支：非任务负责人更新 - 抛出异常"""
        with pytest.raises(ValueError, match="只能更新分配给自己的任务"):
            update_task_progress(
                db=db_session,
                task_id=test_task.id,
                progress=50,
                updater_id=999,  # 不同的用户
            )

    def test_update_progress_completed_task(self, db_session, test_task):
        """分支:任务已完成 - 抛出异常"""
        test_task.status = "COMPLETED"
        db_session.commit()

        with pytest.raises(ValueError, match="任务已完成或已被拒绝"):
            update_task_progress(
                db=db_session,
                task_id=test_task.id,
                progress=60,
                updater_id=1,
            )

    def test_update_progress_invalid_range(self, db_session, test_task):
        """分支：进度超出范围 - 抛出异常"""
        with pytest.raises(ValueError, match="进度必须在0到100之间"):
            update_task_progress(
                db=db_session,
                task_id=test_task.id,
                progress=150,
                updater_id=1,
            )

    def test_update_progress_with_note(self, db_session, test_task):
        """分支：更新进度并记录日志"""
        task, result = update_task_progress(
            db=db_session,
            task_id=test_task.id,
            progress=50,
            updater_id=1,
            progress_note="完成了一半的工作",
            create_progress_log=True,
            run_aggregation=False,
        )

        # 验证进度日志是否创建
        log = db_session.query(ProgressLog).filter(
            ProgressLog.task_id == test_task.id
        ).first()
        assert log is not None
        assert "完成了一半的工作" in log.update_note


class TestProgressAggregationBranches:
    """测试进度聚合的分支逻辑"""

    def test_aggregate_to_project(self, db_session, test_project, test_task):
        """分支：聚合到项目级别"""
        # 更新任务进度
        test_task.progress = 75
        db_session.commit()

        # 执行聚合
        result = aggregate_task_progress(db_session, test_task.id)

        assert result["project_progress_updated"] is True
        assert result["project_id"] == test_project.id
        assert result["new_project_progress"] > 0

    def test_aggregate_to_stage(self, db_session, test_project, test_task):
        """分支：聚合到阶段级别"""
        # 设置任务阶段
        test_task.stage = "S4"
        test_task.progress = 80
        db_session.commit()

        # 创建阶段记录
        stage = ProjectStage(
            project_id=test_project.id,
            stage_code="S4",
            stage_name="加工制造",
            progress_pct=Decimal("0.0"),
        )
        db_session.add(stage)
        db_session.commit()

        # 执行聚合
        result = aggregate_task_progress(db_session, test_task.id)

        assert result["stage_progress_updated"] is True
        assert result["stage_code"] == "S4"
        assert result["new_stage_progress"] > 0

    def test_aggregate_no_project(self, db_session, test_task):
        """分支：任务无关联项目 - 不聚合"""
        test_task.project_id = None
        db_session.commit()

        result = aggregate_task_progress(db_session, test_task.id)

        assert result["project_progress_updated"] is False
        assert result["project_id"] is None

    def test_aggregate_weighted_progress(self, db_session, test_project):
        """分支：按工时加权计算进度"""
        # 创建多个任务，不同工时
        tasks = [
            TaskUnified(
                project_id=test_project.id,
                task_name=f"任务{i}",
                assignee_id=1,
                status="IN_PROGRESS",
                progress=50 if i == 0 else 100,  # 第一个任务50%,其他100%
                estimated_hours=Decimal(f"{10 * i if i > 0 else 10}.0"),
                is_active=True,
            )
            for i in range(3)
        ]
        db_session.add_all(tasks)
        db_session.commit()

        # 执行聚合
        service = ProgressAggregationService()
        result = service.aggregate_project_progress(test_project.id, db_session)

        assert result["total_tasks"] >= 3
        # 加权平均应该更接近100%（大工时任务都是100%）
        assert result["overall_progress"] > 50


class TestProgressAutoServiceBranches:
    """测试进度自动化服务的分支逻辑"""

    def test_auto_block_delayed_task(self, db_session, test_project):
        """分支：自动阻塞延迟任务"""
        from app.schemas.progress import TaskForecastItem

        # 创建任务
        task = Task(
            project_id=test_project.id,
            task_name="延迟任务",
            status="TODO",
            progress_percent=10,
        )
        db_session.add(task)
        db_session.commit()

        # 创建预测结果（延迟10天）
        forecast_items = [
            TaskForecastItem(
                task_id=task.id,
                task_name="延迟任务",
                current_progress=10,
                predicted_progress=50,
                status="Delayed",
                delay_days=10,
                critical=True,
            )
        ]

        service = ProgressAutoService(db_session)
        result = service.apply_forecast_to_tasks(
            project_id=test_project.id,
            forecast_items=forecast_items,
            auto_block=True,
            delay_threshold=3,
        )

        assert result["blocked"] == 1
        db_session.refresh(task)
        assert task.status == "BLOCKED"
        assert "预测延迟" in task.block_reason

    def test_auto_block_skip_completed(self, db_session, test_project):
        """分支：跳过已完成任务的阻塞"""
        from app.schemas.progress import TaskForecastItem

        task = Task(
            project_id=test_project.id,
            task_name="已完成任务",
            status="DONE",
            progress_percent=100,
        )
        db_session.add(task)
        db_session.commit()

        forecast_items = [
            TaskForecastItem(
                task_id=task.id,
                task_name="已完成任务",
                current_progress=100,
                predicted_progress=100,
                status="Delayed",
                delay_days=10,
                critical=True,
            )
        ]

        service = ProgressAutoService(db_session)
        result = service.apply_forecast_to_tasks(
            project_id=test_project.id,
            forecast_items=forecast_items,
            auto_block=True,
            delay_threshold=3,
        )

        # 已完成任务不应该被阻塞
        assert result["blocked"] == 0
        db_session.refresh(task)
        assert task.status == "DONE"

    def test_auto_tag_high_risk(self, db_session, test_project):
        """分支：高风险任务自动标记"""
        from app.schemas.progress import TaskForecastItem

        task = Task(
            project_id=test_project.id,
            task_name="高风险任务",
            status="TODO",
            progress_percent=5,
        )
        db_session.add(task)
        db_session.commit()

        forecast_items = [
            TaskForecastItem(
                task_id=task.id,
                task_name="高风险任务",
                current_progress=5,
                predicted_progress=30,
                status="Delayed",
                delay_days=5,
                critical=True,
            )
        ]

        service = ProgressAutoService(db_session)
        result = service.apply_forecast_to_tasks(
            project_id=test_project.id,
            forecast_items=forecast_items,
            auto_block=False,  # 不自动阻塞，只标记
            delay_threshold=3,
        )

        assert result["risk_tagged"] >= 1

        # 验证进度日志
        logs = db_session.query(ProgressLog).filter(
            ProgressLog.task_id == task.id
        ).all()
        assert len(logs) >= 1
        assert "高风险预警" in logs[0].update_note


class TestDependencyFixBranches:
    """测试依赖修复的分支逻辑"""

    def test_fix_timing_conflict(self, db_session, test_project):
        """分支：修复时序冲突"""
        from app.schemas.progress import DependencyIssue

        # 创建前置任务和后续任务
        pred_task = Task(
            project_id=test_project.id,
            task_name="前置任务",
            plan_start=date.today(),
            plan_end=date.today() + timedelta(days=5),
            actual_end=date.today() + timedelta(days=3),
        )
        succ_task = Task(
            project_id=test_project.id,
            task_name="后续任务",
            plan_start=date.today(),  # 时序冲突：比前置任务早
            plan_end=date.today() + timedelta(days=3),
        )
        db_session.add_all([pred_task, succ_task])
        db_session.commit()

        # 创建依赖关系
        dep = TaskDependency(
            task_id=succ_task.id,
            depends_on_task_id=pred_task.id,
            lag_days=1,
        )
        db_session.add(dep)
        db_session.commit()

        # 创建依赖问题
        issue = DependencyIssue(
            task_id=succ_task.id,
            task_name="后续任务",
            issue_type="TIMING_CONFLICT",
            severity="HIGH",
            detail="后续任务开始时间早于前置任务结束时间",
        )

        service = ProgressAutoService(db_session)
        result = service.auto_fix_dependency_issues(
            project_id=test_project.id,
            issues=[issue],
            auto_fix_timing=True,
            auto_fix_missing=False,
        )

        assert result["timing_fixed"] == 1
        db_session.refresh(succ_task)
        # 后续任务应该被调整到前置任务之后
        assert succ_task.plan_start > pred_task.actual_end

    def test_remove_missing_dependency(self, db_session, test_project):
        """分支：移除缺失的依赖"""
        from app.schemas.progress import DependencyIssue

        # 创建任务（前置任务不存在）
        task = Task(
            project_id=test_project.id,
            task_name="孤立任务",
        )
        db_session.add(task)
        db_session.commit()

        # 创建指向不存在任务的依赖
        dep = TaskDependency(
            task_id=task.id,
            depends_on_task_id=99999,  # 不存在的任务
        )
        db_session.add(dep)
        db_session.commit()

        # 创建依赖问题
        issue = DependencyIssue(
            task_id=task.id,
            task_name="孤立任务",
            issue_type="MISSING_PREDECESSOR",
            severity="MEDIUM",
            detail="前置任务不存在",
        )

        service = ProgressAutoService(db_session)
        result = service.auto_fix_dependency_issues(
            project_id=test_project.id,
            issues=[issue],
            auto_fix_timing=False,
            auto_fix_missing=True,
        )

        assert result["missing_removed"] == 1

        # 验证依赖已被删除
        remaining_deps = db_session.query(TaskDependency).filter(
            TaskDependency.task_id == task.id
        ).count()
        assert remaining_deps == 0

    def test_skip_cycle_issues(self, db_session, test_project):
        """分支：跳过循环依赖问题（不自动修复）"""
        from app.schemas.progress import DependencyIssue

        issue = DependencyIssue(
            task_id=1,
            task_name="循环任务",
            issue_type="CYCLE",
            severity="CRITICAL",
            detail="检测到循环依赖",
        )

        service = ProgressAutoService(db_session)
        result = service.auto_fix_dependency_issues(
            project_id=test_project.id,
            issues=[issue],
            auto_fix_timing=True,
            auto_fix_missing=True,
        )

        # 循环依赖应该被跳过
        assert result["cycles_skipped"] == 1
        assert result["timing_fixed"] == 0
        assert result["missing_removed"] == 0


class TestProjectProgressSummaryBranches:
    """测试项目进度汇总的分支逻辑"""

    def test_summary_with_tasks(self, db_session, test_project):
        """分支：有任务的项目汇总"""
        # 创建不同状态的任务
        tasks = [
            TaskUnified(
                project_id=test_project.id,
                task_name="已完成任务",
                status="COMPLETED",
                progress=100,
                is_active=True,
            ),
            TaskUnified(
                project_id=test_project.id,
                task_name="进行中任务",
                status="IN_PROGRESS",
                progress=50,
                is_active=True,
            ),
            TaskUnified(
                project_id=test_project.id,
                task_name="待开始任务",
                status="ACCEPTED",
                progress=0,
                is_active=True,
            ),
            TaskUnified(
                project_id=test_project.id,
                task_name="已取消任务",
                status="CANCELLED",
                progress=0,
                is_active=False,
            ),
        ]
        db_session.add_all(tasks)
        db_session.commit()

        summary = get_project_progress_summary(db_session, test_project.id)

        assert summary["total_tasks"] == 3  # 不含已取消任务
        assert summary["completed_tasks"] == 1
        assert summary["in_progress_tasks"] == 1
        assert summary["overall_progress"] > 0
        assert summary["completion_rate"] > 0

    def test_summary_with_delayed_tasks(self, db_session, test_project):
        """分支：包含延期任务的汇总"""
        # 创建延期任务
        task = TaskUnified(
            project_id=test_project.id,
            task_name="延期任务",
            status="IN_PROGRESS",
            progress=30,
            is_delayed=True,
            is_active=True,
        )
        db_session.add(task)
        db_session.commit()

        summary = get_project_progress_summary(db_session, test_project.id)

        assert summary["delayed_tasks"] >= 1

    def test_summary_with_overdue_tasks(self, db_session, test_project):
        """分支：包含逾期任务的汇总"""
        # 创建逾期任务
        task = TaskUnified(
            project_id=test_project.id,
            task_name="逾期任务",
            status="IN_PROGRESS",
            progress=20,
            deadline=datetime.now() - timedelta(days=5),
            is_active=True,
        )
        db_session.add(task)
        db_session.commit()

        summary = get_project_progress_summary(db_session, test_project.id)

        assert summary["overdue_tasks"] >= 1

    def test_summary_empty_project(self, db_session, test_project):
        """分支：无任务的项目汇总"""
        summary = get_project_progress_summary(db_session, test_project.id)

        assert summary["total_tasks"] == 0
        assert summary["completed_tasks"] == 0
        assert summary["in_progress_tasks"] == 0
        assert summary["completion_rate"] == 0
