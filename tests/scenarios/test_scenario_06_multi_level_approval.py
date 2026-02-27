"""
场景6：多级审批流程

测试需要经过多个审批节点的复杂审批流程
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.approval.instance import ApprovalInstance
from app.models.approval.task import ApprovalTask
from app.models.approval.template import ApprovalTemplate
from app.models.purchase import PurchaseRequest


class TestMultiLevelApproval:
    """多级审批流程测试"""

    @pytest.fixture
    def approval_template(self, db_session: Session):
        """创建多级审批模板"""
        template = ApprovalTemplate(
            template_code="TPL-PURCHASE-MULTI",
            template_name="采购多级审批",
            business_type="PURCHASE_REQUEST",
            description="大额采购申请多级审批流程",
            is_active=True,
            created_by=1,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)
        return template

    def test_01_create_multi_level_approval_instance(self, db_session: Session):
        """测试1：创建多级审批实例"""
        # 创建采购申请
        pr = PurchaseRequest(
            request_no="PR-MULTI-001",
            requested_by=3,
            total_amount=Decimal("100000.00"),  # 大额采购
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        # 创建审批实例
        instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="PENDING",
            initiator_id=3,
        )
        db_session.add(instance)
        db_session.commit()

        assert instance.id is not None
        assert instance.status == "PENDING"

    def test_02_create_approval_tasks_chain(self, db_session: Session):
        """测试2：创建审批任务链"""
        pr = PurchaseRequest(
            request_no="PR-MULTI-002",
            requested_by=3,
            total_amount=Decimal("150000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="PENDING",
            initiator_id=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 创建多级审批任务
        # 第一级：部门经理
        task1 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            assignee_name="部门经理",
            assignee_name="部门经理审批",
            task_order=1,
            status="PENDING",
        )
        db_session.add(task1)

        # 第二级：财务总监
        task2 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=5,
            assignee_name="财务总监",
            assignee_name="财务总监审批",
            task_order=2,
            status="NOT_STARTED",
        )
        db_session.add(task2)

        # 第三级：总经理
        task3 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=1,
            assignee_name="总经理",
            assignee_name="总经理审批",
            task_order=3,
            status="NOT_STARTED",
        )
        db_session.add(task3)
        db_session.commit()

        tasks = db_session.query(ApprovalTask).filter(
            ApprovalTask.instance_id == instance.id
        ).order_by(ApprovalTask.sequence).all()

        assert len(tasks) == 3
        assert tasks[0].status == "PENDING"
        assert tasks[1].status == "NOT_STARTED"

    def test_03_first_level_approval(self, db_session: Session):
        """测试3：第一级审批通过"""
        pr = PurchaseRequest(
            request_no="PR-MULTI-003",
            requested_by=3,
            total_amount=Decimal("120000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="PENDING",
            initiator_id=3,
        )
        db_session.add(instance)
        db_session.commit()

        task1 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            assignee_name="部门经理审批",
            task_order=1,
            status="PENDING",
        )
        db_session.add(task1)

        task2 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=5,
            assignee_name="财务总监审批",
            task_order=2,
            status="NOT_STARTED",
        )
        db_session.add(task2)
        db_session.commit()

        # 第一级审批通过
        task1.status = "APPROVED"
        task1.decision = "APPROVE"
        task1.comment = "同意采购"
        task1.approved_at = datetime.now()
        db_session.commit()

        # 激活下一级审批
        task2.status = "PENDING"
        db_session.commit()

        assert task1.status == "APPROVED"
        assert task2.status == "PENDING"

    def test_04_sequential_approval_completion(self, db_session: Session):
        """测试4：顺序审批完成"""
        pr = PurchaseRequest(
            request_no="PR-MULTI-004",
            requested_by=3,
            total_amount=Decimal("180000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="PENDING",
            initiator_id=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 创建三级审批任务
        tasks_data = [
            {"approver_id": 4, "node_name": "部门经理", "sequence": 1},
            {"approver_id": 5, "node_name": "财务总监", "sequence": 2},
            {"approver_id": 1, "node_name": "总经理", "sequence": 3},
        ]

        tasks = []
        for data in tasks_data:
            task = ApprovalTask(
                instance_id=instance.id,
                assignee_id=data["approver_id"],
                assignee_name=data["node_name"],
                task_order=data["sequence"],
                status="PENDING" if data["sequence"] == 1 else "NOT_STARTED",
            )
            db_session.add(task)
            tasks.append(task)
        db_session.commit()

        # 第一级审批
        tasks[0].status = "APPROVED"
        tasks[0].approved_at = datetime.now()
        tasks[1].status = "PENDING"
        db_session.commit()

        # 第二级审批
        tasks[1].status = "APPROVED"
        tasks[1].approved_at = datetime.now()
        tasks[2].status = "PENDING"
        db_session.commit()

        # 第三级审批
        tasks[2].status = "APPROVED"
        tasks[2].approved_at = datetime.now()
        db_session.commit()

        # 审批完成
        instance.status = "APPROVED"
        instance.approved_at = datetime.now()
        pr.status = "APPROVED"
        db_session.commit()

        assert all(t.status == "APPROVED" for t in tasks)
        assert instance.status == "APPROVED"
        assert pr.status == "APPROVED"

    def test_05_approval_rejection_at_middle_level(self, db_session: Session):
        """测试5：中间级别审批驳回"""
        pr = PurchaseRequest(
            request_no="PR-MULTI-005",
            requested_by=3,
            total_amount=Decimal("200000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="PENDING",
            initiator_id=3,
        )
        db_session.add(instance)
        db_session.commit()

        tasks = [
            ApprovalTask(
                instance_id=instance.id,
                assignee_id=4,
                task_order=1,
                status="APPROVED",
                approved_at=datetime.now(),
            ),
            ApprovalTask(
                instance_id=instance.id,
                assignee_id=5,
                task_order=2,
                status="PENDING",
            ),
            ApprovalTask(
                instance_id=instance.id,
                assignee_id=1,
                task_order=3,
                status="NOT_STARTED",
            ),
        ]
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # 第二级审批驳回
        tasks[1].status = "REJECTED"
        tasks[1].decision = "REJECT"
        tasks[1].comment = "预算超支，需重新评估"
        tasks[1].approved_at = datetime.now()
        db_session.commit()

        # 终止后续审批
        tasks[2].status = "CANCELLED"
        db_session.commit()

        # 审批实例驳回
        instance.status = "REJECTED"
        pr.status = "REJECTED"
        db_session.commit()

        assert tasks[1].status == "REJECTED"
        assert tasks[2].status == "CANCELLED"
        assert instance.status == "REJECTED"

    def test_06_approval_with_countersignature(self, db_session: Session):
        """测试6：会签审批（同级多人）"""
        pr = PurchaseRequest(
            request_no="PR-MULTI-006",
            requested_by=3,
            total_amount=Decimal("250000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="PENDING",
            initiator_id=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 第一级：部门经理（单人）
        task1 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            assignee_name="部门经理",
            task_order=1,
            status="APPROVED",
            approved_at=datetime.now(),
        )
        db_session.add(task1)

        # 第二级：技术总监和财务总监会签
        task2a = ApprovalTask(
            instance_id=instance.id,
            assignee_id=5,
            assignee_name="财务总监会签",
            task_order=2,
            status="PENDING",
        )
        task2b = ApprovalTask(
            instance_id=instance.id,
            assignee_id=6,
            assignee_name="技术总监会签",
            task_order=2,
            status="PENDING",
        )
        db_session.add(task2a)
        db_session.add(task2b)
        db_session.commit()

        # 财务总监同意
        task2a.status = "APPROVED"
        task2a.approved_at = datetime.now()
        db_session.commit()

        # 技术总监同意
        task2b.status = "APPROVED"
        task2b.approved_at = datetime.now()
        db_session.commit()

        # 检查会签是否全部通过
        countersign_tasks = db_session.query(ApprovalTask).filter(
            ApprovalTask.instance_id == instance.id,
            ApprovalTask.sequence == 2
        ).all()

        all_approved = all(t.status == "APPROVED" for t in countersign_tasks)
        assert all_approved is True

    def test_07_approval_delegation(self, db_session: Session):
        """测试7：审批委托"""
        pr = PurchaseRequest(
            request_no="PR-MULTI-007",
            requested_by=3,
            total_amount=Decimal("90000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="PENDING",
            initiator_id=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 原审批人
        task = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            assignee_name="部门经理",
            status="PENDING",
        )
        db_session.add(task)
        db_session.commit()

        # 委托给其他人
        task.delegated_to = 7
        task.delegation_note = "出差期间委托代理审批"
        db_session.commit()

        # 代理人审批
        task.status = "APPROVED"
        task.approved_at = datetime.now()
        task.comment = "代理审批通过"
        db_session.commit()

        assert task.delegated_to == 7
        assert task.status == "APPROVED"

    def test_08_approval_with_conditional_routing(self, db_session: Session):
        """测试8：条件路由审批"""
        # 金额小于10万，只需部门经理审批
        pr_small = PurchaseRequest(
            request_no="PR-COND-001",
            requested_by=3,
            total_amount=Decimal("80000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr_small)
        db_session.commit()

        instance_small = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr_small.id,
            instance_no=pr_small.request_code,
            initiator_id=3,
            status="PENDING",
            initiator_id=3,
        )
        db_session.add(instance_small)
        db_session.commit()

        # 只创建一级审批
        task_small = ApprovalTask(
            instance_id=instance_small.id,
            assignee_id=4,
            assignee_name="部门经理",
            task_order=1,
            status="APPROVED",
            approved_at=datetime.now(),
        )
        db_session.add(task_small)
        db_session.commit()

        instance_small.status = "APPROVED"
        pr_small.status = "APPROVED"
        db_session.commit()

        # 金额大于等于10万，需要多级审批
        pr_large = PurchaseRequest(
            request_no="PR-COND-002",
            requested_by=3,
            total_amount=Decimal("150000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr_large)
        db_session.commit()

        instance_large = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr_large.id,
            instance_no=pr_large.request_code,
            initiator_id=3,
            status="PENDING",
            initiator_id=3,
        )
        db_session.add(instance_large)
        db_session.commit()

        # 创建多级审批
        for i, approver_id in enumerate([4, 5, 1], 1):
            task = ApprovalTask(
                instance_id=instance_large.id,
                assignee_id=approver_id,
                task_order=i,
                status="PENDING" if i == 1 else "NOT_STARTED",
            )
            db_session.add(task)
        db_session.commit()

        tasks_large = db_session.query(ApprovalTask).filter(
            ApprovalTask.instance_id == instance_large.id
        ).all()

        assert len(tasks_large) == 3

    def test_09_approval_time_tracking(self, db_session: Session):
        """测试9：审批时间跟踪"""
        pr = PurchaseRequest(
            request_no="PR-TIME-001",
            requested_by=3,
            total_amount=Decimal("100000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="PENDING",
            created_at=datetime.now() - timedelta(days=5),
            initiator_id=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 第一级审批
        task1_start = datetime.now() - timedelta(days=5)
        task1_end = datetime.now() - timedelta(days=4)
        task1 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            task_order=1,
            status="APPROVED",
            created_at=task1_start,
            approved_at=task1_end,
        )
        db_session.add(task1)

        # 第二级审批
        task2_start = datetime.now() - timedelta(days=4)
        task2_end = datetime.now() - timedelta(days=2)
        task2 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=5,
            task_order=2,
            status="APPROVED",
            created_at=task2_start,
            approved_at=task2_end,
        )
        db_session.add(task2)

        # 第三级审批
        task3_start = datetime.now() - timedelta(days=2)
        task3_end = datetime.now()
        task3 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=1,
            task_order=3,
            status="APPROVED",
            created_at=task3_start,
            approved_at=task3_end,
        )
        db_session.add(task3)
        db_session.commit()

        instance.status = "APPROVED"
        instance.approved_at = task3_end
        db_session.commit()

        # 计算审批时长
        task1_duration = (task1_end - task1_start).days
        task2_duration = (task2_end - task2_start).days
        task3_duration = (task3_end - task3_start).days
        total_duration = (instance.approved_at - instance.created_at).days

        assert task1_duration == 1
        assert task2_duration == 2
        assert task3_duration == 2
        assert total_duration == 5

    def test_10_approval_with_auto_escalation(self, db_session: Session):
        """测试10：审批超时自动升级"""
        pr = PurchaseRequest(
            request_no="PR-ESC-001",
            requested_by=3,
            total_amount=Decimal("120000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="PENDING",
            initiator_id=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 审批任务超时
        task = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            assignee_name="部门经理",
            status="PENDING",
            created_at=datetime.now() - timedelta(days=3),  # 超时3天
            due_date=datetime.now() - timedelta(days=1),
        )
        db_session.add(task)
        db_session.commit()

        # 检查超时
        is_overdue = task.due_date < datetime.now().date()
        assert is_overdue is True

        # 自动升级给上级
        task.status = "ESCALATED"
        task.escalated_to = 1  # 升级给总经理
        task.escalation_note = "审批超时，自动升级"
        db_session.commit()

        # 上级审批
        task.status = "APPROVED"
        task.approved_at = datetime.now()
        db_session.commit()

        assert task.escalated_to == 1
        assert task.status == "APPROVED"
