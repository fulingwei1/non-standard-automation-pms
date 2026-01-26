# -*- coding: utf-8 -*-
"""
知识贡献服务单元测试

测试 KnowledgeContributionService 的核心功能:
- 知识贡献的创建、查询、更新、删除
- 提交审核和审批流程
- 复用记录
- 贡献排行和统计
- 代码模块库和PLC模块库
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.knowledge_contribution_service import KnowledgeContributionService


class TestKnowledgeContributionServiceInit:
    """服务初始化测试"""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = KnowledgeContributionService(db_session)
        assert service.db == db_session


class TestGetContribution:
    """获取知识贡献测试"""

    def test_get_contribution_not_found(self, db_session: Session):
        """测试获取不存在的贡献返回None"""
        service = KnowledgeContributionService(db_session)
        result = service.get_contribution(99999)
        assert result is None


class TestListContributions:
    """获取知识贡献列表测试"""

    def test_list_contributions_no_filter(self, db_session: Session):
        """测试无筛选条件获取列表"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_contributions()
        assert isinstance(items, list)
        assert isinstance(total, int)
        assert total >= 0

    def test_list_contributions_with_contributor_filter(self, db_session: Session):
        """测试按贡献者筛选"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_contributions(contributor_id=1)
        assert isinstance(items, list)
        assert isinstance(total, int)

    def test_list_contributions_with_job_type_filter(self, db_session: Session):
        """测试按工种筛选"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_contributions(job_type='software')
        assert isinstance(items, list)
        assert isinstance(total, int)

    def test_list_contributions_with_contribution_type_filter(self, db_session: Session):
        """测试按贡献类型筛选"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_contributions(contribution_type='code')
        assert isinstance(items, list)
        assert isinstance(total, int)

    def test_list_contributions_with_status_filter(self, db_session: Session):
        """测试按状态筛选"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_contributions(status='approved')
        assert isinstance(items, list)
        assert isinstance(total, int)

    def test_list_contributions_with_pagination(self, db_session: Session):
        """测试分页参数"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_contributions(limit=10, offset=0)
        assert isinstance(items, list)
        assert len(items) <= 10


class TestDeleteContribution:
    """删除知识贡献测试"""

    def test_delete_contribution_not_found(self, db_session: Session):
        """测试删除不存在的贡献返回False"""
        service = KnowledgeContributionService(db_session)
        result = service.delete_contribution(99999, user_id=1)
        assert result is False


class TestGetReuseLogs:
    """获取复用记录测试"""

    def test_get_reuse_logs_empty(self, db_session: Session):
        """测试获取不存在贡献的复用记录"""
        service = KnowledgeContributionService(db_session)
        items, total = service.get_reuse_logs(contribution_id=99999)
        assert isinstance(items, list)
        assert total == 0


class TestGetContributionRanking:
    """获取贡献排行测试"""

    def test_get_contribution_ranking_no_filter(self, db_session: Session):
        """测试无筛选条件获取排行"""
        service = KnowledgeContributionService(db_session)
        ranking = service.get_contribution_ranking()
        assert isinstance(ranking, list)

    def test_get_contribution_ranking_with_job_type(self, db_session: Session):
        """测试按工种筛选排行"""
        service = KnowledgeContributionService(db_session)
        ranking = service.get_contribution_ranking(job_type='software')
        assert isinstance(ranking, list)

    def test_get_contribution_ranking_with_contribution_type(self, db_session: Session):
        """测试按贡献类型筛选排行"""
        service = KnowledgeContributionService(db_session)
        ranking = service.get_contribution_ranking(contribution_type='code')
        assert isinstance(ranking, list)

    def test_get_contribution_ranking_with_limit(self, db_session: Session):
        """测试限制排行数量"""
        service = KnowledgeContributionService(db_session)
        ranking = service.get_contribution_ranking(limit=5)
        assert isinstance(ranking, list)
        assert len(ranking) <= 5


class TestGetContributorStats:
    """获取贡献者统计测试"""

    def test_get_contributor_stats_no_contributions(self, db_session: Session):
        """测试无贡献用户的统计"""
        service = KnowledgeContributionService(db_session)
        stats = service.get_contributor_stats(user_id=99999)

        assert stats['total_contributions'] == 0
        assert stats['total_reuse'] == 0
        assert stats['avg_rating'] == 0
        assert stats['by_type'] == {}

    def test_get_contributor_stats_structure(self, db_session: Session):
        """测试统计数据结构"""
        service = KnowledgeContributionService(db_session)
        stats = service.get_contributor_stats(user_id=1)

        assert 'total_contributions' in stats
        assert 'total_reuse' in stats
        assert 'avg_rating' in stats
        assert 'by_type' in stats
        assert isinstance(stats['total_contributions'], int)
        assert isinstance(stats['total_reuse'], int)
        assert isinstance(stats['by_type'], dict)


class TestListCodeModules:
    """获取代码模块列表测试"""

    def test_list_code_modules_no_filter(self, db_session: Session):
        """测试无筛选条件获取代码模块"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_code_modules()
        assert isinstance(items, list)
        assert isinstance(total, int)

    def test_list_code_modules_with_category(self, db_session: Session):
        """测试按分类筛选代码模块"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_code_modules(category='vision')
        assert isinstance(items, list)
        assert isinstance(total, int)

    def test_list_code_modules_with_language(self, db_session: Session):
        """测试按语言筛选代码模块"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_code_modules(language='python')
        assert isinstance(items, list)
        assert isinstance(total, int)

    def test_list_code_modules_with_pagination(self, db_session: Session):
        """测试分页参数"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_code_modules(limit=10, offset=0)
        assert isinstance(items, list)
        assert len(items) <= 10


class TestListPlcModules:
    """获取PLC模块列表测试"""

    def test_list_plc_modules_no_filter(self, db_session: Session):
        """测试无筛选条件获取PLC模块"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_plc_modules()
        assert isinstance(items, list)
        assert isinstance(total, int)

    def test_list_plc_modules_with_category(self, db_session: Session):
        """测试按分类筛选PLC模块"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_plc_modules(category='motion')
        assert isinstance(items, list)
        assert isinstance(total, int)

    def test_list_plc_modules_with_plc_brand(self, db_session: Session):
        """测试按PLC品牌筛选"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_plc_modules(plc_brand='siemens')
        assert isinstance(items, list)
        assert isinstance(total, int)

    def test_list_plc_modules_with_pagination(self, db_session: Session):
        """测试分页参数"""
        service = KnowledgeContributionService(db_session)
        items, total = service.list_plc_modules(limit=10, offset=0)
        assert isinstance(items, list)
        assert len(items) <= 10


class TestSubmitForReview:
    """提交审核测试"""

    def test_submit_for_review_not_found(self, db_session: Session):
        """测试提交不存在的贡献"""
        service = KnowledgeContributionService(db_session)
        with pytest.raises(ValueError, match="贡献不存在"):
            service.submit_for_review(99999, user_id=1)


class TestApproveContribution:
    """审核知识贡献测试"""

    def test_approve_contribution_not_found(self, db_session: Session):
        """测试审核不存在的贡献"""
        service = KnowledgeContributionService(db_session)
        with pytest.raises(ValueError, match="贡献不存在"):
            service.approve_contribution(99999, approver_id=1)


class TestRecordReuse:
    """记录复用测试"""

    def test_record_reuse_contribution_not_found(self, db_session: Session):
        """测试记录不存在贡献的复用"""
        service = KnowledgeContributionService(db_session)
        mock_data = MagicMock()
        mock_data.contribution_id = 99999

        with pytest.raises(ValueError, match="贡献不存在"):
            service.record_reuse(mock_data, user_id=1)
