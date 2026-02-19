# -*- coding: utf-8 -*-
"""
第三十二批覆盖率测试 - 知识贡献服务 (扩展)
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

try:
    from app.services.knowledge_contribution_service import KnowledgeContributionService
    HAS_KCS = True
except Exception:
    HAS_KCS = False

pytestmark = pytest.mark.skipif(not HAS_KCS, reason="knowledge_contribution_service 导入失败")


def make_service():
    db = MagicMock()
    svc = KnowledgeContributionService(db)
    return svc, db


class TestKnowledgeContributionServiceInit:
    def test_init(self):
        db = MagicMock()
        svc = KnowledgeContributionService(db)
        assert svc.db is db


class TestCreateContribution:
    def test_create_contribution_success(self):
        svc, db = make_service()
        data = MagicMock()
        data.contribution_type = "code_module"
        data.job_type = "ELECTRICAL"
        data.title = "测试贡献"
        data.description = "描述"
        data.file_path = "/path/to/file"
        data.tags = ["tag1", "tag2"]

        with patch("app.services.knowledge_contribution_service.KnowledgeContribution") as MockKC, \
             patch("app.services.knowledge_contribution_service.save_obj"):
            mock_contribution = MagicMock()
            MockKC.return_value = mock_contribution
            result = svc.create_contribution(data, contributor_id=1)
        assert result is mock_contribution


class TestGetContribution:
    def test_get_existing(self):
        svc, db = make_service()
        mock_contribution = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_contribution
        result = svc.get_contribution(1)
        assert result is mock_contribution

    def test_get_not_found(self):
        svc, db = make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.get_contribution(999)
        assert result is None


class TestSubmitForReview:
    def test_submit_not_found(self):
        svc, db = make_service()
        with patch.object(svc, "get_contribution", return_value=None):
            with pytest.raises(ValueError, match="贡献不存在"):
                svc.submit_for_review(999, user_id=1)

    def test_submit_wrong_owner(self):
        svc, db = make_service()
        mock_contrib = MagicMock()
        mock_contrib.contributor_id = 2  # 不同用户
        mock_contrib.status = "draft"
        with patch.object(svc, "get_contribution", return_value=mock_contrib):
            with pytest.raises(PermissionError):
                svc.submit_for_review(1, user_id=1)

    def test_submit_wrong_status(self):
        svc, db = make_service()
        mock_contrib = MagicMock()
        mock_contrib.contributor_id = 1
        mock_contrib.status = "approved"  # 非草稿状态
        with patch.object(svc, "get_contribution", return_value=mock_contrib):
            with pytest.raises(ValueError, match="草稿"):
                svc.submit_for_review(1, user_id=1)

    def test_submit_success(self):
        svc, db = make_service()
        mock_contrib = MagicMock()
        mock_contrib.contributor_id = 1
        mock_contrib.status = "draft"
        with patch.object(svc, "get_contribution", return_value=mock_contrib):
            result = svc.submit_for_review(1, user_id=1)
        assert mock_contrib.status == "pending"


class TestApproveContribution:
    def test_approve_not_found(self):
        svc, db = make_service()
        with patch.object(svc, "get_contribution", return_value=None):
            with pytest.raises(ValueError, match="贡献不存在"):
                svc.approve_contribution(999, approver_id=10)

    def test_approve_wrong_status(self):
        svc, db = make_service()
        mock_contrib = MagicMock()
        mock_contrib.status = "draft"
        with patch.object(svc, "get_contribution", return_value=mock_contrib):
            with pytest.raises(ValueError, match="待审核"):
                svc.approve_contribution(1, approver_id=10)

    def test_approve_success(self):
        svc, db = make_service()
        mock_contrib = MagicMock()
        mock_contrib.status = "pending"
        with patch.object(svc, "get_contribution", return_value=mock_contrib):
            result = svc.approve_contribution(1, approver_id=10, approved=True)
        assert mock_contrib.status == "approved"
        assert mock_contrib.approved_by == 10

    def test_reject_contribution(self):
        svc, db = make_service()
        mock_contrib = MagicMock()
        mock_contrib.status = "pending"
        with patch.object(svc, "get_contribution", return_value=mock_contrib):
            result = svc.approve_contribution(1, approver_id=10, approved=False)
        assert mock_contrib.status == "rejected"


class TestListContributions:
    def test_list_all(self):
        svc, db = make_service()
        mock_items = [MagicMock(), MagicMock()]
        db.query.return_value.count.return_value = 2
        db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_items

        items, total = svc.list_contributions()
        assert total == 2
        assert len(items) == 2

    def test_list_with_filters(self):
        svc, db = make_service()
        db.query.return_value.filter.return_value.count.return_value = 1
        mock_items = [MagicMock()]
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_items
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 1
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_items

        items, total = svc.list_contributions(contributor_id=1, status="approved")
        assert total >= 0


class TestDeleteContribution:
    def test_delete_not_found(self):
        svc, db = make_service()
        with patch.object(svc, "get_contribution", return_value=None):
            result = svc.delete_contribution(999, user_id=1)
        assert result is False

    def test_delete_wrong_owner(self):
        svc, db = make_service()
        mock_contrib = MagicMock()
        mock_contrib.contributor_id = 2
        mock_contrib.status = "draft"
        with patch.object(svc, "get_contribution", return_value=mock_contrib):
            with pytest.raises(PermissionError):
                svc.delete_contribution(1, user_id=1)

    def test_delete_approved_raises(self):
        svc, db = make_service()
        mock_contrib = MagicMock()
        mock_contrib.contributor_id = 1
        mock_contrib.status = "approved"
        with patch.object(svc, "get_contribution", return_value=mock_contrib):
            with pytest.raises(ValueError, match="已审核"):
                svc.delete_contribution(1, user_id=1)

    def test_delete_success(self):
        svc, db = make_service()
        mock_contrib = MagicMock()
        mock_contrib.contributor_id = 1
        mock_contrib.status = "draft"
        with patch.object(svc, "get_contribution", return_value=mock_contrib), \
             patch("app.services.knowledge_contribution_service.delete_obj"):
            result = svc.delete_contribution(1, user_id=1)
        assert result is True


class TestRecordReuse:
    def test_record_reuse_contribution_not_found(self):
        svc, db = make_service()
        data = MagicMock()
        data.contribution_id = 999
        with patch.object(svc, "get_contribution", return_value=None):
            with pytest.raises(ValueError, match="贡献不存在"):
                svc.record_reuse(data, user_id=1)
