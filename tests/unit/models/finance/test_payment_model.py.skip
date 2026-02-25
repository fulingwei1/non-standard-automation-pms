# -*- coding: utf-8 -*-
"""
Payment Model 测试
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.models.finance import Payment


class TestPaymentModel:
    """Payment 模型测试"""

    def test_create_payment(self, db_session, sample_project):
        """测试创建付款"""
        payment = Payment(
            payment_code="PAY001",
            payment_amount=Decimal("5000.00"),
            project_id=sample_project.id,
            payment_date=date.today()
        )
        db_session.add(payment)
        db_session.commit()
        
        assert payment.id is not None
        assert payment.payment_code == "PAY001"
        assert payment.payment_amount == Decimal("5000.00")

    def test_payment_type(self, db_session, sample_project):
        """测试付款类型"""
        types = ["预付款", "进度款", "尾款", "质保金"]
        
        for i, pt in enumerate(types):
            payment = Payment(
                payment_code=f"PAY_TYPE_{i}",
                payment_amount=Decimal("1000.00"),
                project_id=sample_project.id,
                payment_type=pt
            )
            db_session.add(payment)
        db_session.commit()
        
        count = db_session.query(Payment).filter(
            Payment.payment_type.in_(types)
        ).count()
        assert count == len(types)

    def test_payment_method(self, db_session, sample_project):
        """测试付款方式"""
        payment = Payment(
            payment_code="PAY002",
            payment_amount=Decimal("3000.00"),
            project_id=sample_project.id,
            payment_method="银行转账"
        )
        db_session.add(payment)
        db_session.commit()
        
        assert payment.payment_method == "银行转账"

    def test_payment_status(self, db_session, sample_payment):
        """测试付款状态"""
        sample_payment.status = "PENDING"
        db_session.commit()
        
        db_session.refresh(sample_payment)
        assert sample_payment.status == "PENDING"

    def test_payment_dates(self, db_session, sample_project):
        """测试付款日期"""
        plan_date = date.today() + timedelta(days=7)
        actual_date = date.today()
        
        payment = Payment(
            payment_code="PAY003",
            payment_amount=Decimal("10000.00"),
            project_id=sample_project.id,
            planned_payment_date=plan_date,
            payment_date=actual_date
        )
        db_session.add(payment)
        db_session.commit()
        
        assert payment.planned_payment_date == plan_date
        assert payment.payment_date == actual_date

    def test_payment_project_relationship(self, db_session, sample_payment):
        """测试付款-项目关系"""
        db_session.refresh(sample_payment)
        assert sample_payment.project is not None

    def test_payment_update(self, db_session, sample_payment):
        """测试更新付款"""
        sample_payment.payment_amount = Decimal("6000.00")
        sample_payment.status = "COMPLETED"
        db_session.commit()
        
        db_session.refresh(sample_payment)
        assert sample_payment.payment_amount == Decimal("6000.00")

    def test_payment_delete(self, db_session, sample_project):
        """测试删除付款"""
        payment = Payment(
            payment_code="PAY_DEL",
            payment_amount=Decimal("1000.00"),
            project_id=sample_project.id
        )
        db_session.add(payment)
        db_session.commit()
        pid = payment.id
        
        db_session.delete(payment)
        db_session.commit()
        
        deleted = db_session.query(Payment).filter_by(id=pid).first()
        assert deleted is None

    def test_multiple_payments(self, db_session, sample_project):
        """测试多个付款"""
        payments = [
            Payment(
                payment_code=f"PAY{i:03d}",
                payment_amount=Decimal(f"{i*1000}.00"),
                project_id=sample_project.id
            ) for i in range(1, 6)
        ]
        db_session.add_all(payments)
        db_session.commit()
        
        count = db_session.query(Payment).count()
        assert count >= 5

    def test_payment_description(self, db_session, sample_project):
        """测试付款描述"""
        desc = "项目启动预付款"
        payment = Payment(
            payment_code="PAY004",
            payment_amount=Decimal("30000.00"),
            project_id=sample_project.id,
            description=desc
        )
        db_session.add(payment)
        db_session.commit()
        
        assert payment.description == desc

    def test_payment_reference_number(self, db_session, sample_project):
        """测试付款参考号"""
        payment = Payment(
            payment_code="PAY005",
            payment_amount=Decimal("7000.00"),
            project_id=sample_project.id,
            reference_number="REF202602210001"
        )
        db_session.add(payment)
        db_session.commit()
        
        assert payment.reference_number == "REF202602210001"

    def test_payment_approval(self, db_session, sample_project):
        """测试付款审批"""
        payment = Payment(
            payment_code="PAY006",
            payment_amount=Decimal("50000.00"),
            project_id=sample_project.id,
            approval_status="PENDING"
        )
        db_session.add(payment)
        db_session.commit()
        
        assert payment.approval_status == "PENDING"
        
        payment.approval_status = "APPROVED"
        db_session.commit()
        
        db_session.refresh(payment)
        assert payment.approval_status == "APPROVED"
