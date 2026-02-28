# -*- coding: utf-8 -*-
"""
Contract Model 测试
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models.sales.contracts import Contract


class TestContractModel:
    """Contract 模型测试"""

    def test_create_contract(self, db_session, sample_customer, sample_user):
        """测试创建合同"""
        contract = Contract(
            contract_code="CONTRACT001",
            contract_name="测试合同",
            customer_id=sample_customer.id,
            contract_type="销售合同",
            total_amount=Decimal("300000.00"),
            signing_date=date.today(),
            sales_owner_id=sample_user.id
        )
        db_session.add(contract)
        db_session.commit()
        
        assert contract.id is not None
        assert contract.contract_code == "CONTRACT001"
        assert contract.contract_amount == Decimal("300000.00")

    def test_contract_code_unique(self, db_session, sample_customer, sample_user):
        """测试合同编码唯一性"""
        c1 = Contract(
            contract_code="C001",
            contract_name="合同1",
            customer_id=sample_customer.id,
            sales_owner_id=sample_user.id
        )
        db_session.add(c1)
        db_session.commit()
        
        c2 = Contract(
            contract_code="C001",
            contract_name="合同2",
            customer_id=sample_customer.id,
            sales_owner_id=sample_user.id
        )
        db_session.add(c2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_contract_dates(self, db_session, sample_customer, sample_user):
        """测试合同日期"""
        signing = date.today()
        start = signing + timedelta(days=7)
        end = start + timedelta(days=365)
        
        contract = Contract(
            contract_code="C002",
            contract_name="日期测试",
            customer_id=sample_customer.id,
            sales_owner_id=sample_user.id,
            signing_date=signing,
            start_date=start,
            end_date=end
        )
        db_session.add(contract)
        db_session.commit()
        
        assert contract.signing_date == signing
        assert contract.start_date == start
        assert contract.end_date == end

    def test_contract_amount_fields(self, db_session, sample_customer, sample_user):
        """测试合同金额字段"""
        contract = Contract(
            contract_code="C003",
            contract_name="金额测试",
            customer_id=sample_customer.id,
            sales_owner_id=sample_user.id,
            contract_type="sales",
            total_amount=Decimal("580000.00")
        )
        db_session.add(contract)
        db_session.commit()
        
        assert contract.total_amount == Decimal("580000.00")

    def test_contract_status(self, db_session, sample_contract):
        """测试合同状态"""
        assert sample_contract.status == "SIGNED"
        
        sample_contract.status = "EXECUTING"
        db_session.commit()
        
        db_session.refresh(sample_contract)
        assert sample_contract.status == "EXECUTING"

    def test_contract_type(self, db_session, sample_customer, sample_user):
        """测试合同类型"""
        types = ["销售合同", "采购合同", "服务合同", "框架协议"]
        
        for i, ct in enumerate(types):
            contract = Contract(
                contract_code=f"C_TYPE_{i}",
                contract_name=f"{ct}测试",
                customer_id=sample_customer.id,
                sales_owner_id=sample_user.id,
                contract_type=ct
            )
            db_session.add(contract)
        db_session.commit()
        
        count = db_session.query(Contract).filter(
            Contract.contract_type.in_(types)
        ).count()
        assert count == len(types)

    def test_contract_relationships(self, db_session, sample_contract):
        """测试合同关系"""
        db_session.refresh(sample_contract)
        assert sample_contract.customer is not None
        assert sample_contract.owner is not None

    def test_contract_update(self, db_session, sample_contract):
        """测试更新合同"""
        sample_contract.contract_name = "更新后的合同"
        sample_contract.contract_amount = Decimal("350000.00")
        db_session.commit()
        
        db_session.refresh(sample_contract)
        assert sample_contract.contract_name == "更新后的合同"
        assert sample_contract.contract_amount == Decimal("350000.00")

    def test_contract_delete(self, db_session, sample_customer, sample_user):
        """测试删除合同"""
        contract = Contract(
            contract_code="C_DEL",
            contract_name="待删除",
            customer_id=sample_customer.id,
            sales_owner_id=sample_user.id
        )
        db_session.add(contract)
        db_session.commit()
        cid = contract.id
        
        db_session.delete(contract)
        db_session.commit()
        
        deleted = db_session.query(Contract).filter_by(id=cid).first()
        assert deleted is None

    def test_contract_payment_terms(self, db_session, sample_customer, sample_user):
        """测试合同付款条款"""
        contract = Contract(
            contract_code="C004",
            contract_name="付款测试",
            customer_id=sample_customer.id,
            sales_owner_id=sample_user.id,
            payment_terms="30%预付，60%进度款，10%质保金"
        )
        db_session.add(contract)
        db_session.commit()
        
        assert contract.payment_terms is not None

    def test_contract_description(self, db_session, sample_customer, sample_user):
        """测试合同描述"""
        desc = "这是一份关于智能制造系统的销售合同"
        contract = Contract(
            contract_code="C005",
            contract_name="描述测试",
            customer_id=sample_customer.id,
            sales_owner_id=sample_user.id,
            description=desc
        )
        db_session.add(contract)
        db_session.commit()
        
        assert contract.description == desc

    def test_multiple_contracts(self, db_session, sample_customer, sample_user):
        """测试多个合同"""
        contracts = [
            Contract(
                contract_code=f"C{i:03d}",
                contract_name=f"合同{i}",
                customer_id=sample_customer.id,
                sales_owner_id=sample_user.id,
                total_amount=Decimal(f"{i*50000}.00")
            ) for i in range(1, 6)
        ]
        db_session.add_all(contracts)
        db_session.commit()
        
        count = db_session.query(Contract).count()
        assert count >= 5
