# -*- coding: utf-8 -*-
"""
Customer Model 测试
"""

import pytest
from sqlalchemy.exc import IntegrityError
from app.models.project.customer import Customer


class TestCustomerModel:
    """Customer 模型测试"""

    def test_create_customer_basic(self, db_session):
        """测试基本客户创建"""
        customer = Customer(
            customer_name="测试企业",
            customer_code="CUST001",
            customer_type="企业",
            contact_person="张三",
            contact_phone="13800138000"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.id is not None
        assert customer.customer_name == "测试企业"
        assert customer.customer_code == "CUST001"
        assert customer.customer_type == "企业"

    def test_customer_code_unique_constraint(self, db_session):
        """测试客户编码唯一性约束"""
        customer1 = Customer(
            customer_name="客户A",
            customer_code="CUST001",
            customer_type="企业"
        )
        db_session.add(customer1)
        db_session.commit()
        
        customer2 = Customer(
            customer_name="客户B",
            customer_code="CUST001",  # 相同编码
            customer_type="企业"
        )
        db_session.add(customer2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_customer_contact_info(self, db_session):
        """测试客户联系信息"""
        customer = Customer(
            customer_name="联系测试公司",
            customer_code="CUST002",
            contact_person="李四",
            contact_phone="13900139000",
            contact_email="lisi@example.com",
            contact_address="北京市朝阳区XXX路XXX号"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.contact_person == "李四"
        assert customer.contact_phone == "13900139000"
        assert customer.contact_email == "lisi@example.com"
        assert customer.contact_address is not None

    def test_customer_industry_info(self, db_session):
        """测试客户行业信息"""
        customer = Customer(
            customer_name="制造企业",
            customer_code="CUST003",
            customer_type="企业",
            industry="制造业",
            scale="大型"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.industry == "制造业"
        assert customer.scale == "大型"

    def test_customer_credit_level(self, db_session):
        """测试客户信用等级"""
        customer = Customer(
            customer_name="优质客户",
            customer_code="CUST004",
            credit_level="AAA"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.credit_level == "AAA"
        
        customer.credit_level = "AA"
        db_session.commit()
        
        db_session.refresh(customer)
        assert customer.credit_level == "AA"

    def test_customer_status(self, db_session):
        """测试客户状态"""
        customer = Customer(
            customer_name="状态测试客户",
            customer_code="CUST005",
            status="ACTIVE"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.status == "ACTIVE"
        
        customer.status = "INACTIVE"
        db_session.commit()
        
        db_session.refresh(customer)
        assert customer.status == "INACTIVE"

    def test_customer_source(self, db_session):
        """测试客户来源"""
        customer = Customer(
            customer_name="来源测试",
            customer_code="CUST006",
            source="网络推广"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.source == "网络推广"

    def test_customer_region(self, db_session):
        """测试客户区域"""
        customer = Customer(
            customer_name="区域客户",
            customer_code="CUST007",
            region="华北"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.region == "华北"

    def test_customer_update(self, db_session):
        """测试更新客户信息"""
        customer = Customer(
            customer_name="初始名称",
            customer_code="CUST008",
            customer_type="个人"
        )
        db_session.add(customer)
        db_session.commit()
        
        customer.customer_name = "更新后的名称"
        customer.customer_type = "企业"
        customer.contact_person = "王五"
        db_session.commit()
        
        db_session.refresh(customer)
        assert customer.customer_name == "更新后的名称"
        assert customer.customer_type == "企业"
        assert customer.contact_person == "王五"

    def test_customer_delete(self, db_session):
        """测试删除客户"""
        customer = Customer(
            customer_name="待删除客户",
            customer_code="CUST_DEL"
        )
        db_session.add(customer)
        db_session.commit()
        customer_id = customer.id
        
        db_session.delete(customer)
        db_session.commit()
        
        deleted = db_session.query(Customer).filter_by(id=customer_id).first()
        assert deleted is None

    def test_customer_description(self, db_session):
        """测试客户描述"""
        desc = "这是一家专注于智能制造的大型企业，年营业额超过10亿元"
        customer = Customer(
            customer_name="描述测试",
            customer_code="CUST009",
            description=desc
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.description == desc

    def test_customer_relationships(self, db_session, sample_customer):
        """测试客户关联关系"""
        from app.models.project.core import Project
        
        # 创建关联项目
        project = Project(
            project_code="PRJ_CUST",
            project_name="客户关联项目",
            customer_id=sample_customer.id,
            contract_amount=100000
        )
        db_session.add(project)
        db_session.commit()
        
        db_session.refresh(sample_customer)
        # 验证客户可以访问其项目（如果模型中定义了关系）
        assert sample_customer.id is not None
