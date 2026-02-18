"""
进度跟踪服务测试
测试进度计算、偏差检测、里程碑跟踪等核心功能
"""
import pytest
pytest.importorskip("app.services.progress_tracking_service")

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.progress_tracking_service import ProgressTrackingService
from app.models.project import Project
from app.models.task import Task
from app.models.milestone import Milestone


class TestProgressTrackingService:
    """进度跟踪服务测试类"""

    @pytest.fixture
    def service(self, mock_database_session):
        """创建服务实例"""
        return ProgressTrackingService(mock_database_session)

    @pytest.fixture
    def project(self):
        """测试项目"""
        return Project(
            id=1,
            name="测试项目",
            start_date=date(2026, 1, 1),
            planned_end_date=date(2026, 6, 30),
            current_progress=0,
            status="in_progress"
        )

    @pytest.fixture
    def tasks(self):
        """测试任务列表"""
        return [
            Task(id=1, project_id=1, name="任务1", progress=100, weight=0.2),
            Task(id=2, project_id=1, name="任务2", progress=80, weight=0.3),
            Task(id=3, project_id=1, name="任务3", progress=50, weight=0.3),
            Task(id=4, project_id=1, name="任务4", progress=0, weight=0.2),
        ]

    def test_calculate_project_progress(self, service, tasks):
        """测试项目进度计算 - 加权平均"""
        # 期望值: 100*0.2 + 80*0.3 + 50*0.3 + 0*0.2 = 59
        progress = service.calculate_project_progress(tasks)
        assert progress == 59.0

    def test_calculate_progress_with_equal_weights(self, service):
        """测试进度计算 - 等权重"""
        tasks = [
            Task(id=1, progress=100, weight=None),
            Task(id=2, progress=80, weight=None),
            Task(id=3, progress=60, weight=None),
            Task(id=4, progress=40, weight=None),
        ]
        # 平均值: (100+80+60+40)/4 = 70
        progress = service.calculate_project_progress(tasks)
        assert progress == 70.0

    def test_calculate_progress_boundary_empty(self, service):
        """测试边界条件 - 空任务列表"""
        progress = service.calculate_project_progress([])
        assert progress == 0.0

    def test_calculate_progress_boundary_single_task(self, service):
        """测试边界条件 - 单个任务"""
        tasks = [Task(id=1, progress=75, weight=1.0)]
        progress = service.calculate_project_progress(tasks)
        assert progress == 75.0

    def test_detect_progress_deviation(self, service, project):
        """测试进度偏差检测"""
        project.current_progress = 40
        project.start_date = date(2026, 1, 1)
        project.planned_end_date = date(2026, 7, 1)  # 6个月项目
        
        current_date = date(2026, 4, 1)  # 3个月后
        # 预期进度: 50%, 实际进度: 40%, 偏差: -10%
        
        deviation = service.detect_progress_deviation(project, current_date)
        
        assert deviation is not None
        assert deviation['planned_progress'] == pytest.approx(50.0, abs=1)
        assert deviation['actual_progress'] == 40.0
        assert deviation['deviation'] == pytest.approx(-10.0, abs=1)
        assert deviation['is_delayed'] is True

    def test_progress_deviation_ahead_of_schedule(self, service, project):
        """测试进度超前情况"""
        project.current_progress = 70
        project.start_date = date(2026, 1, 1)
        project.planned_end_date = date(2026, 7, 1)
        
        current_date = date(2026, 4, 1)  # 应该完成50%
        
        deviation = service.detect_progress_deviation(project, current_date)
        
        assert deviation['planned_progress'] == pytest.approx(50.0, abs=1)
        assert deviation['actual_progress'] == 70.0
        assert deviation['deviation'] > 0
        assert deviation['is_delayed'] is False

    def test_trigger_progress_alert(self, service, project):
        """测试进度预警触发"""
        project.current_progress = 30
        project.start_date = date(2026, 1, 1)
        project.planned_end_date = date(2026, 7, 1)
        
        current_date = date(2026, 4, 1)
        
        # 偏差 > 10% 应该触发预警
        should_alert = service.should_trigger_alert(project, current_date, threshold=10.0)
        assert should_alert is True

    def test_no_alert_for_minor_deviation(self, service, project):
        """测试小偏差不触发预警"""
        project.current_progress = 48
        project.start_date = date(2026, 1, 1)
        project.planned_end_date = date(2026, 7, 1)
        
        current_date = date(2026, 4, 1)  # 应该50%
        
        # 偏差 < 5% 不应该触发预警
        should_alert = service.should_trigger_alert(project, current_date, threshold=5.0)
        assert should_alert is False

    def test_track_milestone_progress(self, service):
        """测试里程碑跟踪"""
        milestones = [
            Milestone(
                id=1,
                name="需求评审",
                planned_date=date(2026, 2, 1),
                actual_date=date(2026, 2, 3),
                status="completed"
            ),
            Milestone(
                id=2,
                name="设计评审",
                planned_date=date(2026, 3, 1),
                actual_date=None,
                status="pending"
            ),
        ]
        
        summary = service.track_milestone_progress(milestones)
        
        assert summary['total'] == 2
        assert summary['completed'] == 1
        assert summary['completion_rate'] == 50.0
        assert summary['delayed_count'] == 1  # 第一个里程碑延期2天

    def test_calculate_critical_path(self, service):
        """测试关键路径计算"""
        tasks_with_dependencies = [
            {
                'id': 1,
                'duration': 5,
                'dependencies': [],
                'name': 'A'
            },
            {
                'id': 2,
                'duration': 3,
                'dependencies': [1],
                'name': 'B'
            },
            {
                'id': 3,
                'duration': 4,
                'dependencies': [1],
                'name': 'C'
            },
            {
                'id': 4,
                'duration': 2,
                'dependencies': [2, 3],
                'name': 'D'
            },
        ]
        
        critical_path = service.calculate_critical_path(tasks_with_dependencies)
        
        # 关键路径应该是 A → C → D (5 + 4 + 2 = 11天)
        assert len(critical_path) > 0
        assert critical_path['duration'] == 11
        assert 1 in critical_path['tasks']  # 任务A
        assert 3 in critical_path['tasks']  # 任务C
        assert 4 in critical_path['tasks']  # 任务D

    def test_generate_progress_report(self, service, project, tasks):
        """测试进度报告生成"""
        with patch.object(service, 'calculate_project_progress', return_value=59.0):
            report = service.generate_progress_report(
                project=project,
                tasks=tasks,
                report_date=date(2026, 4, 1)
            )
        
        assert report is not None
        assert 'project_id' in report
        assert 'progress' in report
        assert 'report_date' in report
        assert report['progress'] == 59.0

    def test_detect_parallel_tasks(self, service):
        """测试并行任务检测"""
        tasks = [
            Task(id=1, start_date=date(2026, 1, 1), end_date=date(2026, 1, 10)),
            Task(id=2, start_date=date(2026, 1, 5), end_date=date(2026, 1, 15)),
            Task(id=3, start_date=date(2026, 1, 11), end_date=date(2026, 1, 20)),
        ]
        
        parallel_groups = service.detect_parallel_tasks(tasks)
        
        # 任务1和任务2有重叠，任务3独立
        assert len(parallel_groups) > 0
        assert {1, 2} in [set(group) for group in parallel_groups]

    def test_calculate_velocity(self, service):
        """测试速度计算 - 基于历史数据"""
        historical_data = [
            {'date': date(2026, 1, 1), 'progress': 10},
            {'date': date(2026, 1, 8), 'progress': 20},  # 7天完成10%
            {'date': date(2026, 1, 15), 'progress': 32}, # 7天完成12%
            {'date': date(2026, 1, 22), 'progress': 43}, # 7天完成11%
        ]
        
        velocity = service.calculate_velocity(historical_data)
        
        # 平均每周速度: (10+12+11)/3 ≈ 11%
        assert velocity == pytest.approx(11.0, abs=1)

    def test_predict_completion_date(self, service, project):
        """测试完成日期预测"""
        project.current_progress = 60
        current_velocity = 10  # 每周10%
        
        predicted_date = service.predict_completion_date(
            current_progress=60,
            velocity=current_velocity,
            current_date=date(2026, 4, 1)
        )
        
        # 剩余40%, 速度10%/周, 需要4周
        expected_date = date(2026, 4, 1) + timedelta(weeks=4)
        assert predicted_date == expected_date

    def test_rollback_progress(self, service, project):
        """测试进度回滚"""
        project.current_progress = 75
        
        rollback_result = service.rollback_progress(
            project=project,
            target_progress=60,
            reason="需求变更，部分功能作废"
        )
        
        assert rollback_result['success'] is True
        assert rollback_result['old_progress'] == 75
        assert rollback_result['new_progress'] == 60

    def test_validate_progress_permissions(self, service):
        """测试进度更新权限验证"""
        user = MagicMock(id=10, role="developer")
        project = MagicMock(id=1, pm_id=20, team_members=[10, 11, 12])
        
        # 开发人员应该有权限
        has_permission = service.validate_update_permission(user, project)
        assert has_permission is True
        
        # 非团队成员无权限
        user.id = 99
        has_permission = service.validate_update_permission(user, project)
        assert has_permission is False


class TestProgressAggregation:
    """进度聚合测试"""

    @pytest.fixture
    def service(self, mock_database_session):
        return ProgressTrackingService(mock_database_session)

    def test_aggregate_department_progress(self, service):
        """测试部门进度聚合"""
        projects = [
            MagicMock(id=1, department_id=1, current_progress=80, weight=1.0),
            MagicMock(id=2, department_id=1, current_progress=60, weight=1.0),
            MagicMock(id=3, department_id=1, current_progress=90, weight=1.0),
        ]
        
        dept_progress = service.aggregate_department_progress(projects)
        
        # 平均进度: (80+60+90)/3 ≈ 76.67
        assert dept_progress == pytest.approx(76.67, abs=0.1)

    def test_aggregate_with_weighted_projects(self, service):
        """测试加权项目聚合"""
        projects = [
            MagicMock(id=1, current_progress=80, weight=2.0),  # 重要项目
            MagicMock(id=2, current_progress=60, weight=1.0),
            MagicMock(id=3, current_progress=90, weight=1.0),
        ]
        
        weighted_progress = service.aggregate_weighted_progress(projects)
        
        # (80*2 + 60*1 + 90*1) / (2+1+1) = 310/4 = 77.5
        assert weighted_progress == 77.5


class TestProgressAnomaly:
    """进度异常检测测试"""

    @pytest.fixture
    def service(self, mock_database_session):
        return ProgressTrackingService(mock_database_session)

    def test_detect_progress_stagnation(self, service):
        """测试进度停滞检测"""
        progress_history = [
            {'date': date(2026, 1, 1), 'progress': 50},
            {'date': date(2026, 1, 8), 'progress': 50},
            {'date': date(2026, 1, 15), 'progress': 51},
            {'date': date(2026, 1, 22), 'progress': 51},
        ]
        
        is_stagnant = service.detect_stagnation(progress_history, threshold_days=14)
        
        assert is_stagnant is True

    def test_detect_progress_regression(self, service):
        """测试进度倒退检测"""
        progress_history = [
            {'date': date(2026, 1, 1), 'progress': 50},
            {'date': date(2026, 1, 8), 'progress': 60},
            {'date': date(2026, 1, 15), 'progress': 55},  # 倒退
        ]
        
        has_regression = service.detect_regression(progress_history)
        
        assert has_regression is True

    def test_detect_abnormal_velocity(self, service):
        """测试异常速度检测"""
        # 正常速度应该在10%/周左右
        historical_velocity = [10, 12, 9, 11, 10]
        current_velocity = 2  # 突然下降
        
        is_abnormal = service.detect_abnormal_velocity(
            current_velocity,
            historical_velocity,
            threshold=0.5  # 偏差50%
        )
        
        assert is_abnormal is True
