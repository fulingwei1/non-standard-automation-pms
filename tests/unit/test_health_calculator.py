# -*- coding: utf-8 -*-
"""
项目健康度计算器单元测试

测试 HealthCalculator 的核心功能:
- 健康度计算（H1/H2/H3/H4）
- 阻塞检测
- 风险检测
- 批量计算
- 健康度详情
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from sqlalchemy.orm import Session

from app.services.health_calculator import HealthCalculator
from app.models.enums import ProjectHealthEnum


class TestHealthCalculatorInit:
    """健康度计算器初始化测试"""

    def test_init(self, db_session: Session):
        """测试计算器初始化"""
        calculator = HealthCalculator(db_session)
        assert calculator.db == db_session


class TestCalculateHealth:
    """计算健康度测试"""

    def test_calculate_health_closed_project(self, db_session: Session):
        """测试已完结项目返回H4"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST30'  # 已结项

        result = calculator.calculate_health(mock_project)
        assert result == ProjectHealthEnum.H4.value

    def test_calculate_health_cancelled_project(self, db_session: Session):
        """测试已取消项目返回H4"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST99'  # 项目取消

        result = calculator.calculate_health(mock_project)
        assert result == ProjectHealthEnum.H4.value

    def test_calculate_health_blocked_status(self, db_session: Session):
        """测试阻塞状态项目返回H3"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST14'  # 缺料阻塞

        result = calculator.calculate_health(mock_project)
        assert result == ProjectHealthEnum.H3.value

    def test_calculate_health_tech_blocked_status(self, db_session: Session):
        """测试技术阻塞状态项目返回H3"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST19'  # 技术阻塞

        result = calculator.calculate_health(mock_project)
        assert result == ProjectHealthEnum.H3.value

    def test_calculate_health_rectification_status(self, db_session: Session):
        """测试整改中状态项目返回H2"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST22'  # FAT整改中
        mock_project.planned_end_date = None

        result = calculator.calculate_health(mock_project)
        assert result == ProjectHealthEnum.H2.value

    def test_calculate_health_normal_project(self, db_session: Session):
        """测试正常项目返回H1"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST10'  # 正常状态
        mock_project.planned_end_date = date.today() + timedelta(days=30)  # 交期还有30天
        mock_project.actual_start_date = None
        mock_project.planned_start_date = None
        mock_project.progress_pct = Decimal('50')

        result = calculator.calculate_health(mock_project)
        assert result == ProjectHealthEnum.H1.value


class TestIsClosedCheck:
    """已完结检查测试"""

    def test_is_closed_st30(self, db_session: Session):
        """测试ST30状态为已完结"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.status = 'ST30'

        result = calculator._is_closed(mock_project)
        assert result is True

    def test_is_closed_st99(self, db_session: Session):
        """测试ST99状态为已完结"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.status = 'ST99'

        result = calculator._is_closed(mock_project)
        assert result is True

    def test_is_closed_normal_status(self, db_session: Session):
        """测试正常状态不是已完结"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.status = 'ST10'

        result = calculator._is_closed(mock_project)
        assert result is False


class TestIsBlockedCheck:
    """阻塞检查测试"""

    def test_is_blocked_by_status_st14(self, db_session: Session):
        """测试ST14状态为阻塞"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST14'

        result = calculator._is_blocked(mock_project)
        assert result is True

    def test_is_blocked_by_status_st19(self, db_session: Session):
        """测试ST19状态为阻塞"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST19'

        result = calculator._is_blocked(mock_project)
        assert result is True

    def test_is_blocked_normal_status(self, db_session: Session):
        """测试正常状态非阻塞（需要检查其他条件）"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999  # 不存在的项目ID，不会有阻塞任务
        mock_project.status = 'ST10'

        result = calculator._is_blocked(mock_project)
        assert result is False


class TestHasRisksCheck:
    """风险检查测试"""

    def test_has_risks_rectification_st22(self, db_session: Session):
        """测试FAT整改中状态有风险"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST22'

        result = calculator._has_risks(mock_project)
        assert result is True

    def test_has_risks_rectification_st26(self, db_session: Session):
        """测试SAT整改中状态有风险"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST26'

        result = calculator._has_risks(mock_project)
        assert result is True

    def test_has_risks_normal_status(self, db_session: Session):
        """测试正常状态无风险"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999
        mock_project.status = 'ST10'
        mock_project.planned_end_date = date.today() + timedelta(days=30)  # 交期还有30天
        mock_project.actual_start_date = None
        mock_project.planned_start_date = None
        mock_project.progress_pct = Decimal('50')

        result = calculator._has_risks(mock_project)
        assert result is False


class TestDeadlineApproachingCheck:
    """交期临近检查测试"""

    def test_deadline_approaching_within_7_days(self, db_session: Session):
        """测试交期在7天内"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.planned_end_date = date.today() + timedelta(days=5)

        result = calculator._is_deadline_approaching(mock_project, days=7)
        assert result is True

    def test_deadline_approaching_today(self, db_session: Session):
        """测试交期是今天"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.planned_end_date = date.today()

        result = calculator._is_deadline_approaching(mock_project, days=7)
        assert result is True

    def test_deadline_not_approaching(self, db_session: Session):
        """测试交期还远"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.planned_end_date = date.today() + timedelta(days=30)

        result = calculator._is_deadline_approaching(mock_project, days=7)
        assert result is False

    def test_deadline_already_passed(self, db_session: Session):
        """测试交期已过"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.planned_end_date = date.today() - timedelta(days=5)

        result = calculator._is_deadline_approaching(mock_project, days=7)
        assert result is False

    def test_deadline_no_end_date(self, db_session: Session):
        """测试没有交期"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.planned_end_date = None

        result = calculator._is_deadline_approaching(mock_project, days=7)
        assert result is False


class TestScheduleVarianceCheck:
    """进度偏差检查测试"""

    def test_schedule_variance_no_dates(self, db_session: Session):
        """测试没有日期时返回False"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.planned_end_date = None
        mock_project.actual_start_date = None

        result = calculator._has_schedule_variance(mock_project)
        assert result is False

    def test_schedule_variance_no_actual_start(self, db_session: Session):
        """测试没有实际开始日期时返回False"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = None

        result = calculator._has_schedule_variance(mock_project)
        assert result is False

    def test_schedule_variance_within_threshold(self, db_session: Session):
        """测试进度偏差在阈值内"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.planned_start_date = date.today() - timedelta(days=50)
        mock_project.planned_end_date = date.today() + timedelta(days=50)
        mock_project.actual_start_date = date.today() - timedelta(days=50)
        mock_project.progress_pct = Decimal('45')  # 接近50%计划进度

        result = calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    def test_schedule_variance_exceeds_threshold(self, db_session: Session):
        """测试进度偏差超过阈值"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.planned_start_date = date.today() - timedelta(days=50)
        mock_project.planned_end_date = date.today() + timedelta(days=50)
        mock_project.actual_start_date = date.today() - timedelta(days=50)
        mock_project.progress_pct = Decimal('20')  # 远低于50%计划进度

        result = calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is True


class TestHasBlockedCriticalTasks:
    """阻塞任务检查测试"""

    def test_no_blocked_tasks(self, db_session: Session):
        """测试没有阻塞任务"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999  # 不存在的项目

        result = calculator._has_blocked_critical_tasks(mock_project)
        assert result is False


class TestHasBlockingIssues:
    """阻塞问题检查测试"""

    def test_no_blocking_issues(self, db_session: Session):
        """测试没有阻塞问题"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999  # 不存在的项目

        result = calculator._has_blocking_issues(mock_project)
        assert result is False


class TestHasCriticalShortageAlerts:
    """严重缺料预警检查测试"""

    def test_no_critical_shortage_alerts(self, db_session: Session):
        """测试没有严重缺料预警"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999  # 不存在的项目

        result = calculator._has_critical_shortage_alerts(mock_project)
        assert result is False


class TestHasOverdueMilestones:
    """逾期里程碑检查测试"""

    def test_no_overdue_milestones(self, db_session: Session):
        """测试没有逾期里程碑"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999  # 不存在的项目

        result = calculator._has_overdue_milestones(mock_project)
        assert result is False


class TestHasShortageWarnings:
    """缺料预警检查测试"""

    def test_no_shortage_warnings(self, db_session: Session):
        """测试没有缺料预警"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999  # 不存在的项目

        result = calculator._has_shortage_warnings(mock_project)
        assert result is False


class TestHasHighPriorityIssues:
    """高优先级问题检查测试"""

    def test_no_high_priority_issues(self, db_session: Session):
        """测试没有高优先级问题"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999  # 不存在的项目

        result = calculator._has_high_priority_issues(mock_project)
        assert result is False


class TestCalculateAndUpdate:
    """计算并更新健康度测试"""

    def test_calculate_and_update_no_change(self, db_session: Session):
        """测试健康度没有变化时不更新"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PJ250101001'
        mock_project.health = ProjectHealthEnum.H4.value
        mock_project.status = 'ST30'  # 已完结
        mock_project.stage = 'S9'

        result = calculator.calculate_and_update(mock_project, auto_save=False)

        assert result['project_id'] == 1
        assert result['project_code'] == 'PJ250101001'
        assert result['old_health'] == ProjectHealthEnum.H4.value
        assert result['new_health'] == ProjectHealthEnum.H4.value
        assert result['changed'] is False

    def test_calculate_and_update_with_change(self, db_session: Session):
        """测试健康度变化时更新"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PJ250101001'
        mock_project.health = ProjectHealthEnum.H1.value  # 原来是正常
        mock_project.status = 'ST30'  # 现在已完结
        mock_project.stage = 'S9'

        result = calculator.calculate_and_update(mock_project, auto_save=False)

        assert result['project_id'] == 1
        assert result['old_health'] == ProjectHealthEnum.H1.value
        assert result['new_health'] == ProjectHealthEnum.H4.value
        assert result['changed'] is True


class TestBatchCalculate:
    """批量计算健康度测试"""

    def test_batch_calculate_empty(self, db_session: Session):
        """测试没有项目时批量计算"""
        calculator = HealthCalculator(db_session)

        result = calculator.batch_calculate(project_ids=[99999])

        assert result['total'] == 0
        assert result['updated'] == 0
        assert result['unchanged'] == 0
        assert result['details'] == []

    def test_batch_calculate_structure(self, db_session: Session):
        """测试批量计算返回结构"""
        calculator = HealthCalculator(db_session)

        result = calculator.batch_calculate()

        assert 'total' in result
        assert 'updated' in result
        assert 'unchanged' in result
        assert 'details' in result
        assert isinstance(result['total'], int)
        assert isinstance(result['updated'], int)
        assert isinstance(result['unchanged'], int)
        assert isinstance(result['details'], list)


class TestGetHealthDetails:
    """获取健康度详情测试"""

    def test_get_health_details_structure(self, db_session: Session):
        """测试健康度详情结构"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999
        mock_project.project_code = 'PJ250101001'
        mock_project.health = ProjectHealthEnum.H1.value
        mock_project.status = 'ST10'
        mock_project.stage = 'S3'
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = None
        mock_project.planned_start_date = None
        mock_project.progress_pct = Decimal('50')

        result = calculator.get_health_details(mock_project)

        assert 'project_id' in result
        assert 'project_code' in result
        assert 'current_health' in result
        assert 'calculated_health' in result
        assert 'status' in result
        assert 'stage' in result
        assert 'checks' in result
        assert 'statistics' in result

    def test_get_health_details_checks_structure(self, db_session: Session):
        """测试健康度详情的检查项结构"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999
        mock_project.project_code = 'PJ250101001'
        mock_project.health = ProjectHealthEnum.H1.value
        mock_project.status = 'ST10'
        mock_project.stage = 'S3'
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = None
        mock_project.planned_start_date = None
        mock_project.progress_pct = Decimal('50')

        result = calculator.get_health_details(mock_project)
        checks = result['checks']

        assert 'is_closed' in checks
        assert 'is_blocked' in checks
        assert 'has_risks' in checks
        assert 'has_blocked_critical_tasks' in checks
        assert 'has_blocking_issues' in checks
        assert 'has_critical_shortage_alerts' in checks
        assert 'is_deadline_approaching' in checks
        assert 'has_overdue_milestones' in checks
        assert 'has_shortage_warnings' in checks
        assert 'has_high_priority_issues' in checks
        assert 'has_schedule_variance' in checks

    def test_get_health_details_statistics_structure(self, db_session: Session):
        """测试健康度详情的统计项结构"""
        calculator = HealthCalculator(db_session)
        mock_project = MagicMock()
        mock_project.id = 99999
        mock_project.project_code = 'PJ250101001'
        mock_project.health = ProjectHealthEnum.H1.value
        mock_project.status = 'ST10'
        mock_project.stage = 'S3'
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = None
        mock_project.planned_start_date = None
        mock_project.progress_pct = Decimal('50')

        result = calculator.get_health_details(mock_project)
        statistics = result['statistics']

        assert 'blocked_tasks' in statistics
        assert 'blocking_issues' in statistics
        assert 'overdue_milestones' in statistics
        assert 'active_alerts' in statistics
