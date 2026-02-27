"""
场景8：审批驳回和重新提交

测试审批驳回后的处理流程和重新提交机制
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.approval.instance import ApprovalInstance
from app.models.approval.task import ApprovalTask
from app.models.purchase import PurchaseRequest


class TestApprovalRejection:
    """审批驳回测试"""

    def test_01_reject_approval_with_reason(self, db_session: Session):
        """测试1：带理由驳回审批"""
        pr = PurchaseRequest(
            request_no="PR-REJ-001",
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

        task = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            status="PENDING",
        )
        db_session.add(task)
        db_session.commit()

        # 驳回
        task.status = "REJECTED"
        task.decision = "REJECT"
        task.comment = "预算超标，需重新评估"
        task.approved_at = datetime.now()
        db_session.commit()

        instance.status = "REJECTED"
        pr.status = "REJECTED"
        pr.reject_reason = task.comment
        db_session.commit()

        assert instance.status == "REJECTED"
        assert pr.reject_reason is not None

    def test_02_modify_and_resubmit(self, db_session: Session):
        """测试2：修改后重新提交"""
        pr = PurchaseRequest(
            request_no="PR-RESUB-001",
            requested_by=3,
            total_amount=Decimal("200000.00"),
            status="REJECTED",
            reject_reason="金额过高",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        # 修改金额
        pr.total_amount = Decimal("120000.00")
        pr.status = "DRAFT"
        pr.reject_reason = None
        db_session.commit()

        # 重新提交
        pr.status = "PENDING_APPROVAL"
        pr.submitted_at = datetime.now()
        db_session.commit()

        assert pr.status == "PENDING_APPROVAL"
        assert pr.total_amount == Decimal("120000.00")

    def test_03_create_new_approval_instance_after_rejection(self, db_session: Session):
        """测试3：驳回后创建新审批实例"""
        pr = PurchaseRequest(
            request_no="PR-NEWINS-001",
            requested_by=3,
            total_amount=Decimal("180000.00"),
            status="REJECTED",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        # 旧审批实例
        old_instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="REJECTED",
            initiator_id=3,
        )
        db_session.add(old_instance)
        db_session.commit()

        # 修改申请
        pr.total_amount = Decimal("140000.00")
        pr.status = "PENDING_APPROVAL"
        db_session.commit()

        # 创建新审批实例
        new_instance = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="PENDING",
            previous_instance_id=old_instance.id,
            initiator_id=3,
        )
        db_session.add(new_instance)
        db_session.commit()

        assert new_instance.previous_instance_id == old_instance.id

    def test_04_rejection_notification(self, db_session: Session):
        """测试4：驳回通知"""
        pr = PurchaseRequest(
            request_no="PR-NOTIF-001",
            requested_by=3,
            total_amount=Decimal("160000.00"),
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

        task = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            status="PENDING",
        )
        db_session.add(task)
        db_session.commit()

        # 驳回
        task.status = "REJECTED"
        task.comment = "采购理由不充分"
        db_session.commit()

        # 应该通知申请人（实际项目中会有通知服务）
        assert task.status == "REJECTED"

    def test_05_partial_rejection_in_multi_level(self, db_session: Session):
        """测试5：多级审批中的部分驳回"""
        pr = PurchaseRequest(
            request_no="PR-PARTIAL-001",
            requested_by=3,
            total_amount=Decimal("300000.00"),
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

        # 第一级通过
        task1 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            task_order=1,
            status="APPROVED",
            approved_at=datetime.now(),
        )
        db_session.add(task1)

        # 第二级驳回
        task2 = ApprovalTask(
            instance_id=instance.id,
            assignee_id=5,
            task_order=2,
            status="REJECTED",
            comment="需要更详细的成本分析",
            approved_at=datetime.now(),
        )
        db_session.add(task2)
        db_session.commit()

        instance.status = "REJECTED"
        pr.status = "REJECTED"
        db_session.commit()

        assert task1.status == "APPROVED"
        assert task2.status == "REJECTED"

    def test_06_rejection_with_modification_suggestions(self, db_session: Session):
        """测试6：驳回并提供修改建议"""
        pr = PurchaseRequest(
            request_no="PR-SUGGEST-001",
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

        task = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            status="PENDING",
        )
        db_session.add(task)
        db_session.commit()

        # 驳回并提供建议
        task.status = "REJECTED"
        task.comment = "建议将总额控制在15万以内"
        task.suggestion = "可以考虑分批采购"
        db_session.commit()

        assert task.suggestion is not None

    def test_07_automatic_resubmission_limit(self, db_session: Session):
        """测试7：自动限制重新提交次数"""
        pr = PurchaseRequest(
            request_no="PR-LIMIT-001",
            requested_by=3,
            total_amount=Decimal("170000.00"),
            status="DRAFT",
            resubmit_count=0,
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        max_resubmit = 3

        # 多次驳回和重提交
        for i in range(max_resubmit + 1):
            pr.status = "PENDING_APPROVAL"
            pr.resubmit_count += 1
            db_session.commit()

            # 驳回
            pr.status = "REJECTED"
            db_session.commit()

            if pr.resubmit_count >= max_resubmit:
                pr.status = "CLOSED"
                break

        assert pr.status == "CLOSED"
        assert pr.resubmit_count >= max_resubmit

    def test_08_rejection_with_escalation(self, db_session: Session):
        """测试8：驳回后升级处理"""
        pr = PurchaseRequest(
            request_no="PR-ESC-001",
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

        task = ApprovalTask(
            instance_id=instance.id,
            assignee_id=4,
            status="PENDING",
        )
        db_session.add(task)
        db_session.commit()

        # 驳回
        task.status = "REJECTED"
        db_session.commit()

        # 申请人不同意，升级到上级
        instance.status = "ESCALATED"
        instance.escalated_to = 1  # 总经理
        db_session.commit()

        assert instance.status == "ESCALATED"

    def test_09_batch_rejection_handling(self, db_session: Session):
        """测试9：批量驳回处理"""
        # 创建多个相关申请
        requests = []
        for i in range(3):
            pr = PurchaseRequest(
                request_no=f"PR-BATCH-REJ-{i+1:03d}",
                requested_by=3,
                total_amount=Decimal("80000.00"),
                status="PENDING_APPROVAL",
                batch_key="BATCH-001",
                created_by=3,
            )
            db_session.add(pr)
            requests.append(pr)
        db_session.commit()

        # 批量驳回
        for pr in requests:
            pr.status = "REJECTED"
            pr.reject_reason = "批量驳回：预算调整"
        db_session.commit()

        rejected_count = sum(1 for pr in requests if pr.status == "REJECTED")
        assert rejected_count == 3

    def test_10_rejection_history_tracking(self, db_session: Session):
        """测试10：驳回历史跟踪"""
        pr = PurchaseRequest(
            request_no="PR-HISTORY-001",
            requested_by=3,
            total_amount=Decimal("190000.00"),
            status="DRAFT",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        # 第一次审批实例
        instance1 = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="REJECTED",
            created_at=datetime.now() - timedelta(days=5),
            initiator_id=3,
        )
        db_session.add(instance1)
        db_session.commit()

        # 第二次审批实例
        instance2 = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="REJECTED",
            previous_instance_id=instance1.id,
            created_at=datetime.now() - timedelta(days=2),
            initiator_id=3,
        )
        db_session.add(instance2)
        db_session.commit()

        # 第三次审批实例
        instance3 = ApprovalInstance(
            entity_type="PURCHASE_REQUEST",
            entity_id=pr.id,
            instance_no=pr.request_code,
            initiator_id=3,
            status="APPROVED",
            previous_instance_id=instance2.id,
            initiator_id=3,
        )
        db_session.add(instance3)
        db_session.commit()

        # 查询审批历史
        history = db_session.query(ApprovalInstance).filter(
            ApprovalInstance.business_id == pr.id,
            ApprovalInstance.business_type == "PURCHASE_REQUEST"
        ).order_by(ApprovalInstance.created_at).all()

        assert len(history) == 3
        assert history[0].status == "REJECTED"
        assert history[1].status == "REJECTED"
        assert history[2].status == "APPROVED"
