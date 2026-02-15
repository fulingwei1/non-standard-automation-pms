from sqlalchemy.orm import Session
from app.models.sales_script import PresaleAISalesScript, SalesScriptTemplate, ScenarioType
from app.models.customer_profile import PresaleCustomerProfile
from app.services.ai_service import AIService
from typing import Optional, List, Dict, Any


class SalesScriptService:
    """销售话术服务"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    async def recommend_script(
        self,
        presale_ticket_id: int,
        scenario: str,
        customer_profile_id: Optional[int] = None,
        context: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> PresaleAISalesScript:
        """推荐销售话术"""
        # 获取客户画像信息
        customer_type = None
        focus_points = None
        
        if customer_profile_id:
            profile = self.db.query(PresaleCustomerProfile).filter(
                PresaleCustomerProfile.id == customer_profile_id
            ).first()
            if profile:
                customer_type = profile.customer_type.value
                focus_points = profile.focus_points
        
        # 调用AI推荐话术
        recommendation = await self.ai_service.recommend_sales_script(
            scenario=scenario,
            customer_type=customer_type,
            focus_points=focus_points,
            context=context
        )
        
        # 保存推荐记录
        sales_script = PresaleAISalesScript(
            presale_ticket_id=presale_ticket_id,
            scenario=ScenarioType(scenario),
            customer_profile_id=customer_profile_id,
            recommended_scripts=recommendation.get("recommended_scripts", []),
            response_strategy=recommendation.get("response_strategy", ""),
            success_case_references=recommendation.get("success_cases", []),
            created_by=created_by
        )
        
        self.db.add(sales_script)
        self.db.commit()
        self.db.refresh(sales_script)
        
        return sales_script

    async def handle_objection(
        self,
        presale_ticket_id: int,
        objection_type: str,
        customer_profile_id: Optional[int] = None,
        context: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> PresaleAISalesScript:
        """处理客户异议"""
        # 获取客户画像信息
        customer_type = None
        
        if customer_profile_id:
            profile = self.db.query(PresaleCustomerProfile).filter(
                PresaleCustomerProfile.id == customer_profile_id
            ).first()
            if profile:
                customer_type = profile.customer_type.value
        
        # 调用AI处理异议
        handling_result = await self.ai_service.handle_objection(
            objection_type=objection_type,
            customer_type=customer_type,
            context=context
        )
        
        # 保存处理记录
        sales_script = PresaleAISalesScript(
            presale_ticket_id=presale_ticket_id,
            scenario=ScenarioType.OBJECTION_HANDLING,
            customer_profile_id=customer_profile_id,
            objection_type=objection_type,
            recommended_scripts=handling_result.get("recommended_scripts", []),
            response_strategy=handling_result.get("response_strategy", ""),
            success_case_references=handling_result.get("success_cases", []),
            created_by=created_by
        )
        
        self.db.add(sales_script)
        self.db.commit()
        self.db.refresh(sales_script)
        
        return sales_script

    async def guide_sales_progress(
        self,
        presale_ticket_id: int,
        current_situation: str,
        customer_profile_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """销售进程指导"""
        # 获取客户画像信息
        customer_type = None
        
        if customer_profile_id:
            profile = self.db.query(PresaleCustomerProfile).filter(
                PresaleCustomerProfile.id == customer_profile_id
            ).first()
            if profile:
                customer_type = profile.customer_type.value
        
        # 调用AI指导
        guidance = await self.ai_service.guide_sales_progress(
            current_situation=current_situation,
            customer_type=customer_type
        )
        
        return guidance

    def get_scripts_by_scenario(
        self,
        scenario: str,
        customer_type: Optional[str] = None,
        limit: int = 10
    ) -> List[SalesScriptTemplate]:
        """获取场景话术模板"""
        query = self.db.query(SalesScriptTemplate).filter(
            SalesScriptTemplate.scenario == ScenarioType(scenario)
        )
        
        if customer_type:
            query = query.filter(SalesScriptTemplate.customer_type == customer_type)
        
        query = query.order_by(SalesScriptTemplate.success_rate.desc())
        
        return query.limit(limit).all()

    def get_script_library(
        self,
        scenario: Optional[str] = None,
        customer_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[SalesScriptTemplate]:
        """获取话术库"""
        query = self.db.query(SalesScriptTemplate)
        
        if scenario:
            query = query.filter(SalesScriptTemplate.scenario == ScenarioType(scenario))
        
        if customer_type:
            query = query.filter(SalesScriptTemplate.customer_type == customer_type)
        
        # TODO: 实现标签过滤
        
        query = query.order_by(SalesScriptTemplate.success_rate.desc())
        
        return query.limit(limit).all()

    def add_script_template(
        self,
        scenario: str,
        script_content: str,
        customer_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        success_rate: Optional[float] = None
    ) -> SalesScriptTemplate:
        """添加话术模板"""
        template = SalesScriptTemplate(
            scenario=ScenarioType(scenario),
            customer_type=customer_type,
            script_content=script_content,
            tags=tags,
            success_rate=success_rate
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return template

    def record_feedback(
        self,
        script_id: int,
        is_effective: bool,
        feedback_notes: Optional[str] = None
    ) -> bool:
        """记录话术反馈（用于优化）"""
        # TODO: 实现反馈机制，可以更新模板成功率
        # 这里简化处理，仅返回成功
        return True
