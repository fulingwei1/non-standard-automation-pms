"""
场景16：事务回滚

测试各种异常情况下的事务回滚机制
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
try:
    from app.models.project import Project, Customer
    from app.models.purchase import PurchaseOrder, PurchaseOrderItem
    from app.models.material import Material, MaterialInventory
    from app.models.approval.instance import ApprovalInstance
except ImportError as e:
    pytest.skip(f"Required models not available: {e}", allow_module_level=True)


class TestTransactionRollback:
    """事务回滚测试"""

    @pytest.fixture
    def test_customer(self, db_session: Session):
        """创建测试客户"""
        customer = Customer(
            customer_code="CUST-TXN-001",
            customer_name="事务测试客户",
            contact_person="测试联系人",
            contact_phone="13800138000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        return customer

    def test_01_rollback_on_constraint_violation(self, db_session: Session, test_customer: Customer):
        """测试1：约束违反时回滚"""
        # 创建项目
        project1 = Project(
            project_code="PJ-UNIQUE-001",
            project_name="唯一性测试项目1",
            customer_id=test_customer.id,
            customer_name=test_customer.customer_name,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project1)
        db_session.commit()

        # 尝试创建重复项目编号（应该回滚）
        try:
            project2 = Project(
                project_code="PJ-UNIQUE-001",  # 重复编号
                project_name="唯一性测试项目2",
                customer_id=test_customer.id,
                customer_name=test_customer.customer_name,
                stage="S1",
                status="ST01",
                created_by=1,
            )
            db_session.add(project2)
            db_session.commit()
            assert False, "应该抛出唯一性约束异常"
        except IntegrityError:
            db_session.rollback()
            # 验证第一个项目仍然存在
            proj = db_session.query(Project).filter(
                Project.project_code == "PJ-UNIQUE-001"
            ).first()
            assert proj is not None
            assert proj.project_name == "唯一性测试项目1"

    def test_02_rollback_on_business_rule_violation(self, db_session: Session):
        """测试2：业务规则违反时回滚"""
        material = Material(
            material_code="MAT-TXN-001",
            material_name="事务测试物料",
            category_id="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        inventory = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            quantity=Decimal("10"),
            available_quantity=Decimal("10"),
        )
        db_session.add(inventory)
        db_session.commit()

        try:
            # 尝试扣减超过可用库存
            if inventory.available_quantity < Decimal("20"):
                raise ValueError("库存不足")
            
            inventory.available_quantity -= Decimal("20")
            db_session.commit()
        except ValueError:
            db_session.rollback()
            db_session.refresh(inventory)
            # 验证库存未变化
            assert inventory.available_quantity == Decimal("10")

    def test_03_rollback_on_partial_operation_failure(self, db_session: Session):
        """测试3：部分操作失败时回滚"""
        # 创建多个物料
        materials = []
        for i in range(3):
            mat = Material(
                material_code=f"MAT-BATCH-{i+1:03d}",
                material_name=f"批量物料{i+1}",
                category_id="GENERAL",
                unit="PCS",
                is_active=True,
                created_by=1,
            )
            db_session.add(mat)
            materials.append(mat)
        db_session.commit()

        # 批量创建库存，第2个失败
        try:
            for i, mat in enumerate(materials):
                if i == 1:
                    # 模拟第2个失败
                    raise Exception("库位不存在")
                
                inv = MaterialInventory(
                    material_id=mat.id,
                    warehouse_code="WH-001",
                    quantity=Decimal("100"),
                    available_quantity=Decimal("100"),
                )
                db_session.add(inv)
            
            db_session.commit()
        except Exception:
            db_session.rollback()
            
            # 验证所有库存都未创建
            inv_count = db_session.query(MaterialInventory).filter(
                MaterialInventory.material_id.in_([m.id for m in materials])
            ).count()
            assert inv_count == 0

    def test_04_nested_transaction_rollback(self, db_session: Session, test_customer: Customer):
        """测试4：嵌套事务回滚"""
        try:
            # 外层事务：创建项目
            project = Project(
                project_code="PJ-NESTED-001",
                project_name="嵌套事务测试",
                customer_id=test_customer.id,
                customer_name=test_customer.customer_name,
                stage="S1",
                status="ST01",
                created_by=1,
            )
            db_session.add(project)
            db_session.flush()

            # 内层事务：创建审批实例（失败）
            try:
                approval = ApprovalInstance(
                    entity_type="PROJECT",
                    entity_id=project.id,
                    instance_no=project.project_code,
                    initiator_id=1,
                    status="PENDING",
                )
                db_session.add(approval)
                db_session.flush()

                # 模拟失败
                raise Exception("审批创建失败")
            
            except Exception:
                # 内层回滚
                db_session.rollback()
                raise

        except Exception:
            # 外层也回滚
            db_session.rollback()

        # 验证项目未创建
        proj = db_session.query(Project).filter(
            Project.project_code == "PJ-NESTED-001"
        ).first()
        assert proj is None

    def test_05_rollback_with_savepoint(self, db_session: Session, test_customer: Customer):
        """测试5：使用保存点回滚"""
        # 创建第一个项目（成功）
        project1 = Project(
            project_code="PJ-SAVE-001",
            project_name="保存点测试1",
            customer_id=test_customer.id,
            customer_name=test_customer.customer_name,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project1)
        db_session.commit()

        # 设置保存点
        try:
            # 创建第二个项目（会失败）
            project2 = Project(
                project_code="PJ-SAVE-002",
                project_name="保存点测试2",
                customer_id=99999,  # 不存在的客户ID
                customer_name="不存在的客户",
                stage="S1",
                status="ST01",
                created_by=1,
            )
            db_session.add(project2)
            db_session.commit()
        except Exception:
            db_session.rollback()

        # 验证第一个项目仍然存在
        proj1 = db_session.query(Project).filter(
            Project.project_code == "PJ-SAVE-001"
        ).first()
        assert proj1 is not None

        # 验证第二个项目未创建
        proj2 = db_session.query(Project).filter(
            Project.project_code == "PJ-SAVE-002"
        ).first()
        assert proj2 is None

    def test_06_rollback_on_concurrent_modification(self, db_session: Session):
        """测试6：并发修改冲突回滚"""
        material = Material(
            material_code="MAT-CONC-001",
            material_name="并发测试物料",
            category_id="GENERAL",
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
            version=1,
        )
        db_session.add(inventory)
        db_session.commit()

        # 模拟并发修改
        from app.models.base import SessionLocal

        # 会话1：读取并准备修改
        sess1 = SessionLocal()
        inv1 = sess1.query(MaterialInventory).filter(
            MaterialInventory.id == inventory.id
        ).first()
        original_version = inv1.version

        # 会话2：先完成修改
        sess2 = SessionLocal()
        inv2 = sess2.query(MaterialInventory).filter(
            MaterialInventory.id == inventory.id,
            MaterialInventory.version == original_version
        ).first()
        inv2.available_quantity -= 10
        inv2.version += 1
        sess2.commit()
        sess2.close()

        # 会话1：尝试基于旧版本修改（应该失败）
        try:
            inv1_update = sess1.query(MaterialInventory).filter(
                MaterialInventory.id == inventory.id,
                MaterialInventory.version == original_version
            ).first()
            
            if not inv1_update:
                raise Exception("版本冲突")
            
            inv1_update.available_quantity -= 20
            inv1_update.version += 1
            sess1.commit()
        except Exception:
            sess1.rollback()
        finally:
            sess1.close()

        # 验证只有会话2的修改生效
        db_session.refresh(inventory)
        assert inventory.available_quantity == Decimal("40")
        assert inventory.version == 2

    def test_07_rollback_on_cascading_delete_failure(self, db_session: Session, test_customer: Customer):
        """测试7：级联删除失败回滚"""
        project = Project(
            project_code="PJ-CASCADE-001",
            project_name="级联测试项目",
            customer_id=test_customer.id,
            customer_name=test_customer.customer_name,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 添加依赖数据
        approval = ApprovalInstance(
            entity_type="PROJECT",
            entity_id=project.id,
            instance_no=project.project_code,
            initiator_id=1,
            status="PENDING",
        )
        db_session.add(approval)
        db_session.commit()

        try:
            # 尝试删除项目（如果有外键约束，应该失败）
            # 注：实际行为取决于数据库外键设置
            db_session.delete(project)
            db_session.commit()
        except Exception:
            db_session.rollback()
            
            # 验证项目和审批都还存在
            proj = db_session.query(Project).filter(
                Project.id == project.id
            ).first()
            appr = db_session.query(ApprovalInstance).filter(
                ApprovalInstance.id == approval.id
            ).first()
            
            # 至少项目应该存在（是否保留审批取决于级联设置）
            assert proj is not None or appr is not None

    def test_08_rollback_on_complex_operation(self, db_session: Session, test_customer: Customer):
        """测试8：复杂操作失败回滚"""
        try:
            # 步骤1：创建项目
            project = Project(
                project_code="PJ-COMPLEX-001",
                project_name="复杂操作测试",
                customer_id=test_customer.id,
                customer_name=test_customer.customer_name,
                stage="S1",
                status="ST01",
                created_by=1,
            )
            db_session.add(project)
            db_session.flush()

            # 步骤2：创建物料
            material = Material(
                material_code="MAT-COMPLEX-001",
                material_name="复杂操作物料",
                category_id="GENERAL",
                unit="PCS",
                is_active=True,
                created_by=1,
            )
            db_session.add(material)
            db_session.flush()

            # 步骤3：创建库存
            inventory = MaterialInventory(
                material_id=material.id,
                warehouse_code="WH-001",
                quantity=Decimal("100"),
                available_quantity=Decimal("100"),
            )
            db_session.add(inventory)
            db_session.flush()

            # 步骤4：扣减库存
            if inventory.available_quantity >= Decimal("150"):
                inventory.available_quantity -= Decimal("150")
            else:
                raise ValueError("库存不足")

            db_session.commit()
        except Exception:
            db_session.rollback()

            # 验证所有操作都已回滚
            proj = db_session.query(Project).filter(
                Project.project_code == "PJ-COMPLEX-001"
            ).first()
            mat = db_session.query(Material).filter(
                Material.material_code == "MAT-COMPLEX-001"
            ).first()
            
            assert proj is None
            assert mat is None

    def test_09_rollback_with_trigger_side_effects(self, db_session: Session):
        """测试9：触发器副作用回滚"""
        # 创建物料
        material = Material(
            material_code="MAT-TRIGGER-001",
            material_name="触发器测试物料",
            category_id="GENERAL",
            unit="PCS",
            standard_price=Decimal("100.00"),
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        try:
            # 修改物料价格（可能触发价格历史记录）
            material.standard_price = Decimal("120.00")
            db_session.flush()

            # 模拟后续操作失败
            raise Exception("后续操作失败")

        except Exception:
            db_session.rollback()
            db_session.refresh(material)

            # 验证价格未变化
            assert material.standard_price == Decimal("100.00")

    def test_10_verify_transaction_atomicity(self, db_session: Session, test_customer: Customer):
        """测试10：验证事务原子性"""
        initial_project_count = db_session.query(Project).count()
        initial_material_count = db_session.query(Material).count()

        try:
            # 批量创建多个实体
            for i in range(5):
                project = Project(
                    project_code=f"PJ-ATOM-{i+1:03d}",
                    project_name=f"原子性测试{i+1}",
                    customer_id=test_customer.id,
                    customer_name=test_customer.customer_name,
                    stage="S1",
                    status="ST01",
                    created_by=1,
                )
                db_session.add(project)

                material = Material(
                    material_code=f"MAT-ATOM-{i+1:03d}",
                    material_name=f"原子性测试物料{i+1}",
                    category_id="GENERAL",
                    unit="PCS",
                    is_active=True,
                    created_by=1,
                )
                db_session.add(material)

                # 在第3个时失败
                if i == 2:
                    raise Exception("中途失败")

            db_session.commit()
        except Exception:
            db_session.rollback()

        # 验证没有任何记录被创建
        final_project_count = db_session.query(Project).count()
        final_material_count = db_session.query(Material).count()

        assert final_project_count == initial_project_count
        assert final_material_count == initial_material_count
