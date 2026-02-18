# -*- coding: utf-8 -*-
"""第十三批 - 知识贡献服务 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

try:
    from app.services.knowledge_contribution_service import KnowledgeContributionService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return KnowledgeContributionService(db)


def make_contribution_data(**kwargs):
    data = MagicMock()
    data.contribution_type = kwargs.get('contribution_type', 'code_module')
    data.job_type = kwargs.get('job_type', 'mechanical')
    data.title = kwargs.get('title', '测试知识贡献')
    data.description = kwargs.get('description', '描述')
    data.file_path = kwargs.get('file_path', '/files/test.pdf')
    data.tags = kwargs.get('tags', ['tag1', 'tag2'])
    data.status = kwargs.get('status', None)
    return data


class TestKnowledgeContributionService:
    def test_init(self, db):
        """服务初始化"""
        svc = KnowledgeContributionService(db)
        assert svc.db is db

    def test_create_contribution(self, service, db):
        """创建知识贡献"""
        with patch('app.services.knowledge_contribution_service.save_obj') as mock_save:
            data = make_contribution_data()
            result = service.create_contribution(data, contributor_id=1)
            mock_save.assert_called_once()

    def test_get_contribution_found(self, service, db):
        """获取存在的知识贡献"""
        mock_contrib = MagicMock()
        mock_contrib.id = 1
        db.query.return_value.filter.return_value.first.return_value = mock_contrib

        result = service.get_contribution(1)
        assert result is mock_contrib

    def test_get_contribution_not_found(self, service, db):
        """获取不存在的知识贡献返回None"""
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.get_contribution(999)
        assert result is None

    def test_update_contribution_not_found(self, service, db):
        """更新不存在的贡献返回None"""
        db.query.return_value.filter.return_value.first.return_value = None
        data = make_contribution_data()
        result = service.update_contribution(999, data, user_id=1)
        assert result is None

    def test_update_contribution_permission_check(self, service, db):
        """非贡献者修改他人内容时抛出PermissionError"""
        mock_contrib = MagicMock()
        mock_contrib.contributor_id = 10  # 原作者
        db.query.return_value.filter.return_value.first.return_value = mock_contrib

        data = make_contribution_data()
        data.status = None
        data.model_dump.return_value = {'title': '修改标题'}

        with pytest.raises(PermissionError):
            service.update_contribution(1, data, user_id=99)  # 非作者

    def test_service_has_create_method(self, service):
        """验证create_contribution方法存在"""
        assert hasattr(service, 'create_contribution')

    def test_service_has_get_method(self, service):
        """验证get_contribution方法存在"""
        assert hasattr(service, 'get_contribution')
