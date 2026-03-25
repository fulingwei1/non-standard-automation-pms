# -*- coding: utf-8 -*-
"""
审批可见性核心模块单元测试（participant_scope）

覆盖:
- resolve_participant_roles: 发起人 / 审批人 / 代理 / 转审 / 抄送 / 无关人
- ApprovalScopeContext: can_view / can_view_detail / can_comment / can_remind
- can_view_approval_instance / can_comment_on_approval / can_remind_approval
- get_visible_approval_instance_ids: 管理员 / 普通用户 / status 过滤
- apply_approval_visibility: 管理员不过滤 / 普通用户注入 OR 条件
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.approval_engine.approval_scope import (
    COMMENTABLE_ROLES,
    FULL_DETAIL_ROLES,
    REMINDABLE_ROLES,
    SUMMARY_ONLY_ROLES,
    ApprovalScopeContext,
    ParticipantRole,
    apply_approval_visibility,
    build_approval_scope,
    can_comment_on_approval,
    can_remind_approval,
    can_view_approval_instance,
    get_visible_approval_instance_ids,
    resolve_participant_roles,
)


# ---------------------------------------------------------------------------
# ApprovalScopeContext 属性测试
# ---------------------------------------------------------------------------


class TestApprovalScopeContext:

    def test_admin_can_do_everything(self):
        ctx = ApprovalScopeContext(user_id=1, is_admin=True)
        assert ctx.can_view
        assert ctx.can_view_detail
        assert ctx.can_comment
        assert ctx.can_remind

    def test_initiator_full_access(self):
        ctx = ApprovalScopeContext(
            user_id=1,
            roles_in_instance={ParticipantRole.INITIATOR},
        )
        assert ctx.can_view
        assert ctx.can_view_detail
        assert ctx.can_comment
        assert ctx.can_remind  # 发起人可催办

    def test_approver_full_detail_can_comment_no_remind(self):
        ctx = ApprovalScopeContext(
            user_id=2,
            roles_in_instance={ParticipantRole.APPROVER},
        )
        assert ctx.can_view
        assert ctx.can_view_detail
        assert ctx.can_comment
        assert not ctx.can_remind  # 审批人不可催办

    def test_delegated_approver_full_detail(self):
        ctx = ApprovalScopeContext(
            user_id=3,
            roles_in_instance={ParticipantRole.DELEGATED_APPROVER},
        )
        assert ctx.can_view
        assert ctx.can_view_detail
        assert ctx.can_comment
        assert not ctx.can_remind

    def test_transferred_approver_full_detail(self):
        ctx = ApprovalScopeContext(
            user_id=4,
            roles_in_instance={ParticipantRole.TRANSFERRED_APPROVER},
        )
        assert ctx.can_view
        assert ctx.can_view_detail
        assert ctx.can_comment
        assert not ctx.can_remind

    def test_cc_summary_only(self):
        ctx = ApprovalScopeContext(
            user_id=5,
            roles_in_instance={ParticipantRole.CC},
        )
        assert ctx.can_view
        assert not ctx.can_view_detail  # 抄送人不可看详情
        assert not ctx.can_comment  # 抄送人不可评论
        assert not ctx.can_remind

    def test_no_roles_no_access(self):
        ctx = ApprovalScopeContext(user_id=99)
        assert not ctx.can_view
        assert not ctx.can_view_detail
        assert not ctx.can_comment
        assert not ctx.can_remind

    def test_multiple_roles_union(self):
        """同时是发起人和抄送人 → 取并集，拥有完整权限"""
        ctx = ApprovalScopeContext(
            user_id=1,
            roles_in_instance={ParticipantRole.INITIATOR, ParticipantRole.CC},
        )
        assert ctx.can_view
        assert ctx.can_view_detail
        assert ctx.can_comment
        assert ctx.can_remind


# ---------------------------------------------------------------------------
# 角色集合完整性
# ---------------------------------------------------------------------------


class TestRoleCollections:

    def test_full_detail_roles_not_include_cc(self):
        assert ParticipantRole.CC not in FULL_DETAIL_ROLES

    def test_summary_only_roles_is_cc(self):
        assert ParticipantRole.CC in SUMMARY_ONLY_ROLES

    def test_commentable_roles_not_include_cc(self):
        assert ParticipantRole.CC not in COMMENTABLE_ROLES

    def test_remindable_roles_only_initiator_and_admin(self):
        assert REMINDABLE_ROLES == {
            ParticipantRole.INITIATOR,
            ParticipantRole.ADMIN,
        }


# ---------------------------------------------------------------------------
# resolve_participant_roles
# ---------------------------------------------------------------------------


class TestResolveParticipantRoles:

    def _mock_db(
        self,
        is_initiator=False,
        task_types=None,
        is_cc=False,
    ):
        """构造 mock db，控制各查询的返回值"""
        db = MagicMock()

        # 链式调用模拟器
        def make_chain(return_val):
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.first.return_value = return_val
            chain.all.return_value = return_val if isinstance(return_val, list) else []
            return chain

        # 三次 db.query() 分别对应 initiator / tasks / cc
        initiator_chain = make_chain((1,) if is_initiator else None)
        task_chain = make_chain(
            [(t,) for t in (task_types or [])]
        )
        cc_chain = make_chain((1,) if is_cc else None)

        db.query.side_effect = [initiator_chain, task_chain, cc_chain]
        return db

    def test_initiator(self):
        db = self._mock_db(is_initiator=True)
        roles = resolve_participant_roles(db, instance_id=1, user_id=10)
        assert ParticipantRole.INITIATOR in roles

    def test_normal_approver(self):
        db = self._mock_db(task_types=["NORMAL"])
        roles = resolve_participant_roles(db, instance_id=1, user_id=20)
        assert ParticipantRole.APPROVER in roles

    def test_delegated_approver(self):
        db = self._mock_db(task_types=["DELEGATED"])
        roles = resolve_participant_roles(db, instance_id=1, user_id=30)
        assert ParticipantRole.DELEGATED_APPROVER in roles

    def test_transferred_approver(self):
        db = self._mock_db(task_types=["TRANSFERRED"])
        roles = resolve_participant_roles(db, instance_id=1, user_id=40)
        assert ParticipantRole.TRANSFERRED_APPROVER in roles

    def test_added_before_counted_as_approver(self):
        """前加签视为普通审批人"""
        db = self._mock_db(task_types=["ADDED_BEFORE"])
        roles = resolve_participant_roles(db, instance_id=1, user_id=50)
        assert ParticipantRole.APPROVER in roles

    def test_added_after_counted_as_approver(self):
        """后加签视为普通审批人"""
        db = self._mock_db(task_types=["ADDED_AFTER"])
        roles = resolve_participant_roles(db, instance_id=1, user_id=60)
        assert ParticipantRole.APPROVER in roles

    def test_cc(self):
        db = self._mock_db(is_cc=True)
        roles = resolve_participant_roles(db, instance_id=1, user_id=70)
        assert ParticipantRole.CC in roles

    def test_no_participation(self):
        db = self._mock_db()
        roles = resolve_participant_roles(db, instance_id=1, user_id=999)
        assert len(roles) == 0

    def test_multiple_roles(self):
        """用户既是发起人又是审批人"""
        db = self._mock_db(is_initiator=True, task_types=["NORMAL"])
        roles = resolve_participant_roles(db, instance_id=1, user_id=10)
        assert ParticipantRole.INITIATOR in roles
        assert ParticipantRole.APPROVER in roles

    def test_multiple_task_types(self):
        """用户同时有代理和转审任务"""
        db = self._mock_db(task_types=["DELEGATED", "TRANSFERRED"])
        roles = resolve_participant_roles(db, instance_id=1, user_id=30)
        assert ParticipantRole.DELEGATED_APPROVER in roles
        assert ParticipantRole.TRANSFERRED_APPROVER in roles


# ---------------------------------------------------------------------------
# 公开 API：单条判断
# ---------------------------------------------------------------------------


class TestCanViewApprovalInstance:

    @patch("app.services.approval_engine.approval_scope.build_approval_scope")
    def test_admin_skips_db_check(self, mock_build):
        result = can_view_approval_instance(MagicMock(), 1, 10, is_admin=True)
        assert result is True
        mock_build.assert_not_called()

    @patch("app.services.approval_engine.approval_scope.build_approval_scope")
    def test_participant_can_view(self, mock_build):
        mock_build.return_value = ApprovalScopeContext(
            user_id=10,
            roles_in_instance={ParticipantRole.APPROVER},
        )
        result = can_view_approval_instance(MagicMock(), 1, 10)
        assert result is True

    @patch("app.services.approval_engine.approval_scope.build_approval_scope")
    def test_non_participant_cannot_view(self, mock_build):
        mock_build.return_value = ApprovalScopeContext(user_id=99)
        result = can_view_approval_instance(MagicMock(), 1, 99)
        assert result is False


class TestCanCommentOnApproval:

    @patch("app.services.approval_engine.approval_scope.build_approval_scope")
    def test_admin_can_comment(self, mock_build):
        result = can_comment_on_approval(MagicMock(), 1, 10, is_admin=True)
        assert result is True
        mock_build.assert_not_called()

    @patch("app.services.approval_engine.approval_scope.build_approval_scope")
    def test_cc_cannot_comment(self, mock_build):
        mock_build.return_value = ApprovalScopeContext(
            user_id=5,
            roles_in_instance={ParticipantRole.CC},
        )
        result = can_comment_on_approval(MagicMock(), 1, 5)
        assert result is False

    @patch("app.services.approval_engine.approval_scope.build_approval_scope")
    def test_initiator_can_comment(self, mock_build):
        mock_build.return_value = ApprovalScopeContext(
            user_id=10,
            roles_in_instance={ParticipantRole.INITIATOR},
        )
        result = can_comment_on_approval(MagicMock(), 1, 10)
        assert result is True


class TestCanRemindApproval:

    @patch("app.services.approval_engine.approval_scope.build_approval_scope")
    def test_admin_can_remind(self, mock_build):
        result = can_remind_approval(MagicMock(), 1, 10, is_admin=True)
        assert result is True
        mock_build.assert_not_called()

    @patch("app.services.approval_engine.approval_scope.build_approval_scope")
    def test_initiator_can_remind(self, mock_build):
        mock_build.return_value = ApprovalScopeContext(
            user_id=10,
            roles_in_instance={ParticipantRole.INITIATOR},
        )
        result = can_remind_approval(MagicMock(), 1, 10)
        assert result is True

    @patch("app.services.approval_engine.approval_scope.build_approval_scope")
    def test_approver_cannot_remind(self, mock_build):
        mock_build.return_value = ApprovalScopeContext(
            user_id=20,
            roles_in_instance={ParticipantRole.APPROVER},
        )
        result = can_remind_approval(MagicMock(), 1, 20)
        assert result is False

    @patch("app.services.approval_engine.approval_scope.build_approval_scope")
    def test_cc_cannot_remind(self, mock_build):
        mock_build.return_value = ApprovalScopeContext(
            user_id=5,
            roles_in_instance={ParticipantRole.CC},
        )
        result = can_remind_approval(MagicMock(), 1, 5)
        assert result is False


# ---------------------------------------------------------------------------
# get_visible_approval_instance_ids
# ---------------------------------------------------------------------------


class TestGetVisibleApprovalInstanceIds:

    def test_admin_queries_all(self):
        """管理员直接查全表"""
        db = MagicMock()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = [(3,), (2,), (1,)]

        ids = get_visible_approval_instance_ids(db, user_id=1, is_admin=True)
        assert ids == [3, 2, 1]

    def test_admin_with_status_filter(self):
        """管理员 + 状态过滤"""
        db = MagicMock()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = [(5,)]

        ids = get_visible_approval_instance_ids(
            db, user_id=1, is_admin=True, status="PENDING"
        )
        assert ids == [5]
        # 验证 filter 被调用过（status 过滤）
        chain.filter.assert_called()

    def test_normal_user_union_query(self):
        """普通用户走 UNION 三表查询"""
        db = MagicMock()
        # 链式调用：db.query().filter() 等全部返回同一个 chain
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = [(10,), (20,)]

        # union_all 返回一个带 .subquery() 的 mock
        with patch(
            "app.services.approval_engine.approval_scope.union_all"
        ) as mock_union:
            mock_subq = MagicMock()
            # .c[0] 需要返回一个可被 db.query() 接受的值
            mock_union.return_value.subquery.return_value = mock_subq

            ids = get_visible_approval_instance_ids(db, user_id=42, is_admin=False)
            assert ids == [10, 20]
            mock_union.assert_called_once()


# ---------------------------------------------------------------------------
# apply_approval_visibility
# ---------------------------------------------------------------------------


class TestApplyApprovalVisibility:

    def test_admin_returns_query_unchanged(self):
        query = MagicMock()
        result = apply_approval_visibility(query, user_id=1, is_admin=True)
        assert result is query
        query.filter.assert_not_called()

    def test_normal_user_injects_filter(self):
        query = MagicMock()
        query.filter.return_value = query
        result = apply_approval_visibility(query, user_id=42, is_admin=False)
        query.filter.assert_called_once()


# ---------------------------------------------------------------------------
# build_approval_scope 集成
# ---------------------------------------------------------------------------


class TestBuildApprovalScope:

    @patch("app.services.approval_engine.approval_scope.resolve_participant_roles")
    def test_builds_context_with_roles(self, mock_resolve):
        mock_resolve.return_value = {
            ParticipantRole.INITIATOR,
            ParticipantRole.APPROVER,
        }
        db = MagicMock()
        ctx = build_approval_scope(db, instance_id=1, user_id=10, is_admin=False)

        assert ctx.user_id == 10
        assert not ctx.is_admin
        assert ParticipantRole.INITIATOR in ctx.roles_in_instance
        assert ParticipantRole.APPROVER in ctx.roles_in_instance
        assert ctx.can_view
        assert ctx.can_view_detail
        assert ctx.can_comment
        assert ctx.can_remind

    @patch("app.services.approval_engine.approval_scope.resolve_participant_roles")
    def test_admin_flag_propagated(self, mock_resolve):
        mock_resolve.return_value = set()
        db = MagicMock()
        ctx = build_approval_scope(db, instance_id=1, user_id=10, is_admin=True)

        assert ctx.is_admin
        assert ctx.can_view
        assert ctx.can_view_detail
