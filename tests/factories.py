# -*- coding: utf-8 -*-
"""
测试数据工厂

使用 factory 创建测试数据，确保测试数据的一致性和可重复性。

使用示例：
    from tests.factories import UserFactory, ProjectFactory

    # 创建单个对象
    user = UserFactory()

    # 创建多个对象
    users = UserFactory.create_batch(5)

    # 自定义属性
    admin = UserFactory(is_superuser=True, username='admin')

    # 创建关联对象
    project = ProjectFactory(customer=CustomerFactory())
"""

import random
from datetime import date, timedelta
from decimal import Decimal

import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.core.security import get_password_hash
from app.models.base import get_session
from app.models.budget import ProjectBudget, ProjectBudgetItem
from app.models.project.financial import ProjectCost
from app.models.material import BomHeader, BomItem, Material, MaterialCategory
from app.models.acceptance import AcceptanceOrder, AcceptanceTemplate, AcceptanceIssue
from app.models.organization import Department, Employee
from app.models.project import (
    Customer,
    Machine,
    Project,
    ProjectMember,
    ProjectMilestone,
    ProjectPaymentPlan,
    ProjectStage,
    ProjectTemplate,
    ProjectTemplateVersion,
)
from app.models.purchase import PurchaseOrder, PurchaseRequest
from app.models.sales import (
    ApprovalWorkflow,
    ApprovalWorkflowStep,
    Contract,
    Lead,
    Opportunity,
    Quote,
)
from app.models.ecn import Ecn
from app.models.user import Role, User
from app.models.vendor import Vendor

# ============== 基础配置 ==============


class BaseFactory(SQLAlchemyModelFactory):
    """基础工厂类，提供数据库会话"""

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """重写创建方法，使用应用的数据库会话"""
        with get_session() as session:
            obj = model_class(*args, **kwargs)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            # 分离对象，避免会话关闭后无法访问
            session.expunge(obj)
            return obj


# ============== 组织架构 ==============


class DepartmentFactory(BaseFactory):
    """部门工厂"""

    class Meta:
        model = Department

    dept_code = factory.Sequence(lambda n: f"DEPT{n:04d}")
    dept_name = factory.Sequence(lambda n: f"测试部门{n}")
    level = 1
    sort_order = factory.Sequence(lambda n: n)
    is_active = True


class EmployeeFactory(BaseFactory):
    """员工工厂"""

    class Meta:
        model = Employee

    employee_code = factory.Sequence(lambda n: f"EMP{n:05d}")
    name = factory.Sequence(lambda n: f"测试员工{n}")
    department = "技术部"
    role = "ENGINEER"
    phone = factory.LazyFunction(lambda: f"138{random.randint(10000000, 99999999)}")
    is_active = True
    employment_status = "active"
    employment_type = "regular"


# ============== 用户与权限 ==============


class UserFactory(BaseFactory):
    """用户工厂"""

    class Meta:
        model = User

    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda o: o.employee.id)
    username = factory.Sequence(lambda n: f"testuser{n}")
    password_hash = factory.LazyFunction(lambda: get_password_hash("test123456"))
    real_name = factory.LazyAttribute(lambda o: o.employee.name)
    department = factory.LazyAttribute(lambda o: o.employee.department)
    is_active = True
    is_superuser = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """确保先创建 employee"""
        employee = kwargs.pop("employee", None)
        if employee is None:
            employee = EmployeeFactory()
        kwargs["employee_id"] = employee.id
        kwargs.setdefault("real_name", employee.name)
        kwargs.setdefault("department", employee.department)

        with get_session() as session:
            obj = model_class(*args, **kwargs)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            session.expunge(obj)
            return obj


class AdminUserFactory(UserFactory):
    """管理员用户工厂"""

    username = factory.Sequence(lambda n: f"admin{n}")
    is_superuser = True


class RoleFactory(BaseFactory):
    """角色工厂"""

    class Meta:
        model = Role

    role_code = factory.Sequence(lambda n: f"ROLE_{n:04d}")
    role_name = factory.Sequence(lambda n: f"测试角色{n}")
    description = "测试角色描述"
    data_scope = "OWN"
    is_system = False
    is_active = True


# ============== 客户 ==============


class CustomerFactory(BaseFactory):
    """客户工厂"""

    class Meta:
        model = Customer

    customer_code = factory.Sequence(lambda n: f"CUST{n:05d}")
    customer_name = factory.Sequence(lambda n: f"测试客户公司{n}")
    short_name = factory.Sequence(lambda n: f"客户{n}")
    customer_type = "ENTERPRISE"
    industry = "电子制造"
    contact_person = factory.Sequence(lambda n: f"联系人{n}")
    contact_phone = factory.LazyFunction(
        lambda: f"139{random.randint(10000000, 99999999)}"
    )
    credit_level = "A"
    status = "ACTIVE"


# ============== 项目 ==============


class ProjectFactory(BaseFactory):
    """项目工厂"""

    class Meta:
        model = Project

    project_code = factory.Sequence(
        lambda n: f"PJ{date.today().strftime('%y%m%d')}{n:06d}"
    )
    project_name = factory.Sequence(lambda n: f"测试项目{n}")
    short_name = factory.Sequence(lambda n: f"项目{n}")
    project_type = "NEW"
    product_category = "ICT"
    industry = "电子"
    project_category = "销售"
    stage = "S1"
    status = "ST01"
    health = "H1"
    progress_pct = Decimal("0.00")
    planned_start_date = factory.LazyFunction(lambda: date.today())
    planned_end_date = factory.LazyFunction(lambda: date.today() + timedelta(days=90))

    @factory.lazy_attribute
    def customer_name(self):
        return "客户名称"


class ProjectWithCustomerFactory(ProjectFactory):
    """带客户的项目工厂"""

    customer = factory.SubFactory(CustomerFactory)
    customer_id = factory.LazyAttribute(lambda o: o.customer.id)
    customer_name = factory.LazyAttribute(lambda o: o.customer.customer_name)


class MachineFactory(BaseFactory):
    """设备/机台工厂"""

    class Meta:
        model = Machine

    project = factory.SubFactory(ProjectFactory)
    project_id = factory.LazyAttribute(lambda o: o.project.id)
    machine_code = factory.Sequence(
        lambda n: f"PN{n:06d}"
    )
    machine_name = factory.Sequence(lambda n: f"测试机台{n}")
    machine_type = "TEST_EQUIPMENT"
    status = "DESIGN"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        project = kwargs.pop("project", None)
        if project is None and "project_id" not in kwargs:
            project = ProjectFactory()
            kwargs["project_id"] = project.id
        elif project is not None:
            kwargs["project_id"] = project.id
        with get_session() as session:
            obj = model_class(*args, **kwargs)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            session.expunge(obj)
            return obj


class ProjectStageFactory(BaseFactory):
    """项目阶段工厂"""

    class Meta:
        model = ProjectStage

    project = factory.SubFactory("tests.factories.ProjectWithCustomerFactory")
    stage_code = factory.Sequence(lambda n: f"S{n}")
    stage_name = factory.Sequence(lambda n: f"阶段{n}")
    stage_order = factory.Sequence(lambda n: n)
    is_active = True


class ProjectMilestoneFactory(BaseFactory):
    """项目里程碑工厂"""

    class Meta:
        model = ProjectMilestone

    milestone_name = factory.Sequence(lambda n: f"里程碑{n}")
    planned_date = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    status = "PENDING"


class ProjectTemplateFactory(BaseFactory):
    """项目模板工厂"""

    class Meta:
        model = ProjectTemplate

    template_code = factory.Sequence(lambda n: f"TPL{n:05d}")
    template_name = factory.Sequence(lambda n: f"测试模板{n}")
    project_type = "NEW"
    product_category = "ICT"
    industry = "电子"
    default_stage = "S1"
    default_status = "ST01"
    default_health = "H1"
    is_active = True
    usage_count = 0


class ProjectTemplateVersionFactory(BaseFactory):
    """项目模板版本工厂"""

    class Meta:
        model = ProjectTemplateVersion

    version_no = factory.Sequence(lambda n: f"V{n}")
    status = "DRAFT"
    template_config = "{}"
    release_notes = factory.Sequence(lambda n: f"版本说明{n}")


class ProjectPaymentPlanFactory(BaseFactory):
    """项目付款计划工厂"""

    class Meta:
        model = ProjectPaymentPlan

    payment_no = factory.Sequence(lambda n: n)
    payment_name = factory.Sequence(lambda n: f"第{n}期款项")
    payment_type = "ADVANCE"
    payment_ratio = Decimal("30.00")
    planned_amount = factory.LazyFunction(
        lambda: Decimal(str(random.uniform(10000, 100000)))
    )
    actual_amount = Decimal("0.00")
    planned_date = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    status = "PENDING"


class ProjectMemberFactory(BaseFactory):
    """项目成员工厂"""

    class Meta:
        model = ProjectMember

    role_code = "ENGINEER"
    allocation_pct = Decimal("100.00")
    start_date = factory.LazyFunction(lambda: date.today())
    end_date = factory.LazyFunction(lambda: date.today() + timedelta(days=90))
    commitment_level = "FULL"
    reporting_to_pm = True
    is_active = True


# ============== 物料与BOM ==============


class MaterialCategoryFactory(BaseFactory):
    """物料类别工厂"""

    class Meta:
        model = MaterialCategory

    category_code = factory.Sequence(lambda n: f"CAT{n:03d}")
    category_name = factory.Sequence(lambda n: f"物料类别{n}")
    parent_id = None
    level = 1
    is_active = True


# Supplier模型已废弃，使用Vendor代替
# class SupplierFactory(BaseFactory):
#     """供应商工厂"""
#
#     class Meta:
#         model = Supplier
#
#     supplier_code = factory.Sequence(lambda n: f"SUP{n:05d}")
#     supplier_name = factory.Sequence(lambda n: f"测试供应商{n}")
#     supplier_short_name = factory.Sequence(lambda n: f"供应商{n}")
#     supplier_type = "STANDARD"
#     contact_person = factory.Sequence(lambda n: f"供应商联系人{n}")
#     contact_phone = factory.LazyFunction(
#         lambda: f"137{random.randint(10000000, 99999999)}"
#     )
#     status = "APPROVED"


class MaterialFactory(BaseFactory):
    """物料工厂"""

    class Meta:
        model = Material

    material_code = factory.Sequence(lambda n: f"MAT{n:06d}")
    material_name = factory.Sequence(lambda n: f"测试物料{n}")
    material_type = "STANDARD"
    specification = "规格A"
    unit = "个"
    unit_price = factory.LazyFunction(lambda: Decimal(str(random.uniform(10, 1000))))
    is_active = True


class BomHeaderFactory(BaseFactory):
    """BOM表头工厂"""

    class Meta:
        model = BomHeader

    bom_code = factory.Sequence(
        lambda n: f"BOM{date.today().strftime('%y%m%d')}{n:03d}"
    )
    bom_name = factory.Sequence(lambda n: f"测试BOM{n}")
    version = "1.0"
    status = "DRAFT"


class BomItemFactory(BaseFactory):
    """BOM明细工厂"""

    class Meta:
        model = BomItem

    item_no = factory.Sequence(lambda n: n)
    quantity = factory.LazyFunction(lambda: Decimal(str(random.randint(1, 100))))
    unit = "个"


# ============== 采购 ==============


class PurchaseOrderFactory(BaseFactory):
    """采购订单工厂"""

    class Meta:
        model = PurchaseOrder

    order_no = factory.Sequence(lambda n: f"PO{date.today().strftime('%y%m%d')}{n:04d}")
    order_type = "NORMAL"
    order_title = factory.Sequence(lambda n: f"采购订单{n}")
    status = "DRAFT"
    total_amount = factory.LazyFunction(
        lambda: Decimal(str(random.uniform(1000, 100000)))
    )
    required_date = factory.LazyFunction(lambda: date.today() + timedelta(days=14))


class PurchaseRequestFactory(BaseFactory):
    """采购申请工厂"""

    class Meta:
        model = PurchaseRequest

    request_no = factory.Sequence(
        lambda n: f"PR{date.today().strftime('%y%m%d')}{n:04d}"
    )
    request_type = "PROJECT"
    request_reason = "项目物料采购"
    status = "DRAFT"
    required_date = factory.LazyFunction(lambda: date.today() + timedelta(days=14))


# ============== 销售 ==============


class LeadFactory(BaseFactory):
    """销售线索工厂"""

    class Meta:
        model = Lead

    lead_code = factory.Sequence(
        lambda n: f"LD{date.today().strftime('%y%m%d')}{n:05d}"
    )
    lead_name = factory.Sequence(lambda n: f"测试线索{n}")
    company_name = factory.Sequence(lambda n: f"潜在客户公司{n}")
    contact_name = factory.Sequence(lambda n: f"联系人{n}")
    contact_phone = factory.LazyFunction(
        lambda: f"136{random.randint(10000000, 99999999)}"
    )
    source = "WEBSITE"
    status = "NEW"
    estimated_amount = factory.LazyFunction(
        lambda: Decimal(str(random.uniform(10000, 1000000)))
    )


class OpportunityFactory(BaseFactory):
    """商机工厂"""

    class Meta:
        model = Opportunity

    opportunity_code = factory.Sequence(
        lambda n: f"OP{date.today().strftime('%y%m%d')}{n:05d}"
    )
    opportunity_name = factory.Sequence(lambda n: f"测试商机{n}")
    stage = "INITIAL"
    status = "ACTIVE"
    probability = 30
    expected_amount = factory.LazyFunction(
        lambda: Decimal(str(random.uniform(50000, 2000000)))
    )
    expected_close_date = factory.LazyFunction(
        lambda: date.today() + timedelta(days=60)
    )


class QuoteFactory(BaseFactory):
    """报价单工厂"""

    class Meta:
        model = Quote

    quote_code = factory.Sequence(
        lambda n: f"QT{date.today().strftime('%y%m%d')}{n:05d}"
    )
    quote_name = factory.Sequence(lambda n: f"测试报价{n}")
    version = 1
    status = "DRAFT"
    total_amount = factory.LazyFunction(
        lambda: Decimal(str(random.uniform(50000, 2000000)))
    )
    valid_until = factory.LazyFunction(lambda: date.today() + timedelta(days=30))


class ContractFactory(BaseFactory):
    """合同工厂"""

    class Meta:
        model = Contract

    contract_code = factory.Sequence(
        lambda n: f"CT{date.today().strftime('%y%m%d')}{n:05d}"
    )
    contract_name = factory.Sequence(lambda n: f"测试合同{n}")
    contract_type = "SALES"
    status = "DRAFT"
    contract_amount = factory.LazyFunction(
        lambda: Decimal(str(random.uniform(100000, 5000000)))
    )
    signing_date = factory.LazyFunction(lambda: date.today())
    effective_date = factory.LazyFunction(lambda: date.today())
    expiry_date = factory.LazyFunction(lambda: date.today() + timedelta(days=365))


# ============== 预算 ==============


class ProjectBudgetFactory(BaseFactory):
    """项目预算工厂"""

    class Meta:
        model = ProjectBudget

    budget_no = factory.Sequence(
        lambda n: f"BG{date.today().strftime('%y%m%d')}{n:04d}"
    )
    budget_type = "INITIAL"
    total_amount = factory.LazyFunction(
        lambda: Decimal(str(random.uniform(100000, 1000000)))
    )
    budget_year = factory.LazyFunction(lambda: date.today().year)
    version = 1
    status = "DRAFT"


class ProjectBudgetItemFactory(BaseFactory):
    """预算明细工厂"""

    class Meta:
        model = ProjectBudgetItem

    item_no = factory.Sequence(lambda n: f"{n:02d}")
    item_name = factory.Sequence(lambda n: f"预算项{n}")
    cost_type = "MATERIAL"
    budget_amount = factory.LazyFunction(
        lambda: Decimal(str(random.uniform(10000, 100000)))
    )


# ============== ECN ==============


class EcnFactory(BaseFactory):
    """ECN工厂"""

    class Meta:
        model = Ecn

    ecn_no = factory.Sequence(lambda n: f"ECN{date.today().strftime('%y%m%d')}{n:04d}")
    ecn_title = factory.Sequence(lambda n: f"测试ECN{n}")
    ecn_type = "DESIGN"
    source_type = "INTERNAL"
    change_reason = "测试变更原因"
    change_description = "测试变更描述"
    change_scope = "PARTIAL"
    priority = "NORMAL"
    urgency = "NORMAL"
    status = "DRAFT"


# ============== 验收 ==============


class AcceptanceTemplateFactory(BaseFactory):
    """验收模板工厂"""

    class Meta:
        model = AcceptanceTemplate

    template_code = factory.Sequence(lambda n: f"AT{n:04d}")
    template_name = factory.Sequence(lambda n: f"测试验收模板{n}")
    acceptance_type = "FAT"
    equipment_type = "TEST_EQUIPMENT"
    version = "1.0"
    is_system = False
    is_active = True


class AcceptanceOrderFactory(BaseFactory):
    """验收单工厂"""

    class Meta:
        model = AcceptanceOrder

    order_no = factory.Sequence(
        lambda n: f"ACC{date.today().strftime('%y%m%d')}{n:05d}"
    )
    acceptance_type = "FAT"
    status = "DRAFT"
    planned_date = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    total_items = 10
    passed_items = 0
    failed_items = 0
    na_items = 0
    pass_rate = Decimal("0.00")


# ============== 审批工作流 ==============


class ApprovalWorkflowFactory(BaseFactory):
    """审批工作流工厂"""

    class Meta:
        model = ApprovalWorkflow

    workflow_type = "QUOTE"
    workflow_name = factory.Sequence(lambda n: f"测试审批流程{n}")
    description = "测试审批工作流描述"
    is_active = True


class ApprovalWorkflowStepFactory(BaseFactory):
    """审批工作流步骤工厂"""

    class Meta:
        model = ApprovalWorkflowStep

    step_order = factory.Sequence(lambda n: n + 1)
    step_name = factory.Sequence(lambda n: f"审批步骤{n}")
    approver_role = "MANAGER"
    is_required = True
    can_delegate = True
    can_withdraw = True
    due_hours = 24


# ============== 便捷方法 ==============


def create_test_user(username: str = None, is_admin: bool = False, **kwargs) -> User:
    """
    创建测试用户的便捷方法

    Args:
        username: 用户名，默认自动生成
        is_admin: 是否为管理员
        **kwargs: 其他用户属性

    Returns:
        User: 创建的用户对象
    """
    factory_class = AdminUserFactory if is_admin else UserFactory
    if username:
        kwargs["username"] = username
    return factory_class(**kwargs)


def create_test_project(with_customer: bool = True, **kwargs) -> Project:
    """
    创建测试项目的便捷方法

    Args:
        with_customer: 是否同时创建客户
        **kwargs: 其他项目属性

    Returns:
        Project: 创建的项目对象
    """
    factory_class = ProjectWithCustomerFactory if with_customer else ProjectFactory
    return factory_class(**kwargs)


def create_complete_project_setup():
    """
    创建完整的项目测试数据集

    Returns:
        dict: 包含所有创建的对象
    """
    # 创建客户
    customer = CustomerFactory()

    # 创建项目
    project = ProjectFactory(
        customer_id=customer.id, customer_name=customer.customer_name
    )

    # 创建供应商
    supplier = SupplierFactory()

    # 创建物料
    materials = MaterialFactory.create_batch(5)

    # 创建BOM
    bom = BomHeaderFactory(project_id=project.id)

    return {
        "customer": customer,
        "project": project,
        "supplier": supplier,
        "materials": materials,
        "bom": bom,
    }


# ============== 缺失的Factory类 ==============


class BudgetFactory(ProjectBudgetFactory):
    """预算工厂别名（用于向后兼容）"""

    pass


class AcceptanceIssueFactory(BaseFactory):
    """验收问题工厂"""

    class Meta:
        model = AcceptanceIssue

    issue_no = factory.Sequence(
        lambda n: f"ISS{n:06d}"
    )
    title = factory.Sequence(lambda n: f"测试问题{n}")
    issue_type = "FUNCTIONAL"
    severity = "NORMAL"
    description = factory.Sequence(lambda n: f"测试问题描述{n}")
    status = "OPEN"


class ProjectCostFactory(BaseFactory):
    """项目成本工厂"""

    class Meta:
        model = ProjectCost

    cost_no = factory.Sequence(lambda n: f"CST{n:05d}")
    cost_type = "MATERIAL"
    description = factory.Sequence(lambda n: f"测试成本{n}")
    budget_amount = factory.LazyFunction(
        lambda: Decimal(str(random.uniform(10000, 100000)))
    )
    actual_amount = factory.LazyFunction(
        lambda: Decimal(str(random.uniform(10000, 100000)))
    )
    cost_date = factory.LazyFunction(lambda: date.today())
    status = "PENDING"


# ============================================================================
# 服务测试辅助函数（非 Factory 类）
# ============================================================================


class SupplierFactory(BaseFactory):
    """供应商工厂（使用 Vendor 模型，向后兼容）"""

    class Meta:
        model = Vendor

    supplier_code = factory.Sequence(lambda n: f"SUP{n:05d}")
    supplier_name = factory.Sequence(lambda n: f"测试供应商{n}")
    vendor_type = "STANDARD"
    status = "ACTIVE"


def create_mock_timesheet_data():
    """创建模拟工时数据（用于服务测试）"""
    return {
        'user_id': 1,
        'user_name': '测试用户',
        'normal_hours': 160.0,
        'overtime_hours': 10.0,
        'weekend_hours': 8.0,
        'holiday_hours': 4.0,
    }


def create_mock_project_data():
    """创建模拟项目数据（用于服务测试）"""
    return {
        'id': 1,
        'project_code': 'PJ260101001',
        'project_name': '测试项目',
        'customer_id': 1,
        'customer_name': '测试客户',
        'stage': 'S1',
        'status': 'ST01',
        'health': 'H1',
    }


def create_mock_user_data():
    """创建模拟用户数据（用于服务测试）"""
    return {
        'id': 1,
        'username': 'test_user',
        'real_name': '测试用户',
        'department': '测试部门',
        'department_id': 1,
        'is_active': True,
    }
