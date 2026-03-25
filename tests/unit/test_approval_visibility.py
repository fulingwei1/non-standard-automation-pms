# -*- coding: utf-8 -*-
"""
审批参与者可见性控制单元测试

覆盖规则：
- 发起人可见自己发起的审批
- 审批人可见分配给自己的审批
- 抄送人可见被抄送的审批
- 审批管理员可见全部审批
- 超级管理员可见全部审批
- 非参与者不可见（fail-closed）
- 异常场景 fail-closed
- 列表查询正确过滤
- 写操作权限控制（催办、加抄送、终止）

测试层级：service/unit 级，通过 mock 隔离数据库依赖
"""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id=1, is_superuser=False, tenant_id=1):
    """构造模拟用户"""
    user = MagicMock()
    user.id = user_id
    user.is_superuser = is_superuser
    user.tenant_id = tenant_id if not is_superuser else None
    user.username = f"user_{user_id}"
    user.is_active = True
    return user


def _make_task(task_id=1, instance_id=100, assignee_id=10):
    """构造模拟审批任务"""
    task = MagicMock()
    task.id = task_id
    task.instance_id = instance_id
    task.assignee_id = assignee_id
    return task


def _mock_db_for_role(
    is_initiator=False,
    has_task=False,
    has_cc=False,
):
    """
    构造 mock db，控制三种参与关系的查询结果。

    db.query(Model.id).filter(...).first() 返回 MagicMock 或 None
    """
    db = MagicMock()

    # 记录调用顺序
    call_count = {"value": 0}
    order = []
    if True:  # 始终查 initiator（第一次）
        order.append(is_initiator)
    order.append(has_task)
    order.append(has_cc)

    def query_side_effect(*args, **kwargs):
        inner = MagicMock()

        def filter_side_effect(*a, **kw):
            filtered = MagicMock()
            idx = call_count["value"]
            call_count["value"] += 1
            if idx < len(order) and order[idx]:
                filtered.first.return_value = MagicMock()  # 找到了
            else:
                filtered.first.return_value = None  # 没找到
            return filtered

        inner.filter.side_effect = filter_side_effect
        return inner

    db.query.side_effect = query_side_effect
    return db


# ===========================================================================
# 一、resolve_participant_role 测试
# ===========================================================================

class TestResolveParticipantRole:
    """测试参与角色解析"""

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=True)
    def test_admin_role(self, mock_admin):
        """管理员角色优先"""
        from app.services.approval_engine.visibility import resolve_participant_role, ParticipantRole

        db = MagicMock()
        user = _make_user(user_id=1)
        result = resolve_participant_role(db, instance_id=100, user=user)
        assert result == ParticipantRole.ADMIN

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_initiator_role(self, mock_admin):
        """发起人角色"""
        from app.services.approval_engine.visibility import resolve_participant_role, ParticipantRole

        db = _mock_db_for_role(is_initiator=True)
        user = _make_user(user_id=5)
        result = resolve_participant_role(db, instance_id=100, user=user)
        assert result == ParticipantRole.INITIATOR

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_approver_role(self, mock_admin):
        """审批人角色"""
        from app.services.approval_engine.visibility import resolve_participant_role, ParticipantRole

        db = _mock_db_for_role(is_initiator=False, has_task=True)
        user = _make_user(user_id=10)
        result = resolve_participant_role(db, instance_id=100, user=user)
        assert result == ParticipantRole.APPROVER

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_cc_role(self, mock_admin):
        """抄送人角色"""
        from app.services.approval_engine.visibility import resolve_participant_role, ParticipantRole

        db = _mock_db_for_role(is_initiator=False, has_task=False, has_cc=True)
        user = _make_user(user_id=20)
        result = resolve_participant_role(db, instance_id=100, user=user)
        assert result == ParticipantRole.CC

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_none_role(self, mock_admin):
        """非参与者"""
        from app.services.approval_engine.visibility import resolve_participant_role, ParticipantRole

        db = _mock_db_for_role(is_initiator=False, has_task=False, has_cc=False)
        user = _make_user(user_id=99)
        result = resolve_participant_role(db, instance_id=100, user=user)
        assert result == ParticipantRole.NONE

    @patch("app.services.approval_engine.visibility._is_approval_admin", side_effect=RuntimeError("boom"))
    def test_exception_returns_none(self, mock_admin):
        """异常时 fail-closed 返回 NONE"""
        from app.services.approval_engine.visibility import resolve_participant_role, ParticipantRole

        db = MagicMock()
        user = _make_user(user_id=1)
        result = resolve_participant_role(db, instance_id=100, user=user)
        assert result == ParticipantRole.NONE


# ===========================================================================
# 二、check_instance_visible 测试
# ===========================================================================

class TestCheckInstanceVisible:
    """测试单实例可见性检查"""

    @patch("app.services.approval_engine.visibility.resolve_participant_role")
    def test_initiator_can_see(self, mock_resolve):
        """发起人可见"""
        from app.services.approval_engine.visibility import check_instance_visible, ParticipantRole
        mock_resolve.return_value = ParticipantRole.INITIATOR
        assert check_instance_visible(MagicMock(), 100, _make_user()) is True

    @patch("app.services.approval_engine.visibility.resolve_participant_role")
    def test_approver_can_see(self, mock_resolve):
        """审批人可见"""
        from app.services.approval_engine.visibility import check_instance_visible, ParticipantRole
        mock_resolve.return_value = ParticipantRole.APPROVER
        assert check_instance_visible(MagicMock(), 100, _make_user()) is True

    @patch("app.services.approval_engine.visibility.resolve_participant_role")
    def test_cc_can_see(self, mock_resolve):
        """抄送人可见"""
        from app.services.approval_engine.visibility import check_instance_visible, ParticipantRole
        mock_resolve.return_value = ParticipantRole.CC
        assert check_instance_visible(MagicMock(), 100, _make_user()) is True

    @patch("app.services.approval_engine.visibility.resolve_participant_role")
    def test_admin_can_see(self, mock_resolve):
        """管理员可见"""
        from app.services.approval_engine.visibility import check_instance_visible, ParticipantRole
        mock_resolve.return_value = ParticipantRole.ADMIN
        assert check_instance_visible(MagicMock(), 100, _make_user()) is True

    @patch("app.services.approval_engine.visibility.resolve_participant_role")
    def test_non_participant_cannot_see(self, mock_resolve):
        """非参与者不可见"""
        from app.services.approval_engine.visibility import check_instance_visible, ParticipantRole
        mock_resolve.return_value = ParticipantRole.NONE
        assert check_instance_visible(MagicMock(), 100, _make_user()) is False


# ===========================================================================
# 三、check_task_visible 测试
# ===========================================================================

class TestCheckTaskVisible:
    """测试任务可见性检查"""

    @patch("app.services.approval_engine.visibility.check_instance_visible")
    def test_delegates_to_instance_check(self, mock_check):
        """任务可见性委托给实例可见性"""
        from app.services.approval_engine.visibility import check_task_visible

        mock_check.return_value = True
        task = _make_task(instance_id=100)
        db = MagicMock()
        user = _make_user()

        assert check_task_visible(db, task, user) is True
        mock_check.assert_called_once_with(db, 100, user)

    @patch("app.services.approval_engine.visibility.check_instance_visible")
    def test_non_participant_task_invisible(self, mock_check):
        """非参与者看不到任务"""
        from app.services.approval_engine.visibility import check_task_visible

        mock_check.return_value = False
        task = _make_task(instance_id=100)

        assert check_task_visible(MagicMock(), task, _make_user()) is False


# ===========================================================================
# 四、filter_visible_instances 测试
# ===========================================================================

class TestFilterVisibleInstances:
    """测试列表查询可见性过滤"""

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=True)
    def test_admin_sees_all(self, mock_admin):
        """管理员看全部，query 不被过滤"""
        from app.services.approval_engine.visibility import filter_visible_instances

        query = MagicMock()
        db = MagicMock()
        user = _make_user()

        result = filter_visible_instances(query, db, user)
        assert result is query
        query.filter.assert_not_called()

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_normal_user_gets_filtered(self, mock_admin):
        """普通用户查询被过滤"""
        from app.services.approval_engine.visibility import filter_visible_instances

        query = MagicMock()
        filtered_query = MagicMock()
        query.filter.return_value = filtered_query
        db = MagicMock()
        user = _make_user()

        result = filter_visible_instances(query, db, user)
        assert result is filtered_query
        query.filter.assert_called_once()

    @patch("app.services.approval_engine.visibility._is_approval_admin", side_effect=RuntimeError("boom"))
    def test_exception_returns_empty(self, mock_admin):
        """异常时 fail-closed 返回空"""
        from app.services.approval_engine.visibility import filter_visible_instances

        query = MagicMock()
        empty_query = MagicMock()
        query.filter.return_value = empty_query
        db = MagicMock()
        user = _make_user()

        result = filter_visible_instances(query, db, user)
        query.filter.assert_called_once_with(False)


# ===========================================================================
# 五、写操作权限控制测试
# ===========================================================================

class TestOperationPermissions:
    """测试写操作权限控制"""

    @patch("app.services.approval_engine.visibility.resolve_participant_role")
    def test_initiator_can_operate(self, mock_resolve):
        """发起人可执行写操作"""
        from app.services.approval_engine.visibility import check_can_operate_instance, ParticipantRole
        mock_resolve.return_value = ParticipantRole.INITIATOR
        assert check_can_operate_instance(MagicMock(), 100, _make_user()) is True

    @patch("app.services.approval_engine.visibility.resolve_participant_role")
    def test_cc_cannot_operate(self, mock_resolve):
        """抄送人不能执行写操作"""
        from app.services.approval_engine.visibility import check_can_operate_instance, ParticipantRole
        mock_resolve.return_value = ParticipantRole.CC
        assert check_can_operate_instance(MagicMock(), 100, _make_user()) is False

    @patch("app.services.approval_engine.visibility.resolve_participant_role")
    def test_none_cannot_operate(self, mock_resolve):
        """非参与者不能执行写操作"""
        from app.services.approval_engine.visibility import check_can_operate_instance, ParticipantRole
        mock_resolve.return_value = ParticipantRole.NONE
        assert check_can_operate_instance(MagicMock(), 100, _make_user()) is False

    @patch("app.services.approval_engine.visibility.resolve_participant_role")
    def test_terminate_only_admin(self, mock_resolve):
        """终止操作仅管理员可执行"""
        from app.services.approval_engine.visibility import check_can_operate_instance, ParticipantRole

        # 发起人不能终止
        mock_resolve.return_value = ParticipantRole.INITIATOR
        assert check_can_operate_instance(
            MagicMock(), 100, _make_user(),
            allowed_roles=(ParticipantRole.ADMIN,),
        ) is False

        # 管理员可以终止
        mock_resolve.return_value = ParticipantRole.ADMIN
        assert check_can_operate_instance(
            MagicMock(), 100, _make_user(),
            allowed_roles=(ParticipantRole.ADMIN,),
        ) is True


# ===========================================================================
# 六、催办权限测试
# ===========================================================================

class TestCanRemind:
    """测试催办权限控制"""

    @patch("app.services.approval_engine.visibility.check_can_operate_instance")
    def test_initiator_can_remind(self, mock_check):
        """发起人可催办"""
        from app.services.approval_engine.visibility import check_can_remind

        mock_check.return_value = True
        task = _make_task()
        assert check_can_remind(MagicMock(), task, _make_user()) is True

    @patch("app.services.approval_engine.visibility.check_can_operate_instance")
    def test_cc_cannot_remind(self, mock_check):
        """抄送人不能催办"""
        from app.services.approval_engine.visibility import check_can_remind

        mock_check.return_value = False
        task = _make_task()
        assert check_can_remind(MagicMock(), task, _make_user()) is False


# ===========================================================================
# 七、_is_approval_admin 测试
# ===========================================================================

class TestIsApprovalAdmin:
    """测试管理员判断"""

    def test_superuser_is_admin(self):
        """超级管理员自动通过"""
        from app.services.approval_engine.visibility import _is_approval_admin

        user = _make_user(is_superuser=True)
        db = MagicMock()
        assert _is_approval_admin(user, db) is True

    @patch("app.services.approval_engine.visibility.check_permission", return_value=True)
    def test_approval_admin_permission(self, mock_perm):
        """持有 approval:admin 权限"""
        from app.services.approval_engine.visibility import _is_approval_admin

        user = _make_user(is_superuser=False)
        db = MagicMock()
        assert _is_approval_admin(user, db) is True
        mock_perm.assert_called_once_with(user, "approval:admin", db)

    @patch("app.services.approval_engine.visibility.check_permission", return_value=False)
    def test_normal_user_not_admin(self, mock_perm):
        """普通用户非管理员"""
        from app.services.approval_engine.visibility import _is_approval_admin

        user = _make_user(is_superuser=False)
        db = MagicMock()
        assert _is_approval_admin(user, db) is False


# ===========================================================================
# 八、业务场景端到端测试
# ===========================================================================

class TestApprovalVisibilityScenarios:
    """模拟真实业务场景的可见性测试"""

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_submitter_can_see_own_approval(self, mock_admin):
        """场景：张三提交了报价审批，张三可以查看"""
        from app.services.approval_engine.visibility import check_instance_visible

        db = _mock_db_for_role(is_initiator=True)
        zhangsan = _make_user(user_id=1)
        assert check_instance_visible(db, 100, zhangsan) is True

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_approver_can_see_assigned_approval(self, mock_admin):
        """场景：李四被分配为审批人，可以查看"""
        from app.services.approval_engine.visibility import check_instance_visible

        db = _mock_db_for_role(is_initiator=False, has_task=True)
        lisi = _make_user(user_id=2)
        assert check_instance_visible(db, 100, lisi) is True

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_cc_can_see_but_limited(self, mock_admin):
        """场景：王五被抄送，可以查看（但实际UI应限制form_data）"""
        from app.services.approval_engine.visibility import check_instance_visible

        db = _mock_db_for_role(is_initiator=False, has_task=False, has_cc=True)
        wangwu = _make_user(user_id=3)
        assert check_instance_visible(db, 100, wangwu) is True

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_random_user_cannot_see(self, mock_admin):
        """场景：赵六与此审批无关，不可查看"""
        from app.services.approval_engine.visibility import check_instance_visible

        db = _mock_db_for_role(is_initiator=False, has_task=False, has_cc=False)
        zhaoliu = _make_user(user_id=99)
        assert check_instance_visible(db, 100, zhaoliu) is False

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_cc_cannot_add_cc(self, mock_admin):
        """场景：抄送人不能加抄送"""
        from app.services.approval_engine.visibility import check_can_operate_instance

        db = _mock_db_for_role(is_initiator=False, has_task=False, has_cc=True)
        cc_user = _make_user(user_id=20)
        assert check_can_operate_instance(db, 100, cc_user) is False

    @patch("app.services.approval_engine.visibility._is_approval_admin", return_value=False)
    def test_initiator_can_add_cc(self, mock_admin):
        """场景：发起人可以加抄送"""
        from app.services.approval_engine.visibility import check_can_operate_instance

        db = _mock_db_for_role(is_initiator=True)
        initiator = _make_user(user_id=1)
        assert check_can_operate_instance(db, 100, initiator) is True
