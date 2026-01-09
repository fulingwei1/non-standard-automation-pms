# -*- coding: utf-8 -*-
"""
资源分配服务
实现工位可用性检查、人员可用性检查、资源冲突检测
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models import (
    Project, Machine, Workstation, Worker, WorkOrder,
    Task, PmoResourceAllocation
)


class ResourceAllocationService:
    """资源分配服务"""
    
    @classmethod
    def check_workstation_availability(
        cls,
        db: Session,
        workstation_id: int,
        start_date: date,
        end_date: date,
        exclude_work_order_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        检查工位可用性
        
        Args:
            db: 数据库会话
            workstation_id: 工位ID
            start_date: 计划开始日期
            end_date: 计划结束日期
            exclude_work_order_id: 排除的工单ID（用于更新时检查）
            
        Returns:
            (是否可用, 不可用原因)
        """
        workstation = db.query(Workstation).filter(Workstation.id == workstation_id).first()
        if not workstation:
            return (False, "工位不存在")
        
        if not workstation.is_active:
            return (False, "工位已停用")
        
        # 检查工位状态
        if workstation.status not in ['IDLE', 'MAINTENANCE']:
            return (False, f"工位状态为：{workstation.status}")
        
        # 检查是否有冲突的工单
        conflicting_orders = db.query(WorkOrder).filter(
            WorkOrder.workstation_id == workstation_id,
            WorkOrder.status.in_(['PLANNED', 'IN_PROGRESS', 'PAUSED']),
            WorkOrder.plan_start_date <= end_date,
            WorkOrder.plan_end_date >= start_date
        )
        
        if exclude_work_order_id:
            conflicting_orders = conflicting_orders.filter(WorkOrder.id != exclude_work_order_id)
        
        conflicting_order = conflicting_orders.first()
        if conflicting_order:
            return (False, f"工位在 {conflicting_order.plan_start_date} 至 {conflicting_order.plan_end_date} 已被工单 {conflicting_order.work_order_no} 占用")
        
        return (True, None)
    
    @classmethod
    def find_available_workstations(
        cls,
        db: Session,
        workshop_id: Optional[int] = None,
        start_date: date = None,
        end_date: date = None,
        required_capability: Optional[str] = None
    ) -> List[Dict]:
        """
        查找可用工位
        
        Args:
            db: 数据库会话
            workshop_id: 车间ID（可选）
            start_date: 计划开始日期（默认今天）
            end_date: 计划结束日期（默认start_date + 7天）
            required_capability: 所需能力（可选）
            
        Returns:
            可用工位列表
        """
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=7)
        
        # 查询工位
        query = db.query(Workstation).filter(
            Workstation.is_active == True,
            Workstation.status == 'IDLE'
        )
        
        if workshop_id:
            query = query.filter(Workstation.workshop_id == workshop_id)
        
        workstations = query.all()
        
        available_workstations = []
        for ws in workstations:
            is_available, reason = cls.check_workstation_availability(
                db, ws.id, start_date, end_date
            )
            
            if is_available:
                available_workstations.append({
                    'workstation_id': ws.id,
                    'workstation_code': ws.workstation_code,
                    'workstation_name': ws.workstation_name,
                    'workshop_id': ws.workshop_id,
                    'workshop_name': ws.workshop.name if ws.workshop else None,
                    'status': ws.status,
                    'available_from': start_date,
                    'available_until': end_date
                })
        
        return available_workstations
    
    @classmethod
    def check_worker_availability(
        cls,
        db: Session,
        worker_id: int,
        start_date: date,
        end_date: date,
        required_hours: float = 8.0,
        exclude_allocation_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str], float]:
        """
        检查人员可用性
        
        Args:
            db: 数据库会话
            worker_id: 工人ID
            start_date: 计划开始日期
            end_date: 计划结束日期
            required_hours: 所需工时（默认8小时/天）
            exclude_allocation_id: 排除的资源分配ID（用于更新时检查）
            
        Returns:
            (是否可用, 不可用原因, 可用工时)
        """
        worker = db.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            return (False, "工人不存在", 0.0)
        
        if not worker.is_active or worker.status != 'ACTIVE':
            return (False, "工人不在职或状态异常", 0.0)
        
        # 计算总可用工时
        workdays = cls._calculate_workdays(start_date, end_date)
        total_available_hours = workdays * 8.0  # 每天8小时
        
        # 计算已分配工时
        assigned_hours = 0.0
        
        # 1. 检查工单分配
        work_orders = db.query(WorkOrder).filter(
            WorkOrder.assigned_to == worker_id,
            WorkOrder.status.in_(['PLANNED', 'IN_PROGRESS', 'PAUSED']),
            WorkOrder.plan_start_date <= end_date,
            WorkOrder.plan_end_date >= start_date
        ).all()
        
        for wo in work_orders:
            if wo.plan_start_date and wo.plan_end_date:
                overlap_days = cls._calculate_overlap_days(
                    start_date, end_date,
                    wo.plan_start_date, wo.plan_end_date
                )
                assigned_hours += overlap_days * 8.0
        
        # 2. 检查资源分配（PMO模块）
        allocations = db.query(PmoResourceAllocation).filter(
            PmoResourceAllocation.resource_id == worker_id,
            PmoResourceAllocation.status != 'CANCELLED',
            PmoResourceAllocation.start_date <= end_date,
            PmoResourceAllocation.end_date >= start_date
        )
        
        if exclude_allocation_id:
            allocations = allocations.filter(PmoResourceAllocation.id != exclude_allocation_id)
        
        for alloc in allocations:
            if alloc.planned_hours:
                assigned_hours += float(alloc.planned_hours)
            else:
                # 如果没有planned_hours，按天数计算
                overlap_days = cls._calculate_overlap_days(
                    start_date, end_date,
                    alloc.start_date, alloc.end_date
                )
                assigned_hours += overlap_days * 8.0
        
        # 3. 检查任务分配（进度模块）
        tasks = db.query(Task).filter(
            Task.owner_id == worker_id,
            Task.status != 'CANCELLED',
            Task.plan_start <= end_date,
            Task.plan_end >= start_date
        ).all()
        
        for task in tasks:
            if task.plan_start and task.plan_end:
                overlap_days = cls._calculate_overlap_days(
                    start_date, end_date,
                    task.plan_start, task.plan_end
                )
                # 假设任务占用50%时间（可配置）
                assigned_hours += overlap_days * 4.0
        
        # 计算可用工时
        available_hours = total_available_hours - assigned_hours
        
        # 检查是否满足需求
        required_total_hours = workdays * required_hours
        if available_hours < required_total_hours:
            return (
                False,
                f"可用工时不足（需要 {required_total_hours:.1f} 小时，可用 {available_hours:.1f} 小时）",
                available_hours
            )
        
        return (True, None, available_hours)
    
    @classmethod
    def find_available_workers(
        cls,
        db: Session,
        workshop_id: Optional[int] = None,
        skill_required: Optional[str] = None,
        start_date: date = None,
        end_date: date = None,
        min_available_hours: float = 8.0
    ) -> List[Dict]:
        """
        查找可用人员
        
        Args:
            db: 数据库会话
            workshop_id: 车间ID（可选）
            skill_required: 所需技能（可选）
            start_date: 计划开始日期
            end_date: 计划结束日期
            min_available_hours: 最小可用工时
            
        Returns:
            可用人员列表
        """
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=7)
        
        # 查询工人
        query = db.query(Worker).filter(
            Worker.is_active == True,
            Worker.status == 'ACTIVE'
        )
        
        if workshop_id:
            query = query.filter(Worker.workshop_id == workshop_id)
        
        workers = query.all()
        
        available_workers = []
        for worker in workers:
            # 检查技能匹配
            skill_match = True
            matched_skills = []
            if skill_required:
                skill_match, matched_skills = cls._check_worker_skill(
                    db, worker.id, skill_required
                )
                if not skill_match:
                    continue  # 技能不匹配，跳过
            
            is_available, reason, available_hours = cls.check_worker_availability(
                db, worker.id, start_date, end_date
            )
            
            if is_available and available_hours >= min_available_hours:
                available_workers.append({
                    'worker_id': worker.id,
                    'worker_no': worker.worker_no,
                    'worker_name': worker.worker_name,
                    'workshop_id': worker.workshop_id,
                    'position': worker.position,
                    'skill_level': worker.skill_level,
                    'available_hours': round(available_hours, 2),
                    'matched_skills': matched_skills,
                    'available_from': start_date,
                    'available_until': end_date
                })
        
        # 按可用工时降序排序
        available_workers.sort(key=lambda x: x['available_hours'], reverse=True)
        
        return available_workers
    
    @classmethod
    def detect_resource_conflicts(
        cls,
        db: Session,
        project_id: int,
        machine_id: Optional[int],
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        检测资源冲突
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            machine_id: 机台ID（可选）
            start_date: 计划开始日期
            end_date: 计划结束日期
            
        Returns:
            冲突列表
        """
        conflicts = []
        
        # 1. 检查机台冲突
        if machine_id:
            machine = db.query(Machine).filter(Machine.id == machine_id).first()
            if machine:
                # 检查是否有其他项目占用该机台
                conflicting_projects = db.query(Project).join(
                    Machine, Project.id == Machine.project_id
                ).filter(
                    Machine.id == machine_id,
                    Project.id != project_id,
                    Project.status.in_(['S4', 'S5']),  # 加工制造、装配调试阶段
                    or_(
                        and_(
                            Project.planned_start_date.isnot(None),
                            Project.planned_start_date <= end_date
                        ),
                        and_(
                            Project.planned_end_date.isnot(None),
                            Project.planned_end_date >= start_date
                        )
                    )
                ).all()
                
                for cp in conflicting_projects:
                    conflicts.append({
                        'type': 'MACHINE',
                        'resource_id': machine_id,
                        'resource_name': machine.machine_code,
                        'conflict_project_id': cp.id,
                        'conflict_project_name': cp.project_name,
                        'conflict_period': f"{cp.planned_start_date or '未知'} 至 {cp.planned_end_date or '未知'}",
                        'severity': 'HIGH'
                    })
        
        return conflicts
    
    @classmethod
    def _calculate_workdays(cls, start_date: date, end_date: date) -> int:
        """计算工作日数量（简单实现，不考虑节假日）"""
        days = (end_date - start_date).days + 1
        # 简单计算：每周5个工作日
        weeks = days // 7
        workdays = weeks * 5 + min(days % 7, 5)
        return max(1, workdays)
    
    @classmethod
    def _calculate_overlap_days(
        cls,
        start1: date,
        end1: date,
        start2: date,
        end2: date
    ) -> int:
        """计算两个日期区间的重叠天数"""
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start > overlap_end:
            return 0
        
        return (overlap_end - overlap_start).days + 1
    
    @classmethod
    def _check_worker_skill(
        cls,
        db: Session,
        worker_id: int,
        skill_required: str
    ) -> Tuple[bool, List[str]]:
        """
        检查工人技能匹配
        
        Args:
            db: 数据库会话
            worker_id: 工人ID
            skill_required: 所需技能（可以是工序编码、工序名称或工序类型）
            
        Returns:
            (是否匹配, 匹配的技能列表)
        """
        from app.models import WorkerSkill, ProcessDict
        
        # 查询工人的技能
        worker_skills = db.query(WorkerSkill).join(
            ProcessDict, WorkerSkill.process_id == ProcessDict.id
        ).filter(
            WorkerSkill.worker_id == worker_id,
            ProcessDict.is_active == True
        ).all()
        
        if not worker_skills:
            return (False, [])
        
        matched_skills = []
        skill_required_lower = skill_required.lower()
        
        for ws in worker_skills:
            process = ws.process
            if not process:
                continue
            
            # 匹配工序编码、名称或类型
            if (skill_required_lower in process.process_code.lower() or
                skill_required_lower in process.process_name.lower() or
                skill_required_lower in (process.process_type or '').lower()):
                matched_skills.append({
                    'process_code': process.process_code,
                    'process_name': process.process_name,
                    'skill_level': ws.skill_level
                })
        
        return (len(matched_skills) > 0, matched_skills)
    
    @classmethod
    def allocate_resources(
        cls,
        db: Session,
        project_id: int,
        machine_id: Optional[int],
        suggested_start_date: date,
        suggested_end_date: date
    ) -> Dict:
        """
        分配资源（工位和人员）
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            machine_id: 机台ID
            suggested_start_date: 建议开始日期
            suggested_end_date: 建议结束日期
            
        Returns:
            资源分配结果
        """
        result = {
            'workstations': [],
            'workers': [],
            'conflicts': [],
            'can_allocate': True
        }
        
        # 1. 检测资源冲突
        conflicts = cls.detect_resource_conflicts(
            db, project_id, machine_id, suggested_start_date, suggested_end_date
        )
        result['conflicts'] = conflicts
        
        if conflicts:
            result['can_allocate'] = False
            return result
        
        # 2. 查找可用工位
        available_workstations = cls.find_available_workstations(
            db,
            start_date=suggested_start_date,
            end_date=suggested_end_date
        )
        result['workstations'] = available_workstations[:3]  # 返回前3个
        
        # 3. 查找可用人员
        available_workers = cls.find_available_workers(
            db,
            start_date=suggested_start_date,
            end_date=suggested_end_date,
            min_available_hours=8.0
        )
        result['workers'] = available_workers[:5]  # 返回前5个
        
        # 4. 判断是否可以分配
        if not available_workstations:
            result['can_allocate'] = False
            result['reason'] = '无可用工位'
        elif not available_workers:
            result['can_allocate'] = False
            result['reason'] = '无可用人员'
        else:
            result['can_allocate'] = True
        
        return result
