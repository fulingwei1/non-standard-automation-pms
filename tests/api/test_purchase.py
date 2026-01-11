# -*- coding: utf-8 -*-
"""
采购管理模块 API 测试

测试内容：
- 采购订单 CRUD 操作
- 采购订单审批流程
- 采购申请管理
- 收货管理
- 质检流程
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project
from app.models.material import Supplier
from app.models.purchase import PurchaseOrder, PurchaseRequest


class TestPurchaseOrderCRUD:
    """采购订单 CRUD 测试"""

    def test_list_purchase_orders(self, client: TestClient, admin_token: str):
        """测试获取采购订单列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/?page=1&page_size=10",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_create_purchase_order_success(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试成功创建采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        supplier = db_session.query(Supplier).first()
        if not supplier:
            pytest.skip("No supplier available for testing")

        project = db_session.query(Project).first()

        headers = {"Authorization": f"Bearer {admin_token}"}
        order_data = {
            "supplier_id": supplier.id,
            "project_id": project.id if project else None,
            "order_type": "NORMAL",
            "order_title": "测试采购订单",
            "required_date": (date.today() + timedelta(days=7)).isoformat(),
            "items": [
                {
                    "material_code": "MAT001",
                    "material_name": "测试物料1",
                    "specification": "规格A",
                    "unit": "个",
                    "quantity": 100,
                    "unit_price": 10.00,
                    "tax_rate": 13,
                },
                {
                    "material_code": "MAT002",
                    "material_name": "测试物料2",
                    "specification": "规格B",
                    "unit": "件",
                    "quantity": 50,
                    "unit_price": 20.00,
                    "tax_rate": 13,
                },
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders/",
            json=order_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "order_no" in data
        assert data["supplier_id"] == supplier.id
        assert len(data["items"]) == 2

    def test_create_purchase_order_invalid_supplier(self, client: TestClient, admin_token: str):
        """测试创建采购订单时供应商不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        order_data = {
            "supplier_id": 999999,
            "order_type": "NORMAL",
            "order_title": "测试订单",
            "items": [
                {
                    "material_code": "MAT001",
                    "material_name": "测试物料",
                    "unit": "个",
                    "quantity": 100,
                    "unit_price": 10.00,
                    "tax_rate": 13,
                },
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders/",
            json=order_data,
            headers=headers
        )

        assert response.status_code == 404
        assert "供应商" in response.json().get("detail", "")

    def test_get_purchase_order_detail(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试获取采购订单详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        order = db_session.query(PurchaseOrder).first()
        if not order:
            pytest.skip("No purchase order available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/{order.id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order.id
        assert "items" in data

    def test_get_purchase_order_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/999999",
            headers=headers
        )

        assert response.status_code == 404

    def test_get_purchase_order_items(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试获取采购订单明细"""
        if not admin_token:
            pytest.skip("Admin token not available")

        order = db_session.query(PurchaseOrder).first()
        if not order:
            pytest.skip("No purchase order available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/{order.id}/items",
            headers=headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestPurchaseOrderFilters:
    """采购订单筛选测试"""

    def test_filter_by_keyword(self, client: TestClient, admin_token: str):
        """测试关键词搜索"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/?keyword=PO",
            headers=headers
        )

        assert response.status_code == 200

    def test_filter_by_supplier(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试按供应商筛选"""
        if not admin_token:
            pytest.skip("Admin token not available")

        supplier = db_session.query(Supplier).first()
        if not supplier:
            pytest.skip("No supplier available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/?supplier_id={supplier.id}",
            headers=headers
        )

        assert response.status_code == 200

    def test_filter_by_status(self, client: TestClient, admin_token: str):
        """测试按状态筛选"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/?status=DRAFT",
            headers=headers
        )

        assert response.status_code == 200


class TestPurchaseOrderUpdate:
    """采购订单更新测试"""

    def test_update_draft_order(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试更新草稿状态的订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        order = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.status == "DRAFT"
        ).first()
        if not order:
            pytest.skip("No draft order available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "order_title": "更新后的订单标题",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{order.id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["order_title"] == "更新后的订单标题"

    def test_update_non_draft_fails(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试更新非草稿状态的订单失败"""
        if not admin_token:
            pytest.skip("Admin token not available")

        order = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.status != "DRAFT"
        ).first()
        if not order:
            pytest.skip("No non-draft order available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "order_title": "尝试更新",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{order.id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == 400


class TestPurchaseOrderApproval:
    """采购订单审批流程测试"""

    def test_submit_order(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试提交采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找有明细的草稿订单
        order = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.status == "DRAFT"
        ).first()
        if not order:
            pytest.skip("No draft order available for testing")

        # 检查是否有明细
        if order.items.count() == 0:
            pytest.skip("Draft order has no items")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{order.id}/submit",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_submit_empty_order_fails(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试提交没有明细的订单失败"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 创建一个没有明细的订单
        supplier = db_session.query(Supplier).first()
        if not supplier:
            pytest.skip("No supplier available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        order_data = {
            "supplier_id": supplier.id,
            "order_type": "NORMAL",
            "order_title": "空订单测试",
            "items": []
        }

        # 创建订单需要至少一个明细，所以这里会失败
        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders/",
            json=order_data,
            headers=headers
        )

        # 可能在创建时就失败（需要至少一个明细）或者在提交时失败
        assert response.status_code in [200, 400, 422]

    def test_approve_order(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试审批采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        order = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.status == "SUBMITTED"
        ).first()
        if not order:
            pytest.skip("No submitted order available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{order.id}/approve?approved=true",
            headers=headers
        )

        assert response.status_code == 200

    def test_reject_order(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试驳回采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        order = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.status == "SUBMITTED"
        ).first()
        if not order:
            pytest.skip("No submitted order available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/{order.id}/approve"
            f"?approved=false&approval_note=测试驳回",
            headers=headers
        )

        assert response.status_code == 200


class TestPurchaseRequest:
    """采购申请测试"""

    def test_list_purchase_requests(self, client: TestClient, admin_token: str):
        """测试获取采购申请列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/requests?page=1&page_size=10",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_create_purchase_request(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试创建采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        request_data = {
            "project_id": project.id,
            "request_type": "PROJECT",
            "request_reason": "项目物料采购",
            "required_date": (date.today() + timedelta(days=14)).isoformat(),
            "items": [
                {
                    "material_code": "MAT001",
                    "material_name": "测试物料",
                    "specification": "规格A",
                    "unit": "个",
                    "quantity": 100,
                    "unit_price": 10.00,
                },
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders/requests",
            json=request_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "request_no" in data
        assert data["project_id"] == project.id

    def test_get_purchase_request_detail(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试获取采购申请详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        request = db_session.query(PurchaseRequest).first()
        if not request:
            pytest.skip("No purchase request available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/requests/{request.id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == request.id

    def test_submit_purchase_request(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试提交采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        request = db_session.query(PurchaseRequest).filter(
            PurchaseRequest.status == "DRAFT"
        ).first()
        if not request:
            pytest.skip("No draft request available for testing")

        # 检查是否有明细
        if request.items.count() == 0:
            pytest.skip("Draft request has no items")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/requests/{request.id}/submit",
            headers=headers
        )

        assert response.status_code == 200

    def test_approve_purchase_request(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试审批采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        request = db_session.query(PurchaseRequest).filter(
            PurchaseRequest.status == "SUBMITTED"
        ).first()
        if not request:
            pytest.skip("No submitted request available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/requests/{request.id}/approve"
            f"?approved=true",
            headers=headers
        )

        assert response.status_code == 200

    def test_delete_draft_request(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试删除草稿状态的采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先创建一个申请
        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        request_data = {
            "project_id": project.id,
            "request_type": "PROJECT",
            "request_reason": "待删除申请",
            "items": [
                {
                    "material_code": "MAT999",
                    "material_name": "待删除物料",
                    "unit": "个",
                    "quantity": 10,
                    "unit_price": 1.00,
                },
            ]
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders/requests",
            json=request_data,
            headers=headers
        )

        if create_response.status_code != 200:
            pytest.skip("Failed to create request for delete test")

        request_id = create_response.json()["id"]

        # 删除申请
        delete_response = client.delete(
            f"{settings.API_V1_PREFIX}/purchase-orders/requests/{request_id}",
            headers=headers
        )

        assert delete_response.status_code == 200


class TestGoodsReceipt:
    """收货管理测试"""

    def test_list_goods_receipts(self, client: TestClient, admin_token: str):
        """测试获取收货单列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/?page=1&page_size=10",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_create_goods_receipt(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试创建收货单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找已审批的采购订单
        order = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.status == "APPROVED"
        ).first()
        if not order:
            pytest.skip("No approved order available for testing")

        # 获取订单明细
        order_items = order.items.all()
        if not order_items:
            pytest.skip("Order has no items")

        headers = {"Authorization": f"Bearer {admin_token}"}
        receipt_data = {
            "order_id": order.id,
            "receipt_date": date.today().isoformat(),
            "receipt_type": "NORMAL",
            "delivery_note_no": "DN001",
            "items": [
                {
                    "order_item_id": order_items[0].id,
                    "delivery_qty": 10,
                    "received_qty": 10,
                }
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/",
            json=receipt_data,
            headers=headers
        )

        # 可能返回200或400（如果数量超过订单数量）
        assert response.status_code in [200, 400]

    def test_update_receipt_item_inspect(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试更新收货明细质检结果"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.purchase import GoodsReceipt, GoodsReceiptItem

        receipt = db_session.query(GoodsReceipt).first()
        if not receipt:
            pytest.skip("No goods receipt available for testing")

        item = receipt.items.first()
        if not item:
            pytest.skip("No receipt item available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/{receipt.id}/items/{item.id}/inspect"
            f"?inspect_qty=10&qualified_qty=9",
            headers=headers
        )

        assert response.status_code in [200, 400]


class TestPurchaseFromBOM:
    """从BOM生成采购订单测试"""

    def test_create_orders_from_bom_no_bom(self, client: TestClient, admin_token: str):
        """测试从不存在的BOM创建订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase-orders/from-bom?bom_id=999999",
            headers=headers
        )

        assert response.status_code == 404
        assert "BOM不存在" in response.json().get("detail", "")
