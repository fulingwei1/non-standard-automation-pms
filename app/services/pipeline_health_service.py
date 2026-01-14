# -*- coding: utf-8 -*-
"""
全链条健康度计算服务

计算线索、商机、报价、合同、回款各环节的健康度
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.sales import Lead, Opportunity, Quote, Contract, Invoice
from app.models.project import Project, ProjectMilestone
from app.models.user import User

logger = logging.getLogger(__name__)


class PipelineHealthService:
    """全链条健康度计算服务"""

    # 健康度阈值（天数）
    HEALTH_THRESHOLDS = {
        'LEAD': {
            'H1': 7,   # 7天内跟进：正常
            'H2': 14,  # 14天内跟进：有风险
            'H3': 30   # 30天以上：可能断链
        },
        'OPPORTUNITY': {
            'H1': 14,  # 14天内有进展：正常
            'H2': 30,  # 30天内有进展：有风险
            'H3': 60   # 60天以上：可能断链
        },
        'QUOTE': {
            'H1': 30,  # 30天内审批：正常
            'H2': 60,  # 60天内审批：有风险
            'H3': 90   # 90天以上：可能断链
        },
        'CONTRACT': {
            'H1': 0,   # 正常执行
            'H2': 1,   # 有风险
            'H3': 1    # 执行受阻
        },
        'PAYMENT': {
            'H1': 0,   # 正常回款
            'H2': 7,   # 延迟7天：有风险
            'H3': 30   # 逾期30天：严重
        }
    }

    def __init__(self, db: Session):
        self.db = db

    def calculate_lead_health(self, lead_id: int) -> Dict[str, Any]:
        """计算线索健康度"""
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"线索 {lead_id} 不存在")

        # H4: 已转化或无效
        if lead.status == 'CONVERTED':
            return {
                'lead_id': lead_id,
                'health_status': 'H4',
                'health_score': 0,
                'risk_factors': ['已转化'],
                'description': '线索已转化为商机'
            }
        if lead.status == 'INVALID':
            return {
                'lead_id': lead_id,
                'health_status': 'H4',
                'health_score': 0,
                'risk_factors': ['已标记为无效'],
                'description': '线索已标记为无效'
            }

        # 计算距离上次跟进的天数
        last_follow_up = lead.next_action_at.date() if lead.next_action_at else lead.created_at.date() if lead.created_at else date.today()
        days_since_follow_up = (date.today() - last_follow_up).days

        # 检查是否有跟进记录
        if lead.follow_ups:
            latest_follow_up = max(lead.follow_ups, key=lambda f: f.created_at if f.created_at else datetime.min)
            if latest_follow_up.created_at:
                last_follow_up = latest_follow_up.created_at.date()
                days_since_follow_up = (date.today() - last_follow_up).days

        thresholds = self.HEALTH_THRESHOLDS['LEAD']
        risk_factors = []

        if days_since_follow_up >= thresholds['H3']:
            health_status = 'H3'
            health_score = 20
            risk_factors.append(f'已{days_since_follow_up}天未跟进')
        elif days_since_follow_up >= thresholds['H2']:
            health_status = 'H2'
            health_score = 50
            risk_factors.append(f'已{days_since_follow_up}天未跟进')
        else:
            health_status = 'H1'
            health_score = 100
            if days_since_follow_up > 0:
                risk_factors.append(f'{days_since_follow_up}天未跟进')

        return {
            'lead_id': lead_id,
            'lead_code': lead.lead_code,
            'health_status': health_status,
            'health_score': health_score,
            'risk_factors': risk_factors,
            'days_since_follow_up': days_since_follow_up,
            'last_follow_up_date': last_follow_up.isoformat()
        }

    def calculate_opportunity_health(self, opp_id: int) -> Dict[str, Any]:
        """计算商机健康度"""
        opportunity = self.db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        if not opportunity:
            raise ValueError(f"商机 {opp_id} 不存在")

        # H4: 已赢单或丢单
        if opportunity.stage == 'WON':
            return {
                'opportunity_id': opp_id,
                'health_status': 'H4',
                'health_score': 0,
                'risk_factors': ['已赢单'],
                'description': '商机已赢单'
            }
        if opportunity.stage == 'LOST':
            return {
                'opportunity_id': opp_id,
                'health_status': 'H4',
                'health_score': 0,
                'risk_factors': ['已丢单'],
                'description': '商机已丢单'
            }

        # 计算距离上次进展的天数
        last_progress = opportunity.updated_at.date() if opportunity.updated_at else opportunity.created_at.date() if opportunity.created_at else date.today()
        days_since_progress = (date.today() - last_progress).days

        thresholds = self.HEALTH_THRESHOLDS['OPPORTUNITY']
        risk_factors = []

        if days_since_progress >= thresholds['H3']:
            health_status = 'H3'
            health_score = 20
            risk_factors.append(f'已{days_since_progress}天无进展')
        elif days_since_progress >= thresholds['H2']:
            health_status = 'H2'
            health_score = 50
            risk_factors.append(f'已{days_since_progress}天无进展')
        else:
            health_status = 'H1'
            health_score = 100

        # 检查阶段门状态
        if opportunity.gate_status == 'REJECTED':
            health_status = 'H3'
            health_score = min(health_score, 30)
            risk_factors.append('阶段门被拒绝')

        return {
            'opportunity_id': opp_id,
            'opp_code': opportunity.opp_code,
            'health_status': health_status,
            'health_score': health_score,
            'risk_factors': risk_factors,
            'days_since_progress': days_since_progress,
            'last_progress_date': last_progress.isoformat()
        }

    def calculate_quote_health(self, quote_id: int) -> Dict[str, Any]:
        """计算报价健康度"""
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise ValueError(f"报价 {quote_id} 不存在")

        # H4: 已批准或拒绝
        if quote.status == 'APPROVED':
            return {
                'quote_id': quote_id,
                'health_status': 'H4',
                'health_score': 0,
                'risk_factors': ['已批准'],
                'description': '报价已批准'
            }
        if quote.status == 'REJECTED':
            return {
                'quote_id': quote_id,
                'health_status': 'H4',
                'health_score': 0,
                'risk_factors': ['已拒绝'],
                'description': '报价已拒绝'
            }

        # 计算报价创建后的天数
        quote_date = quote.created_at.date() if quote.created_at else date.today()
        days_since_quote = (date.today() - quote_date).days

        thresholds = self.HEALTH_THRESHOLDS['QUOTE']
        risk_factors = []

        if days_since_quote >= thresholds['H3']:
            health_status = 'H3'
            health_score = 20
            risk_factors.append(f'报价已{days_since_quote}天未跟进')
        elif days_since_quote >= thresholds['H2']:
            health_status = 'H2'
            health_score = 50
            risk_factors.append(f'报价审批时间过长（{days_since_quote}天）')
        else:
            health_status = 'H1'
            health_score = 100

        # 检查报价是否过期
        if quote.valid_until:
            if date.today() > quote.valid_until:
                health_status = 'H3'
                health_score = min(health_score, 30)
                risk_factors.append('报价已过期')

        return {
            'quote_id': quote_id,
            'quote_code': quote.quote_code,
            'health_status': health_status,
            'health_score': health_score,
            'risk_factors': risk_factors,
            'days_since_quote': days_since_quote
        }

    def calculate_contract_health(self, contract_id: int) -> Dict[str, Any]:
        """计算合同健康度"""
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError(f"合同 {contract_id} 不存在")

        # H4: 已结案或取消
        if contract.status == 'CLOSED':
            return {
                'contract_id': contract_id,
                'health_status': 'H4',
                'health_score': 0,
                'risk_factors': ['已结案'],
                'description': '合同已结案'
            }
        if contract.status == 'CANCELLED':
            return {
                'contract_id': contract_id,
                'health_status': 'H4',
                'health_score': 0,
                'risk_factors': ['已取消'],
                'description': '合同已取消'
            }

        # 检查项目执行情况
        project = None
        if contract.project_id:
            project = self.db.query(Project).filter(Project.id == contract.project_id).first()

        risk_factors = []
        health_score = 100

        if not project:
            health_status = 'H3'
            health_score = 30
            risk_factors.append('合同未生成项目')
        else:
            # 检查项目健康度
            from app.services.health_calculator import HealthCalculator
            health_calc = HealthCalculator(self.db)
            project_health = health_calc.calculate_health(project)

            if project_health == 'H3':
                health_status = 'H3'
                health_score = 30
                risk_factors.append('关联项目阻塞')
            elif project_health == 'H2':
                health_status = 'H2'
                health_score = 60
                risk_factors.append('关联项目有风险')
            else:
                health_status = 'H1'
                health_score = 100

        return {
            'contract_id': contract_id,
            'contract_code': contract.contract_code,
            'health_status': health_status,
            'health_score': health_score,
            'risk_factors': risk_factors,
            'project_health': project.health if project else None
        }

    def calculate_payment_health(self, invoice_id: int) -> Dict[str, Any]:
        """计算回款健康度"""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"发票 {invoice_id} 不存在")

        total_amount = float(invoice.invoice_amount or 0)
        paid_amount = float(invoice.paid_amount or 0)

        # H4: 已完全回款
        if paid_amount >= total_amount:
            return {
                'invoice_id': invoice_id,
                'invoice_no': invoice.invoice_no,
                'health_status': 'H4',
                'health_score': 0,
                'risk_factors': [],
                'description': '已完全回款'
            }

        unpaid_amount = total_amount - paid_amount
        due_date = invoice.due_date or invoice.invoice_date
        days_overdue = (date.today() - due_date).days if due_date else 0

        thresholds = self.HEALTH_THRESHOLDS['PAYMENT']
        risk_factors = []

        if days_overdue >= thresholds['H3']:
            health_status = 'H3'
            health_score = 20
            risk_factors.append(f'逾期{days_overdue}天')
        elif days_overdue >= thresholds['H2']:
            health_status = 'H2'
            health_score = 50
            risk_factors.append(f'延迟{days_overdue}天')
        elif days_overdue > 0:
            health_status = 'H2'
            health_score = 70
            risk_factors.append(f'已逾期{days_overdue}天')
        else:
            health_status = 'H1'
            health_score = 100

        return {
            'invoice_id': invoice_id,
            'invoice_no': invoice.invoice_no,
            'health_status': health_status,
            'health_score': health_score,
            'risk_factors': risk_factors,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'unpaid_amount': unpaid_amount,
            'days_overdue': days_overdue,
            'due_date': due_date.isoformat() if due_date else None
        }

    def calculate_pipeline_health(
        self,
        lead_id: Optional[int] = None,
        opportunity_id: Optional[int] = None,
        quote_id: Optional[int] = None,
        contract_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """计算全链条健康度"""
        pipeline_health = {}

        if lead_id:
            try:
                pipeline_health['lead'] = self.calculate_lead_health(lead_id)
            except Exception as e:
                logger.warning(f"计算线索健康度失败: {e}")

        if opportunity_id:
            try:
                pipeline_health['opportunity'] = self.calculate_opportunity_health(opportunity_id)
            except Exception as e:
                logger.warning(f"计算商机健康度失败: {e}")

        if quote_id:
            try:
                pipeline_health['quote'] = self.calculate_quote_health(quote_id)
            except Exception as e:
                logger.warning(f"计算报价健康度失败: {e}")

        if contract_id:
            try:
                pipeline_health['contract'] = self.calculate_contract_health(contract_id)
            except Exception as e:
                logger.warning(f"计算合同健康度失败: {e}")

        # 计算整体健康度（取最差的）
        if pipeline_health:
            min_health_score = min(
                h.get('health_score', 100) for h in pipeline_health.values()
            )
            overall_health = 'H1'
            if min_health_score <= 20:
                overall_health = 'H3'
            elif min_health_score <= 50:
                overall_health = 'H2'
            elif min_health_score == 0:
                overall_health = 'H4'

            pipeline_health['overall'] = {
                'health_status': overall_health,
                'health_score': min_health_score
            }

        return pipeline_health
