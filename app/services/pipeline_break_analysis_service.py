# -*- coding: utf-8 -*-
"""
全链条断链检测与分析服务

检测各环节的断链情况，统计断链率，识别断链模式
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.sales import Contract, Invoice, Lead, Opportunity, Quote

logger = logging.getLogger(__name__)


class PipelineBreakAnalysisService:
    """全链条断链检测与分析服务"""

    # 默认断链阈值（天数）
    DEFAULT_BREAK_THRESHOLDS = {
        'LEAD_TO_OPP': 30,  # 线索→商机：30天
        'OPP_TO_QUOTE': 60,  # 商机→报价：60天
        'QUOTE_TO_CONTRACT': 90,  # 报价→合同：90天
        'CONTRACT_TO_PROJECT': 30,  # 合同→项目：30天
        'PROJECT_TO_INVOICE': 30,  # 项目→发票：30天（里程碑验收后）
        'INVOICE_TO_PAYMENT': 30,  # 发票→回款：30天（发票到期后）
    }

    def __init__(self, db: Session):
        self.db = db

    def analyze_pipeline_breaks(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        pipeline_type: Optional[str] = None  # LEAD/OPPORTUNITY/QUOTE/CONTRACT
    ) -> Dict[str, Any]:
        """分析全链条断链情况

        Returns:
            包含各环节断链统计、断链率、断链记录的字典
        """
        today = date.today()
        if not start_date:
            start_date = today - timedelta(days=365)  # 默认分析近一年
        if not end_date:
            end_date = today

        breaks = {
            'LEAD_TO_OPP': self._detect_lead_to_opp_breaks(start_date, end_date),
            'OPP_TO_QUOTE': self._detect_opp_to_quote_breaks(start_date, end_date),
            'QUOTE_TO_CONTRACT': self._detect_quote_to_contract_breaks(start_date, end_date),
            'CONTRACT_TO_PROJECT': self._detect_contract_to_project_breaks(start_date, end_date),
            'PROJECT_TO_INVOICE': self._detect_project_to_invoice_breaks(start_date, end_date),
            'INVOICE_TO_PAYMENT': self._detect_invoice_to_payment_breaks(start_date, end_date),
        }

        # 计算各环节断链率
        break_rates = {}
        for stage, break_data in breaks.items():
            total = break_data.get('total', 0)
            break_count = break_data.get('break_count', 0)
            break_rates[stage] = {
                'total': total,
                'break_count': break_count,
                'break_rate': round(break_count / total * 100, 2) if total > 0 else 0
            }

        # 识别最容易断链的环节
        sorted_stages = sorted(
            break_rates.items(),
            key=lambda x: x[1]['break_rate'],
            reverse=True
        )

        return {
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'breaks': breaks,
            'break_rates': break_rates,
            'top_break_stages': [
                {
                    'stage': stage,
                    'break_rate': data['break_rate'],
                    'break_count': data['break_count'],
                    'total': data['total']
                }
                for stage, data in sorted_stages[:3]
            ]
        }

    def _detect_lead_to_opp_breaks(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """检测线索→商机断链"""
        threshold = self.DEFAULT_BREAK_THRESHOLDS['LEAD_TO_OPP']
        cutoff_date = date.today() - timedelta(days=threshold)

        # 查询在时间范围内的线索
        leads = self.db.query(Lead).filter(
            Lead.created_at >= datetime.combine(start_date, datetime.min.time()),
            Lead.created_at <= datetime.combine(end_date, datetime.max.time()),
            Lead.status != 'CONVERTED',
            Lead.status != 'INVALID'
        ).all()

        break_records = []
        for lead in leads:
            # 检查是否已转商机
            has_opportunity = len(lead.opportunities) > 0 if lead.opportunities else False

            if not has_opportunity:
                # 检查是否超过阈值
                lead_date = lead.created_at.date() if lead.created_at else None
                if lead_date and lead_date < cutoff_date:
                    days_since = (date.today() - lead_date).days
                    break_records.append({
                        'pipeline_id': lead.id,
                        'pipeline_code': lead.lead_code,
                        'pipeline_name': lead.customer_name,
                        'pipeline_type': 'LEAD',
                        'break_stage': 'LEAD_TO_OPP',
                        'break_date': lead_date.isoformat(),
                        'days_since_break': days_since,
                        'responsible_person_id': lead.owner_id,
                        'responsible_person_name': lead.owner.real_name if lead.owner else None
                    })

        return {
            'total': len(leads),
            'break_count': len(break_records),
            'break_records': break_records[:50]  # 限制返回数量
        }

    def _detect_opp_to_quote_breaks(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """检测商机→报价断链"""
        threshold = self.DEFAULT_BREAK_THRESHOLDS['OPP_TO_QUOTE']
        cutoff_date = date.today() - timedelta(days=threshold)

        opportunities = self.db.query(Opportunity).filter(
            Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()),
            Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()),
            Opportunity.stage.notin_(['WON', 'LOST', 'ON_HOLD'])
        ).all()

        break_records = []
        for opp in opportunities:
            # 检查是否已创建报价
            has_quote = len(opp.quotes) > 0 if opp.quotes else False

            if not has_quote:
                opp_date = opp.created_at.date() if opp.created_at else None
                if opp_date and opp_date < cutoff_date:
                    days_since = (date.today() - opp_date).days
                    break_records.append({
                        'pipeline_id': opp.id,
                        'pipeline_code': opp.opp_code,
                        'pipeline_name': opp.opp_name,
                        'pipeline_type': 'OPPORTUNITY',
                        'break_stage': 'OPP_TO_QUOTE',
                        'break_date': opp_date.isoformat(),
                        'days_since_break': days_since,
                        'responsible_person_id': opp.owner_id,
                        'responsible_person_name': opp.owner.real_name if opp.owner else None
                    })

        return {
            'total': len(opportunities),
            'break_count': len(break_records),
            'break_records': break_records[:50]
        }

    def _detect_quote_to_contract_breaks(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """检测报价→合同断链"""
        threshold = self.DEFAULT_BREAK_THRESHOLDS['QUOTE_TO_CONTRACT']
        cutoff_date = date.today() - timedelta(days=threshold)

        quotes = self.db.query(Quote).filter(
            Quote.created_at >= datetime.combine(start_date, datetime.min.time()),
            Quote.created_at <= datetime.combine(end_date, datetime.max.time()),
            Quote.status.notin_(['APPROVED', 'REJECTED', 'CANCELLED'])
        ).all()

        break_records = []
        for quote in quotes:
            # 检查是否已签订合同
            has_contract = len(quote.opportunity.contracts) > 0 if quote.opportunity and quote.opportunity.contracts else False

            if not has_contract:
                quote_date = quote.created_at.date() if quote.created_at else None
                if quote_date and quote_date < cutoff_date:
                    days_since = (date.today() - quote_date).days
                    break_records.append({
                        'pipeline_id': quote.id,
                        'pipeline_code': quote.quote_code,
                        'pipeline_name': quote.quote_name or f'报价-{quote.quote_code}',
                        'pipeline_type': 'QUOTE',
                        'break_stage': 'QUOTE_TO_CONTRACT',
                        'break_date': quote_date.isoformat(),
                        'days_since_break': days_since,
                        'responsible_person_id': quote.opportunity.owner_id if quote.opportunity else None,
                        'responsible_person_name': quote.opportunity.owner.real_name if quote.opportunity and quote.opportunity.owner else None
                    })

        return {
            'total': len(quotes),
            'break_count': len(break_records),
            'break_records': break_records[:50]
        }

    def _detect_contract_to_project_breaks(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """检测合同→项目断链"""
        threshold = self.DEFAULT_BREAK_THRESHOLDS['CONTRACT_TO_PROJECT']
        cutoff_date = date.today() - timedelta(days=threshold)

        contracts = self.db.query(Contract).filter(
            Contract.signing_date >= start_date,
            Contract.signing_date <= end_date,
            Contract.status == 'SIGNED'
        ).all()

        break_records = []
        for contract in contracts:
            # 检查是否已生成项目
            has_project = contract.project_id is not None

            if not has_project:
                sign_date = contract.signing_date
                if sign_date and sign_date < cutoff_date:
                    days_since = (date.today() - sign_date).days
                    break_records.append({
                        'pipeline_id': contract.id,
                        'pipeline_code': contract.contract_code,
                        'pipeline_name': contract.contract_name,
                        'pipeline_type': 'CONTRACT',
                        'break_stage': 'CONTRACT_TO_PROJECT',
                        'break_date': sign_date.isoformat(),
                        'days_since_break': days_since,
                        'responsible_person_id': contract.opportunity.owner_id if contract.opportunity else None,
                        'responsible_person_name': contract.opportunity.owner.real_name if contract.opportunity and contract.opportunity.owner else None
                    })

        return {
            'total': len(contracts),
            'break_count': len(break_records),
            'break_records': break_records[:50]
        }

    def _detect_project_to_invoice_breaks(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """检测项目→发票断链（里程碑验收后）"""
        threshold = self.DEFAULT_BREAK_THRESHOLDS['PROJECT_TO_INVOICE']
        cutoff_date = date.today() - timedelta(days=threshold)

        # 查询已完成里程碑但未开票的项目
        from app.models.project import ProjectMilestone
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.status == 'COMPLETED',
            ProjectMilestone.actual_date >= start_date,
            ProjectMilestone.actual_date <= end_date
        ).all()

        break_records = []
        for milestone in milestones:
            project = milestone.project
            if not project:
                continue

            # 检查该里程碑是否已开票
            # 通过检查是否有对应的发票记录（简化处理）
            has_invoice = False
            if project.contract:
                has_invoice = len(project.contract.invoices) > 0 if project.contract.invoices else False

            if not has_invoice:
                completed_date = milestone.actual_date
                if completed_date and completed_date < cutoff_date:
                    days_since = (date.today() - completed_date).days
                    break_records.append({
                        'pipeline_id': project.id,
                        'pipeline_code': project.project_code,
                        'pipeline_name': project.project_name,
                        'pipeline_type': 'PROJECT',
                        'break_stage': 'PROJECT_TO_INVOICE',
                        'break_date': completed_date.isoformat(),
                        'days_since_break': days_since,
                        'responsible_person_id': project.pm_id,
                        'responsible_person_name': project.manager.real_name if project.manager else None,
                        'milestone_name': milestone.milestone_name
                    })

        return {
            'total': len(milestones),
            'break_count': len(break_records),
            'break_records': break_records[:50]
        }

    def _detect_invoice_to_payment_breaks(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """检测发票→回款断链"""
        threshold = self.DEFAULT_BREAK_THRESHOLDS['INVOICE_TO_PAYMENT']
        cutoff_date = date.today() - timedelta(days=threshold)

        invoices = self.db.query(Invoice).filter(
            Invoice.issue_date >= start_date,
            Invoice.issue_date <= end_date,
            Invoice.status == 'ISSUED'
        ).all()

        break_records = []
        for invoice in invoices:
            # 检查是否已完全回款
            total_amount = float(invoice.invoice_amount or 0)
            paid_amount = float(invoice.paid_amount or 0)
            is_fully_paid = paid_amount >= total_amount

            if not is_fully_paid:
                # 检查是否超过到期日+阈值
                due_date = invoice.due_date or invoice.issue_date
                if due_date and due_date < cutoff_date:
                    days_since = (date.today() - due_date).days
                    break_records.append({
                        'pipeline_id': invoice.id,
                        'pipeline_code': invoice.invoice_no,
                        'pipeline_name': invoice.customer_name or '未知客户',
                        'pipeline_type': 'INVOICE',
                        'break_stage': 'INVOICE_TO_PAYMENT',
                        'break_date': due_date.isoformat(),
                        'days_since_break': days_since,
                        'invoice_amount': total_amount,
                        'paid_amount': paid_amount,
                        'unpaid_amount': total_amount - paid_amount,
                        'responsible_person_id': invoice.contract.opportunity.owner_id if invoice.contract and invoice.contract.opportunity else None,
                        'responsible_person_name': invoice.contract.opportunity.owner.real_name if invoice.contract and invoice.contract.opportunity and invoice.contract.opportunity.owner else None
                    })

        return {
            'total': len(invoices),
            'break_count': len(break_records),
            'break_records': break_records[:50]
        }

    def get_break_reasons(
        self,
        break_stage: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取断链原因统计"""
        # 这里可以从断链记录中提取原因，或者从项目/线索的备注中提取
        # 简化实现：返回常见断链原因统计
        common_reasons = {
            '客户需求变化': 0,
            '价格不匹配': 0,
            '技术方案不匹配': 0,
            '客户预算不足': 0,
            '竞争对手优势': 0,
            '客户关系不足': 0,
            '交期不满足': 0,
            '其他': 0
        }

        # 实际应该从数据库中的断链记录或项目备注中提取
        # 这里返回示例数据
        return {
            'break_stage': break_stage,
            'reasons': common_reasons,
            'top_reasons': []
        }

    def get_break_patterns(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """识别断链模式"""
        analysis = self.analyze_pipeline_breaks(start_date, end_date)

        patterns = {
            'most_common_stage': None,
            'time_patterns': {},
            'person_patterns': {},
            'department_patterns': {}
        }

        # 找出最容易断链的环节
        if analysis['top_break_stages']:
            patterns['most_common_stage'] = analysis['top_break_stages'][0]

        # 按时间模式分析（按月统计）
        # 按人员模式分析
        # 按部门模式分析

        return patterns

    def get_break_warnings(
        self,
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """获取即将断链的预警列表"""
        warnings = []

        # 检查各环节即将断链的情况
        today = date.today()

        # 线索即将断链
        lead_threshold = self.DEFAULT_BREAK_THRESHOLDS['LEAD_TO_OPP'] - days_ahead
        cutoff_date = today - timedelta(days=lead_threshold)
        leads = self.db.query(Lead).filter(
            Lead.created_at <= datetime.combine(cutoff_date, datetime.min.time()),
            Lead.status.notin_(['CONVERTED', 'INVALID'])
        ).all()

        for lead in leads:
            # 检查是否已转商机
            has_opportunity = len(lead.opportunities) > 0 if lead.opportunities else False
            if not has_opportunity:
                lead_date = lead.created_at.date() if lead.created_at else None
                if lead_date:
                    days_until_break = lead_threshold - (today - lead_date).days
                    if 0 < days_until_break <= days_ahead:
                        warnings.append({
                            'pipeline_id': lead.id,
                            'pipeline_code': lead.lead_code,
                            'pipeline_type': 'LEAD',
                            'break_stage': 'LEAD_TO_OPP',
                            'days_until_break': days_until_break,
                            'responsible_person_id': lead.owner_id,
                            'responsible_person_name': lead.owner.real_name if lead.owner else None
                        })

        return warnings
