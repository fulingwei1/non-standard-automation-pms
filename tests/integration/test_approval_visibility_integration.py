# -*- coding: utf-8 -*-
"""
审批参与者可见性集成测试

使用 SQLite 内存数据库，直接调用 visibility / approval_scope 服务层函数，
验证参与者角色解析、列表过滤、评论/催办权限边界。

覆盖场景：
  1. 参与者（发起人/审批人/抄送人）可见
  2. 非参与者不可见
  3. 管理员（approval:admin / superuser）可见所有
  4. 催办权限：发起人/管理员可催，抄送人/审批人不可催
  5. 评论权限：抄送人不可评论，审批人/发起人可评论
  6. 列表过滤正确返回参与实例
"""

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from sqlalchemy import Column, Integer, Table, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


def _create_test_engine():
    """创建测试专用 SQLite 内存引擎。"""
    import app.models  # noqa: F401

    for stub in ["production_work_orders", "suppliers"]:
        if stub not in Base.metadata.tables:
            Table(stub, Base.metadata, Column("id", Integer, primary_key=True))

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in Base.metadata.sorted_tables:
        try:
            table.create(bind=engine, checkfirst=True)
        except Exception:
            pass
    return engine


@pytest.fixture(scope="function")
def db():
    engine = _create_test_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(db, username, real_name="测试用户", is_superuser=False):
    from app.models.user import User

    user = User(
        username=username,
        password_hash="hashed_pw",
        real_name=real_name,
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.flush()
    return user


def _make_template(db, user_id):
    from app.models.approval import ApprovalTemplate

    tmpl = ApprovalTemplate(
        template_code=f"TMPL-VIS-{uuid.uuid4().hex[:6]}",
        template_name="可见性测试模板",
        category="PROJECT",
        entity_type="PROJECT",
        description="测试",
        version=1,
        is_published=True,
        published_at=datetime.now(),
        published_by=user_id,
    )
    db.add(tmpl)
    db.flush()
    return tmpl


def _make_flow(db, template_id, user_id):
    from app.models.approval import ApprovalFlowDefinition

    flow = ApprovalFlowDefinition(
        template_id=template_id,
        flow_name="默认流程",
        description="测试",
        is_default=True,
        version=1,
        is_active=True,
        created_by=user_id,
    )
    db.add(flow)
    db.flush()
    return flow


def _make_node(db, flow_id, order=1):
    from app.models.approval import ApprovalNodeDefinition

    node = ApprovalNodeDefinition(
        flow_id=flow_id,
        node_name="审批节点",
        node_type="APPROVAL",
        node_order=order,
        approval_mode="SINGLE",
        is_active=True,
    )
    db.add(node)
    db.flush()
    return node


def _make_instance(db, template_id, flow_id, node_id, initiator_id):
    from app.models.approval import ApprovalInstance

    inst = ApprovalInstance(
        instance_no=f"AP-VIS-{uuid.uuid4().hex[:8]}",
        template_id=template_id,
        flow_id=flow_id,
        entity_type="PROJECT",
        entity_id=1,
        initiator_id=initiator_id,
        initiator_name="发起人",
        form_data={"title": "可见性测试"},
        status="PENDING",
        current_node_id=node_id,
        current_node_order=1,
        urgency="NORMAL",
        title="可见性测试审批",
        summary="测试",
    )
    db.add(inst)
    db.flush()
    return inst


def _make_task(db, instance_id, node_id, assignee_id, assignee_type="NORMAL"):
    from app.models.approval import ApprovalTask

    task = ApprovalTask(
        instance_id=instance_id,
        node_id=node_id,
        task_type="APPROVAL",
        task_order=1,
        assignee_id=assignee_id,
        assignee_name="审批人",
        assignee_type=assignee_type,
        status="PENDING",
    )
    db.add(task)
    db.flush()
    return task


def _make_cc(db, instance_id, cc_user_id):
    from app.models.approval.task import ApprovalCarbonCopy

    cc = ApprovalCarbonCopy(
        instance_id=instance_id,
        cc_user_id=cc_user_id,
        cc_user_name="抄送人",
        cc_source="FLOW",
        is_read=False,
    )
    db.add(cc)
    db.flush()
    return cc


def _setup_scenario(db):
    """创建包含所有角色的标准场景，返回 (instance, initiator, approver, cc_user, outsider, task)。"""
    initiator = _make_user(db, "initiator01", "发起人")
    approver = _make_user(db, "approver01", "审批人")
    cc_user = _make_user(db, "cc01", "抄送人")
    outsider = _make_user(db, "outsider01", "外部人员")

    tmpl = _make_template(db, initiator.id)
    flow = _make_flow(db, tmpl.id, initiator.id)
    node = _make_node(db, flow.id)
    instance = _make_instance(db, tmpl.id, flow.id, node.id, initiator.id)
    task = _make_task(db, instance.id, node.id, approver.id)
    _make_cc(db, instance.id, cc_user.id)

    db.commit()
    return instance, initiator, approver, cc_user, outsider, task


# ===========================================================================
# Tests — visibility.py（直接 DB 调用）
# ===========================================================================


@pytest.mark.integration
@pytest.mark.permission
class TestParticipantVisibility:
    """TC-VIS-1x: 参与者可见性判断"""

    def test_initiator_can_view(self, db):
        """TC-VIS-11: 发起人可以看到自己发起的审批实例。"""
        from app.services.approval_engine.visibility import (
            check_instance_visible,
            resolve_participant_role,
            ParticipantRole,
        )

        instance, initiator, *_ = _setup_scenario(db)

        role = resolve_participant_role(db, instance.id, initiator)
        assert role == ParticipantRole.INITIATOR

        assert check_instance_visible(db, instance.id, initiator) is True

    def test_approver_can_view(self, db):
        """TC-VIS-12: 审批人可以看到分配给自己的审批实例。"""
        from app.services.approval_engine.visibility import (
            check_instance_visible,
            resolve_participant_role,
            ParticipantRole,
        )

        instance, _, approver, *_ = _setup_scenario(db)

        role = resolve_participant_role(db, instance.id, approver)
        assert role == ParticipantRole.APPROVER

        assert check_instance_visible(db, instance.id, approver) is True

    def test_cc_user_can_view(self, db):
        """TC-VIS-13: 抄送人可以看到被抄送的审批实例。"""
        from app.services.approval_engine.visibility import (
            check_instance_visible,
            resolve_participant_role,
            ParticipantRole,
        )

        instance, _, _, cc_user, *_ = _setup_scenario(db)

        role = resolve_participant_role(db, instance.id, cc_user)
        assert role == ParticipantRole.CC

        assert check_instance_visible(db, instance.id, cc_user) is True


@pytest.mark.integration
@pytest.mark.permission
class TestNonParticipantInvisible:
    """TC-VIS-2x: 非参与者不可见"""

    def test_outsider_cannot_view(self, db):
        """TC-VIS-21: 与审批无关的用户无法看到该实例。"""
        from app.services.approval_engine.visibility import (
            check_instance_visible,
            resolve_participant_role,
            ParticipantRole,
        )

        instance, _, _, _, outsider, _ = _setup_scenario(db)

        role = resolve_participant_role(db, instance.id, outsider)
        assert role == ParticipantRole.NONE

        assert check_instance_visible(db, instance.id, outsider) is False

    def test_filter_excludes_non_participant(self, db):
        """TC-VIS-22: 列表过滤不会返回非参与者的实例。"""
        from app.models.approval.instance import ApprovalInstance
        from app.services.approval_engine.visibility import filter_visible_instances

        instance, _, _, _, outsider, _ = _setup_scenario(db)

        query = db.query(ApprovalInstance)
        # outsider 不是 admin，mock check_permission 返回 False
        with patch("app.services.approval_engine.visibility.check_permission", return_value=False):
            filtered = filter_visible_instances(query, db, outsider)

        results = filtered.all()
        instance_ids = [r.id for r in results]
        assert instance.id not in instance_ids


@pytest.mark.integration
@pytest.mark.permission
class TestAdminVisibility:
    """TC-VIS-3x: 管理员可见所有"""

    def test_superuser_can_view_all(self, db):
        """TC-VIS-31: 超管可以看到所有审批实例。"""
        from app.services.approval_engine.visibility import check_instance_visible

        instance, *_ = _setup_scenario(db)
        admin = _make_user(db, "superadmin", "超管", is_superuser=True)
        db.commit()

        assert check_instance_visible(db, instance.id, admin) is True

    def test_approval_admin_can_view_all(self, db):
        """TC-VIS-32: 持有 approval:admin 权限的用户可以看到所有审批实例。"""
        from app.services.approval_engine.visibility import (
            check_instance_visible,
            resolve_participant_role,
            ParticipantRole,
        )

        instance, *_ = _setup_scenario(db)
        admin_user = _make_user(db, "approval_admin", "审批管理员")
        db.commit()

        # mock check_permission 让该用户持有 approval:admin
        with patch(
            "app.services.approval_engine.visibility.check_permission",
            return_value=True,
        ):
            role = resolve_participant_role(db, instance.id, admin_user)
            assert role == ParticipantRole.ADMIN
            assert check_instance_visible(db, instance.id, admin_user) is True

    def test_admin_filter_returns_all(self, db):
        """TC-VIS-33: 管理员的列表过滤不做任何限制，返回所有实例。"""
        from app.models.approval.instance import ApprovalInstance
        from app.services.approval_engine.visibility import filter_visible_instances

        instance, *_ = _setup_scenario(db)
        admin = _make_user(db, "superadmin2", "超管2", is_superuser=True)
        db.commit()

        query = db.query(ApprovalInstance)
        filtered = filter_visible_instances(query, db, admin)
        results = filtered.all()

        assert any(r.id == instance.id for r in results)


@pytest.mark.integration
@pytest.mark.permission
class TestRemindPermissionBoundary:
    """TC-VIS-4x: 催办权限边界"""

    def test_initiator_can_remind(self, db):
        """TC-VIS-41: 发起人可以催办。"""
        from app.services.approval_engine.visibility import check_can_remind

        instance, initiator, _, _, _, task = _setup_scenario(db)
        assert check_can_remind(db, task, initiator) is True

    def test_cc_cannot_remind(self, db):
        """TC-VIS-42: 抄送人不可催办。"""
        from app.services.approval_engine.visibility import check_can_remind

        instance, _, _, cc_user, _, task = _setup_scenario(db)

        with patch("app.services.approval_engine.visibility.check_permission", return_value=False):
            assert check_can_remind(db, task, cc_user) is False

    def test_outsider_cannot_remind(self, db):
        """TC-VIS-43: 非参与者不可催办。"""
        from app.services.approval_engine.visibility import check_can_remind

        instance, _, _, _, outsider, task = _setup_scenario(db)

        with patch("app.services.approval_engine.visibility.check_permission", return_value=False):
            assert check_can_remind(db, task, outsider) is False


@pytest.mark.integration
@pytest.mark.permission
class TestCommentPermissionBoundary:
    """TC-VIS-5x: 评论权限边界（approval_scope 模块）"""

    def test_approver_can_comment(self, db):
        """TC-VIS-51: 审批人可以评论。"""
        from app.services.approval_engine.approval_scope import (
            build_approval_scope,
        )

        instance, _, approver, *_ = _setup_scenario(db)

        ctx = build_approval_scope(db, instance.id, approver.id, is_admin=False)
        assert ctx.can_comment is True

    def test_cc_cannot_comment(self, db):
        """TC-VIS-52: 抄送人不可评论。"""
        from app.services.approval_engine.approval_scope import (
            build_approval_scope,
        )

        instance, _, _, cc_user, *_ = _setup_scenario(db)

        ctx = build_approval_scope(db, instance.id, cc_user.id, is_admin=False)
        assert ctx.can_comment is False

    def test_cc_can_view_but_not_detail(self, db):
        """TC-VIS-53: 抄送人可看摘要但不可看完整详情。"""
        from app.services.approval_engine.approval_scope import (
            build_approval_scope,
        )

        instance, _, _, cc_user, *_ = _setup_scenario(db)

        ctx = build_approval_scope(db, instance.id, cc_user.id, is_admin=False)
        assert ctx.can_view is True
        assert ctx.can_view_detail is False

    def test_admin_can_comment_and_remind(self, db):
        """TC-VIS-54: 管理员可评论也可催办。"""
        from app.services.approval_engine.approval_scope import (
            build_approval_scope,
        )

        instance, *_ = _setup_scenario(db)
        admin_user = _make_user(db, "admin_scope", "管理员")
        db.commit()

        ctx = build_approval_scope(db, instance.id, admin_user.id, is_admin=True)
        assert ctx.can_comment is True
        assert ctx.can_remind is True
        assert ctx.can_view_detail is True


@pytest.mark.integration
@pytest.mark.permission
class TestDelegatedApproverVisibility:
    """TC-VIS-6x: 委托/转审审批人可见性"""

    def test_delegated_approver_can_view_detail(self, db):
        """TC-VIS-61: 委托审批人拥有完整详情查看权。"""
        from app.services.approval_engine.approval_scope import (
            build_approval_scope,
            ParticipantRole,
            FULL_DETAIL_ROLES,
        )

        initiator = _make_user(db, "init_d", "发起人")
        delegated = _make_user(db, "delegated01", "代理审批人")

        tmpl = _make_template(db, initiator.id)
        flow = _make_flow(db, tmpl.id, initiator.id)
        node = _make_node(db, flow.id)
        instance = _make_instance(db, tmpl.id, flow.id, node.id, initiator.id)
        _make_task(db, instance.id, node.id, delegated.id, assignee_type="DELEGATED")
        db.commit()

        ctx = build_approval_scope(db, instance.id, delegated.id, is_admin=False)
        assert ParticipantRole.DELEGATED_APPROVER in ctx.roles_in_instance
        assert ctx.can_view_detail is True
        assert ctx.can_comment is True


# ===========================================================================
# Tests — P2: 聚合统计 / 详情字段可见性
# ===========================================================================


@pytest.mark.integration
@pytest.mark.permission
class TestInstanceDetailFieldVisibility:
    """TC-VIS-7x: 实例详情按角色裁剪字段"""

    def test_cc_user_gets_no_form_data(self, db):
        """TC-VIS-71: 抄送人访问详情时 form_data 应为 None。"""
        from app.services.approval_engine.visibility import (
            resolve_participant_role,
            ParticipantRole,
        )

        instance, _, _, cc_user, *_ = _setup_scenario(db)

        role = resolve_participant_role(db, instance.id, cc_user)
        assert role == ParticipantRole.CC

        # CC 用户的 is_summary_only == True → form_data 应被剥离
        is_summary_only = role == ParticipantRole.CC
        assert is_summary_only is True

    def test_initiator_gets_full_detail(self, db):
        """TC-VIS-72: 发起人访问详情时可见 form_data。"""
        from app.services.approval_engine.visibility import (
            resolve_participant_role,
            ParticipantRole,
        )

        instance, initiator, *_ = _setup_scenario(db)

        role = resolve_participant_role(db, instance.id, initiator)
        assert role == ParticipantRole.INITIATOR
        assert role != ParticipantRole.CC

    def test_approver_gets_full_detail(self, db):
        """TC-VIS-73: 审批人访问详情时可见 form_data。"""
        from app.services.approval_engine.visibility import (
            resolve_participant_role,
            ParticipantRole,
        )

        instance, _, approver, *_ = _setup_scenario(db)

        role = resolve_participant_role(db, instance.id, approver)
        assert role == ParticipantRole.APPROVER
        assert role != ParticipantRole.CC

    def test_outsider_gets_none_role(self, db):
        """TC-VIS-74: 非参与者角色为 NONE，详情端点应拒绝。"""
        from app.services.approval_engine.visibility import (
            resolve_participant_role,
            ParticipantRole,
        )

        instance, _, _, _, outsider, _ = _setup_scenario(db)

        role = resolve_participant_role(db, instance.id, outsider)
        assert role == ParticipantRole.NONE


@pytest.mark.integration
@pytest.mark.permission
class TestPendingEndpointSelfScoped:
    """TC-VIS-8x: 待办/已处理查询仅返回自身数据"""

    def test_pending_mine_only_shows_own_tasks(self, db):
        """TC-VIS-81: /pending/mine 仅返回用户自己的待办任务。"""
        from app.models.approval import ApprovalTask

        instance, initiator, approver, cc_user, outsider, task = _setup_scenario(db)

        # 审批人的待办查询
        pending_tasks = (
            db.query(ApprovalTask)
            .filter(
                ApprovalTask.assignee_id == approver.id,
                ApprovalTask.status == "PENDING",
            )
            .all()
        )
        assert len(pending_tasks) == 1
        assert pending_tasks[0].id == task.id

        # 外部人员无待办
        outsider_tasks = (
            db.query(ApprovalTask)
            .filter(
                ApprovalTask.assignee_id == outsider.id,
                ApprovalTask.status == "PENDING",
            )
            .all()
        )
        assert len(outsider_tasks) == 0

    def test_initiated_only_shows_own_instances(self, db):
        """TC-VIS-82: /pending/initiated 仅返回用户发起的审批。"""
        from app.models.approval import ApprovalInstance

        instance, initiator, approver, *_ = _setup_scenario(db)

        # 发起人可见
        own = (
            db.query(ApprovalInstance)
            .filter(ApprovalInstance.initiator_id == initiator.id)
            .all()
        )
        assert len(own) == 1

        # 审批人的发起列表为空
        approver_initiated = (
            db.query(ApprovalInstance)
            .filter(ApprovalInstance.initiator_id == approver.id)
            .all()
        )
        assert len(approver_initiated) == 0

    def test_cc_only_shows_own_records(self, db):
        """TC-VIS-83: /pending/cc 仅返回发给自己的抄送。"""
        from app.models.approval.task import ApprovalCarbonCopy

        instance, _, _, cc_user, outsider, _ = _setup_scenario(db)

        own_cc = (
            db.query(ApprovalCarbonCopy)
            .filter(ApprovalCarbonCopy.cc_user_id == cc_user.id)
            .all()
        )
        assert len(own_cc) == 1

        outsider_cc = (
            db.query(ApprovalCarbonCopy)
            .filter(ApprovalCarbonCopy.cc_user_id == outsider.id)
            .all()
        )
        assert len(outsider_cc) == 0

    def test_counts_only_reflect_own_data(self, db):
        """TC-VIS-84: /pending/counts 的各项计数仅反映自身参与。"""
        from app.models.approval import ApprovalTask
        from app.models.approval.task import ApprovalCarbonCopy

        instance, initiator, approver, cc_user, outsider, task = _setup_scenario(db)

        # 审批人待办 = 1
        assert (
            db.query(ApprovalTask)
            .filter(
                ApprovalTask.assignee_id == approver.id,
                ApprovalTask.status == "PENDING",
            )
            .count()
            == 1
        )

        # 外部人员待办 = 0
        assert (
            db.query(ApprovalTask)
            .filter(
                ApprovalTask.assignee_id == outsider.id,
                ApprovalTask.status == "PENDING",
            )
            .count()
            == 0
        )

        # 外部人员抄送 = 0
        assert (
            db.query(ApprovalCarbonCopy)
            .filter(
                ApprovalCarbonCopy.cc_user_id == outsider.id,
                ApprovalCarbonCopy.is_read == False,  # noqa: E712
            )
            .count()
            == 0
        )

        # 抄送人未读 = 1
        assert (
            db.query(ApprovalCarbonCopy)
            .filter(
                ApprovalCarbonCopy.cc_user_id == cc_user.id,
                ApprovalCarbonCopy.is_read == False,  # noqa: E712
            )
            .count()
            == 1
        )
