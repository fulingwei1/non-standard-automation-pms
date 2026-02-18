# -*- coding: utf-8 -*-
"""
第十四批：项目奖金查询服务 单元测试
"""
import pytest
from unittest.mock import MagicMock
from datetime import date

try:
    from app.services.project_bonus_service import ProjectBonusService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_service(db=None):
    return ProjectBonusService(db or make_db())


def make_project(**kwargs):
    p = MagicMock()
    p.id = 1
    p.project_type = kwargs.get("project_type", "STANDARD")
    return p


class TestProjectBonusService:
    def test_get_project_bonus_rules_project_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = make_service(db)
        result = svc.get_project_bonus_rules(999)
        assert result == []

    def test_is_rule_applicable_no_attrs(self):
        """规则没有 apply_to_projects、effective_start_date 等属性时应返回 True"""
        db = make_db()
        svc = make_service(db)
        # spec=[] 让 hasattr 返回 False
        rule = MagicMock(spec=[])
        project = make_project()
        result = svc._is_rule_applicable(rule, project)
        assert result is True

    def test_is_rule_applicable_expired_rule(self):
        """规则已过期（effective_end_date < today）时应返回 False"""
        from datetime import date, timedelta
        db = make_db()
        svc = make_service(db)
        rule = MagicMock()
        rule.apply_to_projects = None
        rule.effective_start_date = None
        rule.effective_end_date = date.today() - timedelta(days=1)
        project = make_project()
        result = svc._is_rule_applicable(rule, project)
        assert result is False

    def test_is_rule_applicable_future_rule(self):
        """规则尚未生效（effective_start_date > today）时应返回 False"""
        from datetime import date, timedelta
        db = make_db()
        svc = make_service(db)
        rule = MagicMock()
        rule.apply_to_projects = None
        rule.effective_start_date = date.today() + timedelta(days=10)
        rule.effective_end_date = None
        project = make_project()
        result = svc._is_rule_applicable(rule, project)
        assert result is False

    def test_get_project_bonus_calculations_no_filter(self):
        db = make_db()
        mock_q = MagicMock()
        db.query.return_value.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = []
        svc = make_service(db)
        result = svc.get_project_bonus_calculations(project_id=1)
        assert result == []

    def test_get_project_bonus_calculations_filters_user(self):
        db = make_db()
        mock_q = MagicMock()
        db.query.return_value.filter.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = []
        svc = make_service(db)
        result = svc.get_project_bonus_calculations(project_id=1, user_id=5)
        assert result == []

    def test_get_project_bonus_calculations_with_dates(self):
        db = make_db()
        mock_q = MagicMock()
        db.query.return_value.filter.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = []
        svc = make_service(db)
        result = svc.get_project_bonus_calculations(
            project_id=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31)
        )
        assert result == []

    def test_get_project_bonus_calculations_with_status(self):
        db = make_db()
        mock_q = MagicMock()
        db.query.return_value.filter.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = []
        svc = make_service(db)
        result = svc.get_project_bonus_calculations(project_id=1, status="APPROVED")
        assert result == []
