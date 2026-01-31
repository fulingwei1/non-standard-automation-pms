# -*- coding: utf-8 -*-
"""
CollaborationService 综合单元测试

测试覆盖:
- create_rating: 创建跨部门评价
- get_rating: 获取单个评价
- get_ratings_received: 获取收到的评价
- get_ratings_given: 获取给出的评价
- get_collaboration_matrix: 获取协作评价矩阵
- get_pending_ratings: 获取待评价的工程师列表
- get_collaboration_stats: 获取协作统计
- _group_by_rater_type: 按评价人岗位类型分组统计
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestCreateRating:
    """测试 create_rating 方法"""

    def test_raises_error_when_rater_not_engineer(self):
        """测试评价人不是工程师时抛出异常"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = CollaborationService(mock_db)
        mock_data = MagicMock()
        mock_data.ratee_id = 2

        with pytest.raises(ValueError, match="评价人或被评价人不是工程师"):
            service.create_rating(mock_data, rater_id=1)

    def test_raises_error_when_same_job_type(self):
        """测试相同岗位类型时抛出异常"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()

        mock_rater_profile = MagicMock()
        mock_rater_profile.job_type = "mechanical"

        mock_ratee_profile = MagicMock()
        mock_ratee_profile.job_type = "mechanical"  # 相同岗位

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_rater_profile, mock_ratee_profile
        ]

        service = CollaborationService(mock_db)
        mock_data = MagicMock()
        mock_data.ratee_id = 2

        with pytest.raises(ValueError, match="相同岗位类型不能互评"):
            service.create_rating(mock_data, rater_id=1)

    def test_raises_error_when_already_rated(self):
        """测试已评价时抛出异常"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()

        mock_rater_profile = MagicMock()
        mock_rater_profile.job_type = "mechanical"

        mock_ratee_profile = MagicMock()
        mock_ratee_profile.job_type = "test"

        mock_existing_rating = MagicMock()

        def filter_side_effect(*args, **kwargs):
            result = MagicMock()
            # Return different values based on call order
            if hasattr(filter_side_effect, 'call_count'):
                filter_side_effect.call_count += 1
            else:
                filter_side_effect.call_count = 1

            if filter_side_effect.call_count <= 2:
                # First two calls are for profiles
                if filter_side_effect.call_count == 1:
                    result.first.return_value = mock_rater_profile
                else:
                    result.first.return_value = mock_ratee_profile
            else:
                # Third call is for existing rating
                result.first.return_value = mock_existing_rating
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = CollaborationService(mock_db)
        mock_data = MagicMock()
        mock_data.ratee_id = 2
        mock_data.period_id = 1

        with pytest.raises(ValueError, match="本周期已对该工程师进行过评价"):
            service.create_rating(mock_data, rater_id=1)

    def test_creates_rating_successfully(self):
        """测试成功创建评价"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()

        mock_rater_profile = MagicMock()
        mock_rater_profile.job_type = "mechanical"

        mock_ratee_profile = MagicMock()
        mock_ratee_profile.job_type = "test"

        # Setup query chain
        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.first.return_value = mock_rater_profile
            elif call_count[0] == 2:
                result.first.return_value = mock_ratee_profile
            else:
                result.first.return_value = None  # No existing rating
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = CollaborationService(mock_db)
        mock_data = MagicMock()
        mock_data.ratee_id = 2
        mock_data.period_id = 1
        mock_data.communication_score = 4
        mock_data.response_score = 4
        mock_data.delivery_score = 5
        mock_data.interface_score = 4
        mock_data.comment = "合作愉快"
        mock_data.project_id = 10

        result = service.create_rating(mock_data, rater_id=1)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        # 总分: (4+4+5+4)/4 * 20 = 85
        assert result.total_score == Decimal("85.0")


class TestGetRating:
    """测试 get_rating 方法"""

    def test_returns_rating(self):
        """测试返回评价"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        mock_rating = MagicMock()
        mock_rating.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_rating

        service = CollaborationService(mock_db)
        result = service.get_rating(1)

        assert result.id == 1

    def test_returns_none_when_not_found(self):
        """测试未找到时返回None"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = CollaborationService(mock_db)
        result = service.get_rating(999)

        assert result is None


class TestGetRatingsReceived:
    """测试 get_ratings_received 方法"""

    def test_returns_ratings_and_total(self):
        """测试返回评价列表和总数"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        mock_rating1 = MagicMock()
        mock_rating2 = MagicMock()

        mock_query = MagicMock()
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_rating1, mock_rating2
        ]
        mock_db.query.return_value.filter.return_value = mock_query

        service = CollaborationService(mock_db)
        items, total = service.get_ratings_received(user_id=1)

        assert len(items) == 2
        assert total == 2

    def test_filters_by_period_id(self):
        """测试按周期ID筛选"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value = mock_query

        service = CollaborationService(mock_db)
        items, total = service.get_ratings_received(user_id=1, period_id=5)

        assert total == 0


class TestGetRatingsGiven:
    """测试 get_ratings_given 方法"""

    def test_returns_ratings_and_total(self):
        """测试返回评价列表和总数"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        mock_rating = MagicMock()

        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_rating]
        mock_db.query.return_value.filter.return_value = mock_query

        service = CollaborationService(mock_db)
        items, total = service.get_ratings_given(user_id=1)

        assert len(items) == 1
        assert total == 1


class TestGetCollaborationMatrix:
    """测试 get_collaboration_matrix 方法"""

    def test_builds_matrix_correctly(self):
        """测试正确构建矩阵"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()

        mock_rating1 = MagicMock()
        mock_rating1.rater_job_type = "mechanical"
        mock_rating1.ratee_job_type = "test"
        mock_rating1.total_score = Decimal("80")

        mock_rating2 = MagicMock()
        mock_rating2.rater_job_type = "mechanical"
        mock_rating2.ratee_job_type = "test"
        mock_rating2.total_score = Decimal("90")

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_rating1, mock_rating2]

        service = CollaborationService(mock_db)
        result = service.get_collaboration_matrix(period_id=1)

        assert result["period_id"] == 1
        assert "matrix" in result
        # mechanical -> test 平均分: (80 + 90) / 2 = 85
        assert result["matrix"]["mechanical"]["test"] == 85.0

    def test_returns_empty_matrix_when_no_ratings(self):
        """测试无评价时返回空矩阵"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = CollaborationService(mock_db)
        result = service.get_collaboration_matrix(period_id=1)

        assert result["matrix"] == {}


class TestGetPendingRatings:
    """测试 get_pending_ratings 方法"""

    def test_returns_empty_when_not_engineer(self):
        """测试非工程师返回空列表"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = CollaborationService(mock_db)
        result = service.get_pending_ratings(user_id=1, period_id=1)

        assert result == []

    def test_returns_pending_engineers(self):
        """测试返回待评价工程师"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()

        mock_rater_profile = MagicMock()
        mock_rater_profile.job_type = "mechanical"

        mock_ratee_profile = MagicMock()
        mock_ratee_profile.user_id = 2
        mock_ratee_profile.job_type = "test"
        mock_ratee_profile.job_level = "P5"

        mock_user = MagicMock()
        mock_user.name = "测试工程师"

        # Setup query chain
        call_count = [0]
        def query_side_effect(model):
            query_mock = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                # Rater profile query
                query_mock.filter.return_value.first.return_value = mock_rater_profile
            elif call_count[0] == 2:
                # Rated users query
                query_mock.filter.return_value.all.return_value = []
            else:
                # Pending engineers query
                query_mock.join.return_value.filter.return_value.all.return_value = [
                    (mock_ratee_profile, mock_user)
                ]
            return query_mock

        mock_db.query.side_effect = query_side_effect

        service = CollaborationService(mock_db)
        result = service.get_pending_ratings(user_id=1, period_id=1)

        assert len(result) == 1
        assert result[0]["user_id"] == 2
        assert result[0]["job_type"] == "test"


class TestGetCollaborationStats:
    """测试 get_collaboration_stats 方法"""

    def test_returns_empty_stats_when_no_ratings(self):
        """测试无评价时返回空统计"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = CollaborationService(mock_db)
        result = service.get_collaboration_stats(user_id=1)

        assert result["total_ratings"] == 0
        assert result["avg_score"] == 0
        assert result["by_dimension"] == {}

    def test_calculates_stats_correctly(self):
        """测试正确计算统计"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()

        mock_rating1 = MagicMock()
        mock_rating1.total_score = Decimal("80")
        mock_rating1.communication_score = 4
        mock_rating1.response_score = 4
        mock_rating1.delivery_score = 4
        mock_rating1.interface_score = 4
        mock_rating1.rater_job_type = "test"

        mock_rating2 = MagicMock()
        mock_rating2.total_score = Decimal("90")
        mock_rating2.communication_score = 5
        mock_rating2.response_score = 4
        mock_rating2.delivery_score = 5
        mock_rating2.interface_score = 4
        mock_rating2.rater_job_type = "electrical"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_rating1, mock_rating2]

        service = CollaborationService(mock_db)
        result = service.get_collaboration_stats(user_id=1)

        assert result["total_ratings"] == 2
        assert result["avg_score"] == 85.0  # (80 + 90) / 2
        assert result["by_dimension"]["communication"] == 4.5  # (4 + 5) / 2

    def test_groups_by_rater_type(self):
        """测试按评价人类型分组"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()

        mock_rating1 = MagicMock()
        mock_rating1.total_score = Decimal("80")
        mock_rating1.communication_score = 4
        mock_rating1.response_score = 4
        mock_rating1.delivery_score = 4
        mock_rating1.interface_score = 4
        mock_rating1.rater_job_type = "test"

        mock_rating2 = MagicMock()
        mock_rating2.total_score = Decimal("90")
        mock_rating2.communication_score = 5
        mock_rating2.response_score = 5
        mock_rating2.delivery_score = 5
        mock_rating2.interface_score = 5
        mock_rating2.rater_job_type = "test"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_rating1, mock_rating2]

        service = CollaborationService(mock_db)
        result = service.get_collaboration_stats(user_id=1)

        assert "test" in result["by_rater_type"]
        assert result["by_rater_type"]["test"]["count"] == 2
        assert result["by_rater_type"]["test"]["avg_score"] == 85.0


class TestGroupByRaterType:
    """测试 _group_by_rater_type 方法"""

    def test_groups_correctly(self):
        """测试正确分组"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        service = CollaborationService(mock_db)

        mock_rating1 = MagicMock()
        mock_rating1.rater_job_type = "mechanical"
        mock_rating1.total_score = Decimal("80")

        mock_rating2 = MagicMock()
        mock_rating2.rater_job_type = "electrical"
        mock_rating2.total_score = Decimal("90")

        mock_rating3 = MagicMock()
        mock_rating3.rater_job_type = "mechanical"
        mock_rating3.total_score = Decimal("70")

        result = service._group_by_rater_type([mock_rating1, mock_rating2, mock_rating3])

        assert result["mechanical"]["count"] == 2
        assert result["mechanical"]["avg_score"] == 75.0  # (80 + 70) / 2
        assert result["electrical"]["count"] == 1
        assert result["electrical"]["avg_score"] == 90.0

    def test_handles_empty_list(self):
        """测试处理空列表"""
        from app.services.collaboration_service import CollaborationService

        mock_db = MagicMock()
        service = CollaborationService(mock_db)

        result = service._group_by_rater_type([])

        assert result == {}


class TestValidRatingPairs:
    """测试有效的评价对"""

    def test_valid_rating_pairs_defined(self):
        """测试有效评价对已定义"""
        from app.services.collaboration_service import CollaborationService

        assert len(CollaborationService.VALID_RATING_PAIRS) > 0
        assert ('mechanical', 'test') in CollaborationService.VALID_RATING_PAIRS
        assert ('mechanical', 'electrical') in CollaborationService.VALID_RATING_PAIRS
        assert ('test', 'electrical') in CollaborationService.VALID_RATING_PAIRS
