# -*- coding: utf-8 -*-
"""
Invoice Model 测试
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models.sales.invoices import Invoice


class TestInvoiceModel:
    """Invoice 模型测试"""

    def test_create_invoice(self, db_session, sample_customer):
        """测试创建发票"""
        invoice = Invoice(
            invoice_code="INV001",
            invoice_amount=Decimal("10000.00"),
            customer_id=sample_customer.id,
            invoice_date=date.today()
        )
        db_session.add(invoice)
        db_session.commit()
        
        assert invoice.id is not None
        assert invoice.invoice_code == "INV001"
        assert invoice.invoice_amount == Decimal("10000.00")

    def test_invoice_code_unique(self, db_session, sample_customer):
        """测试发票编码唯一性"""
        i1 = Invoice(
            invoice_code="INV001",
            invoice_amount=Decimal("1000.00"),
            customer_id=sample_customer.id
        )
        db_session.add(i1)
        db_session.commit()
        
        i2 = Invoice(
            invoice_code="INV001",
            invoice_amount=Decimal("2000.00"),
            customer_id=sample_customer.id
        )
        db_session.add(i2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_invoice_amounts(self, db_session, sample_customer):
        """测试发票金额"""
        invoice = Invoice(
            invoice_code="INV002",
            invoice_amount=Decimal("10000.00"),
            tax_amount=Decimal("1600.00"),
            total_amount=Decimal("11600.00"),
            customer_id=sample_customer.id
        )
        db_session.add(invoice)
        db_session.commit()
        
        assert invoice.invoice_amount == Decimal("10000.00")
        assert invoice.tax_amount == Decimal("1600.00")
        assert invoice.total_amount == Decimal("11600.00")

    def test_invoice_type(self, db_session, sample_customer):
        """测试发票类型"""
        types = ["增值税专用发票", "增值税普通发票", "电子发票"]
        
        for i, it in enumerate(types):
            invoice = Invoice(
                invoice_code=f"INV_TYPE_{i}",
                invoice_amount=Decimal("1000.00"),
                customer_id=sample_customer.id,
                invoice_type=it
            )
            db_session.add(invoice)
        db_session.commit()
        
        count = db_session.query(Invoice).filter(
            Invoice.invoice_type.in_(types)
        ).count()
        assert count == len(types)

    def test_invoice_status(self, db_session, sample_invoice):
        """测试发票状态"""
        sample_invoice.status = "ISSUED"
        db_session.commit()
        
        db_session.refresh(sample_invoice)
        assert sample_invoice.status == "ISSUED"

    def test_invoice_dates(self, db_session, sample_customer):
        """测试发票日期"""
        issue_date = date.today()
        due_date = issue_date + timedelta(days=30)
        
        invoice = Invoice(
            invoice_code="INV003",
            invoice_amount=Decimal("5000.00"),
            customer_id=sample_customer.id,
            invoice_date=issue_date,
            due_date=due_date
        )
        db_session.add(invoice)
        db_session.commit()
        
        assert invoice.invoice_date == issue_date
        assert invoice.due_date == due_date

    def test_invoice_customer_relationship(self, db_session, sample_invoice):
        """测试发票-客户关系"""
        db_session.refresh(sample_invoice)
        assert sample_invoice.customer is not None

    def test_invoice_update(self, db_session, sample_invoice):
        """测试更新发票"""
        sample_invoice.invoice_amount = Decimal("15000.00")
        sample_invoice.status = "PAID"
        db_session.commit()
        
        db_session.refresh(sample_invoice)
        assert sample_invoice.invoice_amount == Decimal("15000.00")
        assert sample_invoice.status == "PAID"

    def test_invoice_delete(self, db_session, sample_customer):
        """测试删除发票"""
        invoice = Invoice(
            invoice_code="INV_DEL",
            invoice_amount=Decimal("1000.00"),
            customer_id=sample_customer.id
        )
        db_session.add(invoice)
        db_session.commit()
        iid = invoice.id
        
        db_session.delete(invoice)
        db_session.commit()
        
        deleted = db_session.query(Invoice).filter_by(id=iid).first()
        assert deleted is None

    def test_invoice_number_and_code(self, db_session, sample_customer):
        """测试发票号码和编码"""
        invoice = Invoice(
            invoice_code="INV004",
            invoice_number="1234567890",
            invoice_amount=Decimal("8000.00"),
            customer_id=sample_customer.id
        )
        db_session.add(invoice)
        db_session.commit()
        
        assert invoice.invoice_number == "1234567890"

    def test_multiple_invoices(self, db_session, sample_customer):
        """测试多个发票"""
        invoices = [
            Invoice(
                invoice_code=f"INV{i:03d}",
                invoice_amount=Decimal(f"{i*1000}.00"),
                customer_id=sample_customer.id
            ) for i in range(1, 6)
        ]
        db_session.add_all(invoices)
        db_session.commit()
        
        count = db_session.query(Invoice).count()
        assert count >= 5

    def test_invoice_description(self, db_session, sample_customer):
        """测试发票描述"""
        desc = "项目阶段性付款发票"
        invoice = Invoice(
            invoice_code="INV005",
            invoice_amount=Decimal("20000.00"),
            customer_id=sample_customer.id,
            description=desc
        )
        db_session.add(invoice)
        db_session.commit()
        
        assert invoice.description == desc
