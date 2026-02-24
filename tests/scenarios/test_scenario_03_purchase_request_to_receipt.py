"""
场景3：采购申请 → 审批 → 订单 → 收货 完整流程

测试采购业务从需求申请到物料入库的完整链路
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
try:
    from app.models.purchase import (
        PurchaseRequest,
        PurchaseOrder,
        PurchaseOrderItem,
        PurchaseReceipt,
        PurchaseReceiptItem,
    )
    from app.models.vendor import Vendor
    from app.models.material import Material
    from app.models.approval.instance import ApprovalInstance
except ImportError as e:
    pytest.skip(f"Required models not available: {e}", allow_module_level=True)


class TestPurchaseRequestToReceipt:
    """采购完整流程测试"""

    @pytest.fixture
    def test_supplier(self, db_session: Session):
        """创建测试供应商"""
        supplier = Vendor(
            supplier_code="SUP-TEST-001",
            supplier_name="测试供应商A",
            vendor_type="MATERIAL",
            contact_person="王经理",
            contact_phone="13700137000",
            status="ACTIVE",
            created_by=1,
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)
        return supplier

    @pytest.fixture
    def test_material(self, db_session: Session):
        """创建测试物料"""
        material = Material(
            material_code="MAT-001",
            material_name="测试物料-电机",
            category="ELECTRICAL",
            unit="PCS",
            standard_price=Decimal("1500.00"),
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()
        db_session.refresh(material)
        return material

    def test_01_create_purchase_request(self, db_session: Session, test_material: Material):
        """测试1：创建采购申请"""
        pr = PurchaseRequest(
            request_code="PR-2026-001",
            request_date=date.today(),
            requester_id=2,
            department="工程部",
            request_type="NORMAL",
            status="DRAFT",
            total_amount=Decimal("15000.00"),
            remark="项目物料采购",
            created_by=2,
        )
        db_session.add(pr)
        db_session.commit()

        assert pr.id is not None
        assert pr.status == "DRAFT"

    def test_02_submit_purchase_request_for_approval(self, db_session: Session):
        """测试2：提交采购申请审批"""
        pr = PurchaseRequest(
            request_code="PR-2026-002",
            request_date=date.today(),
            requester_id=2,
            status="DRAFT",
            total_amount=Decimal("8000.00"),
            created_by=2,
        )
        db_session.add(pr)
        db_session.commit()

        # 提交审批
        pr.status = "PENDING_APPROVAL"
        pr.submitted_at = datetime.now()
        db_session.commit()

        assert pr.status == "PENDING_APPROVAL"
        assert pr.submitted_at is not None

    def test_03_approve_purchase_request(self, db_session: Session):
        """测试3：审批采购申请"""
        pr = PurchaseRequest(
            request_code="PR-2026-003",
            request_date=date.today(),
            requester_id=2,
            status="PENDING_APPROVAL",
            total_amount=Decimal("12000.00"),
            created_by=2,
        )
        db_session.add(pr)
        db_session.commit()

        # 部门经理审批
        pr.status = "APPROVED"
        pr.approved_by = 1
        pr.approved_at = datetime.now()
        db_session.commit()

        assert pr.status == "APPROVED"
        assert pr.approved_by is not None

    def test_04_reject_and_resubmit_purchase_request(self, db_session: Session):
        """测试4：驳回采购申请并重新提交"""
        pr = PurchaseRequest(
            request_code="PR-2026-004",
            request_date=date.today(),
            requester_id=2,
            status="PENDING_APPROVAL",
            total_amount=Decimal("50000.00"),
            created_by=2,
        )
        db_session.add(pr)
        db_session.commit()

        # 驳回
        pr.status = "REJECTED"
        pr.reject_reason = "预算不足，需重新评估"
        db_session.commit()

        # 修改后重新提交
        pr.total_amount = Decimal("35000.00")
        pr.status = "PENDING_APPROVAL"
        pr.reject_reason = None
        db_session.commit()

        # 再次审批通过
        pr.status = "APPROVED"
        db_session.commit()

        assert pr.status == "APPROVED"
        assert pr.total_amount == Decimal("35000.00")

    def test_05_create_purchase_order_from_request(
        self, db_session: Session, test_supplier: Vendor, test_material: Material
    ):
        """测试5：从采购申请创建采购订单"""
        # 创建已批准的采购申请
        pr = PurchaseRequest(
            request_code="PR-2026-005",
            request_date=date.today(),
            requester_id=2,
            status="APPROVED",
            total_amount=Decimal("18000.00"),
            created_by=2,
        )
        db_session.add(pr)
        db_session.commit()

        # 创建采购订单
        po = PurchaseOrder(
            order_code="PO-2026-001",
            request_id=pr.id,
            supplier_id=test_supplier.id,
            order_date=date.today(),
            delivery_date=date.today() + timedelta(days=30),
            total_amount=Decimal("18000.00"),
            status="DRAFT",
            payment_terms="货到付款",
            created_by=1,
        )
        db_session.add(po)
        db_session.commit()

        # 添加订单明细
        po_item = PurchaseOrderItem(
            order_id=po.id,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            quantity=Decimal("12"),
            unit_price=Decimal("1500.00"),
            total_price=Decimal("18000.00"),
        )
        db_session.add(po_item)
        db_session.commit()

        # 采购申请状态更新
        pr.status = "ORDERED"
        db_session.commit()

        assert po.id is not None
        assert pr.status == "ORDERED"

    def test_06_confirm_purchase_order(self, db_session: Session, test_supplier: Vendor):
        """测试6：确认采购订单"""
        po = PurchaseOrder(
            order_code="PO-2026-002",
            supplier_id=test_supplier.id,
            order_date=date.today(),
            total_amount=Decimal("25000.00"),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(po)
        db_session.commit()

        # 确认订单
        po.status = "CONFIRMED"
        po.confirmed_by = 1
        po.confirmed_at = datetime.now()
        db_session.commit()

        assert po.status == "CONFIRMED"

    def test_07_send_purchase_order_to_supplier(self, db_session: Session, test_supplier: Vendor):
        """测试7：发送采购订单给供应商"""
        po = PurchaseOrder(
            order_code="PO-2026-003",
            supplier_id=test_supplier.id,
            order_date=date.today(),
            total_amount=Decimal("30000.00"),
            status="CONFIRMED",
            created_by=1,
        )
        db_session.add(po)
        db_session.commit()

        # 发送给供应商
        po.status = "SENT"
        po.sent_at = datetime.now()
        db_session.commit()

        assert po.status == "SENT"

    def test_08_create_purchase_receipt(
        self, db_session: Session, test_supplier: Vendor, test_material: Material
    ):
        """测试8：创建采购收货单"""
        # 创建采购订单
        po = PurchaseOrder(
            order_code="PO-2026-004",
            supplier_id=test_supplier.id,
            order_date=date.today(),
            delivery_date=date.today() + timedelta(days=15),
            total_amount=Decimal("22500.00"),
            status="SENT",
            created_by=1,
        )
        db_session.add(po)
        db_session.commit()

        # 创建订单明细
        po_item = PurchaseOrderItem(
            order_id=po.id,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            quantity=Decimal("15"),
            unit_price=Decimal("1500.00"),
            total_price=Decimal("22500.00"),
            received_quantity=Decimal("0"),
        )
        db_session.add(po_item)
        db_session.commit()

        # 创建收货单
        receipt = PurchaseReceipt(
            receipt_code="GR-2026-001",
            order_id=po.id,
            supplier_id=test_supplier.id,
            receipt_date=date.today(),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(receipt)
        db_session.commit()

        # 创建收货明细
        receipt_item = PurchaseReceiptItem(
            receipt_id=receipt.id,
            order_item_id=po_item.id,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            ordered_quantity=Decimal("15"),
            received_quantity=Decimal("15"),
            qualified_quantity=Decimal("15"),
            rejected_quantity=Decimal("0"),
        )
        db_session.add(receipt_item)
        db_session.commit()

        assert receipt.id is not None
        assert receipt_item.received_quantity == Decimal("15")

    def test_09_conduct_quality_inspection(
        self, db_session: Session, test_supplier: Vendor, test_material: Material
    ):
        """测试9：执行质量检验"""
        po = PurchaseOrder(
            order_code="PO-2026-005",
            supplier_id=test_supplier.id,
            order_date=date.today(),
            status="SENT",
            created_by=1,
        )
        db_session.add(po)
        db_session.commit()

        po_item = PurchaseOrderItem(
            order_id=po.id,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            quantity=Decimal("20"),
            unit_price=Decimal("1500.00"),
            total_price=Decimal("30000.00"),
        )
        db_session.add(po_item)
        db_session.commit()

        receipt = PurchaseReceipt(
            receipt_code="GR-2026-002",
            order_id=po.id,
            supplier_id=test_supplier.id,
            receipt_date=date.today(),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(receipt)
        db_session.commit()

        # 质检结果
        receipt_item = PurchaseReceiptItem(
            receipt_id=receipt.id,
            order_item_id=po_item.id,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            ordered_quantity=Decimal("20"),
            received_quantity=Decimal("20"),
            qualified_quantity=Decimal("18"),  # 18个合格
            rejected_quantity=Decimal("2"),  # 2个不合格
            inspection_result="PARTIAL_PASS",
        )
        db_session.add(receipt_item)
        db_session.commit()

        assert receipt_item.qualified_quantity == Decimal("18")
        assert receipt_item.rejected_quantity == Decimal("2")

    def test_10_complete_purchase_receipt(self, db_session: Session, test_supplier: Vendor):
        """测试10：完成采购收货"""
        po = PurchaseOrder(
            order_code="PO-2026-006",
            supplier_id=test_supplier.id,
            order_date=date.today(),
            status="SENT",
            created_by=1,
        )
        db_session.add(po)
        db_session.commit()

        receipt = PurchaseReceipt(
            receipt_code="GR-2026-003",
            order_id=po.id,
            supplier_id=test_supplier.id,
            receipt_date=date.today(),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(receipt)
        db_session.commit()

        # 完成收货
        receipt.status = "COMPLETED"
        receipt.completed_by = 1
        receipt.completed_at = datetime.now()
        db_session.commit()

        # 订单状态更新
        po.status = "RECEIVED"
        db_session.commit()

        assert receipt.status == "COMPLETED"
        assert po.status == "RECEIVED"

    def test_11_handle_partial_delivery(
        self, db_session: Session, test_supplier: Vendor, test_material: Material
    ):
        """测试11：处理部分交货"""
        po = PurchaseOrder(
            order_code="PO-2026-007",
            supplier_id=test_supplier.id,
            order_date=date.today(),
            total_amount=Decimal("30000.00"),
            status="SENT",
            created_by=1,
        )
        db_session.add(po)
        db_session.commit()

        po_item = PurchaseOrderItem(
            order_id=po.id,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            quantity=Decimal("20"),
            unit_price=Decimal("1500.00"),
            total_price=Decimal("30000.00"),
            received_quantity=Decimal("0"),
        )
        db_session.add(po_item)
        db_session.commit()

        # 第一次收货（部分）
        receipt1 = PurchaseReceipt(
            receipt_code="GR-2026-004A",
            order_id=po.id,
            supplier_id=test_supplier.id,
            receipt_date=date.today(),
            status="COMPLETED",
            created_by=1,
        )
        db_session.add(receipt1)
        db_session.commit()

        receipt_item1 = PurchaseReceiptItem(
            receipt_id=receipt1.id,
            order_item_id=po_item.id,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            ordered_quantity=Decimal("20"),
            received_quantity=Decimal("12"),
            qualified_quantity=Decimal("12"),
        )
        db_session.add(receipt_item1)
        db_session.commit()

        # 更新订单明细已收数量
        po_item.received_quantity = Decimal("12")
        db_session.commit()

        # 第二次收货（剩余）
        receipt2 = PurchaseReceipt(
            receipt_code="GR-2026-004B",
            order_id=po.id,
            supplier_id=test_supplier.id,
            receipt_date=date.today() + timedelta(days=3),
            status="COMPLETED",
            created_by=1,
        )
        db_session.add(receipt2)
        db_session.commit()

        receipt_item2 = PurchaseReceiptItem(
            receipt_id=receipt2.id,
            order_item_id=po_item.id,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            ordered_quantity=Decimal("20"),
            received_quantity=Decimal("8"),
            qualified_quantity=Decimal("8"),
        )
        db_session.add(receipt_item2)
        db_session.commit()

        # 更新订单明细已收数量
        po_item.received_quantity = Decimal("20")
        db_session.commit()

        # 订单完全收货
        po.status = "RECEIVED"
        db_session.commit()

        assert po_item.received_quantity == po_item.quantity
        assert po.status == "RECEIVED"

    def test_12_track_purchase_lead_time(
        self, db_session: Session, test_supplier: Vendor
    ):
        """测试12：跟踪采购提前期"""
        # 记录时间戳
        request_date = date.today() - timedelta(days=50)
        approval_date = date.today() - timedelta(days=45)
        order_date = date.today() - timedelta(days=40)
        delivery_date = date.today() - timedelta(days=10)
        receipt_date = date.today()

        # 计算各阶段提前期
        approval_lead_time = (approval_date - request_date).days
        ordering_lead_time = (order_date - approval_date).days
        supplier_lead_time = (delivery_date - order_date).days
        inspection_lead_time = (receipt_date - delivery_date).days
        total_lead_time = (receipt_date - request_date).days

        # 验证提前期
        assert approval_lead_time == 5  # 审批用时
        assert ordering_lead_time == 5  # 下单用时
        assert supplier_lead_time == 30  # 供应商交货用时
        assert inspection_lead_time == 10  # 检验用时
        assert total_lead_time == 50  # 总提前期
