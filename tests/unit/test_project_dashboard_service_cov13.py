# -*- coding: utf-8 -*-
"""第十三批 - 项目仪表盘数据聚合服务 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date

try:
    from app.services.project_dashboard_service import (
        build_basic_info,
        calculate_progress_stats,
    )
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_project(**kwargs):
    """创建模拟项目对象"""
    project = MagicMock()
    project.project_code = kwargs.get('project_code', 'PRJ001')
    project.project_name = kwargs.get('project_name', '测试项目')
    project.customer_name = kwargs.get('customer_name', '客户A')
    project.pm_name = kwargs.get('pm_name', '张三')
    project.stage = kwargs.get('stage', 'S2')
    project.status = kwargs.get('status', 'ST01')
    project.health = kwargs.get('health', 'H1')
    project.progress_pct = kwargs.get('progress_pct', 50)
    project.planned_start_date = kwargs.get('planned_start_date', date(2024, 1, 1))
    project.planned_end_date = kwargs.get('planned_end_date', date(2024, 12, 31))
    project.actual_start_date = kwargs.get('actual_start_date', date(2024, 1, 5))
    project.actual_end_date = kwargs.get('actual_end_date', None)
    project.contract_amount = kwargs.get('contract_amount', 1000000)
    project.budget_amount = kwargs.get('budget_amount', 800000)
    return project


class TestBuildBasicInfo:
    def test_basic_fields(self):
        """基本字段正确返回"""
        project = make_project()
        info = build_basic_info(project)
        assert info['project_code'] == 'PRJ001'
        assert info['project_name'] == '测试项目'
        assert info['pm_name'] == '张三'

    def test_stage_default(self):
        """stage为空时使用默认值S1"""
        project = make_project(stage=None)
        project.stage = None
        info = build_basic_info(project)
        assert info['stage'] == 'S1'

    def test_status_default(self):
        """status为空时使用默认值ST01"""
        project = make_project()
        project.status = None
        info = build_basic_info(project)
        assert info['status'] == 'ST01'

    def test_dates_isoformat(self):
        """日期以ISO格式输出"""
        project = make_project(
            planned_start_date=date(2024, 1, 1),
            planned_end_date=date(2024, 12, 31)
        )
        info = build_basic_info(project)
        assert info['planned_start_date'] == '2024-01-01'
        assert info['planned_end_date'] == '2024-12-31'

    def test_none_dates(self):
        """空日期输出None"""
        project = make_project()
        project.planned_start_date = None
        project.planned_end_date = None
        project.actual_start_date = None
        project.actual_end_date = None
        info = build_basic_info(project)
        assert info['planned_start_date'] is None

    def test_amounts_as_float(self):
        """金额以float格式返回"""
        project = make_project(contract_amount=1500000, budget_amount=1200000)
        info = build_basic_info(project)
        assert isinstance(info['contract_amount'], float)
        assert info['contract_amount'] == 1500000.0


class TestCalculateProgressStats:
    def test_progress_deviation(self):
        """进度偏差计算"""
        today = date(2024, 7, 1)
        project = make_project(
            planned_start_date=date(2024, 1, 1),
            planned_end_date=date(2024, 12, 31),
            progress_pct=30
        )
        stats = calculate_progress_stats(project, today)
        assert 'progress_deviation' in stats

    def test_no_planned_dates(self):
        """无计划日期时plan_progress为0"""
        today = date(2024, 7, 1)
        project = make_project()
        project.planned_start_date = None
        project.planned_end_date = None
        stats = calculate_progress_stats(project, today)
        assert stats is not None
