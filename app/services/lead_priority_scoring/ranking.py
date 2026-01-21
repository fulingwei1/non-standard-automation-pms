# -*- coding: utf-8 -*-
"""
排名查询模块
提供优先级排名和关键项查询功能
"""

import logging
from typing import Any, Dict, List

from app.models.sales import Lead, Opportunity

logger = logging.getLogger(__name__)


class RankingMixin:
    """排名查询功能混入类"""

    def get_priority_ranking(
        self,
        entity_type: str = "lead",  # 'lead' or 'opportunity'
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """获取优先级排名"""
        rankings = []

        if entity_type == "lead":
            leads = self.db.query(Lead).filter(Lead.status != "INVALID").all()

            for lead in leads:
                try:
                    priority_data = self.calculate_lead_priority(lead.id)
                    rankings.append(
                        {
                            "id": lead.id,
                            "code": lead.lead_code,
                            "name": lead.customer_name or "未知客户",
                            "total_score": priority_data["total_score"],
                            "is_key": priority_data["is_key_lead"],
                            "priority_level": priority_data["priority_level"],
                            "importance_level": priority_data["importance_level"],
                            "urgency_level": priority_data["urgency_level"],
                        }
                    )
                except Exception as e:
                    logger.warning(f"计算线索 {lead.id} 优先级失败: {e}")
                    continue

        else:  # opportunity
            opportunities = (
                self.db.query(Opportunity)
                .filter(Opportunity.stage.notin_(["WON", "LOST"]))
                .all()
            )

            for opp in opportunities:
                try:
                    priority_data = self.calculate_opportunity_priority(opp.id)
                    rankings.append(
                        {
                            "id": opp.id,
                            "code": opp.opp_code,
                            "name": opp.opp_name,
                            "total_score": priority_data["total_score"],
                            "is_key": priority_data["is_key_opportunity"],
                            "priority_level": priority_data["priority_level"],
                            "importance_level": priority_data["importance_level"],
                            "urgency_level": priority_data["urgency_level"],
                        }
                    )
                except Exception as e:
                    logger.warning(f"计算商机 {opp.id} 优先级失败: {e}")
                    continue

        # 按总分排序
        rankings.sort(key=lambda x: x["total_score"], reverse=True)

        return rankings[:limit]

    def get_key_leads(self) -> List[Dict[str, Any]]:
        """获取关键线索列表"""
        rankings = self.get_priority_ranking("lead", limit=1000)
        return [r for r in rankings if r["is_key"]]

    def get_key_opportunities(self) -> List[Dict[str, Any]]:
        """获取关键商机列表"""
        rankings = self.get_priority_ranking("opportunity", limit=1000)
        return [r for r in rankings if r["is_key"]]
