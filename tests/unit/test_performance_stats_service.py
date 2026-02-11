# -*- coding: utf-8 -*-
"""Tests for performance_stats_service.py"""
from unittest.mock import MagicMock, patch
from datetime import date

from app.services.performance_stats_service import PerformanceStatsService


class TestGetUserPerformanceStats:
    def setup_method(self):
        self.db = MagicMock()
        self.service = PerformanceStatsService(self.db)

    def test_user_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.get_user_performance_stats(999)
        assert result == {'error': '用户不存在'}

    def test_basic_stats(self):
        user = MagicMock(id=1, real_name="张三", username="zhangsan")
        ts = MagicMock(user_id=1, project_id=1, hours=8, overtime_type="NORMAL",
                       work_date=MagicMock(strftime=MagicMock(return_value="2025-01")))

        self.db.query.return_value.filter.return_value.first.side_effect = [
            user,  # user query
            MagicMock(project_code="P001", project_name="项目A"),  # project
        ]
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        self.db.query.return_value.filter.return_value.scalar.return_value = 100

        result = self.service.get_user_performance_stats(1)
        assert result['user_id'] == 1
        assert result['total_hours'] == 8.0


class TestGetDepartmentPerformanceStats:
    def setup_method(self):
        self.db = MagicMock()
        self.service = PerformanceStatsService(self.db)

    def test_department_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.get_department_performance_stats(999)
        assert result == {'error': '部门不存在'}

    def test_empty_department(self):
        dept = MagicMock(id=1, name="技术部")
        self.db.query.return_value.filter.return_value.first.return_value = dept
        self.db.query.return_value.filter.return_value.all.side_effect = [
            [],  # no users
        ]
        result = self.service.get_department_performance_stats(1)
        assert result['total_hours'] == 0


class TestAnalyzeSkillExpertise:
    def setup_method(self):
        self.db = MagicMock()
        self.service = PerformanceStatsService(self.db)

    def test_no_timesheets(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.service.analyze_skill_expertise(1)
        assert result['total_hours'] == 0

    def test_skill_detection(self):
        ts = MagicMock(user_id=1, hours=8, work_content="PLC程序调试", overtime_type="NORMAL",
                       work_date=MagicMock(strftime=MagicMock(return_value="2025-01")))
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        result = self.service.analyze_skill_expertise(1)
        assert result['skill_distribution']['电气']['hours'] == 8.0
        assert result['primary_skill'] == '电气'
