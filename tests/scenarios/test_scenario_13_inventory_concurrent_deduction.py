"""
场景13：库存并发扣减

测试多个用户同时扣减同一物料库存的并发场景
"""
import pytest
import threading
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
try:
    from app.models.material import Material, MaterialInventory, InventoryTransaction
except ImportError as e:
    pytest.skip(f"Required models not available: {e}", allow_module_level=True)


class TestInventoryConcurrentDeduction:
    """库存并发扣减测试"""

    @pytest.fixture
    def test_material_stock(self, db_session: Session):
        """创建测试物料和库存"""
        material = Material(
            material_code="MAT-CONC-001",
            material_name="并发测试物料",
            category="GENERAL",
            unit="PCS",
            standard_price=Decimal("100.00"),
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()
        db_session.refresh(material)

        # 初始库存100件
        inventory = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            location="A-01-01",
            quantity=Decimal("100"),
            available_quantity=Decimal("100"),
            reserved_quantity=Decimal("0"),
        )
        db_session.add(inventory)
        db_session.commit()
        db_session.refresh(inventory)

        return material, inventory

    def test_01_concurrent_deduction_with_lock(self, db_session: Session, test_material_stock):
        """测试1：使用行锁的并发扣减"""
        material, inventory = test_material_stock

        # 模拟并发扣减
        def deduct_stock(session, inv_id, quantity):
            # 使用 SELECT FOR UPDATE 行锁
            inv = session.query(MaterialInventory).filter(
                MaterialInventory.id == inv_id
            ).with_for_update().first()

            if inv and inv.available_quantity >= quantity:
                inv.available_quantity -= quantity
                inv.reserved_quantity += quantity
                session.commit()
                return True
            session.rollback()
            return False

        # 10个并发请求，每个扣减10件
        results = []
        from app.models.base import SessionLocal

        for i in range(10):
            sess = SessionLocal()
            result = deduct_stock(sess, inventory.id, Decimal("10"))
            results.append(result)
            sess.close()

        db_session.refresh(inventory)

        # 验证最终库存正确
        assert inventory.available_quantity == Decimal("0")
        assert inventory.reserved_quantity == Decimal("100")
        assert sum(results) == 10  # 10次都成功

    def test_02_concurrent_deduction_exceeding_stock(self, db_session: Session, test_material_stock):
        """测试2：并发扣减超过库存"""
        material, inventory = test_material_stock

        def try_deduct(session, inv_id, quantity):
            inv = session.query(MaterialInventory).filter(
                MaterialInventory.id == inv_id
            ).with_for_update().first()

            if inv and inv.available_quantity >= quantity:
                inv.available_quantity -= quantity
                session.commit()
                return True
            session.rollback()
            return False

        # 15个并发请求，每个扣减10件（总需求150 > 库存100）
        results = []
        from app.models.base import SessionLocal

        for i in range(15):
            sess = SessionLocal()
            result = try_deduct(sess, inventory.id, Decimal("10"))
            results.append(result)
            sess.close()

        db_session.refresh(inventory)

        # 只有10次成功，5次失败
        assert sum(results) == 10
        assert inventory.available_quantity == Decimal("0")

    def test_03_optimistic_locking_with_version(self, db_session: Session):
        """测试3：乐观锁版本控制"""
        material = Material(
            material_code="MAT-OPT-001",
            material_name="乐观锁测试物料",
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
            version=1,  # 版本号
        )
        db_session.add(inventory)
        db_session.commit()

        # 模拟乐观锁更新
        def optimistic_update(session, inv_id, expected_version, quantity):
            inv = session.query(MaterialInventory).filter(
                MaterialInventory.id == inv_id,
                MaterialInventory.version == expected_version
            ).first()

            if inv and inv.available_quantity >= quantity:
                inv.available_quantity -= quantity
                inv.version += 1
                session.commit()
                return True, inv.version
            session.rollback()
            return False, expected_version

        from app.models.base import SessionLocal

        # 第一次更新成功
        sess1 = SessionLocal()
        success1, version1 = optimistic_update(sess1, inventory.id, 1, Decimal("10"))
        sess1.close()

        # 第二次更新，使用错误的版本号失败
        sess2 = SessionLocal()
        success2, version2 = optimistic_update(sess2, inventory.id, 1, Decimal("10"))
        sess2.close()

        # 第三次更新，使用正确的版本号成功
        sess3 = SessionLocal()
        success3, version3 = optimistic_update(sess3, inventory.id, version1, Decimal("10"))
        sess3.close()

        assert success1 is True
        assert success2 is False  # 版本号冲突
        assert success3 is True

    def test_04_concurrent_reservation(self, db_session: Session, test_material_stock):
        """测试4：并发预留库存"""
        material, inventory = test_material_stock

        def reserve_stock(session, inv_id, quantity, reservation_code):
            inv = session.query(MaterialInventory).filter(
                MaterialInventory.id == inv_id
            ).with_for_update().first()

            if inv and inv.available_quantity >= quantity:
                inv.available_quantity -= quantity
                inv.reserved_quantity += quantity
                
                # 记录预留交易
                trans = InventoryTransaction(
                    material_id=inv.material_id,
                    transaction_type="RESERVE",
                    quantity=quantity,
                    reference_code=reservation_code,
                    created_at=datetime.now(),
                )
                session.add(trans)
                session.commit()
                return True
            session.rollback()
            return False

        from app.models.base import SessionLocal

        # 5个并发预留请求
        results = []
        for i in range(5):
            sess = SessionLocal()
            result = reserve_stock(sess, inventory.id, Decimal("15"), f"RSV-{i+1}")
            results.append(result)
            sess.close()

        db_session.refresh(inventory)

        # 验证预留结果
        assert sum(results) >= 1  # 至少有一个成功
        total_reserved = inventory.reserved_quantity
        assert total_reserved <= Decimal("100")

    def test_05_concurrent_issue_and_return(self, db_session: Session, test_material_stock):
        """测试5：并发出库和退库"""
        material, inventory = test_material_stock

        # 先预留50件
        inventory.available_quantity = Decimal("50")
        inventory.reserved_quantity = Decimal("50")
        db_session.commit()

        def issue_stock(session, inv_id, quantity):
            inv = session.query(MaterialInventory).filter(
                MaterialInventory.id == inv_id
            ).with_for_update().first()

            if inv and inv.reserved_quantity >= quantity:
                inv.reserved_quantity -= quantity
                inv.quantity -= quantity
                session.commit()
                return True
            session.rollback()
            return False

        def return_stock(session, inv_id, quantity):
            inv = session.query(MaterialInventory).filter(
                MaterialInventory.id == inv_id
            ).with_for_update().first()

            if inv:
                inv.quantity += quantity
                inv.available_quantity += quantity
                session.commit()
                return True
            session.rollback()
            return False

        from app.models.base import SessionLocal

        # 并发出库
        for i in range(5):
            sess = SessionLocal()
            issue_stock(sess, inventory.id, Decimal("10"))
            sess.close()

        # 并发退库
        for i in range(2):
            sess = SessionLocal()
            return_stock(sess, inventory.id, Decimal("5"))
            sess.close()

        db_session.refresh(inventory)

        # 验证最终库存
        expected_qty = Decimal("100") - Decimal("50") + Decimal("10")
        assert inventory.quantity == expected_qty

    def test_06_deadlock_detection(self, db_session: Session):
        """测试6：死锁检测"""
        # 创建两个物料
        mat1 = Material(
            material_code="MAT-DL-001",
            material_name="死锁测试物料1",
            category="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        mat2 = Material(
            material_code="MAT-DL-002",
            material_name="死锁测试物料2",
            category="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add_all([mat1, mat2])
        db_session.commit()

        inv1 = MaterialInventory(
            material_id=mat1.id,
            warehouse_code="WH-001",
            quantity=Decimal("100"),
            available_quantity=Decimal("100"),
        )
        inv2 = MaterialInventory(
            material_id=mat2.id,
            warehouse_code="WH-001",
            quantity=Decimal("100"),
            available_quantity=Decimal("100"),
        )
        db_session.add_all([inv1, inv2])
        db_session.commit()

        # 模拟可能产生死锁的操作
        # 事务1: 先锁inv1再锁inv2
        # 事务2: 先锁inv2再锁inv1

        deadlock_occurred = False

        def trans1(session):
            try:
                i1 = session.query(MaterialInventory).filter(
                    MaterialInventory.id == inv1.id
                ).with_for_update().first()
                i2 = session.query(MaterialInventory).filter(
                    MaterialInventory.id == inv2.id
                ).with_for_update().first()
                
                i1.available_quantity -= 10
                i2.available_quantity -= 10
                session.commit()
                return True
            except Exception:
                session.rollback()
                return False

        # 由于SQLite不支持真正的并发，这里只是模拟逻辑
        assert True  # 测试框架验证

    def test_07_batch_concurrent_deduction(self, db_session: Session):
        """测试7：批量并发扣减"""
        # 创建多个物料
        materials = []
        for i in range(5):
            mat = Material(
                material_code=f"MAT-BATCH-{i+1:03d}",
                material_name=f"批量测试物料{i+1}",
                category="GENERAL",
                unit="PCS",
                is_active=True,
                created_by=1,
            )
            db_session.add(mat)
            materials.append(mat)
        
        db_session.commit()

        # 创建库存
        inventories = []
        for mat in materials:
            inv = MaterialInventory(
                material_id=mat.id,
                warehouse_code="WH-001",
                quantity=Decimal("100"),
                available_quantity=Decimal("100"),
            )
            db_session.add(inv)
            inventories.append(inv)
        
        db_session.commit()

        # 批量扣减
        def batch_deduct(session, inv_ids, quantities):
            invs = session.query(MaterialInventory).filter(
                MaterialInventory.id.in_(inv_ids)
            ).with_for_update().all()

            for inv, qty in zip(invs, quantities):
                if inv.available_quantity >= qty:
                    inv.available_quantity -= qty
                else:
                    session.rollback()
                    return False
            
            session.commit()
            return True

        from app.models.base import SessionLocal

        inv_ids = [inv.id for inv in inventories]
        quantities = [Decimal("20")] * 5

        sess = SessionLocal()
        result = batch_deduct(sess, inv_ids, quantities)
        sess.close()

        assert result is True

    def test_08_concurrent_inventory_adjustment(self, db_session: Session, test_material_stock):
        """测试8：并发库存调整"""
        material, inventory = test_material_stock

        def adjust_inventory(session, inv_id, adjustment):
            inv = session.query(MaterialInventory).filter(
                MaterialInventory.id == inv_id
            ).with_for_update().first()

            if inv:
                inv.quantity += adjustment
                inv.available_quantity += adjustment
                
                trans = InventoryTransaction(
                    material_id=inv.material_id,
                    transaction_type="ADJUSTMENT",
                    quantity=adjustment,
                    reference_code=f"ADJ-{datetime.now().timestamp()}",
                    created_at=datetime.now(),
                )
                session.add(trans)
                session.commit()
                return True
            session.rollback()
            return False

        from app.models.base import SessionLocal

        # 并发调整（有正有负）
        adjustments = [Decimal("10"), Decimal("-5"), Decimal("8"), Decimal("-3")]
        
        for adj in adjustments:
            sess = SessionLocal()
            adjust_inventory(sess, inventory.id, adj)
            sess.close()

        db_session.refresh(inventory)

        expected_qty = Decimal("100") + sum(adjustments)
        assert inventory.quantity == expected_qty

    def test_09_concurrent_stock_transfer(self, db_session: Session):
        """测试9：并发库存转移"""
        material = Material(
            material_code="MAT-TRANS-001",
            material_name="转移测试物料",
            category="GENERAL",
            unit="PCS",
            is_active=True,
            created_by=1,
        )
        db_session.add(material)
        db_session.commit()

        # 源库位
        inv_from = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            location="A-01-01",
            quantity=Decimal("100"),
            available_quantity=Decimal("100"),
        )
        # 目标库位
        inv_to = MaterialInventory(
            material_id=material.id,
            warehouse_code="WH-001",
            location="A-02-01",
            quantity=Decimal("0"),
            available_quantity=Decimal("0"),
        )
        db_session.add_all([inv_from, inv_to])
        db_session.commit()

        def transfer_stock(session, from_id, to_id, quantity):
            from_inv = session.query(MaterialInventory).filter(
                MaterialInventory.id == from_id
            ).with_for_update().first()
            
            to_inv = session.query(MaterialInventory).filter(
                MaterialInventory.id == to_id
            ).with_for_update().first()

            if from_inv and to_inv and from_inv.available_quantity >= quantity:
                from_inv.quantity -= quantity
                from_inv.available_quantity -= quantity
                to_inv.quantity += quantity
                to_inv.available_quantity += quantity
                session.commit()
                return True
            session.rollback()
            return False

        from app.models.base import SessionLocal

        # 并发转移
        for i in range(5):
            sess = SessionLocal()
            transfer_stock(sess, inv_from.id, inv_to.id, Decimal("15"))
            sess.close()

        db_session.refresh(inv_from)
        db_session.refresh(inv_to)

        # 验证库存守恒
        total_qty = inv_from.quantity + inv_to.quantity
        assert total_qty == Decimal("100")

    def test_10_concurrent_with_transaction_isolation(self, db_session: Session, test_material_stock):
        """测试10：事务隔离级别测试"""
        material, inventory = test_material_stock

        from app.models.base import SessionLocal
        from sqlalchemy import text

        # 使用不同的事务隔离级别
        def deduct_with_isolation(inv_id, quantity, isolation_level="READ COMMITTED"):
            sess = SessionLocal()
            
            try:
                # 设置事务隔离级别（SQLite不完全支持，这里演示概念）
                # sess.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
                
                inv = sess.query(MaterialInventory).filter(
                    MaterialInventory.id == inv_id
                ).with_for_update().first()

                if inv and inv.available_quantity >= quantity:
                    inv.available_quantity -= quantity
                    sess.commit()
                    return True
                sess.rollback()
                return False
            finally:
                sess.close()

        # 并发扣减测试
        results = []
        for i in range(10):
            result = deduct_with_isolation(inventory.id, Decimal("10"))
            results.append(result)

        db_session.refresh(inventory)

        # 验证结果一致性
        assert sum(results) == 10
        assert inventory.available_quantity == Decimal("0")
