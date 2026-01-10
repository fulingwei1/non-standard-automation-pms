# -*- coding: utf-8 -*-
"""
资源浪费分析服务

分析失败线索投入的工程师资源，计算浪费成本，
识别高浪费销售人员和失败模式
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.project import Project, Customer
from app.models.user import User
from app.models.work_log import WorkLog
from app.models.enums import LeadOutcomeEnum, LossReasonEnum

logger = logging.getLogger(__name__)


class ResourceWasteAnalysisService:
    """资源浪费分析服务"""

    # 默认工时成本（元/小时）
    DEFAULT_HOURLY_RATE = Decimal('300')

    # 角色工时成本
    ROLE_HOURLY_RATES = {
        'engineer': Decimal('300'),      # 工程师
        'senior_engineer': Decimal('400'),  # 高级工程师
        'presales': Decimal('350'),       # 售前
        'designer': Decimal('320'),       # 设计师
        'project_manager': Decimal('450'),  # 项目经理
    }

    def __init__(self, db: Session, hourly_rate: Optional[Decimal] = None):
        self.db = db
        self.hourly_rate = hourly_rate or self.DEFAULT_HOURLY_RATE

    def get_lead_resource_investment(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """获取单个线索/项目的资源投入详情

        Returns:
            {
                'total_hours': float,
                'engineer_hours': dict,  # 按工程师分
                'monthly_hours': dict,   # 按月份分
                'stage_hours': dict,     # 按阶段分
                'estimated_cost': Decimal,
                'engineer_count': int
            }
        """
        work_logs = self.db.query(WorkLog).filter(
            WorkLog.project_id == project_id
        ).all()

        total_hours = 0.0
        engineer_hours = defaultdict(float)
        monthly_hours = defaultdict(float)
        stage_hours = defaultdict(float)

        for log in work_logs:
            hours = log.work_hours or 0
            total_hours += hours

            # 按工程师
            emp_id = log.employee_id or 0
            engineer_hours[emp_id] += hours

            # 按月份
            if log.work_date:
                month_key = log.work_date.strftime('%Y-%m')
                monthly_hours[month_key] += hours

            # 按工作类型/阶段
            work_type = getattr(log, 'work_type', 'other') or 'other'
            stage_hours[work_type] += hours

        # 获取工程师详情
        engineer_details = []
        for emp_id, hours in engineer_hours.items():
            if emp_id:
                user = self.db.query(User).filter(User.id == emp_id).first()
                engineer_details.append({
                    'employee_id': emp_id,
                    'employee_name': user.name if user else f'Employee_{emp_id}',
                    'hours': round(hours, 1),
                    'cost': float(Decimal(str(hours)) * self.hourly_rate)
                })

        estimated_cost = Decimal(str(total_hours)) * self.hourly_rate

        return {
            'total_hours': round(total_hours, 1),
            'engineer_hours': dict(engineer_hours),
            'engineer_details': sorted(engineer_details, key=lambda x: x['hours'], reverse=True),
            'monthly_hours': dict(sorted(monthly_hours.items())),
            'stage_hours': dict(stage_hours),
            'estimated_cost': estimated_cost,
            'engineer_count': len([h for h in engineer_hours.values() if h > 0])
        }

    def calculate_waste_by_period(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """计算指定周期内的资源浪费

        Returns:
            {
                'period': str,
                'total_leads': int,
                'won_leads': int,
                'lost_leads': int,
                'win_rate': float,
                'total_investment_hours': float,
                'productive_hours': float,  # 中标项目
                'wasted_hours': float,       # 失败项目
                'wasted_cost': Decimal,
                'waste_rate': float,
                'loss_reasons': dict
            }
        """
        projects = self.db.query(Project).filter(
            Project.created_at >= start_date,
            Project.created_at < end_date
        ).all()

        total_leads = len(projects)
        won_projects = [p for p in projects if p.outcome == LeadOutcomeEnum.WON.value]
        lost_projects = [p for p in projects if p.outcome in [
            LeadOutcomeEnum.LOST.value,
            LeadOutcomeEnum.ABANDONED.value
        ]]
        pending_projects = [p for p in projects if p.outcome in [
            LeadOutcomeEnum.PENDING.value,
            LeadOutcomeEnum.ON_HOLD.value,
            None
        ]]

        # 计算各类项目的工时
        total_investment_hours = 0.0
        productive_hours = 0.0
        wasted_hours = 0.0
        loss_reasons = defaultdict(int)

        # 获取所有相关工时
        project_ids = [p.id for p in projects]
        if project_ids:
            work_hours_map = dict(
                self.db.query(
                    WorkLog.project_id,
                    func.sum(WorkLog.work_hours)
                ).filter(
                    WorkLog.project_id.in_(project_ids)
                ).group_by(WorkLog.project_id).all()
            )
        else:
            work_hours_map = {}

        for project in projects:
            hours = work_hours_map.get(project.id, 0) or 0
            total_investment_hours += hours

            if project.outcome == LeadOutcomeEnum.WON.value:
                productive_hours += hours
            elif project.outcome in [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]:
                wasted_hours += hours
                reason = project.loss_reason or 'OTHER'
                loss_reasons[reason] += 1

        win_rate = len(won_projects) / (len(won_projects) + len(lost_projects)) if (len(won_projects) + len(lost_projects)) > 0 else 0
        waste_rate = wasted_hours / total_investment_hours if total_investment_hours > 0 else 0
        wasted_cost = Decimal(str(wasted_hours)) * self.hourly_rate

        return {
            'period': f'{start_date.isoformat()} ~ {end_date.isoformat()}',
            'total_leads': total_leads,
            'won_leads': len(won_projects),
            'lost_leads': len(lost_projects),
            'pending_leads': len(pending_projects),
            'win_rate': round(win_rate, 3),
            'total_investment_hours': round(total_investment_hours, 1),
            'productive_hours': round(productive_hours, 1),
            'wasted_hours': round(wasted_hours, 1),
            'wasted_cost': wasted_cost,
            'waste_rate': round(waste_rate, 3),
            'loss_reasons': dict(loss_reasons)
        }

    def get_salesperson_waste_ranking(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取销售人员资源浪费排行

        Returns:
            按浪费工时排序的销售人员列表
        """
        query = self.db.query(Project)

        if start_date:
            query = query.filter(Project.created_at >= start_date)
        if end_date:
            query = query.filter(Project.created_at < end_date)

        projects = query.all()

        # 按销售人员分组统计
        salesperson_stats = defaultdict(lambda: {
            'total_leads': 0,
            'won_leads': 0,
            'lost_leads': 0,
            'total_hours': 0.0,
            'wasted_hours': 0.0,
            'won_amount': Decimal('0'),
            'loss_reasons': defaultdict(int)
        })

        # 获取工时映射
        project_ids = [p.id for p in projects]
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

        for project in projects:
            sp_id = project.salesperson_id
            if not sp_id:
                continue

            stats = salesperson_stats[sp_id]
            stats['total_leads'] += 1

            hours = work_hours_map.get(project.id, 0) or 0
            stats['total_hours'] += hours

            if project.outcome == LeadOutcomeEnum.WON.value:
                stats['won_leads'] += 1
                stats['won_amount'] += project.contract_amount or Decimal('0')
            elif project.outcome in [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]:
                stats['lost_leads'] += 1
                stats['wasted_hours'] += hours
                reason = project.loss_reason or 'OTHER'
                stats['loss_reasons'][reason] += 1

        # 获取销售人员信息并构建结果
        results = []
        for sp_id, stats in salesperson_stats.items():
            user = self.db.query(User).filter(User.id == sp_id).first()

            win_rate = stats['won_leads'] / (stats['won_leads'] + stats['lost_leads']) \
                if (stats['won_leads'] + stats['lost_leads']) > 0 else 0

            wasted_cost = Decimal(str(stats['wasted_hours'])) * self.hourly_rate

            # 资源效率：中标金额 / 总投入工时
            resource_efficiency = float(stats['won_amount']) / stats['total_hours'] \
                if stats['total_hours'] > 0 else 0

            # 主要丢标原因（Top 3）
            top_reasons = sorted(stats['loss_reasons'].items(), key=lambda x: x[1], reverse=True)[:3]

            results.append({
                'salesperson_id': sp_id,
                'salesperson_name': user.name if user else f'Sales_{sp_id}',
                'department': getattr(user, 'department_name', None) if user else None,
                'total_leads': stats['total_leads'],
                'won_leads': stats['won_leads'],
                'lost_leads': stats['lost_leads'],
                'win_rate': round(win_rate, 3),
                'total_hours': round(stats['total_hours'], 1),
                'wasted_hours': round(stats['wasted_hours'], 1),
                'wasted_cost': wasted_cost,
                'won_amount': stats['won_amount'],
                'resource_efficiency': round(resource_efficiency, 2),
                'top_loss_reasons': [{'reason': r, 'count': c} for r, c in top_reasons]
            })

        # 按浪费工时排序
        results.sort(key=lambda x: x['wasted_hours'], reverse=True)

        return results[:limit]

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

        # 分析竞争对手多的项目
        # high_competitor_projects = [p for p in failed_projects if getattr(p, 'competitor_count', 0) > 4]
        # if len(high_competitor_projects) > len(failed_projects) * 0.4:
        #     high_waste_characteristics.append({
        #         'pattern': '高竞争线索失败率高',
        #         'description': f'竞争对手>4的线索占失败项目{len(high_competitor_projects)/len(failed_projects)*100:.0f}%',
        #         'suggestion': '对高竞争线索提前评估差异化优势，无优势则降低投入'
        #     })

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

    def get_monthly_trend(
        self,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """获取月度趋势数据

        Returns:
            近N个月的浪费趋势
        """
        results = []
        today = date.today()

        for i in range(months - 1, -1, -1):
            # 计算月份起止日期
            month_start = date(today.year, today.month, 1) - timedelta(days=30 * i)
            month_start = date(month_start.year, month_start.month, 1)

            if month_start.month == 12:
                month_end = date(month_start.year + 1, 1, 1)
            else:
                month_end = date(month_start.year, month_start.month + 1, 1)

            # 计算该月数据
            month_data = self.calculate_waste_by_period(month_start, month_end)

            results.append({
                'month': month_start.strftime('%Y-%m'),
                'total_leads': month_data['total_leads'],
                'won_leads': month_data['won_leads'],
                'lost_leads': month_data['lost_leads'],
                'win_rate': month_data['win_rate'],
                'total_hours': month_data['total_investment_hours'],
                'wasted_hours': month_data['wasted_hours'],
                'waste_rate': month_data['waste_rate'],
                'wasted_cost': float(month_data['wasted_cost'])
            })

        return results

    def get_department_comparison(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """获取部门间资源浪费对比

        Returns:
            按部门分组的浪费统计
        """
        # 获取销售人员及其部门
        # 这里简化处理，实际应该通过部门关联
        salesperson_rankings = self.get_salesperson_waste_ranking(start_date, end_date, limit=100)

        # 按部门分组
        department_stats = defaultdict(lambda: {
            'salespeople_count': 0,
            'total_leads': 0,
            'won_leads': 0,
            'lost_leads': 0,
            'total_hours': 0.0,
            'wasted_hours': 0.0,
            'won_amount': Decimal('0')
        })

        for sp in salesperson_rankings:
            dept = sp.get('department') or '未分配部门'
            stats = department_stats[dept]
            stats['salespeople_count'] += 1
            stats['total_leads'] += sp['total_leads']
            stats['won_leads'] += sp['won_leads']
            stats['lost_leads'] += sp['lost_leads']
            stats['total_hours'] += sp['total_hours']
            stats['wasted_hours'] += sp['wasted_hours']
            stats['won_amount'] += sp['won_amount']

        results = []
        for dept, stats in department_stats.items():
            win_rate = stats['won_leads'] / (stats['won_leads'] + stats['lost_leads']) \
                if (stats['won_leads'] + stats['lost_leads']) > 0 else 0
            waste_rate = stats['wasted_hours'] / stats['total_hours'] \
                if stats['total_hours'] > 0 else 0

            results.append({
                'department': dept,
                'salespeople_count': stats['salespeople_count'],
                'total_leads': stats['total_leads'],
                'won_leads': stats['won_leads'],
                'lost_leads': stats['lost_leads'],
                'win_rate': round(win_rate, 3),
                'total_hours': round(stats['total_hours'], 1),
                'wasted_hours': round(stats['wasted_hours'], 1),
                'wasted_cost': Decimal(str(stats['wasted_hours'])) * self.hourly_rate,
                'waste_rate': round(waste_rate, 3),
                'won_amount': stats['won_amount']
            })

        # 按浪费工时排序
        results.sort(key=lambda x: x['wasted_hours'], reverse=True)

        return results

    def generate_waste_report(
        self,
        period: str  # 'YYYY' or 'YYYY-MM'
    ) -> Dict[str, Any]:
        """生成资源浪费综合报告

        Returns:
            完整的资源浪费分析报告
        """
        # 解析周期
        if len(period) == 7:  # YYYY-MM
            year, month = int(period[:4]), int(period[5:7])
            start_date = date(year, month, 1)
            end_date = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        else:  # YYYY
            year = int(period)
            start_date = date(year, 1, 1)
            end_date = date(year + 1, 1, 1)

        # 1. 总体统计
        overall_stats = self.calculate_waste_by_period(start_date, end_date)

        # 2. 销售人员排行（Top 10 浪费最多）
        top_wasters = self.get_salesperson_waste_ranking(start_date, end_date, limit=10)

        # 3. 失败模式分析
        failure_patterns = self.analyze_failure_patterns(start_date, end_date)

        # 4. 月度趋势（如果是年度报告）
        monthly_trend = []
        if len(period) == 4:  # 年度
            monthly_trend = self.get_monthly_trend(12)

        # 5. 部门对比
        department_comparison = self.get_department_comparison(start_date, end_date)

        return {
            'report_period': period,
            'generated_at': datetime.now().isoformat(),
            'overall_statistics': overall_stats,
            'top_resource_wasters': top_wasters,
            'failure_pattern_analysis': failure_patterns,
            'monthly_trend': monthly_trend,
            'department_comparison': department_comparison,
            'summary': {
                'total_wasted_cost': overall_stats['wasted_cost'],
                'waste_rate': overall_stats['waste_rate'],
                'top_loss_reason': max(
                    overall_stats['loss_reasons'].items(),
                    key=lambda x: x[1]
                )[0] if overall_stats['loss_reasons'] else 'N/A',
                'key_recommendation': failure_patterns['recommendations'][0]
                if failure_patterns['recommendations'] else '暂无建议'
            }
        }
