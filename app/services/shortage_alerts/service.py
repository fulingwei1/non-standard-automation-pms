# -*- coding: utf-8 -*-
"""
缺料预警业务逻辑服务
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.shortage.smart_alert import (
    ShortageAlert,
    ShortageHandlingPlan,
    MaterialDemandForecast
)
from app.models.project import Project
from app.services.shortage.smart_alert_engine import SmartAlertEngine
from app.services.shortage.demand_forecast_engine import DemandForecastEngine
from app.core.exceptions import BusinessException


class ShortageAlertService:
    """缺料预警业务逻辑服务"""
    
    def __init__(self, db: Session):
        """
        初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def get_alerts_with_filters(
        self,
        project_id: Optional[int] = None,
        material_id: Optional[int] = None,
        alert_level: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ShortageAlert], int]:
        """
        获取缺料预警列表（支持多维度筛选和分页）
        
        Args:
            project_id: 项目ID
            material_id: 物料ID
            alert_level: 预警级别
            status: 状态
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            page_size: 每页数量
            
        Returns:
            (预警列表, 总数)
        """
        query = self.db.query(ShortageAlert)
        
        # 构建过滤条件
        filters = []
        
        if project_id:
            filters.append(ShortageAlert.project_id == project_id)
        if material_id:
            filters.append(ShortageAlert.material_id == material_id)
        if alert_level:
            filters.append(ShortageAlert.alert_level == alert_level)
        if status:
            filters.append(ShortageAlert.status == status)
        if start_date:
            filters.append(ShortageAlert.alert_date >= start_date)
        if end_date:
            filters.append(ShortageAlert.alert_date <= end_date)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        alerts = query.order_by(desc(ShortageAlert.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return alerts, total
    
    def get_alert_by_id(self, alert_id: int) -> ShortageAlert:
        """
        获取缺料预警详情
        
        Args:
            alert_id: 预警ID
            
        Returns:
            预警对象
            
        Raises:
            BusinessException: 预警不存在
        """
        alert = self.db.query(ShortageAlert).filter(
            ShortageAlert.id == alert_id
        ).first()
        
        if not alert:
            raise BusinessException("预警不存在")
        
        return alert
    
    def trigger_scan(
        self,
        project_id: Optional[int] = None,
        material_id: Optional[int] = None,
        days_ahead: int = 7
    ) -> Tuple[List[ShortageAlert], datetime]:
        """
        触发缺料扫描
        
        Args:
            project_id: 项目ID
            material_id: 物料ID
            days_ahead: 提前天数
            
        Returns:
            (预警列表, 扫描时间)
        """
        engine = SmartAlertEngine(self.db)
        
        alerts = engine.scan_and_alert(
            project_id=project_id,
            material_id=material_id,
            days_ahead=days_ahead
        )
        
        return alerts, datetime.now()
    
    def get_handling_solutions(self, alert_id: int) -> List[ShortageHandlingPlan]:
        """
        获取预警的处理方案
        
        Args:
            alert_id: 预警ID
            
        Returns:
            处理方案列表（按评分排序）
            
        Raises:
            BusinessException: 预警不存在
        """
        alert = self.get_alert_by_id(alert_id)
        
        # 查询现有处理方案
        plans = self.db.query(ShortageHandlingPlan).filter(
            ShortageHandlingPlan.alert_id == alert_id
        ).order_by(desc(ShortageHandlingPlan.ai_score)).all()
        
        # 如果没有方案，自动生成
        if not plans:
            engine = SmartAlertEngine(self.db)
            plans = engine.generate_solutions(alert)
        
        return plans
    
    def resolve_alert(
        self,
        alert_id: int,
        handler_id: int,
        resolution_type: Optional[str] = None,
        resolution_note: Optional[str] = None,
        actual_cost_impact: Optional[float] = None,
        actual_delay_days: Optional[int] = None
    ) -> ShortageAlert:
        """
        标记预警已解决
        
        Args:
            alert_id: 预警ID
            handler_id: 处理人ID
            resolution_type: 解决方式
            resolution_note: 解决说明
            actual_cost_impact: 实际成本影响
            actual_delay_days: 实际延误天数
            
        Returns:
            更新后的预警对象
            
        Raises:
            BusinessException: 预警不存在或已解决
        """
        alert = self.get_alert_by_id(alert_id)
        
        if alert.status == 'RESOLVED':
            raise BusinessException("预警已解决")
        
        # 更新状态
        alert.status = 'RESOLVED'
        alert.resolved_at = datetime.now()
        alert.handler_id = handler_id
        
        if resolution_type:
            alert.resolution_type = resolution_type
        if resolution_note:
            alert.resolution_note = resolution_note
        if actual_cost_impact is not None:
            alert.actual_cost_impact = actual_cost_impact
        if actual_delay_days is not None:
            alert.actual_delay_days = actual_delay_days
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def get_material_forecast(
        self,
        material_id: int,
        forecast_horizon_days: int = 30,
        algorithm: str = 'EXP_SMOOTHING',
        historical_days: int = 90,
        project_id: Optional[int] = None
    ) -> MaterialDemandForecast:
        """
        获取物料需求预测
        
        Args:
            material_id: 物料ID
            forecast_horizon_days: 预测周期（天）
            algorithm: 预测算法
            historical_days: 历史数据周期（天）
            project_id: 项目ID
            
        Returns:
            需求预测对象
        """
        engine = DemandForecastEngine(self.db)
        
        forecast = engine.forecast_material_demand(
            material_id=material_id,
            forecast_horizon_days=forecast_horizon_days,
            algorithm=algorithm,
            historical_days=historical_days,
            project_id=project_id
        )
        
        return forecast
    
    def analyze_shortage_trend(
        self,
        days: int = 30,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        缺料趋势分析
        
        Args:
            days: 统计天数
            project_id: 项目ID
            
        Returns:
            趋势分析结果字典
        """
        start_date = datetime.now().date() - timedelta(days=days)
        
        query = self.db.query(ShortageAlert).filter(
            ShortageAlert.alert_date >= start_date
        )
        
        if project_id:
            query = query.filter(ShortageAlert.project_id == project_id)
        
        alerts = query.all()
        
        # 统计数据
        total_alerts = len(alerts)
        by_level = {}
        by_status = {}
        total_resolution_hours = 0
        resolved_count = 0
        total_cost_impact = 0
        
        for alert in alerts:
            # 按级别统计
            level = alert.alert_level
            by_level[level] = by_level.get(level, 0) + 1
            
            # 按状态统计
            status = alert.status
            by_status[status] = by_status.get(status, 0) + 1
            
            # 解决时长
            if alert.resolved_at and alert.detected_at:
                hours = (alert.resolved_at - alert.detected_at).total_seconds() / 3600
                total_resolution_hours += hours
                resolved_count += 1
            
            # 成本影响
            total_cost_impact += float(alert.estimated_cost_impact or 0)
        
        avg_resolution_hours = (
            total_resolution_hours / resolved_count if resolved_count > 0 else 0
        )
        
        # 每日趋势数据
        trend_data = []
        current_date = start_date
        while current_date <= datetime.now().date():
            daily_alerts = [
                a for a in alerts
                if a.alert_date == current_date
            ]
            
            trend_data.append({
                'date': current_date.isoformat(),
                'count': len(daily_alerts),
                'urgent': sum(1 for a in daily_alerts if a.alert_level == 'URGENT'),
                'critical': sum(1 for a in daily_alerts if a.alert_level == 'CRITICAL'),
                'warning': sum(1 for a in daily_alerts if a.alert_level == 'WARNING'),
                'info': sum(1 for a in daily_alerts if a.alert_level == 'INFO'),
            })
            
            current_date += timedelta(days=1)
        
        return {
            'period_start': start_date,
            'period_end': datetime.now().date(),
            'total_alerts': total_alerts,
            'by_level': by_level,
            'by_status': by_status,
            'avg_resolution_hours': round(avg_resolution_hours, 2),
            'total_cost_impact': total_cost_impact,
            'trend_data': trend_data
        }
    
    def analyze_root_cause(self, days: int = 30) -> Dict[str, Any]:
        """
        缺料根因分析
        
        Args:
            days: 分析天数
            
        Returns:
            根因分析结果字典
        """
        start_date = datetime.now().date() - timedelta(days=days)
        
        alerts = self.db.query(ShortageAlert).filter(
            ShortageAlert.alert_date >= start_date
        ).all()
        
        total_analyzed = len(alerts)
        
        # 根因分类
        cause_map = {
            '供应商交期延误': [],
            '需求预测不准': [],
            '库存管理不当': [],
            '采购流程延迟': [],
            '计划变更频繁': [],
            '其他原因': []
        }
        
        for alert in alerts:
            # 根据预警数据推断根因
            if alert.in_transit_qty > 0:
                cause_map['供应商交期延误'].append(alert)
            elif alert.available_qty == 0:
                cause_map['库存管理不当'].append(alert)
            elif alert.estimated_delay_days > 7:
                cause_map['采购流程延迟'].append(alert)
            else:
                cause_map['需求预测不准'].append(alert)
        
        # 构建结果
        top_causes = []
        for cause, alert_list in cause_map.items():
            if alert_list:
                count = len(alert_list)
                percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
                avg_cost = sum(float(a.estimated_cost_impact or 0) for a in alert_list) / count
                
                top_causes.append({
                    'cause': cause,
                    'count': count,
                    'percentage': round(percentage, 2),
                    'avg_cost_impact': avg_cost,
                    'examples': [a.alert_no for a in alert_list[:3]]
                })
        
        # 按数量排序
        top_causes.sort(key=lambda x: x['count'], reverse=True)
        
        # 生成改进建议
        recommendations = []
        if top_causes:
            top_cause = top_causes[0]['cause']
            if '供应商' in top_cause:
                recommendations.append("加强供应商管理，建立备用供应商")
                recommendations.append("与供应商签订SLA协议，明确交期保障")
            elif '预测' in top_cause:
                recommendations.append("优化需求预测算法，提高预测准确率")
                recommendations.append("引入AI预测模型，考虑季节性因素")
            elif '库存' in top_cause:
                recommendations.append("建立安全库存机制，设置最低库存预警")
                recommendations.append("优化库存周转率，避免积压和缺货")
            elif '采购' in top_cause:
                recommendations.append("简化采购流程，提高审批效率")
                recommendations.append("对紧急采购建立快速通道")
        
        return {
            'period_start': start_date,
            'period_end': datetime.now().date(),
            'total_analyzed': total_analyzed,
            'top_causes': top_causes[:5],
            'recommendations': recommendations
        }
    
    def analyze_project_impact(
        self,
        alert_level: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        缺料对项目的影响分析
        
        Args:
            alert_level: 预警级别过滤
            status: 状态过滤
            
        Returns:
            项目影响列表
        """
        query = self.db.query(
            ShortageAlert.project_id,
            func.count(ShortageAlert.id).label('alert_count'),
            func.sum(ShortageAlert.shortage_qty).label('total_shortage_qty'),
            func.max(ShortageAlert.estimated_delay_days).label('max_delay_days'),
            func.sum(ShortageAlert.estimated_cost_impact).label('total_cost_impact')
        ).filter(
            ShortageAlert.status.in_(['PENDING', 'PROCESSING'])
        )
        
        if alert_level:
            query = query.filter(ShortageAlert.alert_level == alert_level)
        if status:
            query = query.filter(ShortageAlert.status == status)
        
        query = query.group_by(ShortageAlert.project_id)
        
        results = query.all()
        
        # 构建项目影响列表
        items = []
        for row in results:
            project = self.db.query(Project).filter(Project.id == row.project_id).first()
            
            # 获取关键物料
            critical_materials_query = self.db.query(ShortageAlert.material_name).filter(
                and_(
                    ShortageAlert.project_id == row.project_id,
                    ShortageAlert.alert_level.in_(['URGENT', 'CRITICAL'])
                )
            ).limit(5).all()
            
            critical_materials = [m[0] for m in critical_materials_query]
            
            items.append({
                'project_id': row.project_id,
                'project_name': project.project_name if project else f"项目{row.project_id}",
                'alert_count': row.alert_count,
                'total_shortage_qty': row.total_shortage_qty or 0,
                'estimated_delay_days': row.max_delay_days or 0,
                'estimated_cost_impact': row.total_cost_impact or 0,
                'critical_materials': critical_materials
            })
        
        # 按成本影响排序
        items.sort(key=lambda x: x['estimated_cost_impact'], reverse=True)
        
        return items
    
    def create_notification_subscription(
        self,
        user_id: int,
        alert_levels: List[str],
        project_ids: Optional[List[int]] = None,
        material_ids: Optional[List[int]] = None,
        notification_channels: List[str] = None,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        创建预警通知订阅
        
        Args:
            user_id: 用户ID
            alert_levels: 预警级别列表
            project_ids: 项目ID列表
            material_ids: 物料ID列表
            notification_channels: 通知渠道列表
            enabled: 是否启用
            
        Returns:
            订阅信息字典
        """
        # 简化实现：直接返回订阅信息
        # 实际应该存储到数据库的notification_subscriptions表
        
        subscription_id = int(datetime.now().timestamp())
        
        return {
            'subscription_id': subscription_id,
            'user_id': user_id,
            'alert_levels': alert_levels,
            'project_ids': project_ids or [],
            'material_ids': material_ids or [],
            'notification_channels': notification_channels or ['EMAIL'],
            'enabled': enabled,
            'created_at': datetime.now()
        }
