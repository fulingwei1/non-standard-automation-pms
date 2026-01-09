# -*- coding: utf-8 -*-
"""
指标计算服务
根据ReportMetricDefinition配置动态计算指标值
"""
from datetime import date, datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_, case, extract

from app.models.management_rhythm import ReportMetricDefinition
from app.models.project import Project
from app.models.sales import Lead, Opportunity, Contract, ContractPayment, Invoice
from app.models.purchase import PurchaseOrder, PurchaseOrderItem, GoodsReceipt
from app.models.material import Material, ShortageReport
from app.models.ecn import Ecn
from app.models.acceptance import AcceptanceOrder, AcceptanceIssue
from app.models.issue import Issue
from app.models.alert import AlertRecord
from app.models.timesheet import Timesheet
from app.models.performance import PerformanceResult
from app.models.outsourcing import OutsourcingOrder
from app.models.task_center import TaskUnified
from app.models.management_rhythm import StrategicMeeting, MeetingActionItem


class MetricCalculationService:
    """指标计算服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_source_map = {
            'Project': Project,
            'Lead': Lead,
            'Opportunity': Opportunity,
            'Contract': Contract,
            'ContractPayment': ContractPayment,
            'Invoice': Invoice,
            'PurchaseOrder': PurchaseOrder,
            'PurchaseOrderItem': PurchaseOrderItem,
            'GoodsReceipt': GoodsReceipt,
            'Material': Material,
            'ShortageReport': ShortageReport,
            'Ecn': Ecn,
            'AcceptanceOrder': AcceptanceOrder,
            'AcceptanceIssue': AcceptanceIssue,
            'Issue': Issue,
            'AlertRecord': AlertRecord,
            'Timesheet': Timesheet,
            'PerformanceResult': PerformanceResult,
            'OutsourcingOrder': OutsourcingOrder,
            'TaskUnified': TaskUnified,
            'StrategicMeeting': StrategicMeeting,
            'MeetingActionItem': MeetingActionItem,
        }
    
    def calculate_metric(
        self,
        metric_code: str,
        period_start: date,
        period_end: date,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        计算单个指标值
        
        Args:
            metric_code: 指标编码
            period_start: 周期开始日期
            period_end: 周期结束日期
            filter_conditions: 额外筛选条件
            
        Returns:
            指标计算结果
        """
        # 获取指标定义
        metric_def = self.db.query(ReportMetricDefinition).filter(
            ReportMetricDefinition.metric_code == metric_code,
            ReportMetricDefinition.is_active == True
        ).first()
        
        if not metric_def:
            raise ValueError(f"指标定义不存在或未启用: {metric_code}")
        
        # 获取数据源模型
        model_class = self.data_source_map.get(metric_def.data_source)
        if not model_class:
            raise ValueError(f"不支持的数据源: {metric_def.data_source}")
        
        # 构建查询
        query = self.db.query(model_class)
        
        # 应用时间筛选（根据指标定义中的字段）
        query = self._apply_period_filter(query, model_class, period_start, period_end, metric_def)
        
        # 应用指标定义中的筛选条件
        if metric_def.filter_conditions:
            query = self._apply_filter_conditions(query, model_class, metric_def.filter_conditions, period_start, period_end)
        
        # 应用额外筛选条件
        if filter_conditions:
            query = self._apply_filter_conditions(query, model_class, filter_conditions, period_start, period_end)
        
        # 根据计算类型计算结果
        result = self._calculate_by_type(query, model_class, metric_def)
        
        return {
            "metric_code": metric_code,
            "metric_name": metric_def.metric_name,
            "value": result,
            "unit": metric_def.unit or "",
            "format_type": metric_def.format_type,
            "decimal_places": metric_def.decimal_places
        }
    
    def _apply_period_filter(self, query, model_class, period_start: date, period_end: date, metric_def: ReportMetricDefinition):
        """应用时间周期筛选"""
        # 根据指标定义确定时间字段
        time_field = None
        
        # 根据数据源类型确定时间字段
        if metric_def.data_source == 'Project':
            # 根据指标类型选择时间字段
            if 'new' in metric_def.metric_code or '新增' in metric_def.metric_name:
                time_field = model_class.created_at
            elif 'completed' in metric_def.metric_code or '完成' in metric_def.metric_name:
                time_field = model_class.actual_end_date
            elif 'contract' in metric_def.metric_code or '合同' in metric_def.metric_name:
                time_field = model_class.contract_date
        elif metric_def.data_source in ['Lead', 'Opportunity', 'Contract', 'PurchaseOrder', 'Ecn', 'AcceptanceOrder', 'Issue', 'AlertRecord', 'OutsourcingOrder', 'TaskUnified']:
            if 'new' in metric_def.metric_code or '新增' in metric_def.metric_name:
                time_field = model_class.created_at
            else:
                # 尝试查找日期字段
                if hasattr(model_class, 'created_at'):
                    time_field = model_class.created_at
        elif metric_def.data_source == 'ContractPayment':
            time_field = model_class.payment_date if hasattr(model_class, 'payment_date') else model_class.created_at
        elif metric_def.data_source == 'Invoice':
            time_field = model_class.issue_date if hasattr(model_class, 'issue_date') else model_class.created_at
        elif metric_def.data_source == 'Timesheet':
            time_field = model_class.work_date if hasattr(model_class, 'work_date') else model_class.created_at
        elif metric_def.data_source in ['StrategicMeeting', 'MeetingActionItem']:
            if hasattr(model_class, 'meeting_date'):
                time_field = model_class.meeting_date
            elif hasattr(model_class, 'created_at'):
                time_field = model_class.created_at
        
        # 应用时间筛选
        if time_field:
            if isinstance(time_field.property.columns[0].type.python_type, datetime):
                # 日期时间字段
                query = query.filter(
                    and_(
                        func.date(time_field) >= period_start,
                        func.date(time_field) <= period_end
                    )
                )
            else:
                # 日期字段
                query = query.filter(
                    and_(
                        time_field >= period_start,
                        time_field <= period_end
                    )
                )
        
        return query
    
    def _apply_filter_conditions(self, query, model_class, filter_conditions: Dict[str, Any], period_start: date, period_end: date):
        """应用筛选条件"""
        if not filter_conditions or 'filters' not in filter_conditions:
            return query
        
        for filter_item in filter_conditions['filters']:
            field_name = filter_item.get('field')
            operator = filter_item.get('operator', '=')
            value = filter_item.get('value')
            
            if not field_name or not hasattr(model_class, field_name):
                continue
            
            field = getattr(model_class, field_name)
            
            # 处理特殊值
            if value == 'period_start':
                value = period_start
            elif value == 'period_end':
                value = period_end
            
            # 应用操作符
            if operator == '=':
                query = query.filter(field == value)
            elif operator == '!=':
                query = query.filter(field != value)
            elif operator == '>':
                query = query.filter(field > value)
            elif operator == '>=':
                query = query.filter(field >= value)
            elif operator == '<':
                query = query.filter(field < value)
            elif operator == '<=':
                query = query.filter(field <= value)
            elif operator == 'IN':
                if isinstance(value, list):
                    query = query.filter(field.in_(value))
                elif isinstance(value, str):
                    # 尝试解析为列表
                    value_list = [v.strip() for v in value.split(',')]
                    query = query.filter(field.in_(value_list))
            elif operator == 'NOT IN':
                if isinstance(value, list):
                    query = query.filter(~field.in_(value))
        
        return query
    
    def _calculate_by_type(self, query, model_class, metric_def: ReportMetricDefinition):
        """根据计算类型计算结果"""
        calculation_type = metric_def.calculation_type
        
        if calculation_type == 'COUNT':
            return query.count()
        
        elif calculation_type == 'SUM':
            if not metric_def.data_field:
                raise ValueError(f"SUM计算类型需要指定data_field: {metric_def.metric_code}")
            field = getattr(model_class, metric_def.data_field)
            result = query.with_entities(func.sum(field)).scalar()
            return float(result) if result else 0.0
        
        elif calculation_type == 'AVG':
            if not metric_def.data_field:
                raise ValueError(f"AVG计算类型需要指定data_field: {metric_def.metric_code}")
            field = getattr(model_class, metric_def.data_field)
            result = query.with_entities(func.avg(field)).scalar()
            return float(result) if result else 0.0
        
        elif calculation_type == 'MAX':
            if not metric_def.data_field:
                raise ValueError(f"MAX计算类型需要指定data_field: {metric_def.metric_code}")
            field = getattr(model_class, metric_def.data_field)
            result = query.with_entities(func.max(field)).scalar()
            return float(result) if result else 0.0
        
        elif calculation_type == 'MIN':
            if not metric_def.data_field:
                raise ValueError(f"MIN计算类型需要指定data_field: {metric_def.metric_code}")
            field = getattr(model_class, metric_def.data_field)
            result = query.with_entities(func.min(field)).scalar()
            return float(result) if result else 0.0
        
        elif calculation_type == 'RATIO':
            # 比率计算需要自定义公式
            return self._calculate_ratio(query, model_class, metric_def)
        
        elif calculation_type == 'CUSTOM':
            # 自定义公式计算
            return self._calculate_custom(query, model_class, metric_def)
        
        else:
            raise ValueError(f"不支持的计算类型: {calculation_type}")
    
    def _calculate_ratio(self, query, model_class, metric_def: ReportMetricDefinition):
        """计算比率"""
        # 解析比率公式，例如: "COUNT(WHERE status='COMPLETED') / COUNT()"
        formula = metric_def.calculation_formula or ""
        
        if not formula:
            raise ValueError(f"RATIO计算类型需要提供calculation_formula: {metric_def.metric_code}")
        
        # 简单的比率计算：分子/分母
        # 例如：已完成数 / 总数
        if 'COMPLETED' in formula.upper() and 'COUNT()' in formula:
            # 已完成数 / 总数
            total_count = query.count()
            if total_count == 0:
                return 0.0
            
            # 根据数据源确定完成状态字段
            if hasattr(model_class, 'status'):
                completed_count = query.filter(model_class.status == 'COMPLETED').count()
            elif hasattr(model_class, 'status'):
                completed_count = query.filter(model_class.status.in_(['COMPLETED', 'RESOLVED', 'APPROVED'])).count()
            else:
                completed_count = 0
            
            return (completed_count / total_count * 100) if total_count > 0 else 0.0
        
        # 其他比率计算可以根据需要扩展
        return 0.0
    
    def _calculate_custom(self, query, model_class, metric_def: ReportMetricDefinition):
        """自定义公式计算"""
        formula = metric_def.calculation_formula
        if not formula:
            raise ValueError(f"CUSTOM计算类型需要提供calculation_formula: {metric_def.metric_code}")
        
        # 这里可以实现更复杂的公式解析和计算
        # 目前先返回0，后续可以扩展
        return 0.0
    
    def calculate_metrics_batch(
        self,
        metric_codes: List[str],
        period_start: date,
        period_end: date
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量计算多个指标
        
        Args:
            metric_codes: 指标编码列表
            period_start: 周期开始日期
            period_end: 周期结束日期
            
        Returns:
            指标计算结果字典 {metric_code: result}
        """
        results = {}
        for metric_code in metric_codes:
            try:
                result = self.calculate_metric(metric_code, period_start, period_end)
                results[metric_code] = result
            except Exception as e:
                # 记录错误但继续计算其他指标
                results[metric_code] = {
                    "metric_code": metric_code,
                    "error": str(e),
                    "value": None
                }
        
        return results
    
    def format_metric_value(self, value: Any, format_type: str, decimal_places: int = 2) -> str:
        """格式化指标值"""
        if value is None:
            return "-"
        
        if format_type == 'NUMBER':
            if isinstance(value, float):
                return f"{value:.{decimal_places}f}"
            return str(value)
        
        elif format_type == 'PERCENTAGE':
            if isinstance(value, (int, float)):
                return f"{value:.{decimal_places}f}%"
            return str(value)
        
        elif format_type == 'CURRENCY':
            if isinstance(value, (int, float, Decimal)):
                return f"¥{value:,.{decimal_places}f}"
            return str(value)
        
        else:
            return str(value)
