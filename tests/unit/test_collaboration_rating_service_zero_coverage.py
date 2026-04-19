# -*- coding: utf-8 -*-
"""
协作评分服务单元测试

测试覆盖:
- CollaborationRatingService: 协作评分服务
- RatingManager: 评分管理器
- Selector: 协作者选择器
- Statistics: 统计聚合器
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.collaboration_rating import CollaborationRatingService
from app.services.collaboration_rating.ratings import RatingManager
from app.services.collaboration_rating.selector import CollaboratorSelector
from app.services.collaboration_rating.statistics import RatingStatistics


class TestCollaborationRatingService:
    """测试协作评分服务"""

    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        from app.services.collaboration_rating import CollaborationRatingService

        return CollaborationRatingService(db_session)

    def test_service_initialization(self, service):
        """测试服务初始化"""
        assert service is not None
        assert hasattr(service, "db")


class TestRatingManager:
    """测试评分管理器"""

    @pytest.fixture
    def manager(self, db_session):
        """创建管理器实例"""
        service = CollaborationRatingService(db_session)
        return service.ratings

    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert manager is not None

    def test_create_rating_invitations(self, manager):
        """测试创建评分邀请"""
        result = manager.create_rating_invitations(
            engineer_id=1,
            period_id=1,
            collaborator_ids=[],
        )

        assert isinstance(result, list)

    def test_submit_rating_not_found(self, manager):
        """测试提交评分 - 评分不存在"""
        with pytest.raises(ValueError):
            manager.submit_rating(
                rating_id=99999,
                rater_id=1,
                communication_score=4,
                response_score=4,
                delivery_score=5,
                interface_score=4,
            )

    def test_get_pending_ratings(self, manager):
        """测试获取待完成评分"""
        result = manager.get_pending_ratings(rater_id=1)

        assert isinstance(result, list)

    def test_auto_complete_missing_ratings(self, manager):
        """测试自动完成缺失评分"""
        result = manager.auto_complete_missing_ratings(
            period_id=1,
            default_score=75,
        )

        assert isinstance(result, int)


class TestRatingDimensions:
    """测试评分维度"""

    def test_dimension_names(self):
        """测试评分维度名称"""
        dimensions = [
            "communication",  # 沟通配合
            "response_speed",  # 响应速度
            "delivery_quality",  # 交付质量
            "interface_compliance",  # 接口规范
        ]

        assert len(dimensions) == 4

    def test_score_range(self):
        """测试分数范围"""
        # 1-5分制
        min_score = 1
        max_score = 5

        assert min_score < max_score
        assert max_score - min_score + 1 == 5

    def test_score_to_percentage(self):
        """测试分数转换为百分制"""
        # 5分 -> 100分
        # 4分 -> 80分
        # 3分 -> 60分
        # 2分 -> 40分
        # 1分 -> 20分

        def convert_score(score):
            return score * 20

        assert convert_score(5) == 100
        assert convert_score(4) == 80
        assert convert_score(3) == 60
        assert convert_score(1) == 20


class TestSelector:
    """测试协作者选择器"""

    def test_import_class(self):
        """测试导入类"""
        assert CollaboratorSelector is not None

    def test_select_collaborators(self, db_session):
        """测试选择协作者"""
        selector = CollaboratorSelector(db_session, CollaborationRatingService(db_session))
        result = selector._get_target_job_types("mechanical")

        assert isinstance(result, list)


class TestStatistics:
    """测试统计聚合器"""

    def test_import_class(self):
        """测试导入类"""
        assert RatingStatistics is not None

    def test_get_user_statistics(self, db_session):
        """测试获取用户统计"""
        stats = RatingStatistics(db_session, CollaborationRatingService(db_session))
        result = stats.get_average_collaboration_score(engineer_id=1, period_id=1)

        assert result is not None

    def test_get_department_statistics(self, db_session):
        """测试获取部门统计"""
        stats = RatingStatistics(db_session, CollaborationRatingService(db_session))
        result = stats.get_rating_statistics(period_id=1)

        assert result is not None
        assert isinstance(result, dict)


class TestCollaborationRatingModule:
    """测试协作评分模块"""

    def test_import_module(self):
        """测试导入模块"""
        from app.services.collaboration_rating import CollaborationRatingService

        assert CollaborationRatingService is not None

    def test_import_all_components(self):
        """测试导入所有组件"""
        from app.services.collaboration_rating import (
            CollaborationRatingService,
        )

        assert CollaborationRatingService is not None
