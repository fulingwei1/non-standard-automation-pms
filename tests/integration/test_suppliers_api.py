# -*- coding: utf-8 -*-
"""
Integration tests for Suppliers API
Covers: app/api/v1/endpoints/suppliers.py
"""

from datetime import date
from decimal import Decimal


class TestSuppliersAPI:
    """供应商管理API集成测试"""

    def test_list_suppliers(self, client, admin_token):
        """测试获取供应商列表"""
        response = client.get(
            "/api/v1/suppliers/", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_list_suppliers_with_pagination(self, client, admin_token):
        """测试分页参数"""
        response = client.get(
            "/api/v1/suppliers/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_suppliers_with_filters(self, client, admin_token):
        """测试过滤参数"""
        response = client.get(
            "/api/v1/suppliers/?supplier_type=VENDOR&status=ACTIVE",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_list_suppliers_with_keyword_search(self, client, admin_token):
        """测试关键词搜索"""
        response = client.get(
            "/api/v1/suppliers/?keyword=测试",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_get_supplier_detail(self, client, admin_token, test_supplier):
        """测试获取供应商详情"""
        response = client.get(
            f"/api/v1/suppliers/{test_supplier.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_supplier.id
        assert data["supplier_name"] == test_supplier.supplier_name

    def test_get_supplier_not_found(self, client, admin_token):
        """测试获取不存在的供应商"""
        response = client.get(
            "/api/v1/suppliers/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_create_supplier(self, client, admin_token):
        """测试创建供应商"""
        supplier_data = {
            "supplier_name": "API测试供应商",
            "supplier_code": f"SUP-{date.today().strftime('%Y%m%d')}-001",
            "supplier_short_name": "测试供应商",
            "supplier_type": "VENDOR",
            "contact_person": "张三",
            "contact_phone": "13800138000",
            "contact_email": "test@supplier.com",
            "address": "测试地址",
        }
        response = client.post(
            "/api/v1/suppliers/",
            json=supplier_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["supplier_name"] == supplier_data["supplier_name"]
        assert "id" in data

    def test_create_supplier_duplicate_code(self, client, admin_token, test_supplier):
        """测试创建重复供应商编码"""
        supplier_data = {
            "supplier_name": "重复编码供应商",
            "supplier_code": test_supplier.supplier_code,
        }
        response = client.post(
            "/api/v1/suppliers/",
            json=supplier_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "已存在" in response.json().get("detail", "")

    def test_create_supplier_validation_error(self, client, admin_token):
        """测试创建供应商验证错误"""
        supplier_data = {}
        response = client.post(
            "/api/v1/suppliers/",
            json=supplier_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_update_supplier(self, client, admin_token, test_supplier):
        """测试更新供应商"""
        update_data = {
            "supplier_name": "更新后的供应商名称",
            "contact_person": "李四",
            "contact_phone": "13900139000",
        }
        response = client.put(
            f"/api/v1/suppliers/{test_supplier.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["supplier_name"] == update_data["supplier_name"]

    def test_update_supplier_not_found(self, client, admin_token):
        """测试更新不存在的供应商"""
        update_data = {"supplier_name": "不存在的供应商"}
        response = client.put(
            "/api/v1/suppliers/999999",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_update_supplier_rating(self, client, admin_token, test_supplier):
        """测试更新供应商评级"""
        response = client.put(
            f"/api/v1/suppliers/{test_supplier.id}/rating",
            params={
                "quality_rating": Decimal("4.5"),
                "delivery_rating": Decimal("4.0"),
                "service_rating": Decimal("4.2"),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quality_rating"] == Decimal("4.5")
        assert data["delivery_rating"] == Decimal("4.0")
        assert data["service_rating"] == Decimal("4.2")

    def test_update_supplier_rating_partial(self, client, admin_token, test_supplier):
        """测试部分更新供应商评级"""
        response = client.put(
            f"/api/v1/suppliers/{test_supplier.id}/rating",
            params={"quality_rating": Decimal("3.5")},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quality_rating"] == Decimal("3.5")

    def test_delete_supplier(self, client, admin_token, db_session):
        """测试删除供应商"""
        from app.models.material import Supplier

        supplier = Supplier(
            supplier_code=f"SUP-DELETE-{date.today().strftime('%Y%m%d')}",
            supplier_name="待删除测试供应商",
            contact_person="测试",
            contact_phone="13800000000",
            supplier_type="VENDOR",
            status="ACTIVE",
        )
        db_session.add(supplier)
        db_session.commit()
        db_session.refresh(supplier)

        response = client.delete(
            f"/api/v1/suppliers/{supplier.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_delete_supplier_not_found(self, client, admin_token):
        """测试删除不存在的供应商"""
        response = client.delete(
            "/api/v1/suppliers/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


class TestSuppliersAPIAuth:
    """供应商API认证测试"""

    def test_list_suppliers_without_token(self, client):
        """测试无token访问"""
        response = client.get("/api/v1/suppliers/")
        assert response.status_code == 401

    def test_get_supplier_without_token(self, client):
        """测试无token获取详情"""
        response = client.get("/api/v1/suppliers/1")
        assert response.status_code == 401

    def test_create_supplier_without_token(self, client):
        """测试无token创建"""
        response = client.post("/api/v1/suppliers/", json={"supplier_name": "测试"})
        assert response.status_code == 401


class TestSuppliersAPISorting:
    """供应商API排序测试"""

    def test_sort_by_created_at_desc(self, client, admin_token):
        """测试按创建时间降序排序"""
        response = client.get(
            "/api/v1/suppliers/?order_by=created_at&order=desc",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_sort_by_supplier_name_asc(self, client, admin_token):
        """测试按供应商名称升序排序"""
        response = client.get(
            "/api/v1/suppliers/?order_by=supplier_name&order=asc",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200


class TestSuppliersAPIValidation:
    """供应商API验证测试"""

    def test_invalid_page_number(self, client, admin_token):
        """测试无效页码"""
        response = client.get(
            "/api/v1/suppliers/?page=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_invalid_rating_value(self, client, admin_token, test_supplier):
        """测试无效评分值"""
        response = client.put(
            f"/api/v1/suppliers/{test_supplier.id}/rating",
            params={"quality_rating": Decimal("6.0")},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_empty_keyword_search(self, client, admin_token):
        """测试空关键词搜索"""
        response = client.get(
            "/api/v1/suppliers/?keyword=",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
