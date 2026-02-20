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
    ProductionResourceConflict,
    ScheduleAdjustmentLog,
    Worker,
    WorkerSkill,
    WorkOrder,
)
from app.schemas.production_schedule import (
    GanttTask,
    ScheduleAdjustRequest,
    ScheduleGenerateRequest,
    ScheduleResponse,
    ScheduleScoreMetrics,
    ConflictResponse,
)
from app.common.query_filters import apply_pagination

logger = logging.getLogger(__name__)


class ProductionScheduleService:
    """生产排程服务"""

    ALGORITHM_VERSION = "v1.0.0"

    # 工作时间配置
    WORK_START_HOUR = 8  # 08:00
    WORK_END_HOUR = 18   # 18:00
    WORK_HOURS_PER_DAY = 8

    # 甘特图状态颜色映射
    GANTT_COLOR_MAP = {
        'PENDING': '#9E9E9E',
        'CONFIRMED': '#2196F3',
        'IN_PROGRESS': '#FF9800',
        'COMPLETED': '#4CAF50',
        'CANCELLED': '#F44336',
    }

    def __init__(self, db: Session):
        self.db = db

    # ==================== 智能排程算法 ====================

    def generate_schedule(
        self,
        request: ScheduleGenerateRequest,
        user_id: int
    ) -> Tuple[int, List[ProductionSchedule], List[ProductionResourceConflict]]:
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

    def generate_and_evaluate_schedule(
        self,
        request: ScheduleGenerateRequest,
        user_id: int
    ) -> Dict[str, Any]:
        """
        生成排程并执行评估，返回完整的响应数据

        包含排程生成、计时、指标计算和警告生成。

        Args:
            request: 排程请求
            user_id: 用户ID

        Returns:
            包含 plan_id, schedules, metrics, warnings 等的完整结果字典
        """
        start_time = datetime.now()

        # 生成排程
        plan_id, schedules, conflicts = self.generate_schedule(request, user_id)

        elapsed_time = (datetime.now() - start_time).total_seconds()

        # 获取工单信息
        work_orders = self._fetch_work_orders(request.work_orders)

        # 计算评估指标
        metrics = self.calculate_overall_metrics(schedules, work_orders)
        overall_score = metrics.calculate_overall_score()

        # 生成警告信息
        warnings = []
        if conflicts:
            warnings.append(f"检测到 {len(conflicts)} 个资源冲突")
        if metrics.completion_rate < 0.8:
            warnings.append(f"交期达成率较低: {metrics.completion_rate:.1%}")
        if elapsed_time > 5:
            warnings.append(f"排程耗时较长: {elapsed_time:.2f}秒")

        # 提交事务
        self.db.commit()

        # 转换响应
        schedule_responses = [ScheduleResponse.model_validate(s) for s in schedules]

        return {
            "plan_id": plan_id,
            "schedules": schedule_responses,
            "total_count": len(request.work_orders),
            "success_count": len(schedules),
            "failed_count": len(request.work_orders) - len(schedules),
            "conflicts_count": len(conflicts),
            "score": overall_score,
            "metrics": {
                "completion_rate": metrics.completion_rate,
                "equipment_utilization": metrics.equipment_utilization,
                "worker_utilization": metrics.worker_utilization,
                "total_duration_hours": metrics.total_duration_hours,
                "skill_match_rate": metrics.skill_match_rate,
                "elapsed_time_seconds": elapsed_time,
            },
            "warnings": warnings,
        }

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
    ) -> List[ProductionResourceConflict]:
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
                    conflict = ProductionResourceConflict(
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
                    conflict = ProductionResourceConflict(
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
    ) -> Tuple[Optional[ProductionSchedule], List[ProductionSchedule], List[ProductionResourceConflict]]:
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

    def execute_urgent_insert_with_logging(
        self,
        work_order_id: int,
        insert_time: datetime,
        max_delay_hours: float,
        auto_adjust: bool,
        user_id: int
    ) -> Dict[str, Any]:
        """
        紧急插单并创建调整日志，返回完整的响应数据

        Args:
            work_order_id: 工单ID
            insert_time: 期望插入时间
            max_delay_hours: 最大允许延迟小时数
            auto_adjust: 是否自动调整其他排程
            user_id: 用户ID

        Returns:
            包含 schedule, adjusted_schedules, conflicts, message 的字典
        """
        new_schedule, adjusted_schedules, conflicts = self.urgent_insert(
            work_order_id=work_order_id,
            insert_time=insert_time,
            max_delay_hours=max_delay_hours,
            auto_adjust=auto_adjust,
            user_id=user_id
        )

        # 保存
        self.db.add(new_schedule)
        if adjusted_schedules:
            self.db.add_all(adjusted_schedules)
        if conflicts:
            self.db.add_all(conflicts)

        # 创建调整日志
        for adj_schedule in adjusted_schedules:
            log = ScheduleAdjustmentLog(
                schedule_id=adj_schedule.id,
                adjustment_type='TIME_CHANGE',
                trigger_source='URGENT_ORDER',
                reason=f"紧急插单导致延后: 工单 {work_order_id}",
                adjusted_by=user_id,
                adjusted_at=datetime.now()
            )
            self.db.add(log)

        self.db.commit()

        schedule_response = ScheduleResponse.model_validate(new_schedule) if new_schedule else None
        adjusted_responses = [ScheduleResponse.model_validate(s) for s in adjusted_schedules]
        conflict_dicts = [{"type": c.conflict_type, "severity": c.severity} for c in conflicts]

        return {
            "success": True,
            "schedule": schedule_response,
            "adjusted_schedules": adjusted_responses,
            "conflicts": conflict_dicts,
            "message": f"紧急插单成功，调整了 {len(adjusted_schedules)} 个排程",
        }

    # ==================== 排程预览 ====================

    def get_schedule_preview(self, plan_id: int) -> Dict[str, Any]:
        """
        排程预览，包含统计、冲突数量和优化建议

        Args:
            plan_id: 排程方案ID

        Returns:
            包含 schedules, statistics, conflicts, warnings, optimization_suggestions 的字典

        Raises:
            ValueError: 排程方案不存在时
        """
        # 获取排程列表
        schedules = self.db.query(ProductionSchedule).filter(
            ProductionSchedule.schedule_plan_id == plan_id
        ).all()

        if not schedules:
            raise ValueError("排程方案不存在")

        # 获取冲突
        schedule_ids = [s.id for s in schedules]
        conflicts = self.db.query(ProductionResourceConflict).filter(
            ProductionResourceConflict.schedule_id.in_(schedule_ids),
            ProductionResourceConflict.status == 'UNRESOLVED'
        ).all()

        # 统计信息
        work_order_ids = [s.work_order_id for s in schedules]
        work_orders = self._fetch_work_orders(work_order_ids)
        metrics = self.calculate_overall_metrics(schedules, work_orders)

        statistics = {
            "total_schedules": len(schedules),
            "pending": sum(1 for s in schedules if s.status == 'PENDING'),
            "confirmed": sum(1 for s in schedules if s.status == 'CONFIRMED'),
            "in_progress": sum(1 for s in schedules if s.status == 'IN_PROGRESS'),
            "completed": sum(1 for s in schedules if s.status == 'COMPLETED'),
            "total_duration_hours": metrics.total_duration_hours,
            "completion_rate": metrics.completion_rate,
            "equipment_utilization": metrics.equipment_utilization,
        }

        # 优化建议
        optimization_suggestions = []
        if conflicts:
            optimization_suggestions.append("建议解决资源冲突后再确认排程")
        if metrics.completion_rate < 0.8:
            optimization_suggestions.append("部分工单可能延期，建议调整优先级或增加资源")
        if metrics.equipment_utilization < 0.6:
            optimization_suggestions.append("设备利用率较低，可以考虑安排更多工单")

        schedule_responses = [ScheduleResponse.model_validate(s) for s in schedules]
        conflict_responses = [ConflictResponse.model_validate(c) for c in conflicts]

        warnings = []
        if conflicts:
            warnings.append(f"存在 {len(conflicts)} 个未解决的冲突")

        return {
            "plan_id": plan_id,
            "schedules": schedule_responses,
            "statistics": statistics,
            "conflicts": conflict_responses,
            "warnings": warnings,
            "is_optimizable": len(optimization_suggestions) > 0,
            "optimization_suggestions": optimization_suggestions,
        }

    # ==================== 确认排程 ====================

    def confirm_schedule(self, plan_id: int, user_id: int) -> Dict[str, Any]:
        """
        确认排程，校验冲突后更新状态

        Args:
            plan_id: 排程方案ID
            user_id: 用户ID

        Returns:
            包含 success, message, plan_id, confirmed_count, confirmed_at 的字典

        Raises:
            ValueError: 没有待确认的排程
            RuntimeError: 存在高优先级未解决冲突
        """
        # 获取排程
        schedules = self.db.query(ProductionSchedule).filter(
            ProductionSchedule.schedule_plan_id == plan_id,
            ProductionSchedule.status == 'PENDING'
        ).all()

        if not schedules:
            raise ValueError("没有待确认的排程")

        # 检查是否有未解决的冲突
        schedule_ids = [s.id for s in schedules]
        unresolved_conflicts = self.db.query(ProductionResourceConflict).filter(
            ProductionResourceConflict.schedule_id.in_(schedule_ids),
            ProductionResourceConflict.status == 'UNRESOLVED',
            ProductionResourceConflict.severity.in_(['HIGH', 'CRITICAL'])
        ).count()

        if unresolved_conflicts > 0:
            raise RuntimeError(
                f"存在 {unresolved_conflicts} 个高优先级冲突，请先解决后再确认"
            )

        # 更新状态
        confirmed_at = datetime.now()
        for schedule in schedules:
            schedule.status = 'CONFIRMED'
            schedule.confirmed_by = user_id
            schedule.confirmed_at = confirmed_at

        self.db.commit()

        return {
            "success": True,
            "message": f"已确认 {len(schedules)} 个排程",
            "plan_id": plan_id,
            "confirmed_count": len(schedules),
            "confirmed_at": confirmed_at,
        }

    # ==================== 冲突摘要 ====================

    def get_conflict_summary(
        self,
        plan_id: Optional[int] = None,
        schedule_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        按类型和严重程度汇总冲突

        Args:
            plan_id: 排程方案ID（可选）
            schedule_id: 排程ID（可选）
            status: 冲突状态过滤（可选）

        Returns:
            包含 has_conflicts, total_conflicts, conflicts_by_type,
            conflicts, severity_summary 的字典
        """
        query = self.db.query(ProductionResourceConflict)

        if plan_id:
            # 获取该方案的所有排程ID
            schedule_ids = self.db.query(ProductionSchedule.id).filter(
                ProductionSchedule.schedule_plan_id == plan_id
            ).all()
            schedule_ids = [sid[0] for sid in schedule_ids]
            query = query.filter(ProductionResourceConflict.schedule_id.in_(schedule_ids))

        if schedule_id:
            query = query.filter(ProductionResourceConflict.schedule_id == schedule_id)

        if status:
            query = query.filter(ProductionResourceConflict.status == status)

        conflicts = query.all()

        # 按类型分组统计
        conflicts_by_type: Dict[str, int] = {}
        for conflict in conflicts:
            conflict_type = conflict.conflict_type
            conflicts_by_type[conflict_type] = conflicts_by_type.get(conflict_type, 0) + 1

        # 按严重程度统计
        severity_summary: Dict[str, int] = {}
        for conflict in conflicts:
            severity = conflict.severity
            severity_summary[severity] = severity_summary.get(severity, 0) + 1

        conflict_responses = [ConflictResponse.model_validate(c) for c in conflicts]

        return {
            "has_conflicts": len(conflicts) > 0,
            "total_conflicts": len(conflicts),
            "conflicts_by_type": conflicts_by_type,
            "conflicts": conflict_responses,
            "severity_summary": severity_summary,
        }

    # ==================== 排程调整 ====================

    def adjust_schedule(
        self,
        request: ScheduleAdjustRequest,
        user_id: int
    ) -> Dict[str, Any]:
        """
        手动调整排程，包含变更追踪和日志

        Args:
            request: 调整请求
            user_id: 用户ID

        Returns:
            包含 success, message, schedule_id, changes, adjustment_log_id 的字典

        Raises:
            ValueError: 排程不存在
        """
        # 获取排程
        schedule = self.db.query(ProductionSchedule).filter(
            ProductionSchedule.id == request.schedule_id
        ).first()
        if not schedule:
            raise ValueError("排程不存在")

        # 记录调整前的数据
        before_data = {
            "scheduled_start_time": schedule.scheduled_start_time.isoformat() if schedule.scheduled_start_time else None,
            "scheduled_end_time": schedule.scheduled_end_time.isoformat() if schedule.scheduled_end_time else None,
            "equipment_id": schedule.equipment_id,
            "worker_id": schedule.worker_id,
        }

        # 应用调整
        changes = []
        if request.new_start_time:
            schedule.scheduled_start_time = request.new_start_time
            changes.append("开始时间")
        if request.new_end_time:
            schedule.scheduled_end_time = request.new_end_time
            changes.append("结束时间")
        if request.new_equipment_id is not None:
            schedule.equipment_id = request.new_equipment_id
            changes.append("设备")
        if request.new_worker_id is not None:
            schedule.worker_id = request.new_worker_id
            changes.append("工人")

        schedule.is_manually_adjusted = True
        schedule.adjustment_reason = request.reason
        schedule.adjusted_by = user_id
        schedule.adjusted_at = datetime.now()

        # 记录调整后的数据
        after_data = {
            "scheduled_start_time": schedule.scheduled_start_time.isoformat() if schedule.scheduled_start_time else None,
            "scheduled_end_time": schedule.scheduled_end_time.isoformat() if schedule.scheduled_end_time else None,
            "equipment_id": schedule.equipment_id,
            "worker_id": schedule.worker_id,
        }

        # 创建调整日志
        adjustment_log = ScheduleAdjustmentLog(
            schedule_id=schedule.id,
            schedule_plan_id=schedule.schedule_plan_id,
            adjustment_type=request.adjustment_type,
            trigger_source='MANUAL',
            before_data=before_data,
            after_data=after_data,
            changes_summary=f"调整了: {', '.join(changes)}",
            reason=request.reason,
            adjusted_by=user_id,
            adjusted_at=datetime.now()
        )

        self.db.add(adjustment_log)

        # 如果需要自动解决冲突
        if request.auto_resolve_conflicts:
            conflicts = self._detect_conflicts([schedule])
            if conflicts:
                self.db.add_all(conflicts)

        self.db.commit()

        return {
            "success": True,
            "message": "排程调整成功",
            "schedule_id": schedule.id,
            "changes": changes,
            "adjustment_log_id": adjustment_log.id,
        }

    # ==================== 方案对比 ====================

    def compare_schedule_plans(self, plan_ids: List[int]) -> Dict[str, Any]:
        """
        排程方案对比，含排名

        Args:
            plan_ids: 方案ID列表（2-5个）

        Returns:
            包含 comparison_time, plans_compared, results,
            best_plan_id, comparison_summary 的字典

        Raises:
            ValueError: 方案数量不合法
        """
        if len(plan_ids) < 2:
            raise ValueError("至少需要2个方案进行对比")
        if len(plan_ids) > 5:
            raise ValueError("最多支持5个方案对比")

        results = []

        for plan_id in plan_ids:
            schedules = self.db.query(ProductionSchedule).filter(
                ProductionSchedule.schedule_plan_id == plan_id
            ).all()

            if not schedules:
                continue

            # 获取工单
            work_order_ids = [s.work_order_id for s in schedules]
            work_orders = self._fetch_work_orders(work_order_ids)

            # 计算指标
            metrics = self.calculate_overall_metrics(schedules, work_orders)
            overall_score = metrics.calculate_overall_score()

            results.append({
                "plan_id": plan_id,
                "plan_name": f"方案 {plan_id}",
                "metrics": {
                    "overall_score": overall_score,
                    "completion_rate": metrics.completion_rate,
                    "equipment_utilization": metrics.equipment_utilization,
                    "worker_utilization": metrics.worker_utilization,
                    "total_duration_hours": metrics.total_duration_hours,
                    "conflict_count": metrics.conflict_count,
                },
                "rank": 0,
                "recommendation": None,
            })

        # 排序
        results.sort(key=lambda x: x["metrics"]["overall_score"], reverse=True)
        for i, result in enumerate(results):
            result["rank"] = i + 1
            if i == 0:
                result["recommendation"] = "推荐方案：综合评分最高"

        best_plan_id = results[0]["plan_id"] if results else 0

        return {
            "comparison_time": datetime.now(),
            "plans_compared": len(results),
            "results": results,
            "best_plan_id": best_plan_id,
            "comparison_summary": {
                "total_plans": len(results),
                "best_plan": best_plan_id,
                "score_range": {
                    "min": min(r["metrics"]["overall_score"] for r in results) if results else 0,
                    "max": max(r["metrics"]["overall_score"] for r in results) if results else 0,
                },
            },
        }

    # ==================== 甘特图数据 ====================

    def generate_gantt_data(self, plan_id: int) -> Dict[str, Any]:
        """
        生成甘特图数据

        Args:
            plan_id: 排程方案ID

        Returns:
            包含 tasks, total_tasks, start_date, end_date,
            resources, milestones 的字典

        Raises:
            ValueError: 排程方案不存在
        """
        schedules = self.db.query(ProductionSchedule).filter(
            ProductionSchedule.schedule_plan_id == plan_id
        ).all()

        if not schedules:
            raise ValueError("排程方案不存在")

        # 获取关联的工单
        work_order_ids = [s.work_order_id for s in schedules]
        work_orders_dict = {
            wo.id: wo for wo in self.db.query(WorkOrder).filter(
                WorkOrder.id.in_(work_order_ids)
            ).all()
        }

        # 构建甘特图任务
        tasks = []
        for schedule in schedules:
            work_order = work_orders_dict.get(schedule.work_order_id)
            if not work_order:
                continue

            task = GanttTask(
                id=schedule.id,
                name=work_order.task_name,
                work_order_no=work_order.work_order_no,
                start=schedule.scheduled_start_time,
                end=schedule.scheduled_end_time,
                duration=schedule.duration_hours,
                progress=work_order.progress / 100 if work_order.progress else 0,
                resource=f"设备{schedule.equipment_id}" if schedule.equipment_id else None,
                equipment=f"设备{schedule.equipment_id}" if schedule.equipment_id else None,
                worker=f"工人{schedule.worker_id}" if schedule.worker_id else None,
                status=schedule.status,
                priority=work_order.priority,
                dependencies=[],
                color=self.GANTT_COLOR_MAP.get(schedule.status, '#9E9E9E')
            )
            tasks.append(task)

        # 计算时间范围
        start_date = min(s.scheduled_start_time for s in schedules)
        end_date = max(s.scheduled_end_time for s in schedules)

        # 资源列表
        equipment_ids = set(s.equipment_id for s in schedules if s.equipment_id)
        worker_ids = set(s.worker_id for s in schedules if s.worker_id)

        resources = []
        for eq_id in equipment_ids:
            resources.append({"type": "equipment", "id": eq_id, "name": f"设备{eq_id}"})
        for w_id in worker_ids:
            resources.append({"type": "worker", "id": w_id, "name": f"工人{w_id}"})

        return {
            "tasks": tasks,
            "total_tasks": len(tasks),
            "start_date": start_date,
            "end_date": end_date,
            "resources": resources,
            "milestones": [],
        }

    # ==================== 重置排程 ====================

    def reset_schedule_plan(self, plan_id: int) -> Dict[str, Any]:
        """
        重置排程方案，删除排程、冲突和日志

        Args:
            plan_id: 排程方案ID

        Returns:
            包含 success, message, deleted_count 的字典
        """
        # 获取排程ID列表（在删除前获取，用于删除冲突）
        schedule_ids = self.db.query(ProductionSchedule.id).filter(
            ProductionSchedule.schedule_plan_id == plan_id
        ).all()
        schedule_id_list = [sid[0] for sid in schedule_ids]

        # 删除相关冲突记录
        if schedule_id_list:
            self.db.query(ProductionResourceConflict).filter(
                ProductionResourceConflict.schedule_id.in_(schedule_id_list)
            ).delete(synchronize_session=False)

        # 删除调整日志
        self.db.query(ScheduleAdjustmentLog).filter(
            ScheduleAdjustmentLog.schedule_plan_id == plan_id
        ).delete()

        # 删除排程
        deleted_count = self.db.query(ProductionSchedule).filter(
            ProductionSchedule.schedule_plan_id == plan_id
        ).delete()

        self.db.commit()

        return {
            "success": True,
            "message": f"已重置方案 {plan_id}",
            "deleted_count": deleted_count,
        }

    # ==================== 排程历史 ====================

    def get_schedule_history(
        self,
        schedule_id: Optional[int] = None,
        plan_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        查询排程调整历史，带分页

        Args:
            schedule_id: 排程ID（可选）
            plan_id: 方案ID（可选）
            page: 页码
            page_size: 每页条数

        Returns:
            包含 schedules, adjustments, total_count, page, page_size 的字典
        """
        # 查询调整日志
        query = self.db.query(ScheduleAdjustmentLog)

        if schedule_id:
            query = query.filter(ScheduleAdjustmentLog.schedule_id == schedule_id)

        if plan_id:
            query = query.filter(ScheduleAdjustmentLog.schedule_plan_id == plan_id)

        total_count = query.count()

        # 排序
        query = query.order_by(ScheduleAdjustmentLog.adjusted_at.desc())

        # 分页（使用通用工具）
        offset = (page - 1) * page_size
        query = apply_pagination(query, offset, page_size)

        adjustments = query.all()

        # 获取关联的排程
        related_schedule_ids = list(set(a.schedule_id for a in adjustments))
        schedules = []
        if related_schedule_ids:
            schedules = self.db.query(ProductionSchedule).filter(
                ProductionSchedule.id.in_(related_schedule_ids)
            ).all()

        return {
            "schedules": schedules,
            "adjustments": adjustments,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
        }
