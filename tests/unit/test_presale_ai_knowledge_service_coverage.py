# -*- coding: utf-8 -*-
"""
售前AI知识服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List, Optional
import numpy as np

from app.services.presale.presale_ai_knowledge_service import PresaleAIKnowledgeService


class TestPresaleAiKnowledgeServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = PresaleAIKnowledgeService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            PresaleAIKnowledgeService()


class TestPresaleAiKnowledgeServiceCRUD:
    """测试案例CRUD操作"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return PresaleAIKnowledgeService(mock_db)

    def test_create_case_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'create_case')

    def test_update_case_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'update_case')

    def test_get_case_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_case')

    def test_delete_case_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'delete_case')


class TestPresaleAiKnowledgeServiceSearch:
    """测试搜索功能"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return PresaleAIKnowledgeService(mock_db)

    def test_semantic_search_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'semantic_search')

    def test_search_knowledge_base_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'search_knowledge_base')

    def test_get_all_tags_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_all_tags')


class TestPresaleAiKnowledgeServiceAI:
    """测试AI功能"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return PresaleAIKnowledgeService(mock_db)

    def test_recommend_best_practices_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'recommend_best_practices')

    def test_extract_case_knowledge_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'extract_case_knowledge')

    def test_ask_question_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'ask_question')

    def test_submit_qa_feedback_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'submit_qa_feedback')

    def test_has_live_ai_accepts_qwen_client(self):
        """配置通义千问/百炼时不应降级为规则模板。"""
        service = PresaleAIKnowledgeService(Mock())
        ai_client = Mock()
        ai_client.openai_client = None
        ai_client.openai_api_key = ""
        ai_client.zhipu_client = None
        ai_client.kimi_api_key = ""
        ai_client.qwen_api_key = "test-qwen-key"
        service.ai_client = ai_client

        assert service._has_live_ai() is True


class TestPresaleAiKnowledgeServiceEmbedding:
    """测试嵌入向量"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return PresaleAIKnowledgeService(mock_db)

    def test__generate_embedding_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_generate_embedding')

    def test__serialize_embedding_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_serialize_embedding')

    def test__deserialize_embedding_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_deserialize_embedding')

    def test__cosine_similarity_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_cosine_similarity')

    def test__keyword_similarity_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_keyword_similarity')


class TestPresaleAiKnowledgeServiceAnalysis:
    """测试分析功能"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return PresaleAIKnowledgeService(mock_db)

    def test__analyze_success_patterns_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_analyze_success_patterns')

    def test__extract_risk_warnings_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_extract_risk_warnings')

    def test__generate_summary_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_generate_summary')
