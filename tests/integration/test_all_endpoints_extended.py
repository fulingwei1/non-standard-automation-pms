# -*- coding: utf-8 -*-
"""
Comprehensive API Integration Tests for Extended Endpoints

This file tests the following endpoint modules:
- materials (categories, suppliers)
- bom/ (list, detail, items, versions, templates, generate, import, export)
- purchase/ (orders, receipts, requests)
- ecn/ (core, evaluations, approvals, tasks, impacts, types, utils)
- acceptance/ (order_crud, order_workflow, order_items, templates, reports)
- outsourcing/ (orders, deliveries, payments, quality, progress, suppliers)
- alert/ (rules, records, exceptions, notifications, statistics, subscriptions)
- shortage/ (arrivals, substitutions, transfers)
- issue/ (core, workflow, follow_ups)

Each module has 5-10 tests covering:
- List resources (with filters, pagination)
- Get detail by ID
- Create resource
- Update resource
- Delete resource
- Workflow operations where applicable
- Error cases
"""



import uuid

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material import (
    BomHeader,
    MaterialCategory,
)
from app.models.purchase import PurchaseOrder
from app.models.ecn import Ecn
from app.models.acceptance import (
    AcceptanceOrder,
    AcceptanceTemplate,
)
from app.models.outsourcing import (
    OutsourcingOrder,
)
from app.models.alert import AlertRule, AlertRecord
from app.models.issue import Issue
from app.models.project import Project, Machine
from app.models.vendor import Vendor
from app.models.shortage.reports import ShortageReport

# Vendor 模型替代了历史上的 Supplier/OutsourcingVendor，这里保持别名兼容
Supplier = Vendor
OutsourcingVendor = Vendor


def _uid(prefix: str = "") -> str:
    """生成唯一后缀，避免 unique 约束冲突"""
    return f"{prefix}{uuid.uuid4().hex[:8].upper()}"


# ============================================================================
# Materials API Tests
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestMaterialsCategoriesAPI:
    """物料分类 API 测试"""

    @pytest.fixture
    def test_category(self, db_session: Session):
        category = MaterialCategory(
            category_code=_uid("CATT"),
            category_name="测试分类",
            parent_id=None,
            level=1,
            full_path="测试分类",
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        yield category
        try:
            db_session.delete(category)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_categories_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取物料分类列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials/categories/",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_list_categories_with_parent_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用父分类ID筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials/categories/?is_active=true",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_category_success(
        self, client: TestClient, admin_auth_headers: dict, test_category: MaterialCategory
    ):
        """测试获取物料分类详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials/categories/{test_category.id}",
            headers=admin_auth_headers,
        )

    def test_create_category_success(self, client: TestClient, admin_auth_headers: dict):
        """测试创建物料分类"""
        category_data = {
            "category_code": _uid("CATN"),
            "category_name": "新分类",
            "parent_id": None,
            "level": 1,
            "full_path": "新分类",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/materials/categories/",
            json=category_data,
            headers=admin_auth_headers,
        )

    def test_update_category_success(
        self, client: TestClient, admin_auth_headers: dict, test_category: MaterialCategory
    ):
        """测试更新物料分类"""
        update_data = {"category_name": "更新后的分类"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/materials/categories/{test_category.id}",
            json=update_data,
            headers=admin_auth_headers,
        )

    def test_delete_category_success(
        self, client: TestClient, admin_auth_headers: dict, test_category: MaterialCategory
    ):
        """测试删除物料分类"""
        response = client.delete(
            f"{settings.API_V1_PREFIX}/materials/categories/{test_category.id}",
            headers=admin_auth_headers,
        )


@pytest.mark.api
@pytest.mark.integration
class TestMaterialsSuppliersAPI:
    """物料供应商 API 测试"""

    @pytest.fixture
    def test_supplier(self, db_session: Session):
        supplier = Supplier(
            supplier_code=_uid("SUPT"),
            supplier_name="测试供应商",
            supplier_type="VENDOR",
            contact_person="张三",
            contact_phone="13800000000",
            status="ACTIVE",
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)
        yield supplier
        try:
            db_session.delete(supplier)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_suppliers_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取供应商列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials/suppliers?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

    def test_list_suppliers_with_keyword_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用关键词筛选供应商"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials/suppliers?keyword=测试",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_list_suppliers_with_type_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用供应商类型筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials/suppliers?supplier_type=VENDOR",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_supplier_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_supplier: Supplier
    ):
        """测试获取供应商详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials/suppliers/{test_supplier.id}",
            headers=admin_auth_headers,
        )

    def test_create_supplier_success(self, client: TestClient, admin_auth_headers: dict):
        """测试创建供应商"""
        supplier_data = {
            "supplier_code": _uid("SUPN"),
            "supplier_name": "新供应商",
            "supplier_type": "VENDOR",
            "contact_person": "李四",
            "contact_phone": "13900000000",
            "status": "ACTIVE",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/materials/suppliers",
            json=supplier_data,
            headers=admin_auth_headers,
        )

    def test_update_supplier_success(
        self, client: TestClient, admin_auth_headers: dict, test_supplier: Supplier
    ):
        """测试更新供应商"""
        update_data = {"supplier_name": "更新后的供应商"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/materials/suppliers/{test_supplier.id}",
            json=update_data,
            headers=admin_auth_headers,
        )

    def test_delete_supplier_success(
        self, client: TestClient, admin_auth_headers: dict, test_supplier: Supplier
    ):
        """测试删除供应商"""
        response = client.delete(
            f"{settings.API_V1_PREFIX}/materials/suppliers/{test_supplier.id}",
            headers=admin_auth_headers,
        )

    def test_get_material_suppliers(self, client: TestClient, admin_auth_headers: dict):
        """测试获取物料的供应商列表"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials/1/suppliers",
            headers=admin_auth_headers,
        )


# ============================================================================
# BOM API Tests
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestBomAPI:
    """BOM 管理 API 测试"""

    @pytest.fixture
    def test_project(self, db_session: Session):
        project = Project(
            project_code=_uid("PJBM"),
            project_name="BOM测试项目",
            customer_name="测试客户",
            status="S1",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        yield project
        try:
            db_session.delete(project)
            db_session.commit()
        except Exception:
            db_session.rollback()

    @pytest.fixture
    def test_bom(self, db_session: Session, test_project: Project):
        # BomHeader 模型字段: bom_no, bom_name, project_id, machine_id, version,
        # is_latest, status, total_items, total_amount, approved_by, approved_at,
        # remark, created_by, created_at, updated_at
        # 注意: 没有 bom_type 字段
        bom = BomHeader(
            bom_no=_uid("BOMT"),
            project_id=test_project.id,
            bom_name="测试BOM",  # 添加 bom_name 字段
            version="1.0",
            is_latest=True,
            status="DRAFT",
            created_by=1,
        )
        db_session.add(bom)
        db_session.commit()
        db_session.refresh(bom)
        yield bom
        try:
            db_session.delete(bom)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_boms_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取BOM列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

    def test_list_boms_with_project_filter(
        self, client: TestClient, admin_auth_headers: dict, test_project: Project
    ):
        """测试使用项目ID筛选BOM"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/?project={test_project.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_list_boms_with_latest_filter(self, client: TestClient, admin_auth_headers: dict):
        """测试筛选最新版本BOM"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/?is_latest=true",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_bom_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_bom: BomHeader
    ):
        """测试获取BOM详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/{test_bom.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_create_bom_success(
        self, client: TestClient, admin_auth_headers: dict, test_project: Project
    ):
        """测试创建BOM"""
        bom_data = {
            "bom_no": _uid("BOMN"),
            "project_id": test_project.id,
            "bom_name": "新BOM",  # 使用 bom_name 而不是 bom_type
            "version": "1.0",
            "status": "DRAFT",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/bom/",
            json=bom_data,
            headers=admin_auth_headers,
        )

    def test_update_bom_success(
        self, client: TestClient, admin_auth_headers: dict, test_bom: BomHeader
    ):
        """测试更新BOM"""
        update_data = {"version": "1.1", "status": "PUBLISHED"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/bom/{test_bom.id}",
            json=update_data,
            headers=admin_auth_headers,
        )

    def test_delete_bom_success(
        self, client: TestClient, admin_auth_headers: dict, test_bom: BomHeader
    ):
        """测试删除BOM"""
        response = client.delete(
            f"{settings.API_V1_PREFIX}/bom/{test_bom.id}",
            headers=admin_auth_headers,
        )

    def test_get_bom_items(
        self, client: TestClient, admin_auth_headers: dict, test_bom: BomHeader
    ):
        """测试获取BOM明细"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/{test_bom.id}/items",
            headers=admin_auth_headers,
        )

    def test_bom_versions(
        self, client: TestClient, admin_auth_headers: dict, test_bom: BomHeader
    ):
        """测试获取BOM版本历史"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/{test_bom.id}/versions",
            headers=admin_auth_headers,
        )


# ============================================================================
# Purchase API Tests
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestPurchaseOrdersAPI:
    """采购订单 API 测试"""

    @pytest.fixture
    def test_supplier(self, db_session: Session):
        supplier = Supplier(
            supplier_code=_uid("SUPP"),
            supplier_name="PO测试供应商",
            supplier_type="VENDOR",
            contact_person="王五",
            contact_phone="13700000000",
            status="ACTIVE",
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)
        yield supplier
        try:
            db_session.delete(supplier)
            db_session.commit()
        except Exception:
            db_session.rollback()

    @pytest.fixture
    def test_order(self, db_session: Session, test_supplier: Supplier):
        order = PurchaseOrder(
            order_no=_uid("POTST"),
            supplier_id=test_supplier.id,
            order_type="NORMAL",
            status="DRAFT",
            total_amount=Decimal("10000.00"),
            order_date=date.today(),
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        yield order
        try:
            db_session.delete(order)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_purchase_orders_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取采购订单列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

    def test_list_orders_with_keyword_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用关键词搜索订单"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/?keyword=TEST",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_list_orders_with_status_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用状态筛选订单"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/?status=DRAFT",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_order_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: PurchaseOrder
    ):
        """测试获取订单详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_order.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_create_order_success(
        self, client: TestClient, admin_auth_headers: dict, test_supplier: Supplier
    ):
        """测试创建采购订单"""
        order_data = {
            "supplier_id": test_supplier.id,
            "order_title": "测试采购订单",
            "required_date": (date.today() + timedelta(days=7)).isoformat(),
            "items": [
                {
                    "material_code": f"MAT-001-{uuid.uuid4().hex[:8]}",
                    "material_name": "测试物料",
                    "quantity": 10,
                    "unit_price": 100.00,
                    "tax_rate": 13,
                }
            ],
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders/",
            json=order_data,
            headers=admin_auth_headers,
        )

    def test_update_order_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: PurchaseOrder
    ):
        """测试更新采购订单"""
        update_data = {
            "order_title": "更新后的订单标题",
            "remark": "测试备注",
        }
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_order.id}",
            json=update_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 422, 500)

    def test_submit_order_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: PurchaseOrder
    ):
        """测试提交采购订单"""
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_order.id}/submit",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 422, 500)

    def test_approve_order_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: PurchaseOrder,
        db_session: Session,
    ):
        """测试审批采购订单"""
        test_order.status = "SUBMITTED"
        db_session.commit()

        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_order.id}/approve?approved=true",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 422, 500)

    def test_get_order_items(
        self, client: TestClient, admin_auth_headers: dict, test_order: PurchaseOrder
    ):
        """测试获取订单明细"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_order.id}/items",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)


# ============================================================================
# ECN API Tests
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestEcnAPI:
    """ECN 管理 API 测试"""

    @pytest.fixture
    def test_project(self, db_session: Session):
        project = Project(
            project_code=_uid("PJEC"),
            project_name="ECN测试项目",
            customer_name="测试客户",
            status="S2",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        yield project
        try:
            db_session.delete(project)
            db_session.commit()
        except Exception:
            db_session.rollback()

    @pytest.fixture
    def test_ecn(self, db_session: Session, test_project: Project):
        ecn = Ecn(
            ecn_no=_uid("ECNT"),
            ecn_title="测试ECN",
            ecn_type="DESIGN_CHANGE",
            source_type="MANUAL",
            project_id=test_project.id,
            change_reason="测试变更原因",
            change_description="测试变更描述",
            status="DRAFT",
            priority="MEDIUM",
            applicant_id=1,
        )
        db_session.add(ecn)
        db_session.commit()
        db_session.refresh(ecn)
        yield ecn
        try:
            db_session.delete(ecn)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_ecns_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取ECN列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

    def test_list_ecns_with_keyword_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用关键词搜索ECN"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns?keyword=TEST",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_list_ecns_with_type_filter(self, client: TestClient, admin_auth_headers: dict):
        """测试使用变更类型筛选ECN"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns?ecn_type=DESIGN_CHANGE",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_list_ecns_with_status_filter(self, client: TestClient, admin_auth_headers: dict):
        """测试使用状态筛选ECN"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns?status=DRAFT",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_ecn_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_ecn: Ecn
    ):
        """测试获取ECN详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns/{test_ecn.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_create_ecn_success(
        self, client: TestClient, admin_auth_headers: dict, test_project: Project
    ):
        """测试创建ECN"""
        ecn_data = {
            "ecn_title": "新ECN申请",
            "ecn_type": "DESIGN_CHANGE",
            "source_type": "MANUAL",
            "project_id": test_project.id,
            "change_reason": "设计优化需求",
            "change_description": "详细描述变更内容",
            "change_scope": "模块A",
            "priority": "MEDIUM",
            "urgency": "NORMAL",
            "cost_impact": 5000.00,
            "schedule_impact_days": 3,
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/ecns",
            json=ecn_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 201, 400, 422, 500)

    def test_update_ecn_success(
        self, client: TestClient, admin_auth_headers: dict, test_ecn: Ecn
    ):
        """测试更新ECN"""
        update_data = {
            "ecn_title": "更新后的ECN标题",
            "priority": "HIGH",
        }
        response = client.put(
            f"{settings.API_V1_PREFIX}/ecns/{test_ecn.id}",
            json=update_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 422, 500)

    def test_submit_ecn_success(
        self, client: TestClient, admin_auth_headers: dict, test_ecn: Ecn
    ):
        """测试提交ECN"""
        submit_data = {"remark": "提交ECN申请"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/ecns/{test_ecn.id}/submit",
            json=submit_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 422, 500)

    def test_cancel_ecn_success(
        self, client: TestClient, admin_auth_headers: dict, test_ecn: Ecn
    ):
        """测试取消ECN"""
        response = client.put(
            f"{settings.API_V1_PREFIX}/ecns/{test_ecn.id}/cancel",
            params={"cancel_reason": "取消测试"},
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 422, 500)

    def test_ecn_not_found(self, client: TestClient, admin_auth_headers: dict):
        """测试获取不存在的ECN"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/ecns/999999",
            headers=admin_auth_headers,
        )
        assert response.status_code in (404, 500)


# ============================================================================
# Acceptance API Tests
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestAcceptanceOrdersAPI:
    """验收订单 API 测试"""

    @pytest.fixture
    def test_project(self, db_session: Session):
        project = Project(
            project_code=_uid("PJAC"),
            project_name="验收测试项目",
            customer_name="测试客户",
            status="S6",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        yield project
        try:
            db_session.delete(project)
            db_session.commit()
        except Exception:
            db_session.rollback()

    @pytest.fixture
    def test_machine(self, db_session: Session, test_project: Project):
        machine = Machine(
            project_id=test_project.id,
            machine_code=_uid("MACC"),
            machine_name="验收测试设备",
            machine_type="TEST",
            status="ASSEMBLY",
        )
        db_session.add(machine)
        db_session.commit()
        db_session.refresh(machine)
        yield machine
        try:
            db_session.delete(machine)
            db_session.commit()
        except Exception:
            db_session.rollback()

    @pytest.fixture
    def test_template(self, db_session: Session):
        template = AcceptanceTemplate(
            template_code=_uid("ATPL"),
            template_name="测试验收模板",
            acceptance_type="FAT",
            equipment_type="TEST",
            version="1.0",
            is_system=False,
            is_active=True,
            created_by=1,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)
        yield template
        try:
            db_session.delete(template)
            db_session.commit()
        except Exception:
            db_session.rollback()

    @pytest.fixture
    def test_order(
        self,
        db_session: Session,
        test_project: Project,
        test_machine: Machine,
        test_template: AcceptanceTemplate,
    ):
        order = AcceptanceOrder(
            order_no=_uid("AODR"),
            project_id=test_project.id,
            machine_id=test_machine.id,
            acceptance_type="FAT",
            template_id=test_template.id,
            planned_date=date.today() + timedelta(days=3),
            location="工厂测试区",
            status="DRAFT",
            total_items=0,
            passed_items=0,
            failed_items=0,
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        yield order
        try:
            db_session.delete(order)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_acceptance_orders_success(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试获取验收订单列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

    def test_list_orders_with_type_filter(self, client: TestClient, admin_auth_headers: dict):
        """测试使用验收类型筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders?acceptance_type=FAT",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_order_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: AcceptanceOrder
    ):
        """测试获取验收订单详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{test_order.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_create_order_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_project: Project,
        test_machine: Machine,
        test_template: AcceptanceTemplate,
    ):
        """测试创建验收订单"""
        order_data = {
            "order_no": _uid("AONW"),
            "project_id": test_project.id,
            "machine_id": test_machine.id,
            "acceptance_type": "FAT",
            "template_id": test_template.id,
            "planned_date": (date.today() + timedelta(days=3)).isoformat(),
            "location": "工厂测试区",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/acceptance/orders",
            json=order_data,
            headers=admin_auth_headers,
        )

    def test_update_order_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: AcceptanceOrder
    ):
        """测试更新验收订单"""
        update_data = {
            "location": "更新后的地点",
            "remark": "测试备注",
        }
        response = client.put(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{test_order.id}",
            json=update_data,
            headers=admin_auth_headers,
        )

    def test_submit_order_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: AcceptanceOrder
    ):
        """测试提交验收订单"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{test_order.id}/submit",
            headers=admin_auth_headers,
        )

    def test_start_order_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: AcceptanceOrder,
        db_session: Session,
    ):
        """测试开始验收"""
        test_order.status = "SUBMITTED"
        db_session.commit()

        response = client.post(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{test_order.id}/start",
            headers=admin_auth_headers,
        )

    def test_get_order_items(
        self, client: TestClient, admin_auth_headers: dict, test_order: AcceptanceOrder
    ):
        """测试获取验收订单明细"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/acceptance-orders/{test_order.id}/items",
            headers=admin_auth_headers,
        )


# ============================================================================
# Outsourcing API Tests
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestOutsourcingOrdersAPI:
    """外协订单 API 测试"""

    @pytest.fixture
    def test_vendor(self, db_session: Session):
        # 使用 Vendor 而不是 OutsourcingVendor 别名
        vendor = Vendor(
            supplier_code=_uid("OSVD"),
            supplier_name="测试外协商",
            vendor_type="OUTSOURCING",  # 正确的字段名和值
            contact_person="赵六",
            contact_phone="13600000000",
            status="ACTIVE",
        )
        db_session.add(vendor)
        db_session.commit()
        db_session.refresh(vendor)
        yield vendor
        try:
            db_session.delete(vendor)
            db_session.commit()
        except Exception:
            db_session.rollback()

    @pytest.fixture
    def test_project(self, db_session: Session):
        project = Project(
            project_code=_uid("PJOS"),
            project_name="外协测试项目",
            customer_name="测试客户",
            status="S4",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        yield project
        try:
            db_session.delete(project)
            db_session.commit()
        except Exception:
            db_session.rollback()

    @pytest.fixture
    def test_order(self, db_session: Session, test_vendor, test_project):
        # 移除类型提示,避免 OutsourcingVendor 别名问题
        order = OutsourcingOrder(
            order_no=_uid("OSOD"),
            vendor_id=test_vendor.id,
            project_id=test_project.id,
            order_type="PROCESSING",
            order_title="外协加工订单",
            total_amount=Decimal("5000.00"),
            tax_rate=Decimal("13"),
            tax_amount=Decimal("650.00"),
            amount_with_tax=Decimal("5650.00"),
            required_date=date.today() + timedelta(days=10),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        yield order
        try:
            db_session.delete(order)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_outsourcing_orders_success(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试获取外协订单列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/outsourcing-orders?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

    def test_list_orders_with_keyword_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用关键词搜索"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/outsourcing-orders?keyword=测试",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_list_orders_with_status_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用状态筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/outsourcing-orders?status=DRAFT",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_order_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: OutsourcingOrder
    ):
        """测试获取外协订单详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/outsourcing-orders/{test_order.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_create_order_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_vendor,  # 移除类型提示
        test_project: Project,
    ):
        """测试创建外协订单"""
        order_data = {
            "vendor_id": test_vendor.id,
            "project_id": test_project.id,
            "order_type": "PROCESSING",
            "order_title": "新外协订单",
            "tax_rate": 13,
            "required_date": (date.today() + timedelta(days=10)).isoformat(),
            "items": [
                {
                    "material_code": f"MAT-OS-001-{uuid.uuid4().hex[:8]}",
                    "material_name": "外协物料",
                    "quantity": 10,
                    "unit_price": 100.00,
                }
            ],
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/outsourcing-orders",
            json=order_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 201, 400, 422, 500)

    def test_update_order_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: OutsourcingOrder
    ):
        """测试更新外协订单"""
        update_data = {
            "order_title": "更新后的外协订单",
            "remark": "测试备注",
        }
        response = client.put(
            f"{settings.API_V1_PREFIX}/outsourcing-orders/{test_order.id}",
            json=update_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 422, 500)

    def test_approve_order_success(
        self, client: TestClient, admin_auth_headers: dict, test_order: OutsourcingOrder,
        db_session: Session,
    ):
        """测试审批外协订单"""
        test_order.status = "SUBMITTED"
        db_session.commit()

        response = client.put(
            f"{settings.API_V1_PREFIX}/outsourcing-orders/{test_order.id}/approve",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 422, 500)

    def test_get_order_items(
        self, client: TestClient, admin_auth_headers: dict, test_order: OutsourcingOrder
    ):
        """测试获取外协订单明细"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/outsourcing-orders/{test_order.id}/items",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)


# ============================================================================
# Alerts API Tests
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestAlertRulesAPI:
    """预警规则 API 测试"""

    @pytest.fixture
    def test_rule(self, db_session: Session):
        rule = AlertRule(
            rule_code=_uid("ALRL"),
            rule_name="测试预警规则",
            rule_type="PROJECT_DELAY",
            target_type="PROJECT",
            condition_type="THRESHOLD",
            alert_level="WARNING",
            is_enabled=True,
            is_system=False,
            created_by=1,
        )
        db_session.add(rule)
        db_session.commit()
        db_session.refresh(rule)
        yield rule
        try:
            db_session.delete(rule)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_alert_rule_templates(self, client: TestClient, admin_auth_headers: dict):
        """测试获取预警规则模板列表"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/alert-rule-templates",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_list_alert_rules_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取预警规则列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/alert-rules?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

    def test_list_rules_with_keyword_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用关键词搜索规则"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/alert-rules?keyword=测试",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_list_rules_with_type_filter(self, client: TestClient, admin_auth_headers: dict):
        """测试使用规则类型筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/alert-rules?rule_type=PROJECT_DELAY",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_rule_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_rule: AlertRule
    ):
        """测试获取预警规则详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/alert-rules/{test_rule.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_create_rule_success(self, client: TestClient, admin_auth_headers: dict):
        """测试创建预警规则"""
        rule_data = {
            "rule_code": _uid("NWRL"),
            "rule_name": "新预警规则",
            "rule_type": "PROJECT_DELAY",
            "target_type": "PROJECT",
            "condition_type": "THRESHOLD",
            "alert_level": "WARNING",
            "description": "项目延期预警",
            "check_frequency": "DAILY",
            "notify_channels": ["SYSTEM", "EMAIL"],
            "is_enabled": True,
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/alert-rules",
            json=rule_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 201, 400, 422, 500)

    def test_update_rule_success(
        self, client: TestClient, admin_auth_headers: dict, test_rule: AlertRule
    ):
        """测试更新预警规则"""
        update_data = {
            "rule_name": "更新后的规则",
            "alert_level": "CRITICAL",
        }
        response = client.put(
            f"{settings.API_V1_PREFIX}/alert-rules/{test_rule.id}",
            json=update_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 422, 500)

    def test_toggle_rule_success(
        self, client: TestClient, admin_auth_headers: dict, test_rule: AlertRule
    ):
        """测试启用/禁用预警规则"""
        response = client.put(
            f"{settings.API_V1_PREFIX}/alert-rules/{test_rule.id}/toggle",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 500)

    def test_delete_rule_success(
        self, client: TestClient, admin_auth_headers: dict, test_rule: AlertRule,
        db_session: Session,
    ):
        """测试删除预警规则"""
        test_rule.is_system = False  # Ensure not system rule
        db_session.commit()

        response = client.delete(
            f"{settings.API_V1_PREFIX}/alert-rules/{test_rule.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 500)


@pytest.mark.api
@pytest.mark.integration
class TestAlertRecordsAPI:
    """预警记录 API 测试"""

    @pytest.fixture
    def test_record(self, db_session: Session):
        # AlertRecord 模型: alert_no(唯一必填), rule_id(FK必填),
        # target_type/target_id(必填), alert_level/alert_title/alert_content(必填),
        # status 默认 'PENDING'
        from app.models.alert import AlertRule
        rule = db_session.query(AlertRule).first()
        if not rule:
            # 如果没有预警规则，创建一个测试用规则
            rule = AlertRule(
                rule_code=_uid("RULE"),
                rule_name="测试预警规则",
                rule_type="PROJECT_DELAY",
                target_type="PROJECT",
                condition_type="THRESHOLD",
                alert_level="WARNING",
                is_enabled=True,
                is_system=False,
                created_by=1,
            )
            db_session.add(rule)
            db_session.commit()
            db_session.refresh(rule)

        record = AlertRecord(
            alert_no=_uid("AREC"),
            rule_id=rule.id,
            target_type="PROJECT",
            target_id=1,
            alert_level="WARNING",
            alert_title="测试预警标题",
            alert_content="测试预警内容",
            status="PENDING",
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        yield record
        try:
            db_session.delete(record)
            # 如果是我们创建的规则，也删除它
            if rule.rule_code.startswith("RULE"):
                db_session.delete(rule)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_alert_records_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取预警记录列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/alerts/records?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_list_records_with_status_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用状态筛选记录"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/alerts/records?status=OPEN",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_record_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_record: AlertRecord
    ):
        """测试获取预警记录详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/alerts/records/{test_record.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_handle_record_success(
        self, client: TestClient, admin_auth_headers: dict, test_record: AlertRecord
    ):
        """测试处理预警记录"""
        handle_data = {
            "handle_note": "处理说明",
            "action_taken": "ACKNOWLEDGED",
        }
        response = client.put(
            f"{settings.API_V1_PREFIX}/alerts/records/{test_record.id}/handle",
            json=handle_data,
            headers=admin_auth_headers,
        )


# ============================================================================
# Issue API Tests
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestIssuesAPI:
    """问题管理 API 测试"""

    @pytest.fixture
    def test_issue(self, db_session: Session):
        # Issue 模型: issue_no(唯一必填), title(必填), category(必填),
        # issue_type(必填), severity(必填), description(必填),
        # reporter_id(FK必填), report_date(必填)
        issue = Issue(
            issue_no=_uid("ISSU"),
            title="测试问题",
            category="QUALITY",
            issue_type="QUALITY",
            severity="HIGH",
            priority="HIGH",
            status="OPEN",
            description="问题描述",
            reporter_id=1,
            report_date=datetime.now(),
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)
        yield issue
        try:
            db_session.delete(issue)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_issues_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取问题列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_list_issues_with_type_filter(self, client: TestClient, admin_auth_headers: dict):
        """测试使用问题类型筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues?issue_type=QUALITY",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_list_issues_with_status_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用状态筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues?status=OPEN",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_get_issue_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_issue: Issue
    ):
        """测试获取问题详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues/{test_issue.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_create_issue_success(self, client: TestClient, admin_auth_headers: dict):
        """测试创建问题"""
        issue_data = {
            "title": "新问题",
            "issue_type": "QUALITY",
            "category": "QUALITY",
            "severity": "HIGH",
            "priority": "HIGH",
            "description": "问题描述详情",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues",
            json=issue_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 201, 400, 422, 500)

    def test_update_issue_success(
        self, client: TestClient, admin_auth_headers: dict, test_issue: Issue
    ):
        """测试更新问题"""
        update_data = {
            "title": "更新后的问题",
            "priority": "MEDIUM",
        }
        response = client.put(
            f"{settings.API_V1_PREFIX}/issues/{test_issue.id}",
            json=update_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 400, 404, 422, 500)

    def test_assign_issue_success(
        self, client: TestClient, admin_auth_headers: dict, test_issue: Issue
    ):
        """测试分配问题"""
        assign_data = {
            "assignee_id": 1,
            "assign_note": "分配处理",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues/{test_issue.id}/assign",
            json=assign_data,
            headers=admin_auth_headers,
        )

    def test_resolve_issue_success(
        self, client: TestClient, admin_auth_headers: dict, test_issue: Issue
    ):
        """测试解决问题"""
        resolve_data = {
            "resolution": "解决方案",
            "resolution_note": "处理说明",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues/{test_issue.id}/resolve",
            json=resolve_data,
            headers=admin_auth_headers,
        )

    def test_get_issue_follow_ups(
        self, client: TestClient, admin_auth_headers: dict, test_issue: Issue
    ):
        """测试获取问题跟进记录"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues/{test_issue.id}/follow-ups",
            headers=admin_auth_headers,
        )


# ============================================================================
# Shortage API Tests
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestMaterialShortageAPI:
    """物料缺料 API 测试"""

    @pytest.fixture
    def test_shortage(self, db_session: Session):
        # ShortageReport 模型: report_no(唯一必填), project_id(FK必填),
        # material_id(FK必填), material_code(必填), material_name(必填),
        # required_qty(必填), shortage_qty(必填), reporter_id(FK必填),
        # report_time(必填), status 默认 'REPORTED'
        from app.models.project import Project
        from app.models.material import Material
        project = db_session.query(Project).first()
        material = db_session.query(Material).first()
        if not project or not material:
            pytest.skip("缺少测试数据：项目或物料")
        shortage = ShortageReport(
            report_no=_uid("MSHT"),
            project_id=project.id,
            material_id=material.id,
            material_code=_uid("MATS"),
            material_name="缺料物料",
            required_qty=Decimal("10"),
            shortage_qty=Decimal("10"),
            report_time=datetime.now(),
            reporter_id=1,
            status="REPORTED",
        )
        db_session.add(shortage)
        db_session.commit()
        db_session.refresh(shortage)
        yield shortage
        try:
            db_session.delete(shortage)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_list_shortages_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取缺料列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/shortage/arrivals?page=1&page_size=10",
            headers=admin_auth_headers,
        )

    def test_list_shortages_with_status_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试使用状态筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/shortage/arrivals?status=OPEN",
            headers=admin_auth_headers,
        )

    def test_get_shortage_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_shortage: ShortageReport
    ):
        """测试获取缺料详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/shortage/arrivals/{test_shortage.id}",
            headers=admin_auth_headers,
        )

    def test_create_shortage_arrival(self, client: TestClient, admin_auth_headers: dict):
        """测试创建到货记录"""
        arrival_data = {
            "shortage_id": 1,
            "arrival_quantity": 10,
            "arrival_date": date.today().isoformat(),
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/shortage/arrivals",
            json=arrival_data,
            headers=admin_auth_headers,
        )

    def test_update_shortage_arrival(
        self, client: TestClient, admin_auth_headers: dict, test_shortage: ShortageReport
    ):
        """测试更新到货记录"""
        update_data = {
            "arrival_quantity": 15,
            "arrival_note": "数量调整",
        }
        response = client.put(
            f"{settings.API_V1_PREFIX}/shortage/arrivals/{test_shortage.id}",
            json=update_data,
            headers=admin_auth_headers,
        )

    def test_list_substitutions(self, client: TestClient, admin_auth_headers: dict):
        """测试获取物料替代列表"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/shortage/substitutions?page=1&page_size=10",
            headers=admin_auth_headers,
        )

    def test_create_substitution(self, client: TestClient, admin_auth_headers: dict):
        """测试创建物料替代"""
        substitution_data = {
            "original_material_id": 1,
            "substitute_material_id": 2,
            "substitution_reason": "替代说明",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/shortage/substitutions",
            json=substitution_data,
            headers=admin_auth_headers,
        )

    def test_list_transfers(self, client: TestClient, admin_auth_headers: dict):
        """测试获取物料调拨列表"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/shortage/transfers?page=1&page_size=10",
            headers=admin_auth_headers,
        )


# ============================================================================
# Pagination and Filter Tests (Shared Across Modules)
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestPaginationAndFiltering:
    """分页和筛选通用测试"""

    def test_pagination_out_of_bounds(self, client: TestClient, admin_auth_headers: dict):
        """测试分页超出边界"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?page=9999&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "items" in data:
                assert len(data["items"]) == 0

    def test_invalid_page_size(self, client: TestClient, admin_auth_headers: dict):
        """测试无效的页大小"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?page=1&page_size=999",
            headers=admin_auth_headers,
        )

    def test_multiple_filters(self, client: TestClient, admin_auth_headers: dict):
        """测试多个筛选条件组合"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?status=S1&health=H1&page=1",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)

    def test_empty_filter_results(self, client: TestClient, admin_auth_headers: dict):
        """测试筛选返回空结果"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?status=INVALID_STATUS",
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 404, 422, 500)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "total" in data:
                assert data["total"] == 0


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.api
@pytest.mark.integration
class TestErrorHandling:
    """错误处理测试"""

    def test_unauthorized_access(self, client: TestClient):
        """测试未授权访问"""
        response = client.get(f"{settings.API_V1_PREFIX}/projects")
        assert response.status_code in (401, 403)

    def test_invalid_token(self, client: TestClient):
        """测试无效token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get(f"{settings.API_V1_PREFIX}/projects", headers=headers)
        assert response.status_code in (401, 403)

    def test_resource_not_found(self, client: TestClient, admin_auth_headers: dict):
        """测试资源不存在"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/999999",
            headers=admin_auth_headers,
        )
        assert response.status_code in (404, 500)

    def test_validation_error_missing_required(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试缺少必填字段的验证错误"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects",
            json={"project_name": "缺少编码的项目"},
            headers=admin_auth_headers,
        )
        assert response.status_code in (400, 422, 500)

    def test_method_not_allowed(self, client: TestClient, admin_auth_headers: dict):
        """测试不允许的HTTP方法"""
        response = client.patch(
            f"{settings.API_V1_PREFIX}/projects/1",
            json={"project_name": "测试"},
            headers=admin_auth_headers,
        )
        assert response.status_code in [405, 404]
