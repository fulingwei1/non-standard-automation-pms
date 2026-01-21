# -*- coding: utf-8 -*-
"""
progress_aggregation_service 单元测试

测试进���聚合服务的各个方法：
- 任务进度聚合
- 阶段进度聚合
- 项目进度聚合
- 健康度计算
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.progress_aggregation_service import (
    ProgressAggregationService,
    _check_and_update_health,
    aggregate_task_progress,
    create_progress_log,
    get_project_progress_summary,
)


def create_mock_db_session():
    """创建模拟的数据库会话"""
    return MagicMock()


def create_mock_task(
    task_id=1,
    project_id=1,
    stage="S1",
    progress=50,
    is_active=True,
    status="IN_PROGRESS",
    is_delayed=False,
    deadline=None,
):
    """创建模拟的任务对象"""
    mock = MagicMock()
    mock.id = task_id
    mock.project_id = project_id
    mock.stage = stage
    mock.progress = progress
    mock.is_active = is_active
    mock.status = status
    mock.is_delayed = is_delayed
    mock.deadline = deadline or (datetime.now() + timedelta(days=7))
    return mock


def create_mock_project(project_id=1, progress_pct=0, health="H1"):
    """创建模拟的项目对象"""
    mock = MagicMock()
    mock.id = project_id
    mock.progress_pct = progress_pct
    mock.health = health
    mock.updated_at = datetime.now()
    return mock


def create_mock_project_stage(project_id=1, stage_code="S1", progress_pct=0):
    """创建模拟的项目阶段对象"""
    mock = MagicMock()
    mock.project_id = project_id
    mock.stage_code = stage_code
    mock.progress_pct = progress_pct
    mock.updated_at = datetime.now()
    return mock


@pytest.mark.unit
class TestAggregateTaskProgress:
    """测试 aggregate_task_progress 函数"""

    def test_returns_empty_result_for_nonexistent_task(self):
        """测试任务不存在时返回空结果"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        result = aggregate_task_progress(db, 999)

        assert result["project_progress_updated"] is False
        assert result["project_id"] is None

    def test_returns_empty_result_for_task_without_project(self):
        """测试任务无项目时返回空结果"""
        db = create_mock_db_session()
        task = create_mock_task(project_id=None)
        db.query.return_value.filter.return_value.first.return_value = task

        result = aggregate_task_progress(db, 1)

        assert result["project_progress_updated"] is False

    def test_updates_project_progress(self):
        """测试更新项目进度"""
        db = create_mock_db_session()
        task = create_mock_task(project_id=1, stage=None)
        project = create_mock_project()

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            model_name = str(model)
            if call_count[0] == 0:  # TaskUnified
                mock_query.filter.return_value.first.return_value = task
                mock_query.filter.return_value.scalar.return_value = 5  # total tasks
            elif call_count[0] == 1:  # count
                mock_query.filter.return_value.scalar.return_value = 5
            elif call_count[0] == 2:  # sum progress
                mock_query.filter.return_value.scalar.return_value = 250  # avg 50%
            elif call_count[0] == 3:  # Project
                mock_query.filter.return_value.first.return_value = project
            call_count[0] += 1
            return mock_query

        db.query.side_effect = query_side_effect

        with patch(
            "app.services.progress_aggregation_service._check_and_update_health"
        ):
            result = aggregate_task_progress(db, 1)

        assert result["project_id"] == 1

    def test_returns_result_with_project_id(self):
        """测试返回包含项目ID的结果"""
        db = create_mock_db_session()
        task = create_mock_task(project_id=1, stage=None)
        project = create_mock_project()

        db.query.return_value.filter.return_value.first.side_effect = [
            task,
            project,
            project,  # for _check_and_update_health
        ]
        db.query.return_value.filter.return_value.scalar.return_value = 100

        with patch(
            "app.services.progress_aggregation_service._check_and_update_health"
        ):
            result = aggregate_task_progress(db, 1)

        assert result["project_id"] == 1
        assert result["project_progress_updated"] is True


@pytest.mark.unit
class TestCheckAndUpdateHealth:
    """测试 _check_and_update_health 函数"""

    def test_does_nothing_for_nonexistent_project(self):
        """测试项目不存在时不做任何操作"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        _check_and_update_health(db, 999)

        db.commit.assert_not_called()

    def test_does_nothing_for_no_active_tasks(self):
        """测试无活跃任务时不更新健康度"""
        db = create_mock_db_session()
        project = create_mock_project(health="H1")
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.scalar.return_value = 0

        _check_and_update_health(db, 1)

        # 没有活跃任务，不应更新
        assert project.health == "H1"

    def test_sets_h1_for_healthy_project(self):
        """测试健康项目设置H1"""
        db = create_mock_db_session()
        project = create_mock_project(health="H2")

        call_count = [0]

        def scalar_side_effect():
            results = [10, 0, 0]  # total=10, delayed=0, overdue=0
            result = results[call_count[0]] if call_count[0] < len(results) else 0
            call_count[0] += 1
            return result

        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.scalar.side_effect = scalar_side_effect

        _check_and_update_health(db, 1)

        assert project.health == "H1"

    def test_sets_h2_for_at_risk_project(self):
        """测试有风险项目设置H2"""
        db = create_mock_db_session()
        project = create_mock_project(health="H1")

        call_count = [0]

        def scalar_side_effect():
            # 20% delayed = H2
            results = [10, 2, 0]  # total=10, delayed=2 (20%), overdue=0
            result = results[call_count[0]] if call_count[0] < len(results) else 0
            call_count[0] += 1
            return result

        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.scalar.side_effect = scalar_side_effect

        _check_and_update_health(db, 1)

        assert project.health == "H2"

    def test_sets_h3_for_blocked_project(self):
        """测试阻塞项目设置H3"""
        db = create_mock_db_session()
        project = create_mock_project(health="H1")

        call_count = [0]

        def scalar_side_effect():
            # 30% delayed = H3
            results = [10, 3, 0]  # total=10, delayed=3 (30%), overdue=0
            result = results[call_count[0]] if call_count[0] < len(results) else 0
            call_count[0] += 1
            return result

        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.scalar.side_effect = scalar_side_effect

        _check_and_update_health(db, 1)

        assert project.health == "H3"

    def test_sets_h3_for_high_overdue(self):
        """测试高逾期率设置H3"""
        db = create_mock_db_session()
        project = create_mock_project(health="H1")

        call_count = [0]

        def scalar_side_effect():
            # 20% overdue = H3
            results = [10, 0, 2]  # total=10, delayed=0, overdue=2 (20%)
            result = results[call_count[0]] if call_count[0] < len(results) else 0
            call_count[0] += 1
            return result

        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.scalar.side_effect = scalar_side_effect

        _check_and_update_health(db, 1)

        assert project.health == "H3"


@pytest.mark.unit
class TestCreateProgressLog:
    """测试 create_progress_log 函数"""

    def test_creates_log_successfully(self):
        """测试成功创建日志"""
        db = create_mock_db_session()

        result = create_progress_log(
            db=db,
            task_id=1,
            progress=50,
            actual_hours=4.0,
            note="测试进度更新",
            updater_id=1,
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_creates_log_with_default_note(self):
        """测试使用默认说明创建日志"""
        db = create_mock_db_session()

        result = create_progress_log(
            db=db,
            task_id=1,
            progress=75,
            actual_hours=None,
            note=None,
            updater_id=1,
        )

        db.add.assert_called_once()
        created_log = db.add.call_args[0][0]
        assert "75%" in created_log.update_note

    def test_handles_exception_gracefully(self):
        """测试异常时优雅处理"""
        db = create_mock_db_session()
        db.add.side_effect = Exception("数据库错误")

        result = create_progress_log(
            db=db,
            task_id=1,
            progress=50,
            actual_hours=4.0,
            note="测试",
            updater_id=1,
        )

        assert result is None
        db.rollback.assert_called_once()


@pytest.mark.unit
class TestGetProjectProgressSummary:
    """测试 get_project_progress_summary 函数"""

    def test_returns_summary_structure(self):
        """测试返回汇总结构"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = (
            []
        )

        result = get_project_progress_summary(db, 1)

        assert "project_id" in result
        assert "total_tasks" in result
        assert "completed_tasks" in result
        assert "in_progress_tasks" in result
        assert "delayed_tasks" in result
        assert "overdue_tasks" in result
        assert "overall_progress" in result
        assert "completion_rate" in result

    def test_calculates_completion_rate(self):
        """测试计算完成率"""
        db = create_mock_db_session()

        call_count = [0]

        def query_side_effect(*args):
            mock_query = MagicMock()
            if call_count[0] == 0:  # total tasks
                mock_query.filter.return_value.scalar.return_value = 10
            elif call_count[0] == 1:  # status counts
                mock_query.filter.return_value.group_by.return_value.all.return_value = [
                    ("COMPLETED", 5),
                    ("IN_PROGRESS", 3),
                ]
            elif call_count[0] == 2:  # delayed
                mock_query.filter.return_value.scalar.return_value = 1
            elif call_count[0] == 3:  # overdue
                mock_query.filter.return_value.scalar.return_value = 0
            elif call_count[0] == 4:  # avg progress
                mock_query.filter.return_value.scalar.return_value = 60.0
            call_count[0] += 1
            return mock_query

        db.query.side_effect = query_side_effect

        result = get_project_progress_summary(db, 1)

        assert result["total_tasks"] == 10
        assert result["completed_tasks"] == 5
        assert result["completion_rate"] == 50.0

    def test_handles_zero_tasks(self):
        """测试无任务时处理"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = (
            []
        )

        result = get_project_progress_summary(db, 1)

        assert result["total_tasks"] == 0
        assert result["completion_rate"] == 0


@pytest.mark.unit
class TestProgressAggregationService:
    """测试 ProgressAggregationService 类"""

    def test_aggregate_project_progress_returns_structure(self):
        """测试聚合项目进度返回结构"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = (
            []
        )

        result = ProgressAggregationService.aggregate_project_progress(1, db)

        assert "project_id" in result
        assert "total_tasks" in result
        assert "completed_tasks" in result
        assert "in_progress_tasks" in result
        assert "pending_approval_tasks" in result
        assert "delayed_tasks" in result
        assert "overdue_tasks" in result
        assert "overall_progress" in result
        assert "calculated_at" in result

    def test_calculates_weighted_progress(self):
        """测试计算加权进度"""
        db = create_mock_db_session()

        call_count = [0]

        def query_side_effect(*args):
            mock_query = MagicMock()
            if call_count[0] == 0:  # total tasks count
                mock_query.filter.return_value.scalar.return_value = 3
            elif call_count[0] == 1:  # status counts
                mock_query.filter.return_value.group_by.return_value.all.return_value = [
                    ("COMPLETED", 1),
                    ("IN_PROGRESS", 2),
                ]
            elif call_count[0] == 2:  # total hours (weight)
                mock_query.filter.return_value.scalar.return_value = 24.0
            elif call_count[0] == 3:  # weighted progress sum
                mock_query.filter.return_value.scalar.return_value = 1200.0  # 50 * 24
            elif call_count[0] == 4:  # delayed
                mock_query.filter.return_value.scalar.return_value = 0
            elif call_count[0] == 5:  # overdue
                mock_query.filter.return_value.scalar.return_value = 0
            call_count[0] += 1
            return mock_query

        db.query.side_effect = query_side_effect

        result = ProgressAggregationService.aggregate_project_progress(1, db)

        assert result["total_tasks"] == 3
        assert result["overall_progress"] == 50.0

    def test_falls_back_to_simple_average_without_hours(self):
        """测试无工时时退化为简单平均"""
        db = create_mock_db_session()

        call_count = [0]

        def query_side_effect(*args):
            mock_query = MagicMock()
            if call_count[0] == 0:  # total tasks count
                mock_query.filter.return_value.scalar.return_value = 3
            elif call_count[0] == 1:  # status counts
                mock_query.filter.return_value.group_by.return_value.all.return_value = []
            elif call_count[0] == 2:  # total hours = 0
                mock_query.filter.return_value.scalar.return_value = 0
            elif call_count[0] == 3:  # weighted progress = 0
                mock_query.filter.return_value.scalar.return_value = 0
            elif call_count[0] == 4:  # avg progress fallback
                mock_query.filter.return_value.scalar.return_value = 60.0
            elif call_count[0] == 5:  # delayed
                mock_query.filter.return_value.scalar.return_value = 0
            elif call_count[0] == 6:  # overdue
                mock_query.filter.return_value.scalar.return_value = 0
            call_count[0] += 1
            return mock_query

        db.query.side_effect = query_side_effect

        result = ProgressAggregationService.aggregate_project_progress(1, db)

        assert result["overall_progress"] == 60.0

    def test_handles_no_tasks(self):
        """测试无任务时处理"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = (
            []
        )

        result = ProgressAggregationService.aggregate_project_progress(1, db)

        assert result["total_tasks"] == 0
        assert result["overall_progress"] == 0.0

    def test_counts_status_correctly(self):
        """测试正确统计状态"""
        db = create_mock_db_session()

        call_count = [0]

        def query_side_effect(*args):
            mock_query = MagicMock()
            if call_count[0] == 0:  # total tasks count
                mock_query.filter.return_value.scalar.return_value = 10
            elif call_count[0] == 1:  # status counts
                mock_query.filter.return_value.group_by.return_value.all.return_value = [
                    ("COMPLETED", 3),
                    ("IN_PROGRESS", 4),
                    ("ACCEPTED", 1),
                    ("PENDING_APPROVAL", 2),
                ]
            elif call_count[0] == 2:  # total hours
                mock_query.filter.return_value.scalar.return_value = 10.0
            elif call_count[0] == 3:  # weighted progress
                mock_query.filter.return_value.scalar.return_value = 500.0
            elif call_count[0] == 4:  # delayed
                mock_query.filter.return_value.scalar.return_value = 1
            elif call_count[0] == 5:  # overdue
                mock_query.filter.return_value.scalar.return_value = 0
            call_count[0] += 1
            return mock_query

        db.query.side_effect = query_side_effect

        result = ProgressAggregationService.aggregate_project_progress(1, db)

        assert result["completed_tasks"] == 3
        assert result["in_progress_tasks"] == 5  # IN_PROGRESS + ACCEPTED
        assert result["pending_approval_tasks"] == 2
        assert result["delayed_tasks"] == 1
