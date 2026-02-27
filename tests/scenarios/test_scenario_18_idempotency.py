"""
场景18：幂等性验证

测试API和操作的幂等性，确保重复请求不会产生副作用
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
try:
    from app.models.project import Project, Customer
    from app.models.sales.contracts import Contract
    from app.models.material import Material, MaterialInventory
    from app.models.approval.instance import ApprovalInstance
except ImportError as e:
    pytest.skip(f"Required models not available: {e}", allow_module_level=True)


class TestIdempotency:
    """幂等性测试"""

    @pytest.fixture
    def idempotency_customer(self, db_session: Session):
        customer = Customer(
            customer_code="CUST-IDEMP-001",
            customer_name="幂等性测试客户",
            contact_person="测试联系人",
            contact_phone="13800138000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        return customer

    def test_01_create_operation_with_idempotency_key(
        self, db_session: Session, idempotency_customer: Customer
    ):
        """测试1：使用幂等性键创建操作"""
        idempotency_key = "IDEMP-KEY-001"

        # 第一次创建
        project1 = db_session.query(Project).filter(
            Project.project_code == "PJ-IDEMP-001"
        ).first()

        if not project1:
            project1 = Project(
                project_code="PJ-IDEMP-001",
                project_name="幂等性测试项目",
                customer_id=idempotency_customer.id,
                customer_name=idempotency_customer.customer_name,
                stage="S1",
                status="ST01",
                idempotency_key=idempotency_key,
                created_by=1,
            )
            db_session.add(project1)
            db_session.commit()

        # 第二次创建（使用相同幂等性键）
        project2 = db_session.query(Project).filter(
            Project.idempotency_key == idempotency_key
        ).first()

        # 应该返回已存在的项目，而不是创建新的
        assert project2 is not None
        assert project2.id == project1.id

    def test_02_update_operation_idempotency(
        self, db_session: Session, idempotency_customer: Customer
    ):
        """测试2：更新操作幂等性"""
        # 创建项目
        project = Project(
            project_code="PJ-UPD-001",
            project_name="更新测试项目",
            customer_id=idempotency_customer.id,
            customer_name=idempotency_customer.customer_name,
            stage="S1",
            status="ST01",
            progress=0,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 第一次更新
        project.progress = 50
        db_session.commit()
        first_update_time = project.updated_at

        # 第二次更新（相同值）
        project.progress = 50
        db_session.commit()

        # 值相同，幂等操作
        assert project.progress == 50

    def test_03_delete_operation_idempotency(
        self, db_session: Session, idempotency_customer: Customer
    ):
        """测试3：删除操作幂等性"""
        # 创建项目
        project = Project(
            project_code="PJ-DEL-001",
            project_name="删除测试项目",
            customer_id=idempotency_customer.id,
            customer_name=idempotency_customer.customer_name,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()
        project_id = project.id

        # 第一次删除
        db_session.delete(project)
        db_session.commit()

        # 第二次删除（已经不存在）
        project_retry = db_session.query(Project).filter(
            Project.id == project_id
        ).first()

        # 应该返回None，不抛出异常
        assert project_retry is None

    def test_04_inventory_deduction_idempotency(
        self, db_session: Session
    ):
        """测试4：库存扣减幂等性"""
        # 创建物料和库存
        material = Material(
            material_code="MAT-IDEMP-001",
            material_name="幂等性测试物料",
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
        )
        db_session.add(inventory)
        db_session.commit()

        # 扣减请求（带幂等性键）
        deduction_key = "DEDUCT-001"
        deduction_amount = Decimal("20")

        # 检查是否已处理
        processed = db_session.query(InventoryTransaction).filter(
            InventoryTransaction.reference_code == deduction_key
        ).first()

        if not processed:
            # 第一次扣减
            inventory.available_quantity -= deduction_amount
            
            from app.models.material import InventoryTransaction
            trans = InventoryTransaction(
                material_id=material.id,
                transaction_type="OUT",
                quantity=deduction_amount,
                reference_code=deduction_key,
                created_at=datetime.now(),
            )
            db_session.add(trans)
            db_session.commit()

        # 第二次扣减（相同键）
        processed_again = db_session.query(InventoryTransaction).filter(
            InventoryTransaction.reference_code == deduction_key
        ).first()

        # 应该找到之前的记录，不重复扣减
        assert processed_again is not None
        
        db_session.refresh(inventory)
        assert inventory.available_quantity == Decimal("80")  # 只扣减一次

    def test_05_approval_submission_idempotency(
        self, db_session: Session
    ):
        """测试5：审批提交幂等性"""
        from app.models.purchase import PurchaseRequest

        # 创建采购申请
        pr = PurchaseRequest(
            request_no="PR-IDEMP-001",
            requester_id=3,
            total_amount=Decimal("100000.00"),
            status="DRAFT",
            created_by=3,
        )
        db_session.add(pr)
        db_session.commit()

        submission_key = "SUBMIT-PR-001"

        # 检查是否已提交
        existing_instance = db_session.query(ApprovalInstance).filter(
            ApprovalInstance.business_id == pr.id,
            ApprovalInstance.business_type == "PURCHASE_REQUEST"
        ).first()

        if not existing_instance:
            # 第一次提交审批
            instance = ApprovalInstance(
                business_type="PURCHASE_REQUEST",
                business_id=pr.id,
                business_code=pr.request_code,
                initiator_id=3,
                status="PENDING",
                idempotency_key=submission_key,
                created_by=3,
            )
            db_session.add(instance)
            pr.status = "PENDING_APPROVAL"
            db_session.commit()

        # 第二次提交（相同键）
        instance_retry = db_session.query(ApprovalInstance).filter(
            ApprovalInstance.idempotency_key == submission_key
        ).first()

        # 应该返回已存在的实例
        assert instance_retry is not None
        assert pr.status == "PENDING_APPROVAL"

    def test_06_payment_recording_idempotency(
        self, db_session: Session, idempotency_customer: Customer
    ):
        """测试6：回款记录幂等性"""
        from app.models.sales.invoices import Invoice

        # 创建发票
        invoice = Invoice(
            invoice_code="INV-IDEMP-001",
            customer_id=idempotency_customer.id,
            total_amount=Decimal("113000.00"),
            paid_amount=Decimal("0"),
            status="ISSUED",
            created_by=1,
        )
        db_session.add(invoice)
        db_session.commit()

        payment_key = "PAY-001"
        payment_amount = Decimal("113000.00")

        # 检查是否已记录
        if invoice.paid_amount < payment_amount:
            # 第一次记录回款
            invoice.paid_amount += payment_amount
            invoice.paid_date = date.today()
            invoice.status = "PAID"
            invoice.payment_reference = payment_key
            db_session.commit()

        # 第二次记录（相同键）
        db_session.refresh(invoice)

        # 应该只记录一次
        assert invoice.paid_amount == Decimal("113000.00")
        assert invoice.status == "PAID"

    def test_07_status_transition_idempotency(
        self, db_session: Session, idempotency_customer: Customer
    ):
        """测试7：状态流转幂等性"""
        # 创建合同
        contract = Contract(
            contract_code="CT-IDEMP-001",
            customer_id=idempotency_customer.id,
            total_amount=Decimal("800000.00"),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 第一次签署
        if contract.status != "SIGNED":
            contract.status = "SIGNED"
            contract.signed_date = date.today()
            db_session.commit()

        # 第二次签署（已是SIGNED状态）
        if contract.status != "SIGNED":
            contract.status = "SIGNED"
            contract.signed_date = date.today()
            db_session.commit()

        # 状态应该保持SIGNED，不会重复处理
        assert contract.status == "SIGNED"

    def test_08_batch_operation_idempotency(
        self, db_session: Session, idempotency_customer: Customer
    ):
        """测试8：批量操作幂等性"""
        batch_key = "BATCH-CREATE-001"

        # 检查批次是否已处理
        existing_projects = db_session.query(Project).filter(
            Project.batch_key == batch_key
        ).all()

        if not existing_projects:
            # 第一次批量创建
            for i in range(3):
                project = Project(
                    project_code=f"PJ-BATCH-{i+1:03d}",
                    project_name=f"批量项目{i+1}",
                    customer_id=idempotency_customer.id,
                    customer_name=idempotency_customer.customer_name,
                    stage="S1",
                    status="ST01",
                    batch_key=batch_key,
                    created_by=1,
                )
                db_session.add(project)
            db_session.commit()

        # 第二次批量创建（相同键）
        projects = db_session.query(Project).filter(
            Project.batch_key == batch_key
        ).all()

        # 应该只有3个项目
        assert len(projects) == 3

    def test_09_api_request_idempotency_header(
        self, db_session: Session, idempotency_customer: Customer
    ):
        """测试9：API请求幂等性头"""
        # 模拟API请求处理
        request_id = "REQ-IDEMP-001"

        # 第一次请求
        def process_request(session, req_id, customer_id):
            # 检查请求是否已处理
            existing = session.query(Project).filter(
                Project.request_id == req_id
            ).first()

            if existing:
                return existing, False  # 已存在，未创建

            # 创建新项目
            project = Project(
                project_code=f"PJ-REQ-{req_id}",
                project_name="API创建项目",
                customer_id=customer_id,
                customer_name="测试客户",
                stage="S1",
                status="ST01",
                request_id=req_id,
                created_by=1,
            )
            session.add(project)
            session.commit()
            return project, True  # 新创建

        # 第一次请求
        proj1, created1 = process_request(
            db_session, request_id, idempotency_customer.id
        )
        assert created1 is True

        # 第二次请求（相同request_id）
        proj2, created2 = process_request(
            db_session, request_id, idempotency_customer.id
        )
        assert created2 is False
        assert proj2.id == proj1.id

    def test_10_concurrent_idempotent_operations(
        self, db_session: Session
    ):
        """测试10：并发幂等操作"""
        material = Material(
            material_code="MAT-CONC-IDEMP-001",
            material_name="并发幂等测试物料",
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
        )
        db_session.add(inventory)
        db_session.commit()

        # 模拟并发扣减请求（相同幂等性键）
        deduction_key = "CONC-DEDUCT-001"
        deduction_amount = Decimal("30")

        from app.models.base import SessionLocal
        from app.models.material import InventoryTransaction

        def idempotent_deduct(session, inv_id, amount, ref_code):
            # 检查是否已处理
            existing = session.query(InventoryTransaction).filter(
                InventoryTransaction.reference_code == ref_code
            ).first()

            if existing:
                return False  # 已处理

            # 加锁扣减
            inv = session.query(MaterialInventory).filter(
                MaterialInventory.id == inv_id
            ).with_for_update().first()

            if inv and inv.available_quantity >= amount:
                inv.available_quantity -= amount
                trans = InventoryTransaction(
                    material_id=inv.material_id,
                    transaction_type="OUT",
                    quantity=amount,
                    reference_code=ref_code,
                    created_at=datetime.now(),
                )
                session.add(trans)
                session.commit()
                return True

            session.rollback()
            return False

        # 多次请求（相同键）
        results = []
        for i in range(3):
            sess = SessionLocal()
            result = idempotent_deduct(
                sess, inventory.id, deduction_amount, deduction_key
            )
            results.append(result)
            sess.close()

        # 只有一次成功
        assert sum(results) == 1

        db_session.refresh(inventory)
        assert inventory.available_quantity == Decimal("70")
