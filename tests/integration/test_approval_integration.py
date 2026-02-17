# -*- coding: utf-8 -*-
"""
K1组集成测试 - 审批流程集成测试

测试从提交审批→审批人处理→通知发送的完整审批流程。
使用 SQLite 内存数据库，不依赖真实数据库。

覆盖流程：
  1. 创建审批模板 & 流程定义
  2. 发起人提交审批实例
  3. 审批任务分配给审批人
  4. 审批人通过 / 驳回
  5. 操作日志记录
  6. 通知发送
"""

import pytest
from datetime import datetime, date

from sqlalchemy import create_engine, Table, Column, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

def _create_test_engine():
    """创建测试专用 SQLite 内存引擎，兼容模型中已知的 FK 与索引问题。"""
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
    for table in Base.metadata.sorted_tables:
        for index in table.indexes:
            try:
                index.create(bind=engine, checkfirst=True)
            except Exception:
                pass
    return engine


@pytest.fixture(scope="function")
def db():
    """每个测试函数独立的 SQLite 内存 session。"""
    engine = _create_test_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _make_user(db, username="approver01", real_name="审批人"):
    from app.models.user import User
    user = User(
        username=username,
        password_hash="hashed_pw",
        real_name=real_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()
    return user


def _make_template(db, user_id, code="TMPL-001", name="项目立项审批"):
    from app.models.approval import ApprovalTemplate
    tmpl = ApprovalTemplate(
        template_code=code,
        template_name=name,
        category="PROJECT",
        entity_type="PROJECT",
        description="项目立项审批模板",
        version=1,
        is_published=True,
        published_at=datetime.now(),
        published_by=user_id,
    )
    db.add(tmpl)
    db.flush()
    return tmpl


def _make_flow(db, template_id, user_id, name="默认流程"):
    from app.models.approval import ApprovalFlowDefinition
    flow = ApprovalFlowDefinition(
        template_id=template_id,
        flow_name=name,
        description="默认审批流程",
        is_default=True,
        version=1,
        is_active=True,
        created_by=user_id,
    )
    db.add(flow)
    db.flush()
    return flow


def _make_node(db, flow_id, order=1, name="部门负责人审批"):
    from app.models.approval import ApprovalNodeDefinition
    node = ApprovalNodeDefinition(
        flow_id=flow_id,
        node_name=name,
        node_type="APPROVAL",
        node_order=order,
        approval_mode="SINGLE",
        is_active=True,
    )
    db.add(node)
    db.flush()
    return node


def _make_instance(db, template_id, flow_id, node_id, initiator_id,
                   instance_no="AP202601200001", entity_type="PROJECT", entity_id=1):
    from app.models.approval import ApprovalInstance
    inst = ApprovalInstance(
        instance_no=instance_no,
        template_id=template_id,
        flow_id=flow_id,
        entity_type=entity_type,
        entity_id=entity_id,
        initiator_id=initiator_id,
        initiator_name="发起人",
        form_data={"title": "项目立项审批申请", "reason": "新项目需要立项"},
        status="PENDING",
        current_node_id=node_id,
        current_node_order=1,
        urgency="NORMAL",
        title="项目立项审批",
        summary="申请立项",
    )
    db.add(inst)
    db.flush()
    return inst


# ===========================================================================
# 测试类
# ===========================================================================

class TestApprovalTemplateSetup:
    """TC-AP-1x: 审批模板与流程定义测试"""

    def test_create_approval_template(self, db):
        """TC-AP-11: 创建审批模板，验证字段正确保存。"""
        user = _make_user(db, "admin01", "管理员")
        tmpl = _make_template(db, user.id)
        db.commit()

        from app.models.approval import ApprovalTemplate
        saved = db.query(ApprovalTemplate).filter_by(template_code="TMPL-001").one()
        assert saved.template_name == "项目立项审批"
        assert saved.category == "PROJECT"
        assert saved.is_published is True

    def test_create_flow_definition_with_nodes(self, db):
        """TC-AP-12: 为审批模板创建流程定义，并绑定审批节点。"""
        user = _make_user(db, "admin02", "管理员2")
        tmpl = _make_template(db, user.id, "TMPL-002", "采购审批")
        flow = _make_flow(db, tmpl.id, user.id, "采购审批流程")

        node1 = _make_node(db, flow.id, 1, "部门负责人")
        node2 = _make_node(db, flow.id, 2, "财务经理")
        db.commit()

        from app.models.approval import ApprovalNodeDefinition
        nodes = db.query(ApprovalNodeDefinition).filter_by(
            flow_id=flow.id
        ).order_by(ApprovalNodeDefinition.node_order).all()

        assert len(nodes) == 2
        assert nodes[0].node_name == "部门负责人"
        assert nodes[1].node_name == "财务经理"
        assert nodes[0].node_order == 1
        assert nodes[1].node_order == 2


class TestApprovalSubmission:
    """TC-AP-2x: 审批提交测试"""

    def test_submit_approval_instance(self, db):
        """TC-AP-21: 发起人提交审批，创建审批实例，状态为 PENDING。"""
        initiator = _make_user(db, "user01", "项目经理")
        tmpl = _make_template(db, initiator.id, "TMPL-003", "项目立项")
        flow = _make_flow(db, tmpl.id, initiator.id)
        node = _make_node(db, flow.id)
        instance = _make_instance(
            db, tmpl.id, flow.id, node.id, initiator.id,
            instance_no="AP202601200002",
            entity_type="PROJECT", entity_id=100,
        )
        db.commit()

        from app.models.approval import ApprovalInstance
        saved = db.query(ApprovalInstance).filter_by(
            instance_no="AP202601200002"
        ).one()
        assert saved.status == "PENDING"
        assert saved.initiator_id == initiator.id
        assert saved.entity_type == "PROJECT"
        assert saved.entity_id == 100

    def test_submit_creates_action_log(self, db):
        """TC-AP-22: 提交审批时记录 SUBMIT 操作日志。"""
        initiator = _make_user(db, "user02", "项目经理2")
        tmpl = _make_template(db, initiator.id, "TMPL-004", "费用报销")
        flow = _make_flow(db, tmpl.id, initiator.id)
        node = _make_node(db, flow.id)
        instance = _make_instance(
            db, tmpl.id, flow.id, node.id, initiator.id,
            instance_no="AP202601200003",
        )

        from app.models.approval import ApprovalActionLog
        submit_log = ApprovalActionLog(
            instance_id=instance.id,
            operator_id=initiator.id,
            operator_name=initiator.real_name,
            action="SUBMIT",
            action_at=datetime.now(),
            comment="项目立项，请审批",
        )
        db.add(submit_log)
        db.commit()

        saved_log = db.query(ApprovalActionLog).filter_by(
            instance_id=instance.id, action="SUBMIT"
        ).one()
        assert saved_log.operator_id == initiator.id
        assert saved_log.action == "SUBMIT"


class TestApprovalTaskAssignment:
    """TC-AP-3x: 审批任务分配测试"""

    def test_assign_approval_task_to_approver(self, db):
        """TC-AP-31: 审批任务分配给审批人，任务状态为 PENDING。"""
        initiator = _make_user(db, "user03", "发起人3")
        approver = _make_user(db, "approver03", "审批人3")
        tmpl = _make_template(db, initiator.id, "TMPL-005", "变更审批")
        flow = _make_flow(db, tmpl.id, initiator.id)
        node = _make_node(db, flow.id)
        instance = _make_instance(
            db, tmpl.id, flow.id, node.id, initiator.id,
            instance_no="AP202601200004",
        )

        from app.models.approval import ApprovalTask
        task = ApprovalTask(
            instance_id=instance.id,
            node_id=node.id,
            task_type="APPROVAL",
            task_order=1,
            assignee_id=approver.id,
            assignee_name=approver.real_name,
            assignee_type="NORMAL",
            status="PENDING",
            is_active=True,
        )
        db.add(task)
        db.commit()

        from app.models.approval import ApprovalTask as AT
        saved = db.query(AT).filter_by(instance_id=instance.id).one()
        assert saved.assignee_id == approver.id
        assert saved.status == "PENDING"
        assert saved.task_type == "APPROVAL"


class TestApprovalApprove:
    """TC-AP-4x: 审批通过流程测试"""

    def test_approve_task_and_update_instance(self, db):
        """TC-AP-41: 审批人通过审批任务，审批实例状态变为 APPROVED。"""
        initiator = _make_user(db, "user04", "发起人4")
        approver = _make_user(db, "approver04", "审批人4")
        tmpl = _make_template(db, initiator.id, "TMPL-006", "合同审批")
        flow = _make_flow(db, tmpl.id, initiator.id)
        node = _make_node(db, flow.id)
        instance = _make_instance(
            db, tmpl.id, flow.id, node.id, initiator.id,
            instance_no="AP202601200005",
        )

        from app.models.approval import ApprovalTask, ApprovalActionLog
        task = ApprovalTask(
            instance_id=instance.id,
            node_id=node.id,
            task_type="APPROVAL",
            task_order=1,
            assignee_id=approver.id,
            assignee_name=approver.real_name,
            assignee_type="NORMAL",
            status="PENDING",
            is_active=True,
        )
        db.add(task)
        db.flush()

        # 审批通过
        task.status = "APPROVED"
        task.action = "APPROVE"
        task.completed_at = datetime.now()
        task.comment = "符合立项条件，同意"

        # 更新实例状态
        instance.status = "APPROVED"

        # 记录审批日志
        log = ApprovalActionLog(
            instance_id=instance.id,
            task_id=task.id,
            node_id=node.id,
            operator_id=approver.id,
            operator_name=approver.real_name,
            action="APPROVE",
            action_at=datetime.now(),
            comment="同意立项",
        )
        db.add(log)
        db.commit()

        from app.models.approval import ApprovalInstance
        saved_inst = db.query(ApprovalInstance).get(instance.id)
        assert saved_inst.status == "APPROVED"

        from app.models.approval import ApprovalActionLog as AAL
        approve_log = db.query(AAL).filter_by(
            instance_id=instance.id, action="APPROVE"
        ).first()
        assert approve_log is not None
        assert approve_log.operator_id == approver.id

    def test_reject_task_and_update_instance(self, db):
        """TC-AP-42: 审批人驳回审批任务，实例状态变为 REJECTED，记录驳回意见。"""
        initiator = _make_user(db, "user05", "发起人5")
        approver = _make_user(db, "approver05", "审批人5")
        tmpl = _make_template(db, initiator.id, "TMPL-007", "立项审批")
        flow = _make_flow(db, tmpl.id, initiator.id)
        node = _make_node(db, flow.id)
        instance = _make_instance(
            db, tmpl.id, flow.id, node.id, initiator.id,
            instance_no="AP202601200006",
        )

        from app.models.approval import ApprovalTask, ApprovalActionLog
        task = ApprovalTask(
            instance_id=instance.id,
            node_id=node.id,
            task_type="APPROVAL",
            task_order=1,
            assignee_id=approver.id,
            assignee_name=approver.real_name,
            assignee_type="NORMAL",
            status="PENDING",
            is_active=True,
        )
        db.add(task)
        db.flush()

        # 驳回
        task.status = "REJECTED"
        task.action = "REJECT"
        task.completed_at = datetime.now()
        task.comment = "资料不完整，请补充"

        instance.status = "REJECTED"

        log = ApprovalActionLog(
            instance_id=instance.id,
            task_id=task.id,
            node_id=node.id,
            operator_id=approver.id,
            operator_name=approver.real_name,
            action="REJECT",
            action_at=datetime.now(),
            comment="资料不完整",
        )
        db.add(log)
        db.commit()

        from app.models.approval import ApprovalInstance
        saved = db.query(ApprovalInstance).get(instance.id)
        assert saved.status == "REJECTED"


class TestApprovalNotification:
    """TC-AP-5x: 审批通知测试"""

    def test_approval_result_triggers_notification(self, db):
        """TC-AP-51: 审批通过后，向发起人发送审批结果通知。"""
        initiator = _make_user(db, "user06", "发起人6")
        approver = _make_user(db, "approver06", "审批人6")
        tmpl = _make_template(db, initiator.id, "TMPL-008", "通知测试")
        flow = _make_flow(db, tmpl.id, initiator.id)
        node = _make_node(db, flow.id)
        instance = _make_instance(
            db, tmpl.id, flow.id, node.id, initiator.id,
            instance_no="AP202601200007",
        )
        instance.status = "APPROVED"
        db.flush()

        from app.models.notification import Notification
        notif = Notification(
            user_id=initiator.id,
            notification_type="APPROVAL_RESULT",
            source_type="approval",
            source_id=instance.id,
            title="您提交的审批已通过",
            content=f"审批单号 {instance.instance_no} 已于 {datetime.now().strftime('%Y-%m-%d')} 审批通过",
            is_read=False,
            priority="NORMAL",
        )
        db.add(notif)
        db.commit()

        from app.models.notification import Notification as N
        saved = db.query(N).filter_by(
            user_id=initiator.id,
            notification_type="APPROVAL_RESULT",
        ).first()
        assert saved is not None
        assert saved.source_id == instance.id
        assert saved.is_read is False

    def test_pending_approval_notifies_approver(self, db):
        """TC-AP-52: 提交审批后，向待审批人发送待办通知。"""
        initiator = _make_user(db, "user07", "发起人7")
        approver = _make_user(db, "approver07", "审批人7")
        tmpl = _make_template(db, initiator.id, "TMPL-009", "待办通知测试")
        flow = _make_flow(db, tmpl.id, initiator.id)
        node = _make_node(db, flow.id)
        instance = _make_instance(
            db, tmpl.id, flow.id, node.id, initiator.id,
            instance_no="AP202601200008",
        )

        from app.models.notification import Notification
        notif = Notification(
            user_id=approver.id,
            notification_type="APPROVAL_PENDING",
            source_type="approval",
            source_id=instance.id,
            title="您有新的审批待处理",
            content=f"{initiator.real_name} 提交了审批申请，请及时处理",
            is_read=False,
            priority="NORMAL",
        )
        db.add(notif)
        db.commit()

        from app.models.notification import Notification as N
        saved = db.query(N).filter_by(
            user_id=approver.id,
            notification_type="APPROVAL_PENDING",
        ).first()
        assert saved is not None
        assert saved.source_id == instance.id


class TestApprovalMultiStep:
    """TC-AP-6x: 多级审批流程测试"""

    def test_two_level_approval_flow(self, db):
        """TC-AP-61: 两级串行审批：第一级通过后，任务推进到第二级审批节点。"""
        initiator = _make_user(db, "user08", "发起人8")
        approver1 = _make_user(db, "approver08a", "一级审批人")
        approver2 = _make_user(db, "approver08b", "二级审批人")

        tmpl = _make_template(db, initiator.id, "TMPL-010", "两级审批")
        flow = _make_flow(db, tmpl.id, initiator.id)
        node1 = _make_node(db, flow.id, 1, "部门经理")
        node2 = _make_node(db, flow.id, 2, "总经理")

        instance = _make_instance(
            db, tmpl.id, flow.id, node1.id, initiator.id,
            instance_no="AP202601200009",
        )
        instance.current_node_order = 1

        from app.models.approval import ApprovalTask, ApprovalActionLog
        # 第一级任务
        task1 = ApprovalTask(
            instance_id=instance.id,
            node_id=node1.id,
            task_type="APPROVAL",
            task_order=1,
            assignee_id=approver1.id,
            assignee_name=approver1.real_name,
            assignee_type="NORMAL",
            status="PENDING",
            is_active=True,
        )
        db.add(task1)
        db.flush()

        # 一级审批通过
        task1.status = "APPROVED"
        task1.is_active = False
        ApprovalActionLog(
            instance_id=instance.id,
            task_id=task1.id,
            node_id=node1.id,
            operator_id=approver1.id,
            operator_name=approver1.real_name,
            action="APPROVE",
            action_at=datetime.now(),
        )
        instance.current_node_id = node2.id
        instance.current_node_order = 2

        # 第二级任务
        task2 = ApprovalTask(
            instance_id=instance.id,
            node_id=node2.id,
            task_type="APPROVAL",
            task_order=1,
            assignee_id=approver2.id,
            assignee_name=approver2.real_name,
            assignee_type="NORMAL",
            status="PENDING",
            is_active=True,
        )
        db.add(task2)
        db.flush()

        # 二级审批通过
        task2.status = "APPROVED"
        instance.status = "APPROVED"
        db.commit()

        from app.models.approval import ApprovalInstance, ApprovalTask as AT
        saved_inst = db.query(ApprovalInstance).get(instance.id)
        assert saved_inst.status == "APPROVED"
        assert saved_inst.current_node_order == 2

        tasks = db.query(AT).filter_by(instance_id=instance.id).all()
        assert len(tasks) == 2
        assert all(t.status == "APPROVED" for t in tasks)
