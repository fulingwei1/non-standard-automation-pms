# -*- coding: utf-8 -*-
"""
供应商管理模块 API 集成测试

测试范围：
- 供应商CRUD (CRUD)
- 供应商评级 (Rating)
- 供应商分类 (Category)
- 供应商物料关联 (Material Relations)
"""

import pytest
from datetime import date

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator, Colors


@pytest.mark.integration
class TestSuppliersCRUDAPI:
    """供应商CRUD API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("供应商CRUD API 测试")

    def test_create_supplier(self):
        """测试创建供应商"""
        self.helper.print_info("测试创建供应商...")

        supplier_data = {
            "supplier_code": f"SUP-{TestDataGenerator.generate_order_no()}",
            "supplier_name": "精密加工厂",
            "supplier_short_name": "精密厂",
            "supplier_type": "MACHINING",
            "industry": "PRECISION_MACHINING",
            "level": "A",
            "contact_person": "王经理",
            "contact_phone": "13900139001",
            "contact_email": "wang@precision.com",
            "province": "广东省",
            "city": "深圳市",
            "address": "科技园北区123号",
            "website": "www.precision.com",
            "business_scope": "精密零件加工、表面处理",
            "annual_capcity": 5000000.00,
            "delivery_lead_time_days": 7,
            "quality_level": "HIGH",
            "is_active": True,
        }

        response = self.helper.post(
            "/suppliers", supplier_data, resource_type="supplier"
        )

        result = self.helper.assert_success(response)
        if result:
            supplier_id = result.get("id")
            if supplier_id:
                self.tracked_resources.append(("supplier", supplier_id))
                self.helper.print_success(f"供应商创建成功，ID: {supplier_id}")
                self.helper.assert_field_equals(result, "supplier_name", "精密加工厂")
            else:
                self.helper.print_warning("供应商创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建供应商响应不符合预期，继续测试")

    def test_get_suppliers_list(self):
        """测试获取供应商列表"""
        self.helper.print_info("测试获取供应商列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "supplier_type": "MACHINING",
            "is_active": True,
        }

        response = self.helper.get(
            "/suppliers", params=params, resource_type="suppliers_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个供应商")
        else:
            self.helper.print_warning("获取供应商列表响应不符合预期")

    def test_get_supplier_detail(self):
        """测试获取供应商详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的供应商ID")

        supplier_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取供应商详情 (ID: {supplier_id})...")

        response = self.helper.get(
            f"/suppliers/{supplier_id}", resource_type=f"supplier_{supplier_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("供应商详情获取成功")
        else:
            self.helper.print_warning("获取供应商详情响应不符合预期")

    def test_update_supplier(self):
        """测试更新供应商"""
        if not self.tracked_resources:
            pytest.skip("没有可用的供应商ID")

        supplier_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新供应商 (ID: {supplier_id})...")

        update_data = {
            "quality_level": "VERY_HIGH",
            "delivery_lead_time_days": 5,
            "annual_capcity": 8000000.00,
            "contact_phone": "13900139002",
            "website": "www.precision-new.com",
        }

        response = self.helper.put(
            f"/suppliers/{supplier_id}",
            update_data,
            resource_type=f"supplier_{supplier_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("供应商更新成功")
        else:
            self.helper.print_warning("更新供应商响应不符合预期")

    def test_deactivate_supplier(self):
        """测试停用供应商"""
        if not self.tracked_resources:
            pytest.skip("没有可用的供应商ID")

        supplier_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试停用供应商 (ID: {supplier_id})...")

        response = self.helper.delete(
            f"/suppliers/{supplier_id}",
            resource_type=f"supplier_{supplier_id}_deactivate",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("供应商停用成功")
        else:
            self.helper.print_warning("停用供应商响应不符合预期")


@pytest.mark.integration
class TestSuppliersRatingAPI:
    """供应商评级 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_supplier_id = 1  # 假设存在供应商ID
        self.tracked_resources = []
        self.helper.print_info("供应商评级 API 测试")

    def test_rate_supplier(self):
        """测试给供应商评分"""
        self.helper.print_info("测试给供应商评分...")

        rating_data = {
            "supplier_id": self.test_supplier_id,
            "rating": 4.5,
            "rating_type": "QUALITY",
            "rating_period": "month",
            "delivery_timeliness": 5,
            "product_quality": 5,
            "service_attitude": 5,
            "technical_capability": 4,
            "comments": "整体表现优秀",
            "rated_by": 1,  # 假设存在用户ID
            "rating_date": date.today().isoformat(),
        }

        response = self.helper.post(
            "/ratings", rating_data, resource_type="supplier_rating"
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            rating_id = result.get("id")
            if rating_id:
                self.tracked_resources.append(("rating", rating_id))
                self.helper.print_success(f"评分创建成功，ID: {rating_id}")
            else:
                self.helper.print_warning("评分创建成功，但未返回ID")
        else:
            self.helper.print_warning("评分创建响应不符合预期，继续测试")

    def test_get_supplier_ratings_list(self):
        """测试获取供应商评分列表"""
        self.helper.print_info("测试获取供应商评分列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "supplier_id": self.test_supplier_id,
        }

        response = self.helper.get(
            "/ratings", params=params, resource_type="supplier_ratings_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条评分记录")
        else:
            self.helper.print_warning("获取评分列表响应不符合预期")

    def test_get_supplier_summary(self):
        """测试获取供应商汇总"""
        self.helper.print_info("测试获取供应商汇总...")

        params = {
            "period": "quarter",
            "year": date.today().year,
            "quarter": (date.today().month - 1) // 3 + 1,
            "supplier_id": self.test_supplier_id,
        }

        response = self.helper.get(
            "/ratings/summary", params=params, resource_type="supplier_summary"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("供应商汇总获取成功")
        else:
            self.helper.print_warning("获取供应商汇总响应不符合预期")


@pytest.mark.integration
class TestSuppliersMaterialsAPI:
    """供应商物料关联 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_supplier_id = 1  # 假设存在供应商ID
        self.test_material_id = 1  # 假设存在物料ID
        self.tracked_resources = []
        self.helper.print_info("供应商物料关联 API 测试")

    def test_add_material_to_supplier(self):
        """测试添加物料到供应商"""
        self.helper.print_info("测试添加物料到供应商...")

        association_data = {
            "supplier_id": self.test_supplier_id,
            "material_ids": [self.test_material_id],
            "supply_capacity": "HIGH",
            "lead_time_days": 7,
            "notes": "该供应商可以快速交付该物料",
        }

        response = self.helper.post(
            "/materials/add",
            association_data,
            resource_type="supplier_material_relation",
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            relation_id = result.get("id")
            if relation_id:
                self.tracked_resources.append(("relation", relation_id))
                self.helper.print_success(f"物料关联创建成功，ID: {relation_id}")
            else:
                self.helper.print_warning("物料关联创建成功，但未返回ID")
        else:
            self.helper.print_warning("物料关联创建响应不符合预期，继续测试")

    def test_get_supplier_materials(self):
        """测试获取供应商物料列表"""
        self.helper.print_info("测试获取供应商物料列表...")

        params = {
            "supplier_id": self.test_supplier_id,
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            f"/suppliers/{self.test_supplier_id}/materials",
            params=params,
            resource_type=f"supplier_{self.test_supplier_id}_materials",
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个关联物料")
        else:
            self.helper.print_warning("获取供应商物料响应不符合预期")

    def test_get_supplier_categories(self):
        """测试获取供应商分类"""
        self.helper.print_info("测试获取供应商分类...")

        response = self.helper.get(
            "/suppliers/categories", resource_type="supplier_categories"
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个供应商分类")
        else:
            self.helper.print_warning("获取供应商分类响应不符合预期")

    def test_get_supplier_products(self):
        """测试获取供应商产品"""
        if not self.tracked_resources:
            pytest.skip("没有可用的供应商ID")

        supplier_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取供应商产品 (ID: {supplier_id})...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            f"/suppliers/{supplier_id}/products",
            params=params,
            resource_type=f"supplier_{supplier_id}_products",
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个产品")
        else:
            self.helper.print_warning("获取供应商产品响应不符合预期")


@pytest.mark.integration
class TestSuppliersQualityAPI:
    """供应商质检API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_supplier_id = 1  # 假设存在供应商ID
        self.tracked_resources = []
        self.helper.print_info("供应商质检 API 测试")

    def test_create_inspection(self):
        """测试创建质检记录"""
        self.helper.print_info("测试创建质检记录...")

        inspection_data = {
            "supplier_id": self.test_supplier_id,
            "inspection_date": date.today().isoformat(),
            "inspection_type": "INCOMING",
            "inspector": "张质检",
            "items": [
                {
                    "item_id": 1,  # 假设存在物料ID
                    "inspection_result": "QUALIFIED",
                    "defect_description": "",
                    "quantity": 100,
                },
            ],
            "overall_result": "QUALIFIED",
            "notes": "供应商质量符合要求",
        }

        response = self.helper.post(
            "/quality/inspections", inspection_data, resource_type="quality_inspection"
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            inspection_id = result.get("id")
            if inspection_id:
                self.tracked_resources.append(("inspection", inspection_id))
                self.helper.print_success(f"质检记录创建成功，ID: {inspection_id}")
            else:
                self.helper.print_warning("质检记录创建成功，但未返回ID")
        else:
            self.helper.print_warning("质检记录创建响应不符合预期，继续测试")

    def test_get_inspections_list(self):
        """测试获取质检列表"""
        self.helper.print_info("测试获取质检列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "supplier_id": self.test_supplier_id,
            "inspection_type": "INCOMING",
        }

        response = self.helper.get(
            "/quality/inspections", params=params, resource_type="inspections_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条质检记录")
        else:
            self.helper.print_warning("获取质检列表响应不符合预期")

    def test_get_supplier_quality_summary(self):
        """测试获取质量汇总"""
        self.helper.print_info("测试获取质量汇总...")

        params = {
            "period": "year",
            "year": date.today().year,
            "supplier_id": self.test_supplier_id,
        }

        response = self.helper.get(
            "/quality/summary", params=params, resource_type="quality_summary"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("质量汇总获取成功")
        else:
            self.helper.print_warning("获取质量汇总响应不符合预期")
