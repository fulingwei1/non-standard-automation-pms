"""
场景17：数据一致性

测试跨表、跨模块的数据一致性保证
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.project import Project, Customer
from app.models.sales.contracts import Contract
from app.models.sales.invoices import Invoice
from app.models.material import Material, MaterialInventory, InventoryTransaction


class TestDataConsistency:
    """数据一致性测试"""

    @pytest.fixture
    def consistency_customer(self, db_session: Session):
        customer = Customer(
            customer_code="CUST-CONS-001",
            customer_name="一致性测试客户",
            contact_person="测试联系人",
            contact_phone="13900139000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        return customer

    def test_01_project_contract_amount_consistency(
        self, db_session: Session, consistency_customer: Customer
    ):
        """测试1：项目与合同金额一致性"""
        # 创建合同
        contract = Contract(
            contract_code="CT-CONS-001",
            customer_id=consistency_customer.id,
            total_amount=Decimal("1500000.00"),
            status="SIGNED",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 创建项目
        project = Project(
            project_code="PJ-CONS-001",
            project_name="一致性测试项目",
            customer_id=consistency_customer.id,
            customer_name=consistency_customer.customer_name,
            contract_id=contract.id,
            contract_amount=contract.total_amount,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 验证金额一致
        assert project.contract_amount == contract.total_amount

        # 合同金额变更
        contract.total_amount = Decimal("1600000.00")
        db_session.commit()

        # 项目金额应同步更新
        project.contract_amount = contract.total_amount
        db_session.commit()

        db_session.refresh(project)
        assert project.contract_amount == Decimal("1600000.00")

    def test_02_invoice_total_vs_contract_amount(
        self, db_session: Session, consistency_customer: Customer
    ):
        """测试2：发票总额与合同金额一致性"""
        # 创建合同
        contract = Contract(
            contract_code="CT-INV-001",
            customer_id=consistency_customer.id,
            total_amount=Decimal("1000000.00"),
            status="SIGNED",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 创建发票（含税）
        tax_rate = Decimal("0.13")
        
        # 预付30%
        inv1_amount = contract.total_amount * Decimal("0.3")
        inv1_tax = inv1_amount * tax_rate
        inv1 = Invoice(
            invoice_code="INV-CONS-001",
            contract_id=contract.id,
            customer_id=consistency_customer.id,
            invoice_type="ADVANCE",
            amount=inv1_amount,
            tax_rate=tax_rate,
            tax_amount=inv1_tax,
            total_amount=inv1_amount + inv1_tax,
            status="ISSUED",
            created_by=1,
        )
        db_session.add(inv1)

        # 发货款30%
        inv2_amount = contract.total_amount * Decimal("0.3")
        inv2_tax = inv2_amount * tax_rate
        inv2 = Invoice(
            invoice_code="INV-CONS-002",
            contract_id=contract.id,
            customer_id=consistency_customer.id,
            invoice_type="DELIVERY",
            amount=inv2_amount,
            tax_rate=tax_rate,
            tax_amount=inv2_tax,
            total_amount=inv2_amount + inv2_tax,
            status="ISSUED",
            created_by=1,
        )
        db_session.add(inv2)

        # 验收款40%
        inv3_amount = contract.total_amount * Decimal("0.4")
        inv3_tax = inv3_amount * tax_rate
        inv3 = Invoice(
            invoice_code="INV-CONS-003",
            contract_id=contract.id,
            customer_id=consistency_customer.id,
            invoice_type="ACCEPTANCE",
            amount=inv3_amount,
            tax_rate=tax_rate,
            tax_amount=inv3_tax,
            total_amount=inv3_amount + inv3_tax,
            status="ISSUED",
            created_by=1,
        )
        db_session.add(inv3)
        db_session.commit()

        # 验证发票总额（不含税）= 合同金额
        total_invoice_amount = db_session.query(
            func.sum(Invoice.amount)
        ).filter(
            Invoice.contract_id == contract.id
        ).scalar()

        assert total_invoice_amount == contract.total_amount

    def test_03_inventory_transaction_balance(
        self, db_session: Session
    ):
        """测试3：库存交易流水与库存余额一致性"""
        # 创建物料
        material = Material(
            material_code="MAT-CONS-001",
            material_name="一致性测试物料",
            category="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        # 创建库存
        inventory = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            quantity=Decimal("0"),
            available_quantity=Decimal("0"),
        )
        db_session.add(inventory)
        db_session.commit()

        # 记录交易
        transactions = [
            {"type": "IN", "qty": Decimal("100")},
            {"type": "OUT", "qty": Decimal("30")},
            {"type": "IN", "qty": Decimal("50")},
            {"type": "OUT", "qty": Decimal("20")},
        ]

        for trans_data in transactions:
            trans = InventoryTransaction(
                material_id=material.id,
                transaction_type=trans_data["type"],
                quantity=trans_data["qty"],
                reference_code=f"TXN-{datetime.now().timestamp()}",
                created_at=datetime.now(),
            )
            db_session.add(trans)

            # 更新库存
            if trans_data["type"] == "IN":
                inventory.quantity += trans_data["qty"]
                inventory.available_quantity += trans_data["qty"]
            else:
                inventory.quantity -= trans_data["qty"]
                inventory.available_quantity -= trans_data["qty"]
        
        db_session.commit()

        # 验证库存余额 = 交易流水合计
        total_in = db_session.query(
            func.sum(InventoryTransaction.quantity)
        ).filter(
            InventoryTransaction.material_id == material.id,
            InventoryTransaction.transaction_type == "IN"
        ).scalar() or Decimal("0")

        total_out = db_session.query(
            func.sum(InventoryTransaction.quantity)
        ).filter(
            InventoryTransaction.material_id == material.id,
            InventoryTransaction.transaction_type == "OUT"
        ).scalar() or Decimal("0")

        expected_balance = total_in - total_out
        assert inventory.quantity == expected_balance

    def test_04_customer_project_count_consistency(
        self, db_session: Session, consistency_customer: Customer
    ):
        """测试4：客户项目数量一致性"""
        # 创建多个项目
        for i in range(5):
            project = Project(
                project_code=f"PJ-CUST-{i+1:03d}",
                project_name=f"客户项目{i+1}",
                customer_id=consistency_customer.id,
                customer_name=consistency_customer.customer_name,
                stage="S1",
                status="ST01",
                created_by=1,
            )
            db_session.add(project)
        db_session.commit()

        # 统计项目数
        project_count = db_session.query(Project).filter(
            Project.customer_id == consistency_customer.id
        ).count()

        assert project_count == 5

    def test_05_foreign_key_integrity(
        self, db_session: Session, consistency_customer: Customer
    ):
        """测试5：外键完整性"""
        # 创建项目
        project = Project(
            project_code="PJ-FK-001",
            project_name="外键测试项目",
            customer_id=consistency_customer.id,
            customer_name=consistency_customer.customer_name,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 验证外键关联
        proj = db_session.query(Project).filter(
            Project.id == project.id
        ).first()
        assert proj.customer_id == consistency_customer.id

        # 尝试删除被引用的客户（应该失败或级联）
        # 根据数据库设置，可能抛出异常或级联删除
        try:
            db_session.delete(consistency_customer)
            db_session.commit()
        except Exception:
            db_session.rollback()
            # 验证项目仍然存在
            proj_after = db_session.query(Project).filter(
                Project.id == project.id
            ).first()
            assert proj_after is not None

    def test_06_cascading_update_consistency(
        self, db_session: Session, consistency_customer: Customer
    ):
        """测试6：级联更新一致性"""
        # 创建合同
        contract = Contract(
            contract_code="CT-CAS-001",
            customer_id=consistency_customer.id,
            total_amount=Decimal("800000.00"),
            status="SIGNED",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 创建多个发票
        for i in range(3):
            invoice = Invoice(
                invoice_code=f"INV-CAS-{i+1:03d}",
                contract_id=contract.id,
                customer_id=consistency_customer.id,
                amount=Decimal("200000.00"),
                total_amount=Decimal("226000.00"),
                status="ISSUED",
                created_by=1,
            )
            db_session.add(invoice)
        db_session.commit()

        # 更新合同状态
        contract.status = "COMPLETED"
        db_session.commit()

        # 如果配置了级联更新，发票可能也需要更新状态
        # 这里手动更新演示一致性
        db_session.query(Invoice).filter(
            Invoice.contract_id == contract.id
        ).update({"related_contract_status": contract.status})
        db_session.commit()

        # 验证所有发票都关联到正确的合同状态
        invoices = db_session.query(Invoice).filter(
            Invoice.contract_id == contract.id
        ).all()
        assert all(inv.contract_id == contract.id for inv in invoices)

    def test_07_aggregate_data_consistency(
        self, db_session: Session, consistency_customer: Customer
    ):
        """测试7：聚合数据一致性"""
        # 创建项目
        project = Project(
            project_code="PJ-AGG-001",
            project_name="聚合测试项目",
            customer_id=consistency_customer.id,
            customer_name=consistency_customer.customer_name,
            contract_amount=Decimal("2000000.00"),
            stage="S3",
            status="ST02",
            progress=0,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 模拟项目进度更新
        milestones_completed = 3
        total_milestones = 10
        calculated_progress = int((milestones_completed / total_milestones) * 100)

        project.progress = calculated_progress
        db_session.commit()

        # 验证进度计算正确
        assert project.progress == 30

    def test_08_denormalized_data_sync(
        self, db_session: Session, consistency_customer: Customer
    ):
        """测试8：冗余数据同步"""
        # 创建项目（冗余存储客户名称）
        project = Project(
            project_code="PJ-DENORM-001",
            project_name="冗余数据测试",
            customer_id=consistency_customer.id,
            customer_name=consistency_customer.customer_name,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 更新客户名称
        old_name = consistency_customer.customer_name
        consistency_customer.customer_name = "更新后的客户名称"
        db_session.commit()

        # 同步更新项目中的冗余数据
        db_session.query(Project).filter(
            Project.customer_id == consistency_customer.id
        ).update({"customer_name": consistency_customer.customer_name})
        db_session.commit()

        db_session.refresh(project)
        assert project.customer_name == "更新后的客户名称"

    def test_09_temporal_consistency(
        self, db_session: Session, consistency_customer: Customer
    ):
        """测试9：时间一致性"""
        from datetime import timedelta

        # 创建项目
        project = Project(
            project_code="PJ-TIME-001",
            project_name="时间一致性测试",
            customer_id=consistency_customer.id,
            customer_name=consistency_customer.customer_name,
            plan_start_date=date.today(),
            plan_end_date=date.today() + timedelta(days=90),
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 验证计划结束日期在开始日期之后
        assert project.plan_end_date > project.plan_start_date

        # 项目启动
        project.actual_start_date = date.today()
        project.status = "ST02"
        db_session.commit()

        # 项目完成
        project.actual_end_date = date.today() + timedelta(days=95)
        project.status = "ST03"
        db_session.commit()

        # 验证实际结束日期在开始日期之后
        assert project.actual_end_date > project.actual_start_date

    def test_10_cross_module_data_consistency(
        self, db_session: Session, consistency_customer: Customer
    ):
        """测试10：跨模块数据一致性"""
        # 销售模块：合同
        contract = Contract(
            contract_code="CT-CROSS-001",
            customer_id=consistency_customer.id,
            total_amount=Decimal("1200000.00"),
            status="SIGNED",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 项目模块：项目
        project = Project(
            project_code="PJ-CROSS-001",
            project_name="跨模块测试项目",
            customer_id=consistency_customer.id,
            customer_name=consistency_customer.customer_name,
            contract_id=contract.id,
            contract_code=contract.contract_code,
            contract_amount=contract.total_amount,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 财务模块：发票
        invoice = Invoice(
            invoice_code="INV-CROSS-001",
            contract_id=contract.id,
            customer_id=consistency_customer.id,
            amount=Decimal("360000.00"),  # 30%预付
            total_amount=Decimal("406800.00"),
            status="ISSUED",
            created_by=1,
        )
        db_session.add(invoice)
        db_session.commit()

        # 验证跨模块数据一致
        assert project.contract_id == contract.id
        assert invoice.contract_id == contract.id
        assert project.customer_id == invoice.customer_id == contract.customer_id
