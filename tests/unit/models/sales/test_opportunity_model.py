# -*- coding: utf-8 -*-
"""
Opportunity Model 测试
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models.sales.leads import Opportunity


class TestOpportunityModel:
    """Opportunity 模型测试"""

    def test_create_opportunity(self, db_session, sample_user, sample_customer):
        """测试创建商机"""
        opp = Opportunity(
            opp_code="OPP001",
            opp_name="测试商机",
            customer_id=sample_customer.id,
            owner_id=sample_user.id,
            stage="需求分析",
            probability=Decimal("60.00"),
            expected_amount=Decimal("500000.00")
        )
        db_session.add(opp)
        db_session.commit()
        
        assert opp.id is not None
        assert opp.opp_code == "OPP001"
        assert opp.opp_name == "测试商机"
        assert opp.probability == Decimal("60.00")

    def test_opportunity_code_unique(self, db_session, sample_user, sample_customer):
        """测试商机编码唯一性"""
        opp1 = Opportunity(
            opp_code="OPP001",
            opp_name="商机1",
            customer_id=sample_customer.id,
            owner_id=sample_user.id
        )
        db_session.add(opp1)
        db_session.commit()
        
        opp2 = Opportunity(
            opp_code="OPP001",
            opp_name="商机2",
            customer_id=sample_customer.id,
            owner_id=sample_user.id
        )
        db_session.add(opp2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_opportunity_stage_progression(self, db_session, sample_user, sample_customer):
        """测试商机阶段推进"""
        opp = Opportunity(
            opp_code="OPP002",
            opp_name="阶段测试",
            customer_id=sample_customer.id,
            owner_id=sample_user.id,
            stage="初步接洽",
            probability=Decimal("20.00")
        )
        db_session.add(opp)
        db_session.commit()
        
        # 推进阶段
        opp.stage = "需求分析"
        opp.probability = Decimal("40.00")
        db_session.commit()
        
        db_session.refresh(opp)
        assert opp.stage == "需求分析"
        assert opp.probability == Decimal("40.00")

    def test_opportunity_amount_tracking(self, db_session, sample_user, sample_customer):
        """测试商机金额跟踪"""
        opp = Opportunity(
            opp_code="OPP003",
            opp_name="金额测试",
            customer_id=sample_customer.id,
            owner_id=sample_user.id,
            expected_amount=Decimal("1000000.00"),
            actual_amount=Decimal("950000.00")
        )
        db_session.add(opp)
        db_session.commit()
        
        assert opp.expected_amount == Decimal("1000000.00")
        assert opp.actual_amount == Decimal("950000.00")

    def test_opportunity_win_probability(self, db_session, sample_user, sample_customer):
        """测试商机赢单概率"""
        opp = Opportunity(
            opp_code="OPP004",
            opp_name="概率测试",
            customer_id=sample_customer.id,
            owner_id=sample_user.id,
            probability=Decimal("75.50")
        )
        db_session.add(opp)
        db_session.commit()
        
        assert opp.probability == Decimal("75.50")

    def test_opportunity_close_date(self, db_session, sample_user, sample_customer):
        """测试商机关闭日期"""
        expected_date = date.today() + timedelta(days=60)
        actual_date = date.today() + timedelta(days=65)
        
        opp = Opportunity(
            opp_code="OPP005",
            opp_name="日期测试",
            customer_id=sample_customer.id,
            owner_id=sample_user.id,
            expected_close_date=expected_date,
            actual_close_date=actual_date
        )
        db_session.add(opp)
        db_session.commit()
        
        assert opp.expected_close_date == expected_date
        assert opp.actual_close_date == actual_date

    def test_opportunity_relationships(self, db_session, sample_opportunity):
        """测试商机关系"""
        db_session.refresh(sample_opportunity)
        assert sample_opportunity.customer is not None
        assert sample_opportunity.owner is not None

    def test_opportunity_update(self, db_session, sample_opportunity):
        """测试更新商机"""
        sample_opportunity.opp_name = "更新后的商机名"
        sample_opportunity.stage = "方案设计"
        db_session.commit()
        
        db_session.refresh(sample_opportunity)
        assert sample_opportunity.opp_name == "更新后的商机名"
        assert sample_opportunity.stage == "方案设计"

    def test_opportunity_delete(self, db_session, sample_user, sample_customer):
        """测试删除商机"""
        opp = Opportunity(
            opp_code="OPP_DEL",
            opp_name="待删除",
            customer_id=sample_customer.id,
            owner_id=sample_user.id
        )
        db_session.add(opp)
        db_session.commit()
        opp_id = opp.id
        
        db_session.delete(opp)
        db_session.commit()
        
        deleted = db_session.query(Opportunity).filter_by(id=opp_id).first()
        assert deleted is None

    def test_opportunity_status(self, db_session, sample_opportunity):
        """测试商机状态"""
        assert sample_opportunity.status in [None, "进行中", "赢单", "输单"]

    def test_multiple_opportunities(self, db_session, sample_user, sample_customer):
        """测试多个商机"""
        opps = [
            Opportunity(
                opp_code=f"OPP{i:03d}",
                opp_name=f"商机{i}",
                customer_id=sample_customer.id,
                owner_id=sample_user.id,
                expected_amount=Decimal(f"{i*100000}.00")
            ) for i in range(1, 6)
        ]
        db_session.add_all(opps)
        db_session.commit()
        
        count = db_session.query(Opportunity).count()
        assert count >= 5
