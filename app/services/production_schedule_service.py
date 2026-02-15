# -*- coding: utf-8 -*-
"""
生产排程优化服务
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.production import (
    Equipment,
    ProductionSchedule,
    ResourceConflict,
    ScheduleAdjustmentLog,
    Worker,
    WorkerSkill,
    WorkOrder,
)
from app.schemas.production_schedule import (
    ScheduleGenerateRequest,
    ScheduleScoreMetrics,
)

logger = logging.getLogger(__name__)


class ProductionScheduleService:
    """生产排程服务"""
    
    ALGORITHM_VERSION = "v1.0.0"
    
    # 工作时间配置
    WORK_START_HOUR = 8  # 08:00
    WORK_END_HOUR = 18   # 18:00
    WORK_HOURS_PER_DAY = 8
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 智能排程算法 ====================
    
    def generate_schedule(
        self,
        request: ScheduleGenerateRequest,
        user_id: int
    ) -> Tuple[int, List[ProductionSchedule], List[ResourceConflict]]:
        """
        生成智能排程
        
        Args:
            request: 排程请求
            user_id: 用户ID
            
        Returns:
            (plan_id, schedules, conflicts)
        """
        logger.info(f"开始生成排程，工单数量: {len(request.work_orders)}")
        
        # 1. 获取工单数据
        work_orders = self._fetch_work_orders(request.work_orders)
        if not work_orders:
            raise ValueError("未找到有效工单")
        
        # 2. 生成排程方案ID
        plan_id = self._generate_plan_id()
        
        # 3. 获取可用资源
        available_equipment = self._get_available_equipment()
        available_workers = self._get_available_workers()
        
        # 4. 执行排程算法
        if request.algorithm == "GREEDY":
            schedules = self._greedy_scheduling(
                work_orders,
                available_equipment,
                available_workers,
                request,
                plan_id,
                user_id
            )
        elif request.algorithm == "HEURISTIC":
            schedules = self._heuristic_scheduling(
                work_orders,
                available_equipment,
                available_workers,
                request,
                plan_id,
                user_id
            )
        else:
            # 默认使用贪心算法
            schedules = self._greedy_scheduling(
                work_orders,
                available_equipment,
                available_workers,
                request,
                plan_id,
                user_id
            )
        
        # 5. 检测资源冲突
        conflicts = self._detect_conflicts(schedules)
        
        # 6. 评分
        for schedule in schedules:
            schedule.score = self._calculate_schedule_score(schedule, work_orders)
        
        # 7. 保存到数据库
        self.db.add_all(schedules)
        if conflicts:
            self.db.add_all(conflicts)
        self.db.flush()
        
        logger.info(f"排程生成完成，成功: {len(schedules)}, 冲突: {len(conflicts)}")
        
        return plan_id, schedules, conflicts
    
    def _greedy_scheduling(
        self,
        work_orders: List[WorkOrder],
        equipment: List[Equipment],
        workers: List[Worker],
        request: ScheduleGenerateRequest,
        plan_id: int,
        user_id: int
    ) -> List[ProductionSchedule]:
        """
        贪心排程算法
        
        策略:
        1. 按优先级和交期排序工单
        2. 对每个工单选择最优资源(设备+工人)
        3. 安排在最早可用时间
        """
        schedules = []
        
        # 1. 工单排序: 优先级 > 交期 > 工单号
        sorted_orders = sorted(
            work_orders,
            key=lambda x: (
                self._get_priority_weight(x.priority),
                x.plan_end_date or datetime.max.date(),
                x.work_order_no
            )
        )
        
        # 2. 资源时间表 (记录每个资源的占用情况)
        equipment_timeline = {eq.id: [] for eq in equipment}
        worker_timeline = {w.id: [] for w in workers}
        
        # 3. 为每个工单分配资源和时间
        current_time = request.start_date
        
        for order in sorted_orders:
            # 获取工单所需时长
            duration_hours = float(order.standard_hours or 8)
            
            # 选择最优设备和工人
            best_equipment = self._select_best_equipment(
                order, equipment, equipment_timeline, request
            )
            best_worker = self._select_best_worker(
                order, workers, worker_timeline, request
            )
            
            # 计算最早开始时间
            earliest_start = self._find_earliest_available_slot(
                equipment_timeline.get(best_equipment.id if best_equipment else None, []),
                worker_timeline.get(best_worker.id if best_worker else None, []),
                current_time,
                duration_hours,
                request
            )
            
            # 计算结束时间(考虑工作时间)
            end_time = self._calculate_end_time(earliest_start, duration_hours, request)
            
            # 创建排程
            schedule = ProductionSchedule(
                work_order_id=order.id,
                schedule_plan_id=plan_id,
                equipment_id=best_equipment.id if best_equipment else None,
                worker_id=best_worker.id if best_worker else None,
                workshop_id=order.workshop_id,
                process_id=order.process_id,
                scheduled_start_time=earliest_start,
                scheduled_end_time=end_time,
                duration_hours=duration_hours,
                priority_score=self._calculate_priority_score(order),
                status='PENDING',
                algorithm_version=self.ALGORITHM_VERSION,
                created_by=user_id,
                sequence_no=len(schedules) + 1
            )
            
            schedules.append(schedule)
            
            # 更新资源时间表
            if best_equipment:
                equipment_timeline[best_equipment.id].append((earliest_start, end_time))
            if best_worker:
                worker_timeline[best_worker.id].append((earliest_start, end_time))
        
        return schedules
    
    def _heuristic_scheduling(
        self,
        work_orders: List[WorkOrder],
        equipment: List[Equipment],
        workers: List[Worker],
        request: ScheduleGenerateRequest,
        plan_id: int,
        user_id: int
    ) -> List[ProductionSchedule]:
        """
        启发式排程算法
        
        策略:
        1. 考虑多个因素的综合评分
        2. 动态调整排程策略
        3. 尝试优化总体目标
        """
        # 使用贪心算法作为基础，然后进行优化
        schedules = self._greedy_scheduling(
            work_orders, equipment, workers, request, plan_id, user_id
        )
        
        # 优化步骤:尝试交换排程以提高整体评分
        schedules = self._optimize_schedules(schedules, request)
        
        return schedules
    
    def _optimize_schedules(
        self,
        schedules: List[ProductionSchedule],
        request: ScheduleGenerateRequest
    ) -> List[ProductionSchedule]:
        """优化排程"""
        # 简单的交换优化
        improved = True
        iterations = 0
        max_iterations = 10
        
        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            
            for i in range(len(schedules) - 1):
                for j in range(i + 1, len(schedules)):
                    # 尝试交换时间
                    if self._should_swap_schedules(schedules[i], schedules[j]):
                        # 交换
                        schedules[i].scheduled_start_time, schedules[j].scheduled_start_time = \
                            schedules[j].scheduled_start_time, schedules[i].scheduled_start_time
                        schedules[i].scheduled_end_time, schedules[j].scheduled_end_time = \
                            schedules[j].scheduled_end_time, schedules[i].scheduled_end_time
                        improved = True
        
        return schedules
    
    def _should_swap_schedules(
        self,
        schedule1: ProductionSchedule,
        schedule2: ProductionSchedule
    ) -> bool:
        """判断是否应该交换两个排程"""
        # 如果高优先级的工单被排在后面，应该交换
        if schedule1.priority_score < schedule2.priority_score:
            if schedule1.scheduled_start_time < schedule2.scheduled_start_time:
                return True
        return False
    
    # ==================== 资源选择算法 ====================
    
    def _select_best_equipment(
        self,
        order: WorkOrder,
        equipment: List[Equipment],
        timeline: Dict[int, List],
        request: ScheduleGenerateRequest
    ) -> Optional[Equipment]:
        """选择最优设备"""
        if not equipment:
            return None
        
        # 如果工单指定了设备，直接返回
        if order.machine_id:
            return next((eq for eq in equipment if eq.id == order.machine_id), None)
        
        # 根据车间筛选
        candidates = [eq for eq in equipment if eq.workshop_id == order.workshop_id]
        if not candidates:
            candidates = equipment
        
        # 选择最空闲的设备
        best_eq = min(candidates, key=lambda eq: len(timeline.get(eq.id, [])))
        return best_eq
    
    def _select_best_worker(
        self,
        order: WorkOrder,
        workers: List[Worker],
        timeline: Dict[int, List],
        request: ScheduleGenerateRequest
    ) -> Optional[Worker]:
        """选择最优工人"""
        if not workers:
            return None
        
        # 如果工单指定了工人，直接返回
        if order.assigned_to:
            return next((w for w in workers if w.id == order.assigned_to), None)
        
        # 根据车间和技能筛选
        candidates = []
        
        if request.consider_worker_skills and order.process_id:
            # 查询具有该工序技能的工人
            skilled_worker_ids = self.db.query(WorkerSkill.worker_id).filter(
                WorkerSkill.process_id == order.process_id
            ).all()
            skilled_ids = [w[0] for w in skilled_worker_ids]
            candidates = [w for w in workers if w.id in skilled_ids and w.workshop_id == order.workshop_id]
        
        if not candidates:
            candidates = [w for w in workers if w.workshop_id == order.workshop_id]
        
        if not candidates:
            candidates = workers
        
        # 选择最空闲的工人
        best_worker = min(candidates, key=lambda w: len(timeline.get(w.id, [])))
        return best_worker
    
    # ==================== 时间计算 ====================
    
    def _find_earliest_available_slot(
        self,
        equipment_slots: List[Tuple[datetime, datetime]],
        worker_slots: List[Tuple[datetime, datetime]],
        start_from: datetime,
        duration_hours: float,
        request: ScheduleGenerateRequest
    ) -> datetime:
        """找到最早可用时间槽"""
        current = start_from
        
        # 调整到工作时间开始
        current = self._adjust_to_work_time(current, request)
        
        max_attempts = 100
        attempts = 0
        
        while attempts < max_attempts:
            end = self._calculate_end_time(current, duration_hours, request)
            
            # 检查是否与已有排程冲突
            has_conflict = False
            
            for slot_start, slot_end in equipment_slots:
                if self._time_overlap(current, end, slot_start, slot_end):
                    has_conflict = True
                    current = slot_end
                    break
            
            if not has_conflict:
                for slot_start, slot_end in worker_slots:
                    if self._time_overlap(current, end, slot_start, slot_end):
                        has_conflict = True
                        current = slot_end
                        break
            
            if not has_conflict:
                return current
            
            current = self._adjust_to_work_time(current, request)
            attempts += 1
        
        return current
    
    def _calculate_end_time(
        self,
        start_time: datetime,
        duration_hours: float,
        request: ScheduleGenerateRequest
    ) -> datetime:
        """计算结束时间(考虑工作时间和非工作时段)"""
        remaining_hours = duration_hours
        current = start_time
        
        while remaining_hours > 0:
            # 获取当天剩余工作时间
            work_end = current.replace(hour=self.WORK_END_HOUR, minute=0, second=0)
            if current >= work_end:
                # 已经下班，跳到第二天上班
                current = (current + timedelta(days=1)).replace(
                    hour=self.WORK_START_HOUR, minute=0, second=0
                )
                continue
            
            hours_until_end_of_day = (work_end - current).total_seconds() / 3600
            
            if remaining_hours <= hours_until_end_of_day:
                # 可以在今天完成
                current = current + timedelta(hours=remaining_hours)
                remaining_hours = 0
            else:
                # 需要跨天
                remaining_hours -= hours_until_end_of_day
                current = (current + timedelta(days=1)).replace(
                    hour=self.WORK_START_HOUR, minute=0, second=0
                )
        
        return current
    
    def _adjust_to_work_time(self, dt: datetime, request: ScheduleGenerateRequest) -> datetime:
        """调整到工作时间"""
        # 检查是否在工作时间内
        if dt.hour < self.WORK_START_HOUR:
            return dt.replace(hour=self.WORK_START_HOUR, minute=0, second=0)
        elif dt.hour >= self.WORK_END_HOUR:
            return (dt + timedelta(days=1)).replace(hour=self.WORK_START_HOUR, minute=0, second=0)
        return dt
    
    def _time_overlap(
        self,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime
    ) -> bool:
        """检查时间段是否重叠"""
        return start1 < end2 and end1 > start2
    
    # ==================== 冲突检测 ====================
    
    def _detect_conflicts(
        self,
        schedules: List[ProductionSchedule]
    ) -> List[ResourceConflict]:
        """检测资源冲突"""
        conflicts = []
        detected_at = datetime.now()
        
        # 检查设备冲突
        for i, schedule1 in enumerate(schedules):
            for schedule2 in schedules[i+1:]:
                # 设备冲突
                if (schedule1.equipment_id and
                    schedule1.equipment_id == schedule2.equipment_id and
                    self._time_overlap(
                        schedule1.scheduled_start_time,
                        schedule1.scheduled_end_time,
                        schedule2.scheduled_start_time,
                        schedule2.scheduled_end_time
                    )):
                    conflict = ResourceConflict(
                        schedule_id=schedule1.id,
                        conflicting_schedule_id=schedule2.id,
                        conflict_type='EQUIPMENT',
                        resource_type='equipment',
                        resource_id=schedule1.equipment_id,
                        conflict_description=f'设备 {schedule1.equipment_id} 时间冲突',
                        severity='HIGH',
                        conflict_start_time=max(schedule1.scheduled_start_time, schedule2.scheduled_start_time),
                        conflict_end_time=min(schedule1.scheduled_end_time, schedule2.scheduled_end_time),
                        status='UNRESOLVED',
                        detected_at=detected_at,
                        detected_by='AUTO'
                    )
                    conflicts.append(conflict)
                
                # 工人冲突
                if (schedule1.worker_id and
                    schedule1.worker_id == schedule2.worker_id and
                    self._time_overlap(
                        schedule1.scheduled_start_time,
                        schedule1.scheduled_end_time,
                        schedule2.scheduled_start_time,
                        schedule2.scheduled_end_time
                    )):
                    conflict = ResourceConflict(
                        schedule_id=schedule1.id,
                        conflicting_schedule_id=schedule2.id,
                        conflict_type='WORKER',
                        resource_type='worker',
                        resource_id=schedule1.worker_id,
                        conflict_description=f'工人 {schedule1.worker_id} 时间冲突',
                        severity='MEDIUM',
                        conflict_start_time=max(schedule1.scheduled_start_time, schedule2.scheduled_start_time),
                        conflict_end_time=min(schedule1.scheduled_end_time, schedule2.scheduled_end_time),
                        status='UNRESOLVED',
                        detected_at=detected_at,
                        detected_by='AUTO'
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    # ==================== 评分算法 ====================
    
    def _calculate_priority_score(self, order: WorkOrder) -> float:
        """计算优先级评分"""
        priority_map = {
            'LOW': 1.0,
            'NORMAL': 2.0,
            'HIGH': 3.0,
            'URGENT': 5.0
        }
        return priority_map.get(order.priority, 2.0)
    
    def _get_priority_weight(self, priority: str) -> int:
        """获取优先级权重(用于排序)"""
        priority_map = {
            'URGENT': 1,
            'HIGH': 2,
            'NORMAL': 3,
            'LOW': 4
        }
        return priority_map.get(priority, 3)
    
    def _calculate_schedule_score(
        self,
        schedule: ProductionSchedule,
        work_orders: List[WorkOrder]
    ) -> float:
        """计算单个排程的评分"""
        # 简化评分:考虑优先级满足度和时间延迟
        order = next((wo for wo in work_orders if wo.id == schedule.work_order_id), None)
        if not order:
            return 0.0
        
        score = schedule.priority_score * 10
        
        # 如果在计划日期内，加分
        if order.plan_end_date and schedule.scheduled_end_time.date() <= order.plan_end_date:
            score += 20
        
        return min(score, 100)
    
    def calculate_overall_metrics(
        self,
        schedules: List[ProductionSchedule],
        work_orders: List[WorkOrder]
    ) -> ScheduleScoreMetrics:
        """计算排程方案的整体评估指标"""
        if not schedules:
            return ScheduleScoreMetrics(
                completion_rate=0,
                equipment_utilization=0,
                worker_utilization=0,
                total_duration_hours=0,
                average_waiting_time=0,
                skill_match_rate=0,
                priority_satisfaction=0,
                conflict_count=0
            )
        
        # 交期达成率
        on_time_count = 0
        for schedule in schedules:
            order = next((wo for wo in work_orders if wo.id == schedule.work_order_id), None)
            if order and order.plan_end_date:
                if schedule.scheduled_end_time.date() <= order.plan_end_date:
                    on_time_count += 1
        completion_rate = on_time_count / len(schedules) if schedules else 0
        
        # 设备利用率(简化计算)
        equipment_ids = set(s.equipment_id for s in schedules if s.equipment_id)
        total_work_hours = sum(s.duration_hours for s in schedules)
        total_available_hours = len(equipment_ids) * self.WORK_HOURS_PER_DAY * 10  # 假设10天
        equipment_utilization = min(total_work_hours / total_available_hours, 1.0) if total_available_hours > 0 else 0
        
        # 工人利用率
        worker_ids = set(s.worker_id for s in schedules if s.worker_id)
        worker_utilization = min(total_work_hours / (len(worker_ids) * self.WORK_HOURS_PER_DAY * 10), 1.0) if worker_ids else 0
        
        # 总时长
        if schedules:
            min_start = min(s.scheduled_start_time for s in schedules)
            max_end = max(s.scheduled_end_time for s in schedules)
            total_duration = (max_end - min_start).total_seconds() / 3600
        else:
            total_duration = 0
        
        # 技能匹配率(简化)
        skill_match_rate = 0.85  # 假设85%匹配
        
        # 优先级满足度
        priority_satisfaction = completion_rate  # 简化为与交期达成率相同
        
        # 冲突数量
        conflicts = self._detect_conflicts(schedules)
        conflict_count = len(conflicts)
        
        return ScheduleScoreMetrics(
            completion_rate=completion_rate,
            equipment_utilization=equipment_utilization,
            worker_utilization=worker_utilization,
            total_duration_hours=total_duration,
            average_waiting_time=0,
            skill_match_rate=skill_match_rate,
            priority_satisfaction=priority_satisfaction,
            conflict_count=conflict_count
        )
    
    # ==================== 辅助方法 ====================
    
    def _fetch_work_orders(self, work_order_ids: List[int]) -> List[WorkOrder]:
        """获取工单列表"""
        return self.db.query(WorkOrder).filter(WorkOrder.id.in_(work_order_ids)).all()
    
    def _get_available_equipment(self) -> List[Equipment]:
        """获取可用设备"""
        return self.db.query(Equipment).filter(
            Equipment.is_active == True,
            Equipment.status.in_(['IDLE', 'RUNNING'])
        ).all()
    
    def _get_available_workers(self) -> List[Worker]:
        """获取可用工人"""
        return self.db.query(Worker).filter(
            Worker.is_active == True,
            Worker.status == 'ACTIVE'
        ).all()
    
    def _generate_plan_id(self) -> int:
        """生成排程方案ID"""
        # 使用时间戳
        return int(datetime.now().timestamp())
    
    # ==================== 紧急插单 ====================
    
    def urgent_insert(
        self,
        work_order_id: int,
        insert_time: datetime,
        max_delay_hours: float,
        auto_adjust: bool,
        user_id: int
    ) -> Tuple[Optional[ProductionSchedule], List[ProductionSchedule], List[ResourceConflict]]:
        """
        紧急插单
        
        Returns:
            (new_schedule, adjusted_schedules, conflicts)
        """
        # 获取工单
        order = self.db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not order:
            raise ValueError("工单不存在")
        
        duration_hours = float(order.standard_hours or 8)
        
        # 查找可用资源
        equipment = self._get_available_equipment()
        workers = self._get_available_workers()
        
        # 选择资源
        best_equipment = self._select_best_equipment(order, equipment, {}, ScheduleGenerateRequest(
            work_orders=[work_order_id],
            start_date=insert_time,
            end_date=insert_time + timedelta(days=7),
            consider_worker_skills=True,
            consider_equipment_capacity=True
        ))
        best_worker = self._select_best_worker(order, workers, {}, ScheduleGenerateRequest(
            work_orders=[work_order_id],
            start_date=insert_time,
            end_date=insert_time + timedelta(days=7),
            consider_worker_skills=True,
            consider_equipment_capacity=True
        ))
        
        end_time = self._calculate_end_time(insert_time, duration_hours, ScheduleGenerateRequest(
            work_orders=[work_order_id],
            start_date=insert_time,
            end_date=insert_time + timedelta(days=7)
        ))
        
        # 创建新排程
        new_schedule = ProductionSchedule(
            work_order_id=work_order_id,
            equipment_id=best_equipment.id if best_equipment else None,
            worker_id=best_worker.id if best_worker else None,
            workshop_id=order.workshop_id,
            process_id=order.process_id,
            scheduled_start_time=insert_time,
            scheduled_end_time=end_time,
            duration_hours=duration_hours,
            priority_score=5.0,  # 紧急优先级最高
            status='PENDING',
            is_urgent=True,
            algorithm_version=self.ALGORITHM_VERSION,
            created_by=user_id
        )
        
        adjusted_schedules = []
        conflicts = []
        
        if auto_adjust:
            # 查找冲突的排程
            conflicting = self.db.query(ProductionSchedule).filter(
                and_(
                    or_(
                        ProductionSchedule.equipment_id == new_schedule.equipment_id,
                        ProductionSchedule.worker_id == new_schedule.worker_id
                    ),
                    ProductionSchedule.scheduled_start_time < end_time,
                    ProductionSchedule.scheduled_end_time > insert_time,
                    ProductionSchedule.status.in_(['PENDING', 'CONFIRMED'])
                )
            ).all()
            
            # 延后冲突的排程
            for conf_schedule in conflicting:
                delay = (end_time - conf_schedule.scheduled_start_time).total_seconds() / 3600
                if delay <= max_delay_hours:
                    conf_schedule.scheduled_start_time = end_time
                    conf_schedule.scheduled_end_time = self._calculate_end_time(
                        end_time,
                        conf_schedule.duration_hours,
                        ScheduleGenerateRequest(
                            work_orders=[],
                            start_date=end_time,
                            end_date=end_time + timedelta(days=7)
                        )
                    )
                    adjusted_schedules.append(conf_schedule)
        
        return new_schedule, adjusted_schedules, conflicts
