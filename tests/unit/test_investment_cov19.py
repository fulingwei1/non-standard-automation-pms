# -*- coding: utf-8 -*-
"""
第十九批 - 资源投入分析模块单元测试
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

pytest.importorskip("app.services.resource_waste_analysis.investment")


def make_instance():
    from app.services.resource_waste_analysis.investment import InvestmentAnalysisMixin

    class ConcreteInvestment(InvestmentAnalysisMixin):
        def __init__(self, db):
            self.db = db

    db = MagicMock()
    return ConcreteInvestment(db)


def _make_log(project_id=1, employee_id=10, work_hours=8.0,
              work_date=None, work_type="design"):
    log = MagicMock()
    log.project_id = project_id
    log.employee_id = employee_id
    log.work_hours = work_hours
    log.work_date = work_date or date(2024, 3, 15)
    log.work_type = work_type
    return log


def test_get_lead_resource_investment_no_logs():
    """无工作日志时返回零值"""
    inst = make_instance()
    inst.db.query.return_value.filter.return_value.all.return_value = []
    result = inst.get_lead_resource_investment(project_id=999)
    assert result['total_hours'] == 0.0
    assert result['engineer_hours'] == {}
    assert result['engineer_count'] == 0


def test_get_lead_resource_investment_total_hours():
    """正确汇总总工时"""
    inst = make_instance()
    logs = [
        _make_log(work_hours=8.0),
        _make_log(work_hours=6.0),
        _make_log(work_hours=4.0),
    ]
    inst.db.query.return_value.filter.return_value.all.return_value = logs
    # 工程师详情查询
    user = MagicMock()
    user.real_name = "张工"
    inst.db.query.return_value.filter.return_value.first.return_value = user

    result = inst.get_lead_resource_investment(project_id=1)
    assert result['total_hours'] == 18.0


def test_get_lead_resource_investment_engineer_hours():
    """按工程师分组统计工时"""
    inst = make_instance()
    logs = [
        _make_log(employee_id=1, work_hours=10.0),
        _make_log(employee_id=1, work_hours=5.0),
        _make_log(employee_id=2, work_hours=8.0),
    ]
    inst.db.query.return_value.filter.return_value.all.return_value = logs
    inst.db.query.return_value.filter.return_value.first.return_value = MagicMock()

    result = inst.get_lead_resource_investment(project_id=1)
    assert result['engineer_hours'][1] == 15.0
    assert result['engineer_hours'][2] == 8.0


def test_get_lead_resource_investment_monthly_hours():
    """按月份分组统计工时"""
    inst = make_instance()
    logs = [
        _make_log(work_hours=8.0, work_date=date(2024, 1, 15)),
        _make_log(work_hours=6.0, work_date=date(2024, 1, 20)),
        _make_log(work_hours=10.0, work_date=date(2024, 2, 10)),
    ]
    inst.db.query.return_value.filter.return_value.all.return_value = logs
    inst.db.query.return_value.filter.return_value.first.return_value = MagicMock()

    result = inst.get_lead_resource_investment(project_id=1)
    assert result['monthly_hours']['2024-01'] == 14.0
    assert result['monthly_hours']['2024-02'] == 10.0


def test_get_lead_resource_investment_stage_hours():
    """按工作类型（阶段）分组统计"""
    inst = make_instance()
    logs = [
        _make_log(work_hours=5.0, work_type='design'),
        _make_log(work_hours=3.0, work_type='design'),
        _make_log(work_hours=7.0, work_type='development'),
    ]
    inst.db.query.return_value.filter.return_value.all.return_value = logs
    inst.db.query.return_value.filter.return_value.first.return_value = MagicMock()

    result = inst.get_lead_resource_investment(project_id=1)
    assert result['stage_hours']['design'] == 8.0
    assert result['stage_hours']['development'] == 7.0


def test_get_lead_resource_investment_engineer_count():
    """正确统计工程师数量"""
    inst = make_instance()
    logs = [
        _make_log(employee_id=1, work_hours=4.0),
        _make_log(employee_id=2, work_hours=4.0),
        _make_log(employee_id=3, work_hours=4.0),
    ]
    inst.db.query.return_value.filter.return_value.all.return_value = logs
    inst.db.query.return_value.filter.return_value.first.return_value = MagicMock()

    result = inst.get_lead_resource_investment(project_id=1)
    assert result['engineer_count'] == 3


def test_get_lead_resource_investment_returns_dict_keys():
    """返回结果包含所有必需字段"""
    inst = make_instance()
    inst.db.query.return_value.filter.return_value.all.return_value = []
    result = inst.get_lead_resource_investment(project_id=1)
    for key in ['total_hours', 'engineer_hours', 'monthly_hours',
                'stage_hours', 'estimated_cost', 'engineer_count']:
        assert key in result
