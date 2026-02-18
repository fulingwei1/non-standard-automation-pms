# -*- coding: utf-8 -*-
"""
第十九批 - 岗位职责任务生成服务单元测试
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.job_duty_task_service")


def _make_template(frequency='DAILY', day_of_week=None, day_of_month=None,
                   month_of_year=None, generate_before_days=0, position_id=1,
                   department_id=None, duty_name="日报", duty_description="每日报告",
                   estimated_hours=1.0, deadline_offset_days=1,
                   default_priority='MEDIUM', is_active=True):
    t = MagicMock()
    t.frequency = frequency
    t.day_of_week = day_of_week
    t.day_of_month = day_of_month
    t.month_of_year = month_of_year
    t.generate_before_days = generate_before_days
    t.position_id = position_id
    t.department_id = department_id
    t.duty_name = duty_name
    t.duty_description = duty_description
    t.estimated_hours = estimated_hours
    t.deadline_offset_days = deadline_offset_days
    t.default_priority = default_priority
    t.id = 1
    return t


def test_should_generate_daily():
    """DAILY 频率每天都应生成"""
    from app.services.job_duty_task_service import should_generate_task
    template = _make_template(frequency='DAILY')
    today = date(2024, 3, 15)
    should, target = should_generate_task(template, today)
    assert should is True
    assert target == today


def test_should_generate_daily_with_advance_days():
    """DAILY 频率带提前天数时目标日期正确"""
    from app.services.job_duty_task_service import should_generate_task
    template = _make_template(frequency='DAILY', generate_before_days=2)
    today = date(2024, 3, 15)
    should, target = should_generate_task(template, today)
    assert should is True
    assert target == date(2024, 3, 17)


def test_should_generate_weekly_on_target_day():
    """WEEKLY 频率在目标星期几时应生成"""
    from app.services.job_duty_task_service import should_generate_task
    # 2024-03-15 是星期五 (weekday=4)
    today = date(2024, 3, 15)
    # day_of_week=5 表示星期五（1-indexed, 内部判断 (5-4-1)%7=0）
    template = _make_template(frequency='WEEKLY', day_of_week=5)
    should, target = should_generate_task(template, today)
    assert should is True


def test_should_generate_weekly_not_target_day():
    """WEEKLY 频率不在目标日期且超出提前范围时不生成"""
    from app.services.job_duty_task_service import should_generate_task
    today = date(2024, 3, 15)  # 星期五 (weekday=4)
    # day_of_week=3 (Wednesday): days_until_target = (3-4-1)%7 = 5
    # generate_before_days=2，5 > 2，不在提前生成范围内
    template = _make_template(frequency='WEEKLY', day_of_week=3, generate_before_days=2)
    should, target = should_generate_task(template, today)
    assert should is False


def test_should_not_generate_unknown_frequency():
    """未知频率不生成"""
    from app.services.job_duty_task_service import should_generate_task
    template = _make_template(frequency='UNKNOWN')
    should, target = should_generate_task(template, date.today())
    assert should is False


def test_find_template_users_by_department():
    """根据 department_id 查找用户（User 无 position_id 时走部门路径）"""
    from app.services.job_duty_task_service import find_template_users
    from app.models.user import User
    db = MagicMock()
    # User 没有 position_id，所以走 department_id 路径
    template = _make_template(position_id=None, department_id=5)

    user = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [user]

    if hasattr(User, 'department_id'):
        users = find_template_users(db, template)
        assert len(users) == 1
    else:
        # User 也没有 department_id，结果为空列表
        users = find_template_users(db, template)
        assert users == []


def test_create_task_from_template():
    """根据模板创建任务"""
    from app.services.job_duty_task_service import create_task_from_template
    db = MagicMock()
    template = _make_template(duty_name="周报", deadline_offset_days=3, estimated_hours=2.0)
    user = MagicMock()
    user.id = 5
    user.real_name = "李四"
    user.username = "lisi"

    def gen_code(db):
        return "JD-001"

    target_date = date(2024, 3, 15)
    task = create_task_from_template(db, template, user, target_date, gen_code)

    assert task.task_code == "JD-001"
    assert task.title == "周报"
    assert task.assignee_id == 5
    assert task.task_type == 'JOB_DUTY'
    assert task.status == 'PENDING'
    assert task.deadline == target_date + timedelta(days=3)


def test_check_task_exists_true():
    """任务已存在时返回 True"""
    from app.services.job_duty_task_service import check_task_exists
    db = MagicMock()
    template = _make_template()
    db.query.return_value.filter.return_value.first.return_value = MagicMock()
    result = check_task_exists(db, template, date(2024, 3, 15))
    assert result is True


def test_check_task_exists_false():
    """任务不存在时返回 False"""
    from app.services.job_duty_task_service import check_task_exists
    db = MagicMock()
    template = _make_template()
    db.query.return_value.filter.return_value.first.return_value = None
    result = check_task_exists(db, template, date(2024, 3, 15))
    assert result is False
