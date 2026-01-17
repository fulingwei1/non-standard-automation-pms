# -*- coding: utf-8 -*-
"""
信息把握不足分析服务

分析信息缺失、影响和质量评分
"""

import logging
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.sales import Lead, Opportunity, Quote

logger = logging.getLogger(__name__)


class InformationGapAnalysisService:
    """信息把握不足分析服务"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_missing(
        self,
        entity_type: str,  # LEAD/OPPORTUNITY/QUOTE
        entity_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """信息缺失分析"""
        missing_fields = []
        completeness_score = 100

        if entity_type == 'LEAD':
            if entity_id:
                lead = self.db.query(Lead).filter(Lead.id == entity_id).first()
                if lead:
                    missing_fields, completeness_score = self._analyze_lead_missing(lead)
            else:
                # 分析所有线索
                leads = self.db.query(Lead).all()
                return self._analyze_batch_missing('LEAD', leads)

        elif entity_type == 'OPPORTUNITY':
            if entity_id:
                opp = self.db.query(Opportunity).filter(Opportunity.id == entity_id).first()
                if opp:
                    missing_fields, completeness_score = self._analyze_opportunity_missing(opp)
            else:
                opportunities = self.db.query(Opportunity).all()
                return self._analyze_batch_missing('OPPORTUNITY', opportunities)

        elif entity_type == 'QUOTE':
            if entity_id:
                quote = self.db.query(Quote).filter(Quote.id == entity_id).first()
                if quote:
                    missing_fields, completeness_score = self._analyze_quote_missing(quote)
            else:
                quotes = self.db.query(Quote).all()
                return self._analyze_batch_missing('QUOTE', quotes)

        return {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'missing_fields': missing_fields,
            'completeness_score': completeness_score,
            'quality_level': self._get_quality_level(completeness_score)
        }

    def analyze_impact(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """信息把握不足的影响分析"""
        # 分析线索信息质量对转化率的影响
        leads = self.db.query(Lead).all()

        high_quality_leads = []
        low_quality_leads = []

        for lead in leads:
            missing, score = self._analyze_lead_missing(lead)
            if score >= 80:
                high_quality_leads.append(lead)
            else:
                low_quality_leads.append(lead)

        # 计算转化率
        high_quality_conversion = sum(1 for l in high_quality_leads if l.status == 'CONVERTED') / len(high_quality_leads) * 100 if high_quality_leads else 0
        low_quality_conversion = sum(1 for l in low_quality_leads if l.status == 'CONVERTED') / len(low_quality_leads) * 100 if low_quality_leads else 0

        # 分析报价准确性影响
        quotes = self.db.query(Quote).all()
        accurate_quotes = []
        inaccurate_quotes = []

        for quote in quotes:
            missing, score = self._analyze_quote_missing(quote)
            if score >= 80:
                accurate_quotes.append(quote)
            else:
                inaccurate_quotes.append(quote)

        return {
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'lead_quality_impact': {
                'high_quality_count': len(high_quality_leads),
                'low_quality_count': len(low_quality_leads),
                'high_quality_conversion_rate': round(high_quality_conversion, 2),
                'low_quality_conversion_rate': round(low_quality_conversion, 2),
                'conversion_gap': round(high_quality_conversion - low_quality_conversion, 2)
            },
            'quote_quality_impact': {
                'accurate_count': len(accurate_quotes),
                'inaccurate_count': len(inaccurate_quotes)
            }
        }

    def get_quality_score(
        self,
        entity_type: str,
        entity_id: int
    ) -> Dict[str, Any]:
        """获取信息质量评分"""
        missing_analysis = self.analyze_missing(entity_type, entity_id)

        return {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'quality_score': missing_analysis['completeness_score'],
            'quality_level': missing_analysis['quality_level'],
            'missing_fields': missing_analysis['missing_fields'],
            'recommendations': self._get_recommendations(missing_analysis['missing_fields'])
        }

    def _analyze_lead_missing(self, lead: Lead) -> tuple:
        """分析线索信息缺失"""
        missing = []
        score = 100

        required_fields = {
            'customer_name': 10,
            'contact_name': 10,
            'contact_phone': 10,
            'demand_summary': 15,
            'source': 5,
            'industry': 10
        }

        for field, weight in required_fields.items():
            value = getattr(lead, field, None)
            if not value or (isinstance(value, str) and len(value.strip()) == 0):
                missing.append(field)
                score -= weight

        return missing, max(0, score)

    def _analyze_opportunity_missing(self, opp: Opportunity) -> tuple:
        """分析商机信息缺失"""
        missing = []
        score = 100

        required_fields = {
            'opp_name': 10,
            'est_amount': 15,
            'budget_range': 10,
            'delivery_window': 10,
            'decision_chain': 10,
            'acceptance_basis': 10
        }

        for field, weight in required_fields.items():
            value = getattr(opp, field, None)
            if not value or (isinstance(value, str) and len(value.strip()) == 0):
                missing.append(field)
                score -= weight

        return missing, max(0, score)

    def _analyze_quote_missing(self, quote: Quote) -> tuple:
        """分析报价信息缺失"""
        missing = []
        score = 100

        # 检查报价明细
        if not quote.items or len(quote.items) == 0:
            missing.append('quote_items')
            score -= 20

        # 检查报价金额
        if not quote.total_amount or quote.total_amount == 0:
            missing.append('total_amount')
            score -= 15

        # 检查有效期
        if not quote.valid_until:
            missing.append('valid_until')
            score -= 10

        return missing, max(0, score)

    def _analyze_batch_missing(
        self,
        entity_type: str,
        entities: List
    ) -> Dict[str, Any]:
        """批量分析信息缺失"""
        total = len(entities)
        quality_distribution = {
            'high': 0,  # >=80
            'medium': 0,  # 60-79
            'low': 0  # <60
        }

        common_missing = defaultdict(int)

        for entity in entities:
            if entity_type == 'LEAD':
                missing, score = self._analyze_lead_missing(entity)
            elif entity_type == 'OPPORTUNITY':
                missing, score = self._analyze_opportunity_missing(entity)
            else:  # QUOTE
                missing, score = self._analyze_quote_missing(entity)

            if score >= 80:
                quality_distribution['high'] += 1
            elif score >= 60:
                quality_distribution['medium'] += 1
            else:
                quality_distribution['low'] += 1

            for field in missing:
                common_missing[field] += 1

        return {
            'entity_type': entity_type,
            'total': total,
            'quality_distribution': quality_distribution,
            'common_missing_fields': [
                {'field': field, 'count': count, 'percentage': round(count / total * 100, 2)}
                for field, count in sorted(common_missing.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
        }

    def _get_quality_level(self, score: int) -> str:
        """获取质量等级"""
        if score >= 80:
            return 'HIGH'
        elif score >= 60:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _get_recommendations(self, missing_fields: List[str]) -> List[str]:
        """获取改进建议"""
        recommendations = []

        field_recommendations = {
            'customer_name': '请填写客户名称',
            'contact_name': '请填写联系人姓名',
            'contact_phone': '请填写联系电话',
            'demand_summary': '请填写需求摘要',
            'est_amount': '请填写预估金额',
            'budget_range': '请填写预算范围',
            'delivery_window': '请填写交付窗口',
            'quote_items': '请添加报价明细'
        }

        for field in missing_fields:
            if field in field_recommendations:
                recommendations.append(field_recommendations[field])

        return recommendations
