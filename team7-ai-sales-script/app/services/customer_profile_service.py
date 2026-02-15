from sqlalchemy.orm import Session
from app.models.customer_profile import PresaleCustomerProfile, CustomerType, DecisionStyle
from app.services.ai_service import AIService
from typing import Optional, Dict, Any


class CustomerProfileService:
    """客户画像服务"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    async def analyze_customer(
        self,
        customer_id: int,
        communication_notes: str,
        presale_ticket_id: Optional[int] = None
    ) -> PresaleCustomerProfile:
        """分析客户画像"""
        # 调用AI分析
        analysis_result = await self.ai_service.analyze_customer_profile(communication_notes)
        
        # 创建或更新客户画像
        profile = self.db.query(PresaleCustomerProfile).filter(
            PresaleCustomerProfile.customer_id == customer_id
        ).first()
        
        if profile:
            # 更新现有画像
            profile.customer_type = CustomerType(analysis_result.get("customer_type", "mixed"))
            profile.focus_points = analysis_result.get("focus_points", [])
            profile.decision_style = DecisionStyle(analysis_result.get("decision_style", "rational"))
            profile.communication_notes = communication_notes
            profile.ai_analysis = analysis_result.get("analysis", "")
            if presale_ticket_id:
                profile.presale_ticket_id = presale_ticket_id
        else:
            # 创建新画像
            profile = PresaleCustomerProfile(
                customer_id=customer_id,
                presale_ticket_id=presale_ticket_id,
                customer_type=CustomerType(analysis_result.get("customer_type", "mixed")),
                focus_points=analysis_result.get("focus_points", []),
                decision_style=DecisionStyle(analysis_result.get("decision_style", "rational")),
                communication_notes=communication_notes,
                ai_analysis=analysis_result.get("analysis", "")
            )
            self.db.add(profile)
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile

    def get_customer_profile(self, customer_id: int) -> Optional[PresaleCustomerProfile]:
        """获取客户画像"""
        return self.db.query(PresaleCustomerProfile).filter(
            PresaleCustomerProfile.customer_id == customer_id
        ).first()

    def get_profile_by_id(self, profile_id: int) -> Optional[PresaleCustomerProfile]:
        """通过ID获取客户画像"""
        return self.db.query(PresaleCustomerProfile).filter(
            PresaleCustomerProfile.id == profile_id
        ).first()
