# -*- coding: utf-8 -*-
"""
K2组集成测试 - 采购到入库闭环流程
流程：BOM缺料检测 → 采购申请 → 申请审批 → 采购订单 → 到货收货 → 质检入库
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal


# ============================================================
# SQLite 内存数据库 fixture
# ============================================================
@pytest.fixture(scope="module")
def db():
    """为本模块提供独立的 SQLite 内存数据库"""
    import sys
    from unittest.mock import MagicMock
    if "redis" not in sys.modules:
        sys.modules["redis"] = MagicMock()
        sys.modules["redis.exceptions"] = MagicMock()

    import os
    os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
    os.environ.setdefault("REDIS_URL", "")
    os.environ.setdefault("ENABLE_SCHEDULER", "false")

    import app.models  # noqa: F401 - 注册所有 ORM 元数据
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ============================================================
# 基础数据 fixtures
# ============================================================
@pytest.fixture(scope="module")
def tenant(db):
    """创建测试租户（MaterialTransaction 必须关联租户）"""
    from app.models.tenant import Tenant
    t = Tenant(
        tenant_code="TENANT-PURCH-001",
        tenant_name="测试租户",
        status="ACTIVE",
        plan_type="ENTERPRISE",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture(scope="module")
def purchase_user(db):
    """创建采购员用户"""
    from app.models.user import User
    from app.models.organization import Employee
    from app.core.security import get_password_hash

    emp = Employee(
        employee_code="EMP-PURCH-001",
        name="李采购",
        department="采购部",
        role="PURCHASE",
        phone="13800000002",
    )
    db.add(emp)
    db.flush()
    user = User(
        employee_id=emp.id,
        username="purchase_flow_test",
        password_hash=get_password_hash("test123"),
        real_name="李采购",
        department="采购部",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def purchase_customer(db):
    """创建关联客户"""
    from app.models.project import Customer
    c = Customer(
        customer_code="CUST-PURCH-001",
        customer_name="采购测试客户",
        contact_person="测试联系人",
        contact_phone="13900000002",
        status="ACTIVE",
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture(scope="module")
def purchase_project(db, purchase_customer, purchase_user):
    """创建关联项目"""
    from app.models.project import Project
    p = Project(
        project_code="PJ-PURCH-001",
        project_name="采购闭环测试项目",
        customer_id=purchase_customer.id,
        customer_name=purchase_customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        created_by=purchase_user.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture(scope="module")
def purchase_supplier(db, purchase_user):
    """创建供应商"""
    from app.models.vendor import Vendor
    v = Vendor(
        supplier_code="SUP-PURCH-001",
        supplier_name="精密零件供应商",
        vendor_type="MATERIAL",
        contact_person="赵供应",
        contact_phone="13700000002",
        status="ACTIVE",
        created_by=purchase_user.id,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@pytest.fixture(scope="module")
def test_material(db, purchase_user):
    """创建测试物料，初始库存为0（模拟缺料）"""
    from app.models.material import Material
    m = Material(
        material_code="MAT-PURCH-001",
        material_name="精密轴承 6205-2RS",
        specification="内径25mm 外径52mm 厚15mm",
        brand="NSK",
        unit="个",
        material_type="PURCHASED",
        source_type="PURCHASE",
        standard_price=Decimal("45.00"),
        safety_stock=Decimal("10"),
        current_stock=Decimal("0"),   # 初始缺料
        lead_time_days=14,
        is_active=True,
        created_by=purchase_user.id,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


# ============================================================
# 测试用例
# ============================================================
class TestPurchaseInventoryIntegration:
    """采购到入库闭环集成测试"""

    # ─── 1. BOM 缺料检测 ─────────────────────────────────────
    def test_bom_shortage_detected(self, db, purchase_project, purchase_user,
                                   purchase_customer, test_material):
        """BOM 创建后检测到物料缺料"""
        from app.models.material import BomHeader, BomItem

        # 创建 BOM 表头
        bom = BomHeader(
            bom_no="BOM-PURCH-001",
            bom_name="装配机主体 BOM",
            project_id=purchase_project.id,
            version="V1.0",
            is_latest=True,
            status="RELEASED",
            created_by=purchase_user.id,
        )
        db.add(bom)
        db.flush()

        # 添加 BOM 行：需要 50 个轴承
        bom_item = BomItem(
            bom_id=bom.id,
            item_no=1,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            specification=test_material.specification,
            unit=test_material.unit,
            quantity=Decimal("50"),
            unit_price=test_material.standard_price,
            source_type="PURCHASE",
            level=1,
            sort_order=1,
        )
        db.add(bom_item)
        db.commit()
        db.refresh(bom_item)

        # 检测缺料：需求 50，库存 0 → 缺货 50 个
        shortage_qty = float(bom_item.quantity) - float(test_material.current_stock)
        assert shortage_qty == 50.0
        assert float(test_material.current_stock) == 0.0
        assert bom_item.material_code == "MAT-PURCH-001"

    # ─── 2. 创建采购申请 ──────────────────────────────────────
    def test_purchase_request_created_from_shortage(self, db, purchase_project,
                                                     purchase_user, purchase_supplier,
                                                     test_material):
        """基于缺料创建采购申请"""
        from app.models.purchase import PurchaseRequest, PurchaseRequestItem
        from app.models.material import BomItem

        bom_item = db.query(BomItem).filter(
            BomItem.bom_id == db.query(BomItem).filter(
                BomItem.material_code == "MAT-PURCH-001"
            ).first().bom_id
        ).first()

        # 创建采购申请
        request = PurchaseRequest(
            request_no="PR-PURCH-001",
            project_id=purchase_project.id,
            supplier_id=purchase_supplier.id,
            request_type="NORMAL",
            source_type="BOM",
            source_id=bom_item.id,
            request_reason="BOM缺料，项目生产急需",
            required_date=date.today() + timedelta(days=21),
            total_amount=Decimal("2250.00"),
            status="DRAFT",
            requested_by=purchase_user.id,
            created_by=purchase_user.id,
        )
        db.add(request)
        db.flush()

        # 添加申请明细
        item = PurchaseRequestItem(
            request_id=request.id,
            bom_item_id=bom_item.id,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            specification=test_material.specification,
            unit=test_material.unit,
            quantity=Decimal("50"),
            unit_price=test_material.standard_price,
            amount=Decimal("2250.00"),
            required_date=request.required_date,
        )
        db.add(item)
        db.commit()
        db.refresh(request)

        assert request.id is not None
        assert request.status == "DRAFT"
        assert request.source_type == "BOM"
        items = db.query(PurchaseRequestItem).filter(
            PurchaseRequestItem.request_id == request.id
        ).all()
        assert len(items) == 1
        assert float(items[0].quantity) == 50.0

    # ─── 3. 提交采购申请审批 ──────────────────────────────────
    def test_purchase_request_submitted_for_approval(self, db, purchase_user):
        """采购申请提交审批，状态变为 PENDING"""
        from app.models.purchase import PurchaseRequest

        request = db.query(PurchaseRequest).filter(
            PurchaseRequest.request_no == "PR-PURCH-001"
        ).first()
        assert request is not None

        request.status = "PENDING"
        request.submitted_at = datetime.now()
        request.requested_at = datetime.now()
        db.commit()
        db.refresh(request)

        assert request.status == "PENDING"
        assert request.submitted_at is not None

    # ─── 4. 审批通过，生成采购订单 ───────────────────────────
    def test_purchase_order_created_from_approved_request(self, db, purchase_user,
                                                           purchase_project,
                                                           purchase_supplier,
                                                           test_material):
        """采购申请审批通过后，创建采购订单"""
        from app.models.purchase import (
            PurchaseRequest, PurchaseOrder, PurchaseOrderItem
        )

        request = db.query(PurchaseRequest).filter(
            PurchaseRequest.request_no == "PR-PURCH-001"
        ).first()

        # 审批通过
        request.status = "APPROVED"
        request.approved_by = purchase_user.id
        request.approved_at = datetime.now()
        request.approval_note = "采购必要，金额合理，批准采购"
        db.flush()

        # 创建采购订单
        order = PurchaseOrder(
            order_no="PO-PURCH-001",
            supplier_id=purchase_supplier.id,
            project_id=purchase_project.id,
            source_request_id=request.id,
            order_type="NORMAL",
            order_title="精密轴承采购订单",
            total_amount=Decimal("2250.00"),
            tax_rate=Decimal("13"),
            tax_amount=Decimal("292.50"),
            amount_with_tax=Decimal("2542.50"),
            currency="CNY",
            order_date=date.today(),
            required_date=date.today() + timedelta(days=14),
            status="CONFIRMED",
            payment_terms="货到验收后30日付款",
            delivery_address="上海市嘉定区工厂仓库",
            created_by=purchase_user.id,
        )
        db.add(order)
        db.flush()

        # 订单明细
        order_item = PurchaseOrderItem(
            order_id=order.id,
            item_no=1,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            specification=test_material.specification,
            unit=test_material.unit,
            quantity=Decimal("50"),
            unit_price=Decimal("45.00"),
            amount=Decimal("2250.00"),
            tax_rate=Decimal("13"),
            required_date=order.required_date,
            status="PENDING",
        )
        db.add(order_item)
        db.commit()
        db.refresh(order)

        # 更新申请的自动生单状态
        request.auto_po_created = True
        request.auto_po_created_at = datetime.now()
        db.commit()

        assert order.id is not None
        assert order.status == "CONFIRMED"
        assert order.source_request_id == request.id
        assert request.auto_po_created is True

    # ─── 5. 供应商发货，创建收货单 ───────────────────────────
    def test_goods_receipt_created_on_delivery(self, db, purchase_user,
                                                purchase_supplier):
        """供应商送货到厂，创建到货收货单"""
        from app.models.purchase import PurchaseOrder, PurchaseOrderItem, GoodsReceipt

        order = db.query(PurchaseOrder).filter(
            PurchaseOrder.order_no == "PO-PURCH-001"
        ).first()
        order_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.order_id == order.id
        ).first()

        receipt = GoodsReceipt(
            receipt_no="GR-PURCH-001",
            order_id=order.id,
            supplier_id=purchase_supplier.id,
            receipt_date=date.today(),
            receipt_type="NORMAL",
            delivery_note_no="DN-2026-001",
            logistics_company="顺丰物流",
            tracking_no="SF1234567890",
            status="PENDING",
            inspect_status="PENDING",
            created_by=purchase_user.id,
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)

        assert receipt.id is not None
        assert receipt.status == "PENDING"
        assert receipt.order_id == order.id

    # ─── 6. 质检通过，完成入库 ───────────────────────────────
    def test_goods_receipt_inspection_and_warehousing(self, db, purchase_user,
                                                       test_material):
        """收货质检通过，执行入库并更新库存"""
        from app.models.purchase import (
            PurchaseOrder, PurchaseOrderItem,
            GoodsReceipt, GoodsReceiptItem
        )

        receipt = db.query(GoodsReceipt).filter(
            GoodsReceipt.receipt_no == "GR-PURCH-001"
        ).first()
        order_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.order_id == receipt.order_id
        ).first()

        # 创建收货明细
        ri = GoodsReceiptItem(
            receipt_id=receipt.id,
            order_item_id=order_item.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            delivery_qty=Decimal("50"),
            received_qty=Decimal("50"),
            inspect_qty=Decimal("50"),
            qualified_qty=Decimal("48"),   # 48件合格
            rejected_qty=Decimal("2"),     # 2件不合格
            inspect_result="PARTIAL_PASS",
            inspect_note="2件外观有轻微划痕，其余均合格",
            warehoused_qty=Decimal("48"),
            warehouse_location="A-01-03",
        )
        db.add(ri)

        # 更新收货单状态
        receipt.status = "RECEIVED"
        receipt.inspect_status = "PARTIAL_PASS"
        receipt.inspected_at = datetime.now()
        receipt.inspected_by = purchase_user.id
        receipt.warehoused_at = datetime.now()
        receipt.warehoused_by = purchase_user.id
        db.flush()

        # 更新物料库存（入库48件）
        test_material.current_stock = Decimal("0") + Decimal("48")
        test_material.last_price = order_item.unit_price
        db.commit()

        db.refresh(receipt)
        db.refresh(test_material)

        assert receipt.status == "RECEIVED"
        assert float(ri.warehoused_qty) == 48.0
        assert float(test_material.current_stock) == 48.0

    # ─── 7. 记录库存流水（入库事务） ─────────────────────────
    def test_inventory_transaction_recorded(self, db, tenant, purchase_user,
                                             test_material):
        """入库完成后，记录物料交易流水（PURCHASE_IN）"""
        from app.models.inventory_tracking import MaterialTransaction

        receipt = db.query(
            __import__("app.models.purchase", fromlist=["GoodsReceipt"]).GoodsReceipt
        ).filter_by(receipt_no="GR-PURCH-001").first()

        txn = MaterialTransaction(
            tenant_id=tenant.id,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            transaction_type="PURCHASE_IN",
            quantity=Decimal("48"),
            unit=test_material.unit,
            unit_price=Decimal("45.00"),
            total_amount=Decimal("2160.00"),
            target_location="A-01-03",
            batch_number="BATCH-20260217",
            related_order_id=receipt.order_id,
            related_order_type="PURCHASE_ORDER",
            related_order_no="PO-PURCH-001",
            transaction_date=datetime.now(),
            operator_id=purchase_user.id,
            cost_method="WEIGHTED_AVG",
            remark="采购入库，48件合格品",
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)

        assert txn.id is not None
        assert txn.transaction_type == "PURCHASE_IN"
        assert float(txn.quantity) == 48.0

    # ─── 8. 全流程闭环验证 ───────────────────────────────────
    def test_full_purchase_flow_end_to_end(self, db, test_material,
                                            purchase_project, purchase_supplier):
        """验证采购到入库完整链路的数据一致性"""
        from app.models.purchase import (
            PurchaseRequest, PurchaseOrder,
            GoodsReceipt, GoodsReceiptItem
        )
        from app.models.inventory_tracking import MaterialTransaction
        from app.models.material import BomItem

        # 查询各环节记录
        request = db.query(PurchaseRequest).filter(
            PurchaseRequest.request_no == "PR-PURCH-001"
        ).first()
        order = db.query(PurchaseOrder).filter(
            PurchaseOrder.order_no == "PO-PURCH-001"
        ).first()
        receipt = db.query(GoodsReceipt).filter(
            GoodsReceipt.receipt_no == "GR-PURCH-001"
        ).first()
        txn = db.query(MaterialTransaction).filter(
            MaterialTransaction.related_order_no == "PO-PURCH-001"
        ).first()

        # 链路关联校验
        assert request.status == "APPROVED"
        assert order.source_request_id == request.id
        assert receipt.order_id == order.id
        assert txn is not None
        assert txn.material_code == test_material.material_code

        # 库存数量校验：48 件已入库
        assert float(test_material.current_stock) == 48.0

        # BOM 缺料数量已满足（需求50，到货48，仍缺2件）
        bom_item = db.query(BomItem).filter(
            BomItem.material_code == "MAT-PURCH-001"
        ).first()
        remaining_shortage = float(bom_item.quantity) - float(test_material.current_stock)
        assert remaining_shortage == 2.0   # 2件不合格，仍有少量缺口

        # 金额一致性
        assert float(order.total_amount) == float(request.total_amount)
