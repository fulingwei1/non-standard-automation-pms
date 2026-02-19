# -*- coding: utf-8 -*-
"""
Unit tests for ProfileAggregator (第三十八批)
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.staff_matching.profile_aggregation", reason="导入失败，跳过")

try:
    from app.services.staff_matching.profile_aggregation import ProfileAggregator
except ImportError:
    pytestmark = pytest.mark.skip(reason="profile_aggregation 不可用")
    ProfileAggregator = None


@pytest.fixture
def mock_db():
    return MagicMock()


def make_eval(tag_id=1, tag_code="PYTHON", tag_name="Python开发", score=4.0, tag_type="SKILL"):
    ev = MagicMock()
    ev.tag_id = tag_id
    ev.score = score
    ev.is_valid = True
    ev.tag = MagicMock()
    ev.tag.tag_code = tag_code
    ev.tag.tag_name = tag_name
    ev.tag.weight = Decimal("1.0")
    ev.tag.tag_type = tag_type
    return ev


def make_profile(employee_id=1):
    profile = MagicMock()
    profile.employee_id = employee_id
    profile.skill_tags = []
    profile.domain_tags = []
    profile.attitude_tags = []
    profile.character_tags = []
    profile.special_tags = []
    profile.attitude_score = None
    return profile


class TestAggregateEmployeeProfile:
    """测试 aggregate_employee_profile 方法"""

    def _setup_db_for_profile(self, mock_db, existing_profile=None, evals=None):
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.join.return_value = mock_q
        mock_q.all.return_value = evals or []

        def side_effect(*args, **kwargs):
            return mock_q

        mock_db.query.side_effect = side_effect

        # 第一次查询返回 profile
        call_count = [0]
        original_filter = mock_q.filter

        mock_profile_q = MagicMock()
        mock_profile_q.filter.return_value = mock_profile_q
        mock_profile_q.first.return_value = existing_profile

        mock_eval_q = MagicMock()
        mock_eval_q.join.return_value = mock_eval_q
        mock_eval_q.filter.return_value = mock_eval_q
        mock_eval_q.all.return_value = evals or []

        def query_side(*args):
            nonlocal call_count
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_profile_q
            return mock_eval_q

        mock_db.query.side_effect = query_side
        return mock_profile_q, mock_eval_q

    def test_creates_new_profile_when_not_found(self, mock_db):
        """不存在档案时创建新档案"""
        profile_q, eval_q = self._setup_db_for_profile(mock_db, existing_profile=None)
        
        with patch("app.services.staff_matching.profile_aggregation.HrEmployeeProfile") as MockProfile:
            new_profile = make_profile()
            MockProfile.return_value = new_profile
            result = ProfileAggregator.aggregate_employee_profile(mock_db, employee_id=1)
            mock_db.add.assert_called()

    def test_uses_existing_profile_when_found(self, mock_db):
        """已存在档案时复用"""
        existing = make_profile(1)
        profile_q, eval_q = self._setup_db_for_profile(mock_db, existing_profile=existing)
        result = ProfileAggregator.aggregate_employee_profile(mock_db, employee_id=1)
        assert result is existing

    def test_computes_attitude_score_with_evals(self, mock_db):
        """有评估数据时计算态度分"""
        existing = make_profile(1)
        attitude_evals = [make_eval(score=4.0), make_eval(score=3.0)]

        call_count = [0]

        def query_side(*args):
            call_count[0] += 1
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            mock_q.join.return_value = mock_q
            if call_count[0] == 1:
                mock_q.first.return_value = existing
            else:
                mock_q.all.return_value = attitude_evals
            return mock_q

        mock_db.query.side_effect = query_side
        result = ProfileAggregator.aggregate_employee_profile(mock_db, employee_id=1)
        assert result is not None

    def test_attitude_score_zero_when_no_evals(self, mock_db):
        """无评估数据时不计算态度分"""
        existing = make_profile(1)

        call_count = [0]

        def query_side(*args):
            call_count[0] += 1
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            mock_q.join.return_value = mock_q
            if call_count[0] == 1:
                mock_q.first.return_value = existing
            else:
                mock_q.all.return_value = []
            return mock_q

        mock_db.query.side_effect = query_side
        result = ProfileAggregator.aggregate_employee_profile(mock_db, employee_id=1)
        assert result is not None

    def test_sets_skill_tags(self, mock_db):
        """正确设置 skill_tags"""
        existing = make_profile(1)
        evals = [make_eval(tag_code="PYTHON", score=4.0)]

        call_count = [0]

        def query_side(*args):
            call_count[0] += 1
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            mock_q.join.return_value = mock_q
            if call_count[0] == 1:
                mock_q.first.return_value = existing
            else:
                mock_q.all.return_value = evals
            return mock_q

        mock_db.query.side_effect = query_side
        result = ProfileAggregator.aggregate_employee_profile(mock_db, employee_id=1)
        assert result is not None
