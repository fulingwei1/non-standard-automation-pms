# -*- coding: utf-8 -*-
"""
生产进度跟踪服务
包含核心算法：
1. 进度偏差计算引擎
2. 瓶颈工位识别算法
3. 进度预警规则引擎
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.production import (
    ProductionProgressLog,
    ProgressAlert,
    WorkOrder,
    Workstation,
    WorkstationStatus,
)
from app.schemas.production_progress import (
    ProductionProgressLogCreate,
    ProgressAlertCreate,
    ProgressDeviation,
    RealtimeProgressOverview,
    WorkOrderProgressTimeline,
)


class ProductionProgressService:
    """生产进度跟踪服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 核心算法1: 进度偏差计算引擎 ====================

    def calculate_progress_deviation(
        self,
        work_order_id: int,
        actual_progress: int,
        actual_date: Optional[date] = None
    ) -> Tuple[int, int, bool]:
        """
        计算进度偏差 (实际 vs 计划)
        
        Args:
            work_order_id: 工单ID
            actual_progress: 实际进度(%)
            actual_date: 实际日期，默认为今天
            
        Returns:
            (计划进度, 偏差, 是否延期)
        """
        if actual_date is None:
            actual_date = date.today()
            
        work_order = self.db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not work_order:
            return 0, 0, False
            
        # 计算计划进度
        plan_progress = self._calculate_planned_progress(work_order, actual_date)
        
        # 计算偏差
        deviation = actual_progress - plan_progress
        
        # 判断是否延期（实际进度低于计划进度超过5%认为延期）
        is_delayed = deviation < -5
        
        return plan_progress, deviation, is_delayed

    def _calculate_planned_progress(self, work_order: WorkOrder, target_date: date) -> int:
        """计算目标日期的计划进度"""
        if not work_order.plan_start_date or not work_order.plan_end_date:
            return 0
            
        plan_start = work_order.plan_start_date
        plan_end = work_order.plan_end_date
        
        # 如果还没开始
        if target_date < plan_start:
            return 0
            
        # 如果已经结束
        if target_date >= plan_end:
            return 100
            
        # 线性插值计算计划进度
        total_days = (plan_end - plan_start).days
        if total_days == 0:
            return 100
            
        elapsed_days = (target_date - plan_start).days
        plan_progress = int((elapsed_days / total_days) * 100)
        
        return min(max(plan_progress, 0), 100)

    def calculate_deviation_percentage(self, deviation: int, plan_progress: int) -> Decimal:
        """计算偏差百分比"""
        if plan_progress == 0:
            return Decimal('0')
        return Decimal(str(abs(deviation))) / Decimal(str(plan_progress)) * Decimal('100')

    # ==================== 核心算法2: 瓶颈工位识别算法 ====================

    def identify_bottlenecks(
        self,
        workshop_id: Optional[int] = None,
        min_level: int = 1
    ) -> List[Dict]:
        """
        识别瓶颈工位（基于产能利用率）
        
        瓶颈判断规则：
        1. 产能利用率 > 90%：轻度瓶颈 (level=1)
        2. 产能利用率 > 95% 且有排队工单：中度瓶颈 (level=2)
        3. 产能利用率 > 98% 且排队工单 > 3：严重瓶颈 (level=3)
        
        Args:
            workshop_id: 车间ID筛选
            min_level: 最小瓶颈等级
            
        Returns:
            瓶颈工位列表
        """
        # 查询工位状态
        query = self.db.query(
            WorkstationStatus,
            Workstation,
        ).join(
            Workstation,
            WorkstationStatus.workstation_id == Workstation.id
        ).filter(
            Workstation.is_active == True,
            WorkstationStatus.capacity_utilization >= 90  # 利用率≥90%
        )
        
        if workshop_id:
            query = query.filter(Workstation.workshop_id == workshop_id)
            
        results = query.all()
        
        bottlenecks = []
        for ws_status, workstation in results:
            # 计算瓶颈等级
            level, reason = self._calculate_bottleneck_level(ws_status, workstation.id)
            
            if level >= min_level:
                # 统计工单数量
                current_wo_count = self.db.query(func.count(WorkOrder.id)).filter(
                    WorkOrder.workstation_id == workstation.id,
                    WorkOrder.status == 'IN_PROGRESS'
                ).scalar() or 0
                
                pending_wo_count = self.db.query(func.count(WorkOrder.id)).filter(
                    WorkOrder.workstation_id == workstation.id,
                    WorkOrder.status == 'PENDING'
                ).scalar() or 0
                
                bottlenecks.append({
                    'workstation_id': workstation.id,
                    'workstation_code': workstation.workstation_code,
                    'workstation_name': workstation.workstation_name,
                    'bottleneck_level': level,
                    'capacity_utilization': ws_status.capacity_utilization,
                    'work_hours_today': ws_status.work_hours_today,
                    'idle_hours_today': ws_status.idle_hours_today,
                    'current_work_order_count': current_wo_count,
                    'pending_work_order_count': pending_wo_count,
                    'alert_count': ws_status.alert_count,
                    'bottleneck_reason': reason,
                })
                
        # 按瓶颈等级和产能利用率排序
        bottlenecks.sort(key=lambda x: (x['bottleneck_level'], x['capacity_utilization']), reverse=True)
        
        return bottlenecks

    def _calculate_bottleneck_level(self, ws_status: WorkstationStatus, workstation_id: int) -> Tuple[int, str]:
        """计算瓶颈等级和原因"""
        utilization = float(ws_status.capacity_utilization)
        
        # 统计排队工单
        pending_count = self.db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.workstation_id == workstation_id,
            WorkOrder.status == 'PENDING'
        ).scalar() or 0
        
        if utilization > 98 and pending_count > 3:
            return 3, f"产能利用率{utilization:.1f}%，排队工单{pending_count}个"
        elif utilization > 95 and pending_count > 0:
            return 2, f"产能利用率{utilization:.1f}%，排队工单{pending_count}个"
        elif utilization > 90:
            return 1, f"产能利用率{utilization:.1f}%"
        else:
            return 0, "正常"

    # ==================== 核心算法3: 进度预警规则引擎 ====================

    def evaluate_alert_rules(self, work_order_id: int, user_id: int) -> List[ProgressAlertCreate]:
        """
        评估进度预警规则
        
        预警规则：
        1. DELAY：进度偏差 < -10%
        2. CRITICAL_DELAY：进度偏差 < -20%
        3. BOTTLENECK：所在工位为瓶颈
        4. QUALITY：合格率 < 95%
        5. EFFICIENCY：效率 < 80%
        
        Returns:
            需要创建的预警列表
        """
        work_order = self.db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not work_order:
            return []
            
        alerts = []
        
        # 规则1: 进度延期预警
        plan_progress, deviation, is_delayed = self.calculate_progress_deviation(
            work_order_id,
            work_order.progress
        )
        
        if deviation < -20:
            alerts.append(ProgressAlertCreate(
                work_order_id=work_order_id,
                workstation_id=work_order.workstation_id,
                alert_type='DELAY',
                alert_level='CRITICAL',
                alert_title='严重进度延期',
                alert_message=f'工单 {work_order.work_order_no} 进度严重落后，偏差{deviation}%',
                current_value=Decimal(str(work_order.progress)),
                threshold_value=Decimal(str(plan_progress)),
                deviation_value=Decimal(str(deviation)),
                rule_code='RULE_DELAY_CRITICAL',
                rule_name='严重延期预警规则'
            ))
        elif deviation < -10:
            alerts.append(ProgressAlertCreate(
                work_order_id=work_order_id,
                workstation_id=work_order.workstation_id,
                alert_type='DELAY',
                alert_level='WARNING',
                alert_title='进度延期预警',
                alert_message=f'工单 {work_order.work_order_no} 进度落后，偏差{deviation}%',
                current_value=Decimal(str(work_order.progress)),
                threshold_value=Decimal(str(plan_progress)),
                deviation_value=Decimal(str(deviation)),
                rule_code='RULE_DELAY_WARNING',
                rule_name='延期预警规则'
            ))
            
        # 规则2: 瓶颈预警
        if work_order.workstation_id:
            ws_status = self.db.query(WorkstationStatus).filter(
                WorkstationStatus.workstation_id == work_order.workstation_id
            ).first()
            
            if ws_status and ws_status.is_bottleneck:
                level_map = {3: 'CRITICAL', 2: 'WARNING', 1: 'INFO'}
                alerts.append(ProgressAlertCreate(
                    work_order_id=work_order_id,
                    workstation_id=work_order.workstation_id,
                    alert_type='BOTTLENECK',
                    alert_level=level_map.get(ws_status.bottleneck_level, 'WARNING'),
                    alert_title='工位瓶颈预警',
                    alert_message=f'工位产能利用率{ws_status.capacity_utilization}%，存在瓶颈',
                    current_value=ws_status.capacity_utilization,
                    threshold_value=Decimal('90'),
                    rule_code='RULE_BOTTLENECK',
                    rule_name='瓶颈预警规则'
                ))
                
        # 规则3: 质量预警
        if work_order.completed_qty > 0:
            quality_rate = (work_order.qualified_qty / work_order.completed_qty) * 100
            if quality_rate < 95:
                alerts.append(ProgressAlertCreate(
                    work_order_id=work_order_id,
                    workstation_id=work_order.workstation_id,
                    alert_type='QUALITY',
                    alert_level='CRITICAL' if quality_rate < 90 else 'WARNING',
                    alert_title='质量预警',
                    alert_message=f'工单 {work_order.work_order_no} 合格率{quality_rate:.1f}%，低于标准',
                    current_value=Decimal(str(quality_rate)),
                    threshold_value=Decimal('95'),
                    deviation_value=Decimal(str(95 - quality_rate)),
                    rule_code='RULE_QUALITY',
                    rule_name='质量预警规则'
                ))
                
        # 规则4: 效率预警
        if work_order.standard_hours and work_order.actual_hours:
            efficiency = (float(work_order.standard_hours) / float(work_order.actual_hours)) * 100
            if efficiency < 80:
                alerts.append(ProgressAlertCreate(
                    work_order_id=work_order_id,
                    workstation_id=work_order.workstation_id,
                    alert_type='EFFICIENCY',
                    alert_level='WARNING',
                    alert_title='效率预警',
                    alert_message=f'工单 {work_order.work_order_no} 生产效率{efficiency:.1f}%，低于标准',
                    current_value=Decimal(str(efficiency)),
                    threshold_value=Decimal('80'),
                    deviation_value=Decimal(str(80 - efficiency)),
                    rule_code='RULE_EFFICIENCY',
                    rule_name='效率预警规则'
                ))
                
        return alerts

    # ==================== 业务方法 ====================

    def create_progress_log(
        self,
        log_data: ProductionProgressLogCreate,
        user_id: int
    ) -> ProductionProgressLog:
        """创建进度日志"""
        work_order = self.db.query(WorkOrder).filter(
            WorkOrder.id == log_data.work_order_id
        ).first()
        
        if not work_order:
            raise ValueError("工单不存在")
            
        # 获取上一次进度
        last_log = self.db.query(ProductionProgressLog).filter(
            ProductionProgressLog.work_order_id == log_data.work_order_id
        ).order_by(desc(ProductionProgressLog.logged_at)).first()
        
        previous_progress = last_log.current_progress if last_log else 0
        previous_status = last_log.status if last_log else work_order.status
        
        # 计算累计工时
        cumulative_hours = Decimal('0')
        if last_log and last_log.cumulative_hours:
            cumulative_hours = last_log.cumulative_hours
        if log_data.work_hours:
            cumulative_hours += log_data.work_hours
            
        # 计算进度偏差
        plan_progress, deviation, is_delayed = self.calculate_progress_deviation(
            log_data.work_order_id,
            log_data.current_progress
        )
        
        # 创建日志
        progress_log = ProductionProgressLog(
            work_order_id=log_data.work_order_id,
            workstation_id=log_data.workstation_id,
            previous_progress=previous_progress,
            current_progress=log_data.current_progress,
            progress_delta=log_data.current_progress - previous_progress,
            completed_qty=log_data.completed_qty,
            qualified_qty=log_data.qualified_qty,
            defect_qty=log_data.defect_qty,
            work_hours=log_data.work_hours,
            cumulative_hours=cumulative_hours,
            status=log_data.status,
            previous_status=previous_status,
            logged_at=datetime.now(),
            logged_by=user_id,
            note=log_data.note,
            plan_progress=plan_progress,
            deviation=deviation,
            is_delayed=1 if is_delayed else 0
        )
        
        self.db.add(progress_log)
        
        # 更新工单进度
        work_order.progress = log_data.current_progress
        work_order.status = log_data.status
        work_order.completed_qty = log_data.completed_qty
        work_order.qualified_qty = log_data.qualified_qty
        work_order.defect_qty = log_data.defect_qty
        if log_data.work_hours:
            work_order.actual_hours = (work_order.actual_hours or Decimal('0')) + log_data.work_hours
            
        # 评估预警规则
        alerts = self.evaluate_alert_rules(log_data.work_order_id, user_id)
        for alert_data in alerts:
            # 检查是否已有相同类型的活跃预警
            existing_alert = self.db.query(ProgressAlert).filter(
                ProgressAlert.work_order_id == alert_data.work_order_id,
                ProgressAlert.alert_type == alert_data.alert_type,
                ProgressAlert.status == 'ACTIVE'
            ).first()
            
            if not existing_alert:
                alert = ProgressAlert(
                    **alert_data.model_dump(),
                    triggered_at=datetime.now()
                )
                self.db.add(alert)
                
        # 更新工位状态
        if log_data.workstation_id:
            self._update_workstation_status(log_data.workstation_id, work_order.id)
            
        self.db.commit()
        self.db.refresh(progress_log)
        
        return progress_log

    def _update_workstation_status(self, workstation_id: int, work_order_id: int):
        """更新工位状态"""
        ws_status = self.db.query(WorkstationStatus).filter(
            WorkstationStatus.workstation_id == workstation_id
        ).first()
        
        if not ws_status:
            # 创建新状态
            ws_status = WorkstationStatus(
                workstation_id=workstation_id,
                current_state='BUSY',
                current_work_order_id=work_order_id,
                status_updated_at=datetime.now()
            )
            self.db.add(ws_status)
        else:
            ws_status.current_work_order_id = work_order_id
            ws_status.current_state = 'BUSY'
            ws_status.status_updated_at = datetime.now()
            
        # 计算今日产能利用率
        today = date.today()
        today_logs = self.db.query(
            func.sum(ProductionProgressLog.work_hours)
        ).filter(
            ProductionProgressLog.workstation_id == workstation_id,
            func.date(ProductionProgressLog.logged_at) == today
        ).scalar() or Decimal('0')
        
        ws_status.work_hours_today = today_logs
        ws_status.capacity_utilization = min(
            (today_logs / ws_status.planned_hours_today * Decimal('100'))
            if ws_status.planned_hours_today > 0 else Decimal('0'),
            Decimal('100')
        )
        
        # 识别瓶颈
        level, reason = self._calculate_bottleneck_level(ws_status, workstation_id)
        ws_status.is_bottleneck = 1 if level > 0 else 0
        ws_status.bottleneck_level = level

    def get_realtime_overview(self, workshop_id: Optional[int] = None) -> RealtimeProgressOverview:
        """获取实时进度总览"""
        query = self.db.query(WorkOrder)
        
        if workshop_id:
            query = query.filter(WorkOrder.workshop_id == workshop_id)
            
        total = query.count()
        in_progress = query.filter(WorkOrder.status == 'IN_PROGRESS').count()
        
        today = date.today()
        completed_today = query.filter(
            WorkOrder.status == 'COMPLETED',
            func.date(WorkOrder.actual_end_time) == today
        ).count()
        
        # 统计延期工单
        delayed_query = self.db.query(ProductionProgressLog.work_order_id).filter(
            ProductionProgressLog.is_delayed == 1
        ).distinct()
        if workshop_id:
            delayed_query = delayed_query.join(WorkOrder).filter(WorkOrder.workshop_id == workshop_id)
        delayed = delayed_query.count()
        
        # 统计工位
        ws_query = self.db.query(WorkstationStatus).join(Workstation)
        if workshop_id:
            ws_query = ws_query.filter(Workstation.workshop_id == workshop_id)
            
        active_ws = ws_query.filter(WorkstationStatus.current_state.in_(['BUSY', 'PAUSED'])).count()
        idle_ws = ws_query.filter(WorkstationStatus.current_state == 'IDLE').count()
        bottleneck_ws = ws_query.filter(WorkstationStatus.is_bottleneck == 1).count()
        
        # 统计预警
        alert_query = self.db.query(ProgressAlert).filter(ProgressAlert.status == 'ACTIVE')
        if workshop_id:
            alert_query = alert_query.join(WorkOrder).filter(WorkOrder.workshop_id == workshop_id)
            
        active_alerts = alert_query.count()
        critical_alerts = alert_query.filter(ProgressAlert.alert_level == 'CRITICAL').count()
        
        # 计算整体进度
        avg_progress = self.db.query(func.avg(WorkOrder.progress)).filter(
            WorkOrder.status.in_(['IN_PROGRESS', 'PENDING'])
        )
        if workshop_id:
            avg_progress = avg_progress.filter(WorkOrder.workshop_id == workshop_id)
        overall_progress = avg_progress.scalar() or Decimal('0')
        
        # 计算整体产能利用率
        avg_utilization = self.db.query(func.avg(WorkstationStatus.capacity_utilization)).join(Workstation)
        if workshop_id:
            avg_utilization = avg_utilization.filter(Workstation.workshop_id == workshop_id)
        overall_utilization = avg_utilization.scalar() or Decimal('0')
        
        # 计算平均效率
        avg_efficiency = self.db.query(func.avg(WorkstationStatus.efficiency_rate)).join(Workstation).filter(
            WorkstationStatus.efficiency_rate.isnot(None)
        )
        if workshop_id:
            avg_efficiency = avg_efficiency.filter(Workstation.workshop_id == workshop_id)
        efficiency = avg_efficiency.scalar() or Decimal('0')
        
        return RealtimeProgressOverview(
            total_work_orders=total,
            in_progress=in_progress,
            completed_today=completed_today,
            delayed=delayed,
            active_workstations=active_ws,
            idle_workstations=idle_ws,
            bottleneck_workstations=bottleneck_ws,
            active_alerts=active_alerts,
            critical_alerts=critical_alerts,
            overall_progress=Decimal(str(overall_progress)),
            overall_capacity_utilization=Decimal(str(overall_utilization)),
            efficiency_rate=Decimal(str(efficiency))
        )

    def get_work_order_timeline(self, work_order_id: int) -> Optional[WorkOrderProgressTimeline]:
        """获取工单进度时间线"""
        work_order = self.db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not work_order:
            return None
            
        # 获取进度日志
        logs = self.db.query(ProductionProgressLog).filter(
            ProductionProgressLog.work_order_id == work_order_id
        ).order_by(ProductionProgressLog.logged_at).all()
        
        # 获取预警
        alerts = self.db.query(ProgressAlert).filter(
            ProgressAlert.work_order_id == work_order_id
        ).order_by(desc(ProgressAlert.triggered_at)).all()
        
        return WorkOrderProgressTimeline(
            work_order_id=work_order.id,
            work_order_no=work_order.work_order_no,
            task_name=work_order.task_name,
            current_progress=work_order.progress,
            current_status=work_order.status,
            plan_start_date=work_order.plan_start_date,
            plan_end_date=work_order.plan_end_date,
            actual_start_time=work_order.actual_start_time,
            actual_end_time=work_order.actual_end_time,
            timeline=[log for log in logs],
            alerts=[alert for alert in alerts]
        )

    def get_workstation_realtime(self, workstation_id: int) -> Optional[WorkstationStatus]:
        """获取工位实时状态"""
        return self.db.query(WorkstationStatus).filter(
            WorkstationStatus.workstation_id == workstation_id
        ).first()

    def get_progress_deviations(
        self,
        workshop_id: Optional[int] = None,
        min_deviation: int = 10,
        only_delayed: bool = True
    ) -> List[ProgressDeviation]:
        """获取进度偏差列表"""
        query = self.db.query(WorkOrder).filter(
            WorkOrder.status.in_(['IN_PROGRESS', 'PENDING'])
        )
        
        if workshop_id:
            query = query.filter(WorkOrder.workshop_id == workshop_id)
            
        work_orders = query.all()
        
        deviations = []
        for wo in work_orders:
            plan_progress, deviation, is_delayed = self.calculate_progress_deviation(
                wo.id,
                wo.progress
            )
            
            if only_delayed and not is_delayed:
                continue
                
            if abs(deviation) < min_deviation:
                continue
                
            # 计算预计完成日期
            estimated_completion = None
            delay_days = None
            if wo.plan_end_date and wo.progress > 0:
                # 基于当前进度速率估算
                if wo.actual_start_time:
                    elapsed_days = (datetime.now() - wo.actual_start_time).days
                    if elapsed_days > 0 and wo.progress > 0:
                        daily_rate = wo.progress / elapsed_days
                        remaining_days = int((100 - wo.progress) / daily_rate)
                        estimated_completion = datetime.now() + timedelta(days=remaining_days)
                        delay_days = (estimated_completion.date() - wo.plan_end_date).days
                        
            # 确定风险等级
            risk_level = 'LOW'
            if deviation < -20:
                risk_level = 'CRITICAL'
            elif deviation < -15:
                risk_level = 'HIGH'
            elif deviation < -10:
                risk_level = 'MEDIUM'
                
            deviations.append(ProgressDeviation(
                work_order_id=wo.id,
                work_order_no=wo.work_order_no,
                task_name=wo.task_name,
                plan_progress=plan_progress,
                actual_progress=wo.progress,
                deviation=deviation,
                deviation_percentage=self.calculate_deviation_percentage(deviation, plan_progress),
                is_delayed=is_delayed,
                plan_end_date=wo.plan_end_date,
                estimated_completion_date=estimated_completion,
                delay_days=delay_days,
                risk_level=risk_level
            ))
            
        # 按偏差排序
        deviations.sort(key=lambda x: x.deviation)
        
        return deviations

    def dismiss_alert(self, alert_id: int, user_id: int, note: Optional[str] = None) -> bool:
        """关闭预警"""
        alert = self.db.query(ProgressAlert).filter(ProgressAlert.id == alert_id).first()
        if not alert:
            return False
            
        alert.status = 'DISMISSED'
        alert.dismissed_at = datetime.now()
        alert.dismissed_by = user_id
        if note:
            alert.resolution_note = note
            
        self.db.commit()
        return True

    def get_alerts(
        self,
        work_order_id: Optional[int] = None,
        workstation_id: Optional[int] = None,
        alert_type: Optional[str] = None,
        alert_level: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[ProgressAlert]:
        """获取预警列表"""
        query = self.db.query(ProgressAlert)
        
        if work_order_id:
            query = query.filter(ProgressAlert.work_order_id == work_order_id)
        if workstation_id:
            query = query.filter(ProgressAlert.workstation_id == workstation_id)
        if alert_type:
            query = query.filter(ProgressAlert.alert_type == alert_type)
        if alert_level:
            query = query.filter(ProgressAlert.alert_level == alert_level)
        if status:
            query = query.filter(ProgressAlert.status == status)
        else:
            # 默认只返回活跃预警
            query = query.filter(ProgressAlert.status == 'ACTIVE')
            
        return query.order_by(desc(ProgressAlert.triggered_at)).all()
