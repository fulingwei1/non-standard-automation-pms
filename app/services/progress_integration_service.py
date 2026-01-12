# -*- coding: utf-8 -*-
"""
进度跟踪模块与其他模块的联动服务
包含：缺料联动、ECN联动、验收联动
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.progress import Task, TaskDependency
from app.models.project import ProjectMilestone
from app.models.shortage import ShortageAlert
from app.models.ecn import Ecn
from app.models.acceptance import AcceptanceOrder
from app.models.issue import Issue
from app.models.enums import IssueTypeEnum, IssueStatusEnum, SeverityEnum


class ProgressIntegrationService:
    """进度跟踪联动服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 缺料联动 ====================
    
    def handle_shortage_alert_created(self, alert: ShortageAlert) -> List[Task]:
        """
        处理缺料预警创建，自动阻塞相关任务
        
        Args:
            alert: 缺料预警对象
        
        Returns:
            List[Task]: 被阻塞的任务列表
        """
        blocked_tasks = []
        
        if not alert.project_id:
            return blocked_tasks
        
        # 查找可能受影响的任务（装配、调试相关任务）
        affected_stages = ['S5', 'S6']  # 装配调试、出厂验收阶段
        affected_keywords = ['装配', '调试', '组装', '安装', '联调']
        
        # 查找项目中的相关任务
        tasks = self.db.query(Task).filter(
            Task.project_id == alert.project_id,
            Task.status.in_(['TODO', 'IN_PROGRESS']),
            or_(
                Task.stage.in_(affected_stages),
                *[Task.task_name.like(f'%{kw}%') for kw in affected_keywords]
            )
        ).all()
        
        # 如果缺料预警级别较高（level3/level4）或影响类型为stop/delivery，阻塞任务
        if alert.alert_level in ['level3', 'level4'] or alert.impact_type in ['stop', 'delivery']:
            for task in tasks:
                if task.status != 'BLOCKED':
                    task.status = 'BLOCKED'
                    task.block_reason = f"缺料预警：{alert.material_name}（{alert.alert_no}），预计延迟{alert.estimated_delay_days}天"
                    self.db.add(task)
                    blocked_tasks.append(task)
        
        # 如果预计延迟天数 > 0，调整任务计划结束日期
        if alert.estimated_delay_days and alert.estimated_delay_days > 0:
            for task in tasks:
                if task.plan_end:
                    # 延迟计划结束日期
                    new_plan_end = task.plan_end + timedelta(days=alert.estimated_delay_days)
                    task.plan_end = new_plan_end
                    self.db.add(task)
        
        self.db.commit()
        return blocked_tasks
    
    def handle_shortage_alert_resolved(self, alert: ShortageAlert) -> List[Task]:
        """
        处理缺料预警解决，自动解除相关任务阻塞
        
        Args:
            alert: 缺料预警对象
        
        Returns:
            List[Task]: 被解除阻塞的任务列表
        """
        unblocked_tasks = []
        
        if not alert.project_id:
            return unblocked_tasks
        
        alert_no = getattr(alert, 'alert_no', None) or f"ALERT-{alert.id}"
        material_code = getattr(alert, 'material_code', None) or ''
        
        # 查找因该缺料预警而阻塞的任务
        tasks = self.db.query(Task).filter(
            Task.project_id == alert.project_id,
            Task.status == 'BLOCKED',
            or_(
                Task.block_reason.like(f'%{alert_no}%'),
                Task.block_reason.like(f'%{material_code}%')
            )
        ).all()
        
        for task in tasks:
            # 检查是否还有其他阻塞原因
            other_alerts = self.db.query(ShortageAlert).filter(
                ShortageAlert.project_id == alert.project_id,
                ShortageAlert.status.in_(['pending', 'handling']),
                or_(
                    ShortageAlert.alert_level.in_(['level3', 'level4', 'L3', 'L4', 'CRITICAL']),
                    ShortageAlert.impact_type.in_(['stop', 'delivery'])
                ),
                ShortageAlert.id != alert.id
            ).count()
            
            if other_alerts == 0:
                # 没有其他严重缺料预警，解除阻塞
                task.status = 'IN_PROGRESS'
                task.block_reason = None
                self.db.add(task)
                unblocked_tasks.append(task)
        
        self.db.commit()
        return unblocked_tasks
    
    # ==================== ECN联动 ====================
    
    def handle_ecn_approved(self, ecn: Ecn, threshold_days: int = 3) -> Dict[str, Any]:
        """
        处理ECN审批通过，如果工期影响 > 阈值，自动调整相关任务计划
        
        Args:
            ecn: ECN对象
            threshold_days: 阈值天数，默认3天
        
        Returns:
            Dict: 调整结果
        """
        result = {
            'adjusted_tasks': [],
            'created_tasks': [],
            'affected_milestones': []
        }
        
        if not ecn.project_id:
            return result
        
        # 如果工期影响 > 阈值，需要调整任务计划
        if ecn.schedule_impact_days and ecn.schedule_impact_days > threshold_days:
            # 查找项目中的相关任务（根据ECN关联的机台或阶段）
            query = self.db.query(Task).filter(
                Task.project_id == ecn.project_id,
                Task.status.in_(['TODO', 'IN_PROGRESS'])
            )
            
            if ecn.machine_id:
                query = query.filter(Task.machine_id == ecn.machine_id)
            
            tasks = query.all()
            
            # 调整任务计划
            for task in tasks:
                if task.plan_end:
                    new_plan_end = task.plan_end + timedelta(days=ecn.schedule_impact_days)
                    task.plan_end = new_plan_end
                    
                    # 如果任务已开始，更新预计完成时间
                    if task.actual_start:
                        if task.plan_start:
                            # 保持原计划开始时间，只延后结束时间
                            pass
                    
                    self.db.add(task)
                    result['adjusted_tasks'].append({
                        'task_id': task.id,
                        'task_name': task.task_name,
                        'old_plan_end': task.plan_end - timedelta(days=ecn.schedule_impact_days),
                        'new_plan_end': new_plan_end
                    })
            
            # 调整相关里程碑
            milestones = self.db.query(ProjectMilestone).filter(
                ProjectMilestone.project_id == ecn.project_id,
                ProjectMilestone.status.in_(['PENDING', 'IN_PROGRESS'])
            ).all()
            
            for milestone in milestones:
                if milestone.planned_date:
                    new_planned_date = milestone.planned_date + timedelta(days=ecn.schedule_impact_days)
                    milestone.planned_date = new_planned_date
                    self.db.add(milestone)
                    result['affected_milestones'].append({
                        'milestone_id': milestone.id,
                        'milestone_name': milestone.milestone_name,
                        'old_planned_date': milestone.planned_date - timedelta(days=ecn.schedule_impact_days),
                        'new_planned_date': new_planned_date
                    })
        
        # 如果ECN有执行任务，创建或更新进度任务
        if ecn.tasks:
            for ecn_task in ecn.tasks:
                # 查找是否已有对应的进度任务
                existing_task = self.db.query(Task).filter(
                    Task.project_id == ecn.project_id,
                    Task.task_name.like(f'%{ecn_task.task_name}%'),
                    Task.stage == 'S4'  # 变更通常在S4阶段
                ).first()
                
                if existing_task:
                    # 更新现有任务
                    existing_task.plan_start = ecn_task.planned_start
                    existing_task.plan_end = ecn_task.planned_end
                    existing_task.owner_id = ecn_task.assignee_id
                    if ecn_task.status == 'COMPLETED':
                        existing_task.status = 'DONE'
                        existing_task.progress_percent = 100
                    self.db.add(existing_task)
                else:
                    # 创建新任务
                    new_task = Task(
                        project_id=ecn.project_id,
                        machine_id=ecn.machine_id,
                        task_name=f"ECN执行：{ecn_task.task_name}",
                        stage='S4',
                        status='TODO',
                        owner_id=ecn_task.assignee_id,
                        plan_start=ecn_task.planned_start,
                        plan_end=ecn_task.planned_end,
                        weight=Decimal('1.0')
                    )
                    self.db.add(new_task)
                    self.db.flush()
                    result['created_tasks'].append({
                        'task_id': new_task.id,
                        'task_name': new_task.task_name
                    })
        
        self.db.commit()
        return result
    
    # ==================== 验收联动 ====================
    
    def check_milestone_completion_requirements(
        self,
        milestone: ProjectMilestone
    ) -> tuple[bool, List[str]]:
        """
        检查里程碑完成条件（交付物、验收）
        
        Args:
            milestone: 里程碑对象
        
        Returns:
            tuple: (是否满足条件, 缺失项列表)
        """
        missing_items = []
        
        # 检查交付物要求
        # 里程碑的deliverables字段存储JSON格式的交付物列表
        # 如果里程碑类型为DELIVERY，需要检查交付物是否已审批
        if milestone.milestone_type == 'DELIVERY' and milestone.deliverables:
            import json
            try:
                deliverable_list = json.loads(milestone.deliverables) if isinstance(milestone.deliverables, str) else milestone.deliverables
                if isinstance(deliverable_list, list) and len(deliverable_list) > 0:
                    # 检查交付物是否都已审批（这里简化处理，实际需要根据交付物模型检查）
                    # 假设交付物JSON格式：{"name": "xxx", "status": "APPROVED"}
                    all_approved = all(
                        item.get('status') == 'APPROVED' if isinstance(item, dict) else True
                        for item in deliverable_list
                    )
                    if not all_approved:
                        missing_items.append('交付物未全部审批')
            except (json.JSONDecodeError, TypeError, KeyError):
                # JSON解析失败，跳过检查
                pass
        
        # 检查验收要求
        if hasattr(milestone, 'acceptance_required') and milestone.acceptance_required:
            # 查找关联的验收单
            acceptance_orders = self.db.query(AcceptanceOrder).filter(
                AcceptanceOrder.project_id == milestone.project_id,
                or_(
                    AcceptanceOrder.milestone_id == milestone.id,
                    AcceptanceOrder.acceptance_type.in_(['FAT', 'SAT', 'FINAL'])
                )
            ).all()
            
            # 检查是否有通过的验收单
            passed_orders = [o for o in acceptance_orders if o.overall_result == 'PASSED']
            if not passed_orders:
                missing_items.append('验收未通过')
        
        return len(missing_items) == 0, missing_items
    
    def handle_acceptance_failed(
        self,
        acceptance_order: AcceptanceOrder
    ) -> List[ProjectMilestone]:
        """
        处理验收失败，自动生成问题清单并阻塞相关里程碑
        
        Args:
            acceptance_order: 验收单对象
        
        Returns:
            List[ProjectMilestone]: 被阻塞的里程碑列表
        """
        blocked_milestones = []
        
        if acceptance_order.overall_result != 'FAILED':
            return blocked_milestones
        
        # 查找关联的里程碑
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == acceptance_order.project_id,
            ProjectMilestone.status.in_(['PENDING', 'IN_PROGRESS'])
        ).all()
        
        # 根据验收类型确定关联的里程碑
        if acceptance_order.acceptance_type == 'FAT':
            # FAT关联S6阶段的里程碑
            milestones = [m for m in milestones if m.stage_code == 'S6']
        elif acceptance_order.acceptance_type in ['SAT', 'FINAL']:
            # SAT/终验收关联S8/S9阶段的里程碑
            milestones = [m for m in milestones if m.stage_code in ['S8', 'S9']]
        
        # 阻塞里程碑并生成问题清单
        for milestone in milestones:
            milestone.status = 'BLOCKED'
            self.db.add(milestone)
            blocked_milestones.append(milestone)
            
            # 生成问题清单
            issue = Issue(
                issue_no=f"ISSUE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=acceptance_order.project_id,
                category='ACCEPTANCE',
                issue_type=IssueTypeEnum.BLOCKER.value,
                severity=SeverityEnum.HIGH.value,
                title=f"验收失败：{acceptance_order.order_no}",
                description=f"验收单 {acceptance_order.order_no} 验收失败，阻塞里程碑 {milestone.milestone_name}",
                status=IssueStatusEnum.OPEN.value,
                is_blocking=True,
                acceptance_order_id=acceptance_order.id,
                report_date=datetime.now(),
                reporter_id=acceptance_order.created_by or 1
            )
            self.db.add(issue)
        
        self.db.commit()
        return blocked_milestones
    
    def handle_acceptance_passed(
        self,
        acceptance_order: AcceptanceOrder
    ) -> List[ProjectMilestone]:
        """
        处理验收通过，自动解除相关里程碑阻塞
        
        Args:
            acceptance_order: 验收单对象
        
        Returns:
            List[ProjectMilestone]: 被解除阻塞的里程碑列表
        """
        unblocked_milestones = []
        
        if acceptance_order.overall_result != 'PASSED':
            return unblocked_milestones
        
        # 查找因该验收失败而阻塞的里程碑
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == acceptance_order.project_id,
            ProjectMilestone.status == 'BLOCKED'
        ).all()
        
        # 根据验收类型确定关联的里程碑
        if acceptance_order.acceptance_type == 'FAT':
            milestones = [m for m in milestones if getattr(m, 'stage_code', None) == 'S6']
        elif acceptance_order.acceptance_type in ['SAT', 'FINAL']:
            milestones = [m for m in milestones if getattr(m, 'stage_code', None) in ['S8', 'S9']]
        
        # 检查是否还有其他阻塞原因
        for milestone in milestones:
            # 检查是否还有未解决的阻塞问题
            blocking_issues = self.db.query(Issue).filter(
                Issue.project_id == acceptance_order.project_id,
                Issue.is_blocking == True,
                Issue.status.in_([IssueStatusEnum.OPEN.value, IssueStatusEnum.PROCESSING.value]),
                Issue.acceptance_order_id != acceptance_order.id
            ).count()
            
            if blocking_issues == 0:
                # 没有其他阻塞问题，解除阻塞
                milestone.status = 'IN_PROGRESS'
                self.db.add(milestone)
                unblocked_milestones.append(milestone)
        
        self.db.commit()
        return unblocked_milestones

