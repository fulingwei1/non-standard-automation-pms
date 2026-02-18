# -*- coding: utf-8 -*-
"""第十七批 - 跨部门协作评价服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

pytest.importorskip("app.services.collaboration_service")


def _make_service(db=None):
    from app.services.collaboration_service import CollaborationService
    return CollaborationService(db or MagicMock())


def _make_rating_data(period_id=1, ratee_id=2, project_id=None):
    data = MagicMock()
    data.period_id = period_id
    data.ratee_id = ratee_id
    data.project_id = project_id
    data.communication_score = 4
    data.response_score = 3
    data.delivery_score = 5
    data.interface_score = 4
    data.comment = "不错"
    return data


class TestCollaborationService:

    def test_create_rating_raises_when_no_rater_profile(self):
        """评价人没有工程师档案时抛出 ValueError"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = _make_service(db)
        with pytest.raises(ValueError, match="评价人或被评价人不是工程师"):
            svc.create_rating(_make_rating_data(), rater_id=10)

    def test_create_rating_raises_same_job_type(self):
        """相同岗位类型不能互评"""
        db = MagicMock()
        rater_profile = MagicMock()
        rater_profile.job_type = "mechanical"
        ratee_profile = MagicMock()
        ratee_profile.job_type = "mechanical"
        db.query.return_value.filter.return_value.first.side_effect = [
            rater_profile, ratee_profile
        ]
        svc = _make_service(db)
        with pytest.raises(ValueError, match="相同岗位类型不能互评"):
            svc.create_rating(_make_rating_data(), rater_id=10)

    def test_create_rating_raises_already_rated(self):
        """同周期已评价时抛出 ValueError"""
        db = MagicMock()
        rater_profile = MagicMock()
        rater_profile.job_type = "mechanical"
        ratee_profile = MagicMock()
        ratee_profile.job_type = "test"
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            rater_profile, ratee_profile, existing
        ]
        svc = _make_service(db)
        with pytest.raises(ValueError, match="已对该工程师进行过评价"):
            svc.create_rating(_make_rating_data(), rater_id=10)

    def test_get_rating_returns_none_when_not_found(self):
        """评价不存在时返回 None"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = _make_service(db)
        result = svc.get_rating(9999)
        assert result is None

    def test_get_ratings_received_returns_tuple(self):
        """get_ratings_received 返回 (列表, 数量) 元组"""
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 3
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [MagicMock()] * 3
        svc = _make_service(db)
        items, total = svc.get_ratings_received(user_id=1)
        assert total == 3
        assert len(items) == 3

    def test_get_collaboration_matrix_builds_correct_structure(self):
        """get_collaboration_matrix 正确聚合评价矩阵"""
        db = MagicMock()
        r1 = MagicMock()
        r1.rater_job_type = "mechanical"
        r1.ratee_job_type = "test"
        r1.total_score = Decimal("80")
        r2 = MagicMock()
        r2.rater_job_type = "mechanical"
        r2.ratee_job_type = "test"
        r2.total_score = Decimal("90")
        db.query.return_value.filter.return_value.all.return_value = [r1, r2]

        svc = _make_service(db)
        result = svc.get_collaboration_matrix(period_id=1)

        assert result["period_id"] == 1
        assert "matrix" in result
        assert result["matrix"]["mechanical"]["test"] == 85.0

    def test_get_collaboration_stats_empty(self):
        """无评价时返回零值统计"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = _make_service(db)
        result = svc.get_collaboration_stats(user_id=1)
        assert result["total_ratings"] == 0
        assert result["avg_score"] == 0

    def test_group_by_rater_type(self):
        """_group_by_rater_type 正确分组统计"""
        from app.services.collaboration_service import CollaborationService
        svc = _make_service()
        r1 = MagicMock()
        r1.rater_job_type = "electrical"
        r1.total_score = Decimal("70")
        r2 = MagicMock()
        r2.rater_job_type = "electrical"
        r2.total_score = Decimal("90")
        result = svc._group_by_rater_type([r1, r2])
        assert result["electrical"]["count"] == 2
        assert result["electrical"]["avg_score"] == 80.0
