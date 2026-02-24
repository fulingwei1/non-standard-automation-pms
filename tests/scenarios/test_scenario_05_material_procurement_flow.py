"""
场景5：物料需求 → 采购 → 入库 → 领用流程

测试物料从需求提出到实际使用的完整流程
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
try:
    from app.models.material import Material, MaterialInventory, MaterialRequisition
    from app.models.purchase import PurchaseRequest, PurchaseOrder
    from app.models.vendor import Vendor
except ImportError as e:
    pytest.skip(f"Required models not available: {e}", allow_module_level=True)


class TestMaterialProcurementFlow:
    """物料采购流程测试"""

    @pytest.fixture
    def test_vendor(self, db_session: Session):
        vendor = Vendor(
            supplier_code="SUP-MAT-001",
            supplier_name="物料供应商",
            vendor_type="MATERIAL",
            contact_person="供应商联系人",
            contact_phone="13700137000",
            status="ACTIVE",
            created_by=1,
        )
        db_session.add(vendor)
        db_session.commit()
        db_session.refresh(vendor)
        return vendor

    def test_01_create_material_requisition(self, db_session: Session):
        """测试1：创建物料需求"""
        material = Material(
            material_code="MAT-REQ-001",
            material_name="需求测试物料",
            category="ELECTRICAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        req = MaterialRequisition(
            requisition_code="MR-001",
            material_id=material.id,
            requested_quantity=Decimal("50"),
            required_date=date.today() + timedelta(days=14),
            purpose="生产使用",
            status="PENDING",
            created_by=2,
        )
        db_session.add(req)
        db_session.commit()

        assert req.id is not None
        assert req.status == "PENDING"

    def test_02_approve_material_requisition(self, db_session: Session):
        """测试2：审批物料需求"""
        material = Material(
            material_code="MAT-REQ-002",
            material_name="审批测试物料",
            category="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        req = MaterialRequisition(
            requisition_code="MR-002",
            material_id=material.id,
            requested_quantity=Decimal("30"),
            status="PENDING",
            created_by=2,
        )
        db_session.add(req)
        db_session.commit()

        # 审批通过
        req.status = "APPROVED"
        req.approved_by = 1
        db_session.commit()

        assert req.status == "APPROVED"

    def test_03_create_purchase_request_from_requisition(
        self, db_session: Session
    ):
        """测试3：从物料需求创建采购申请"""
        material = Material(
            material_code="MAT-PR-001",
            material_name="采购申请测试物料",
            category="GENERAL",
            unit="PCS",
            standard_price=Decimal("200.00"),
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        req = MaterialRequisition(
            requisition_code="MR-003",
            material_id=material.id,
            requested_quantity=Decimal("40"),
            status="APPROVED",
            created_by=2,
        )
        db_session.add(req)
        db_session.commit()

        # 创建采购申请
        pr = PurchaseRequest(
            request_code="PR-MAT-001",
            requester_id=2,
            total_amount=req.requested_quantity * material.standard_price,
            status="DRAFT",
            source_requisition_id=req.id,
            created_by=2,
        )
        db_session.add(pr)
        db_session.commit()

        assert pr.source_requisition_id == req.id
        assert pr.total_amount == Decimal("8000.00")

    def test_04_create_purchase_order(
        self, db_session: Session, test_vendor: Vendor
    ):
        """测试4：创建采购订单"""
        material = Material(
            material_code="MAT-PO-001",
            material_name="采购订单测试物料",
            category="GENERAL",
            unit="PCS",
            standard_price=Decimal("150.00"),
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        po = PurchaseOrder(
            order_code="PO-MAT-001",
            supplier_id=test_vendor.id,
            order_date=date.today(),
            delivery_date=date.today() + timedelta(days=20),
            total_amount=Decimal("6000.00"),
            status="CONFIRMED",
            created_by=1,
        )
        db_session.add(po)
        db_session.commit()

        assert po.status == "CONFIRMED"

    def test_05_receive_materials(self, db_session: Session):
        """测试5：物料入库"""
        material = Material(
            material_code="MAT-RCV-001",
            material_name="入库测试物料",
            category="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        # 物料入库
        inventory = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            location="A-01-01",
            quantity=Decimal("50"),
            available_quantity=Decimal("50"),
        )
        db_session.add(inventory)
        db_session.commit()

        assert inventory.quantity == Decimal("50")

    def test_06_issue_materials_for_production(self, db_session: Session):
        """测试6：物料领用"""
        material = Material(
            material_code="MAT-ISS-001",
            material_name="领用测试物料",
            category="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        inventory = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            quantity=Decimal("100"),
            available_quantity=Decimal("100"),
            reserved_quantity=Decimal("0"),
        )
        db_session.add(inventory)
        db_session.commit()

        # 领用30件
        issue_qty = Decimal("30")
        inventory.quantity -= issue_qty
        inventory.available_quantity -= issue_qty
        db_session.commit()

        assert inventory.quantity == Decimal("70")

    def test_07_return_unused_materials(self, db_session: Session):
        """测试7：退料"""
        material = Material(
            material_code="MAT-RET-001",
            material_name="退料测试物料",
            category="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        inventory = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            quantity=Decimal("50"),
            available_quantity=Decimal("50"),
        )
        db_session.add(inventory)
        db_session.commit()

        # 退料10件
        return_qty = Decimal("10")
        inventory.quantity += return_qty
        inventory.available_quantity += return_qty
        db_session.commit()

        assert inventory.quantity == Decimal("60")

    def test_08_reserve_materials(self, db_session: Session):
        """测试8：物料预留"""
        material = Material(
            material_code="MAT-RSV-001",
            material_name="预留测试物料",
            category="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        inventory = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            quantity=Decimal("80"),
            available_quantity=Decimal("80"),
            reserved_quantity=Decimal("0"),
        )
        db_session.add(inventory)
        db_session.commit()

        # 预留20件
        reserve_qty = Decimal("20")
        inventory.available_quantity -= reserve_qty
        inventory.reserved_quantity += reserve_qty
        db_session.commit()

        assert inventory.available_quantity == Decimal("60")
        assert inventory.reserved_quantity == Decimal("20")

    def test_09_cancel_reservation(self, db_session: Session):
        """测试9：取消预留"""
        material = Material(
            material_code="MAT-CNCL-001",
            material_name="取消预留测试物料",
            category="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        inventory = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            quantity=Decimal("100"),
            available_quantity=Decimal("70"),
            reserved_quantity=Decimal("30"),
        )
        db_session.add(inventory)
        db_session.commit()

        # 取消预留15件
        cancel_qty = Decimal("15")
        inventory.available_quantity += cancel_qty
        inventory.reserved_quantity -= cancel_qty
        db_session.commit()

        assert inventory.available_quantity == Decimal("85")
        assert inventory.reserved_quantity == Decimal("15")

    def test_10_complete_material_flow(self, db_session: Session, test_vendor: Vendor):
        """测试10：完整物料流程"""
        # 1. 创建物料
        material = Material(
            material_code="MAT-FULL-001",
            material_name="完整流程测试物料",
            category="GENERAL",
            unit="PCS",
            standard_price=Decimal("100.00"),
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        # 2. 创建需求
        req = MaterialRequisition(
            requisition_code="MR-FULL-001",
            material_id=material.id,
            requested_quantity=Decimal("100"),
            status="APPROVED",
            created_by=2,
        )
        db_session.add(req)
        db_session.commit()

        # 3. 创建采购订单
        po = PurchaseOrder(
            order_code="PO-FULL-001",
            supplier_id=test_vendor.id,
            order_date=date.today(),
            total_amount=Decimal("10000.00"),
            status="CONFIRMED",
            created_by=1,
        )
        db_session.add(po)
        db_session.commit()

        # 4. 入库
        inventory = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            quantity=Decimal("100"),
            available_quantity=Decimal("100"),
            reserved_quantity=Decimal("0"),
        )
        db_session.add(inventory)
        db_session.commit()

        # 5. 预留
        inventory.available_quantity -= Decimal("50")
        inventory.reserved_quantity += Decimal("50")
        db_session.commit()

        # 6. 领用
        inventory.quantity -= Decimal("50")
        inventory.reserved_quantity -= Decimal("50")
        db_session.commit()

        # 验证最终状态
        assert inventory.quantity == Decimal("50")
        assert inventory.available_quantity == Decimal("50")
        assert inventory.reserved_quantity == Decimal("0")
