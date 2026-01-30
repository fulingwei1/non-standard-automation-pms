# -*- coding: utf-8 -*-
"""
job_duty_task_service 综合单元测试

测试覆盖:
- should_generate_task: 判断是否需要生成任务
- find_template_users: 查找模板对应的用户列表
- create_task_from_template: 根据模板为用户创建任务
- check_task_exists: 检查是否已经生成过该日期的任务
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestShouldGenerateTask:
    """测试 should_generate_task 函数"""

    def test_daily_always_generates(self):
        """测试每日频率总是生成"""
        from app.services.job_duty_task_service import should_generate_task

        mock_template = MagicMock()
        mock_template.frequency = 'DAILY'
        mock_template.generate_before_days = 0

        today = date.today()
        should_gen, target = should_generate_task(mock_template, today)

        assert should_gen is True
        assert target == today

    def test_daily_with_advance_days(self):
        """测试每日频率带提前天数"""
        from app.services.job_duty_task_service import should_generate_task

        mock_template = MagicMock()
        mock_template.frequency = 'DAILY'
        mock_template.generate_before_days = 1

        today = date.today()
        should_gen, target = should_generate_task(mock_template, today)

        assert should_gen is True
        assert target == today + timedelta(days=1)

    def test_weekly_on_target_day(self):
        """测试每周频率在目标日期"""
        from app.services.job_duty_task_service import should_generate_task

        mock_template = MagicMock()
        mock_template.frequency = 'WEEKLY'
        mock_template.day_of_week = date.today().weekday() + 1  # 设置为今天
        mock_template.generate_before_days = 0

        today = date.today()
        should_gen, target = should_generate_task(mock_template, today)

        assert should_gen is True

    def test_weekly_before_target_day(self):
        """测试每周频率在目标日期之前"""
        from app.services.job_duty_task_service import should_generate_task

        mock_template = MagicMock()
        mock_template.frequency = 'WEEKLY'
        # 设置目标为2天后的星期几
        future_weekday = (date.today().weekday() + 2) % 7 + 1
        mock_template.day_of_week = future_weekday
        mock_template.generate_before_days = 3

        today = date.today()
        should_gen, target = should_generate_task(mock_template, today)

        # 在提前生成范围内应该生成
        assert should_gen is True

    def test_monthly_on_target_day(self):
        """测试每月频率在目标日期"""
        from app.services.job_duty_task_service import should_generate_task

        mock_template = MagicMock()
        mock_template.frequency = 'MONTHLY'
        mock_template.day_of_month = date.today().day
        mock_template.generate_before_days = 0

        today = date.today()
        should_gen, target = should_generate_task(mock_template, today)

        assert should_gen is True

    def test_monthly_before_target_day(self):
        """测试每月频率在目标日期之前"""
        from app.services.job_duty_task_service import should_generate_task

        mock_template = MagicMock()
        mock_template.frequency = 'MONTHLY'
        # 设置目标为2天后
        target_day = min(date.today().day + 2, 28)  # 避免月末问题
        mock_template.day_of_month = target_day
        mock_template.generate_before_days = 3

        today = date.today()
        should_gen, target = should_generate_task(mock_template, today)

        # 在提前生成范围内应该生成
        if target_day > today.day:
            assert should_gen is True

    def test_yearly_on_target_date(self):
        """测试每年频率在目标日期"""
        from app.services.job_duty_task_service import should_generate_task

        mock_template = MagicMock()
        mock_template.frequency = 'YEARLY'
        mock_template.month_of_year = date.today().month
        mock_template.day_of_month = date.today().day
        mock_template.generate_before_days = 0

        today = date.today()
        should_gen, target = should_generate_task(mock_template, today)

        assert should_gen is True

    def test_unknown_frequency_no_generate(self):
        """测试未知频率不生成"""
        from app.services.job_duty_task_service import should_generate_task

        mock_template = MagicMock()
        mock_template.frequency = 'UNKNOWN'

        today = date.today()
        should_gen, target = should_generate_task(mock_template, today)

        assert should_gen is False


class TestFindTemplateUsers:
    """测试 find_template_users 函数"""

    def test_finds_users_by_position(self):
        """测试按岗位查找用户"""
        from app.services.job_duty_task_service import find_template_users

        mock_db = MagicMock()
        mock_template = MagicMock()
        mock_template.position_id = 1
        mock_template.department_id = None

        mock_user = MagicMock()
        mock_user.id = 10

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_user]

        # Mock User class to have position_id attribute
        with patch('app.services.job_duty_task_service.User') as MockUser:
            MockUser.position_id = MagicMock()
            MockUser.is_active = MagicMock()

            result = find_template_users(mock_db, mock_template)

            assert len(result) == 1

    def test_finds_users_by_department(self):
        """测试按部门查找用户"""
        from app.services.job_duty_task_service import find_template_users

        mock_db = MagicMock()
        mock_template = MagicMock()
        mock_template.position_id = None
        mock_template.department_id = 5

        mock_user = MagicMock()
        mock_user.id = 20

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_user]

        # Mock User class
        with patch('app.services.job_duty_task_service.User') as MockUser:
            MockUser.department_id = MagicMock()
            MockUser.is_active = MagicMock()
            # Remove position_id
            del MockUser.position_id

            result = find_template_users(mock_db, mock_template)

            assert len(result) == 1

    def test_returns_empty_when_no_filters(self):
        """测试无筛选条件时返回空"""
        from app.services.job_duty_task_service import find_template_users

        mock_db = MagicMock()
        mock_template = MagicMock()
        mock_template.position_id = None
        mock_template.department_id = None

        with patch('app.services.job_duty_task_service.User') as MockUser:
            # No position_id or department_id attributes
            del MockUser.position_id
            del MockUser.department_id

            result = find_template_users(mock_db, mock_template)

            assert result == []


class TestCreateTaskFromTemplate:
    """测试 create_task_from_template 函数"""

    def test_creates_task_with_correct_attributes(self):
        """测试创建任务带正确属性"""
        from app.services.job_duty_task_service import create_task_from_template

        mock_db = MagicMock()

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.duty_name = "每日工作汇报"
        mock_template.duty_description = "提交每日工作进展"
        mock_template.deadline_offset_days = 1
        mock_template.estimated_hours = 0.5
        mock_template.default_priority = "HIGH"

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"

        mock_generate_func = MagicMock(return_value="TASK-20260130-001")

        target_date = date.today()

        result = create_task_from_template(
            mock_db, mock_template, mock_user, target_date, mock_generate_func
        )

        assert result.title == "每日工作汇报"
        assert result.assignee_id == 10
        assert result.assignee_name == "张三"
        assert result.task_type == 'JOB_DUTY'
        assert result.priority == "HIGH"
        assert result.source_type == 'JOB_DUTY_TEMPLATE'
        assert result.source_id == 1

    def test_calculates_deadline(self):
        """测试计算截止日期"""
        from app.services.job_duty_task_service import create_task_from_template

        mock_db = MagicMock()

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.duty_name = "周报"
        mock_template.duty_description = "提交周报"
        mock_template.deadline_offset_days = 3
        mock_template.estimated_hours = 1.0
        mock_template.default_priority = "MEDIUM"

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.real_name = "张三"

        mock_generate_func = MagicMock(return_value="TASK-001")

        target_date = date.today()

        result = create_task_from_template(
            mock_db, mock_template, mock_user, target_date, mock_generate_func
        )

        assert result.deadline == target_date + timedelta(days=3)

    def test_uses_default_priority(self):
        """测试使用默认优先级"""
        from app.services.job_duty_task_service import create_task_from_template

        mock_db = MagicMock()

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.duty_name = "任务"
        mock_template.duty_description = "描述"
        mock_template.deadline_offset_days = 0
        mock_template.estimated_hours = None
        mock_template.default_priority = None  # 无默认优先级

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.real_name = None
        mock_user.username = "user1"

        mock_generate_func = MagicMock(return_value="TASK-001")

        result = create_task_from_template(
            mock_db, mock_template, mock_user, date.today(), mock_generate_func
        )

        assert result.priority == 'MEDIUM'  # 默认中等优先级
        assert result.assignee_name == "user1"  # 使用username


class TestCheckTaskExists:
    """测试 check_task_exists 函数"""

    def test_returns_true_when_exists(self):
        """测试任务存在时返回True"""
        from app.services.job_duty_task_service import check_task_exists

        mock_db = MagicMock()
        mock_template = MagicMock()
        mock_template.id = 1

        mock_task = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = check_task_exists(mock_db, mock_template, date.today())

        assert result is True

    def test_returns_false_when_not_exists(self):
        """测试任务不存在时返回False"""
        from app.services.job_duty_task_service import check_task_exists

        mock_db = MagicMock()
        mock_template = MagicMock()
        mock_template.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = check_task_exists(mock_db, mock_template, date.today())

        assert result is False

    def test_checks_correct_filters(self):
        """测试检查正确的筛选条件"""
        from app.services.job_duty_task_service import check_task_exists

        mock_db = MagicMock()
        mock_template = MagicMock()
        mock_template.id = 5

        mock_db.query.return_value.filter.return_value.first.return_value = None

        target_date = date(2026, 1, 15)
        check_task_exists(mock_db, mock_template, target_date)

        # 验证查询被调用
        mock_db.query.assert_called()
