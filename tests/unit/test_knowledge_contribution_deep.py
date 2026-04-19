# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 知识贡献服务"""
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class TestKnowledgeContributionServiceBusinessLogic:
    """知识贡献服务业务逻辑测试"""

    def test_create_contribution(self):
        """测试创建贡献"""
        try:
            from app.services.knowledge_contribution_service import KnowledgeContributionService

            mock_db = MagicMock()
            service = KnowledgeContributionService(mock_db)
            data = SimpleNamespace(
                contribution_type="experience",
                job_type="pm",
                title="test",
                description="desc",
                file_path=None,
                tags=[],
            )

            result = service.create_contribution(data, contributor_id=1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_approve_contribution(self):
        """测试审批贡献"""
        try:
            from app.services.knowledge_contribution_service import KnowledgeContributionService

            mock_db = MagicMock()
            contribution = MagicMock()
            contribution.status = "pending"
            mock_db.query.return_value.filter.return_value.first.return_value = contribution
            service = KnowledgeContributionService(mock_db)

            result = service.approve_contribution(1, approver_id=1)

            assert result is contribution
        except ImportError:
            pytest.skip("Module not found")
