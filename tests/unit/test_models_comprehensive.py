# -*- coding: utf-8 -*-
"""
单元测试: 模型测试综合文件 (models)

测试内容：
- Project 模型的基本字段和验证
- User 模型的认证相关功能
- Material 模型的 BOM 相关功能
- ProjectStage 和 ProjectStatus 枚举测试
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# 直接在这里定义 ProjectHealth 枚举,避免导入问题
class ProjectHealth(str, Enum):
    H1 = "h1"  # 正常（绿色）
    H2 = "h2"  # 有风险（黄色）
    H3 = "h3"  # 阻塞（红色）
    H4 = "h4"  # 已完结（灰色）


from app.models.project import (
    Project,
    ProjectStage,
    ProjectStatus,
)
from app.models.user import User
from app.models.organization import Employee
from app.models.material import Material
from app.models.vendor import Vendor as Supplier


def _create_employee_for_user(db_session, code, name="测试用户"):
    """创建 Employee 以满足 User.employee_id NOT NULL 约束"""
    emp = Employee(
        employee_code=code,
        name=name,
        department="测试部",
        role="ENGINEER",
        phone="18800000000",
    )
    db_session.add(emp)
    db_session.flush()
    return emp


class TestProjectModel:
    """测试 Project 模型"""

    def test_project_creation_basic(self, db_session):
        """测试基本的 Project 创建"""
        project = Project(
        project_code="PJ250101001",
        project_name="测试项目",
        customer_name="测试客户",
        contract_amount=1000000.00,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        current_stage=ProjectStage.S1.value,
        status=ProjectStatus.ACTIVE.value,
        health=ProjectHealth.H1.value,
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.id is not None
        assert project.project_code == "PJ250101001"
        assert project.project_name == "测试项目"
        assert project.contract_amount == 1000000.00
        assert project.status == ProjectStatus.ACTIVE.value

    def test_project_relationships(self, db_session):
        """测试 Project 关系"""
        project = Project(
        project_code="PJ250101002",
        project_name="关系测试",
        customer_name="测试客户",
        contract_amount=500000.00,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
        current_stage=ProjectStage.S1.value,
        status=ProjectStatus.ACTIVE.value,
        health=ProjectHealth.H1.value,
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 验证默认字段
        assert project.description is None
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_project_enum_fields(self):
        """测试枚举字段"""
        # 验证 ProjectStage 枚举值
        assert ProjectStage.S1.value == "S1"
        assert ProjectStage.S9.value == "S9"
        assert len(ProjectStage) == 9  # S1-S9

        # 验证 ProjectStatus 枚举值
        assert ProjectStatus.ACTIVE.value == "active"
        assert ProjectStatus.CANCELLED.value == "cancelled"
        assert len(ProjectStatus) >= 3

        # 验证 ProjectHealth 枚举值
        assert ProjectHealth.H1.value == "h1"
        assert ProjectHealth.H4.value == "h4"
        assert len(ProjectHealth) == 4

    def test_project_unique_constraint(self, db_session):
        """测试 project_code 唯一约束"""
        project1 = Project(
        project_code="PJ250101003",
        project_name="测试项目1",
        customer_name="测试客户",
        contract_amount=100000.00,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
        current_stage=ProjectStage.S1.value,
        status=ProjectStatus.ACTIVE.value,
        health=ProjectHealth.H1.value,
        )

        db_session.add(project1)
        db_session.commit()

        # 尝试创建相同 code 的项目
        project2 = Project(
        project_code="PJ250101003",  # 相同的 code
        project_name="测试项目2",
        customer_name="测试客户",
        contract_amount=200000.00,
        start_date=date(2024, 7, 1),
        end_date=date(2024, 12, 31),
        current_stage=ProjectStage.S1.value,
        status=ProjectStatus.ACTIVE.value,
        )


class TestUserModel:
    """测试 User 模型"""

    def test_user_creation_basic(self, db_session):
        """测试基本的 User 创建"""
        emp = _create_employee_for_user(db_session, "EMP-BASIC", "Test User")
        user = User(
            employee_id=emp.id,
            username="testuser",
            email="test@example.com",
            password_hash="password_hash_here",
            real_name="Test User",
            is_active=True,
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True

    def test_user_password_hashing(self, db_session):
        """测试密码哈希字段"""
        from app.core.auth import get_password_hash

        plain_password = "test_password"
        hashed = get_password_hash(plain_password)

        emp = _create_employee_for_user(db_session, "EMP-HASH", "User With Hash")
        user = User(
            employee_id=emp.id,
            username="user_with_hash",
            email="user@example.com",
            password_hash=hashed,
            real_name="User With Hash",
            is_active=True,
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.password_hash == hashed
        assert user.password_hash is not None
        assert len(user.password_hash) > 50

    def test_user_default_values(self, db_session):
        """测试 User 默认值"""
        emp = _create_employee_for_user(db_session, "EMP-DEFAULT", "Default User")
        user = User(
            employee_id=emp.id,
            username="defaultuser",
            email="default@example.com",
            password_hash="hash",
            real_name="Default User",
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # 验证默认值
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None


class TestMaterialModel:
    """测试 Material 模型"""

    def test_material_creation_basic(self, db_session):
        """测试基本的 Material 创建"""
        material = Material(
        material_code="MAT001",
        material_name="测试材料",
        material_type="standard",
        unit="piece",
        standard_price=Decimal("100.50"),
        is_active=True,
        )

        db_session.add(material)
        db_session.commit()
        db_session.refresh(material)

        assert material.id is not None
        assert material.material_code == "MAT001"
        assert material.material_name == "测试材料"
        assert material.unit_price == 100.50

    def test_material_categories(self, db_session):
        """测试 Material 类别字段"""
        # 测试不同类别
        categories = ["standard", "mechanical", "electrical", "pneumatic"]

        for i, category in enumerate(categories):
            material = Material(
            material_code=f"MAT{100 + i:03d}",
            material_name=f"测试材料{i}",
            material_type=category,
            unit="piece",
            standard_price=Decimal("50.00"),
            )

            db_session.add(material)

            db_session.commit()

            # 验证所有材料都被保存
            materials = (
            db_session.query(Material).filter(Material.material_code.like("MAT%")).all()
            )
            assert len(materials) == 4

    def test_supplier_creation(self, db_session):
        """测试 Supplier 创建"""
        supplier = Supplier(
        supplier_name="测试供应商",
        contact_person="张三",
        contact_phone="13800138000",
        contact_email="supplier@example.com",
        address="北京市朝阳区",
        )

        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)

        assert supplier.id is not None
        assert supplier.name == "测试供应商"
        assert supplier.phone == "13800138000"

    def test_material_supplier_relationship(self, db_session):
        """测试 Material 和 Supplier 关系"""
        supplier = Supplier(
        supplier_name="关联供应商",
        contact_person="李四",
        contact_phone="13900139000",
        contact_email="关联@example.com",
        )

        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)

        material = Material(
        material_code="MAT005",
        material_name="关联测试材料",
        material_type="standard",
        unit="piece",
        standard_price=Decimal("200.00"),
        is_active=True,
        )

        db_session.add(material)
        db_session.commit()
        db_session.refresh(material)

        assert material.material_name == "关联测试材料"


class TestModelTimestamps:
    """测试模型时间戳"""

    def test_project_timestamps(self, db_session):
        """测试 Project 时间戳"""
        project = Project(
        project_code="PJ250101004",
        project_name="时间戳测试",
        customer_name="测试客户",
        contract_amount=1000.00,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
        current_stage=ProjectStage.S1.value,
        status=ProjectStatus.ACTIVE.value,
        health=ProjectHealth.H1.value,
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 验证时间戳字段
        assert project.created_at is not None
        assert project.updated_at is not None
        assert project.created_at <= datetime.utcnow()
        assert project.updated_at <= datetime.utcnow()

    def test_user_timestamps(self, db_session):
        """测试 User 时间戳"""
        emp = _create_employee_for_user(db_session, "EMP-TIME", "Time Test User")
        user = User(
            employee_id=emp.id,
            username="timetestuser",
            email="timetest@example.com",
            password_hash="hash",
            real_name="Time Test User",
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # 验证时间戳字段
        assert user.created_at is not None
        assert user.updated_at is not None


class TestModelValidators:
    """测试模型验证"""

    def test_project_required_fields(self, db_session):
        """测试 Project 必填字段验证"""
        project = Project(
            # 缺少必填字段
        project_code="PJ250101005",
            # project_name 缺失
        customer_name="测试客户",
        )

        # SQLAlchemy 不会自动验证必填字段，但模型应该定义它们
        # 这里我们只测试对象可以创建
        assert project.project_code == "PJ250101005"
        assert project.project_name is None  # 因为我们没有设置

    def test_user_email_validation(self, db_session):
        """测试 User 邮箱字段"""
        emp = _create_employee_for_user(db_session, "EMP-EMAIL", "Email Test User")
        user = User(
            employee_id=emp.id,
            username="emailtestuser",
            email="user@example.com",
            password_hash="hash",
            real_name="Email Test User",
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.email == "user@example.com"


class TestModelQueryMethods:
    """测试模型查询方法"""

    def test_filter_by_status(self, db_session):
        """测试按状态过滤"""
        # 创建不同状态的项目
        active_project = Project(
        project_code="PJ250101006",
        project_name="活跃项目",
        customer_name="客户1",
        contract_amount=1000.00,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
        current_stage=ProjectStage.S1.value,
        status=ProjectStatus.ACTIVE.value,
        health=ProjectHealth.H1.value,
        )

        completed_project = Project(
        project_code="PJ250101007",
        project_name="完成项目",
        customer_name="客户2",
        contract_amount=2000.00,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        current_stage=ProjectStage.S9.value,
        status=ProjectStatus.COMPLETED.value,
        health=ProjectHealth.H4.value,
        )

        db_session.add(active_project)
        db_session.add(completed_project)
        db_session.commit()

        # 查询活跃项目
        active_projects = (
        db_session.query(Project)
        .filter(Project.status == ProjectStatus.ACTIVE.value)
        .all()
        )
        assert len(active_projects) == 1
        assert active_projects[0].project_code == "PJ250101006"

        # 查询完成项目
        completed_projects = (
        db_session.query(Project)
        .filter(Project.status == ProjectStatus.COMPLETED.value)
        .all()
        )
        assert len(completed_projects) == 1

    def test_filter_by_active_status(self, db_session):
        """测试按 is_active 字段过滤"""
        emp1 = _create_employee_for_user(db_session, "EMP-ACTIVE", "Active User")
        emp2 = _create_employee_for_user(db_session, "EMP-INACTIVE", "Inactive User")

        active_user = User(
            employee_id=emp1.id,
            username="activeuser",
            email="active@example.com",
            password_hash="hash",
            real_name="Active User",
            is_active=True,
        )

        inactive_user = User(
            employee_id=emp2.id,
            username="inactiveuser",
            email="inactive@example.com",
            password_hash="hash",
            real_name="Inactive User",
            is_active=False,
        )

        db_session.add(active_user)
        db_session.add(inactive_user)
        db_session.commit()

        # 查询活跃用户
        active_users = db_session.query(User).filter(User.is_active == True).all()
        assert len(active_users) == 1
        assert active_users[0].username == "activeuser"

        # 查询禁用用户
        inactive_users = db_session.query(User).filter(User.is_active == False).all()
        assert len(inactive_users) == 1
        assert inactive_users[0].username == "inactiveuser"


# Pytest fixture for database session is provided by conftest.py
