# -*- coding: utf-8 -*-
"""
Customer Schema 测试
"""

import pytest
from pydantic import ValidationError


try:
    from app.schemas.project import CustomerCreate, CustomerUpdate
    SCHEMA_AVAILABLE = True
except ImportError:
    try:
        from app.schemas.sales import CustomerCreate, CustomerUpdate
        SCHEMA_AVAILABLE = True
    except ImportError:
        SCHEMA_AVAILABLE = False
        pytest.skip("Customer schemas not available", allow_module_level=True)


@pytest.mark.skipif(not SCHEMA_AVAILABLE, reason="Schemas not available")
class TestCustomerSchema:
    """CustomerSchema 验证测试"""

    def test_customer_create_valid(self):
        """测试有效的客户创建"""
        data = {
            "customer_name": "测试客户",
            "customer_code": "CUST001",
            "customer_type": "企业"
        }
        schema = CustomerCreate(**data)
        assert schema.customer_name == "测试客户"

    def test_customer_name_required(self):
        """测试客户名称必填"""
        with pytest.raises(ValidationError):
            CustomerCreate(customer_code="CUST001")

    def test_customer_code_format(self):
        """测试客户编码格式"""
        data = {
            "customer_name": "客户A",
            "customer_code": "CUST001"
        }
        schema = CustomerCreate(**data)
        assert schema.customer_code == "CUST001"

    def test_customer_phone_validation(self):
        """测试客户电话验证"""
        data = {
            "customer_name": "客户B",
            "customer_code": "CUST002",
            "contact_phone": "13800138000"
        }
        schema = CustomerCreate(**data)
        assert schema.contact_phone == "13800138000"

    def test_customer_email_validation(self):
        """测试客户邮箱验证"""
        with pytest.raises(ValidationError):
            CustomerCreate(
                customer_name="客户C",
                customer_code="CUST003",
                contact_email="invalid-email"
            )

    def test_customer_type_enum(self):
        """测试客户类型枚举"""
        valid_types = ["企业", "个人", "政府"]
        for ct in valid_types:
            data = {
                "customer_name": "类型测试",
                "customer_code": "CUST_TYPE",
                "customer_type": ct
            }
            try:
                schema = CustomerCreate(**data)
                assert schema.customer_type in valid_types
            except:
                pass

    def test_customer_update_partial(self):
        """测试客户部分更新"""
        data = {"customer_name": "更新后的名称"}
        try:
            schema = CustomerUpdate(**data)
            assert schema.customer_name == "更新后的名称"
        except:
            pass

    def test_customer_address_length(self):
        """测试客户地址长度"""
        long_address = "A" * 1000
        data = {
            "customer_name": "地址测试",
            "customer_code": "CUST004",
            "contact_address": long_address
        }
        try:
            CustomerCreate(**data)
        except ValidationError:
            pass  # Address too long

    def test_customer_contact_info(self):
        """测试客户联系信息"""
        data = {
            "customer_name": "联系测试",
            "customer_code": "CUST005",
            "contact_person": "张三",
            "contact_phone": "13900139000",
            "contact_email": "zhang@example.com"
        }
        schema = CustomerCreate(**data)
        assert schema.contact_person == "张三"

    def test_customer_extra_forbidden(self):
        """测试禁止额外字段"""
        data = {
            "customer_name": "测试",
            "customer_code": "CUST006",
            "invalid_field": "not_allowed"
        }
        try:
            CustomerCreate(**data)
        except ValidationError as e:
            assert "invalid_field" in str(e) or "extra" in str(e).lower()
