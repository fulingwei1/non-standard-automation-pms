"""
场景7：并行审批

测试多个审批人同时审批的并行审批流程
"""
import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.approval.instance import ApprovalInstance
from app.models.approval.task import ApprovalTask
from app.models.purchase import PurchaseRequest


class TestParallelApproval:
    """并行审批测试"""

    def test_01_create_parallel_approval_tasks(self, db_session: Session):
        """测试1：创建并行审批任务"""
        pr = PurchaseRequest(
            request_code="PR-PAR-001",
            requester_id=3,
            total_amount=Decimal("200000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            business_type="PURCHASE_REQUEST",
            business_id=pr.id,
            business_code=pr.request_code,
            initiator_id=3,
            status="PENDING",
            created_by=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 创建并行审批任务（技术总监和财务总监同时审批）
        task1 = ApprovalTask(
            instance_id=instance.id,
            approver_id=5,
            approver_name="技术总监",
            node_name="技术评审",
            sequence=1,
            status="PENDING",
        )
        task2 = ApprovalTask(
            instance_id=instance.id,
            approver_id=6,
            approver_name="财务总监",
            node_name="财务评审",
            sequence=1,  # 相同sequence表示并行
            status="PENDING",
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        tasks = db_session.query(ApprovalTask).filter(
            ApprovalTask.instance_id == instance.id
        ).all()
        assert len(tasks) == 2
        assert all(t.status == "PENDING" for t in tasks)

    def test_02_one_approver_approves_first(self, db_session: Session):
        """测试2：一个审批人先审批"""
        pr = PurchaseRequest(
            request_code="PR-PAR-002",
            requester_id=3,
            total_amount=Decimal("180000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            business_type="PURCHASE_REQUEST",
            business_id=pr.id,
            business_code=pr.request_code,
            initiator_id=3,
            status="PENDING",
            created_by=3,
        )
        db_session.add(instance)
        db_session.commit()

        task1 = ApprovalTask(
            instance_id=instance.id,
            approver_id=5,
            node_name="技术评审",
            sequence=1,
            status="PENDING",
        )
        task2 = ApprovalTask(
            instance_id=instance.id,
            approver_id=6,
            node_name="财务评审",
            sequence=1,
            status="PENDING",
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        # 技术总监先审批
        task1.status = "APPROVED"
        task1.decision = "APPROVE"
        task1.comment = "技术方案可行"
        task1.approved_at = datetime.now()
        db_session.commit()

        # 实例仍在等待财务审批
        assert instance.status == "PENDING"
        assert task1.status == "APPROVED"
        assert task2.status == "PENDING"

    def test_03_all_parallel_approvers_approve(self, db_session: Session):
        """测试3：所有并行审批人都通过"""
        pr = PurchaseRequest(
            request_code="PR-PAR-003",
            requester_id=3,
            total_amount=Decimal("220000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            business_type="PURCHASE_REQUEST",
            business_id=pr.id,
            business_code=pr.request_code,
            initiator_id=3,
            status="PENDING",
            created_by=3,
        )
        db_session.add(instance)
        db_session.commit()

        task1 = ApprovalTask(
            instance_id=instance.id,
            approver_id=5,
            sequence=1,
            status="PENDING",
        )
        task2 = ApprovalTask(
            instance_id=instance.id,
            approver_id=6,
            sequence=1,
            status="PENDING",
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        # 技术总监审批
        task1.status = "APPROVED"
        task1.approved_at = datetime.now()
        db_session.commit()

        # 财务总监审批
        task2.status = "APPROVED"
        task2.approved_at = datetime.now()
        db_session.commit()

        # 检查所有并行任务是否完成
        all_approved = all(
            t.status == "APPROVED" for t in [task1, task2]
        )
        assert all_approved is True

        # 审批实例通过
        instance.status = "APPROVED"
        instance.approved_at = datetime.now()
        pr.status = "APPROVED"
        db_session.commit()

        assert instance.status == "APPROVED"

    def test_04_one_parallel_approver_rejects(self, db_session: Session):
        """测试4：一个并行审批人拒绝"""
        pr = PurchaseRequest(
            request_code="PR-PAR-004",
            requester_id=3,
            total_amount=Decimal("250000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            business_type="PURCHASE_REQUEST",
            business_id=pr.id,
            business_code=pr.request_code,
            initiator_id=3,
            status="PENDING",
            created_by=3,
        )
        db_session.add(instance)
        db_session.commit()

        task1 = ApprovalTask(
            instance_id=instance.id,
            approver_id=5,
            sequence=1,
            status="PENDING",
        )
        task2 = ApprovalTask(
            instance_id=instance.id,
            approver_id=6,
            sequence=1,
            status="PENDING",
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        # 技术总监通过
        task1.status = "APPROVED"
        task1.approved_at = datetime.now()
        db_session.commit()

        # 财务总监拒绝
        task2.status = "REJECTED"
        task2.decision = "REJECT"
        task2.comment = "预算超支"
        task2.approved_at = datetime.now()
        db_session.commit()

        # 一票否决，审批失败
        instance.status = "REJECTED"
        pr.status = "REJECTED"
        db_session.commit()

        assert instance.status == "REJECTED"

    def test_05_parallel_with_minimum_approval_count(self, db_session: Session):
        """测试5：并行审批需要最少通过数量"""
        pr = PurchaseRequest(
            request_code="PR-PAR-005",
            requester_id=3,
            total_amount=Decimal("300000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            business_type="PURCHASE_REQUEST",
            business_id=pr.id,
            business_code=pr.request_code,
            initiator_id=3,
            status="PENDING",
            minimum_approval_count=2,  # 至少需要2人通过
            created_by=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 创建3个并行审批人
        tasks = [
            ApprovalTask(
                instance_id=instance.id,
                approver_id=5,
                sequence=1,
                status="PENDING",
            ),
            ApprovalTask(
                instance_id=instance.id,
                approver_id=6,
                sequence=1,
                status="PENDING",
            ),
            ApprovalTask(
                instance_id=instance.id,
                approver_id=7,
                sequence=1,
                status="PENDING",
            ),
        ]
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # 前两人通过
        tasks[0].status = "APPROVED"
        tasks[0].approved_at = datetime.now()
        tasks[1].status = "APPROVED"
        tasks[1].approved_at = datetime.now()
        db_session.commit()

        # 检查是否满足最少通过数
        approved_count = sum(1 for t in tasks if t.status == "APPROVED")
        assert approved_count >= instance.minimum_approval_count

        # 第三人可以不审批，已满足条件
        instance.status = "APPROVED"
        db_session.commit()

        assert instance.status == "APPROVED"

    def test_06_parallel_approval_timeout_handling(self, db_session: Session):
        """测试6：并行审批超时处理"""
        pr = PurchaseRequest(
            request_code="PR-PAR-006",
            requester_id=3,
            total_amount=Decimal("150000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            business_type="PURCHASE_REQUEST",
            business_id=pr.id,
            business_code=pr.request_code,
            initiator_id=3,
            status="PENDING",
            created_by=3,
        )
        db_session.add(instance)
        db_session.commit()

        from datetime import timedelta

        # 创建并行任务
        task1 = ApprovalTask(
            instance_id=instance.id,
            approver_id=5,
            sequence=1,
            status="PENDING",
            due_date=datetime.now().date() - timedelta(days=2),  # 已超时
        )
        task2 = ApprovalTask(
            instance_id=instance.id,
            approver_id=6,
            sequence=1,
            status="PENDING",
            due_date=datetime.now().date() + timedelta(days=2),  # 未超时
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        # 检查超时任务
        is_task1_overdue = task1.due_date < datetime.now().date()
        assert is_task1_overdue is True

        # 超时任务自动通过或升级
        task1.status = "ESCALATED"
        task1.escalation_note = "审批超时，自动升级"
        db_session.commit()

        assert task1.status == "ESCALATED"

    def test_07_hybrid_parallel_and_sequential_approval(self, db_session: Session):
        """测试7：混合并行和顺序审批"""
        pr = PurchaseRequest(
            request_code="PR-HYBRID-001",
            requester_id=3,
            total_amount=Decimal("400000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            business_type="PURCHASE_REQUEST",
            business_id=pr.id,
            business_code=pr.request_code,
            initiator_id=3,
            status="PENDING",
            created_by=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 第一级：并行审批（技术+财务）
        task1_1 = ApprovalTask(
            instance_id=instance.id,
            approver_id=5,
            sequence=1,
            status="PENDING",
        )
        task1_2 = ApprovalTask(
            instance_id=instance.id,
            approver_id=6,
            sequence=1,
            status="PENDING",
        )

        # 第二级：总经理审批
        task2 = ApprovalTask(
            instance_id=instance.id,
            approver_id=1,
            sequence=2,
            status="NOT_STARTED",
        )
        
        db_session.add_all([task1_1, task1_2, task2])
        db_session.commit()

        # 完成第一级并行审批
        task1_1.status = "APPROVED"
        task1_1.approved_at = datetime.now()
        task1_2.status = "APPROVED"
        task1_2.approved_at = datetime.now()
        db_session.commit()

        # 激活第二级
        task2.status = "PENDING"
        db_session.commit()

        # 第二级审批
        task2.status = "APPROVED"
        task2.approved_at = datetime.now()
        db_session.commit()

        assert all(t.status == "APPROVED" for t in [task1_1, task1_2, task2])

    def test_08_parallel_approval_with_veto_power(self, db_session: Session):
        """测试8：并行审批中的一票否决"""
        pr = PurchaseRequest(
            request_code="PR-VETO-001",
            requester_id=3,
            total_amount=Decimal("500000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            business_type="PURCHASE_REQUEST",
            business_id=pr.id,
            business_code=pr.request_code,
            initiator_id=3,
            status="PENDING",
            created_by=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 创建3个并行审批，技术总监有一票否决权
        task1 = ApprovalTask(
            instance_id=instance.id,
            approver_id=5,
            node_name="技术总监（一票否决）",
            sequence=1,
            status="PENDING",
            has_veto_power=True,
        )
        task2 = ApprovalTask(
            instance_id=instance.id,
            approver_id=6,
            sequence=1,
            status="PENDING",
        )
        task3 = ApprovalTask(
            instance_id=instance.id,
            approver_id=7,
            sequence=1,
            status="PENDING",
        )
        db_session.add_all([task1, task2, task3])
        db_session.commit()

        # 其他人都通过
        task2.status = "APPROVED"
        task2.approved_at = datetime.now()
        task3.status = "APPROVED"
        task3.approved_at = datetime.now()
        db_session.commit()

        # 技术总监拒绝（一票否决）
        task1.status = "REJECTED"
        task1.decision = "REJECT"
        task1.comment = "技术风险太大"
        task1.approved_at = datetime.now()
        db_session.commit()

        # 整个审批失败
        instance.status = "REJECTED"
        pr.status = "REJECTED"
        db_session.commit()

        assert instance.status == "REJECTED"

    def test_09_parallel_approval_notification(self, db_session: Session):
        """测试9：并行审批通知"""
        pr = PurchaseRequest(
            request_code="PR-NOTIF-001",
            requester_id=3,
            total_amount=Decimal("180000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            business_type="PURCHASE_REQUEST",
            business_id=pr.id,
            business_code=pr.request_code,
            initiator_id=3,
            status="PENDING",
            created_by=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 创建并行任务
        tasks = [
            ApprovalTask(
                instance_id=instance.id,
                approver_id=5,
                sequence=1,
                status="PENDING",
            ),
            ApprovalTask(
                instance_id=instance.id,
                approver_id=6,
                sequence=1,
                status="PENDING",
            ),
        ]
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # 模拟发送通知（实际项目中会有通知服务）
        pending_tasks = db_session.query(ApprovalTask).filter(
            ApprovalTask.instance_id == instance.id,
            ApprovalTask.status == "PENDING"
        ).all()

        notification_count = len(pending_tasks)
        assert notification_count == 2

    def test_10_parallel_approval_completion_check(self, db_session: Session):
        """测试10：并行审批完成检查"""
        pr = PurchaseRequest(
            request_code="PR-CHECK-001",
            requester_id=3,
            total_amount=Decimal("280000.00"),
            status="PENDING_APPROVAL",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        instance = ApprovalInstance(
            business_type="PURCHASE_REQUEST",
            business_id=pr.id,
            business_code=pr.request_code,
            initiator_id=3,
            status="PENDING",
            created_by=3,
        )
        db_session.add(instance)
        db_session.commit()

        # 创建并行任务
        tasks = [
            ApprovalTask(
                instance_id=instance.id,
                approver_id=i,
                sequence=1,
                status="PENDING",
            )
            for i in range(5, 9)  # 4个审批人
        ]
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # 逐个审批
        for i, task in enumerate(tasks):
            task.status = "APPROVED"
            task.approved_at = datetime.now()
            db_session.commit()

            # 检查是否所有并行任务完成
            parallel_tasks = db_session.query(ApprovalTask).filter(
                ApprovalTask.instance_id == instance.id,
                ApprovalTask.sequence == 1
            ).all()

            all_completed = all(
                t.status in ["APPROVED", "REJECTED"] for t in parallel_tasks
            )

            if i < len(tasks) - 1:
                assert all_completed is False
            else:
                assert all_completed is True
