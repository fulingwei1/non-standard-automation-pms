# -*- coding: utf-8 -*-
"""
KnowledgeSearchService 测试
知识检索服务
"""

import pytest
from unittest.mock import Mock, MagicMock

from app.services.knowledge.search_service import KnowledgeSearchService
from app.models.knowledge_base import KnowledgeEntry, KnowledgeTypeEnum, KnowledgeSourceEnum, KnowledgeStatusEnum


class TestKnowledgeSearchService:
    """知识检索服务测试"""

    def test_search_keyword(self, db_session):
        """
        测试关键词搜索
        """
        # 创建模拟知识条目
        mock_entry = Mock(spec=KnowledgeEntry)
        mock_entry.id = 1
        mock_entry.title = "测试知识标题"
        mock_entry.summary = "测试摘要"
        
        db_session.query = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_entry]
        db_session.query.return_value = mock_query
        
        service = KnowledgeSearchService(db_session)
        result = service.search(keyword="测试")
        
        # 验证结果
        assert "total" in result
        assert "items" in result
        assert result["total"] == 1

    def test_search_with_filters(self, db_session):
        """
        测试多维度筛选
        """
        db_session.query = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        db_session.query.return_value = mock_query
        
        service = KnowledgeSearchService(db_session)
        result = service.search(
            knowledge_type="RISK_RESPONSE",
            project_type="非标设备",
            product_category="ICT测试设备",
            status=KnowledgeStatusEnum.PUBLISHED,
        )
        
        # 验证结果结构
        assert "total" in result
        assert "items" in result
        assert result["page"] == 1

    def test_search_pagination(self, db_session):
        """
        测试分页功能
        """
        db_session.query = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        db_session.query.return_value = mock_query
        
        service = KnowledgeSearchService(db_session)
        result = service.search(page=2, page_size=10)
        
        # 验证分页参数
        assert result["page"] == 2
        assert result["page_size"] == 10

    def test_get_by_id_success(self, db_session):
        """
        测试通过ID获取知识条目
        """
        mock_entry = Mock(spec=KnowledgeEntry)
        mock_entry.id = 1
        mock_entry.title = "测试标题"
        mock_entry.view_count = 5
        
        db_session.query = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_entry
        db_session.query.return_value = mock_query
        
        service = KnowledgeSearchService(db_session)
        result = service.get_by_id(1, increment_view=True)
        
        # 验证
        assert result is not None
        assert result.id == 1

    def test_get_by_id_not_found(self, db_session):
        """
        测试获取不存在的知识条目
        """
        db_session.query = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        db_session.query.return_value = mock_query
        
        service = KnowledgeSearchService(db_session)
        result = service.get_by_id(9999)
        
        assert result is None

    def test_vote_success(self, db_session):
        """
        测试投票功能
        """
        mock_entry = Mock(spec=KnowledgeEntry)
        mock_entry.id = 1
        mock_entry.vote_count = 5
        mock_entry.usefulness_score = 4.0
        
        db_session.query = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_entry
        db_session.query.return_value = mock_query
        
        service = KnowledgeSearchService(db_session)
        result = service.vote(1, score=5.0)
        
        # 验证投票更新
        assert result.vote_count == 6

    def test_vote_not_found(self, db_session):
        """
        测试对不存在的知识条目投票
        """
        db_session.query = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        db_session.query.return_value = mock_query
        
        service = KnowledgeSearchService(db_session)
        
        with pytest.raises(ValueError, match="知识条目 999 不存在"):
            service.vote(999, score=5.0)

    def test_get_statistics(self, db_session):
        """
        测试知识库统计
        """
        
        db_session.query = MagicMock()
        
        # 模拟多个查询
        mock_query_total = MagicMock()
        mock_query_total.scalar.return_value = 100
        
        mock_query_published = MagicMock()
        mock_query_published.scalar.return_value = 80
        
        mock_query_type = MagicMock()
        mock_query_type.group_by.return_value.all.return_value = [
            (KnowledgeTypeEnum.RISK_RESPONSE, 30),
            (KnowledgeTypeEnum.ISSUE_SOLUTION, 50),
        ]
        
        mock_query_source = MagicMock()
        mock_query_source.group_by.return_value.all.return_value = [
            (KnowledgeSourceEnum.RISK, 40),
            (KnowledgeSourceEnum.ISSUE, 40),
        ]
        
        def query_side_effect(*args, **kwargs):
            # 根据查询的模型判断返回什么 mock
            if args and hasattr(args[0], '__name__'):
                model_name = args[0].__name__
                if model_name == 'func':
                    return mock_query_total
                elif 'count' in str(args):
                    return mock_query_published
                    
            # 检查是否是 group by 查询
            if hasattr(args[0], 'group_by'):
                if 'knowledge_type' in str(args[0].c):
                    return mock_query_type
                elif 'source_type' in str(args[0].c):
                    return mock_query_source
                    
            return mock_query_total
        
        db_session.query.side_effect = query_side_effect
        
        service = KnowledgeSearchService(db_session)
        result = service.get_statistics()
        
        # 验证统计结果结构
        assert "total" in result
        assert "published" in result
        assert "by_type" in result
        assert "by_source" in result