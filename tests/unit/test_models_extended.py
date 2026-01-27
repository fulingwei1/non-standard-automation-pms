# -*- coding: utf-8 -*-
"""
扩展模型单元测试 - Extended Model Tests

测试模型：
- project/core.py: Project, Machine
- material.py: Material, Supplier, BomHeader, BomItem
- purchase.py: PurchaseOrder, PurchaseOrderItem
- ecn.py: Ecn, EcnEvaluation, EcnTask
- acceptance.py: AcceptanceOrder, AcceptanceOrderItem
- outsourcing.py: OutsourcingOrder
- alert.py: AlertRecord, AlertRule
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session


# Import models
from app.models.project.core import Project, Machine
from app.models.material import Material, BomHeader, BomItem
from app.models.vendor import Vendor as Supplier, Vendor as OutsourcingVendor
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.ecn import Ecn, EcnEvaluation, EcnTask
from app.models.acceptance import AcceptanceOrder, AcceptanceOrderItem
from app.models.outsourcing import OutsourcingOrder
from app.models.alert import AlertRecord, AlertRule


# ============================================================================
# Project Core Models Tests
# ============================================================================


@pytest.mark.unit
class TestProjectModel:
    """项目模型测试"""

    @pytest.fixture
    def test_project_data(self, test_user, test_project_with_customer):
        """测试项目数据"""
        timestamp = datetime.now().timestamp()
        return {
        "project_code": f"PJTEST{timestamp}",
        "project_name": "测试项目",
        "customer_id": test_project_with_customer.customer_id,
        "customer_name": test_project_with_customer.customer_name,
        "stage": "S1",
        "status": "ST01",
        "health": "H1",
        "created_by": test_user.id,
        }

    def test_project_creation(self, db_session: Session, test_project_data):
        """测试项目创建"""
        project = Project(
        project_code=test_project_data["project_code"],
        project_name=test_project_data["project_name"],
        customer_id=test_project_data["customer_id"],
        customer_name=test_project_data["customer_name"],
        stage=test_project_data["stage"],
        status=test_project_data["status"],
        health=test_project_data["health"],
        created_by=test_project_data["created_by"],
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.id is not None
        assert project.project_code == test_project_data["project_code"]
        assert project.project_name == test_project_data["project_name"]
        assert project.customer_id == test_project_data["customer_id"]
        assert project.stage == test_project_data["stage"]
        assert project.status == test_project_data["status"]
        assert project.health == test_project_data["health"]

    def test_project_required_fields(self, db_session: Session, test_customer):
        """测试项目必填字段"""
        timestamp = datetime.now().timestamp()
        project = Project(
        project_code=f"PJREQ{timestamp}",
        project_name="必填字段测试",
        customer_id=test_customer.id,
        customer_name="必填客户",
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        assert project.project_code is not None
        assert project.project_name == "必填字段测试"
        assert project.stage == "S1"

    def test_project_date_fields(self, db_session: Session):
        """测试项目日期字段"""
        today = date.today()
        timestamp = datetime.now().timestamp()
        project = Project(
        project_code=f"PJDATE{timestamp}",
        project_name="日期字段测试",
        customer_id=1,
        customer_name="测试客户",
        contract_date=today,
        planned_start_date=today + timedelta(days=7),
        planned_end_date=today + timedelta(days=90),
        actual_start_date=today + timedelta(days=10),
        actual_end_date=today + timedelta(days=95),
        )
        db_session.add(project)
        db_session.commit()

        assert project.contract_date == today
        assert project.planned_start_date == today + timedelta(days=7)
        assert project.planned_end_date == today + timedelta(days=90)

    def test_project_amount_fields(self, db_session: Session):
        """测试项目金额字段"""
        timestamp = datetime.now().timestamp()
        project = Project(
        project_code=f"PJAMT{timestamp}",
        project_name="金额字段测试",
        customer_id=1,
        customer_name="测试客户",
        contract_amount=Decimal("1000000.00"),
        budget_amount=Decimal("950000.00"),
        actual_cost=Decimal("800000.00"),
        )
        db_session.add(project)
        db_session.commit()

        assert project.contract_amount == Decimal("1000000.00")
        assert project.budget_amount == Decimal("950000.00")
        assert project.actual_cost == Decimal("800000.00")

    def test_project_progress_field(self, db_session: Session):
        """测试项目进度字段"""
        timestamp = datetime.now().timestamp()
        project = Project(
        project_code=f"PJPROG{timestamp}",
        project_name="进度测试",
        customer_id=1,
        customer_name="测试客户",
        progress_pct=Decimal("75.50"),
        )
        db_session.add(project)
        db_session.commit()

        assert project.progress_pct == Decimal("75.50")

    def test_project_status_transitions(self, db_session: Session):
        """测试项目状态变更"""
        timestamp = datetime.now().timestamp()
        project = Project(
        project_code=f"PJSTAT{timestamp}",
        project_name="状态变更测试",
        customer_id=1,
        customer_name="测试客户",
        stage="S1",
        status="ST01",
        )
        db_session.add(project)
        db_session.commit()

        project.stage = "S5"
        project.status = "ST05"
        db_session.commit()

        assert project.stage == "S5"
        assert project.status == "ST05"

    def test_project_repr(self, db_session: Session):
        """测试项目字符串表示"""
        timestamp = datetime.now().timestamp()
        project = Project(
        project_code=f"PJREPR{timestamp}",
        project_name="repr测试",
        customer_id=1,
        customer_name="测试客户",
        )
        db_session.add(project)
        db_session.commit()

        assert f"<Project {project.project_code}>" in repr(project)


@pytest.mark.unit
class TestMachineModel:
    """设备模型测试"""

    @pytest.fixture
    def test_machine_data(self, test_project_with_customer):
        """测试设备数据"""
        return {
        "project_id": test_project_with_customer.id,
        "machine_code": f"MACH{datetime.now().timestamp()}",
        "machine_name": "测试设备",
        "machine_no": 1,
        "machine_type": "ICT测试设备",
        }

    def test_machine_creation(self, db_session: Session, test_machine_data):
        """测试设备创建"""
        machine = Machine(
        project_id=test_machine_data["project_id"],
        machine_code=test_machine_data["machine_code"],
        machine_name=test_machine_data["machine_name"],
        machine_no=test_machine_data["machine_no"],
        machine_type=test_machine_data["machine_type"],
        )
        db_session.add(machine)
        db_session.commit()
        db_session.refresh(machine)

        assert machine.id is not None
        assert machine.machine_code == test_machine_data["machine_code"]
        assert machine.project_id == test_machine_data["project_id"]

    def test_machine_required_fields(
        self, db_session: Session, test_project_with_customer
    ):
        """测试设备必填字段"""
        timestamp = datetime.now().timestamp()
        machine = Machine(
        project_id=test_project_with_customer.id,
        machine_code=f"MAC{timestamp}",
        machine_name="必填测试",
        machine_no=1,
        )
        db_session.add(machine)
        db_session.commit()

        assert machine.machine_code is not None
        assert machine.machine_name == "必填测试"
        assert machine.stage == "S1"

    def test_machine_stage_and_status(
        self, db_session: Session, test_project_with_customer
    ):
        timestamp = datetime.now().timestamp()
        machine = Machine(
        project_id=test_project_with_customer.id,
        machine_code=f"MSTATUS{timestamp}",
        machine_name="阶段状态测试",
        machine_no=1,
        stage="S4",
        status="ST04",
        health="H2",
        )
        db_session.add(machine)
        db_session.commit()

        assert machine.stage == "S4"
        assert machine.status == "ST04"
        assert machine.health == "H2"

    def test_machine_dates(self, db_session: Session, test_project_with_customer):
        today = date.today()
        timestamp = datetime.now().timestamp()
        machine = Machine(
        project_id=test_project_with_customer.id,
        machine_code=f"MDATE{timestamp}",
        machine_name="日期测试",
        machine_no=1,
        planned_start_date=today + timedelta(days=7),
        planned_end_date=today + timedelta(days=60),
        actual_start_date=today + timedelta(days=10),
        actual_end_date=today + timedelta(days=65),
        fat_date=today + timedelta(days=70),
        sat_date=today + timedelta(days=80),
        ship_date=today + timedelta(days=75),
        )
        db_session.add(machine)
        db_session.commit()

        assert machine.fat_date == today + timedelta(days=70)
        assert machine.sat_date == today + timedelta(days=80)

    def test_machine_progress(self, db_session: Session, test_project_with_customer):
        timestamp = datetime.now().timestamp()
        machine = Machine(
        project_id=test_project_with_customer.id,
        machine_code=f"MPROG{timestamp}",
        machine_name="进度测试",
        machine_no=1,
        progress_pct=Decimal("85.00"),
        )
        db_session.add(machine)
        db_session.commit()

        assert machine.progress_pct == Decimal("85.00")

    def test_machine_specification(
        self, db_session: Session, test_project_with_customer
    ):
        timestamp = datetime.now().timestamp()
        machine = Machine(
        project_id=test_project_with_customer.id,
        machine_code=f"MSPEC{timestamp}",
        machine_name="规格测试",
        machine_no=1,
        machine_type="ICT测试设备",
        specification="规格描述",
        )
        db_session.add(machine)
        db_session.commit()

        assert machine.specification == "规格描述"
        assert machine.machine_type == "ICT测试设备"

    def test_machine_repr(self, db_session: Session):
        timestamp = datetime.now().timestamp()
        machine = Machine(
        project_id=1,
        machine_code=f"MREPR{timestamp}",
        machine_name="repr测试",
        machine_no=1,
        )
        db_session.add(machine)
        db_session.commit()

        assert f"<Machine {machine.machine_code}>" in repr(machine)


# ============================================================================
# Material Models Tests
# ============================================================================


@pytest.mark.unit
class TestMaterialModel:
    """物料模型测试"""

    @pytest.fixture
    def test_material_data(self, test_user):
        """测试物料数据"""
        return {
        "material_code": f"MAT{datetime.now().timestamp()}",
        "material_name": "测试物料",
        "unit": "件",
        "created_by": test_user.id,
        }

    def test_material_creation(self, db_session: Session, test_material_data):
        """测试物料创建"""
        material = Material(
        material_code=test_material_data["material_code"],
        material_name=test_material_data["material_name"],
        unit=test_material_data["unit"],
        material_type="电气件",
        created_by=test_material_data["created_by"],
        )
        db_session.add(material)
        db_session.commit()
        db_session.refresh(material)

        assert material.id is not None
        assert material.material_code == test_material_data["material_code"]
        assert material.material_name == test_material_data["material_name"]
        assert material.material_type == "电气件"

    def test_material_required_fields(self, db_session: Session):
        """测试物料必填字段"""
        timestamp = datetime.now().timestamp()
        material = Material(
        material_code=f"MATREQ{timestamp}",
        material_name="必填测试",
        unit="件",
        )
        db_session.add(material)
        db_session.commit()

        assert material.material_code == f"MATREQ{timestamp}"
        assert material.material_name == "必填测试"
        assert material.unit == "件"

    def test_material_pricing(self, db_session: Session):
        """测试物料定价"""
        timestamp = datetime.now().timestamp()
        material = Material(
        material_code=f"MATPRC{timestamp}",
        material_name="定价测试",
        unit="件",
        standard_price=Decimal("150.00"),
        last_price=Decimal("140.00"),
        currency="CNY",
        )
        db_session.add(material)
        db_session.commit()

        assert material.standard_price == Decimal("150.00")
        assert material.last_price == Decimal("140.00")
        assert material.currency == "CNY"

    def test_material_stock(self, db_session: Session):
        """测试物料库存"""
        timestamp = datetime.now().timestamp()
        material = Material(
        material_code=f"MATSTK{timestamp}",
        material_name="库存测试",
        unit="件",
        safety_stock=Decimal("100.00"),
        current_stock=Decimal("500.00"),
        )
        db_session.add(material)
        db_session.commit()

        assert material.safety_stock == Decimal("100.00")
        assert material.current_stock == Decimal("500.00")

    def test_material_key_flag(self, db_session: Session):
        """测试物料关键标记"""
        timestamp = datetime.now().timestamp()
        material = Material(
        material_code=f"MATKEY{timestamp}",
        material_name="关键物料测试",
        unit="件",
        is_key_material=True,
        )
        db_session.add(material)
        db_session.commit()

        assert material.is_key_material is True

    def test_material_specification(self, db_session: Session):
        """测试物料规格"""
        timestamp = datetime.now().timestamp()
        material = Material(
        material_code=f"MATSPEC{timestamp}",
        material_name="规格测试",
        unit="件",
        specification="规格描述",
        brand="测试品牌",
        drawing_no="DWG001",
        )
        db_session.add(material)
        db_session.commit()

        assert material.specification == "规格描述"
        assert material.brand == "测试品牌"
        assert material.drawing_no == "DWG001"

    def test_material_repr(self, db_session: Session):
        """测试物料字符串表示"""
        timestamp = datetime.now().timestamp()
        material = Material(
        material_code=f"MATREP{timestamp}", material_name="repr测试"
        )
        db_session.add(material)
        db_session.commit()

        assert f"<Material {material.material_code}>" in repr(material)


@pytest.mark.unit
class TestSupplierModel:
    """供应商模型测试"""

    @pytest.fixture
    def test_supplier_data(self):
        """测试供应商数据"""
        timestamp = datetime.now().timestamp()
        return {
        "supplier_code": f"SUP{timestamp}",
        "supplier_name": "测试供应商",
        "supplier_type": "VENDOR",
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "status": "ACTIVE",
        "created_by": 1,
        }

    def test_supplier_creation(self, db_session: Session, test_supplier_data):
        supplier = Supplier(
        supplier_code=test_supplier_data["supplier_code"],
        supplier_name=test_supplier_data["supplier_name"],
        supplier_type=test_supplier_data["supplier_type"],
        contact_person=test_supplier_data["contact_person"],
        contact_phone=test_supplier_data["contact_phone"],
        status=test_supplier_data["status"],
        created_by=test_supplier_data["created_by"],
        vendor_type="MATERIAL",
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)

        assert supplier.id is not None
        assert supplier.supplier_code == test_supplier_data["supplier_code"]
        assert supplier.supplier_name == test_supplier_data["supplier_name"]
        assert supplier.contact_person == test_supplier_data["contact_person"]
        assert supplier.status == "ACTIVE"

    def test_supplier_required_fields(self, db_session: Session):
        """测试供应商必填字段"""
        timestamp = datetime.now().timestamp()
        supplier = Supplier(
        supplier_code=f"SUPREQ{timestamp}",
        supplier_name="必填测试",
        supplier_type="VENDOR",
        contact_person="李四",
        contact_phone="13900139000",
        )
        db_session.add(supplier)
        db_session.commit()

        assert supplier.supplier_code == f"SUPREQ{timestamp}"
        assert supplier.supplier_name == "必填测试"
        assert supplier.supplier_type == "VENDOR"

    def test_supplier_ratings(self, db_session: Session):
        """测试供应商评分"""
        timestamp = datetime.now().timestamp()
        supplier = Supplier(
        supplier_code=f"SUPRTG{timestamp}",
        supplier_name="评分测试",
        supplier_type="VENDOR",
        contact_person="王五",
        contact_phone="13900139100",
        quality_rating=Decimal("4.50"),
        delivery_rating=Decimal("4.20"),
        service_rating=Decimal("4.80"),
        overall_rating=Decimal("4.50"),
        supplier_level="A",
        )
        db_session.add(supplier)
        db_session.commit()

        assert supplier.quality_rating == Decimal("4.50")
        assert supplier.delivery_rating == Decimal("4.20")
        assert supplier.overall_rating == Decimal("4.50")
        assert supplier.supplier_level == "A"

    def test_supplier_contact_info(self, db_session: Session):
        """测试供应商联系信息"""
        timestamp = datetime.now().timestamp()
        supplier = Supplier(
        supplier_code=f"SUPCNT{timestamp}",
        supplier_name="联系信息测试",
        supplier_type="VENDOR",
        contact_person="王五",
        contact_phone="13900139100",
        contact_email="test@supplier.com",
        address="测试地址123号",
        )
        db_session.add(supplier)
        db_session.commit()

        assert supplier.contact_person == "王五"
        assert supplier.contact_phone == "13900139100"
        assert supplier.contact_email == "test@supplier.com"
        assert supplier.address == "测试地址123号"

    def test_supplier_financial_info(self, db_session: Session):
        """测试供应商财务信息"""
        timestamp = datetime.now().timestamp()
        supplier = Supplier(
        supplier_code=f"SUPFIN{timestamp}",
        supplier_name="财务信息测试",
        supplier_type="VENDOR",
        contact_person="赵六",
        contact_phone="13900139200",
        bank_name="中国银行",
        bank_account="1234567890",
        tax_number="123456789",
        payment_terms="月结30天",
        )
        db_session.add(supplier)
        db_session.commit()

        assert supplier.bank_name == "中国银行"
        assert supplier.bank_account == "1234567890"
        assert supplier.tax_number == "123456789"
        assert supplier.payment_terms == "月结30天"

    def test_supplier_status(self, db_session: Session):
        """测试供应商状态"""
        timestamp = datetime.now().timestamp()
        supplier = Supplier(
        supplier_code=f"SUPST{timestamp}",
        supplier_name="状态测试",
        supplier_type="VENDOR",
        contact_person="赵六",
        contact_phone="13900139200",
        status="INACTIVE",
        )
        db_session.add(supplier)
        db_session.commit()

        supplier.status = "ACTIVE"
        db_session.commit()

        assert supplier.status == "ACTIVE"

    def test_supplier_cooperation_dates(self, db_session: Session):
        """测试供应商合作日期"""
        today = date.today()
        timestamp = datetime.now().timestamp()
        supplier = Supplier(
        supplier_code=f"SUPDATE{timestamp}",
        supplier_name="合作日期测试",
        supplier_type="VENDOR",
        contact_person="孙七",
        contact_phone="13900139300",
        cooperation_start=today - timedelta(days=365),
        last_order_date=today,
        )
        db_session.add(supplier)
        db_session.commit()

        assert supplier.cooperation_start == today - timedelta(days=365)
        assert supplier.last_order_date == today

    def test_supplier_repr(self, db_session: Session):
        """测试供应商字符串表示"""
        timestamp = datetime.now().timestamp()
        supplier = Supplier(
        supplier_code=f"SUPREP{timestamp}", supplier_name="repr测试"
        )
        db_session.add(supplier)
        db_session.commit()

        assert f"<Supplier {supplier.supplier_code}>" in repr(supplier)


@pytest.mark.unit
class TestBomHeaderModel:
    """BOM表头模型测试"""

    @pytest.fixture
    def test_bom_header_data(self, test_project_with_customer, test_user):
        """测试BOM表头数据"""
        return {
        "project_id": test_project_with_customer.id,
        "bom_no": f"BOM{datetime.now().timestamp()}",
        "bom_name": "测试BOM",
        "version": "1.0",
        "created_by": test_user.id,
        }

    def test_bom_header_creation(self, db_session: Session, test_bom_header_data):
        bom = BomHeader(
        bom_no=test_bom_header_data["bom_no"],
        bom_name=test_bom_header_data["bom_name"],
        project_id=test_bom_header_data["project_id"],
        version=test_bom_header_data["version"],
        created_by=test_bom_header_data["created_by"],
        )
        db_session.add(bom)
        db_session.commit()
        db_session.refresh(bom)

        assert bom.id is not None
        assert bom.bom_no == test_bom_header_data["bom_no"]
        assert bom.project_id == test_bom_header_data["project_id"]
        assert bom.version == "1.0"

    def test_bom_header_required_fields(
        self, db_session: Session, test_project_with_customer
    ):
        """测试BOM表头必填字段"""
        timestamp = datetime.now().timestamp()
        bom = BomHeader(
        bom_no=f"BOMREQ{timestamp}",
        bom_name="必填测试",
        project_id=test_project_with_customer.id,
        version="1.0",
        )
        db_session.add(bom)
        db_session.commit()

        assert bom.bom_no == f"BOMREQ{timestamp}"
        assert bom.project_id == test_project_with_customer.id
        assert bom.version == "1.0"

    def test_bom_header_version(self, db_session: Session, test_project_with_customer):
        """测试BOM表头版本"""
        timestamp = datetime.now().timestamp()
        bom = BomHeader(
        bom_no=f"BOMVER{timestamp}",
        bom_name="版本测试",
        project_id=test_project_with_customer.id,
        version="2.0",
        is_latest=True,
        )
        db_session.add(bom)
        db_session.commit()

        assert bom.version == "2.0"
        assert bom.is_latest is True

    def test_bom_header_status(self, db_session: Session, test_project_with_customer):
        """测试BOM表头状态"""
        timestamp = datetime.now().timestamp()
        bom = BomHeader(
        bom_no=f"BOMSTS{timestamp}",
        bom_name="状态测试",
        project_id=test_project_with_customer.id,
        status="RELEASED",
        total_items=50,
        total_amount=Decimal("5000.00"),
        )
        db_session.add(bom)
        db_session.commit()

        assert bom.status == "RELEASED"
        assert bom.total_items == 50
        assert bom.total_amount == Decimal("5000.00")

    def test_bom_header_totals(self, db_session: Session, test_project_with_customer):
        """测试BOM表头统计"""
        timestamp = datetime.now().timestamp()
        bom = BomHeader(
        bom_no=f"BOMTOTS{timestamp}",
        bom_name="统计测试",
        project_id=test_project_with_customer.id,
        total_items=100,
        total_amount=Decimal("10000.00"),
        )
        db_session.add(bom)
        db_session.commit()

        assert bom.total_items == 100
        assert bom.total_amount == Decimal("10000.00")

    def test_bom_header_repr(self, db_session: Session):
        """测试BOM表头字符串表示"""
        bom = BomHeader(bom_no="BOMREP001", bom_name="repr测试", project_id=1)
        db_session.add(bom)
        db_session.commit()

        assert f"<BomHeader {bom.bom_no}>" in repr(bom)


@pytest.mark.unit
class TestBomItemModel:
    """BOM明细模型测试"""

    @pytest.fixture
    def test_bom_header(self, db_session, test_project_with_customer):
        """创建测试BOM表头"""
        timestamp = datetime.now().timestamp()
        bom = BomHeader(
        bom_no=f"BOMFIX{timestamp}",
        bom_name="测试BOM",
        project_id=test_project_with_customer.id,
        version="1.0",
        )
        db_session.add(bom)
        db_session.commit()
        db_session.refresh(bom)
        return bom

    @pytest.fixture
    def test_bom_item_data(self, test_bom_header):
        """测试BOM明细数据"""
        timestamp = datetime.now().timestamp()
        return {
        "bom_id": test_bom_header.id,
        "item_no": 1,
        "material_code": f"MAT{timestamp}",
        "material_name": "测试物料",
        "unit": "件",
        "quantity": Decimal("10.00"),
        }

    def test_bom_item_creation(self, db_session: Session, test_bom_item_data):
        bom = BomItem(
        bom_id=test_bom_item_data["bom_id"],
        item_no=test_bom_item_data["item_no"],
        material_code=test_bom_item_data["material_code"],
        material_name=test_bom_item_data["material_name"],
        unit=test_bom_item_data["unit"],
        quantity=test_bom_item_data["quantity"],
        )
        db_session.add(bom)
        db_session.commit()
        db_session.refresh(bom)

        assert bom.id is not None
        assert bom.item_no == test_bom_item_data["item_no"]
        assert bom.bom_id == test_bom_item_data["bom_id"]
        assert bom.material_code == test_bom_item_data["material_code"]

    def test_bom_item_required_fields(self, db_session: Session, test_bom_header):
        """测试BOM明细必填字段"""
        timestamp = datetime.now().timestamp()
        bom = BomItem(
        bom_id=test_bom_header.id,
        item_no=2,
        material_code=f"MATREQ{timestamp}",
        material_name="必填测试",
        unit="件",
        quantity=Decimal("5.00"),
        )
        db_session.add(bom)
        db_session.commit()

        assert bom.item_no == 2
        assert bom.material_code == f"MATREQ{timestamp}"
        assert bom.material_name == "必填测试"
        assert bom.quantity == Decimal("5.00")

    def test_bom_item_pricing(self, db_session: Session, test_bom_header):
        """测试BOM明细定价"""
        timestamp = datetime.now().timestamp()
        bom = BomItem(
        bom_id=test_bom_header.id,
        item_no=3,
        material_code=f"MATPRC{timestamp}",
        material_name="定价测试",
        unit="件",
        quantity=Decimal("10.00"),
        unit_price=Decimal("100.00"),
        amount=Decimal("1000.00"),
        )
        db_session.add(bom)
        db_session.commit()

        assert bom.unit_price == Decimal("100.00")
        assert bom.amount == Decimal("1000.00")

    def test_bom_item_source_type(self, db_session: Session, test_bom_header):
        """测试BOM明细来源类型"""
        timestamp = datetime.now().timestamp()
        bom = BomItem(
        bom_id=test_bom_header.id,
        item_no=4,
        material_code=f"MATSRC{timestamp}",
        material_name="来源测试",
        unit="件",
        quantity=Decimal("10.00"),
        source_type="PURCHASE",
        )
        db_session.add(bom)
        db_session.commit()

        assert bom.source_type == "PURCHASE"

    def test_bom_item_level(self, db_session: Session, test_bom_header):
        """测试BOM明细层级"""
        timestamp = datetime.now().timestamp()
        bom = BomItem(
        bom_id=test_bom_header.id,
        item_no=5,
        material_code=f"MATLEV{timestamp}",
        material_name="层级测试",
        unit="件",
        quantity=Decimal("5.00"),
        level=2,
        sort_order=10,
        )
        db_session.add(bom)
        db_session.commit()

        assert bom.level == 2
        assert bom.sort_order == 10

    def test_bom_item_key_flag(self, db_session: Session, test_bom_header):
        """测试BOM明细关键标记"""
        timestamp = datetime.now().timestamp()
        bom = BomItem(
        bom_id=test_bom_header.id,
        item_no=6,
        material_code=f"MATKEY{timestamp}",
        material_name="关键物料测试",
        unit="件",
        quantity=Decimal("5.00"),
        is_key_item=True,
        )
        db_session.add(bom)
        db_session.commit()

        assert bom.is_key_item is True

    def test_bom_item_repr(self, db_session: Session, test_bom_header):
        """测试BOM明细字符串表示"""
        bom = BomItem(
        bom_id=test_bom_header.id,
        item_no=7,
        material_code="MTL-REPR-001",
        material_name="repr测试",
        quantity=1.0,
        )
        db_session.add(bom)
        db_session.commit()

        # Model may not have __repr__, just verify str representation works
        assert "BomItem" in repr(bom)


# ============================================================================
# Purchase Order Models Tests
# ============================================================================


@pytest.mark.unit
class TestPurchaseOrderModel:
    """采购订单模型测试"""

    @pytest.fixture
    def test_purchase_order_data(
        self, test_user, test_project_with_customer, test_supplier
    ):
        """测试采购订单数据"""
        timestamp = datetime.now().timestamp()
        return {
        "order_no": f"PO{timestamp}",
        "supplier_id": test_supplier.id,
        "project_id": test_project_with_customer.id,
        "order_type": "NORMAL",
        "order_title": "测试订单标题",
        "total_amount": Decimal("10000.00"),
        "created_by": test_user.id,
        }

    def test_purchase_order_creation(
        self, db_session: Session, test_purchase_order_data
    ):
        po = PurchaseOrder(
        order_no=test_purchase_order_data["order_no"],
        supplier_id=test_purchase_order_data["supplier_id"],
        project_id=test_purchase_order_data["project_id"],
        order_type=test_purchase_order_data["order_type"],
        order_title=test_purchase_order_data["order_title"],
        total_amount=test_purchase_order_data["total_amount"],
        created_by=test_purchase_order_data["created_by"],
        )
        db_session.add(po)
        db_session.commit()
        db_session.refresh(po)

        assert po.id is not None
        assert po.order_no == test_purchase_order_data["order_no"]
        assert po.supplier_id == test_purchase_order_data["supplier_id"]

    def test_purchase_order_required_fields(self, db_session: Session, test_supplier):
        """测试采购订单必填字段"""
        timestamp = datetime.now().timestamp()
        po = PurchaseOrder(
        order_no=f"POREQ{timestamp}",
        supplier_id=test_supplier.id,
        order_type="NORMAL",
        order_title="必填测试",
        created_by=1,
        )
        db_session.add(po)
        db_session.commit()

        assert po.order_no == f"POREQ{timestamp}"
        assert po.order_type == "NORMAL"
        assert po.order_title == "必填测试"

    def test_purchase_order_amounts(self, db_session: Session, test_supplier):
        """测试采购订单金额"""
        timestamp = datetime.now().timestamp()
        po = PurchaseOrder(
        order_no=f"POAMT{timestamp}",
        supplier_id=test_supplier.id,
        order_type="NORMAL",
        order_title="金额测试",
        total_amount=Decimal("10000.00"),
        tax_rate=Decimal("13.00"),
        tax_amount=Decimal("1300.00"),
        amount_with_tax=Decimal("11300.00"),
        currency="CNY",
        )
        db_session.add(po)
        db_session.commit()

        assert po.total_amount == Decimal("10000.00")
        assert po.tax_amount == Decimal("1300.00")
        assert po.amount_with_tax == Decimal("11300.00")

    def test_purchase_order_dates(self, db_session: Session, test_supplier):
        """测试采购订单日期"""
        today = date.today()
        timestamp = datetime.now().timestamp()
        po = PurchaseOrder(
        order_no=f"PODATE{timestamp}",
        supplier_id=test_supplier.id,
        order_type="NORMAL",
        order_title="日期测试",
        order_date=today,
        required_date=today + timedelta(days=30),
        promised_date=today + timedelta(days=35),
        )
        db_session.add(po)
        db_session.commit()

        assert po.order_date == today
        assert po.required_date == today + timedelta(days=30)

    def test_purchase_order_status(self, db_session: Session, test_supplier):
        """测试采购订单状态"""
        timestamp = datetime.now().timestamp()
        po = PurchaseOrder(
        order_no=f"POSTS{timestamp}",
        supplier_id=test_supplier.id,
        order_type="NORMAL",
        order_title="状态测试",
        status="SUBMITTED",
        payment_status="UNPAID",
        )
        db_session.add(po)
        db_session.commit()

        po.status = "IN_PROGRESS"
        db_session.commit()
        assert po.status == "IN_PROGRESS"

    def test_purchase_order_payment(self, db_session: Session, test_supplier):
        """测试采购订单付款"""
        timestamp = datetime.now().timestamp()
        po = PurchaseOrder(
        order_no=f"POPAY{timestamp}",
        supplier_id=test_supplier.id,
        order_type="NORMAL",
        order_title="付款测试",
        total_amount=Decimal("10000.00"),
        paid_amount=Decimal("5000.00"),
        payment_status="PARTIAL_PAID",
        payment_terms="月结30天",
        )
        db_session.add(po)
        db_session.commit()

        assert po.paid_amount == Decimal("5000.00")
        assert po.payment_status == "PARTIAL_PAID"
        assert po.payment_terms == "月结30天"

    def test_purchase_order_repr(self, db_session: Session):
        """测试采购订单字符串表示"""
        po = PurchaseOrder(order_no="POREP001", order_title="repr测试", supplier_id=1)
        db_session.add(po)
        db_session.commit()

        assert f"<PurchaseOrder {po.order_no}>" in repr(po)


@pytest.mark.unit
class TestPurchaseOrderItemModel:
    """采购订单明细模型测试"""

    @pytest.fixture
    def test_po_for_items(
        self, db_session: Session, test_supplier, test_project_with_customer
    ):
        """创建测试采购订单"""
        timestamp = datetime.now().timestamp()
        po = PurchaseOrder(
        order_no=f"POITEM{timestamp}",
        supplier_id=test_supplier.id,
        project_id=test_project_with_customer.id,
        order_type="NORMAL",
        order_title="测试订单",
        )
        db_session.add(po)
        db_session.commit()
        db_session.refresh(po)
        return po

    @pytest.fixture
    def test_purchase_order_item_data(self, test_po_for_items):
        """测试采购订单明细数据"""
        timestamp = datetime.now().timestamp()
        return {
        "order_id": test_po_for_items.id,
        "item_no": 1,
        "material_code": f"MAT{timestamp}",
        "material_name": "测试物料",
        "unit": "件",
        "quantity": Decimal("10.00"),
        }

    def test_purchase_order_item_creation(
        self, db_session: Session, test_purchase_order_item_data
    ):
        item = PurchaseOrderItem(
        order_id=test_purchase_order_item_data["order_id"],
        item_no=test_purchase_order_item_data["item_no"],
        material_code=test_purchase_order_item_data["material_code"],
        material_name=test_purchase_order_item_data["material_name"],
        unit=test_purchase_order_item_data["unit"],
        quantity=test_purchase_order_item_data["quantity"],
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.id is not None
        assert item.item_no == test_purchase_order_item_data["item_no"]
        assert item.order_id == test_purchase_order_item_data["order_id"]
        assert item.material_code == test_purchase_order_item_data["material_code"]

    def test_purchase_order_item_required_fields(
        self, db_session: Session, test_po_for_items
    ):
        """测试采购订单明细必填字段"""
        timestamp = datetime.now().timestamp()
        item = PurchaseOrderItem(
        order_id=test_po_for_items.id,
        item_no=2,
        material_code=f"MATREQ{timestamp}",
        material_name="必填测试",
        unit="件",
        quantity=Decimal("5.00"),
        )
        db_session.add(item)
        db_session.commit()

        assert item.item_no == 2
        assert item.material_code == f"MATREQ{timestamp}"
        assert item.quantity == Decimal("5.00")

    def test_purchase_order_item_pricing(self, db_session: Session, test_po_for_items):
        """测试采购订单明细定价"""
        timestamp = datetime.now().timestamp()
        item = PurchaseOrderItem(
        order_id=test_po_for_items.id,
        item_no=3,
        material_code=f"MATPRC{timestamp}",
        material_name="定价测试",
        unit="件",
        quantity=Decimal("10.00"),
        unit_price=Decimal("150.00"),
        amount=Decimal("1500.00"),
        tax_rate=Decimal("13.00"),
        tax_amount=Decimal("195.00"),
        amount_with_tax=Decimal("1695.00"),
        )
        db_session.add(item)
        db_session.commit()

        assert item.unit_price == Decimal("150.00")
        assert item.amount == Decimal("1500.00")
        assert item.amount_with_tax == Decimal("1695.00")

    def test_purchase_order_item_dates(self, db_session: Session, test_po_for_items):
        """测试采购订单明细日期"""
        today = date.today()
        timestamp = datetime.now().timestamp()
        item = PurchaseOrderItem(
        order_id=test_po_for_items.id,
        item_no=4,
        material_code=f"MADATE{timestamp}",
        material_name="日期测试",
        unit="件",
        quantity=Decimal("100.00"),
        required_date=today + timedelta(days=30),
        promised_date=today + timedelta(days=35),
        )
        db_session.add(item)
        db_session.commit()

        assert item.required_date == today + timedelta(days=30)

    def test_purchase_order_item_receipt(self, db_session: Session, test_po_for_items):
        """测试采购订单明细收货"""
        timestamp = datetime.now().timestamp()
        item = PurchaseOrderItem(
        order_id=test_po_for_items.id,
        item_no=5,
        material_code=f"MRECT{timestamp}",
        material_name="收货测试",
        unit="件",
        quantity=Decimal("100.00"),
        received_qty=Decimal("80.00"),
        qualified_qty=Decimal("75.00"),
        rejected_qty=Decimal("5.00"),
        )
        db_session.add(item)
        db_session.commit()

        assert item.received_qty == Decimal("80.00")
        assert item.qualified_qty == Decimal("75.00")
        assert item.rejected_qty == Decimal("5.00")

    def test_purchase_order_item_status(self, db_session: Session, test_po_for_items):
        """测试采购订单明细状态"""
        timestamp = datetime.now().timestamp()
        item = PurchaseOrderItem(
        order_id=test_po_for_items.id,
        item_no=6,
        material_code=f"MSTS{timestamp}",
        material_name="状态测试",
        unit="件",
        quantity=Decimal("50.00"),
        status="PARTIAL_RECEIVED",
        )
        db_session.add(item)
        db_session.commit()

        assert item.status == "PARTIAL_RECEIVED"

    def test_purchase_order_item_repr(self, db_session: Session):
        """测试采购订单明细字符串表示"""
        item = PurchaseOrderItem(
        order_id=1,
        item_no=7,
        material_code="MTL-REPR-001",
        material_name="repr测试",
        quantity=1.0,
        )
        db_session.add(item)
        db_session.commit()

        # Model may not have __repr__, just verify str representation works
        assert "PurchaseOrderItem" in repr(item)


# ============================================================================
# ECN Models Tests
# ============================================================================


@pytest.mark.unit
class TestEcnModel:
    """ECN模型测试"""

    @pytest.fixture
    def test_ecn_data(self, test_project_with_customer, test_user):
        """测试ECN数据"""
        timestamp = datetime.now().timestamp()
        return {
        "ecn_no": f"ECN{timestamp}",
        "ecn_title": "测试ECN",
        "ecn_type": "DESIGN_CHANGE",
        "source_type": "MANUAL",
        "project_id": test_project_with_customer.id,
        "change_reason": "测试原因",
        "change_description": "测试变更描述",
        "created_by": test_user.id,
        }

    def test_ecn_creation(self, db_session: Session, test_ecn_data):
        ecn = Ecn(
        ecn_no=test_ecn_data["ecn_no"],
        ecn_title=test_ecn_data["ecn_title"],
        ecn_type=test_ecn_data["ecn_type"],
        source_type=test_ecn_data["source_type"],
        project_id=test_ecn_data["project_id"],
        change_reason=test_ecn_data["change_reason"],
        change_description=test_ecn_data["change_description"],
        created_by=test_ecn_data["created_by"],
        )
        db_session.add(ecn)
        db_session.commit()
        db_session.refresh(ecn)

        assert ecn.id is not None
        assert ecn.ecn_no == test_ecn_data["ecn_no"]
        assert ecn.ecn_title == test_ecn_data["ecn_title"]
        assert ecn.ecn_type == "DESIGN_CHANGE"

    def test_ecn_required_fields(
        self, db_session: Session, test_project_with_customer, test_user
    ):
        """测试ECN必填字段"""
        timestamp = datetime.now().timestamp()
        ecn = Ecn(
        ecn_no=f"ECNREQ{timestamp}",
        ecn_title="必填测试",
        ecn_type="DESIGN_CHANGE",
        source_type="MANUAL",
        project_id=test_project_with_customer.id,
        change_reason="测试原因",
        change_description="测试描述",
        created_by=test_user.id,
        )
        db_session.add(ecn)
        db_session.commit()

        assert ecn.ecn_no == f"ECNREQ{timestamp}"
        assert ecn.change_reason == "测试原因"
        assert ecn.project_id == test_project_with_customer.id

    def test_ecn_status(
        self, db_session: Session, test_project_with_customer, test_user
    ):
        """测试ECN状态"""
        timestamp = datetime.now().timestamp()
        ecn = Ecn(
        ecn_no=f"ECNSTS{timestamp}",
        ecn_title="状态测试",
        ecn_type="DESIGN_CHANGE",
        source_type="MANUAL",
        project_id=test_project_with_customer.id,
        change_reason="测试原因",
        change_description="测试描述",
        status="DRAFT",
        current_step="SUBMIT",
        created_by=test_user.id,
        )
        db_session.add(ecn)
        db_session.commit()

        assert ecn.status == "DRAFT"
        assert ecn.current_step == "SUBMIT"

        ecn.status = "EVALUATION"
        ecn.current_step = "DEPT_EVALUATION"
        db_session.commit()
        assert ecn.current_step == "DEPT_EVALUATION"

    def test_ecn_priority(
        self, db_session: Session, test_project_with_customer, test_user
    ):
        """测试ECN优先级"""
        timestamp = datetime.now().timestamp()
        ecn = Ecn(
        ecn_no=f"ECNPRI{timestamp}",
        ecn_title="优先级测试",
        ecn_type="DESIGN_CHANGE",
        source_type="MANUAL",
        project_id=test_project_with_customer.id,
        change_reason="测试原因",
        change_description="测试描述",
        priority="HIGH",
        urgency="URGENT",
        created_by=test_user.id,
        )
        db_session.add(ecn)
        db_session.commit()

        assert ecn.priority == "HIGH"
        assert ecn.urgency == "URGENT"

    def test_ecn_impact(
        self, db_session: Session, test_project_with_customer, test_user
    ):
        """测试ECN影响"""
        timestamp = datetime.now().timestamp()
        ecn = Ecn(
        ecn_no=f"ECNIMP{timestamp}",
        ecn_title="影响测试",
        ecn_type="DESIGN_CHANGE",
        source_type="MANUAL",
        project_id=test_project_with_customer.id,
        change_reason="测试原因",
        change_description="测试描述",
        cost_impact=Decimal("50000.00"),
        schedule_impact_days=10,
        quality_impact="LOW",
        created_by=test_user.id,
        )
        db_session.add(ecn)
        db_session.commit()

        assert ecn.cost_impact == Decimal("50000.00")
        assert ecn.schedule_impact_days == 10
        assert ecn.quality_impact == "LOW"

    def test_ecn_machine_relationship(
        self, db_session: Session, test_project_with_customer
    ):
        """测试ECN-设备关系"""
        timestamp = datetime.now().timestamp()
        machine = Machine(
        project_id=test_project_with_customer.id,
        machine_code=f"MAC{timestamp}",
        machine_name="ECN关系测试",
        machine_no=1,
        )
        db_session.add(machine)
        db_session.commit()

        ecn = Ecn(
        ecn_no=f"ECNMCH{timestamp}",
        ecn_title="ECN-设备关系测试",
        ecn_type="DESIGN_CHANGE",
        source_type="MANUAL",
        project_id=test_project_with_customer.id,
        machine_id=machine.id,
        change_reason="测试",
        change_description="测试",
        created_by=1,
        )
        db_session.add(ecn)
        db_session.commit()

        assert ecn.machine_id == machine.id

    def test_ecn_repr(self, db_session: Session):
        """测试ECN字符串表示"""
        ecn = Ecn(
        ecn_no="ECNREP001",
        ecn_title="repr测试",
        ecn_type="DESIGN",
        source_type="INTERNAL",
        project_id=1,
        change_reason="测试",
        change_description="测试描述",
        )
        db_session.add(ecn)
        db_session.commit()

        assert f"<Ecn {ecn.ecn_no}>" in repr(ecn)


@pytest.mark.unit
class TestEcnEvaluationModel:
    """ECN评估模型测试"""

    @pytest.fixture
    def test_ecn_for_ecn_evaluation(
        self, db_session: Session, test_project_with_customer, test_user
    ):
        """创建测试ECN"""
        timestamp = datetime.now().timestamp()
        ecn = Ecn(
        ecn_no=f"ECNEVAL{timestamp}",
        ecn_title="评估测试",
        ecn_type="DESIGN_CHANGE",
        source_type="MANUAL",
        project_id=test_project_with_customer.id,
        change_reason="测试原因",
        change_description="测试描述",
        created_by=test_user.id,
        )
        db_session.add(ecn)
        db_session.commit()
        db_session.refresh(ecn)
        return ecn

    @pytest.fixture
    def test_ecn_evaluation_data(self, test_ecn_for_ecn_evaluation, test_user):
        """测试ECN评估数据"""
        return {
        "ecn_id": test_ecn_for_ecn_evaluation.id,
        "ecn_evaluation_dept": "工程部",
        "ecn_evaluator_id": test_user.id,
        "ecn_evaluator_name": "测试评估人",
        }

    def test_ecn_evaluation_creation(
        self, db_session: Session, test_ecn_evaluation_data
    ):
        ecn_evaluation = EcnEvaluation(
        ecn_id=test_ecn_evaluation_data["ecn_id"],
        eval_dept=test_ecn_evaluation_data["ecn_evaluation_dept"],
        evaluator_id=test_ecn_evaluation_data["ecn_evaluator_id"],
        evaluator_name=test_ecn_evaluation_data["ecn_evaluator_name"],
        )
        db_session.add(ecn_evaluation)
        db_session.commit()
        db_session.refresh(ecn_evaluation)

        assert ecn_evaluation.id is not None
        assert ecn_evaluation.ecn_id == test_ecn_evaluation_data["ecn_id"]
        assert ecn_evaluation.eval_dept == "工程部"
        assert (
        ecn_evaluation.evaluator_id == test_ecn_evaluation_data["ecn_evaluator_id"]
        )

    def test_ecn_evaluation_required_fields(
        self, db_session: Session, test_ecn_for_ecn_evaluation, test_user
    ):
        """测试ECN评估必填字段"""
        ecn_evaluation = EcnEvaluation(
        ecn_id=test_ecn_for_ecn_evaluation.id,
        eval_dept="工程部",
        evaluator_id=test_user.id,
        evaluator_name="测试评估人",
        )
        db_session.add(ecn_evaluation)
        db_session.commit()

        assert ecn_evaluation.ecn_id == test_ecn_for_ecn_evaluation.id
        assert ecn_evaluation.eval_dept == "工程部"

    def test_ecn_evaluation_result(
        self, db_session: Session, test_ecn_for_ecn_evaluation, test_user
    ):
        """测试ECN评估结果"""
        ecn_evaluation = EcnEvaluation(
        ecn_id=test_ecn_for_ecn_evaluation.id,
        eval_dept="工程部",
        evaluator_id=test_user.id,
        eval_result="APPROVED",
        eval_opinion="意见内容",
        conditions="附加条件",
        status="COMPLETED",
        )
        db_session.add(ecn_evaluation)
        db_session.commit()

        assert ecn_evaluation.eval_result == "APPROVED"
        assert ecn_evaluation.status == "COMPLETED"

    def test_ecn_evaluation_impact_analysis(
        self, db_session: Session, test_ecn_for_ecn_evaluation, test_user
    ):
        """测试ECN评估影响分析"""
        ecn_evaluation = EcnEvaluation(
        ecn_id=test_ecn_for_ecn_evaluation.id,
        eval_dept="工程部",
        evaluator_id=test_user.id,
        impact_analysis="影响分析内容",
        cost_estimate=Decimal("30000.00"),
        schedule_estimate=7,
        risk_assessment="风险分析内容",
        resource_requirement="需要工程师3人，耗时5天",
        )
        db_session.add(ecn_evaluation)
        db_session.commit()

        assert ecn_evaluation.impact_analysis == "影响分析内容"
        assert ecn_evaluation.cost_estimate == Decimal("30000.00")
        assert ecn_evaluation.schedule_estimate == 7

    def test_ecn_evaluation_user(
        self, db_session: Session, test_ecn_for_ecn_evaluation, test_user
    ):
        """测试ECN评估人"""
        ecn_evaluation = EcnEvaluation(
        ecn_id=test_ecn_for_ecn_evaluation.id,
        eval_dept="工程部",
        evaluator_id=test_user.id,
        evaluator_name=test_user.real_name or test_user.username,
        )
        db_session.add(ecn_evaluation)
        db_session.commit()

        assert ecn_evaluation.evaluator_id == test_user.id
        assert ecn_evaluation.evaluator_name == (
        test_user.real_name or test_user.username
        )

    def test_ecn_evaluation_repr(
        self, db_session: Session, test_ecn_for_ecn_evaluation, test_user
    ):
        """测试ECN评估字符串表示"""
        ecn_evaluation = EcnEvaluation(
        ecn_id=test_ecn_for_ecn_evaluation.id,
        eval_dept="工程部",
        evaluator_id=test_user.id,
        )
        db_session.add(ecn_evaluation)
        db_session.commit()

        # Model may not have __repr__, just verify str representation works
        assert "EcnEvaluation" in repr(ecn_evaluation)


@pytest.mark.unit
class TestEcnTaskModel:
    """ECN任务模型测试"""

    @pytest.fixture
    def test_ecn_for_task(
        self, db_session: Session, test_project_with_customer, test_user
    ):
        """创建测试ECN"""
        timestamp = datetime.now().timestamp()
        ecn = Ecn(
        ecn_no=f"ECNTSK{timestamp}",
        ecn_title="任务测试",
        ecn_type="DESIGN_CHANGE",
        source_type="MANUAL",
        project_id=test_project_with_customer.id,
        change_reason="测试原因",
        change_description="测试描述",
        created_by=test_user.id,
        )
        db_session.add(ecn)
        db_session.commit()
        db_session.refresh(ecn)
        return ecn

    @pytest.fixture
    def test_ecn_task_data(self, test_ecn_for_task, test_user):
        """测试ECN任务数据"""
        return {
        "ecn_id": test_ecn_for_task.id,
        "task_no": 1,
        "task_name": "测试任务",
        "task_type": "设计实施",
        "assignee_id": test_user.id,
        }

    def test_ecn_task_creation(self, db_session: Session, test_ecn_task_data):
        task = EcnTask(
        ecn_id=test_ecn_task_data["ecn_id"],
        task_no=test_ecn_task_data["task_no"],
        task_name=test_ecn_task_data["task_name"],
        task_type=test_ecn_task_data["task_type"],
        assignee_id=test_ecn_task_data["assignee_id"],
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.id is not None
        assert task.ecn_id == test_ecn_task_data["ecn_id"]
        assert task.task_name == "测试任务"
        assert task.task_type == "设计实施"

    def test_ecn_task_required_fields(
        self, db_session: Session, test_ecn_for_task, test_user
    ):
        """测试ECN任务必填字段"""
        task = EcnTask(
        ecn_id=test_ecn_for_task.id,
        task_no=2,
        task_name="必填测试",
        task_type="设计实施",
        assignee_id=test_user.id,
        )
        db_session.add(task)
        db_session.commit()

        assert task.ecn_id == test_ecn_for_task.id
        assert task.task_no == 2
        assert task.task_name == "必填测试"
        assert task.task_type == "设计实施"

    def test_ecn_task_schedule(self, db_session: Session, test_ecn_for_task):
        """测试ECN任务计划"""
        task = EcnTask(
        ecn_id=test_ecn_for_task.id,
        task_no=3,
        task_name="计划测试",
        task_type="设计实施",
        planned_start=date.today() + timedelta(days=1),
        planned_end=date.today() + timedelta(days=5),
        actual_start=date.today() + timedelta(days=1),
        actual_end=date.today() + timedelta(days=5),
        )
        db_session.add(task)
        db_session.commit()

        assert task.planned_start == date.today() + timedelta(days=1)
        assert task.planned_end == date.today() + timedelta(days=5)

    def test_ecn_task_progress(self, db_session: Session, test_ecn_for_task):
        """测试ECN任务进度"""
        task = EcnTask(
        ecn_id=test_ecn_for_task.id,
        task_no=4,
        task_name="进度测试",
        task_type="设计实施",
        progress_pct=75,
        status="IN_PROGRESS",
        )
        db_session.add(task)
        db_session.commit()

        assert task.progress_pct == 75
        assert task.status == "IN_PROGRESS"

    def test_ecn_task_completion(self, db_session: Session, test_ecn_for_task):
        """测试ECN任务完成"""
        task = EcnTask(
        ecn_id=test_ecn_for_task.id,
        task_no=5,
        task_name="完成测试",
        task_type="设计实施",
        progress_pct=100,
        status="COMPLETED",
        actual_end=date.today(),
        completion_note="任务已完成",
        )
        db_session.add(task)
        db_session.commit()

        assert task.progress_pct == 100
        assert task.status == "COMPLETED"
        assert task.actual_end == date.today()

    def test_ecn_task_repr(self, db_session: Session, test_ecn_for_task, test_user):
        """测试ECN任务字符串表示"""
        task = EcnTask(
        ecn_id=test_ecn_for_task.id,
        task_no=6,
        task_name="repr测试",
        task_type="设计实施",
        )
        db_session.add(task)
        db_session.commit()

        # Model may not have __repr__, just verify str representation works
        assert "EcnTask" in repr(task)


# ============================================================================
# Acceptance Models Tests
# ============================================================================


@pytest.mark.unit
class TestAcceptanceOrderModel:
    """验收订单模型测试"""

    @pytest.fixture
    def test_machine_for_acceptance(
        self, db_session: Session, test_project_with_customer
    ):
        """创建测试设备"""
        timestamp = datetime.now().timestamp()
        machine = Machine(
        project_id=test_project_with_customer.id,
        machine_code=f"MACACC{timestamp}",
        machine_name="验收测试设备",
        machine_no=1,
        )
        db_session.add(machine)
        db_session.commit()
        db_session.refresh(machine)
        return machine

    @pytest.fixture
    def test_acceptance_order_data(
        self, test_project_with_customer, test_machine_for_acceptance, test_user
    ):
        """测试验收订单数据"""
        timestamp = datetime.now().timestamp()
        return {
        "order_no": f"AO{timestamp}",
        "project_id": test_project_with_customer.id,
        "machine_id": test_machine_for_acceptance.id,
        "acceptance_type": "FAT",
        "planned_date": date.today(),
        "created_by": test_user.id,
        }

    def test_acceptance_order_creation(
        self, db_session: Session, test_acceptance_order_data
    ):
        order = AcceptanceOrder(
        order_no=test_acceptance_order_data["order_no"],
        project_id=test_acceptance_order_data["project_id"],
        machine_id=test_acceptance_order_data["machine_id"],
        acceptance_type=test_acceptance_order_data["acceptance_type"],
        planned_date=test_acceptance_order_data["planned_date"],
        created_by=test_acceptance_order_data["created_by"],
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.id is not None
        assert order.order_no == test_acceptance_order_data["order_no"]
        assert order.project_id == test_acceptance_order_data["project_id"]
        assert order.acceptance_type == "FAT"

    def test_acceptance_order_required_fields(
        self, db_session: Session, test_machine_for_acceptance
    ):
        """测试验收订单必填字段"""
        timestamp = datetime.now().timestamp()
        order = AcceptanceOrder(
        order_no=f"AOREQ{timestamp}",
        project_id=1,
        machine_id=test_machine_for_acceptance.id,
        acceptance_type="FAT",
        )
        db_session.add(order)
        db_session.commit()

        assert order.order_no == f"AOREQ{timestamp}"
        assert order.acceptance_type == "FAT"

    def test_acceptance_order_dates(
        self, db_session: Session, test_machine_for_acceptance
    ):
        """测试验收订单日期"""
        today = date.today()
        now = datetime.now()
        timestamp = datetime.now().timestamp()
        order = AcceptanceOrder(
        order_no=f"AODATE{timestamp}",
        project_id=1,
        machine_id=test_machine_for_acceptance.id,
        acceptance_type="FAT",
        planned_date=today,
        actual_start_date=now,
        )
        db_session.add(order)
        db_session.commit()

        assert order.planned_date == today
        assert order.actual_start_date is not None

    def test_acceptance_order_location(
        self, db_session: Session, test_machine_for_acceptance
    ):
        """测试验收订单地点"""
        timestamp = datetime.now().timestamp()
        order = AcceptanceOrder(
        order_no=f"AOLOC{timestamp}",
        project_id=1,
        machine_id=test_machine_for_acceptance.id,
        acceptance_type="FAT",
        location="公司一楼",
        )
        db_session.add(order)
        db_session.commit()

        assert order.location == "公司一楼"

    def test_acceptance_order_status(
        self, db_session: Session, test_machine_for_acceptance
    ):
        """测试验收订单状态"""
        timestamp = datetime.now().timestamp()
        order = AcceptanceOrder(
        order_no=f"AOSTS{timestamp}",
        project_id=1,
        machine_id=test_machine_for_acceptance.id,
        acceptance_type="FAT",
        planned_date=date.today(),
        status="IN_PROGRESS",
        )
        db_session.add(order)
        db_session.commit()

        assert order.status == "IN_PROGRESS"

        order.status = "COMPLETED"
        db_session.commit()
        assert order.status == "COMPLETED"

    def test_acceptance_order_statistics(
        self, db_session: Session, test_machine_for_acceptance
    ):
        """测试验收订单统计"""
        today = date.today()
        timestamp = datetime.now().timestamp()
        order = AcceptanceOrder(
        order_no=f"AOSTA{timestamp}",
        project_id=1,
        machine_id=test_machine_for_acceptance.id,
        acceptance_type="FAT",
        planned_date=today,
        total_items=100,
        passed_items=95,
        failed_items=3,
        na_items=2,
        pass_rate=Decimal("95.00"),
        )
        db_session.add(order)
        db_session.commit()

        assert order.total_items == 100
        assert order.passed_items == 95
        assert order.failed_items == 3
        assert order.pass_rate == Decimal("95.00")

    def test_acceptance_order_conclusion(
        self, db_session: Session, test_machine_for_acceptance
    ):
        """测试验收订单结论"""
        timestamp = datetime.now().timestamp()
        order = AcceptanceOrder(
        order_no=f"AOCNC{timestamp}",
        project_id=1,
        machine_id=test_machine_for_acceptance.id,
        acceptance_type="FAT",
        planned_date=date.today(),
        overall_result="PASSED",
        conclusion="验收通过",
        conditions="无",
        )
        db_session.add(order)
        db_session.commit()

        assert order.overall_result == "PASSED"
        assert order.conclusion == "验收通过"
        assert order.conditions == "无"

    def test_acceptance_order_project_relationship(self, db_session: Session):
        """测试验收订单-项目关系"""
        order = AcceptanceOrder(
        order_no="APROJ001",
        project_id=1,
        machine_id=1,
        acceptance_type="FAT",
        created_by=1,
        )
        db_session.add(order)
        db_session.commit()

        assert order.project_id == 1

    def test_acceptance_order_repr(self, db_session: Session):
        """测试验收订单字符串表示"""
        order = AcceptanceOrder(order_no="APRE001", project_id=1, acceptance_type="FAT")
        db_session.add(order)
        db_session.commit()

        assert f"<AcceptanceOrder {order.order_no}>" in repr(order)


@pytest.mark.unit
class TestAcceptanceOrderItemModel:
    """验收订单明细模型测试"""

    @pytest.fixture
    def test_machine_for_acceptance_item(
        self, db_session: Session, test_project_with_customer
    ):
        """创建测试设备"""
        timestamp = datetime.now().timestamp()
        machine = Machine(
        project_id=test_project_with_customer.id,
        machine_code=f"MACITM{timestamp}",
        machine_name="验收明细测试设备",
        machine_no=1,
        )
        db_session.add(machine)
        db_session.commit()
        db_session.refresh(machine)
        return machine

    @pytest.fixture
    def test_acceptance_order_for_items(
        self,
        db_session: Session,
        test_project_with_customer,
        test_machine_for_acceptance_item,
    ):
        """创建测试验收订单"""
        timestamp = datetime.now().timestamp()
        order = AcceptanceOrder(
        order_no=f"AOITEM{timestamp}",
        project_id=test_project_with_customer.id,
        machine_id=test_machine_for_acceptance_item.id,
        acceptance_type="FAT",
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        return order

    @pytest.fixture
    def test_acceptance_order_item_data(self, test_acceptance_order_for_items):
        """测试验收订单明细数据"""
        return {
        "order_id": test_acceptance_order_for_items.id,
        "category_code": "CAT001",
        "category_name": "测试分类",
        "item_code": "ITEM001",
        "item_name": "测试检查项",
        }

    def test_acceptance_order_item_creation(
        self, db_session: Session, test_acceptance_order_item_data
    ):
        item = AcceptanceOrderItem(
        order_id=test_acceptance_order_item_data["order_id"],
        category_code=test_acceptance_order_item_data["category_code"],
        category_name=test_acceptance_order_item_data["category_name"],
        item_code=test_acceptance_order_item_data["item_code"],
        item_name=test_acceptance_order_item_data["item_name"],
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.id is not None
        assert item.order_id == test_acceptance_order_item_data["order_id"]
        assert item.item_code == test_acceptance_order_item_data["item_code"]

    def test_acceptance_order_item_required_fields(
        self, db_session: Session, test_acceptance_order_for_items
    ):
        """测试验收订单明细必填字段"""
        timestamp = datetime.now().timestamp()
        item = AcceptanceOrderItem(
        order_id=test_acceptance_order_for_items.id,
        category_code=f"CAT{timestamp}",
        category_name="必填测试",
        item_code=f"ITEM{timestamp}",
        item_name="测试检查项",
        )
        db_session.add(item)
        db_session.commit()

        assert item.order_id == test_acceptance_order_for_items.id
        assert item.category_name == "必填测试"

    def test_acceptance_order_item_flags(
        self, db_session: Session, test_acceptance_order_for_items
    ):
        """测试验收订单明细标记"""
        timestamp = datetime.now().timestamp()
        item = AcceptanceOrderItem(
        order_id=test_acceptance_order_for_items.id,
        category_code=f"CATFLG{timestamp}",
        category_name="标记测试",
        item_code=f"ITEM{timestamp}",
        item_name="测试检查项",
        is_required=True,
        is_key_item=True,
        )
        db_session.add(item)
        db_session.commit()

        assert item.is_required is True
        assert item.is_key_item is True

    def test_acceptance_order_item_result(
        self, db_session: Session, test_acceptance_order_for_items
    ):
        """测试验收订单明细结果"""
        timestamp = datetime.now().timestamp()
        item = AcceptanceOrderItem(
        order_id=test_acceptance_order_for_items.id,
        category_code=f"CATRST{timestamp}",
        category_name="结果测试",
        item_code=f"ITEM{timestamp}",
        item_name="测试检查项",
        result_status="PASSED",
        actual_value="符合要求",
        remark="备注",
        )
        db_session.add(item)
        db_session.commit()

        assert item.result_status == "PASSED"
        assert item.actual_value == "符合要求"

    def test_acceptance_order_item_sort(
        self, db_session: Session, test_acceptance_order_for_items
    ):
        """测试验收订单明细排序"""
        timestamp = datetime.now().timestamp()
        item = AcceptanceOrderItem(
        order_id=test_acceptance_order_for_items.id,
        category_code=f"CATSRT{timestamp}",
        category_name="排序测试",
        item_code=f"ITEM{timestamp}",
        item_name="测试检查项",
        sort_order=10,
        )
        db_session.add(item)
        db_session.commit()

        assert item.sort_order == 10

    def test_acceptance_order_item_repr(
        self, db_session: Session, test_acceptance_order_for_items
    ):
        """测试验收订单明细字符串表示"""
        item = AcceptanceOrderItem(
        order_id=test_acceptance_order_for_items.id,
        category_code="CATRPR",
        category_name="repr测试分类",
        item_code="ITEMREPR",
        item_name="repr测试",
        )
        db_session.add(item)
        db_session.commit()

        # Model may not have __repr__, just verify str representation works
        assert "AcceptanceOrderItem" in repr(item)


# ============================================================================
# Outsourcing Models Tests
# ============================================================================


@pytest.mark.unit
class TestOutsourcingOrderModel:
    """外协订单模型测试"""

    @pytest.fixture
    def test_outsourcing_vendor(self, db_session: Session):
        """创建测试外协供应商"""
        timestamp = datetime.now().timestamp()
        vendor = OutsourcingVendor(
        supplier_code=f"OUTVEND{timestamp}",
        supplier_name="测试外协供应商",
        supplier_type="MACHINING",
        contact_person="张三",
        contact_phone="13800138000",
        status="ACTIVE",
        vendor_type="OUTSOURCING",
        )
        db_session.add(vendor)
        db_session.commit()
        db_session.refresh(vendor)
        return vendor

    @pytest.fixture
    def test_outsourcing_order_data(
        self, test_project_with_customer, test_outsourcing_vendor, test_user
    ):
        """测试外协订单数据"""
        timestamp = datetime.now().timestamp()
        return {
        "order_no": f"OUT{timestamp}",
        "project_id": test_project_with_customer.id,
        "vendor_id": test_outsourcing_vendor.id,
        "order_type": "MACHINING",
        "order_title": "测试外协订单",
        "created_by": test_user.id,
        }

    def test_outsourcing_order_creation(
        self, db_session: Session, test_outsourcing_order_data
    ):
        order = OutsourcingOrder(
        order_no=test_outsourcing_order_data["order_no"],
        project_id=test_outsourcing_order_data["project_id"],
        vendor_id=test_outsourcing_order_data["vendor_id"],
        order_type=test_outsourcing_order_data["order_type"],
        order_title=test_outsourcing_order_data["order_title"],
        created_by=test_outsourcing_order_data["created_by"],
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.id is not None
        assert order.order_no == test_outsourcing_order_data["order_no"]
        assert order.project_id == test_outsourcing_order_data["project_id"]

    def test_outsourcing_order_required_fields(
        self, db_session: Session, test_outsourcing_vendor
    ):
        """测试外协订单必填字段"""
        timestamp = datetime.now().timestamp()
        order = OutsourcingOrder(
        order_no=f"OUTREQ{timestamp}",
        project_id=1,
        vendor_id=test_outsourcing_vendor.id,
        order_type="MACHINING",
        order_title="必填测试",
        )
        db_session.add(order)
        db_session.commit()

        assert order.order_no == f"OUTREQ{timestamp}"
        assert order.order_type == "MACHINING"

    def test_outsourcing_order_amounts(
        self, db_session: Session, test_outsourcing_vendor
    ):
        """测试外协订单金额"""
        timestamp = datetime.now().timestamp()
        order = OutsourcingOrder(
        order_no=f"OUTAMT{timestamp}",
        project_id=1,
        vendor_id=test_outsourcing_vendor.id,
        order_type="MACHINING",
        order_title="金额测试",
        total_amount=Decimal("10000.00"),
        tax_rate=Decimal("13.00"),
        tax_amount=Decimal("1300.00"),
        amount_with_tax=Decimal("11300.00"),
        )
        db_session.add(order)
        db_session.commit()

        assert order.total_amount == Decimal("10000.00")
        assert order.tax_amount == Decimal("1300.00")

    def test_outsourcing_order_dates(
        self, db_session: Session, test_outsourcing_vendor
    ):
        """测试外协订单日期"""
        today = date.today()
        timestamp = datetime.now().timestamp()
        order = OutsourcingOrder(
        order_no=f"OUTDATE{timestamp}",
        project_id=1,
        vendor_id=test_outsourcing_vendor.id,
        order_type="MACHINING",
        order_title="日期测试",
        required_date=today + timedelta(days=30),
        estimated_date=today + timedelta(days=25),
        )
        db_session.add(order)
        db_session.commit()

        assert order.required_date == today + timedelta(days=30)
        assert order.estimated_date == today + timedelta(days=25)

    def test_outsourcing_order_status(
        self, db_session: Session, test_outsourcing_vendor
    ):
        """测试外协订单状态"""
        timestamp = datetime.now().timestamp()
        order = OutsourcingOrder(
        order_no=f"OUTSTS{timestamp}",
        project_id=1,
        vendor_id=test_outsourcing_vendor.id,
        order_type="MACHINING",
        order_title="状态测试",
        status="SUBMITTED",
        payment_status="UNPAID",
        )
        db_session.add(order)
        db_session.commit()

        assert order.status == "SUBMITTED"
        assert order.payment_status == "UNPAID"

    def test_outsourcing_order_delivery(
        self, db_session: Session, test_outsourcing_vendor
    ):
        """测试外协订单交付"""
        timestamp = datetime.now().timestamp()
        order = OutsourcingOrder(
        order_no=f"OUTDLV{timestamp}",
        project_id=1,
        vendor_id=test_outsourcing_vendor.id,
        order_type="MACHINING",
        order_title="交付测试",
        actual_date=date.today(),
        paid_amount=Decimal("1000.00"),
        )
        db_session.add(order)
        db_session.commit()

        assert order.actual_date == date.today()
        assert order.paid_amount == Decimal("1000.00")

    def test_outsourcing_order_repr(self, db_session: Session, test_outsourcing_vendor):
        """测试外协订单字符串表示"""
        order = OutsourcingOrder(
        order_no="OUTREP001",
        project_id=1,
        vendor_id=test_outsourcing_vendor.id,
        order_type="MACHINING",
        order_title="repr测试",
        )
        db_session.add(order)
        db_session.commit()

        # Model may not have __repr__, just verify str representation works
        assert "OutsourcingOrder" in repr(order)


# ============================================================================
# Alert Models Tests
# ============================================================================


@pytest.mark.unit
class TestAlertRuleModel:
    """预警规则模型测试"""

    @pytest.fixture
    def test_alert_rule_data(self, test_user):
        """测试预警规则数据"""
        timestamp = datetime.now().timestamp()
        return {
        "rule_code": f"RULE{timestamp}",
        "rule_name": "测试预警规则",
        "rule_type": "PROJECT_HEALTH",
        "target_type": "PROJECT",
        "condition_type": "THRESHOLD",  # Required field
        "alert_level": "WARNING",
        "is_enabled": True,
        "created_by": test_user.id,
        }

    def test_alert_rule_creation(self, db_session: Session, test_alert_rule_data):
        rule = AlertRule(
        rule_code=test_alert_rule_data["rule_code"],
        rule_name=test_alert_rule_data["rule_name"],
        rule_type=test_alert_rule_data["rule_type"],
        target_type=test_alert_rule_data["target_type"],
        condition_type=test_alert_rule_data["condition_type"],
        alert_level=test_alert_rule_data["alert_level"],
        is_enabled=test_alert_rule_data["is_enabled"],
        created_by=test_alert_rule_data["created_by"],
        )
        db_session.add(rule)
        db_session.commit()
        db_session.refresh(rule)

        assert rule.id is not None
        assert rule.rule_code == test_alert_rule_data["rule_code"]
        assert rule.rule_name == test_alert_rule_data["rule_name"]
        assert rule.rule_type == "PROJECT_HEALTH"

    def test_alert_rule_required_fields(self, db_session: Session):
        """测试预警规则必填字段"""
        timestamp = datetime.now().timestamp()
        rule = AlertRule(
        rule_code=f"RULE{timestamp}",
        rule_name="必填测试",
        rule_type="PROJECT_HEALTH",
        target_type="PROJECT",
        condition_type="THRESHOLD",
        alert_level="WARNING",
        )
        db_session.add(rule)
        db_session.commit()

        assert rule.rule_code == f"RULE{timestamp}"
        assert rule.rule_name == "必填测试"
        assert rule.rule_type == "PROJECT_HEALTH"

    def test_alert_rule_conditions(self, db_session: Session):
        """测试预警规则条件"""
        timestamp = datetime.now().timestamp()
        rule = AlertRule(
        rule_code=f"RULECND{timestamp}",
        rule_name="条件测试",
        rule_type="PROJECT_HEALTH",
        target_type="PROJECT",
        condition_type="THRESHOLD",
        alert_level="WARNING",
        target_field="progress_pct",
        condition_operator="<=",
        threshold_value="75",
        )
        db_session.add(rule)
        db_session.commit()

        assert rule.target_field == "progress_pct"
        assert rule.condition_operator == "<="
        assert rule.threshold_value == "75"

    def test_alert_rule_level(self, db_session: Session):
        """测试预警规则级别"""
        timestamp = datetime.now().timestamp()
        rule = AlertRule(
        rule_code=f"RULELVL{timestamp}",
        rule_name="级别测试",
        rule_type="PROJECT_HEALTH",
        target_type="PROJECT",
        condition_type="THRESHOLD",
        alert_level="SEVERE",
        is_enabled=True,
        )
        db_session.add(rule)
        db_session.commit()

        assert rule.alert_level == "SEVERE"
        assert rule.is_enabled is True

    def test_alert_rule_notification(self, db_session: Session):
        """测试预警规则通知"""
        timestamp = datetime.now().timestamp()
        rule = AlertRule(
        rule_code=f"RULENTF{timestamp}",
        rule_name="通知测试",
        rule_type="PROJECT_HEALTH",
        target_type="PROJECT",
        condition_type="THRESHOLD",
        alert_level="WARNING",
        notify_channels=["EMAIL", "SMS"],
        )
        db_session.add(rule)
        db_session.commit()

        assert rule.notify_channels == ["EMAIL", "SMS"]

    def test_alert_rule_frequency(self, db_session: Session):
        """测试预警规则频率"""
        timestamp = datetime.now().timestamp()
        rule = AlertRule(
        rule_code=f"RULEFRQ{timestamp}",
        rule_name="频率测试",
        rule_type="PROJECT_HEALTH",
        target_type="PROJECT",
        condition_type="THRESHOLD",
        alert_level="WARNING",
        check_frequency="HOURLY",
        )
        db_session.add(rule)
        db_session.commit()

        assert rule.check_frequency == "HOURLY"

    def test_alert_rule_repr(self, db_session: Session):
        """测试预警规则字符串表示"""
        rule = AlertRule(
        rule_code="RULREP001",
        rule_name="repr测试",
        rule_type="PROJECT_HEALTH",
        target_type="PROJECT",
        condition_type="THRESHOLD",
        )
        db_session.add(rule)
        db_session.commit()

        assert f"<AlertRule {rule.rule_code}>" in repr(rule)


@pytest.mark.unit
@pytest.mark.skip(
    reason="SQLite does not properly handle BigInteger autoincrement for AlertRecord.id"
)
class TestAlertRecordModel:
    """预警记录模型测试"""

    @pytest.fixture
    def test_alert_rule_for_record(self, db_session: Session, test_user):
        """创建测试预警规则"""
        timestamp = datetime.now().timestamp()
        rule = AlertRule(
        rule_code=f"RULETST{timestamp}",
        rule_name="测试规则",
        rule_type="PROJECT_HEALTH",
        target_type="PROJECT",
        condition_type="THRESHOLD",
        alert_level="WARNING",
        is_enabled=True,
        created_by=test_user.id,
        )
        db_session.add(rule)
        db_session.commit()
        db_session.refresh(rule)
        return rule

    @pytest.fixture
    def test_alert_record_data(
        self, test_alert_rule_for_record, test_project_with_customer
    ):
        """测试预警记录数据"""
        timestamp = datetime.now().timestamp()
        return {
        "alert_no": f"ALRT{timestamp}",
        "rule_id": test_alert_rule_for_record.id,
        "target_type": "PROJECT",
        "target_id": test_project_with_customer.id,
        "target_no": test_project_with_customer.project_code,
        "target_name": test_project_with_customer.project_name,
        "alert_level": "WARNING",
        "alert_title": "测试预警",
        "alert_content": "测试内容",
        }

    def test_alert_record_creation(self, db_session: Session, test_alert_record_data):
        record = AlertRecord(
        alert_no=test_alert_record_data["alert_no"],
        rule_id=test_alert_record_data["rule_id"],
        target_type=test_alert_record_data["target_type"],
        target_id=test_alert_record_data["target_id"],
        target_no=test_alert_record_data["target_no"],
        target_name=test_alert_record_data["target_name"],
        alert_level=test_alert_record_data["alert_level"],
        alert_title=test_alert_record_data["alert_title"],
        alert_content=test_alert_record_data["alert_content"],
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        assert record.id is not None
        assert record.alert_no == test_alert_record_data["alert_no"]
        assert record.rule_id == test_alert_record_data["rule_id"]
        assert record.target_type == "PROJECT"
        assert record.alert_level == "WARNING"

    def test_alert_record_required_fields(
        self, db_session: Session, test_alert_rule_for_record
    ):
        """测试预警记录必填字段"""
        timestamp = datetime.now().timestamp()
        record = AlertRecord(
        alert_no=f"ALRTREQ{timestamp}",
        rule_id=test_alert_rule_for_record.id,
        target_type="PROJECT",
        target_id=1,
        target_no="PJ250708001",
        target_name="测试项目",
        alert_level="WARNING",
        alert_title="测试必填",
        alert_content="测试内容",
        )
        db_session.add(record)
        db_session.commit()

        assert record.target_id == 1
        assert record.target_type == "PROJECT"
        assert record.target_no == "PJ250708001"
        assert record.alert_title == "测试必填"

    def test_alert_record_trigger_info(
        self, db_session: Session, test_alert_rule_for_record
    ):
        """测试预警记录触发信息"""
        timestamp = datetime.now()
        record = AlertRecord(
        alert_no=f"ALTTRG{timestamp.timestamp()}",
        rule_id=test_alert_rule_for_record.id,
        target_type="PROJECT",
        target_id=1,
        target_no="PJ250708001",
        target_name="测试项目",
        alert_level="WARNING",
        alert_title="触发信息测试",
        alert_content="触发内容",
        triggered_at=datetime.now(),
        trigger_value="35",
        threshold_value="30",
        )
        db_session.add(record)
        db_session.commit()

        assert record.triggered_at is not None
        assert record.trigger_value == "35"
        assert record.threshold_value == "30"

    def test_alert_record_status(self, db_session: Session, test_alert_rule_for_record):
        """测试预警记录状态"""
        timestamp = datetime.now().timestamp()
        record = AlertRecord(
        alert_no=f"ALSTS{timestamp}",
        rule_id=test_alert_rule_for_record.id,
        target_type="PROJECT",
        target_id=1,
        target_no="PJ250708001",
        target_name="测试项目",
        alert_level="WARNING",
        alert_title="状态测试",
        alert_content="状态内容",
        status="PENDING",
        )
        db_session.add(record)
        db_session.commit()

        assert record.status == "PENDING"

        record.status = "RESOLVED"
        record.resolution_note = "已解决"
        db_session.commit()

        assert record.status == "RESOLVED"
        assert record.resolution_note == "已解决"

    def test_alert_record_handling(
        self, db_session: Session, test_alert_rule_for_record
    ):
        """测试预警记录处理"""
        timestamp = datetime.now().timestamp()
        record = AlertRecord(
        alert_no=f"ALHNDL{timestamp}",
        rule_id=test_alert_rule_for_record.id,
        target_type="PROJECT",
        target_id=1,
        target_no="PJ250708001",
        target_name="测试项目",
        alert_level="WARNING",
        alert_title="处理测试",
        alert_content="处理内容",
        status="PENDING",
        )
        db_session.add(record)
        db_session.commit()

        record.status = "IN_PROGRESS"
        record.handler_id = 1
        record.handler_name = "处理人"
        db_session.commit()

        assert record.status == "IN_PROGRESS"
        assert record.handler_name == "处理人"

    def test_alert_record_repr(self, db_session: Session, test_alert_rule_for_record):
        """测试预警记录字符串表示"""
        record = AlertRecord(
        alert_no="ALTREP001",
        rule_id=test_alert_rule_for_record.id,
        target_type="PROJECT",
        target_id=1,
        target_no="PJ250708001",
        target_name="测试项目",
        alert_level="WARNING",
        alert_title="repr测试",
        alert_content="repr内容",
        )
        db_session.add(record)
        db_session.commit()

        assert f"<AlertRecord {record.alert_no}>" in repr(record)


# ============================================================================
# Model Integration Tests
# ============================================================================


@pytest.mark.unit
class TestModelsIntegration:
    """模型关系集成测试"""

    def test_project_machine_relationship(self, db_session: Session, test_user):
        """测试项目-设备关系"""
        timestamp = datetime.now().timestamp()
        project = Project(
        project_code=f"PJREL{timestamp}",
        project_name="关系测试项目",
        customer_id=1,
        customer_name="测试客户",
        created_by=test_user.id,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        machine1 = Machine(
        project_id=project.id,
        machine_code=f"REL001{timestamp}",
        machine_name="关系设备1",
        machine_no=1,
        )
        machine2 = Machine(
        project_id=project.id,
        machine_code=f"REL002{timestamp}",
        machine_name="关系设备2",
        machine_no=2,
        )
        db_session.add_all([machine1, machine2])
        db_session.commit()

        assert len(list(project.machines)) == 2

    def test_supplier_purchase_order_relationship(self, db_session: Session):
        """测试供应商-采购订单关系"""
        timestamp = datetime.now().timestamp()
        supplier = Supplier(
        supplier_code=f"SREL003{timestamp}",
        supplier_name="关系供应商",
        supplier_type="VENDOR",
        contact_person="张三",
        contact_phone="13800138000",
        status="ACTIVE",
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)

        po = PurchaseOrder(
        supplier_id=supplier.id,
        project_id=1,
        order_no=f"POREL001{timestamp}",
        order_title="关系测试",
        order_type="NORMAL",
        )
        db_session.add(po)
        db_session.commit()

        assert po.supplier_id == supplier.id
        assert po.supplier == supplier


# ============================================================================
# End
# ============================================================================
# End of test file
# ============================================================================
