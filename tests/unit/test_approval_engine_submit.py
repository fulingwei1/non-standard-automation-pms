# -*- coding: utf-8 -*-
"""
approval_engine/engine/submit.py 单元测试

测试审批发起功能的各个方法
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.approval_engine.engine.submit import ApprovalSubmitMixin


def _setup_submit_queries(mock_db, initiator_id=100, initiator_name="Test User", template_name="报价审批"):
    mock_template = MagicMock()
    mock_template.id = 1
    mock_template.template_code = "QUOTE"
    mock_template.template_name = template_name

    mock_user = MagicMock()
    mock_user.id = initiator_id
    mock_user.real_name = initiator_name
    mock_user.username = initiator_name.lower().replace(" ", "_")

    template_query = MagicMock()
    template_query.filter.return_value.first.return_value = mock_template

    user_query = MagicMock()
    user_query.filter.return_value.first.return_value = mock_user

    mock_db.query.side_effect = [template_query, user_query]
    return mock_template, mock_user


@pytest.mark.unit
class TestApprovalSubmitMixinInit:
    """测试 ApprovalSubmitMixin 初始化"""

    def test_init_with_core(self):
        """测试使用ApprovalEngineCore初始化"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)

        # Should inherit methods from core
        assert hasattr(mixin, "submit")
        assert hasattr(mixin, "save_draft")
        assert hasattr(mixin, "_generate_instance_no")
        assert hasattr(mixin, "_get_first_node")


@pytest.mark.unit
class TestSubmitApproval:
    """测试 submit 方法"""

    def test_submit_success_basic(self):
        """测试基本提交成功"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)
        mock_template, mock_user = _setup_submit_queries(mock_db)

        mock_flow = MagicMock()
        mock_flow.id = 200
        mixin.router = MagicMock()
        mixin.router.select_flow.return_value = mock_flow
        mixin._generate_instance_no = MagicMock(return_value="APTEST0001")
        mixin._log_action = MagicMock()
        mixin._get_first_node = MagicMock(return_value=None)

        mock_adapter = MagicMock()
        mock_adapter.validate_submit.return_value = (True, None)
        mock_adapter.get_entity_data.return_value = {"amount": 10000}

        with patch("app.services.approval_engine.engine.submit.get_adapter") as mock_get_adapter:
            mock_get_adapter.return_value = mock_adapter

            result = mixin.submit(
                template_code="QUOTE",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={"amount": 10000},
                initiator_id=100,
            )

            assert result.status == "PENDING"
            assert result.template_id == 1
            assert result.flow_id == 200
            assert result.initiator_id == 100
            assert result.initiator_name == "Test User"

    def test_submit_with_title_and_summary(self):
        """测试带标题和摘要的提交"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)
        _setup_submit_queries(mock_db, template_name="模板")

        mock_flow = MagicMock()
        mock_flow.id = 200
        mixin.router = MagicMock()
        mixin.router.select_flow.return_value = mock_flow
        mixin._generate_instance_no = MagicMock(return_value="APTEST0001")
        mixin._log_action = MagicMock()
        mixin._get_first_node = MagicMock(return_value=None)

        mock_adapter = MagicMock()
        mock_adapter.validate_submit.return_value = (True, None)
        mock_adapter.get_entity_data.return_value = {"amount": 10000}
        mock_adapter.get_title.return_value = "Auto Title"
        mock_adapter.get_summary.return_value = "Auto Summary"

        with patch("app.services.approval_engine.engine.submit.get_adapter") as mock_get_adapter:
            mock_get_adapter.return_value = mock_adapter

            result = mixin.submit(
                template_code="QUOTE",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={"amount": 10000},
                initiator_id=100,
                title="Custom Title",
                summary="Custom Summary",
            )

            assert result.title == "Custom Title"
            assert result.summary == "Custom Summary"

    def test_submit_with_urgency_levels(self):
        """测试不同紧急程度"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)
        _setup_submit_queries(mock_db)

        mock_flow = MagicMock()
        mock_flow.id = 200
        mixin.router = MagicMock()
        mixin.router.select_flow.return_value = mock_flow
        mixin._generate_instance_no = MagicMock(return_value="APTEST0001")
        mixin._log_action = MagicMock()
        mixin._get_first_node = MagicMock(return_value=None)

        mock_adapter = MagicMock()
        mock_adapter.validate_submit.return_value = (True, None)
        mock_adapter.get_entity_data.return_value = {}

        with patch("app.services.approval_engine.engine.submit.get_adapter") as mock_get_adapter:
            mock_get_adapter.return_value = mock_adapter

            # Test URGENCY
            result = mixin.submit(
                template_code="QUOTE",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100,
                urgency="URGENT",
            )

            assert result.urgency == "URGENT"

            mock_db.query.side_effect = None
            _setup_submit_queries(mock_db)
            # Test CRITICAL
            result = mixin.submit(
                template_code="QUOTE",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100,
                urgency="CRITICAL",
            )

            assert result.urgency == "CRITICAL"

    def test_submit_template_not_found(self):
        """测试模板不存在"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="审批模板不存在"):
            mixin.submit(
                template_code="NOTEXIST",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100,
            )

    def test_submit_initiator_not_found(self):
        """测试发起人不存在"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_code = "QUOTE"
        template_query = MagicMock()
        template_query.filter.return_value.first.return_value = mock_template
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = None
        mock_db.query.side_effect = [template_query, user_query]

        with pytest.raises(ValueError, match="发起人不存在"):
            mixin.submit(
                template_code="QUOTE",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=999,
            )

    def test_submit_adapter_validation_failed(self):
        """测试适配器验证失败"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)
        _setup_submit_queries(mock_db)

        mock_adapter = MagicMock()
        mock_adapter.validate_submit.return_value = (False, "Cannot submit")

        with patch("app.services.approval_engine.engine.submit.get_adapter") as mock_get_adapter:
            mock_get_adapter.return_value = mock_adapter

            with pytest.raises(ValueError, match="Cannot submit"):
                mixin.submit(
                    template_code="QUOTE",
                    entity_type="QUOTE",
                    entity_id=1001,
                    form_data={},
                    initiator_id=100,
                )

    def test_submit_with_cc_users(self):
        """测试带抄送人"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)
        _setup_submit_queries(mock_db)

        mock_flow = MagicMock()
        mock_flow.id = 200
        mixin.router = MagicMock()
        mixin.router.select_flow.return_value = mock_flow
        mixin._generate_instance_no = MagicMock(return_value="APTEST0001")
        mixin._log_action = MagicMock()
        mixin._get_first_node = MagicMock(return_value=None)
        mixin.executor = MagicMock()

        mock_adapter = MagicMock()
        mock_adapter.validate_submit.return_value = (True, None)
        mock_adapter.get_entity_data.return_value = {}

        with patch("app.services.approval_engine.engine.submit.get_adapter") as mock_get_adapter:
            mock_get_adapter.return_value = mock_adapter

            result = mixin.submit(
                template_code="QUOTE",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100,
                cc_user_ids=[101, 102],
            )

            assert result.status == "PENDING"
            mixin.executor.create_cc_records.assert_called_once()


@pytest.mark.unit
class TestSaveDraft:
    """测试 save_draft 方法"""

    def test_save_draft_success(self):
        """测试保存草稿成功"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)
        _setup_submit_queries(mock_db)
        mixin._generate_instance_no = MagicMock(return_value="APTEST0001")

        result = mixin.save_draft(
            template_code="QUOTE",
            entity_type="QUOTE",
            entity_id=1001,
            form_data={"amount": 10000},
            initiator_id=100,
        )

        assert result.status == "DRAFT"
        assert result.template_id == 1
        assert result.initiator_id == 100

    def test_save_draft_with_title(self):
        """测试保存带标题的草稿"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)
        _setup_submit_queries(mock_db)
        mixin._generate_instance_no = MagicMock(return_value="APTEST0001")

        result = mixin.save_draft(
            template_code="QUOTE",
            entity_type="QUOTE",
            entity_id=1001,
            form_data={},
            initiator_id=100,
            title="Draft Title",
        )

        assert result.title == "Draft Title"

    def test_save_draft_template_not_found(self):
        """测试模板不存在时保存草稿"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="审批模板不存在"):
            mixin.save_draft(
                template_code="NOTEXIST",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100,
            )


@pytest.mark.unit
class TestApprovalSubmitIntegration:
    """集成测试"""

    def test_all_methods_callable(self):
        """测试所有公共方法可调用"""
        mock_db = MagicMock()
        mixin = ApprovalSubmitMixin(mock_db)

        assert hasattr(mixin, "submit")
        assert hasattr(mixin, "save_draft")
