# -*- coding: utf-8 -*-
"""第十七批 - 协作评价管理器（collaboration_rating/ratings.py）单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

pytest.importorskip("app.services.collaboration_rating.ratings")


def _make_manager(db=None, service=None):
    from app.services.collaboration_rating.ratings import RatingManager
    return RatingManager(db or MagicMock(), service or MagicMock())


class TestRatingManager:

    def test_submit_rating_not_found(self):
        """评价记录不存在时抛出 ValueError"""
        db = MagicMock()
        # 单次 filter 调用，返回 None
        db.query.return_value.filter.return_value.first.return_value = None
        mgr = _make_manager(db)
        with pytest.raises(ValueError, match="不存在或无权限"):
            mgr.submit_rating(999, rater_id=1, communication_score=3, response_score=3,
                              delivery_score=3, interface_score=3)

    def test_submit_rating_invalid_score_range(self):
        """评分超出 1-5 范围时抛出 ValueError"""
        db = MagicMock()
        rating = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = rating
        mgr = _make_manager(db)
        with pytest.raises(ValueError, match="1-5"):
            mgr.submit_rating(1, rater_id=1, communication_score=6, response_score=3,
                              delivery_score=3, interface_score=3)

    def test_submit_rating_calculates_total_score(self):
        """submit_rating 正确计算百分制总分"""
        db = MagicMock()
        # 使用真实对象代替 MagicMock 以便验证属性赋值
        class FakeRating:
            pass
        rating = FakeRating()
        db.query.return_value.filter.return_value.first.return_value = rating
        db.refresh = MagicMock(return_value=None)
        mgr = _make_manager(db)

        mgr.submit_rating(1, rater_id=1, communication_score=4, response_score=4,
                          delivery_score=4, interface_score=4)

        # 4*25+4*25+4*25+4*25 = 400, /5*20 = 1600
        expected = Decimal(str(round(400 / 5 * 20, 2)))
        assert rating.total_score == expected
        db.commit.assert_called_once()

    def test_get_pending_ratings_no_period_filter(self):
        """get_pending_ratings 无 period_id 时直接 .all()"""
        db = MagicMock()
        pending = [MagicMock(), MagicMock()]
        # no period filter: query().filter().all()
        db.query.return_value.filter.return_value.all.return_value = pending
        mgr = _make_manager(db)
        result = mgr.get_pending_ratings(rater_id=1)
        assert result == pending

    def test_get_pending_ratings_with_period_filter(self):
        """get_pending_ratings 有 period_id 时走双 filter"""
        db = MagicMock()
        pending = [MagicMock()]
        # with period filter: query().filter().filter().all()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = pending
        mgr = _make_manager(db)
        result = mgr.get_pending_ratings(rater_id=1, period_id=2)
        assert result == pending

    def test_auto_complete_missing_ratings_sets_default_score(self):
        """auto_complete_missing_ratings 填充默认分数"""
        db = MagicMock()

        class FakeRating:
            pass

        r1 = FakeRating()
        r2 = FakeRating()
        db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        mgr = _make_manager(db)

        count = mgr.auto_complete_missing_ratings(period_id=1)

        assert count == 2
        assert r1.total_score == Decimal("75.0")
        assert r2.communication_score == 3
        db.commit.assert_called_once()

    def test_create_rating_invitations_skips_existing(self):
        """已存在评价记录时跳过"""
        db = MagicMock()
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing
        mgr = _make_manager(db)

        result = mgr.create_rating_invitations(
            engineer_id=2, period_id=1, collaborator_ids=[10]
        )
        # 已存在 -> 跳过，invitations 为空
        assert result == []

    def test_create_rating_invitations_creates_new_record(self):
        """无现有评价时创建新邀请记录"""
        db = MagicMock()

        # 检查现有记录返回 None
        existing_check = MagicMock()
        existing_check.first.return_value = None

        # rater/ratee profile
        rater_profile = MagicMock()
        rater_profile.job_type = "test"
        ratee_profile = MagicMock()
        ratee_profile.job_type = "mechanical"

        # 第三次 first() 调用: commit 后更新 rating_id
        post_commit_rating = MagicMock()
        post_commit_rating.id = 55

        call_count = 0
        def filter_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            m = MagicMock()
            if call_count == 1:
                m.first.return_value = None  # 现有检查
            elif call_count == 2:
                m.first.return_value = rater_profile
            elif call_count == 3:
                m.first.return_value = ratee_profile
            else:
                m.first.return_value = post_commit_rating
            return m

        db.query.return_value.filter.side_effect = filter_side_effect

        with patch("app.services.collaboration_rating.ratings.CollaborationRating") as MockRating:
            mock_r = MagicMock()
            MockRating.return_value = mock_r
            mgr = _make_manager(db)
            result = mgr.create_rating_invitations(
                engineer_id=2, period_id=1, collaborator_ids=[10]
            )

        db.add.assert_called()
        db.commit.assert_called()
        assert len(result) == 1
