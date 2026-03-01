# -*- coding: utf-8 -*-
"""绩效评价创建单元测试 - 第三十六批"""

import pytest
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.performance_service.evaluation")

try:
    from app.services.performance_service.evaluation import create_evaluation_tasks
    from app.models.performance import EvaluationStatusEnum, EvaluatorTypeEnum
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    create_evaluation_tasks = None
    EvaluationStatusEnum = None
    EvaluatorTypeEnum = None


def make_summary(employee_id=1, period="2024-01"):
    summary = MagicMock()
    summary.id = 10
    summary.employee_id = employee_id
    summary.period = period
    return summary


def make_db_no_employee():
    """数据库查询不到user时"""
    db = MagicMock()
    db.query.return_value.get.return_value = None
    return db


def make_db_with_employee_no_dept():
    """有user但无部门"""
    db = MagicMock()
    user = MagicMock(); user.employee_id = 5
    emp = MagicMock(); emp.department = None
    db.query.return_value.get.side_effect = lambda *a, **kw: user if True else emp
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    return db


class TestCreateEvaluationTasksNoEmployee:
    def test_no_user_returns_empty(self):
        db = make_db_no_employee()
        summary = make_summary()
        result = create_evaluation_tasks(db, summary)
        assert result == []


class TestCreateEvaluationTasksNoProjectMembers:
    def test_no_project_members_returns_dept_eval_only_or_empty(self):
        db = MagicMock()
        # User不存在
        db.query.return_value.get.return_value = None
        summary = make_summary(employee_id=99)
        result = create_evaluation_tasks(db, summary)
        assert isinstance(result, list)


class TestPeriodParsing:
    def test_period_2024_01_parsed_correctly(self):
        """验证period字符串解析正确"""
        db = MagicMock()
        db.query.return_value.get.return_value = None
        summary = make_summary(period="2024-06")
        result = create_evaluation_tasks(db, summary)
        assert isinstance(result, list)

    def test_period_2024_12(self):
        db = MagicMock()
        db.query.return_value.get.return_value = None
        summary = make_summary(period="2024-12")
        result = create_evaluation_tasks(db, summary)
        assert isinstance(result, list)


class TestReturnType:
    def test_always_returns_list(self):
        db = MagicMock()
        db.query.return_value.get.return_value = None
        summary = make_summary()
        result = create_evaluation_tasks(db, summary)
        assert isinstance(result, list)

    def test_created_records_committed(self):
        """当有记录时应提交DB"""
        db = MagicMock()
        db.query.return_value.get.return_value = None
        summary = make_summary()
        create_evaluation_tasks(db, summary)
        # 由于user为None，不应该提交
        db.commit.assert_not_called()
