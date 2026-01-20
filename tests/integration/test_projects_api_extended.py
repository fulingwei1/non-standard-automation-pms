# -*- coding: utf-8 -*-
"""
项目、物料、BOM、采购订单 API 扩展集成测试

测试内容：
- 项目管理 API (列表、详情、创建、更新、删除、搜索)
- 物料管理 API (列表、详情)
- BOM 管理 API (列表、详情)
- 采购订单 API (列表、详情、创建)
"""

import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.material import Material, Supplier
from app.models.project import Project, Customer
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.core.config import settings


@pytest.mark.api
@pytest.mark.integration
class TestProjectsAPIExtended:
    """项目管理 API 扩展测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def admin_auth_headers(self, client: TestClient):
        """创建管理员认证头"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        if response.status_code != 200:
            pytest.skip("Admin login failed - skipping extended tests")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def test_customer(self, db_session: Session):
        """创建测试客户"""
        customer = Customer(
            customer_code="CUST-EXT-001",
            customer_name="扩展测试客户",
            contact_person="张三",
            contact_phone="13800138001",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        yield customer
        db_session.delete(customer)
        db_session.commit()

    @pytest.fixture
    def test_project(self, db_session: Session, test_customer):
        """创建测试项目"""
        project = Project(
            project_code="PJEXT001",
            project_name="扩展测试项目",
            customer_id=test_customer.id,
            customer_name=test_customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            contract_amount=Decimal("500000.00"),
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        yield project
        db_session.delete(project)
        db_session.commit()

    def test_list_projects_empty_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试项目列表 - 无筛选条件"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_list_projects_with_multiple_filters(
        self, client: TestClient, admin_auth_headers: dict, test_project: Project
    ):
        """测试项目列表 - 多个筛选条件"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?stage=S1&health=H1&is_active=true",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_list_projects_with_keyword_search(
        self, client: TestClient, admin_auth_headers: dict, test_project: Project
    ):
        """测试项目列表 - 关键词搜索"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?keyword={test_project.project_name}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_list_projects_pagination(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试项目列表分页"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_get_project_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_project: Project
    ):
        """测试获取项目详情成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{test_project.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["project_code"] == test_project.project_code
        assert data["project_name"] == test_project.project_name

    def test_get_project_detail_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试获取不存在的项目详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/999999",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_create_project_success(self, client: TestClient, admin_auth_headers: dict):
        """测试创建项目成功"""
        project_data = {
            "project_code": "PJEXT002",
            "project_name": "新建扩展测试项目",
            "customer_name": "新客户",
            "stage": "S1",
            "status": "ST01",
            "health": "H1",
            "contract_amount": 300000.00,
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects",
            json=project_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["project_code"] == project_data["project_code"]
        assert data["project_name"] == project_data["project_name"]

    def test_create_project_validation_error(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试创建项目验证错误"""
        project_data = {
            "project_name": "缺少必填字段的项目",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects",
            json=project_data,
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    def test_update_project_success(
        self, client: TestClient, admin_auth_headers: dict, test_project: Project
    ):
        """测试更新项目成功"""
        update_data = {
            "project_name": "更新后的扩展测试项目",
            "health": "H2",
        }
        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{test_project.id}",
            json=update_data,
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == update_data["project_name"]
        assert data["health"] == update_data["health"]

    def test_update_project_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试更新不存在的项目"""
        update_data = {"project_name": "不存在项目的更新"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/999999",
            json=update_data,
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_delete_project_success(
        self, client: TestClient, admin_auth_headers: dict, test_project: Project
    ):
        """测试删除项目成功（软删除）"""
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/{test_project.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_delete_project_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试删除不存在的项目"""
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/999999",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_project_search_by_code(
        self, client: TestClient, admin_auth_headers: dict, test_project: Project
    ):
        """测试项目搜索 - 按编码"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?keyword={test_project.project_code}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_project_unauthorized(self, client: TestClient):
        """测试未授权访问项目"""
        response = client.get(f"{settings.API_V1_PREFIX}/projects")
        assert response.status_code == 401


@pytest.mark.api
@pytest.mark.integration
class TestMaterialsAPI:
    """物料管理 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def admin_auth_headers(self, client: TestClient):
        """创建管理员认证头"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        if response.status_code != 200:
            pytest.skip("Admin login failed - skipping materials tests")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def test_supplier(self, db_session: Session):
        """创建测试供应商"""
        supplier = Supplier(
            supplier_code="SUP-EXT-001",
            supplier_name="扩展测试供应商",
            supplier_type="VENDOR",
            contact_person="李四",
            contact_phone="13900139001",
            status="ACTIVE",
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)
        yield supplier
        db_session.delete(supplier)
        db_session.commit()

    @pytest.fixture
    def test_material(self, db_session: Session, test_supplier):
        """创建测试物料"""
        material = Material(
            material_code="MAT-EXT-001",
            material_name="扩展测试物料",
            specification="规格描述",
            brand="测试品牌",
            unit="件",
            material_type="STANDARD",
            source_type="PURCHASE",
            standard_price=Decimal("100.00"),
            safety_stock=Decimal("50"),
            lead_time_days=7,
            is_key_material=True,
            is_active=True,
            default_supplier_id=test_supplier.id,
        )
        db_session.add(material)
        db_session.commit()
        db_session.refresh(material)
        yield material
        db_session.delete(material)
        db_session.commit()

    def test_list_materials_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取物料列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_list_materials_with_filter(
        self, client: TestClient, admin_auth_headers: dict, test_material: Material
    ):
        """测试物料列表筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials?material_type=STANDARD&is_key_material=true",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_list_materials_with_keyword_search(
        self, client: TestClient, admin_auth_headers: dict, test_material: Material
    ):
        """测试物料列表关键词搜索"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials?keyword={test_material.material_name}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_material_detail_success(
        self, client: TestClient, admin_auth_headers: dict, test_material: Material
    ):
        """测试获取物料详情成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials/{test_material.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_material.id
        assert data["material_code"] == test_material.material_code
        assert data["material_name"] == test_material.material_name

    def test_get_material_detail_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试获取不存在的物料"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials/999999",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_list_materials_pagination(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试物料列表分页"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/materials?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_materials_unauthorized(self, client: TestClient):
        """测试未授权访问物料"""
        response = client.get(f"{settings.API_V1_PREFIX}/materials")
        assert response.status_code in [401, 403]


@pytest.mark.api
@pytest.mark.integration
class TestBOMAPI:
    """BOM 管理 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def admin_auth_headers(self, client: TestClient):
        """创建管理员认证头"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        if response.status_code != 200:
            pytest.skip("Admin login failed - skipping BOM tests")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def test_project_with_bom(self, db_session: Session):
        """创建带BOM的测试项目"""
        customer = Customer(
            customer_code="CUST-BOM-001",
            customer_name="BOM测试客户",
            contact_person="王五",
            contact_phone="13700137001",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.flush()

        project = Project(
            project_code="PJBOM001",
            project_name="BOM测试项目",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S2",
            status="ST02",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        yield project
        db_session.delete(project)
        db_session.delete(customer)
        db_session.commit()

    def test_list_boms_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_project_with_bom: Project,
    ):
        """测试获取BOM列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_list_boms_with_project_filter(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_project_with_bom: Project,
    ):
        """测试BOM列表按项目筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom?project={test_project_with_bom.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_list_boms_latest_version(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试BOM列表只返回最新版本"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom?is_latest=true",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_list_boms_pagination(self, client: TestClient, admin_auth_headers: dict):
        """测试BOM列表分页"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_get_bom_detail_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试获取不存在的BOM详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/999999",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_boms_unauthorized(self, client: TestClient):
        """测试未授权访问BOM"""
        response = client.get(f"{settings.API_V1_PREFIX}/bom")
        assert response.status_code == 401


@pytest.mark.api
@pytest.mark.integration
class TestPurchaseOrderAPI:
    """采购订单 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def admin_auth_headers(self, client: TestClient):
        """创建管理员认证头"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        if response.status_code != 200:
            pytest.skip("Admin login failed - skipping purchase order tests")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def test_supplier(self, db_session: Session):
        """创建测试供应商"""
        supplier = Supplier(
            supplier_code="SUP-PO-001",
            supplier_name="PO测试供应商",
            supplier_type="VENDOR",
            contact_person="赵六",
            contact_phone="13600136001",
            status="ACTIVE",
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)
        yield supplier
        db_session.delete(supplier)
        db_session.commit()

    @pytest.fixture
    def test_project(self, db_session: Session):
        """创建测试项目"""
        customer = Customer(
            customer_code="CUST-PO-001",
            customer_name="PO测试客户",
            contact_person="钱七",
            contact_phone="13500135001",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.flush()

        project = Project(
            project_code="PJPO001",
            project_name="PO测试项目",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S3",
            status="ST03",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        yield project
        db_session.delete(project)
        db_session.delete(customer)
        db_session.commit()

    @pytest.fixture
    def test_purchase_order(
        self, db_session: Session, test_supplier: Supplier, test_project
    ):
        """创建测试采购订单"""
        order = PurchaseOrder(
            order_no="PO-EXT-001",
            supplier_id=test_supplier.id,
            project_id=test_project.id,
            order_type="NORMAL",
            order_title="扩展测试采购订单",
            status="DRAFT",
            total_amount=Decimal("5000.00"),
            order_date=date.today(),
            created_by=1,
        )
        db_session.add(order)
        db_session.flush()

        item = PurchaseOrderItem(
            order_id=order.id,
            item_no=1,
            material_code="MAT-PO-001",
            material_name="PO测试物料",
            specification="PO规格",
            unit="件",
            quantity=Decimal("10"),
            unit_price=Decimal("500.00"),
            amount=Decimal("5000.00"),
            tax_rate=Decimal("13"),
            status="PENDING",
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(order)
        yield order
        db_session.delete(item)
        db_session.delete(order)
        db_session.commit()

    def test_list_purchase_orders_success(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试获取采购订单列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_list_purchase_orders_with_filter(
        self, client: TestClient, admin_auth_headers: dict, test_supplier: Supplier
    ):
        """测试采购订单列表按供应商筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders?supplier_id={test_supplier.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_list_purchase_orders_with_status_filter(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试采购订单列表按状态筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders?status=DRAFT",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_list_purchase_orders_with_keyword_search(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_purchase_order: PurchaseOrder,
    ):
        """测试采购订单列表关键词搜索"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders?keyword={test_purchase_order.order_no}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_purchase_order_detail_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_purchase_order: PurchaseOrder,
    ):
        """测试获取采购订单详情成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_purchase_order.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_purchase_order.id
        assert data["order_no"] == test_purchase_order.order_no

    def test_get_purchase_order_detail_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试获取不存在的采购订单"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/999999",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_create_purchase_order_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_supplier: Supplier,
        test_project: Project,
    ):
        """测试创建采购订单成功"""
        order_data = {
            "supplier_id": test_supplier.id,
            "project_id": test_project.id,
            "order_title": "新建扩展测试采购订单",
            "items": [
                {
                    "material_code": "MAT-NEW-001",
                    "material_name": "新建测试物料",
                    "specification": "新建规格",
                    "unit": "件",
                    "quantity": 20,
                    "unit_price": 100.00,
                    "tax_rate": 13,
                }
            ],
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders",
            json=order_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["supplier_id"] == test_supplier.id
        assert data["order_title"] == order_data["order_title"]
        assert len(data["items"]) > 0

    def test_create_purchase_order_validation_error(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试创建采购订单验证错误 - 缺少必填字段"""
        order_data = {
            "order_title": "缺少供应商ID的订单",
            "items": [],
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders",
            json=order_data,
            headers=admin_auth_headers,
        )
        assert response.status_code in [400, 422]

    def test_create_purchase_order_no_items(
        self, client: TestClient, admin_auth_headers: dict, test_supplier: Supplier
    ):
        """测试创建采购订单 - 没有明细项"""
        order_data = {
            "supplier_id": test_supplier.id,
            "order_title": "没有明细的订单",
            "items": [],
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders",
            json=order_data,
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_create_purchase_order_invalid_supplier(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试创建采购订单 - 供应商不存在"""
        order_data = {
            "supplier_id": 999999,
            "order_title": "不存在的供应商",
            "items": [
                {
                    "material_code": "MAT-TEST-001",
                    "material_name": "测试物料",
                    "unit": "件",
                    "quantity": 10,
                    "unit_price": 50.00,
                }
            ],
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders",
            json=order_data,
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_update_purchase_order_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_purchase_order: PurchaseOrder,
    ):
        """测试更新采购订单成功"""
        update_data = {
            "order_title": "更新后的采购订单",
            "remark": "更新备注",
        }
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_purchase_order.id}",
            json=update_data,
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["order_title"] == update_data["order_title"]

    def test_update_purchase_order_not_draft(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_purchase_order: PurchaseOrder,
        db_session: Session,
    ):
        """测试更新采购订单 - 非草稿状态"""
        test_purchase_order.status = "SUBMITTED"
        db_session.merge(test_purchase_order)
        db_session.commit()

        update_data = {"order_title": "尝试更新已提交的订单"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_purchase_order.id}",
            json=update_data,
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_update_purchase_order_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试更新不存在的采购订单"""
        update_data = {"order_title": "不存在的订单"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/999999",
            json=update_data,
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_submit_purchase_order_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_purchase_order: PurchaseOrder,
    ):
        """测试提交采购订单成功"""
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_purchase_order.id}/submit",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_submit_purchase_order_not_draft(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_purchase_order: PurchaseOrder,
        db_session: Session,
    ):
        """测试提交采购订单 - 非草稿状态"""
        test_purchase_order.status = "SUBMITTED"
        db_session.merge(test_purchase_order)
        db_session.commit()

        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_purchase_order.id}/submit",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_approve_purchase_order_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_purchase_order: PurchaseOrder,
        db_session: Session,
    ):
        """测试审批采购订单成功"""
        test_purchase_order.status = "SUBMITTED"
        db_session.merge(test_purchase_order)
        db_session.commit()

        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_purchase_order.id}/approve?approved=true",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_approve_purchase_order_reject(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_purchase_order: PurchaseOrder,
        db_session: Session,
    ):
        """测试拒绝采购订单"""
        test_purchase_order.status = "SUBMITTED"
        db_session.merge(test_purchase_order)
        db_session.commit()

        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{test_purchase_order.id}/approve?approved=false&approval_note=不符合要求",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_purchase_orders_unauthorized(self, client: TestClient):
        """测试未授权访问采购订单"""
        response = client.get(f"{settings.API_V1_PREFIX}/purchase-orders")
        assert response.status_code == 401

    def test_list_purchase_orders_pagination(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试采购订单列表分页"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders?page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
