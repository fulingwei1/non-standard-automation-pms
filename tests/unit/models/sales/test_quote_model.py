# -*- coding: utf-8 -*-
"""
Quote Model 测试
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models.sales.quotes import Quote


class TestQuoteModel:
    """Quote 模型测试"""

    def test_create_quote(self, db_session, sample_customer, sample_user):
        """测试创建报价单"""
        quote = Quote(
            quote_code="QUOTE001",
            customer_id=sample_customer.id,
            quote_amount=Decimal("150000.00"),
            valid_until=date.today() + timedelta(days=30),
            created_by=sample_user.id
        )
        db_session.add(quote)
        db_session.commit()
        
        assert quote.id is not None
        assert quote.quote_code == "QUOTE001"
        assert quote.quote_amount == Decimal("150000.00")

    def test_quote_code_unique(self, db_session, sample_customer, sample_user):
        """测试报价单编码唯一性"""
        q1 = Quote(
            quote_code="Q001",
            customer_id=sample_customer.id,
            created_by=sample_user.id
        )
        db_session.add(q1)
        db_session.commit()
        
        q2 = Quote(
            quote_code="Q001",
            customer_id=sample_customer.id,
            created_by=sample_user.id
        )
        db_session.add(q2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_quote_validity_period(self, db_session, sample_customer, sample_user):
        """测试报价单有效期"""
        valid_from = date.today()
        valid_until = valid_from + timedelta(days=30)
        
        quote = Quote(
            quote_code="Q002",
            customer_id=sample_customer.id,
            created_by=sample_user.id,
            valid_from=valid_from,
            valid_until=valid_until
        )
        db_session.add(quote)
        db_session.commit()
        
        assert quote.valid_from == valid_from
        assert quote.valid_until == valid_until

    def test_quote_amount_breakdown(self, db_session, sample_customer, sample_user):
        """测试报价金额分解"""
        quote = Quote(
            quote_code="Q003",
            customer_id=sample_customer.id,
            created_by=sample_user.id,
            quote_amount=Decimal("100000.00"),
            discount_amount=Decimal("5000.00"),
            tax_amount=Decimal("16000.00"),
            total_price=Decimal("111000.00")
        )
        db_session.add(quote)
        db_session.commit()
        
        assert quote.quote_amount == Decimal("100000.00")
        assert quote.discount_amount == Decimal("5000.00")
        assert quote.tax_amount == Decimal("16000.00")

    def test_quote_status(self, db_session, sample_quote):
        """测试报价状态"""
        assert sample_quote.status == "DRAFT"
        
        sample_quote.status = "SUBMITTED"
        db_session.commit()
        
        db_session.refresh(sample_quote)
        assert sample_quote.status == "SUBMITTED"

    def test_quote_relationships(self, db_session, sample_quote):
        """测试报价关系"""
        db_session.refresh(sample_quote)
        assert sample_quote.customer is not None
        assert sample_quote.creator is not None

    def test_quote_update(self, db_session, sample_quote):
        """测试更新报价"""
        sample_quote.quote_name = "更新后的报价"
        sample_quote.quote_amount = Decimal("180000.00")
        db_session.commit()
        
        db_session.refresh(sample_quote)
        assert sample_quote.quote_name == "更新后的报价"
        assert sample_quote.quote_amount == Decimal("180000.00")

    def test_quote_delete(self, db_session, sample_customer, sample_user):
        """测试删除报价"""
        quote = Quote(
            quote_code="Q_DEL",
            customer_id=sample_customer.id,
            created_by=sample_user.id
        )
        db_session.add(quote)
        db_session.commit()
        qid = quote.id
        
        db_session.delete(quote)
        db_session.commit()
        
        deleted = db_session.query(Quote).filter_by(id=qid).first()
        assert deleted is None

    def test_quote_version(self, db_session, sample_customer, sample_user):
        """测试报价版本"""
        quote = Quote(
            quote_code="Q004",
            customer_id=sample_customer.id,
            created_by=sample_user.id,
            version="1.0"
        )
        db_session.add(quote)
        db_session.commit()
        
        assert quote.version == "1.0"

    def test_quote_description(self, db_session, sample_customer, sample_user):
        """测试报价描述"""
        desc = "包含软硬件集成方案的系统报价"
        quote = Quote(
            quote_code="Q005",
            customer_id=sample_customer.id,
            created_by=sample_user.id,
            description=desc
        )
        db_session.add(quote)
        db_session.commit()
        
        assert quote.description == desc

    def test_multiple_quotes(self, db_session, sample_customer, sample_user):
        """测试多个报价单"""
        quotes = [
            Quote(
                quote_code=f"Q{i:03d}",
                customer_id=sample_customer.id,
                created_by=sample_user.id,
                quote_amount=Decimal(f"{i*10000}.00")
            ) for i in range(1, 6)
        ]
        db_session.add_all(quotes)
        db_session.commit()
        
        count = db_session.query(Quote).count()
        assert count >= 5

    def test_quote_approval(self, db_session, sample_quote):
        """测试报价审批"""
        sample_quote.status = "PENDING_APPROVAL"
        db_session.commit()
        
        db_session.refresh(sample_quote)
        assert sample_quote.status == "PENDING_APPROVAL"
        
        sample_quote.status = "APPROVED"
        db_session.commit()
        
        db_session.refresh(sample_quote)
        assert sample_quote.status == "APPROVED"
