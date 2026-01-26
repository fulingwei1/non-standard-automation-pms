# -*- coding: utf-8 -*-
"""
失败模式分析模块
提供失败模式分析和预警指标功能
"""

from collections import defaultdict
from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy import func

from app.models.enums import LeadOutcomeEnum, LossReasonEnum
from app.models.project import Project
from app.models.work_log import WorkLog


class FailurePatternsMixin:
    """失败模式分析功能混入类"""

    def analyze_failure_patterns(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """分析失败模式

        Returns:
            {
                'loss_reason_distribution': dict,
                'high_waste_characteristics': list,
                'early_warning_indicators': list,
                'recommendations': list
            }
        """
        query = self.db.query(Project).filter(
            Project.outcome.in_([LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value])
        )

        if start_date:
            query = query.filter(Project.created_at >= start_date)
        if end_date:
            query = query.filter(Project.created_at < end_date)

        failed_projects = query.all()

        if not failed_projects:
            return {
                'loss_reason_distribution': {},
                'high_waste_characteristics': [],
                'early_warning_indicators': [],
                'recommendations': ['数据不足，无法进行模式分析']
            }

        # 1. 丢标原因分布
        loss_reason_distribution = defaultdict(lambda: {'count': 0, 'total_hours': 0})

        project_ids = [p.id for p in failed_projects]
        work_hours_map = {}
        if project_ids:
            work_hours_map = dict(
                self.db.query(
                    WorkLog.project_id,
                    func.sum(WorkLog.work_hours)
                ).filter(
                    WorkLog.project_id.in_(project_ids)
                ).group_by(WorkLog.project_id).all()
            )

        for project in failed_projects:
            reason = project.loss_reason or 'OTHER'
            hours = work_hours_map.get(project.id, 0) or 0
            loss_reason_distribution[reason]['count'] += 1
            loss_reason_distribution[reason]['total_hours'] += hours

        # 2. 高浪费特征分析
        high_waste_characteristics = []

        # 分析评估分数与浪费的关系
        low_score_high_waste = sum(
            1 for p in failed_projects
            if p.evaluation_score and p.evaluation_score < 60 and work_hours_map.get(p.id, 0) > 40
        )
        if low_score_high_waste > len(failed_projects) * 0.3:
            high_waste_characteristics.append({
                'pattern': '低评估分仍大量投入',
                'description': f'{low_score_high_waste}个低评估分(<60)项目投入超40工时',
                'suggestion': '对评估分低于60的线索，应限制资源投入上限'
            })

        # 3. 早期预警指标
        early_warning_indicators = [
            '评估分数低于60分但仍决定跟进',
            '客户需求频繁变更超过3次',
            '方案设计阶段超过预期2周以上',
            '客户沟通间隔超过2周',
            '竞争对手数量超过4家'
        ]

        # 4. 改进建议
        recommendations = []

        # 基于丢标原因分布生成建议
        sorted_reasons = sorted(loss_reason_distribution.items(), key=lambda x: x[1]['count'], reverse=True)

        if sorted_reasons:
            top_reason = sorted_reasons[0][0]
            if top_reason == LossReasonEnum.PRICE_TOO_HIGH.value:
                recommendations.append('价格因素导致丢标最多，建议优化成本结构或调整目标客户定位')
            elif top_reason == LossReasonEnum.TECH_NOT_MATCH.value:
                recommendations.append('技术不匹配导致丢标最多，建议售前阶段加强技术评估深度')
            elif top_reason == LossReasonEnum.COMPETITOR_ADVANTAGE.value:
                recommendations.append('竞对优势导致丢标最多，建议进行系统性竞争分析，寻找差异化突破点')
            elif top_reason == LossReasonEnum.RELATIONSHIP.value:
                recommendations.append('客户关系导致丢标最多，建议加强客户关系管理，建立高层联系')

        recommendations.append('建立线索评估门槛，低于阈值的线索限制资源投入')
        recommendations.append('定期复盘失败案例，将经验沉淀到失败案例库')

        return {
            'loss_reason_distribution': {
                k: {'count': v['count'], 'total_hours': round(v['total_hours'], 1)}
                for k, v in sorted_reasons
            },
            'high_waste_characteristics': high_waste_characteristics,
            'early_warning_indicators': early_warning_indicators,
            'recommendations': recommendations
        }
