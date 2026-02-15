"""客户画像分析测试 - 6个用例"""
import pytest
from app.models.customer_profile import PresaleCustomerProfile, CustomerType, DecisionStyle
from app.services.customer_profile_service import CustomerProfileService


class TestCustomerProfileAnalysis:
    """客户画像分析测试"""

    def test_create_customer_profile_technical(self, db_session):
        """测试1: 创建技术型客户画像"""
        service = CustomerProfileService(db_session)
        
        # 模拟分析结果（实际会调用AI）
        profile = PresaleCustomerProfile(
            customer_id=1,
            presale_ticket_id=101,
            customer_type=CustomerType.TECHNICAL,
            focus_points=["quality", "delivery"],
            decision_style=DecisionStyle.RATIONAL,
            communication_notes="客户关注技术细节和系统架构",
            ai_analysis="技术型客户，注重产品质量和交付速度"
        )
        
        db_session.add(profile)
        db_session.commit()
        
        assert profile.id is not None
        assert profile.customer_type == CustomerType.TECHNICAL
        assert "quality" in profile.focus_points

    def test_create_customer_profile_commercial(self, db_session):
        """测试2: 创建商务型客户画像"""
        profile = PresaleCustomerProfile(
            customer_id=2,
            customer_type=CustomerType.COMMERCIAL,
            focus_points=["price", "service"],
            decision_style=DecisionStyle.RATIONAL,
            communication_notes="客户关注价格和性价比",
            ai_analysis="商务型客户，价格敏感"
        )
        
        db_session.add(profile)
        db_session.commit()
        
        assert profile.customer_type == CustomerType.COMMERCIAL
        assert "price" in profile.focus_points

    def test_create_customer_profile_decision_maker(self, db_session):
        """测试3: 创建决策型客户画像"""
        profile = PresaleCustomerProfile(
            customer_id=3,
            customer_type=CustomerType.DECISION_MAKER,
            focus_points=["quality", "service"],
            decision_style=DecisionStyle.AUTHORITATIVE,
            communication_notes="高层决策者，关注战略价值",
            ai_analysis="决策型客户，权威决策风格"
        )
        
        db_session.add(profile)
        db_session.commit()
        
        assert profile.customer_type == CustomerType.DECISION_MAKER
        assert profile.decision_style == DecisionStyle.AUTHORITATIVE

    def test_get_customer_profile(self, db_session):
        """测试4: 获取客户画像"""
        # 创建测试数据
        profile = PresaleCustomerProfile(
            customer_id=4,
            customer_type=CustomerType.MIXED,
            focus_points=["price", "quality", "delivery"],
            decision_style=DecisionStyle.RATIONAL,
            communication_notes="综合考虑型客户",
            ai_analysis="混合型客户"
        )
        db_session.add(profile)
        db_session.commit()
        
        # 测试获取
        service = CustomerProfileService(db_session)
        result = service.get_customer_profile(4)
        
        assert result is not None
        assert result.customer_id == 4
        assert result.customer_type == CustomerType.MIXED

    def test_update_customer_profile(self, db_session):
        """测试5: 更新客户画像"""
        # 创建初始画像
        profile = PresaleCustomerProfile(
            customer_id=5,
            customer_type=CustomerType.TECHNICAL,
            focus_points=["quality"],
            decision_style=DecisionStyle.RATIONAL,
            communication_notes="初始评估",
            ai_analysis="初步分析"
        )
        db_session.add(profile)
        db_session.commit()
        
        # 更新画像
        profile.focus_points = ["quality", "price", "service"]
        profile.ai_analysis = "更新后的分析"
        db_session.commit()
        
        # 验证更新
        updated = db_session.query(PresaleCustomerProfile).filter_by(customer_id=5).first()
        assert len(updated.focus_points) == 3
        assert "price" in updated.focus_points

    def test_customer_profile_to_dict(self, db_session):
        """测试6: 客户画像转字典"""
        profile = PresaleCustomerProfile(
            customer_id=6,
            customer_type=CustomerType.COMMERCIAL,
            focus_points=["price"],
            decision_style=DecisionStyle.EMOTIONAL,
            communication_notes="测试备注",
            ai_analysis="测试分析"
        )
        db_session.add(profile)
        db_session.commit()
        
        profile_dict = profile.to_dict()
        
        assert profile_dict["customer_id"] == 6
        assert profile_dict["customer_type"] == "commercial"
        assert profile_dict["decision_style"] == "emotional"
        assert isinstance(profile_dict["focus_points"], list)
