# -*- coding: utf-8 -*-
"""
变更应对方案生成服务
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from app.models import ChangeImpactAnalysis, ChangeRequest, ChangeResponseSuggestion
from app.services.glm_service import call_glm_api

logger = logging.getLogger(__name__)


class ChangeResponseSuggestionService:
    """变更应对方案生成服务"""

    def __init__(self, db: Session):
        self.db = db

    async def generate_suggestions(
        self,
        change_request_id: int,
        impact_analysis_id: int,
        user_id: int,
        max_suggestions: int = 3
    ) -> List[ChangeResponseSuggestion]:
        """生成应对方案"""
        # 获取影响分析
        analysis = self.db.query(ChangeImpactAnalysis).filter(
            ChangeImpactAnalysis.id == impact_analysis_id
        ).first()
        
        if not analysis:
            raise ValueError(f"影响分析 {impact_analysis_id} 不存在")
        
        # 获取变更请求
        change = self.db.query(ChangeRequest).filter(
            ChangeRequest.id == change_request_id
        ).first()
        
        if not change:
            raise ValueError(f"变更请求 {change_request_id} 不存在")
        
        suggestions = []
        
        # 方案1：批准方案
        if analysis.overall_risk_level in ["LOW", "MEDIUM"]:
            suggestion = self._create_approve_suggestion(
                change, analysis, user_id
            )
            suggestions.append(suggestion)
        
        # 方案2：修改方案
        suggestion = self._create_modify_suggestion(
            change, analysis, user_id
        )
        suggestions.append(suggestion)
        
        # 方案3：缓解方案
        if analysis.overall_risk_level in ["HIGH", "CRITICAL"]:
            suggestion = self._create_mitigate_suggestion(
                change, analysis, user_id
            )
            suggestions.append(suggestion)
        
        # 保存到数据库
        for sug in suggestions:
            self.db.add(sug)
        
        self.db.commit()
        
        logger.info(f"生成了 {len(suggestions)} 个应对方案")
        return suggestions[:max_suggestions]

    def _create_approve_suggestion(
        self,
        change: ChangeRequest,
        analysis: ChangeImpactAnalysis,
        user_id: int
    ) -> ChangeResponseSuggestion:
        """创建批准方案"""
        return ChangeResponseSuggestion(
            change_request_id=change.id,
            impact_analysis_id=analysis.id,
            suggestion_code=f"SUG-{change.change_code}-01",
            suggestion_title="批准变更并按计划执行",
            suggestion_type="APPROVE",
            suggestion_priority=8,
            summary="影响可控，建议批准变更请求",
            detailed_description=f"根据分析，此变更的综合风险等级为 {analysis.overall_risk_level}，影响在可控范围内。建议批准变更并按原计划执行。",
            action_steps=[
                {"step": 1, "description": "批准变更请求", "owner": "项目经理", "duration": 1},
                {"step": 2, "description": "通知相关团队", "owner": "PMO", "duration": 1},
                {"step": 3, "description": "执行变更", "owner": "项目团队", "duration": analysis.schedule_delay_days or 5},
                {"step": 4, "description": "验收变更结果", "owner": "QA", "duration": 2},
            ],
            estimated_cost=analysis.cost_impact_amount,
            estimated_duration_days=analysis.schedule_delay_days or 5,
            resource_requirements=[
                {"type": "项目团队", "quantity": 1, "duration": analysis.schedule_delay_days or 5}
            ],
            feasibility_score=Decimal("90"),
            technical_feasibility="HIGH",
            cost_feasibility="HIGH",
            schedule_feasibility="HIGH",
            feasibility_analysis="风险可控，资源充足，建议批准",
            ai_recommendation_score=Decimal("85"),
            ai_confidence_level="HIGH",
            ai_reasoning="基于影响分析，此变更风险可控，建议批准执行",
            created_by=user_id,
        )

    def _create_modify_suggestion(
        self,
        change: ChangeRequest,
        analysis: ChangeImpactAnalysis,
        user_id: int
    ) -> ChangeResponseSuggestion:
        """创建修改方案"""
        return ChangeResponseSuggestion(
            change_request_id=change.id,
            impact_analysis_id=analysis.id,
            suggestion_code=f"SUG-{change.change_code}-02",
            suggestion_title="调整变更范围以降低影响",
            suggestion_type="MODIFY",
            suggestion_priority=7,
            summary="建议调整变更范围，分阶段实施",
            detailed_description="为降低风险和影响，建议将变更拆分为多个阶段，优先实施关键部分，次要部分延后。",
            action_steps=[
                {"step": 1, "description": "与客户沟通调整方案", "owner": "项目经理", "duration": 2},
                {"step": 2, "description": "制定分阶段实施计划", "owner": "技术负责人", "duration": 3},
                {"step": 3, "description": "实施第一阶段变更", "owner": "项目团队", "duration": (analysis.schedule_delay_days or 10) // 2},
                {"step": 4, "description": "评估后续阶段", "owner": "PMO", "duration": 1},
            ],
            estimated_cost=analysis.cost_impact_amount * Decimal("0.7"),
            estimated_duration_days=(analysis.schedule_delay_days or 10) // 2 + 5,
            resource_requirements=[
                {"type": "项目经理", "quantity": 1, "duration": 2},
                {"type": "技术团队", "quantity": 1, "duration": 5},
            ],
            feasibility_score=Decimal("80"),
            technical_feasibility="MEDIUM",
            cost_feasibility="HIGH",
            schedule_feasibility="MEDIUM",
            feasibility_analysis="分阶段实施可降低风险，但需要额外协调",
            ai_recommendation_score=Decimal("75"),
            ai_confidence_level="MEDIUM",
            ai_reasoning="通过调整范围可以平衡风险和收益",
            created_by=user_id,
        )

    def _create_mitigate_suggestion(
        self,
        change: ChangeRequest,
        analysis: ChangeImpactAnalysis,
        user_id: int
    ) -> ChangeResponseSuggestion:
        """创建缓解方案"""
        return ChangeResponseSuggestion(
            change_request_id=change.id,
            impact_analysis_id=analysis.id,
            suggestion_code=f"SUG-{change.change_code}-03",
            suggestion_title="制定风险缓解措施后执行",
            suggestion_type="MITIGATE",
            suggestion_priority=9,
            summary="高风险变更，需要制定详细的缓解措施",
            detailed_description="此变更风险较高，建议制定详细的风险缓解措施，增加资源投入，加强监控。",
            action_steps=[
                {"step": 1, "description": "制定详细风险缓解计划", "owner": "风险经理", "duration": 3},
                {"step": 2, "description": "申请额外资源和预算", "owner": "PMO", "duration": 2},
                {"step": 3, "description": "建立变更监控机制", "owner": "项目经理", "duration": 1},
                {"step": 4, "description": "执行变更并严格监控", "owner": "项目团队", "duration": analysis.schedule_delay_days or 10},
                {"step": 5, "description": "定期风险评估", "owner": "风险经理", "duration": 1},
            ],
            estimated_cost=analysis.cost_impact_amount * Decimal("1.3"),
            estimated_duration_days=(analysis.schedule_delay_days or 10) + 7,
            resource_requirements=[
                {"type": "风险经理", "quantity": 1, "duration": 7},
                {"type": "项目团队", "quantity": 1, "duration": analysis.schedule_delay_days or 10},
                {"type": "QA团队", "quantity": 1, "duration": 5},
            ],
            risks=[
                {"risk": "资源不足", "probability": "MEDIUM", "impact": "HIGH", "mitigation": "提前申请资源"},
                {"risk": "进度延期", "probability": "MEDIUM", "impact": "MEDIUM", "mitigation": "建立监控机制"},
            ],
            feasibility_score=Decimal("75"),
            technical_feasibility="MEDIUM",
            cost_feasibility="MEDIUM",
            schedule_feasibility="LOW",
            feasibility_analysis="需要额外资源，但可以显著降低风险",
            ai_recommendation_score=Decimal("80"),
            ai_confidence_level="MEDIUM",
            ai_reasoning="高风险变更需要采取缓解措施",
            created_by=user_id,
        )
