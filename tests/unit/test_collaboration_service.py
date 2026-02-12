# -*- coding: utf-8 -*-
"""
collaboration_service 单元测试

测试跨部门协作评价服务的各个方法：
- 创建评价
- 查询评价（收到的/给出的）
- 协作评价矩阵
- 待评价列表
- 统计分析
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

import app.models.tenant  # noqa: F401 - ensure Tenant model is registered for relationship resolution
from app.services.collaboration_service import CollaborationService


def create_mock_db_session():
    """创建模拟的数据库会话"""
    return MagicMock()


def create_mock_engineer_profile(
    user_id=1,
    job_type="mechanical",
    job_level="senior",
):
    """创建模拟的工程师档案"""
    mock_profile = MagicMock()
    mock_profile.user_id = user_id
    mock_profile.job_type = job_type
    mock_profile.job_level = job_level
    return mock_profile


def create_mock_user(user_id=1, name="测试用户", department_name="机械部"):
    """创建模拟的用户"""
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.name = name
    mock_user.department_name = department_name
    return mock_user


def create_mock_rating(
    rating_id=1,
    period_id=1,
    rater_id=1,
    ratee_id=2,
    rater_job_type="mechanical",
    ratee_job_type="test",
    communication_score=4,
    response_score=4,
    delivery_score=4,
    interface_score=4,
    total_score=Decimal("80.0"),
):
    """创建模拟的评价记录"""
    mock_rating = MagicMock()
    mock_rating.id = rating_id
    mock_rating.period_id = period_id
    mock_rating.rater_id = rater_id
    mock_rating.ratee_id = ratee_id
    mock_rating.rater_job_type = rater_job_type
    mock_rating.ratee_job_type = ratee_job_type
    mock_rating.communication_score = communication_score
    mock_rating.response_score = response_score
    mock_rating.delivery_score = delivery_score
    mock_rating.interface_score = interface_score
    mock_rating.total_score = total_score
    return mock_rating


def create_mock_rating_data(
    period_id=1,
    ratee_id=2,
    communication_score=4,
    response_score=4,
    delivery_score=4,
    interface_score=4,
    comment="测试评价",
    project_id=None,
):
    """创建模拟的评价创建数据"""
    mock_data = MagicMock()
    mock_data.period_id = period_id
    mock_data.ratee_id = ratee_id
    mock_data.communication_score = communication_score
    mock_data.response_score = response_score
    mock_data.delivery_score = delivery_score
    mock_data.interface_score = interface_score
    mock_data.comment = comment
    mock_data.project_id = project_id
    return mock_data


@pytest.mark.unit
class TestValidRatingPairs:
    """测试岗位互评关系常量"""

    def test_mechanical_can_rate_test(self):
        """测试机械可评价测试"""
        assert ("mechanical", "test") in CollaborationService.VALID_RATING_PAIRS

    def test_mechanical_can_rate_electrical(self):
        """测试机械可评价电气"""
        assert ("mechanical", "electrical") in CollaborationService.VALID_RATING_PAIRS

    def test_test_can_rate_mechanical(self):
        """测试测试可评价机械"""
        assert ("test", "mechanical") in CollaborationService.VALID_RATING_PAIRS

    def test_same_type_not_in_pairs(self):
        """测试相同岗位不在互评关系中"""
        assert ("mechanical", "mechanical") not in CollaborationService.VALID_RATING_PAIRS
        assert ("test", "test") not in CollaborationService.VALID_RATING_PAIRS
        assert ("electrical", "electrical") not in CollaborationService.VALID_RATING_PAIRS


@pytest.mark.unit
class TestCreateRating:
    """测试 create_rating 方法"""

    def test_creates_rating_successfully(self):
        """测试成功创建评价"""
        db = create_mock_db_session()

        # 模拟评价人和被评价人档案
        rater_profile = create_mock_engineer_profile(user_id=1, job_type="mechanical")
        ratee_profile = create_mock_engineer_profile(user_id=2, job_type="test")

        # 使用列表追踪调用次数
        engineer_call_count = [0]
        rating_call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            model_name = str(model)

            if "EngineerProfile" in model_name:
                mock_filter = MagicMock()
                # 根据调用次数返回���同的档案
                if engineer_call_count[0] == 0:
                    mock_filter.first.return_value = rater_profile
                    engineer_call_count[0] += 1
                else:
                    mock_filter.first.return_value = ratee_profile
                mock_query.filter.return_value = mock_filter
            elif "CollaborationRating" in model_name:
                mock_filter = MagicMock()
                mock_filter.first.return_value = None  # 无重复评价
                mock_query.filter.return_value = mock_filter
            return mock_query

        db.query.side_effect = query_side_effect

        service = CollaborationService(db)
        data = create_mock_rating_data(ratee_id=2)

        rating = service.create_rating(data, rater_id=1)

        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_raises_error_for_non_engineer_rater(self):
        """测试非工程师评价人抛出错误"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        service = CollaborationService(db)
        data = create_mock_rating_data()

        with pytest.raises(ValueError, match="评价人或被评价人不是工程师"):
            service.create_rating(data, rater_id=1)

    def test_raises_error_for_same_job_type(self):
        """测试相同岗位互评抛出错误"""
        db = create_mock_db_session()

        # 两人都是 mechanical
        rater_profile = create_mock_engineer_profile(user_id=1, job_type="mechanical")
        ratee_profile = create_mock_engineer_profile(user_id=2, job_type="mechanical")

        db.query.return_value.filter.return_value.first.side_effect = [
            rater_profile,
            ratee_profile,
        ]

        service = CollaborationService(db)
        data = create_mock_rating_data(ratee_id=2)

        with pytest.raises(ValueError, match="相同岗位类型不能互评"):
            service.create_rating(data, rater_id=1)

    def test_raises_error_for_duplicate_rating(self):
        """测试重复评价抛出错误"""
        db = create_mock_db_session()

        rater_profile = create_mock_engineer_profile(user_id=1, job_type="mechanical")
        ratee_profile = create_mock_engineer_profile(user_id=2, job_type="test")
        existing_rating = create_mock_rating()

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            model_name = str(model)

            if "EngineerProfile" in model_name:
                mock_filter = MagicMock()
                if call_count[0] == 0:
                    mock_filter.first.return_value = rater_profile
                    call_count[0] += 1
                else:
                    mock_filter.first.return_value = ratee_profile
                mock_query.filter.return_value = mock_filter
            else:
                # CollaborationRating 返回已存在记录
                mock_filter = MagicMock()
                mock_filter.first.return_value = existing_rating
                mock_query.filter.return_value = mock_filter
            return mock_query

        db.query.side_effect = query_side_effect

        service = CollaborationService(db)
        data = create_mock_rating_data(ratee_id=2)

        with pytest.raises(ValueError, match="本周期已对该工程师进行过评价"):
            service.create_rating(data, rater_id=1)

    def test_calculates_total_score_correctly(self):
        """测试总分计算正确"""
        # 手动计算：(4+4+4+4)/4 * 20 = 80
        db = create_mock_db_session()

        rater_profile = create_mock_engineer_profile(user_id=1, job_type="mechanical")
        ratee_profile = create_mock_engineer_profile(user_id=2, job_type="test")

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            if "EngineerProfile" in str(model):
                mock_filter = MagicMock()
                if call_count[0] == 0:
                    mock_filter.first.return_value = rater_profile
                    call_count[0] += 1
                else:
                    mock_filter.first.return_value = ratee_profile
                mock_query.filter.return_value = mock_filter
            else:
                mock_filter = MagicMock()
                mock_filter.first.return_value = None
                mock_query.filter.return_value = mock_filter
            return mock_query

        db.query.side_effect = query_side_effect

        service = CollaborationService(db)
        data = create_mock_rating_data(
            communication_score=5,
            response_score=5,
            delivery_score=5,
            interface_score=5,
        )

        rating = service.create_rating(data, rater_id=1)

        # (5+5+5+5)/4 * 20 = 100
        assert rating.total_score == Decimal("100")


@pytest.mark.unit
class TestGetRating:
    """测试 get_rating 方法"""

    def test_returns_rating_by_id(self):
        """测试根据ID获取评价"""
        db = create_mock_db_session()
        expected_rating = create_mock_rating(rating_id=123)
        db.query.return_value.filter.return_value.first.return_value = expected_rating

        service = CollaborationService(db)
        rating = service.get_rating(123)

        assert rating == expected_rating

    def test_returns_none_for_nonexistent_id(self):
        """测试不存在的ID返回None"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        service = CollaborationService(db)
        rating = service.get_rating(999)

        assert rating is None


@pytest.mark.unit
class TestGetRatingsReceived:
    """测试 get_ratings_received 方法"""

    def test_returns_ratings_and_count(self):
        """测试返回评价列表和总数"""
        db = create_mock_db_session()
        ratings = [create_mock_rating(rating_id=i) for i in range(3)]

        mock_query = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.count.return_value = 3
        mock_filtered.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            ratings
        )
        mock_query.filter.return_value = mock_filtered
        db.query.return_value = mock_query

        service = CollaborationService(db)
        items, total = service.get_ratings_received(user_id=1)

        assert len(items) == 3
        assert total == 3

    def test_filters_by_period_when_provided(self):
        """测试提供周期ID时进行过滤"""
        db = create_mock_db_session()
        mock_query = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.filter.return_value = mock_filtered
        mock_filtered.count.return_value = 1
        mock_filtered.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            create_mock_rating()
        ]
        mock_query.filter.return_value = mock_filtered
        db.query.return_value = mock_query

        service = CollaborationService(db)
        items, total = service.get_ratings_received(user_id=1, period_id=5)

        assert total == 1


@pytest.mark.unit
class TestGetRatingsGiven:
    """测试 get_ratings_given 方法"""

    def test_returns_ratings_given_by_user(self):
        """测试返回用户给出的评价"""
        db = create_mock_db_session()
        ratings = [create_mock_rating(rating_id=i, rater_id=1) for i in range(2)]

        mock_query = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.count.return_value = 2
        mock_filtered.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            ratings
        )
        mock_query.filter.return_value = mock_filtered
        db.query.return_value = mock_query

        service = CollaborationService(db)
        items, total = service.get_ratings_given(user_id=1)

        assert len(items) == 2
        assert total == 2


@pytest.mark.unit
class TestGetCollaborationMatrix:
    """测试 get_collaboration_matrix 方法"""

    def test_builds_matrix_from_ratings(self):
        """测试从评价构建矩阵"""
        db = create_mock_db_session()
        ratings = [
            create_mock_rating(
                rater_job_type="mechanical",
                ratee_job_type="test",
                total_score=Decimal("80"),
            ),
            create_mock_rating(
                rater_job_type="mechanical",
                ratee_job_type="test",
                total_score=Decimal("90"),
            ),
            create_mock_rating(
                rater_job_type="test",
                ratee_job_type="electrical",
                total_score=Decimal("70"),
            ),
        ]
        db.query.return_value.filter.return_value.all.return_value = ratings

        service = CollaborationService(db)
        result = service.get_collaboration_matrix(period_id=1)

        assert result["period_id"] == 1
        assert "matrix" in result
        # mechanical -> test 平均分：(80+90)/2 = 85
        assert result["matrix"]["mechanical"]["test"] == 85.0
        # test -> electrical 平均分：70
        assert result["matrix"]["test"]["electrical"] == 70.0

    def test_returns_empty_matrix_for_no_ratings(self):
        """测试无评价时返回空矩阵"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []

        service = CollaborationService(db)
        result = service.get_collaboration_matrix(period_id=1)

        assert result["period_id"] == 1
        assert result["matrix"] == {}


@pytest.mark.unit
class TestGetPendingRatings:
    """测试 get_pending_ratings 方法"""

    def test_returns_empty_for_non_engineer(self):
        """测试非工程师返回空列表"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        service = CollaborationService(db)
        result = service.get_pending_ratings(user_id=1, period_id=1)

        assert result == []

    def test_excludes_already_rated_users(self):
        """测试排除已评价的用户"""
        db = create_mock_db_session()
        rater_profile = create_mock_engineer_profile(user_id=1, job_type="mechanical")

        call_count = [0]

        def query_side_effect(*models):
            mock_query = MagicMock()
            model_names = [str(m) for m in models]

            if call_count[0] == 0:
                # 第一次：获取评价人档案
                mock_query.filter.return_value.first.return_value = rater_profile
                call_count[0] += 1
            elif call_count[0] == 1:
                # 第二次：获取已评价用户ID
                mock_query.filter.return_value.all.return_value = [(2,)]  # 已评价用户2
                call_count[0] += 1
            else:
                # 第三次：获取待评价工程师（多参数查询）
                pending_profile = create_mock_engineer_profile(user_id=3, job_type="test")
                pending_user = create_mock_user(user_id=3, name="待评价用户")
                mock_query.join.return_value.filter.return_value.all.return_value = [
                    (pending_profile, pending_user)
                ]

            return mock_query

        db.query.side_effect = query_side_effect

        service = CollaborationService(db)
        result = service.get_pending_ratings(user_id=1, period_id=1)

        # 应返回待评价的用户3
        assert len(result) == 1
        assert result[0]["user_id"] == 3


@pytest.mark.unit
class TestGetCollaborationStats:
    """测试 get_collaboration_stats 方法"""

    def test_returns_empty_stats_for_no_ratings(self):
        """测试无评价时返回空统计"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []

        service = CollaborationService(db)
        stats = service.get_collaboration_stats(user_id=1)

        assert stats["total_ratings"] == 0
        assert stats["avg_score"] == 0
        assert stats["by_dimension"] == {}

    def test_calculates_dimension_averages(self):
        """测试计算各维度平均分"""
        db = create_mock_db_session()
        ratings = [
            create_mock_rating(
                communication_score=4,
                response_score=5,
                delivery_score=3,
                interface_score=4,
                total_score=Decimal("80"),
            ),
            create_mock_rating(
                communication_score=5,
                response_score=4,
                delivery_score=4,
                interface_score=5,
                total_score=Decimal("90"),
            ),
        ]
        db.query.return_value.filter.return_value.all.return_value = ratings

        service = CollaborationService(db)
        stats = service.get_collaboration_stats(user_id=1)

        assert stats["total_ratings"] == 2
        assert stats["avg_score"] == 85.0
        assert stats["by_dimension"]["communication"] == 4.5
        assert stats["by_dimension"]["response"] == 4.5
        assert stats["by_dimension"]["delivery"] == 3.5
        assert stats["by_dimension"]["interface"] == 4.5


@pytest.mark.unit
class TestGroupByRaterType:
    """测试 _group_by_rater_type 方法"""

    def test_groups_ratings_by_rater_job_type(self):
        """测试按评价人岗位分组"""
        db = create_mock_db_session()
        service = CollaborationService(db)

        ratings = [
            create_mock_rating(rater_job_type="mechanical", total_score=Decimal("80")),
            create_mock_rating(rater_job_type="mechanical", total_score=Decimal("90")),
            create_mock_rating(rater_job_type="test", total_score=Decimal("70")),
        ]

        result = service._group_by_rater_type(ratings)

        assert result["mechanical"]["count"] == 2
        assert result["mechanical"]["avg_score"] == 85.0
        assert result["test"]["count"] == 1
        assert result["test"]["avg_score"] == 70.0

    def test_returns_empty_for_no_ratings(self):
        """测试无评价时返回空字典"""
        db = create_mock_db_session()
        service = CollaborationService(db)

        result = service._group_by_rater_type([])

        assert result == {}
