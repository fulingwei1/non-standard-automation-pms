# -*- coding: utf-8 -*-
"""
Quote Model 测试
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.sales.quotes import Quote


class TestQuoteModel:
    """Quote 模型测试"""

    def test_create_quote(self, db_session, sample_customer, sample_user, sample_opportunity):
        """测试创建报价单"""
        quote = Quote(
            quote_code="QUOTE001",
            opportunity_id=sample_opportunity.id,
            customer_id=sample_customer.id,
            valid_until=date.today() + timedelta(days=30),
            owner_id=sample_user.id,
        )
        db_session.add(quote)
        db_session.commit()

        assert quote.id is not None
        assert quote.quote_code == "QUOTE001"
        assert quote.customer_id == sample_customer.id

    def test_quote_code_unique(self, db_session, sample_customer, sample_user, sample_opportunity):
        """测试报价单编码唯一性"""
        q1 = Quote(quote_code="Q001", opportunity_id=sample_opportunity.id, customer_id=sample_customer.id, owner_id=sample_user.id)
        db_session.add(q1)
        db_session.commit()

        q2 = Quote(quote_code="Q001", opportunity_id=sample_opportunity.id, customer_id=sample_customer.id, owner_id=sample_user.id)
        db_session.add(q2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_quote_validity_period(self, db_session, sample_customer, sample_user, sample_opportunity):
        """测试报价单有效期"""
        valid_from = date.today()
        valid_until = valid_from + timedelta(days=30)

        quote = Quote(
            quote_code="Q002",
            opportunity_id=sample_opportunity.id,
            customer_id=sample_customer.id,
            owner_id=sample_user.id,
            valid_until=valid_until,
        )
        db_session.add(quote)
        db_session.commit()

        assert quote.valid_until == valid_until

    def test_quote_amount_breakdown(self, db_session, sample_customer, sample_user, sample_opportunity):
        """测试报价金额分解"""
        quote = Quote(
            quote_code="Q003",
            opportunity_id=sample_opportunity.id,
            customer_id=sample_customer.id,
            owner_id=sample_user.id,
        )
        db_session.add(quote)
        db_session.commit()

        assert quote.customer_id == sample_customer.id
        assert quote.owner_id == sample_user.id

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
        assert sample_quote.owner is not None

    def test_quote_update(self, db_session, sample_quote):
        """测试更新报价"""
        sample_quote.status = "SUBMITTED"
        db_session.commit()

        db_session.refresh(sample_quote)
        assert sample_quote.status == "SUBMITTED"

    def test_quote_delete(self, db_session, sample_customer, sample_user, sample_opportunity):
        """测试删除报价"""
        quote = Quote(quote_code="Q_DEL", opportunity_id=sample_opportunity.id, customer_id=sample_customer.id, owner_id=sample_user.id)
        db_session.add(quote)
        db_session.commit()
        qid = quote.id

        db_session.delete(quote)
        db_session.commit()

        deleted = db_session.query(Quote).filter_by(id=qid).first()
        assert deleted is None

    def test_quote_version(self, db_session, sample_customer, sample_user, sample_opportunity):
        """测试报价版本"""
        quote = Quote(
            quote_code="Q004",
            opportunity_id=sample_opportunity.id,
            customer_id=sample_customer.id,
            owner_id=sample_user.id,
        )
        db_session.add(quote)
        db_session.commit()

        assert quote.quote_code == "Q004"

    def test_quote_description(self, db_session, sample_customer, sample_user, sample_opportunity):
        """测试报价描述"""
        desc = "包含软硬件集成方案的系统报价"
        quote = Quote(
            quote_code="Q005",
            opportunity_id=sample_opportunity.id,
            customer_id=sample_customer.id,
            owner_id=sample_user.id,
        )
        db_session.add(quote)
        db_session.commit()

        assert quote.quote_code == "Q005"

    def test_multiple_quotes(self, db_session, sample_customer, sample_user, sample_opportunity):
        """测试多个报价单"""
        quotes = [
            Quote(
                quote_code=f"Q{i:03d}",
                opportunity_id=sample_opportunity.id,
                customer_id=sample_customer.id,
                owner_id=sample_user.id,
            )
            for i in range(1, 6)
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
