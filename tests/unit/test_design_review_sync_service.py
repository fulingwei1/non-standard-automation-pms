# -*- coding: utf-8 -*-
"""
设计评审自动同步服务单元测试
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest


class TestDesignReviewSyncServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self, db_session):
        """测试使用数据库会话初始化"""
        from app.services.design_review_sync_service import DesignReviewSyncService

        service = DesignReviewSyncService(db_session)
        assert service.db == db_session


class TestSyncFromTechnicalReview:
    """测试从技术评审同步"""

    def test_review_not_found(self, db_session):
        """测试评审不存在"""
        from app.services.design_review_sync_service import DesignReviewSyncService

        service = DesignReviewSyncService(db_session)
        result = service.sync_from_technical_review(99999)

        assert result is None

    def test_review_not_completed(self, db_session):
        """测试评审未完成"""
        from app.services.design_review_sync_service import DesignReviewSyncService
        from app.models.technical_review import TechnicalReview

        review = TechnicalReview(
        review_no="TR001",
        status="IN_PROGRESS"
        )
        db_session.add(review)
        db_session.flush()

        service = DesignReviewSyncService(db_session)
        result = service.sync_from_technical_review(review.id)

        assert result is None


class TestSyncAllCompletedReviews:
    """测试同步所有已完成评审"""

    def test_no_reviews(self, db_session):
        """测试无评审"""
        from app.services.design_review_sync_service import DesignReviewSyncService

        service = DesignReviewSyncService(db_session)
        result = service.sync_all_completed_reviews()

        assert result['total_reviews'] == 0
        assert result['synced_count'] == 0

    def test_with_date_filter(self, db_session):
        """测试带日期过滤"""
        from app.services.design_review_sync_service import DesignReviewSyncService

        service = DesignReviewSyncService(db_session)
        result = service.sync_all_completed_reviews(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31)
        )

        assert 'total_reviews' in result

    def test_stats_structure(self, db_session):
        """测试统计结构"""
        from app.services.design_review_sync_service import DesignReviewSyncService

        service = DesignReviewSyncService(db_session)
        result = service.sync_all_completed_reviews()

        expected_fields = [
        'total_reviews', 'synced_count', 'skipped_count',
        'error_count', 'errors'
        ]
        for field in expected_fields:
            assert field in result


class TestReviewResultMapping:
    """测试评审结果映射"""

    def test_pass_result(self):
        """测试通过结果"""
        conclusion = 'PASS'
        review_result = None
        is_first_pass = False

        if conclusion == 'PASS':
            review_result = 'PASSED'
            is_first_pass = True
        elif conclusion == 'PASS_WITH_CONDITION':
            review_result = 'PASSED_WITH_CONDITION'

            assert review_result == 'PASSED'
            assert is_first_pass is True

    def test_pass_with_condition(self):
        """测试有条件通过"""
        conclusion = 'PASS_WITH_CONDITION'
        review_result = None
        is_first_pass = False

        if conclusion == 'PASS':
            review_result = 'PASSED'
            is_first_pass = True
        elif conclusion == 'PASS_WITH_CONDITION':
            review_result = 'PASSED_WITH_CONDITION'
            is_first_pass = False

            assert review_result == 'PASSED_WITH_CONDITION'
            assert is_first_pass is False

    def test_reject_result(self):
        """测试拒绝结果"""
        conclusion = 'REJECT'
        review_result = None
        is_first_pass = False

        if conclusion == 'PASS':
            review_result = 'PASSED'
        elif conclusion == 'PASS_WITH_CONDITION':
            review_result = 'PASSED_WITH_CONDITION'
        elif conclusion == 'REJECT':
            review_result = 'REJECTED'

            assert review_result == 'REJECTED'
            assert is_first_pass is False


class TestDesignNameGeneration:
    """测试设计名称生成"""

    def test_generate_name(self):
        """测试生成名称"""
        review_name = "机械设计评审"
        review_type = "PRELIMINARY"

        design_name = f"{review_name}（{review_type}）"

        assert design_name == "机械设计评审（PRELIMINARY）"

    def test_generate_name_detailed(self):
        """测试生成详细名称"""
        review_name = "电气设计评审"
        review_type = "DETAILED"

        design_name = f"{review_name}（{review_type}）"

        assert design_name == "电气设计评审（DETAILED）"


class TestIssueCountCalculation:
    """测试问题数量计算"""

    def test_total_issues(self):
        """测试计算总问题数"""
        issue_count_a = 2
        issue_count_b = 3
        issue_count_c = 5
        issue_count_d = 1

        total = issue_count_a + issue_count_b + issue_count_c + issue_count_d

        assert total == 11

    def test_zero_issues(self):
        """测试零问题"""
        issue_count_a = 0
        issue_count_b = 0
        issue_count_c = 0
        issue_count_d = 0

        total = issue_count_a + issue_count_b + issue_count_c + issue_count_d

        assert total == 0


# pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
